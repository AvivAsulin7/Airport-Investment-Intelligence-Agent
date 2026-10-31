import { useT } from '../i18n'
import type { VoiceSnapshot } from '../voice'

type Props = {
  voice: VoiceSnapshot
  recognitionSupported: boolean
  synthesisSupported: boolean
  disabled: boolean
  onStart: () => void
  onStop: () => void
  onToggleMute: () => void
}

export function VoiceControls({ voice, recognitionSupported, synthesisSupported, disabled, onStart, onStop, onToggleMute }: Props) {
  const { t } = useT()
  const active = voice.state !== 'idle' && voice.state !== 'error'
  const message = voice.error ? t.voiceErrors[voice.error] : t.voiceStates[voice.state]

  if (!recognitionSupported) return <p className="voice-note">{t.voiceErrors.unsupported}</p>

  return (
    <div className={`voice voice-${voice.state}`} role="group" aria-label={t.voiceGroup}>
      {active ? (
        <button type="button" className="btn-secondary voice-stop" onClick={onStop}>{t.voiceStop}</button>
      ) : (
        <button type="button" className="btn-secondary" onClick={onStart} disabled={disabled}>{t.voiceStart}</button>
      )}
      <button type="button" className="btn-secondary" aria-pressed={voice.muted} onClick={onToggleMute} disabled={!synthesisSupported}>
        {voice.muted ? t.voiceUnmute : t.voiceMute}
      </button>
      <span className="voice-status" role="status">
        {voice.state === 'listening' && <span className="voice-dot" aria-hidden="true" />}
        {message}
      </span>
      {voice.state === 'listening' && voice.transcript && (
        <span className="voice-transcript" dir="auto">“{voice.transcript}”</span>
      )}
      {active && <span className="voice-note">{synthesisSupported ? t.voicePrivacy : `${t.voicePrivacy} ${t.voiceNoSynth}`}</span>}
    </div>
  )
}
