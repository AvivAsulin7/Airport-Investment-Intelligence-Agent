import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { describeError, type ErrorInfo } from '../api'
import { useT } from '../i18n'
import { dataNotes, textLang } from '../notes'
import type { ChatResponse, DemoResponse, EvidenceItem } from '../types'
import { EvidenceStrip, Sources } from './Evidence'
import { Orig } from './Orig'

export type Turn =
  | { kind: 'user'; id: string; text: string }
  | { kind: 'assistant'; id: string; response: ChatResponse }
  | { kind: 'demo'; id: string; response: DemoResponse }
  | { kind: 'error'; id: string; info: ErrorInfo; retryText: string | null }

function DataNotes({ evidence, warnings }: { evidence: EvidenceItem[]; warnings: string[] }) {
  const { t } = useT()
  const { small, partial } = dataNotes(evidence)
  if (!warnings.length && !small.length && !partial.length) return null
  const smallList = small.map(([a, n]) => `${a} (${t.flights(n)})`).join(', ')
  return (
    <details className="data-notes">
      <summary>
        <span className="data-notes-title">{t.dataNotes}</span>
        {small.length > 0 && <span className="badge badge-sample">{t.smallSamples(small.length)}</span>}
        {partial.length > 0 && <span className="badge badge-partial">{t.partialCoverage(partial.length)}</span>}
        <span className="muted">{t.warningsCount(warnings.length)}</span>
      </summary>
      {small.length > 0 && <p>{t.smallSampleText(smallList)}</p>}
      {partial.length > 0 && <p>{t.partialText(partial.join(', '))}</p>}
      <ul className="warning-list">
        {warnings.map((w) => <li key={w}><Orig>{w}</Orig></li>)}
      </ul>
    </details>
  )
}

function StatusBanner({ response }: { response: ChatResponse }) {
  const { t } = useT()
  if (response.status === 'incomplete') {
    return <p className="banner banner-warn" role="status">{t.incomplete}</p>
  }
  if (response.status === 'completed_with_tool_errors') {
    return (
      <div className="banner banner-warn" role="status">
        {t.toolErrors}
        <ul>{response.errors.map((e) => <li key={e}><Orig>{e}</Orig></li>)}</ul>
      </div>
    )
  }
  return null
}

function Evidence({ items }: { items: EvidenceItem[] }) {
  const { t } = useT()
  const shown = items.filter((e) => e.status === 'error' || (e.artifact && e.artifact.result_type !== 'airports'))
  const lookups = items.filter((e) => e.status === 'success' && e.artifact?.result_type === 'airports')
  if (!items.length) return null
  return (
    <div className="evidence" aria-label={t.evidence}>
      {shown.map((e, i) => <EvidenceStrip key={e.tool_call_id ?? i} item={e} />)}
      {lookups.length > 0 && (
        <details className="lookups">
          <summary>{t.lookups(lookups.length)}</summary>
          {lookups.map((e, i) => <EvidenceStrip key={e.tool_call_id ?? i} item={e} />)}
        </details>
      )}
    </div>
  )
}

export function Message({ turn, onRetry }: { turn: Turn; onRetry: (text: string) => void }) {
  const { t, lang } = useT()
  if (turn.kind === 'user') {
    // dir="auto": a Hebrew question reads RTL and an English one LTR, whatever the UI language.
    return <div className="msg msg-user"><p dir="auto">{turn.text}</p></div>
  }
  if (turn.kind === 'error') {
    const e = describeError(turn.info, t)
    return (
      <div className="msg msg-assistant msg-error" role="alert">
        <p className="error-title">{e.title}</p>
        <p>{e.detail}</p>
        {turn.retryText && <button type="button" className="btn-secondary" onClick={() => onRetry(turn.retryText!)}>{t.tryAgain}</button>}
      </div>
    )
  }
  if (turn.kind === 'demo') {
    const r = turn.response
    return (
      <div className="msg msg-assistant">
        <p className="banner banner-info">{t.demoLabel}</p>
        <p className="demo-question">{t.examples[r.scenario] ?? r.question}</p>
        <p className="muted"><Orig>{r.caption}</Orig></p>
        <DataNotes evidence={r.evidence} warnings={r.warnings} />
        <Evidence items={r.evidence} />
      </div>
    )
  }
  const r = turn.response
  const replyLang = textLang(r.reply_markdown)
  return (
    <div className="msg msg-assistant">
      {r.notice && <p className="banner banner-info"><Orig>{r.notice}</Orig></p>}
      <StatusBanner response={r} />
      {replyLang && replyLang !== lang && <p className="reply-lang-note">{t.replyLanguageNote}</p>}
      {/* The AI's reply is shown as written; dir="auto" follows its own language (Hebrew or English). */}
      <div className="reply" dir="auto"><Markdown remarkPlugins={[remarkGfm]}>{r.reply_markdown}</Markdown></div>
      <DataNotes evidence={r.evidence} warnings={r.warnings} />
      <Evidence items={r.evidence} />
      {r.sources.length > 0 && (
        <details className="turn-sources">
          <summary>{t.allSources(r.sources.length)}</summary>
          <Sources sources={r.sources} />
        </details>
      )}
    </div>
  )
}
