import { useEffect, useMemo, useRef, useState } from 'react'
import { classifyError, getHealth, postChat, postDemo } from './api'
import { Composer } from './components/Composer'
import { Message, type Turn } from './components/Conversation'
import { DICTS, LangContext, type Lang } from './i18n'
import { EXAMPLE_IDS } from './notes'
import type { HealthResponse } from './types'

let nextId = 0
const uid = () => `t${++nextId}`
const LANG_KEY = 'ui-lang'

function initialLang(): Lang {
  try {
    return localStorage.getItem(LANG_KEY) === 'he' ? 'he' : 'en'
  } catch {
    return 'en'
  }
}

export default function App() {
  const [lang, setLang] = useState<Lang>(initialLang)
  const [turns, setTurns] = useState<Turn[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const inFlight = useRef(false)

  const t = DICTS[lang]
  const dir = lang === 'he' ? 'rtl' : 'ltr'
  const ctx = useMemo(() => ({ lang, t }), [lang, t])

  // Keep <html lang/dir> in sync (screen readers, browser UI); conversation state is untouched.
  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = dir
    try {
      localStorage.setItem(LANG_KEY, lang)
    } catch {
      // storage unavailable (private mode); the choice simply is not remembered
    }
  }, [lang, dir])

  useEffect(() => {
    getHealth().then(setHealth, () => setHealthError(true))
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' })
  }, [turns, pending])

  useEffect(() => {
    if (!pending) return
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(timer)
  }, [pending])

  const demoMode = health !== null && !health.llm_configured

  async function ask(text: string) {
    if (inFlight.current) return // guard against double submission
    inFlight.current = true
    setElapsed(0)
    setPending(true)
    setTurns((ts) => [...ts, { kind: 'user', id: uid(), text }])
    try {
      const r = await postChat(text, sessionId)
      setSessionId(r.session_id)
      setTurns((ts) => [...ts, { kind: 'assistant', id: uid(), response: r }])
    } catch (err) {
      const info = classifyError(err)
      setTurns((ts) => [...ts, { kind: 'error', id: uid(), info, retryText: info.retryable ? text : null }])
    } finally {
      inFlight.current = false
      setPending(false)
    }
  }

  async function runDemo(id: string, text: string) {
    if (inFlight.current) return
    inFlight.current = true
    setElapsed(0)
    setPending(true)
    setTurns((ts) => [...ts, { kind: 'user', id: uid(), text }])
    try {
      const r = await postDemo(id)
      setTurns((ts) => [...ts, { kind: 'demo', id: uid(), response: r }])
    } catch (err) {
      setTurns((ts) => [...ts, { kind: 'error', id: uid(), info: classifyError(err), retryText: null }])
    } finally {
      inFlight.current = false
      setPending(false)
    }
  }

  function newConversation() {
    setTurns([])
    setSessionId(null)
  }

  return (
    <LangContext.Provider value={ctx}>
      <div className="app" dir={dir} lang={lang}>
        <header className="topbar">
          <div className="brand">
            <h1>{t.title}</h1>
            <p>{t.subtitle}</p>
          </div>
          <div className="topbar-side">
            <span className="status-line" aria-live="polite">
              {healthError && t.backendUnreachable}
              {health && (health.llm_configured ? t.model(health.llm_model) : t.notConfigured)}
              {health?.bts_api.reachable && health.bts_api.latest_month && t.btsThrough(health.bts_api.latest_month)}
            </span>
            <div className="lang-toggle" role="group" aria-label={t.langToggleLabel}>
              <button type="button" lang="en" aria-pressed={lang === 'en'} onClick={() => setLang('en')}>EN</button>
              <span aria-hidden="true">|</span>
              <button type="button" lang="he" aria-pressed={lang === 'he'} onClick={() => setLang('he')}>עברית</button>
            </div>
            <button type="button" className="btn-secondary" onClick={newConversation} disabled={pending || turns.length === 0}>
              {t.newConversation}
            </button>
          </div>
        </header>

        {demoMode && <p className="banner banner-info mode-banner">{t.demoBanner}</p>}

        <main className="conversation" aria-live="polite">
          {turns.length === 0 && (
            <section className="empty">
              <h2>{t.emptyTitle}</h2>
              <p>{t.emptyBody}</p>
              <div className="examples">
                {EXAMPLE_IDS.map((id) => (
                  <button
                    key={id}
                    type="button"
                    className="example"
                    disabled={pending || (!demoMode && !health?.llm_configured && !healthError)}
                    onClick={() => (demoMode ? runDemo(id, t.examples[id]) : ask(t.examples[id]))}
                  >
                    {t.examples[id]}
                  </button>
                ))}
              </div>
            </section>
          )}

          {turns.map((turn) => <Message key={turn.id} turn={turn} onRetry={ask} />)}

          {pending && (
            <div className="msg msg-assistant msg-pending" role="status">
              <span className="pending-dot" aria-hidden="true" />
              {t.pending(elapsed)}
            </div>
          )}
          <div ref={endRef} />
        </main>

        <footer className="composer-wrap">
          <Composer disabled={pending || demoMode} placeholder={demoMode ? t.placeholderDemo : t.placeholder} onSend={ask} />
          {sessionId && <p className="session-hint">{t.sessionHint}</p>}
        </footer>
      </div>
    </LangContext.Provider>
  )
}
