// Voice mode: state machine, guards and cleanup with fake browser speech APIs (no real audio).
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import type { ChatResponse } from '../types'
import {
  END_OF_SPEECH_MS,
  NO_SPEECH_MS,
  speechChunks,
  toSpeech,
  VoiceController,
  type RecognitionLike,
  type UtteranceLike,
  type VoiceDeps,
  type VoiceSnapshot,
} from '../voice'
import ranking from './fixtures/chat_ranking.json'

// Like Chrome in continuous mode: live results keep arriving and the session does NOT end by itself.
class FakeRecognition implements RecognitionLike {
  static all: FakeRecognition[] = []
  lang = ''
  continuous = false
  interimResults = false
  maxAlternatives = 5
  onresult: RecognitionLike['onresult'] = null
  onerror: RecognitionLike['onerror'] = null
  onend: RecognitionLike['onend'] = null
  started = false
  aborted = false
  constructor() {
    FakeRecognition.all.push(this)
  }
  start() {
    this.started = true
  }
  abort() {
    this.aborted = true
    this.onerror?.({ error: 'aborted' })
    this.onend?.()
  }
  /** Words heard so far (segments), as the browser reports them while the user speaks. */
  hear(...segments: string[]) {
    this.onresult?.({ results: segments.map((transcript) => [{ transcript }]) })
  }
  failWith(error: string) {
    this.onerror?.({ error })
    this.onend?.()
  }
}

class FakeSynth {
  queue: (UtteranceLike & { text: string })[] = []
  spoken: { text: string; lang: string }[] = []
  speak(u: UtteranceLike) {
    const item = u as UtteranceLike & { text: string }
    this.queue.push(item)
    this.spoken.push({ text: item.text, lang: u.lang })
  }
  cancel() {
    const q = this.queue
    this.queue = []
    q.forEach((u) => u.onerror?.({ error: 'interrupted' }))
  }
  finishAll() {
    const q = this.queue
    this.queue = []
    q.forEach((u) => u.onend?.())
  }
}

const lastRec = () => FakeRecognition.all[FakeRecognition.all.length - 1]

function setup(opts: { lang?: 'en' | 'he'; muted?: boolean; ask?: (t: string) => Promise<string | null>; recognition?: boolean } = {}) {
  FakeRecognition.all = []
  const synth = new FakeSynth()
  const deps: VoiceDeps = {
    createRecognition: opts.recognition === false ? null : () => new FakeRecognition(),
    synth,
    createUtterance: (text) => ({ text, lang: '', onend: null, onerror: null }) as UtteranceLike,
  }
  const states: string[] = []
  const ask = vi.fn(opts.ask ?? (async () => 'AAA ranks first.'))
  const c = new VoiceController(deps, {
    lang: opts.lang ?? 'en',
    ask,
    muted: opts.muted,
    onChange: (s: VoiceSnapshot) => {
      const label = s.error ? `${s.state}:${s.error}` : s.state
      if (states[states.length - 1] !== label) states.push(label)
    },
  })
  return { c, synth, ask, states }
}

