"""Descriptive analyses: comparison, long-haul share, demand-pressure profile (pure functions)."""

from dataclasses import asdict, dataclass, field

from app.data.operations import ArrivalCauses
from app.data.routes import RouteSegment
from app.data.validation import PASSENGER_CLASSES, DataValidationError, validate_service_classes
from app.engine.kpis import MetricValue

# ---------------------------------------------------------------- comparison


@dataclass
class ComparisonResult:
    airports: list[str]
    metrics: list[str]
    values: dict[str, dict[str, dict]]  # metric -> airport -> MetricValue dict
    differences: dict[str, dict[str, dict]]  # metric -> airport -> {absolute, relative} vs the first airport
    baseline: str

    def to_dict(self) -> dict:
        return asdict(self)


def compare(per_airport: dict[str, dict[str, MetricValue]], airports: list[str], metrics: list[str]) -> ComparisonResult:
    """Side-by-side values; differences are computed vs the first airport (no composite score)."""
    if len(airports) < 2:
        raise DataValidationError("comparison needs at least 2 airports")
    base = airports[0]
    values, diffs = {}, {}
    for m in metrics:
        values[m] = {a: per_airport[a][m].to_dict() for a in airports}
        b = per_airport[base][m].value
        diffs[m] = {}
        for a in airports[1:]:
            v = per_airport[a][m].value
            if v is None or b is None:
                diffs[m][a] = {"absolute": None, "relative": None}
            else:
                diffs[m][a] = {"absolute": v - b, "relative": (v - b) / b if b != 0 else None}
    return ComparisonResult(list(airports), list(metrics), values, diffs, base)


# ---------------------------------------------------------------- long-haul share

MIN_THRESHOLD, MAX_THRESHOLD = 500, 10_000
BAND_EDGES = (1000, 2000, 3000, 4000, 5000, 6000)


@dataclass
class ShareResult:
    service_classes: list[str]
    numerator: float
    denominator: float
    share: float | None
    missing_reason: str | None = None


@dataclass
class LongHaulResult:
    origin: str
    threshold_miles: int
    primary: ShareResult
    all_classes: ShareResult
    by_class: dict[str, dict[str, float]]
    distance_bands: dict[str, dict[str, float]]
    definition: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _share(segments: list[RouteSegment], threshold: int, classes: frozenset[str]) -> ShareResult:
    den = sum(s.departures_performed for s in segments if s.service_class in classes)
    num = sum(s.departures_performed for s in segments if s.service_class in classes and s.distance_miles >= threshold)
    if den == 0:
        return ShareResult(sorted(classes), num, den, None, "no departures performed in these service classes")
    return ShareResult(sorted(classes), num, den, num / den)


def _band(distance: float) -> str:
    lo = 0
    for edge in BAND_EDGES:
        if distance < edge:
            return f"{lo:,}-{edge - 1:,}"
        lo = edge
    return f">={BAND_EDGES[-1]:,}"


def long_haul_share(
    origin: str, segments: list[RouteSegment], threshold_miles: int = 3000, service_classes=PASSENGER_CLASSES
) -> LongHaulResult:
    """Share of departures performed with DISTANCE >= threshold (statute miles, A-016).

    `segments` must contain ALL service classes for the origin so the all-class variant is exact.
    """
    if not isinstance(threshold_miles, int) or not MIN_THRESHOLD <= threshold_miles <= MAX_THRESHOLD:
        raise DataValidationError(f"threshold_miles must be an integer between {MIN_THRESHOLD} and {MAX_THRESHOLD}")
    classes = validate_service_classes(service_classes)
    all_classes = frozenset({"F", "G", "L", "P"})
    by_class: dict[str, dict[str, float]] = {}
    bands: dict[str, dict[str, float]] = {}
    for s in segments:
        c = by_class.setdefault(s.service_class, {"departures": 0.0, "long_haul_departures": 0.0})
        c["departures"] += s.departures_performed
        c["long_haul_departures"] += s.departures_performed if s.distance_miles >= threshold_miles else 0.0
        b = bands.setdefault(_band(s.distance_miles), {"selected_classes": 0.0, "all_classes": 0.0})
        b["all_classes"] += s.departures_performed
        b["selected_classes"] += s.departures_performed if s.service_class in classes else 0.0
    definition = (
        f"departures performed from {origin} with route DISTANCE >= {threshold_miles:,} statute miles "
        f"/ all departures performed from {origin}, service classes {', '.join(sorted(classes))}"
    )
    return LongHaulResult(
        origin,
        threshold_miles,
        _share(segments, threshold_miles, classes),
        _share(segments, threshold_miles, all_classes),
        dict(sorted(by_class.items())),
        dict(sorted(bands.items(), key=lambda kv: float(kv[0].lstrip(">=").split("-")[0].replace(",", "")))),
        definition,
    )


