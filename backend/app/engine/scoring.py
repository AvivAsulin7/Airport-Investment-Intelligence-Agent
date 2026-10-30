"""Expansion-opportunity scoring v1 (D-039; architecture.md §7.1a–§7.1c).

Pure function over raw KPI values; no data access, no LLM. Scores are relative to
the candidate group and are NOT profitability forecasts or proof of capacity shortage.
"""

import math
from dataclasses import asdict, dataclass, field

from app.engine.registry import DEFAULT_WEIGHTS, SCORING_METRICS

MIN_VALUES_PER_KPI = 3
MIN_RANKED_AIRPORTS = 3
DEFAULT_MIN_COVERAGE = 0.60
MAX_WEIGHTED_METRICS = 7
TIE_EPS = 1e-9
LOG_SCALED = frozenset({"passengers_t12m"})

INTERPRETATION = (
    "Scores are relative expansion-opportunity signals within this candidate group (min-max per KPI). "
    "A high relative score means stronger demand-pressure indicators than the other airports in this group; "
    "it is a lead for further analysis, not a verified investment opportunity. "
    "Scores are not profitability forecasts and do not prove a terminal capacity shortage. "
    "Adding or removing airports can change other airports' scores and order. "
    "Scores with different KPI coverage are not perfectly comparable, and airports flagged as small samples "
    "rest on few flights."
)


class ScoringInputError(ValueError):
    pass


@dataclass
class KpiRange:
    metric: str
    weight: float
    low: float | None
    high: float | None
    n_values: int
    usable: bool
    note: str | None = None


@dataclass
class KpiContribution:
    raw: float | None
    normalized: float | None
    weight: float
    contribution: float | None


@dataclass
class AirportScore:
    airport: str
    status: str  # "ranked" | "insufficient_data" | "not_ranked"
    rank: int | None
    score: float | None
    coverage: float
    flags: list[str]
    kpis: dict[str, KpiContribution]


@dataclass
class RankingResult:
    status: str  # "ranked" | "not_ranked"
    reason: str | None
    airports: list[AirportScore]
    weights_used: dict[str, float]
    ranges: list[KpiRange]
    warnings: list[str] = field(default_factory=list)
    rank_changes: dict[str, int] = field(default_factory=dict)
    interpretation: str = INTERPRETATION

    def to_dict(self) -> dict:
        return asdict(self)


def validate_weights(weights: dict[str, float] | None) -> dict[str, float]:
    """Return positive weights normalized to sum 1; reject unknown, negative or all-zero weights."""
    weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    unknown = sorted(set(weights) - SCORING_METRICS)
    if unknown:
        raise ScoringInputError(f"unknown metrics {unknown}; allowed: {sorted(SCORING_METRICS)}")
    for k, v in weights.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0:
            raise ScoringInputError(f"weight for {k} must be a finite number >= 0")
    positive = {k: float(v) for k, v in weights.items() if v > 0}
    if not positive:
        raise ScoringInputError("at least one KPI weight must be > 0")
    if len(positive) > MAX_WEIGHTED_METRICS:
        raise ScoringInputError(f"at most {MAX_WEIGHTED_METRICS} weighted metrics")
    total = sum(positive.values())
    return {k: v / total for k, v in positive.items()}


def _transform(metric: str, value: float | None) -> float | None:
    if value is None:
        return None
    if metric in LOG_SCALED:
        return math.log10(value) if value > 0 else None
    return value


