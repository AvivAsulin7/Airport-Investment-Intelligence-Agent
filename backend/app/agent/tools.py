"""LangChain tools over the deterministic AnalyticsService (Phase 7, D-042, P-024).

Each tool validates its arguments with a Pydantic schema, calls one service method, and returns
(content, artifact): `content` is a compact JSON view for the model; `artifact` is the full
deterministic envelope (warnings, small_sample_airports, provenance, confidence, missing-data
reasons) forwarded unchanged to the frontend (D-030). No formulas live here.
"""

import json
from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel, Field

from app.data.bts_api import BtsApiUnavailable
from app.data.validation import DataValidationError
from app.engine.registry import METRICS, SCORING_METRICS
from app.engine.scoring import ScoringInputError
from app.engine.service import AnalyticsService

Code = Field(pattern=r"^[A-Za-z0-9]{3}$", description="3-letter airport code, e.g. 'BOS'")
HubClass = Literal["L", "M", "S", "N"]
ServiceClass = Literal["F", "G", "L", "P"]


def _round(obj, digits=4):
    """Shorten fractional values for the model view; never alter whole-number counts."""
    if isinstance(obj, float):
        if obj.is_integer():
            return int(obj)
        if abs(obj) >= 1000:
            return round(obj, 1)
        return float(f"{obj:.{digits}g}")
    if isinstance(obj, dict):
        return {k: _round(v, digits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, digits) for v in obj]
    return obj


def _content(envelope: dict, data_view: dict) -> str:
    """Compact model-facing view built from the same envelope as the artifact."""
    view = {
        "result_type": envelope["result_type"],
        "data": data_view,
        "windows": envelope["windows"],
        "warnings": envelope["warnings"],
        "confidence": envelope["confidence"],
        "coverage_notes": envelope["coverage_notes"],
        "sources": [
            f"{p['source_type']}: {p['name']} ({p['observation_period']})" for p in envelope["provenance"]
        ],
    }
    return json.dumps(_round(view), ensure_ascii=False)


# ------------------------------------------------------------------ schemas


class ResolveInput(BaseModel):
    query: str = Field(min_length=1, max_length=100, description="Airport code, airport/city name, US state or FAA region name")
    kind: Literal["airport", "region"] = Field(description="'airport' for one airport, 'region' for a state or FAA region")


class RankInput(BaseModel):
    region: str | None = Field(None, max_length=60, description="US state or FAA region name, e.g. 'New England', 'Florida'")
    airports: list[str] | None = Field(None, min_length=3, max_length=30, description="Explicit candidate airport codes")
    weights: dict[str, float] | None = Field(
        None, description=f"Optional KPI weights (>= 0) keyed by: {sorted(SCORING_METRICS)}. Omit for approved defaults."
    )
    hub_classes: list[HubClass] | None = Field(None, description="Optional FAA hub-size filter: L, M, S, N")


class CompareInput(BaseModel):
    airports: list[str] = Field(min_length=2, max_length=5, description="Airport codes; the first is the baseline")
    metrics: list[str] | None = Field(None, description=f"Optional metric ids from: {sorted(METRICS)}")


class LongHaulInput(BaseModel):
    airport: str = Code
    threshold_miles: int = Field(3000, ge=500, le=10_000, description="Long-haul threshold in statute miles (inclusive)")
    service_classes: list[ServiceClass] = Field(
        default=["F", "L"],
        min_length=1,
        description="T-100 classes: F scheduled passenger, L charter passenger, G scheduled all-cargo, P charter all-cargo",
    )


class ProfileInput(BaseModel):
    airport: str = Code
    peer_group: HubClass | None = Field(None, description="FAA hub class for peers; default = the airport's own hub class")


# ------------------------------------------------------------------ tools