/** The user speaks, then pauses long enough for the app to treat the question as finished. */
async function speak(...segments: string[]) {
  lastRec().hear(...segments)
  await vi.advanceTimersByTimeAsync(END_OF_SPEECH_MS + 10)
}

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('voice state machine', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('runs listen → process → speak → listen, and never listens while speaking', async () => {
    const { c, synth, ask, states } = setup()
    c.start()
    expect(c.snapshot.state).toBe('listening')
    expect(lastRec()).toMatchObject({ lang: 'en-US', continuous: true, interimResults: true, started: true })

    await speak('rank New England airports')
    expect(ask).toHaveBeenCalledWith('rank New England airports')
    expect(c.snapshot.state).toBe('speaking')
    expect(synth.spoken).toEqual([{ text: 'AAA ranks first.', lang: 'en-US' }])
    expect(lastRec().aborted).toBe(true) // microphone closed before the answer is read
    expect(FakeRecognition.all).toHaveLength(1)

    synth.finishAll()
    expect(c.snapshot.state).toBe('listening')
    expect(FakeRecognition.all).toHaveLength(2)
    expect(states).toEqual(['listening', 'processing', 'speaking', 'listening'])
  })

  it('submits when the user pauses even if the browser never ends the session (regression)', async () => {
    const { c, ask } = setup()
    c.start()
    lastRec().hear('what is the unmet demand at SFO') // no onend from the browser, as with background noise
    expect(c.snapshot).toMatchObject({ state: 'listening', transcript: 'what is the unmet demand at SFO' })
    await vi.advanceTimersByTimeAsync(END_OF_SPEECH_MS + 10)
    expect(ask).toHaveBeenCalledWith('what is the unmet demand at SFO')
  })

  it('keeps listening while the user is still speaking and joins the segments', async () => {
    const { c, ask } = setup()
    c.start()
    lastRec().hear('rank Florida')
    await vi.advanceTimersByTimeAsync(END_OF_SPEECH_MS - 400)
    lastRec().hear('rank Florida', ' airports, medium hubs only')
    await vi.advanceTimersByTimeAsync(END_OF_SPEECH_MS - 400)
    expect(ask).not.toHaveBeenCalled() // a short pause mid-question does not submit
    await vi.advanceTimersByTimeAsync(500)
    expect(ask).toHaveBeenCalledTimes(1)
    expect(ask).toHaveBeenCalledWith('rank Florida airports, medium hubs only')
  })

  it('submits each question only once', async () => {
    const { c, ask } = setup()
    c.start()
    const rec = lastRec()
    await speak('q')
    rec.onend?.() // late browser events after submission are ignored (handlers detached)
    await vi.advanceTimersByTimeAsync(END_OF_SPEECH_MS * 2)
    expect(ask).toHaveBeenCalledTimes(1)
    expect(c.snapshot.state).toBe('speaking')
  })

  it('submits immediately if the browser ends the session after hearing speech', async () => {
    const { c, ask } = setup()
    c.start()
    lastRec().hear('compare JFK and BOS')
    lastRec().onend?.()
    await vi.advanceTimersByTimeAsync(0)
    expect(ask).toHaveBeenCalledWith('compare JFK and BOS')
  })

  it('stop cancels recognition and playback and ignores late events', async () => {
    let release!: (v: string) => void
    const { c, synth } = setup({ ask: () => new Promise((r) => (release = r)) })
    c.start()
    await speak('q')
    c.stop() // while the agent is working
    expect(c.snapshot).toMatchObject({ state: 'idle', error: null })
    release('late answer')
    await vi.advanceTimersByTimeAsync(0)
    expect(synth.spoken).toEqual([])
    expect(FakeRecognition.all).toHaveLength(1)

    const second = setup()
    second.c.start()
    second.c.stop() // while listening
    expect(lastRec().aborted).toBe(true)
    await vi.advanceTimersByTimeAsync(NO_SPEECH_MS * 3)
    expect(FakeRecognition.all).toHaveLength(1) // no restart after stop

    second.c.start()
    await speak('q')
    second.c.stop() // while speaking
    expect(second.synth.queue).toEqual([])
    second.synth.finishAll()
    expect(second.c.snapshot.state).toBe('idle')
  })

  it('pauses after repeated silence instead of restarting forever', async () => {
    const { c } = setup()
    c.start()
    await vi.advanceTimersByTimeAsync(NO_SPEECH_MS + 10) // app timeout, no words heard
    expect(c.snapshot.state).toBe('listening')
    lastRec().failWith('no-speech') // or the browser's own no-speech error
    expect(c.snapshot).toMatchObject({ state: 'error', error: 'no-speech' })
    await vi.advanceTimersByTimeAsync(NO_SPEECH_MS * 3)
    expect(FakeRecognition.all).toHaveLength(2)
  })

  it.each([
    ['not-allowed', 'permission'],
    ['network', 'network'],
    ['bad-grammar', 'recognition'],
  ])('recognition error %s stops with %s and does not restart', async (browserError, expected) => {
    const { c } = setup()
    c.start()
    lastRec().failWith(browserError)
    expect(c.snapshot).toMatchObject({ state: 'error', error: expected })
    await vi.advanceTimersByTimeAsync(NO_SPEECH_MS * 3)
    expect(FakeRecognition.all).toHaveLength(1)
  })

  it('a failed chat request stops voice mode (the error is shown in the conversation)', async () => {
    const { c } = setup({ ask: async () => null })
    c.start()
    await speak('q')
    expect(c.snapshot).toMatchObject({ state: 'error', error: 'request' })
    expect(FakeRecognition.all).toHaveLength(1)
  })

  it('reports unsupported browsers', () => {
    const { c } = setup({ recognition: false })
    c.start()
    expect(c.snapshot).toMatchObject({ state: 'error', error: 'unsupported' })
  })

  it('when muted it skips playback; muting during playback cancels it and listens again', async () => {
    const muted = setup({ muted: true })
    muted.c.start()
    await speak('q')
    expect(muted.synth.spoken).toEqual([])
    expect(muted.c.snapshot.state).toBe('listening')

    const live = setup()
    live.c.start()
    await speak('q')
    expect(live.c.snapshot.state).toBe('speaking')
    live.c.setMuted(true)
    expect(live.synth.queue).toEqual([])
    expect(live.c.snapshot).toMatchObject({ state: 'listening', muted: true })
  })

  it('a synthesis failure stops voice mode without a restart loop', async () => {
    const { c, synth } = setup()
    c.start()
    await speak('q')
    synth.queue[0].onerror?.({ error: 'synthesis-failed' })
    expect(c.snapshot).toMatchObject({ state: 'error', error: 'synthesis' })
    expect(FakeRecognition.all).toHaveLength(1)
  })

  it('uses Hebrew recognition for the Hebrew UI and a Hebrew voice for Hebrew answers', async () => {
    const { c, synth } = setup({ lang: 'he', ask: async () => 'כ-4.2% מהיציאות מ-ANC הן לטווח ארוך.' })
    c.start()
    expect(lastRec().lang).toBe('he-IL')
    await speak('מה אחוז הטיסות הארוכות?')
    expect(synth.spoken[0].lang).toBe('he-IL')
  })
})

