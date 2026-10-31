// UI tests against backend-generated contract fixtures (fictional data, see backend/tests/test_contract_fixtures.py).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { Message, type Turn } from '../components/Conversation'
import { DICTS, LangContext } from '../i18n'
import type { ChatResponse } from '../types'
import ranking from './fixtures/chat_ranking.json'
import comparison from './fixtures/chat_comparison.json'
import longHaul from './fixtures/chat_long_haul.json'
import profile from './fixtures/chat_profile.json'
import toolError from './fixtures/chat_tool_error.json'
import incomplete from './fixtures/chat_incomplete.json'

// Type-checks the fixtures against the frontend contract (tsc -b fails on drift).
const R = ranking as ChatResponse
const C = comparison as ChatResponse
const L = longHaul as ChatResponse
const P = profile as ChatResponse
const E = toolError as ChatResponse
const I = incomplete as ChatResponse

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function renderAssistant(response: ChatResponse) {
  const turn: Turn = { kind: 'assistant', id: 'a1', response }
  return render(<Message turn={turn} onRetry={() => {}} />)
}

describe('evidence views render from structured evidence', () => {
  it('ranking: scores, ranks and small-sample badges come from the artifact', () => {
    renderAssistant(R)
    const art = R.evidence[0].artifact!
    if (art.result_type !== 'ranking') throw new Error('fixture')
    const strip = screen.getByRole('region', { name: 'Airport ranking' })
    for (const a of art.data.airports.filter((x) => x.score !== null)) {
      const row = within(strip).getByText(a.airport).closest('tr')!
      expect(row.textContent).toContain(a.score!.toFixed(1))
      expect(row.textContent).toContain(String(a.rank))
    }
    const ddd = within(strip).getByText('DDD').closest('tr')!
    expect(within(ddd).getByText('Small sample')).toBeTruthy()
    expect(strip.textContent).toContain('not a verified investment opportunity')
    expect(screen.getByText(/1 small sample/)).toBeTruthy() // data-notes summary
  })

  it('comparison: values with numerator/denominator and backend differences', () => {
    renderAssistant(C)
    const art = C.evidence[0].artifact!
    if (art.result_type !== 'comparison') throw new Error('fixture')
    const strip = screen.getByRole('region', { name: 'Airport comparison' })
    const delay = art.data.values.delay_rate.AAA
    expect(strip.textContent).toContain(`${(delay.value! * 100).toFixed(1)}%`)
    expect(strip.textContent).toContain(`${delay.numerator!.toLocaleString('en-US')} / ${delay.denominator!.toLocaleString('en-US')}`)
    expect(strip.textContent).toContain('DDD vs AAA')
  })

  it('long haul: passenger and all-class shares with class breakdown', () => {
    renderAssistant(L)
    const art = L.evidence[0].artifact!
    if (art.result_type !== 'long_haul') throw new Error('fixture')
    const strip = screen.getByRole('region', { name: 'Long-haul share' })
    expect(strip.textContent).toContain(`${(art.data.primary.share! * 100).toFixed(1)}%`)
    expect(strip.textContent).toContain(`${(art.data.all_classes.share! * 100).toFixed(1)}%`)
    expect(strip.textContent).toContain('Scheduled all-cargo')
    expect(strip.textContent).toContain('3,000 statute miles')
  })

  it('demand profile: observed demand, peer position, causes and unmet demand not measured', () => {
    renderAssistant(P)
    const strip = screen.getByRole('region', { name: 'Demand-pressure indicators' })
    expect(within(strip).getByText('Unmet demand: not measured')).toBeTruthy()
    expect(strip.textContent).toContain('Observed demand')
    expect(strip.textContent).toContain('National airspace system')
  })

  it('shows sources, periods and confidence', () => {
    renderAssistant(R)
    expect(screen.getAllByText('BTS public API, live').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Public dataset snapshot').length).toBeGreaterThan(0)
    expect(screen.getByText('medium')).toBeTruthy()
  })

  it('statuses: tool errors and incomplete turns are flagged', () => {
    renderAssistant(E)
    expect(screen.getByText(/Some analyses could not run/)).toBeTruthy()
    expect(screen.getByLabelText('Analysis error')).toBeTruthy()
    cleanup()
    renderAssistant(I)
    expect(screen.getByText(/Analysis incomplete. The assistant reached its step limit/)).toBeTruthy()
  })
})

type Call = { url: string; body: Record<string, unknown> | null }

function mockBackend(handlers: { health?: object; chat?: (body: Record<string, unknown>, n: number) => Response | Promise<Response> }) {
  const calls: Call[] = []
  let n = 0
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null
    calls.push({ url, body })
    if (url === '/api/health') {
      return new Response(JSON.stringify(handlers.health ?? { status: 'ok', llm_configured: true, llm_model: 'test-model', bts_api: { reachable: true, latest_month: '2026-07', source_type: 'public_api', url: 'u', retrieved_at: 't' } }))
    }
    if (url.startsWith('/api/demo/')) return new Response(JSON.stringify({ mode: 'demo', label: 'Deterministic demo - AI agent not used.', scenario: 'q1', question: 'q', caption: 'c', evidence: R.evidence, sources: [], warnings: [] }))
    return handlers.chat!(body!, n++)
  })
  vi.stubGlobal('fetch', fetchMock)
  return calls
}

