"""Analytics service: fetches through the Phase 5 data layer, runs the pure engine, and returns
JSON-serializable results with provenance, windows, definitions, warnings and confidence.

Phase 7 tools will wrap these methods; nothing here depends on LangChain or an LLM.
"""

from app.data.layer import DataLayer
from app.data.provenance import Provenance
from app.data.validation import PASSENGER_CLASSES, DataValidationError, validate_airport_codes
from app.engine import FORMULA_VERSION
from app.engine.analyses import compare, demand_profile, long_haul_share
from app.engine.kpis import DEFAULT_MIN_FLIGHTS_WARNING, MetricValue, operational_kpis, traffic_kpis, traffic_windows
from app.engine.registry import METRICS
from app.engine.scoring import DEFAULT_MIN_COVERAGE, rank_airports

CONGESTION_METRICS = ["delay_rate", "cancellation_rate", "avg_taxi_out_min", "avg_dep_delay_min"]
VOLUME_METRICS = ["departures_t12m", "passengers_t12m"]
API_BATCH = 30
FAA_HUB_CLASSES = {"L": "large hub", "M": "medium hub", "S": "small hub", "N": "nonhub primary"}


def _envelope(result_type, data, provenance, windows, metrics, warnings, confidence, notes=None):
    seen, prov = set(), []
    for p in provenance:
        key = (p.source_type, p.name, p.observation_period)
        if key not in seen:
            seen.add(key)
            prov.append(p.to_dict())
    return {
        "result_type": result_type,
        "data": data,
        "provenance": prov,
        "windows": windows,
        "definitions": {m: METRICS[m].formula for m in metrics if m in METRICS},
        "warnings": list(dict.fromkeys(warnings)),
        "coverage_notes": notes or [],
        "confidence": confidence,
        "formula_version": FORMULA_VERSION,
    }


PERIOD_MISMATCH = (
    "Traffic metrics cover the last 12 months from the live BTS API; delay, cancellation and taxi-out metrics "
    "cover a single month from the on-time snapshot. Periods differ."
)