def build_tools(service: AnalyticsService) -> list:
    @tool(args_schema=ResolveInput, response_format="content_and_artifact")
    def resolve_airports(query: str, kind: str) -> tuple[str, dict]:
        """Resolve an airport name/code (kind='airport') or a US state / FAA region (kind='region') to airports.
        States the interpretation used (e.g. 'LA' is interpreted as LAX)."""
        refs = service.data.airports
        res = refs.search(query) if kind == "airport" else refs.resolve_region(query)
        airports = [
            {"code": a.code, "name": a.name, "city": a.city, "state": a.state, "faa_region": a.faa_region,
             "hub": a.hub, "primary": a.is_primary}
            for a in res.airports[:30]
        ]
        artifact = {
            "result_type": "airports",
            "data": {"query": query, "kind": kind, "interpretation": res.interpretation,
                     "eligibility": res.excluded_note, "airports": airports, "truncated": len(res.airports) > 30},
            "provenance": [refs.provenance.to_dict()],
            "windows": {}, "definitions": {}, "warnings": [], "coverage_notes": [], "confidence": "high",
            "formula_version": None,
        }
        return json.dumps(artifact["data"], ensure_ascii=False), artifact

    @tool(args_schema=RankInput, response_format="content_and_artifact")
    def rank_airports(region=None, airports=None, weights=None, hub_classes=None) -> tuple[str, dict]:
        """Rank airports by the deterministic expansion-opportunity score (relative to the candidate group).
        Give either a region or an explicit airport list. Scores are leads for further analysis, not verified
        investment opportunities or profitability forecasts."""
        env = service.rank(region=region, airports=airports, weights=weights, hub_classes=hub_classes)
        d = env["data"]
        view = {
            "status": d["status"], "reason": d["reason"], "candidate_group": d["candidate_group"],
            "weights_used": d["weights_used"], "interpretation": d["interpretation"],
            "small_sample_airports": d["small_sample_airports"],
            "airports": [
                {"airport": s["airport"], "rank": s["rank"], "score": s["score"], "coverage": s["coverage"],
                 "status": s["status"], "flags": s["flags"],
                 "raw": {k: c["raw"] for k, c in s["kpis"].items()}}
                for s in d["airports"]
            ],
        }
        return _content(env, view), env

    @tool(args_schema=CompareInput, response_format="content_and_artifact")
    def compare_airports(airports: list[str], metrics: list[str] | None = None) -> tuple[str, dict]:
        """Compare airports side by side on congestion proxies (departure delay rate, cancellation rate,
        taxi-out, average departure delay) with traffic volume context. Differences are vs the first airport.
        No composite score."""
        env = service.compare(airports, metrics)
        return _content(env, env["data"]), env

    @tool(args_schema=LongHaulInput, response_format="content_and_artifact")
    def get_long_haul_share(airport: str, threshold_miles: int = 3000, service_classes=("F", "L")) -> tuple[str, dict]:
        """Share of departures from an airport flying routes >= threshold statute miles, for explicit T-100
        service classes (default passenger classes F+L). Always also returns the all-class (incl. cargo) share."""
        env = service.long_haul(airport, threshold_miles, list(service_classes))
        return _content(env, env["data"]), env

    @tool(args_schema=ProfileInput, response_format="content_and_artifact")
    def get_demand_pressure_profile(airport: str, peer_group: str | None = None) -> tuple[str, dict]:
        """Observed demand and capacity-pressure indicators for one airport vs FAA hub-class peers, plus
        arrival-delay causes. Unmet demand is NOT measured; the result says so explicitly."""
        env = service.demand_profile(airport, peer_group)
        d = env["data"]
        view = {k: d[k] for k in ("airport", "peer_group", "observed_demand", "capacity_pressure",
                                  "delay_causes", "unmet_demand", "small_sample_airports")}
        view["peer_count"] = len(d["peers"])
        return _content(env, view), env

    @tool(response_format="content_and_artifact")
    def list_metrics() -> tuple[str, dict]:
        """List the metrics this agent can compute, with formulas, units, sources and whether they can be
        weighted in rankings. Use this to explain what is and is not available."""
        rows = [
            {"id": m.id, "label": m.label, "formula": m.formula, "unit": m.unit, "source": m.source,
             "category": m.category, "rankable": m.scoring}
            for m in METRICS.values()
        ]
        artifact = {"result_type": "metrics", "data": {"metrics": rows}, "provenance": [], "windows": {},
                    "definitions": {}, "warnings": [], "coverage_notes": [], "confidence": "high",
                    "formula_version": None}
        return json.dumps(rows, ensure_ascii=False), artifact

    return [resolve_airports, rank_airports, compare_airports, get_long_haul_share, get_demand_pressure_profile,
            list_metrics]


# Errors the model may safely see verbatim (validation messages help it correct its call).
USER_FACING_ERRORS = (DataValidationError, ScoringInputError, BtsApiUnavailable)