const json = (obj: unknown, status = 200) => new Response(JSON.stringify(obj), { status })

async function send(text: string, label = 'Ask about US airports', button = 'Ask') {
  fireEvent.change(screen.getByLabelText(label), { target: { value: text } })
  fireEvent.click(screen.getByRole('button', { name: button }))
}

describe('conversation behaviour', () => {
  it('keeps the session id for follow-ups and resets it for a new conversation', async () => {
    const calls = mockBackend({ chat: () => json({ ...R, session_id: '11111111-1111-4111-8111-111111111111' }) })
    render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())

    await send('first question')
    await waitFor(() => expect(screen.getAllByRole('region', { name: 'Airport ranking' }).length).toBe(1))
    await send('follow-up')
    await waitFor(() => expect(screen.getAllByRole('region', { name: 'Airport ranking' }).length).toBe(2))

    const chats = calls.filter((c) => c.url === '/api/chat')
    expect(chats[0].body!.session_id).toBeNull()
    expect(chats[1].body!.session_id).toBe('11111111-1111-4111-8111-111111111111')

    fireEvent.click(screen.getByRole('button', { name: 'New conversation' }))
    await send('fresh start')
    await waitFor(() => expect(calls.filter((c) => c.url === '/api/chat').length).toBe(3))
    expect(calls.filter((c) => c.url === '/api/chat')[2].body!.session_id).toBeNull()
  })

  it('shows loading feedback and blocks duplicate submissions', async () => {
    let release!: () => void
    const calls = mockBackend({ chat: () => new Promise<Response>((res) => { release = () => res(json(R)) }) })
    render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())

    await send('slow question')
    expect(await screen.findByText(/Analyzing public aviation data/)).toBeTruthy()
    expect((screen.getByLabelText('Ask about US airports') as HTMLTextAreaElement).disabled).toBe(true)
    expect((screen.getByRole('button', { name: 'Ask' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.submit(screen.getByLabelText('Ask about US airports').closest('form')!) // second attempt while pending
    expect(screen.getByRole('button', { name: 'New conversation' }).hasAttribute('disabled')).toBe(true)
    expect(calls.filter((c) => c.url === '/api/chat').length).toBe(1)

    await act(async () => release())
    await waitFor(() => expect(screen.queryByText(/Analyzing public aviation data/)).toBeNull())
  })

  it('explains HTTP errors and retries the same question', async () => {
    const calls = mockBackend({
      chat: (_b, n) => (n === 0 ? json({ detail: 'The language model call failed (APIError, ref abc).' }, 502) : json(R)),
    })
    render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())

    await send('question')
    expect(await screen.findByText('The language model did not respond')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    await waitFor(() => expect(screen.getAllByRole('region', { name: 'Airport ranking' }).length).toBe(1))
    expect(calls.filter((c) => c.url === '/api/chat').map((c) => c.body!.message)).toEqual(['question', 'question'])
  })

  it('409 asks for a new conversation without a retry button', async () => {
    mockBackend({ chat: () => json({ detail: 'limit' }, 409) })
    render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())
    await send('q')
    expect(await screen.findByText('This conversation is full')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Try again' })).toBeNull()
  })

  it('without an API key, shows the labelled deterministic demo and disables free-form input', async () => {
    const calls = mockBackend({ health: { status: 'ok', llm_configured: false, llm_model: 'm', bts_api: { reachable: false, source_type: 'public_api', url: 'u', retrieved_at: 't' } } })
    render(<App />)
    expect(await screen.findByText(/Deterministic demo. The AI assistant is not configured/)).toBeTruthy()
    expect((screen.getByLabelText('Ask about US airports') as HTMLTextAreaElement).disabled).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: /Which airports in New England/ }))
    await waitFor(() => expect(calls.some((c) => c.url === '/api/demo/q1')).toBe(true))
    expect(await screen.findByText(/The AI assistant was not used; this is a fixed example analysis/)).toBeTruthy()
    expect(calls.some((c) => c.url === '/api/chat')).toBe(false)
  })
})