describe('speech text', () => {
  it('speaks only the prose: no tables, headings, list markers, links or emphasis', () => {
    const md = '## Result\n**BGR** leads at 85.4/100.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n- See [evidence](#x).'
    expect(toSpeech(md)).toBe('Result BGR leads at 85.4/100. See evidence.')
  })

  it('splits long answers into sentence chunks', () => {
    const chunks = speechChunks(`${'A'.repeat(150)}. ${'B'.repeat(150)}. Short.`)
    expect(chunks).toHaveLength(2)
    expect(chunks.every((ch) => ch.length <= 200)).toBe(true)
  })
})

describe('voice mode in the app', () => {
  it('sends voice questions through /api/chat with the same session and keeps the evidence', async () => {
    FakeRecognition.all = []
    const synth = new FakeSynth()
    vi.stubGlobal('SpeechRecognition', FakeRecognition)
    vi.stubGlobal('speechSynthesis', synth)
    vi.stubGlobal('SpeechSynthesisUtterance', function (this: { text: string }, text: string) {
      this.text = text
    })
    const bodies: Record<string, unknown>[] = []
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      if (url === '/api/health') {
        return new Response(JSON.stringify({ status: 'ok', llm_configured: true, llm_model: 'test-model', bts_api: { reachable: true, source_type: 'public_api', url: 'u', retrieved_at: 't' } }))
      }
      bodies.push(JSON.parse(String(init!.body)))
      return new Response(JSON.stringify({ ...(ranking as ChatResponse), session_id: '33333333-3333-4333-8333-333333333333' }))
    }))
    const slow = { timeout: END_OF_SPEECH_MS + 2000 }

    const { unmount } = render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())
    fireEvent.click(screen.getByRole('button', { name: 'Start voice conversation' }))
    expect(screen.getByText('Listening. Ask your question.')).toBeTruthy()
    expect((screen.getByLabelText('Ask about US airports') as HTMLTextAreaElement).disabled).toBe(true)

    act(() => lastRec().hear('rank New England airports'))
    expect(screen.getByText('“rank New England airports”')).toBeTruthy() // live words shown while listening
    await waitFor(() => expect(screen.getAllByRole('region', { name: 'Airport ranking' })).toHaveLength(1), slow)
    expect(screen.getByText('rank New England airports')).toBeTruthy() // transcript becomes the user turn
    await waitFor(() => expect(synth.spoken).toHaveLength(1))
    expect(synth.spoken[0].text).toBe('AAA ranks first in this fictional group. See the ranking evidence.')

    act(() => synth.finishAll())
    act(() => lastRec().hear('only medium hubs'))
    await waitFor(() => expect(bodies).toHaveLength(2), slow)
    expect(bodies[0].session_id).toBeNull()
    expect(bodies[1].session_id).toBe('33333333-3333-4333-8333-333333333333')
    await waitFor(() => expect(synth.spoken).toHaveLength(2))

    unmount() // cleanup: playback cancelled, no further listening
    expect(synth.queue).toEqual([])
    const count = FakeRecognition.all.length
    synth.finishAll()
    expect(FakeRecognition.all).toHaveLength(count)
  })
})
