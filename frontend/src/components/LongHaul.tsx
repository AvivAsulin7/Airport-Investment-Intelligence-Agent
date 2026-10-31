import { useT } from '../i18n'
import type { LongHaulData, Share } from '../types'
import { count, pct } from '../format'
import { Orig } from './Orig'

function Figure({ title, share }: { title: string; share: Share }) {
  const { t } = useT()
  return (
    <div className="figure">
      <div className="figure-value">{pct(share.share)}</div>
      <div className="figure-title">{title}</div>
      <div className="fraction">{t.ofDepartures(count(share.numerator), count(share.denominator))}</div>
      {share.missing_reason && <div className="missing"><Orig>{share.missing_reason}</Orig></div>}
    </div>
  )
}

export function LongHaulView({ data }: { data: LongHaulData }) {
  const { t } = useT()
  const bands = Object.entries(data.distance_bands)
  const widest = Math.max(1, ...bands.map(([, b]) => b.all_classes))
  const selected = data.primary.service_classes.join('+')
  return (
    <div>
      <div className="figures">
        <Figure title={t.selectedClasses(selected)} share={data.primary} />
        <Figure title={t.allClasses} share={data.all_classes} />
      </div>
      <p className="definition">{t.longHaulDefinition(count(data.threshold_miles), data.origin)}</p>
      <div className="two-col">
        <table className="data-table compact">
          <caption>{t.byClass}</caption>
          <thead>
            <tr><th scope="col">{t.colClass}</th><th scope="col" className="num">{t.colDepartures}</th><th scope="col" className="num">{t.colLongHaul}</th></tr>
          </thead>
          <tbody>
            {Object.entries(data.by_class).map(([c, v]) => (
              <tr key={c} className={data.primary.service_classes.includes(c) ? '' : 'row-other'}>
                <td><span className="code">{c}</span> {t.classes[c] ?? ''}</td>
                <td className="num">{count(v.departures)}</td>
                <td className="num">{count(v.long_haul_departures)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div>
          <div className="caption">{t.byDistance}</div>
          <ul className="bands">
            {bands.map(([band, b]) => (
              <li key={band}>
                <span className="band-label">{band}</span>
                <span className="band-track">
                  <span className="band-all" style={{ width: `${(100 * b.all_classes) / widest}%` }} />
                  <span className="band-selected" style={{ width: `${(100 * b.selected_classes) / widest}%` }} />
                </span>
                <span className="band-count">{count(b.selected_classes)} / {count(b.all_classes)}</span>
              </li>
            ))}
          </ul>
          <div className="legend">
            <span className="legend-selected">{t.legendSelected}</span>
            <span className="legend-all">{t.legendAll}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
