import { useT } from '../i18n'
import type { DemandProfileData } from '../types'
import { count, metricValue, pct, signedPct } from '../format'
import { Orig } from './Orig'

export function DemandProfileView({ data }: { data: DemandProfileData }) {
  const { t } = useT()
  const o = data.observed_demand
  const p2019 = o.passengers_2019
  return (
    <div className="profile">
      <div className="profile-block">
        <h4>{t.observedDemand}</h4>
        <dl className="kv">
          <dt>{t.passengers12}</dt>
          <dd>{count(o.passengers_t12m?.value)}</dd>
          <dt>{t.passengerGrowth}</dt>
          <dd>{signedPct(o.passenger_growth?.value)}</dd>
          <dt>{t.departures12}</dt>
          <dd>{count(o.departures_t12m?.value)} <span className="muted">{t.inclCargo}</span></dd>
          <dt>{t.flightGrowth}</dt>
          <dd>{signedPct(o.departure_growth?.value)}</dd>
          <dt>{t.vs2019}</dt>
          <dd>{signedPct(p2019?.t12m_vs_2019 ?? null)} <span className="muted">{t.in2019(count(p2019?.value))}</span></dd>
        </dl>
      </div>

      <div className="profile-block">
        <h4>{t.pressureHeading(data.peers.length, data.peer_group)}</h4>
        <table className="data-table compact">
          <thead>
            <tr><th scope="col">{t.colIndicator}</th><th scope="col" className="num">{t.colValue}</th><th scope="col">{t.colPosition}</th></tr>
          </thead>
          <tbody>
            {Object.entries(data.capacity_pressure).map(([m, pos]) => (
              <tr key={m}>
                <th scope="row">{t.metrics[m] ?? m}</th>
                <td className="num">{metricValue(m, pos.value, t.min)}</td>
                <td>
                  {pos.percentile === null ? (
                    <span className="muted">{t.notEnoughPeers}</span>
                  ) : (
                    <div className="percentile" role="img" aria-label={t.peerAria(pos.percentile.toFixed(0))}>
                      <span className="percentile-track"><span className="percentile-mark" style={{ insetInlineStart: `${pos.percentile}%` }} /></span>
                      <span className="percentile-text">
                        {t.peerPosition(pos.rank_desc ?? 0, pos.peers_with_data + 1, pos.percentile.toFixed(0))}
                      </span>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="profile-block">
        <h4>{t.causesHeading(data.airport)}</h4>
        {data.delay_causes ? (
          <>
            <div className="stack" role="img" aria-label={t.causesAria}>
              {data.delay_causes.map((c) => (
                <span key={c.cause} className={`stack-seg cause-${c.cause}`} style={{ width: `${c.share * 100}%` }} />
              ))}
            </div>
            <ul className="stack-legend">
              {data.delay_causes.map((c) => (
                <li key={c.cause}>
                  <span className={`swatch cause-${c.cause}`} />
                  {t.causes[c.cause] ?? c.cause} <span className="num-text">{pct(c.share)}</span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="muted">{t.noCauses}</p>
        )}
      </div>

      <div className="profile-block unmet">
        <h4>{t.unmetHeading}</h4>
        <p>{t.unmetStatement ?? <Orig>{data.unmet_demand.statement}</Orig>}</p>
      </div>
    </div>
  )
}
