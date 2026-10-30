"""Phase 7 tool tests: schema validation, routing to the engine, artifact preservation (offline)."""

import json

import pytest
from langchain_core.messages import ToolMessage
from pydantic import ValidationError

from app.agent.agent import _tool_error_content
from app.agent.tools import build_tools
from app.data.layer import DataLayer
from app.data.validation import DataValidationError
from app.engine.service import AnalyticsService

from .test_engine_service import FakeAirports, FakeOps, FakeTraffic


class RecordingService:
    """Stub that records calls and returns a minimal envelope (routing tests)."""

    def __init__(self):
        self.calls = []

    def _env(self, kind, data):
        return {"result_type": kind, "data": data, "provenance": [], "windows": {}, "definitions": {},
                "warnings": [], "coverage_notes": [], "confidence": "medium", "formula_version": "v1"}

    def rank(self, **kw):
        self.calls.append(("rank", kw))
        return self._env("ranking", {"status": "ranked", "reason": None, "candidate_group": {}, "weights_used": {},
                                     "interpretation": "x", "small_sample_airports": [], "airports": []})

    def compare(self, airports, metrics):
        self.calls.append(("compare", airports, metrics))
        return self._env("comparison", {})

    def long_haul(self, airport, threshold, classes):
        self.calls.append(("long_haul", airport, threshold, classes))
        return self._env("long_haul", {})

    def demand_profile(self, airport, peer_group):
        self.calls.append(("profile", airport, peer_group))
        return self._env("demand_profile", {"airport": airport, "peer_group": "p", "observed_demand": {},
                                             "capacity_pressure": {}, "delay_causes": None,
                                             "unmet_demand": {"measured": False}, "small_sample_airports": [],
                                             "peers": []})


def _tools(service):
    return {t.name: t for t in build_tools(service)}


def _call(t, args):
    """Invoke through the tool-call path the agent uses; returns the ToolMessage."""
    return t.invoke({"type": "tool_call", "name": t.name, "args": args, "id": "call-1"})


def test_tools_route_to_the_engine_with_validated_arguments():
    svc = RecordingService()
    tools = _tools(svc)

    _call(tools["rank_airports"], {"region": "New England", "hub_classes": ["M", "S"]})
    _call(tools["compare_airports"], {"airports": ["LAX", "SNA"]})
    _call(tools["get_long_haul_share"], {"airport": "ANC"})
    _call(tools["get_long_haul_share"], {"airport": "ANC", "threshold_miles": 4000, "service_classes": ["G", "P"]})
    _call(tools["get_demand_pressure_profile"], {"airport": "SFO"})

    assert svc.calls == [
        ("rank", {"region": "New England", "airports": None, "weights": None, "hub_classes": ["M", "S"]}),
        ("compare", ["LAX", "SNA"], None),
        ("long_haul", "ANC", 3000, ["F", "L"]),  # passenger classes by default, explicit
        ("long_haul", "ANC", 4000, ["G", "P"]),
        ("profile", "SFO", None),
    ]


@pytest.mark.parametrize("name,args", [
    ("get_long_haul_share", {"airport": "ANCX"}),
    ("get_long_haul_share", {"airport": "ANC", "threshold_miles": 100}),
    ("get_long_haul_share", {"airport": "ANC", "service_classes": ["Z"]}),
    ("get_long_haul_share", {"airport": "ANC", "service_classes": []}),
    ("compare_airports", {"airports": ["LAX"]}),
    ("rank_airports", {"region": "New England", "hub_classes": ["X"]}),
    ("resolve_airports", {"query": "", "kind": "airport"}),
])
def test_invalid_arguments_are_rejected_by_the_schema(name, args):
    svc = RecordingService()
    with pytest.raises(ValidationError):
        _tools(svc)[name].invoke(args)
    assert svc.calls == []


@pytest.fixture
def real_engine():
    return AnalyticsService(DataLayer(FakeTraffic(), FakeAirports(), FakeOps(), None, None))


def test_artifact_is_the_full_engine_envelope_and_serializable(real_engine):
    msg = _call(_tools(real_engine)["rank_airports"], {"region": "anything"})

    assert isinstance(msg, ToolMessage)
    direct = real_engine.rank(region="anything")
    assert json.loads(json.dumps(msg.artifact)) == json.loads(json.dumps(direct))  # nothing dropped or altered
    assert msg.artifact["data"]["small_sample_airports"][0]["airport"] == "DDD"


def test_model_content_keeps_small_sample_warning_and_interpretation(real_engine):
    msg = _call(_tools(real_engine)["rank_airports"], {"region": "anything"})
    content = json.loads(msg.content)

    assert any(w.startswith("Small sample: DDD") for w in content["warnings"])
    assert content["data"]["small_sample_airports"][0]["eligible_departures"] == 40
    assert "not a verified investment opportunity" in content["data"]["interpretation"]
    assert "metric_details" not in content["data"]  # compact view for the model only
    assert any(s.startswith("public_api") for s in content["sources"])


def test_model_view_keeps_counts_exact_and_rounds_only_fractions():
    from app.agent.tools import _round

    assert _round({"departures": 189964.0, "pax": 26488605.0, "share": 0.042387, "big": 324434.567, "n": None}) == {
        "departures": 189964, "pax": 26488605, "share": 0.04239, "big": 324434.6, "n": None}


def test_ranking_lists_hub_class_per_candidate(real_engine):
    content = json.loads(_call(_tools(real_engine)["rank_airports"], {"region": "anything"}).content)
    assert content["data"]["candidate_group"]["hub_classes"] == {"AAA": "L", "BBB": "M", "CCC": "S", "DDD": "N"}


def test_user_facing_errors_are_explained_others_are_redacted():
    shown = json.loads(_tool_error_content(DataValidationError("unknown region or state: 'Atlantis'"), None))
    hidden = json.loads(_tool_error_content(RuntimeError("secret internal path C:/x"), None))

    assert shown["error"]["message"] == "unknown region or state: 'Atlantis'"
    assert hidden["error"] == {"code": "TOOL_ERROR", "type": "RuntimeError"}


def test_list_metrics_describes_rankable_metrics():
    msg = _call(_tools(RecordingService())["list_metrics"], {})
    ids = {m["id"]: m for m in msg.artifact["data"]["metrics"]}
    assert ids["delay_rate"]["rankable"] and not ids["departures_t12m"]["rankable"]
