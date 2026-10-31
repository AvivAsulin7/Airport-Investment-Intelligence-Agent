import { useT } from '../i18n'
import type { RankingData } from '../types'
import { metricValue, pct, score } from '../format'
import { Orig } from './Orig'

export function RankingView({ data }: { data: RankingData }) {
  const { t } = useT()
  const metrics = data.ranges.map((r) => r.metric)
  const hubs = data.candidate_group.hub_classes ?? {}

  const badges = (flags: string[]) =>
    flags.map((f) => {
      if (f.startsWith('low_sample')) return <span key={f} className="badge badge-sample" title={f}>{t.badgeSmall}</span>
      if (f.startsWith('partial')) return <span key={f} className="badge badge-partial" title={f}>{t.badgePartial}</span>
      if (f.startsWith('tied')) return <span key={f} className="badge" title={f}>{t.badgeTied}</span>
      return null
    })

  return (
    <div>
      <p className="interpretation">
        <Orig>{data.candidate_group.interpretation}</Orig>
        {data.candidate_group.hub_filter && (
          <> {t.filteredTo(data.candidate_group.hub_filter.hub_classes.map((h) => t.hubs[h] ?? h).join(', '))}</>
        )}
      </p>
      {data.status !== 'ranked' && <p className="callout callout-limit">{t.notRanked('')}<Orig>{data.reason}</Orig></p>}
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">{t.colRank}</th>
              <th scope="col">{t.colAirport}</th>
              <th scope="col" className="col-score">{t.colScore}</th>
              <th scope="col">{t.colCoverage}</th>
              {metrics.map((m) => (
                <th key={m} scope="col" className="num">
                  {t.metrics[m] ?? m}
                  <span className="weight">{t.weight(pct(data.weights_used[m] ?? 0, 0))}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.airports.map((a) => (
              <tr key={a.airport} className={a.status === 'ranked' ? '' : 'row-unscored'}>
                <td className="num">{a.rank ?? '–'}</td>
                <td>
                  <span className="code">{a.airport}</span>
                  {hubs[a.airport] && <span className="hub">{t.hubs[hubs[a.airport] ?? ''] ?? hubs[a.airport]}</span>}
                  <div className="badges">{badges(a.flags)}</div>
                </td>
                <td className="col-score">
                  {a.score === null ? (
                    <span className="muted">{a.status === 'insufficient_data' ? t.notScored : '–'}</span>
                  ) : (
                    <div className="scorebar" role="img" aria-label={t.scoreAria(score(a.score))}>
                      <span className="scorebar-fill" style={{ width: `${Math.max(0, Math.min(100, a.score))}%` }} />
                      <span className="scorebar-value">{score(a.score)}</span>
                    </div>
                  )}
                </td>
                <td className="num">{pct(a.coverage, 0)}</td>
                {metrics.map((m) => (
                  <td key={m} className="num">{metricValue(m, a.kpis[m]?.raw, t.min)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="callout callout-limit">{t.rankingNote}</p>
    </div>
  )
}
