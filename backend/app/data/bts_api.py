"""Live BTS Socrata (SODA) API client for monthly airport traffic (dataset r495-tyji).

Verified (Phase 3, A-012/A-023): the API's totals equal T-100 Segment (All Carriers)
sums over service classes F, G, L and P. Departures therefore include all-cargo
flights; seats and passengers come from passenger-capable classes.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.data.provenance import Provenance
from app.data.validation import month_range, parse_month, validate_airport_codes
from app.settings import Settings

DATASET_NAME = "BTS T-100 Segment Summary by Origin Airport (data.bts.gov r495-tyji)"
TRAFFIC_LIMITATIONS = (
    "Monthly totals by origin airport across all service classes (F, G, L, P).",
    "Departures include all-cargo flights; passenger-only departures are not available from this dataset.",
    "Passengers are enplaned segment passengers (connecting passengers count at each segment).",
    "Published with a reporting lag of about three months.",
)

# Whitelisted fields only; SoQL is built from these and validated codes/months (no injection).
_FIELDS = {
    "origin_airport_code": "airport",
    "reporting_month": "month",
    "total_passengers": "passengers",
    "total_seats": "seats",
    "total_departures": "departures",
    "domestic_departures": "domestic_departures",
    "outbound_international": "international_departures",
    "total_freight_lbs": "freight_lbs",
}
_NUMERIC = ("passengers", "seats", "departures", "domestic_departures", "international_departures", "freight_lbs")


class BtsApiUnavailable(RuntimeError):
    """The live API failed and no recorded fallback covers the request."""


@dataclass
class MonthlyTraffic:
    airport: str
    month: str
    passengers: float | None
    seats: float | None
    departures: float | None
    domestic_departures: float | None
    international_departures: float | None
    freight_lbs: float | None


@dataclass
class TrafficSeries:
    rows: list[MonthlyTraffic]
    requested_months: list[str]
    missing_months: dict[str, list[str]]
    provenance: Provenance
    warnings: list[str] = field(default_factory=list)


def _to_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_rows(raw_rows: list[dict]) -> tuple[list[MonthlyTraffic], list[str]]:
    """Map API rows to MonthlyTraffic, summing duplicate (airport, month) rows with a warning."""
    merged: dict[tuple[str, str], MonthlyTraffic] = {}
    warnings = []
    for raw in raw_rows:
        rec = {dst: raw.get(src) for src, dst in _FIELDS.items()}
        airport, month = rec["airport"], (rec["month"] or "")[:7]
        if not airport or not month:
            continue
        values = {k: _to_float(rec[k]) for k in _NUMERIC}
        key = (airport, month)
        if key in merged:
            warnings.append(f"duplicate API rows for {airport} {month} were summed")
            prev = merged[key]
            for k, v in values.items():
                old = getattr(prev, k)
                setattr(prev, k, None if old is None or v is None else old + v)
        else:
            merged[key] = MonthlyTraffic(airport=airport, month=month, **values)
    rows = sorted(merged.values(), key=lambda r: (r.airport, r.month))
    return rows, warnings


class BtsTrafficClient:
    def __init__(
        self,
        settings: Settings,
        client: httpx.Client | None = None,
        fallback_path: Path | None = None,
        cache_ttl_s: float = 3600,
        clock=time.monotonic,
    ):
        self._settings = settings
        self._client = client or httpx.Client(timeout=settings.http_timeout_s)
        self._fallback_path = fallback_path
        self._ttl = cache_ttl_s
        self._clock = clock
        self._cache: dict[str, tuple[float, object]] = {}

    def _get(self, params: dict) -> list[dict]:
        headers = {"X-App-Token": self._settings.bts_app_token} if self._settings.bts_app_token else {}
        last_exc: Exception | None = None
        for _ in range(2):  # one retry
            try:
                resp = self._client.get(self._settings.bts_api_base, params=params, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
        raise BtsApiUnavailable(type(last_exc).__name__) from last_exc

    def _cached(self, key: str):
        hit = self._cache.get(key)
        if hit and self._clock() - hit[0] < self._ttl:
            return hit[1]
        return None

    def latest_month(self) -> str:
        """Latest reporting month available in the live API (YYYY-MM)."""
        cached = self._cached("latest_month")
        if cached:
            return cached
        rows = self._get({"$select": "max(reporting_month) AS latest_month"})
        latest = (rows[0].get("latest_month") or "")[:7]
        parse_month(latest)
        self._cache["latest_month"] = (self._clock(), latest)
        return latest

    def fetch_monthly_traffic(self, airports: list[str], start_month: str, end_month: str) -> TrafficSeries:
        codes = validate_airport_codes(airports)
        months = month_range(start_month, end_month)
        key = json.dumps([codes, start_month, end_month])
        cached = self._cached(key)
        if cached:
            return _with_cache_status(cached, "memory_cache")

        in_list = ",".join(f"'{c}'" for c in codes)
        params = {
            "$select": ",".join(_FIELDS),
            "$where": (
                f"origin_airport_code in({in_list}) AND "
                f"reporting_month between '{start_month}-01T00:00:00' and '{end_month}-01T00:00:00'"
            ),
            "$order": "origin_airport_code,reporting_month",
            "$limit": "50000",
        }
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            raw = self._get(params)
            source_type, cache_status = "public_api", "live"
            url = str(httpx.URL(self._settings.bts_api_base, params=params))
        except BtsApiUnavailable:
            raw, retrieved_at = self._load_fallback(codes, months)
            source_type, cache_status = "recorded_api_fallback", "recorded_fallback"
            url = self._settings.bts_api_base

        rows, warnings = parse_rows(raw)
        rows = [r for r in rows if r.airport in codes and r.month in months]
        missing = {c: [m for m in months if not any(r.airport == c and r.month == m for r in rows)] for c in codes}
        missing = {c: ms for c, ms in missing.items() if ms}
        if cache_status == "recorded_fallback":
            warnings.append(f"Live BTS API unavailable; using a recorded API response retrieved {retrieved_at}.")
        series = TrafficSeries(
            rows=rows,
            requested_months=months,
            missing_months=missing,
            provenance=Provenance(
                source_type=source_type,
                name=DATASET_NAME,
                url=url,
                retrieval_method="SODA JSON API (SoQL query)",
                retrieved_at=retrieved_at,
                observation_period=f"{start_month}..{end_month}",
                limitations=TRAFFIC_LIMITATIONS,
                cache_status=cache_status,
            ),
            warnings=warnings,
        )
        if cache_status == "live":
            self._cache[key] = (self._clock(), series)
        return series

    def _load_fallback(self, codes: list[str], months: list[str]) -> tuple[list[dict], str]:
        if not self._fallback_path or not self._fallback_path.is_file():
            raise BtsApiUnavailable("live API failed and no recorded fallback exists")
        data = json.loads(self._fallback_path.read_text(encoding="utf-8"))
        rows = [r for r in data["rows"] if r.get("origin_airport_code") in codes]
        if not rows:
            raise BtsApiUnavailable("recorded fallback has no rows for the requested airports")
        return rows, data["retrieved_at"]


def _with_cache_status(series: TrafficSeries, status: str) -> TrafficSeries:
    prov = Provenance(**{**asdict(series.provenance), "cache_status": status})
    return TrafficSeries(series.rows, series.requested_months, series.missing_months, prov, list(series.warnings))


def check_connectivity(settings: Settings) -> dict:
    """Live connectivity check for /api/health; never raises on network errors."""
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        latest = BtsTrafficClient(settings, cache_ttl_s=0).latest_month()
        return {
            "reachable": True,
            "status_code": 200,
            "latest_month": latest,
            "source_type": "public_api",
            "url": settings.bts_api_base,
            "retrieved_at": retrieved_at,
        }
    except (BtsApiUnavailable, ValueError) as exc:
        return {
            "reachable": False,
            "error": type(exc).__name__,
            "source_type": "public_api",
            "url": settings.bts_api_base,
            "retrieved_at": retrieved_at,
        }