class AnalyticsService:
    def __init__(self, data: DataLayer, min_flights_warning: int = DEFAULT_MIN_FLIGHTS_WARNING):
        self.data = data
        self.min_flights_warning = min_flights_warning

    # ------------------------------------------------------------ shared KPI assembly

    def _traffic(self, codes: list[str]):
        latest = self.data.traffic.latest_month()
        w = traffic_windows(latest)
        rows, provs, warnings = {c: [] for c in codes}, [], []
        for i in range(0, len(codes), API_BATCH):
            series = self.data.traffic.fetch_monthly_traffic(codes[i : i + API_BATCH], w.prior[0], w.current[-1])
            for r in series.rows:
                rows[r.airport].append(r)
            provs.append(series.provenance)
            warnings += series.warnings
        return w, rows, provs, warnings

    def airport_kpis(self, codes: list[str]):
        codes = validate_airport_codes(codes)
        w, rows, provs, warnings = self._traffic(codes)
        ops = self.data.operations.get(codes)
        kpis: dict[str, dict[str, MetricValue]] = {}
        for c in codes:
            kpis[c] = traffic_kpis(rows[c], w)
            kpis[c].update(operational_kpis(ops.departures[c], ops.observation_period, self.min_flights_warning))
        windows = {
            "traffic_current": w.current_label,
            "traffic_prior": w.prior_label,
            "operations": ops.observation_period,
        }
        return kpis, windows, provs + [ops.provenance], warnings, ops

    @staticmethod
    def _missing_notes(kpis, metrics):
        return [
            f"{a} {m}: {mv.missing_reason}" for a, ms in kpis.items() for m in metrics
            if (mv := ms.get(m)) is not None and mv.value is None and mv.missing_reason
        ]

    def _small_samples(self, kpis: dict[str, dict[str, MetricValue]], codes: list[str], period: str):
        """Structured small-sample records plus matching top-level warnings (D-029, D-049).

        Kept at the envelope level so the warning survives any downstream summarization.
        """
        records, warnings = [], []
        for a in codes:
            mv = kpis[a]["delay_rate"]
            if any(f.startswith("low_sample") for f in mv.flags):
                n = int(mv.denominator)
                records.append({"airport": a, "eligible_departures": n, "threshold": self.min_flights_warning,
                                "period": period,
                                "affected_metrics": ["delay_rate", "cancellation_rate", "avg_taxi_out_min",
                                                     "avg_dep_delay_min"]})
                warnings.append(
                    f"Small sample: {a} has {n} eligible departures in {period} (< {self.min_flights_warning}); "
                    "its delay, cancellation and taxi-out values are statistically noisy. "
                    "Included with this warning, not excluded."
                )
        return records, warnings

    @staticmethod
    def _uses_fallback(provs: list[Provenance]) -> bool:
        return any(p.source_type == "recorded_api_fallback" for p in provs)

    # ------------------------------------------------------------ 1. ranking

    def rank(
        self,
        region: str | None = None,
        airports: list[str] | None = None,
        weights: dict[str, float] | None = None,
        min_coverage: float = DEFAULT_MIN_COVERAGE,
        primary_only: bool = True,
        previous_ranks: dict[str, int] | None = None,
        hub_classes: list[str] | None = None,
    ) -> dict:
        """Rank a region or an explicit list. `hub_classes` (FAA L/M/S/N) narrows the candidate group
        before scoring; the scoring methodology itself is unchanged (D-049)."""
        if bool(region) == bool(airports):
            raise DataValidationError("provide exactly one of region or airports")
        if region:
            res = self.data.airports.resolve_region(region, primary_only=primary_only)
            candidates, interpretation, note = res.airports, res.interpretation, res.excluded_note
        else:
            candidates = self.data.airports.require(airports)
            interpretation, note = "user-specified airports", None
        hub_filter = None
        if hub_classes:
            wanted = {h.strip().upper() for h in hub_classes}
            unknown = sorted(wanted - FAA_HUB_CLASSES.keys())
            if unknown:
                raise DataValidationError(f"unknown FAA hub classes {unknown}; allowed: {sorted(FAA_HUB_CLASSES)}")
            excluded = [a.code for a in candidates if a.hub not in wanted]
            candidates = [a for a in candidates if a.hub in wanted]
            hub_filter = {"hub_classes": sorted(wanted), "excluded_airports": excluded}
        codes = [a.code for a in candidates]
        if not codes:
            raise DataValidationError(f"no eligible airports for {region or airports} with the given filters")

        kpis, windows, provs, warnings, _ = self.airport_kpis(codes)
        values = {a: {m: mv.value for m, mv in kpis[a].items()} for a in codes}
        flags = {a: sorted({f for mv in kpis[a].values() for f in mv.flags}) for a in codes}
        tiebreak = {a: kpis[a]["passengers_t12m"].value or 0.0 for a in codes}
        result = rank_airports(values, weights, min_coverage=min_coverage, tiebreak=tiebreak, flags=flags,
                               previous_ranks=previous_ranks)
        data = result.to_dict()
        data["candidate_group"] = {"query": region or airports, "interpretation": interpretation, "airports": codes,
                                   "eligibility": note, "hub_filter": hub_filter}
        scored = [r.metric for r in result.ranges]  # every requested KPI, usable or dropped
        data["metric_details"] = {a: {m: kpis[a][m].to_dict() for m in scored} for a in codes}
        small, small_warnings = self._small_samples(kpis, codes, windows["operations"])
        data["small_sample_airports"] = small
        warnings = warnings + result.warnings + small_warnings + [PERIOD_MISMATCH]
        # A composite of proxies over mixed windows is never "high"; per-airport partial and
        # low-sample flags are reported on each airport rather than lowering the whole ranking.
        confidence = "low" if self._uses_fallback(provs) or result.status != "ranked" else "medium"
        return _envelope("ranking", data, provs + [self.data.airports.provenance], windows,
                         scored, warnings, confidence, self._missing_notes(kpis, scored))

    # ------------------------------------------------------------ 2. congestion comparison

    def compare(self, airports: list[str], metrics: list[str] | None = None) -> dict:
        found = self.data.airports.require(airports)
        codes = [a.code for a in found]
        if len(codes) < 2:
            raise DataValidationError("comparison needs at least 2 distinct airports")
        metrics = metrics or CONGESTION_METRICS + VOLUME_METRICS
        unknown = [m for m in metrics if m not in METRICS]
        if unknown:
            raise DataValidationError(f"unknown metrics {unknown}")
        kpis, windows, provs, warnings, _ = self.airport_kpis(codes)
        result = compare(kpis, codes, metrics).to_dict()
        small, small_warnings = self._small_samples(kpis, codes, windows["operations"])
        result["small_sample_airports"] = small
        confidence = "low" if self._uses_fallback(provs) or small else "medium"
        notes = ["Delay data covers BTS reporting carriers only (large US passenger airlines)."]
        return _envelope("comparison", result, provs, windows, metrics, warnings + small_warnings + [PERIOD_MISMATCH],
                         confidence, notes + self._missing_notes(kpis, metrics))

    # ------------------------------------------------------------ 3. long-haul share

    def long_haul(self, airport: str, threshold_miles: int = 3000, service_classes=PASSENGER_CLASSES) -> dict:
        [ap] = self.data.airports.require([airport])
        everything = self.data.routes.segments_from(ap.code, ["F", "G", "L", "P"])
        result = long_haul_share(ap.code, everything.segments, threshold_miles, service_classes)
        data = result.to_dict()
        cargo = sum(v["departures"] for k, v in result.by_class.items() if k in ("G", "P"))
        warnings = []
        if result.all_classes.denominator and cargo:
            warnings.append(
                f"All-cargo classes (G, P) are {cargo:,.0f} of {result.all_classes.denominator:,.0f} departures; "
                "the all-class percentage differs from the passenger-class percentage."
            )
        confidence = "high" if result.primary.share is not None else "low"
        return _envelope("long_haul", data, [everything.provenance], {"routes": everything.observation_period},
                         [], warnings, confidence,
                         ["Single month of route data; the route mix can be seasonal.",
                          "There is no universal long-haul definition; the threshold is a stated, adjustable choice."])

    # ------------------------------------------------------------ 4. demand-pressure profile

    def demand_profile(self, airport: str, peer_group: str | None = None) -> dict:
        [ap] = self.data.airports.require([airport])
        hub = peer_group or ap.hub
        if not hub:
            raise DataValidationError(f"{ap.code} has no FAA hub class; specify a peer group")
        peers = [a.code for a in self.data.airports.with_hub(hub) if a.code != ap.code]
        codes = [ap.code] + peers
        kpis: dict[str, dict[str, MetricValue]] = {}
        provs, warnings = [], []
        windows = {}
        for i in range(0, len(codes), API_BATCH):
            k, windows, p, wn, _ = self.airport_kpis(codes[i : i + API_BATCH])
            kpis.update(k)
            provs += p
            warnings += wn
        p2019 = self.data.traffic.fetch_monthly_traffic([ap.code], "2019-01", "2019-12")
        provs.append(p2019.provenance)
        total19 = None if p2019.missing_months or any(r.passengers is None for r in p2019.rows) else sum(
            r.passengers for r in p2019.rows)
        mv19 = MetricValue("passengers_2019", total19, window="2019-01..2019-12",
                           missing_reason="incomplete 2019 data" if total19 is None else None)
        arrivals = self.data.operations.get([ap.code]).arrivals[ap.code]
        result = demand_profile(ap.code, f"FAA hub class {hub}", kpis[ap.code],
                                {c: kpis[c] for c in peers}, arrivals, mv19)
        data = result.to_dict()
        data["subject_metrics"] = {m: mv.to_dict() for m, mv in kpis[ap.code].items()}
        small, small_warnings = self._small_samples(kpis, [ap.code], windows["operations"])
        data["small_sample_airports"] = small
        warnings += small_warnings + [PERIOD_MISMATCH,
                     "Delay causes refer to arrivals into the airport and are airline-reported attributions."]
        confidence = "low" if self._uses_fallback(provs) else "medium"
        return _envelope("demand_profile", data, provs, windows,
                         ["passenger_growth", "departure_growth", "load_factor", "delay_rate",
                          "avg_taxi_out_min", "cancellation_rate"],
                         warnings, confidence,
                         ["Peer percentile = % of peer airports with a strictly lower value (higher = more pressure).",
                          "Delay data covers BTS reporting carriers only."])
