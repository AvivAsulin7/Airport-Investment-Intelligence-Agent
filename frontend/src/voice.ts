// Conversational voice mode: browser speech recognition in, browser speech synthesis out, around the
// existing chat request (same agent, same session). Framework-free so the state machine is testable
// with fake browser APIs. No audio leaves the browser through this app; the browser's own recognition
// service may process audio remotely (stated in the UI).

import { textLang } from './notes'

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
export type VoiceError = 'unsupported' | 'permission' | 'network' | 'no-speech' | 'recognition' | 'request' | 'synthesis'
export type VoiceSnapshot = { state: VoiceState; error: VoiceError | null; muted: boolean; transcript: string }

type RecognitionResultEvent = { results: ArrayLike<ArrayLike<{ transcript: string }>> }

export interface RecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  onresult: ((e: RecognitionResultEvent) => void) | null
  onerror: ((e: { error: string }) => void) | null
  onend: (() => void) | null
  start(): void
  abort(): void
}

export interface UtteranceLike {
  lang: string
  onend: (() => void) | null
  onerror: ((e: { error: string }) => void) | null
}

export interface SynthLike {
  speak(u: UtteranceLike): void
  cancel(): void
}

export interface VoiceDeps {
  createRecognition: (() => RecognitionLike) | null
  synth: SynthLike | null
  createUtterance: (text: string) => UtteranceLike
}

export interface VoiceOptions {
  lang: 'en' | 'he'
  /** Sends the transcript through the normal chat path; resolves to the reply text, or null on failure. */
  ask: (text: string) => Promise<string | null>
  onChange: (s: VoiceSnapshot) => void
  muted?: boolean
}

const SPEECH_LANG = { en: 'en-US', he: 'he-IL' } as const
const MAX_SILENT_WINDOWS = 2 // then pause instead of listening forever
// The app, not the browser, decides when the user has finished: browsers' own end-of-speech detection
// can wait indefinitely with background noise, so a question is submitted after a short pause in the
// live results, and a window with no speech at all is closed after a timeout.
export const END_OF_SPEECH_MS = 1200
export const NO_SPEECH_MS = 10000
const CHUNK_CHARS = 200 // some engines stop long utterances early, so speak sentence by sentence
const CANCELLED = new Set(['interrupted', 'canceled'])

export function browserVoiceDeps(): VoiceDeps {
  const w = window as unknown as {
    SpeechRecognition?: new () => RecognitionLike
    webkitSpeechRecognition?: new () => RecognitionLike
    speechSynthesis?: SynthLike
    SpeechSynthesisUtterance?: new (text: string) => UtteranceLike
  }
  const Recognition = w.SpeechRecognition ?? w.webkitSpeechRecognition
  const Utterance = w.SpeechSynthesisUtterance
  return {
    createRecognition: Recognition ? () => new Recognition() : null,
    synth: w.speechSynthesis && Utterance ? w.speechSynthesis : null,
    createUtterance: (text) => (Utterance ? new Utterance(text) : { lang: '', onend: null, onerror: null }),
  }
}

