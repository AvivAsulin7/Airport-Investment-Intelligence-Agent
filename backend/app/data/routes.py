"""Access to T-100 route segments by origin airport, filtered by explicit service classes."""

from dataclasses import dataclass

from app.data.provenance import Provenance
from app.data.snapshots import SnapshotStore
from app.data.validation import validate_airport_codes, validate_service_classes

SEGMENTS_FILE = "t100_segments.csv"


@dataclass(frozen=True)
class RouteSegment:
    origin: str
    dest: str
    dest_country: str
    service_class: str
    distance_miles: float
    departures_performed: float
    departures_scheduled: float
    seats: float
    passengers: float
    freight_lbs: float


@dataclass
class RouteResult:
    origin: str
    service_classes: frozenset[str]
    segments: list[RouteSegment]
    observation_period: str
    provenance: Provenance


class RouteData:
    def __init__(self, store: SnapshotStore):
        self._prov = store.provenance("t100_segments")
        self._by_origin: dict[str, list[RouteSegment]] = {}
        for r in store.read_csv(SEGMENTS_FILE):
            seg = RouteSegment(
                origin=r["origin"],
                dest=r["dest"],
                dest_country=r["dest_country"],
                service_class=r["service_class"],
                **{
                    k: float(r[k])
                    for k in ("distance_miles", "departures_performed", "departures_scheduled", "seats", "passengers", "freight_lbs")
                },
            )
            self._by_origin.setdefault(seg.origin, []).append(seg)

    def segments_from(self, origin: str, service_classes) -> RouteResult:
        """Classes are required so passenger and cargo flights are never mixed silently."""
        [code] = validate_airport_codes([origin])
        classes = validate_service_classes(service_classes)
        segs = [s for s in self._by_origin.get(code, []) if s.service_class in classes]
        return RouteResult(code, classes, segs, self._prov.observation_period, self._prov)

    def classes_present(self, origin: str) -> dict[str, float]:
        """Departures performed per service class at an origin (to disclose the cargo share)."""
        [code] = validate_airport_codes([origin])
        out: dict[str, float] = {}
        for s in self._by_origin.get(code, []):
            out[s.service_class] = out.get(s.service_class, 0.0) + s.departures_performed
        return out
