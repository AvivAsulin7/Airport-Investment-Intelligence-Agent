import { useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from './api'

// Phase 4 foundation page: proves React -> /api -> FastAPI. The chat UI is Phase 8.
function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getHealth().then(setHealth, (e: Error) => setError(e.message))
  }, [])

  return (
    <main>
      <h1>Airport Investment Intelligence Agent</h1>
      <p className="muted">Project foundation: backend connectivity check.</p>
      {error && <p className="error">{error}</p>}
      {!health && !error && <p>Checking backend…</p>}
      {health && (
        <dl>
          <dt>Backend</dt>
          <dd>{health.status}</dd>
          <dt>LLM</dt>
          <dd>
            {health.llm_configured ? 'configured' : 'not configured (API key missing)'} · model{' '}
            <code>{health.llm_model}</code>
          </dd>
          <dt>BTS public API (live)</dt>
          <dd>
            {health.bts_api.reachable
              ? `reachable · latest month ${health.bts_api.latest_month} · retrieved ${health.bts_api.retrieved_at}`
              : `unreachable (${health.bts_api.error})`}
          </dd>
        </dl>
      )}
    </main>
  )
}

export default App
