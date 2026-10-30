"""Airport reference and region resolution from the FAA enplanements snapshot.

Regions resolve by FAA region code (RO column) or by US state; membership comes
from the data itself, never from a hardcoded airport list.
"""

from dataclasses import dataclass

from app.data.provenance import Provenance
from app.data.snapshots import SnapshotStore
from app.data.validation import DataValidationError, validate_airport_codes

AIRPORTS_FILE = "airports_faa.csv"

# FAA administrative region codes as used in the RO column.
FAA_REGION_NAMES = {
    "AL": "Alaskan",
    "CE": "Central",
    "EA": "Eastern",
    "GL": "Great Lakes",
    "NE": "New England",
    "NM": "Northwest Mountain",
    "SO": "Southern",
    "SW": "Southwest",
    "WP": "Western-Pacific",
}

US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "district of columbia": "DC", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
    "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY", "puerto rico": "PR",
}

# Informal names with an approved default interpretation (P-011, D-040).
ALIASES = {
    "la": ("LAX", "Interpreted 'LA' as Los Angeles International (LAX); other Los Angeles-area airports are not included."),
}


@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    state: str
    faa_region: str
    service_level: str
    hub: str
    enplanements_current: int | None
    enplanements_prior: int | None

    @property
    def is_primary(self) -> bool:
        return self.service_level == "P"


@dataclass
class Resolution:
    airports: list[Airport]
    interpretation: str
    excluded_note: str | None = None


def _int(v: str) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


class AirportReference:
    def __init__(self, store: SnapshotStore):
        self._prov = store.provenance("airports")
        self._by_code = {
            r["code"]: Airport(
                code=r["code"],
                name=r["name"],
                city=r["city"],
                state=r["state"],
                faa_region=r["faa_region"],
                service_level=r["service_level"],
                hub=r["hub"],
                enplanements_current=_int(r["enplanements_current"]),
                enplanements_prior=_int(r["enplanements_prior"]),
            )
            for r in store.read_csv(AIRPORTS_FILE)
        }

    @property
    def provenance(self) -> Provenance:
        return self._prov

    def get(self, code: str) -> Airport | None:
        return self._by_code.get(code.strip().upper())

    def require(self, codes: list[str]) -> list[Airport]:
        cleaned = validate_airport_codes(codes)
        unknown = [c for c in cleaned if c not in self._by_code]
        if unknown:
            raise DataValidationError(f"airports not found in the FAA commercial-service list: {unknown}")
        return [self._by_code[c] for c in cleaned]

    def in_region(self, faa_region: str, primary_only: bool = True) -> list[Airport]:
        return self._filter(lambda a: a.faa_region == faa_region, primary_only)

    def in_states(self, states: list[str], primary_only: bool = True) -> list[Airport]:
        wanted = {s.upper() for s in states}
        return self._filter(lambda a: a.state in wanted, primary_only)

    def _filter(self, pred, primary_only: bool) -> list[Airport]:
        rows = [a for a in self._by_code.values() if pred(a) and (a.is_primary or not primary_only)]
        return sorted(rows, key=lambda a: (-(a.enplanements_current or 0), a.code))

    def resolve_region(self, query: str, primary_only: bool = True) -> Resolution:
        """Resolve an FAA region (name or code) or a US state (name or code) to airports."""
        q = query.strip().lower()
        region = next((c for c, n in FAA_REGION_NAMES.items() if q == n.lower()), None)
        if region is None and q.upper() in FAA_REGION_NAMES and q.upper() not in US_STATES.values():
            region = q.upper()
        note = "FAA primary commercial-service airports only (S/L = P)." if primary_only else None
        if region:
            airports = self.in_region(region, primary_only)
            states = sorted({a.state for a in self.in_region(region, primary_only=False)})
            return Resolution(airports, f"FAA {FAA_REGION_NAMES[region]} region (RO={region}; states {', '.join(states)})", note)
        state = US_STATES.get(q) or (q.upper() if q.upper() in US_STATES.values() else None)
        if state:
            return Resolution(self.in_states([state], primary_only), f"US state {state}", note)
        raise DataValidationError(f"unknown region or state: {query!r}")

    def search(self, query: str) -> Resolution:
        """Resolve a code, an approved alias, or a city/name fragment to candidate airports."""
        q = query.strip()
        if q.lower() in ALIASES:
            code, note = ALIASES[q.lower()]
            return Resolution([self._by_code[code]], note)
        if len(q) == 3 and q.upper() in self._by_code:
            return Resolution([self._by_code[q.upper()]], f"Airport code {q.upper()}")
        ql = q.lower()
        hits = [a for a in self._by_code.values() if ql in a.city.lower() or ql in a.name.lower()]
        hits.sort(key=lambda a: (-(a.enplanements_current or 0), a.code))
        if not hits:
            raise DataValidationError(f"no airport matches {query!r}")
        note = f"Matched {len(hits)} airport(s) by city/name '{q}'."
        return Resolution(hits, note)
