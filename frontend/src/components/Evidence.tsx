import type { ReactNode } from 'react'
import { useT } from '../i18n'
import type { AirportsData, Artifact, EvidenceItem, MetricsData, Provenance } from '../types'
import { RankingView } from './Ranking'
import { ComparisonView } from './Comparison'
import { LongHaulView } from './LongHaul'
import { DemandProfileView } from './DemandProfile'
import { Orig } from './Orig'

function Cell({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="strip-cell">
      <span className="strip-cell-label">{label}</span>
      <span className="strip-cell-value">{children}</span>
    </div>
  )
}

export function Sources({ sources }: { sources: Provenance[] }) {
  const { t } = useT()
  if (!sources.length) return null
  return (
    <ul className="sources">
      {sources.map((p) => (
        <li key={`${p.source_type}-${p.name}-${p.observation_period}`} className={`source source-${p.source_type}`}>
          <span className="source-kind">{t.sources[p.source_type] ?? p.source_type}</span>
          <span className="source-name"><Orig>{p.name}</Orig></span>
          <span className="source-period">{t.period(p.observation_period)}</span>
          {p.retrieved_at && p.retrieved_at.length > 4 && (
            <span className="source-time">{t.retrieved(p.retrieved_at.replace('T', ' ').replace('+00:00', ' UTC'))}</span>
          )}
        </li>
      ))}
    </ul>
  )
}

function Body({ artifact }: { artifact: Artifact }) {
  switch (artifact.result_type) {
    case 'ranking':
      return <RankingView data={artifact.data} />
    case 'comparison':
      return <ComparisonView data={artifact.data} />
    case 'long_haul':
      return <LongHaulView data={artifact.data} />
    case 'demand_profile':
      return <DemandProfileView data={artifact.data} />
    case 'airports':
      return <AirportsView data={artifact.data} />
    case 'metrics':
      return <MetricsView data={artifact.data} />
  }
}

function AirportsView({ data }: { data: AirportsData }) {
  const { t } = useT()
  return (
    <div>
      <p className="interpretation"><Orig>{data.interpretation}</Orig></p>
      <table className="data-table compact">
        <thead>
          <tr><th>{t.colCode}</th><th>{t.colAirport}</th><th>{t.colState}</th><th>{t.colSize}</th></tr>
        </thead>
        <tbody>
          {data.airports.map((a) => (
            <tr key={a.code}>
              <td className="code">{a.code}</td>
              <td><Orig>{a.name}</Orig></td>
              <td className="code">{a.state}</td>
              <td>{a.hub ? t.hubs[a.hub] ?? a.hub : a.primary ? t.primary : t.nonPrimary}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MetricsView({ data }: { data: MetricsData }) {
  const { t } = useT()
  return (
    <ul className="metric-list">
      {data.metrics.map((m) => (
        <li key={m.id}>
          <strong>{t.metrics[m.id] ?? m.label}</strong> <span className="muted"><Orig>({m.source})</Orig></span>
          <div className="formula"><Orig>{m.formula}</Orig></div>
        </li>
      ))}
    </ul>
  )
}

export function EvidenceStrip({ item }: { item: EvidenceItem }) {
  const { t } = useT()
  if (item.status === 'error' || !item.artifact) {
    return (
      <section className="strip strip-error" aria-label={t.analysisError}>
        <header className="strip-head">
          <Cell label={t.analysis}><span className="code">{item.tool}</span></Cell>
          <Cell label={t.result}>{t.couldNotRun}</Cell>
        </header>
        <p className="strip-error-text">{item.error ? <Orig>{item.error}</Orig> : t.noResult}</p>
      </section>
    )
  }
  const a = item.artifact
  const windows = Object.entries(a.windows)
  const title = t.titles[a.result_type] ?? a.result_type
  return (
    <section className={`strip strip-${a.result_type}`} aria-label={title}>
      <header className="strip-head">
        <Cell label={t.analysis}>{title}</Cell>
        {windows.map(([k, v]) => (
          <Cell key={k} label={t.windows[k] ?? k}><span className="num-text">{v}</span></Cell>
        ))}
        <Cell label={t.confidence}>
          <span className={`confidence confidence-${a.confidence}`}>{t.confidenceLevels[a.confidence] ?? a.confidence}</span>
        </Cell>
      </header>
      <div className="strip-body">
        <Body artifact={a} />
      </div>
      {(a.warnings.length > 0 || a.coverage_notes.length > 0 || a.provenance.length > 0) && (
        <details className="strip-notes">
          <summary>
            {t.sourcesAndLimits}
            {a.warnings.length > 0 && <span className="count-badge">{t.warningsCount(a.warnings.length)}</span>}
          </summary>
          {a.warnings.length > 0 && (
            <ul className="warning-list">
              {a.warnings.map((w) => <li key={w}><Orig>{w}</Orig></li>)}
            </ul>
          )}
          {a.coverage_notes.length > 0 && (
            <ul className="note-list">
              {a.coverage_notes.map((n) => <li key={n}><Orig>{n}</Orig></li>)}
            </ul>
          )}
          <Sources sources={a.provenance} />
        </details>
      )}
    </section>
  )
}
