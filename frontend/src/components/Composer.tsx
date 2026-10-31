import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { useT } from '../i18n'

const MAX_CHARS = 2000

export function Composer({ disabled, placeholder, onSend }: { disabled: boolean; placeholder: string; onSend: (text: string) => void }) {
  const { t } = useT()
  const [text, setText] = useState('')
  const trimmed = text.trim()
  const canSend = !disabled && trimmed.length > 0 && trimmed.length <= MAX_CHARS

  function submit(e?: FormEvent) {
    e?.preventDefault()
    if (!canSend) return
    onSend(trimmed)
    setText('')
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <form className="composer" onSubmit={submit}>
      <label htmlFor="question" className="visually-hidden">{t.inputLabel}</label>
      <textarea
        id="question"
        dir="auto"
        value={text}
        rows={2}
        maxLength={MAX_CHARS}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
      />
      <button type="submit" className="btn-primary" disabled={!canSend}>{t.send}</button>
    </form>
  )
}
