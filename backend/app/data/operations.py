"""Access to on-time operational counts (departure delays, cancellations, taxi-out, arrival causes).

Returns counts and sums per airport; rates are computed in the Phase 6 engine.
"""

from dataclasses import dataclass

from app.data.provenance import Provenance
from app.data.snapshots import SnapshotStore
from app.data.validation import validate_airport_codes

DEPARTURES_FILE = "ontime_departures.csv"
ARRIVALS_FILE = "ontime_arrival_causes.csv"


@dataclass(frozen=True)
class DepartureCounts:
    airport: str
    rows: int
    cancelled: int
    diverted: int
    depdel15_eligible: int
    depdel15_delayed: int
    taxi_out_n: int
    taxi_out_sum_min: float
    dep_delay_n: int
    dep_delay_sum_min: float


@dataclass(frozen=True)
class ArrivalCauses:
    airport: str
    arr_rows: int
    arr_cancelled: int
    arrdel15_delayed: int
    carrier_delay_min: float
    weather_delay_min: float
    nas_delay_min: float
    security_delay_min: float
    lateaircraft_delay_min: float


@dataclass
class OperationsResult:
    departures: dict[str, DepartureCounts | None]
    arrivals: dict[str, ArrivalCauses | None]
    observation_period: str
    provenance: Provenance


def _typed(cls, rec: dict):
    kwargs = {}
    for name, f in cls.__dataclass_fields__.items():
        v = rec[name]
        kwargs[name] = v if f.type is str else (int(float(v)) if f.type is int else float(v))
    return cls(**kwargs)


class OperationsData:
    def __init__(self, store: SnapshotStore):
        self._prov = store.provenance("ontime")
        self._dep = {r["airport"]: _typed(DepartureCounts, r) for r in store.read_csv(DEPARTURES_FILE)}
        self._arr = {r["airport"]: _typed(ArrivalCauses, r) for r in store.read_csv(ARRIVALS_FILE)}

    def get(self, airports: list[str]) -> OperationsResult:
        """Missing airports map to None (not covered by reporting carriers), never to zeros."""
        codes = validate_airport_codes(airports)
        return OperationsResult(
            departures={c: self._dep.get(c) for c in codes},
            arrivals={c: self._arr.get(c) for c in codes},
            observation_period=self._prov.observation_period,
            provenance=self._prov,
        )

    def all_airports(self) -> list[str]:
        """Airports with departure records (used later for peer comparisons)."""
        return sorted(self._dep)