def rank_airports(
    values: dict[str, dict[str, float | None]],
    weights: dict[str, float] | None = None,
    *,
    min_coverage: float = DEFAULT_MIN_COVERAGE,
    tiebreak: dict[str, float] | None = None,
    flags: dict[str, list[str]] | None = None,
    previous_ranks: dict[str, int] | None = None,
) -> RankingResult:
    """Rank candidate airports. `values[airport][metric]` is the raw KPI value or None (missing)."""
    if not 0.5 <= min_coverage <= 1.0:
        raise ScoringInputError("min_coverage must be between 0.5 and 1.0")
    w = validate_weights(weights)
    airports = sorted(values)
    tiebreak = tiebreak or {}
    flags = flags or {}
    warnings: list[str] = []

    # 1-4. KPI usability and normalization ranges over the whole candidate group.
    ranges: list[KpiRange] = []
    transformed = {k: {a: _transform(k, values[a].get(k)) for a in airports} for k in w}
    usable = {}
    for k in w:
        present = [v for v in transformed[k].values() if v is not None]
        if len(present) < MIN_VALUES_PER_KPI:
            ranges.append(KpiRange(k, w[k], None, None, len(present), False, f"fewer than {MIN_VALUES_PER_KPI} values"))
            warnings.append(f"KPI {k} dropped: only {len(present)} airport(s) have data")
            continue
        low, high = min(present), max(present)
        note = "KPI does not differentiate this group (all values equal); normalized to 50" if high == low else None
        if note:
            warnings.append(f"KPI {k}: all values equal")
        ranges.append(KpiRange(k, w[k], low, high, len(present), True, note))
        usable[k] = (low, high)

    # 5. Re-scale weights over usable KPIs.
    usable_total = sum(w[k] for k in usable)
    weights_used = {k: w[k] / usable_total for k in usable} if usable else {}

    scores: list[AirportScore] = []
    for a in airports:
        kpis, avail_w, weighted = {}, 0.0, 0.0
        for k in w:
            raw = values[a].get(k)
            if k not in usable:
                kpis[k] = KpiContribution(raw, None, 0.0, None)
                continue
            t = transformed[k][a]
            if t is None:
                kpis[k] = KpiContribution(raw, None, weights_used[k], None)
                continue
            low, high = usable[k]
            n = 50.0 if high == low else 100.0 * (t - low) / (high - low)
            kpis[k] = KpiContribution(raw, n, weights_used[k], None)
            avail_w += weights_used[k]
            weighted += weights_used[k] * n
        coverage = avail_w  # weights_used sums to 1
        score = weighted / avail_w if avail_w > 0 else None
        for k, c in kpis.items():
            if c.normalized is not None and avail_w > 0:
                c.contribution = c.weight * c.normalized / avail_w
        f = list(flags.get(a, []))
        if 0 < coverage < 1 - TIE_EPS:
            f.append(f"partial: coverage {coverage:.0%}")
        status = "ranked" if score is not None and coverage >= min_coverage - TIE_EPS else "insufficient_data"
        if status == "insufficient_data":  # listed with raw values, never scored (§7.1a step 9)
            score = None
            for c in kpis.values():
                c.contribution = None
        scores.append(AirportScore(a, status, None, score, coverage, f, kpis))

    def result(status, reason, rows):
        return RankingResult(status, reason, rows, weights_used, ranges, warnings)

    if not usable:
        return result("not_ranked", "no KPI has data for at least 3 airports", _unranked(scores))
    if len(airports) < MIN_RANKED_AIRPORTS:
        return result("not_ranked", f"ranking requires >= {MIN_RANKED_AIRPORTS} comparable airports", _unranked(scores))
    ranked = [s for s in scores if s.status == "ranked"]
    if len(ranked) < MIN_RANKED_AIRPORTS:
        return result(
            "not_ranked",
            f"only {len(ranked)} airport(s) reach {min_coverage:.0%} KPI coverage; ranking requires >= {MIN_RANKED_AIRPORTS}",
            _unranked(scores),
        )

    # 6. Order: score desc, then T12M passengers desc, then code asc (deterministic tie-break).
    ranked.sort(key=lambda s: (-s.score, -(tiebreak.get(s.airport) or 0.0), s.airport))
    for i, s in enumerate(ranked):
        s.rank = i + 1
        if i > 0 and abs(ranked[i - 1].score - s.score) < TIE_EPS:
            s.flags.append(f"tied score with {ranked[i - 1].airport} (tie-break: T12M passengers, then code)")
    insufficient = sorted((s for s in scores if s.status != "ranked"), key=lambda s: s.airport)
    out = result("ranked", None, ranked + insufficient)
    if previous_ranks:
        out.rank_changes = {s.airport: previous_ranks[s.airport] - s.rank for s in ranked if s.airport in previous_ranks}
    return out


def _unranked(scores: list[AirportScore]) -> list[AirportScore]:
    for s in scores:
        s.status, s.rank, s.score = "not_ranked", None, None
        for c in s.kpis.values():
            c.contribution = None
    return sorted(scores, key=lambda s: s.airport)
