"""Metric registry: ids, formulas, units, scoring direction and source (architecture.md §6, P-029)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDef:
    id: str
    label: str
    formula: str
    unit: str
    source: str
    category: str  # "direct" (measured) or "proxy" (used as a pressure indicator)
    higher_is_stronger: bool = True
    scoring: bool = False  # allowed in the expansion-opportunity score


METRICS: dict[str, MetricDef] = {
    m.id: m
    for m in [
        MetricDef(
            "passenger_growth", "Passenger growth (T12M vs prior 12 months)",
            "sum(total_passengers, last 12 months) / sum(total_passengers, previous 12 months) - 1",
            "ratio", "BTS API (live)", "direct", scoring=True,
        ),
        MetricDef(
            "load_factor", "Seat load factor (T12M)",
            "sum(total_passengers) / sum(total_seats), last 12 months. Airline seat utilization, not terminal utilization.",
            "ratio", "BTS API (live)", "proxy", scoring=True,
        ),
        MetricDef(
            "departure_growth", "Flight (departure) growth (T12M vs prior 12 months)",
            "sum(total_departures, last 12 months) / sum(total_departures, previous 12 months) - 1; "
            "includes all-cargo departures",
            "ratio", "BTS API (live)", "direct", scoring=True,
        ),
        MetricDef(
            "delay_rate", "Departure delay rate (>=15 min)",
            "count(Origin=X, Cancelled=0, DepDel15=1) / count(Origin=X, Cancelled=0, DepDel15 present)",
            "ratio", "BTS on-time snapshot", "proxy", scoring=True,
        ),
        MetricDef(
            "avg_taxi_out_min", "Average taxi-out time",
            "mean(TaxiOut) over Origin=X, Cancelled=0, TaxiOut present",
            "minutes", "BTS on-time snapshot", "proxy", scoring=True,
        ),
        MetricDef(
            "cancellation_rate", "Cancellation rate",
            "count(Origin=X, Cancelled=1) / count(Origin=X)",
            "ratio", "BTS on-time snapshot", "proxy", scoring=True,
        ),
        MetricDef(
            "passengers_t12m", "Enplaned passengers (T12M)",
            "sum(total_passengers, last 12 months); min-max normalized on log10 when used in scoring",
            "passengers", "BTS API (live)", "direct", scoring=True,
        ),
        MetricDef(
            "departures_t12m", "Departures performed (T12M, all service classes)",
            "sum(total_departures, last 12 months)", "departures", "BTS API (live)", "direct",
        ),
        MetricDef(
            "avg_dep_delay_min", "Average departure delay",
            "mean(DepDelay) over Origin=X, Cancelled=0, DepDelay present (early departures negative)",
            "minutes", "BTS on-time snapshot", "direct",
        ),
    ]
}

DEFAULT_WEIGHTS = {
    "passenger_growth": 0.30,
    "load_factor": 0.25,
    "departure_growth": 0.15,
    "delay_rate": 0.20,
    "avg_taxi_out_min": 0.10,
}
SCORING_METRICS = frozenset(m.id for m in METRICS.values() if m.scoring)
