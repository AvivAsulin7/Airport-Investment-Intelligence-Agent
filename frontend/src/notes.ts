import type { EvidenceItem } from './types'

/** Small-sample and partial-coverage airports, read from the evidence (never from the prose). */
export function dataNotes(evidence: EvidenceItem[]) {
  const small = new Map<string, number>()
  const partial = new Set<string>()
  for (const ev of evidence) {
    const a = ev.artifact
    if (!a) continue
    if ('small_sample_airports' in a.data) {
      for (const s of a.data.small_sample_airports ?? []) small.set(s.airport, s.eligible_departures)
    }
    if (a.result_type === 'ranking') {
      for (const ap of a.data.airports) if (ap.flags.some((f) => f.startsWith('partial'))) partial.add(ap.airport)
    }
  }
  return { small: [...small.entries()], partial: [...partial] }
}

/** Rough script detection for display only: is the text mainly Hebrew or Latin? */
export function textLang(text: string): 'he' | 'en' | null {
  const hebrew = (text.match(/[֐-׿]/g) ?? []).length
  const latin = (text.match(/[A-Za-z]/g) ?? []).length
  if (hebrew + latin === 0) return null
  return hebrew > latin ? 'he' : 'en'
}

// Ids of the four assignment questions; their text lives in i18n.ts. They go through the real agent.
export const EXAMPLE_IDS = ['q1', 'q2', 'q3', 'q4'] as const
