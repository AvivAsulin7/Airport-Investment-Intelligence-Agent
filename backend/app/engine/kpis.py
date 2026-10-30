"""KPI calculations from Phase 5 data-layer records (exact definitions: architecture.md §6.0a, P-029)."""

from dataclasses import asdict, dataclass, field

from app.data.bts_api import MonthlyTraffic
from app.data.operations import DepartureCounts
from app.data.validation import month_range, shift_month

DEFAULT_MIN_FLIGHTS_WARNING = 300


@dataclass
class MetricValue:
    metric: str
    value: float | None
    numerator: float | None = None
    denominator: float | None = None
    window: str | None = None
    missing_reason: str | None = None
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TrafficWindows:
    latest: str
    current: tuple[str, ...]
    prior: tuple[str, ...]

    @property
    def current_label(self) -> str:
        return f"{self.current[0]}..{self.current[-1]}"

    @property
    def prior_label(self) -> str:
        return f"{self.prior[0]}..{self.prior[-1]}"


def traffic_windows(latest_month: str) -> TrafficWindows:
    """T12M = latest 12 months ending at latest_month; prior = the 12 months before."""
    current = month_range(shift_month(latest_month, -11), latest_month)
    prior = month_range(shift_month(latest_month, -23), shift_month(latest_month, -12))
    return TrafficWindows(latest_month, tuple(current), tuple(prior))


def _window_sum(rows: dict[str, MonthlyTraffic], months, field_name: str) -> tuple[float | None, str | None]:
    missing = [m for m in months if m not in rows or getattr(rows[m], field_name) is None]
    if missing:
        return None, f"missing {field_name} for {len(missing)} month(s): {', '.join(missing)}"
    return sum(getattr(rows[m], field_name) for m in months), None


def _growth(metric: str, rows, w: TrafficWindows, field_name: str) -> MetricValue:
    label = f"{w.current_label} vs {w.prior_label}"
    cur, why_cur = _window_sum(rows, w.current, field_name)
    prev, why_prev = _window_sum(rows, w.prior, field_name)
    if why_cur or why_prev:
        return MetricValue(metric, None, cur, prev, label, why_cur or why_prev)
    if prev == 0:
        return MetricValue(metric, None, cur, prev, label, "no traffic in the prior window")
    return MetricValue(metric, cur / prev - 1, cur, prev, label)


def traffic_kpis(monthly: list[MonthlyTraffic], w: TrafficWindows) -> dict[str, MetricValue]:
    """Passenger growth, departure growth, load factor and T12M volumes for one airport."""
    rows = {r.month: r for r in monthly}
    out = {
        "passenger_growth": _growth("passenger_growth", rows, w, "passengers"),
        "departure_growth": _growth("departure_growth", rows, w, "departures"),
    }
    pax, why_pax = _window_sum(rows, w.current, "passengers")
    seats, why_seats = _window_sum(rows, w.current, "seats")
    if why_pax or why_seats:
        out["load_factor"] = MetricValue("load_factor", None, pax, seats, w.current_label, why_pax or why_seats)
    elif seats == 0:
        out["load_factor"] = MetricValue("load_factor", None, pax, seats, w.current_label, "no seats reported")
    else:
        out["load_factor"] = MetricValue("load_factor", pax / seats, pax, seats, w.current_label)
    out["passengers_t12m"] = MetricValue("passengers_t12m", pax, window=w.current_label, missing_reason=why_pax)
    deps, why_deps = _window_sum(rows, w.current, "departures")
    out["departures_t12m"] = MetricValue("departures_t12m", deps, window=w.current_label, missing_reason=why_deps)
    return out


def operational_kpis(
    counts: DepartureCounts | None, period: str, min_flights_warning: int = DEFAULT_MIN_FLIGHTS_WARNING
) -> dict[str, MetricValue]:
    """Delay rate, cancellation rate, taxi-out and average departure delay for one airport."""
    ids = ("delay_rate", "cancellation_rate", "avg_taxi_out_min", "avg_dep_delay_min")
    if counts is None:
        reason = "airport not served by BTS reporting carriers in the on-time dataset"
        return {i: MetricValue(i, None, window=period, missing_reason=reason) for i in ids}

    flags = []
    if counts.depdel15_eligible < min_flights_warning:
        flags.append(f"low_sample: {counts.depdel15_eligible} departed flights < {min_flights_warning}")

    def ratio(metric, num, den, empty_reason):
        if den == 0:
            return MetricValue(metric, None, num, den, period, empty_reason)
        return MetricValue(metric, num / den, num, den, period, flags=list(flags))

    return {
        "delay_rate": ratio("delay_rate", counts.depdel15_delayed, counts.depdel15_eligible, "no eligible departures"),
        "cancellation_rate": ratio("cancellation_rate", counts.cancelled, counts.rows, "no scheduled departures"),
        "avg_taxi_out_min": ratio("avg_taxi_out_min", counts.taxi_out_sum_min, counts.taxi_out_n, "no taxi-out records"),
        "avg_dep_delay_min": ratio("avg_dep_delay_min", counts.dep_delay_sum_min, counts.dep_delay_n, "no departure-delay records"),
    }