# ---------------------------------------------------------------- demand-pressure profile

UNMET_DEMAND_STATEMENT = (
    "Unmet flight demand is not measured: it is demand that did not materialize, so it does not appear in traffic "
    "or delay data. The indicators below are consistent with (or against) capacity pressure but do not prove it. "
    "Delays have many causes (weather, airline operations, national airspace system), load factor reflects airline "
    "capacity choices, and growth may be recovery rather than a shortfall."
)


@dataclass
class PeerPosition:
    value: float | None
    peers_with_data: int
    percentile: float | None  # % of peers with a strictly lower value
    rank_desc: int | None  # 1 = highest among subject + peers


@dataclass
class DemandProfile:
    airport: str
    peer_group: str
    peers: list[str]
    observed_demand: dict[str, dict]
    capacity_pressure: dict[str, PeerPosition]
    delay_causes: list[dict] | None
    unmet_demand: dict

    def to_dict(self) -> dict:
        return asdict(self)


def peer_position(value: float | None, peer_values: list[float | None]) -> PeerPosition:
    vals = [v for v in peer_values if v is not None]
    if value is None or len(vals) < 3:
        return PeerPosition(value, len(vals), None, None)
    lower = sum(1 for v in vals if v < value)
    higher = sum(1 for v in vals if v > value)
    return PeerPosition(value, len(vals), 100.0 * lower / len(vals), higher + 1)


CAUSE_FIELDS = {
    "carrier": "carrier_delay_min",
    "weather": "weather_delay_min",
    "national_airspace_system": "nas_delay_min",
    "security": "security_delay_min",
    "late_arriving_aircraft": "lateaircraft_delay_min",
}


def delay_cause_shares(arr: ArrivalCauses | None) -> list[dict] | None:
    """Share of arrival-delay minutes into the airport by reported cause, largest first."""
    if arr is None:
        return None
    minutes = {k: getattr(arr, f) for k, f in CAUSE_FIELDS.items()}
    total = sum(minutes.values())
    if total == 0:
        return None
    rows = [{"cause": k, "minutes": v, "share": v / total} for k, v in minutes.items()]
    return sorted(rows, key=lambda r: (-r["share"], r["cause"]))


def demand_profile(
    airport: str,
    peer_group: str,
    subject: dict[str, MetricValue],
    peers: dict[str, dict[str, MetricValue]],
    arrivals: ArrivalCauses | None,
    passengers_2019: MetricValue,
    pressure_metrics: tuple[str, ...] = ("load_factor", "delay_rate", "avg_taxi_out_min", "cancellation_rate"),
) -> DemandProfile:
    observed = {
        k: subject[k].to_dict() for k in ("passengers_t12m", "passenger_growth", "departures_t12m", "departure_growth")
    }
    p19 = passengers_2019.to_dict()
    cur = subject["passengers_t12m"].value
    p19["t12m_vs_2019"] = cur / passengers_2019.value - 1 if cur and passengers_2019.value else None
    observed["passengers_2019"] = p19
    pressure = {m: peer_position(subject[m].value, [p[m].value for p in peers.values()]) for m in pressure_metrics}
    return DemandProfile(
        airport,
        peer_group,
        sorted(peers),
        observed,
        pressure,
        delay_cause_shares(arrivals),
        {"measured": False, "statement": UNMET_DEMAND_STATEMENT},
    )