/** The concise answer as plain speech: no tables, headings, list markers, links or emphasis. */
export function toSpeech(markdown: string): string {
  return markdown
    .split('\n')
    .filter((line) => !/^\s*\|/.test(line) && !/^\s*```/.test(line))
    .map((line) => line.replace(/^\s*(#{1,6}\s+|[-*•]\s+|\d+\.\s+|>\s*)/, ''))
    .join(' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[*_`~]+/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export function speechChunks(text: string): string[] {
  const chunks: string[] = []
  for (const sentence of text.split(/(?<=[.!?])\s+/)) {
    const last = chunks.length - 1
    if (last >= 0 && chunks[last].length + sentence.length + 1 <= CHUNK_CHARS) chunks[last] += ` ${sentence}`
    else if (sentence) chunks.push(sentence)
  }
  return chunks
}

export class VoiceController {
  private snap: VoiceSnapshot
  private token = 0 // bumped on start/stop/failure: callbacks from older runs are ignored
  private recognition: RecognitionLike | null = null
  private silentWindows = 0
  private readonly deps: VoiceDeps
  private readonly opts: VoiceOptions

  constructor(deps: VoiceDeps, opts: VoiceOptions) {
    this.deps = deps
    this.opts = opts
    this.snap = { state: 'idle', error: null, muted: opts.muted ?? false, transcript: '' }
  }

  get snapshot(): VoiceSnapshot {
    return this.snap
  }

  start() {
    this.halt()
    this.silentWindows = 0
    if (!this.deps.createRecognition) return this.fail('unsupported')
    this.listen()
  }

  /** Stop at any time: cancels recognition and playback; late browser events are ignored. */
  stop() {
    this.halt()
    this.set({ state: 'idle', error: null })
  }

  setMuted(muted: boolean) {
    this.set({ muted })
    if (muted && this.snap.state === 'speaking') {
      this.token++ // drop the cancelled utterances' callbacks
      this.deps.synth?.cancel()
      this.listen()
    }
  }

  private set(patch: Partial<VoiceSnapshot>) {
    this.snap = { ...this.snap, ...patch }
    this.opts.onChange(this.snap)
  }

  private detach(rec: RecognitionLike) {
    rec.onresult = rec.onerror = rec.onend = null
    if (this.recognition === rec) this.recognition = null
    try {
      rec.abort()
    } catch {
      // already stopped
    }
  }

  private halt() {
    this.token++
    if (this.recognition) this.detach(this.recognition)
    this.deps.synth?.cancel()
  }

  private fail(error: VoiceError) {
    this.halt()
    this.set({ state: 'error', error, transcript: '' }) // no automatic restart: the user presses Start again
  }

  private listen() {
    const token = this.token
    const rec = this.deps.createRecognition!()
    this.recognition = rec
    rec.lang = SPEECH_LANG[this.opts.lang]
    rec.continuous = true // the window is closed by the app (pause or timeout), not by the browser
    rec.interimResults = true // live words: shown to the user and used to detect the end of speech
    rec.maxAlternatives = 1
    let done = false
    let text = ''
    let lastError = ''
    let endTimer: ReturnType<typeof setTimeout> | undefined
    const close = () => {
      done = true
      clearTimeout(endTimer)
      clearTimeout(noSpeechTimer)
      this.detach(rec)
    }
    const submit = () => {
      close()
      void this.submit(text)
    }
    const noSpeechTimer = setTimeout(() => {
      if (token !== this.token || done || text) return
      close()
      this.silentWindowEnded('no-speech')
    }, NO_SPEECH_MS)

    rec.onresult = (e) => {
      if (token !== this.token || done) return
      let heard = ''
      for (let i = 0; i < e.results.length; i++) heard += ` ${e.results[i][0]?.transcript ?? ''}`
      text = heard.replace(/\s+/g, ' ').trim()
      this.set({ transcript: text })
      clearTimeout(endTimer)
      if (!text) return
      endTimer = setTimeout(() => {
        if (token === this.token && !done) submit()
      }, END_OF_SPEECH_MS)
    }
    rec.onerror = (e) => {
      if (token === this.token) lastError = e.error
    }
    rec.onend = () => {
      if (token !== this.token || done) return
      if (text) return submit() // the browser ended the session after hearing speech
      close()
      this.silentWindowEnded(lastError)
    }
    this.set({ state: 'listening', error: null, transcript: '' })
    try {
      rec.start()
    } catch {
      this.fail('recognition')
    }
  }

  private silentWindowEnded(browserError: string) {
    if (browserError === 'not-allowed' || browserError === 'service-not-allowed' || browserError === 'audio-capture') {
      return this.fail('permission')
    }
    if (browserError === 'network') return this.fail('network')
    if (browserError && browserError !== 'no-speech') return this.fail('recognition')
    if (++this.silentWindows >= MAX_SILENT_WINDOWS) return this.fail('no-speech')
    this.listen()
  }

  private async submit(transcript: string) {
    const token = this.token
    this.silentWindows = 0
    this.set({ state: 'processing', transcript: '' })
    let reply: string | null = null
    try {
      reply = await this.opts.ask(transcript)
    } catch {
      reply = null
    }
    if (token !== this.token) return // stopped while the agent was working
    if (reply === null) return this.fail('request')
    this.speak(reply)
  }

  private speak(markdown: string) {
    const text = toSpeech(markdown)
    const synth = this.deps.synth
    if (this.snap.muted || !synth || !text) return this.listen()
    const token = ++this.token // the microphone stays off until playback ends
    const lang = SPEECH_LANG[textLang(text) ?? this.opts.lang]
    const chunks = speechChunks(text)
    this.set({ state: 'speaking' })
    synth.cancel()
    chunks.forEach((chunk, i) => {
      const u = this.deps.createUtterance(chunk)
      u.lang = lang
      u.onerror = (e) => {
        if (token !== this.token) return
        if (CANCELLED.has(e.error)) this.stop() // cancelled outside the app (e.g. the browser)
        else this.fail('synthesis')
      }
      if (i === chunks.length - 1) {
        u.onend = () => {
          if (token === this.token && this.snap.state === 'speaking') this.listen()
        }
      }
      synth.speak(u)
    })
  }
}
