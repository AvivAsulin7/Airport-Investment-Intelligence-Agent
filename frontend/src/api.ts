// Typed client for the FastAPI backend. Same origin: Vite proxies /api in dev; FastAPI serves the build.

import type { Dict } from './i18n'
import type { ChatResponse, DemoResponse, HealthResponse } from './types'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export type ErrorInfo = { status: number | null; serverDetail: string; retryable: boolean }

/** Classify a failure; the UI renders the text in the current language (describeError). */
export function classifyError(err: unknown): ErrorInfo {
  if (err instanceof ApiError) {
    return { status: err.status, serverDetail: err.message, retryable: ![503, 409, 422].includes(err.status) }
  }
  return { status: null, serverDetail: '', retryable: true }
}

/** Plain-language explanation for documented backend failures (README "API"). */
export function describeError(e: ErrorInfo, t: Dict): { title: string; detail: string } {
  switch (e.status) {
    case null:
      return { title: t.errNetwork, detail: t.errNetworkDetail }
    case 503:
      return { title: t.err503, detail: e.serverDetail }
    case 502:
      return { title: t.err502, detail: t.err502Detail(e.serverDetail) }
    case 409:
      return { title: t.err409, detail: t.err409Detail }
    case 422:
      return { title: t.err422, detail: t.err422Detail }
    default:
      return { title: t.errHttp(e.status), detail: e.serverDetail }
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, init)
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = (await resp.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // non-JSON error body; keep the status text
    }
    throw new ApiError(resp.status, detail)
  }
  return resp.json() as Promise<T>
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

export function postChat(message: string, sessionId: string | null): Promise<ChatResponse> {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })
}

export function postDemo(scenario: string): Promise<DemoResponse> {
  return request<DemoResponse>(`/api/demo/${scenario}`, { method: 'POST' })
}
