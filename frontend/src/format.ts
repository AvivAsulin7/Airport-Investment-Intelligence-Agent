// Display formatting only. No aviation calculations happen in the frontend (D-028).
// Numbers use Western digits and en-US grouping in both UI languages; labels live in i18n.ts.

const nf0 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const nf1 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1, minimumFractionDigits: 1 })

export const DASH = '–'

export function pct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined) return DASH
  return `${(v * 100).toFixed(digits)}%`
}

export function signedPct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined) return DASH
  const s = (v * 100).toFixed(digits)
  return v > 0 ? `+${s}%` : `${s}%`
}

export function count(v: number | null | undefined): string {
  return v === null || v === undefined ? DASH : nf0.format(v)
}

export function minutes(v: number | null | undefined, unit = 'min'): string {
  return v === null || v === undefined ? DASH : `${nf1.format(v)} ${unit}`
}

export function score(v: number | null | undefined): string {
  return v === null || v === undefined ? DASH : nf1.format(v)
}

/** Format a metric value by its unit as declared in the backend registry. */
export function metricValue(metric: string, v: number | null | undefined, minUnit = 'min'): string {
  if (metric.endsWith('_min')) return minutes(v, minUnit)
  if (metric.endsWith('_t12m')) return count(v)
  if (metric.endsWith('growth')) return signedPct(v)
  return pct(v)
}
