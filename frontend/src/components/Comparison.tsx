import { useT } from '../i18n'
import type { ComparisonData } from '../types'
import { count, metricValue, signedPct } from '../format'
import { Orig } from './Orig'

export function ComparisonView({ data }: { data: ComparisonData }) {
  const { t } = useT()
  const others = data.airports.filter((a) => a !== data.baseline)
  const small = new Set(data.small_sample_airports.map((s) => s.airport))

  /** Backend-computed absolute difference, shown in the metric's own unit (formatting only). */
  const absolute = (metric: string, v: number | null) => {
    if (v === null) return '–'
    const sign = v > 0 ? '+' : ''
    if (metric.endsWith('_min')) return `${sign}${v.toFixed(1)} ${t.min}`
    if (metric.endsWith('_t12m')) return `${sign}${count(v)}`
    return `${sign}${(v * 100).toFixed(1)} ${t.pts}`
  }

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">{t.colMetric}</th>
            {data.airports.map((a) => (
              <th key={a} scope="col" className="num">
                <span className="code">{a}</span>
                {a === data.baseline && <span className="weight">{t.baseline}</span>}
                {small.has(a) && <span className="badge badge-sample">{t.badgeSmall}</span>}
              </th>
            ))}
            {others.map((a) => (
              <th key={`d-${a}`} scope="col" className="num">{t.versus(a, data.baseline)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.metrics.map((m) => (
            <tr key={m}>
              <th scope="row">{t.metrics[m] ?? m}</th>
              {data.airports.map((a) => {
                const v = data.values[m]?.[a]
                return (
                  <td key={a} className="num">
                    {metricValue(m, v?.value, t.min)}
                    {v?.denominator != null && v.numerator != null && !m.endsWith('_min') && (
                      <span className="fraction">{count(v.numerator)} / {count(v.denominator)}</span>
                    )}
                    {v?.missing_reason && <span className="missing" title={v.missing_reason}><Orig>{v.missing_reason}</Orig></span>}
                  </td>
                )
              })}
              {others.map((a) => {
                const d = data.differences[m]?.[a]
                return (
                  <td key={`d-${a}`} className="num diff">
                    {absolute(m, d?.absolute ?? null)}
                    <span className="fraction">{signedPct(d?.relative ?? null)} {t.relative}</span>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