describe('UI language toggle (EN | עברית)', () => {
  afterEach(() => {
    try {
      localStorage.clear()
    } catch {
      // ignore
    }
    document.documentElement.removeAttribute('dir')
    document.documentElement.removeAttribute('lang')
  })

  const root = () => document.querySelector('.app') as HTMLElement

  it('defaults to English LTR and switches the static UI to Hebrew RTL and back', async () => {
    mockBackend({ chat: () => json(R) })
    render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())
    expect(root().getAttribute('dir')).toBe('ltr')
    expect(root().getAttribute('lang')).toBe('en')
    expect(screen.getByRole('heading', { name: 'Airport Investment Research' })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'עברית' }))

    expect(root().getAttribute('dir')).toBe('rtl')
    expect(root().getAttribute('lang')).toBe('he')
    expect(document.documentElement.dir).toBe('rtl')
    expect(screen.getByRole('heading', { name: 'מחקר השקעות בשדות תעופה' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'שיחה חדשה' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'שאל' })).toBeTruthy()
    expect(screen.getByLabelText('שאלו על שדות תעופה בארה"ב')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'עברית' }).getAttribute('aria-pressed')).toBe('true')

    fireEvent.click(screen.getByRole('button', { name: 'EN' }))
    expect(root().getAttribute('dir')).toBe('ltr')
    expect(screen.getByRole('button', { name: 'Ask' })).toBeTruthy()
  })

  it('keeps the conversation, session id and evidence when switching; translates evidence labels, not numbers or the AI reply', async () => {
    const calls = mockBackend({ chat: () => json({ ...R, session_id: '22222222-2222-4222-8222-222222222222' }) })
    render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())
    await send('rank them')
    const strip = await screen.findByRole('region', { name: 'Airport ranking' })
    const art = R.evidence[0].artifact!
    if (art.result_type !== 'ranking') throw new Error('fixture')
    const top = art.data.airports[0]
    const englishRow = within(strip).getByText(top.airport).closest('tr')!.textContent

    fireEvent.click(screen.getByRole('button', { name: 'עברית' }))

    const heStrip = screen.getByRole('region', { name: 'דירוג שדות תעופה' })
    expect(within(heStrip).getByRole('columnheader', { name: 'דירוג' })).toBeTruthy()
    expect(within(heStrip).getAllByText('מדגם קטן').length).toBeGreaterThan(0)
    // Airport codes and numbers are unchanged.
    const heRow = within(heStrip).getByText(top.airport).closest('tr')!
    expect(heRow.textContent).toContain(top.score!.toFixed(1))
    expect(englishRow).toContain(top.score!.toFixed(1))
    // The user's question and the AI reply are shown exactly as before.
    expect(screen.getByText('rank them')).toBeTruthy()
    expect(screen.getByText(/ranks first in this fictional group/)).toBeTruthy()

    await send('ועכשיו רק מרכזים בינוניים', 'שאלו על שדות תעופה בארה"ב', 'שאל')
    await waitFor(() => expect(calls.filter((c) => c.url === '/api/chat').length).toBe(2))
    const second = calls.filter((c) => c.url === '/api/chat')[1].body!
    expect(second.session_id).toBe('22222222-2222-4222-8222-222222222222')
    expect(second.message).toBe('ועכשיו רק מרכזים בינוניים')
  })

  it('translates errors and statuses; Hebrew examples are sent as displayed', async () => {
    const calls = mockBackend({ chat: () => json({ detail: 'The language model call failed (APIError, ref x).' }, 502) })
    render(<App />)
    await waitFor(() => expect(screen.getByText(/Model test-model/)).toBeTruthy())
    fireEvent.click(screen.getByRole('button', { name: 'עברית' }))

    fireEvent.click(screen.getByRole('button', { name: /אילו שדות תעופה בניו אינגלנד/ }))
    expect(await screen.findByText('מודל השפה לא הגיב')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'נסו שוב' })).toBeTruthy()
    expect(calls.find((c) => c.url === '/api/chat')!.body!.message).toMatch(/^אילו שדות תעופה בניו אינגלנד/)

    fireEvent.click(screen.getByRole('button', { name: 'EN' }))
    expect(screen.getByText('The language model did not respond')).toBeTruthy() // same turn, re-rendered
  })

  it('renders evidence views in Hebrew for all four analysis types', () => {
    for (const [fixture, title] of [[R, 'דירוג שדות תעופה'], [C, 'השוואת שדות תעופה'], [L, 'שיעור טיסות ארוכות'], [P, 'מדדי לחץ ביקוש']] as const) {
      render(
        <LangContext.Provider value={{ lang: 'he', t: DICTS.he }}>
          <Message turn={{ kind: 'assistant', id: 'x', response: fixture }} onRetry={() => {}} />
        </LangContext.Provider>,
      )
      expect(screen.getByRole('region', { name: title })).toBeTruthy()
      cleanup()
    }
    render(
      <LangContext.Provider value={{ lang: 'he', t: DICTS.he }}>
        <Message turn={{ kind: 'assistant', id: 'x', response: P }} onRetry={() => {}} />
      </LangContext.Provider>,
    )
    expect(screen.getByText('ביקוש שאינו נענה: לא נמדד')).toBeTruthy()
    expect(screen.getByText('ביקוש נצפה')).toBeTruthy()
  })

  it('notes when the reply language differs from the interface language, and only then', () => {
    const hebrewReply = { ...R, reply_markdown: 'BGR מוביל בדירוג. הציונים יחסיים לקבוצה.' }
    const withLang = (lang: 'en' | 'he', response: ChatResponse) =>
      render(
        <LangContext.Provider value={{ lang, t: DICTS[lang] }}>
          <Message turn={{ kind: 'assistant', id: 'x', response }} onRetry={() => {}} />
        </LangContext.Provider>,
      )

    withLang('en', hebrewReply)
    expect(screen.getByText(/The assistant replied in the language of your question/)).toBeTruthy()
    expect(screen.getByText('BGR מוביל בדירוג. הציונים יחסיים לקבוצה.')).toBeTruthy() // reply not translated
    cleanup()

    withLang('he', hebrewReply)
    expect(screen.queryByText(/העוזר ענה בשפה שבה נשאלה השאלה/)).toBeNull()
    cleanup()

    withLang('he', R) // English reply under the Hebrew UI
    expect(screen.getByText(/העוזר ענה בשפה שבה נשאלה השאלה/)).toBeTruthy()
    cleanup()

    withLang('en', R)
    expect(screen.queryByText(/The assistant replied in the language of your question/)).toBeNull()
  })

  it('remembers the chosen language', async () => {
    mockBackend({ chat: () => json(R) })
    const first = render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'עברית' }))
    first.unmount()
    render(<App />)
    expect(root().getAttribute('dir')).toBe('rtl')
  })
})
