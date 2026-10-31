"""Shared /api/chat contract fixtures for the React tests (architecture.md §10.2, Phase 8).

The fixtures are produced by the real /api/chat path (FastAPI + LangChain tools + engine) with a
scripted fake model and a FICTIONAL fake data layer, so they match the backend contract exactly
and contain no real aviation data (D-037). Regenerate with:  UPDATE_FIXTURES=1 pytest tests/test_contract_fixtures.py
Without the flag, this test fails if the backend output drifts from the committed fixtures.
"""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app import main
from app.data.layer import DataLayer
from app.engine.service import AnalyticsService

from .conftest import ToolCallingFakeModel, tool_call
from .test_engine_service import FakeAirports, FakeOps, FakeRoutes, FakeTraffic

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "test" / "fixtures"
SESSION = "00000000-0000-4000-8000-000000000000"

SCENARIOS = {
    "chat_ranking": [tool_call("rank_airports", {"region": "Fictional region"}, "call_rank"),
                     AIMessage(content="**AAA** ranks first in this fictional group. See the ranking evidence.")],
    "chat_comparison": [tool_call("compare_airports", {"airports": ["AAA", "DDD"]}, "call_compare"),
                        AIMessage(content="Delay rates differ; DDD is a small sample.")],
    "chat_long_haul": [tool_call("get_long_haul_share", {"airport": "AAA"}, "call_lh"),
                       AIMessage(content="Passenger long-haul share is shown with the all-class figure.")],
    "chat_profile": [tool_call("get_demand_pressure_profile", {"airport": "AAA"}, "call_profile"),
                     AIMessage(content="Unmet demand is not measured; indicators are shown.")],
    "chat_tool_error": [tool_call("get_long_haul_share", {"airport": "TOOLONG"}, "call_err"),
                        AIMessage(content="I could not run that analysis: the airport code was invalid.")],
    "chat_incomplete": [tool_call("list_metrics", {}, f"call_loop_{i}") for i in range(10)],
}


def _response(replies, monkeypatch) -> dict:
    monkeypatch.setenv("AGENT_MAX_MODEL_CALLS", "2")
    svc = AnalyticsService(DataLayer(FakeTraffic(), FakeAirports(), FakeOps(), FakeRoutes(), None))
    client = TestClient(main.create_app(service=svc, chat_model=ToolCallingFakeModel(messages=iter(replies))))
    body = client.post("/api/chat", json={"message": "fixture"}).json()
    body["session_id"] = SESSION  # random per run; normalized for stable fixtures
    return body


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_contract_fixture(name, monkeypatch):
    body = _response(SCENARIOS[name], monkeypatch)
    path = FIXTURE_DIR / f"{name}.json"
    text = json.dumps(body, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if os.getenv("UPDATE_FIXTURES") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    assert path.is_file(), f"missing fixture {path}; run with UPDATE_FIXTURES=1"
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(text), f"{name} drifted from the backend"
