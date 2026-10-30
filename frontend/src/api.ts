// Typed client for the FastAPI backend. Types mirror backend responses (D-022).

export type BtsApiStatus = {
  reachable: boolean
  status_code?: number
  latest_month?: string | null
  source_type: 'public_api'
  url: string
  retrieved_at: string
  error?: string
}

export type HealthResponse = {
  status: string
  llm_configured: boolean
  llm_model: string
  bts_api: BtsApiStatus
}

export async function getHealth(): Promise<HealthResponse> {
  const resp = await fetch('/api/health')
  if (!resp.ok) throw new Error(`Health check failed: HTTP ${resp.status}`)
  return resp.json() as Promise<HealthResponse>
}
