"""/api/chat and /api/demo with a scripted fake model and fake data layer (offline, async path)."""

import json

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app import main
from app.data.layer import DataLayer
from app.engine.service import AnalyticsService

from .conftest import ToolCallingFakeModel, tool_call
from .test_engine_service import FakeAirports, FakeOps, FakeTraffic


def _client(replies):
    svc = AnalyticsService(DataLayer(FakeTraffic(), FakeAirports(), FakeOps(), None, None))
    model = ToolCallingFakeModel(messages=iter(replies))
    return TestClient(main.create_app(service=svc, chat_model=model))


def test_chat_returns_reply_and_full_evidence_via_async_path():
    client = _client([tool_call("rank_airports", {"region": "anything"}, "c1"), AIMessage(content="Ranked.")])

    body = client.post("/api/chat", json={"message": "rank them"}).json()

    assert body["reply_markdown"] == "Ranked." and body["incomplete"] is False
    [ev] = body["evidence"]
    assert ev["tool"] == "rank_airports" and ev["input"] == {"region": "anything"} and ev["status"] == "success"
    art = ev["artifact"]
    assert art["result_type"] == "ranking" and art["data"]["small_sample_airports"][0]["airport"] == "DDD"
    assert any(w.startswith("Small sample: DDD") for w in body["warnings"])
    assert {s["source_type"] for s in body["sources"]} == {"public_api", "public_dataset_snapshot"}
    json.dumps(body)  # fully serializable


def test_follow_up_uses_session_memory_and_returns_only_new_evidence():
    client = _client([
        tool_call("rank_airports", {"region": "anything"}, "c1"), AIMessage(content="first"),
        tool_call("compare_airports", {"airports": ["AAA", "DDD"]}, "c2"), AIMessage(content="second"),
    ])
    first = client.post("/api/chat", json={"message": "rank"}).json()

    second = client.post("/api/chat", json={"session_id": first["session_id"], "message": "compare top and DDD"}).json()

    assert second["session_id"] == first["session_id"]
    assert [e["tool"] for e in second["evidence"]] == ["compare_airports"]
    rt = client.app.state.runtime
    thread = rt.sessions[first["session_id"]]["thread"]
    state = rt.agent().get_state({"configurable": {"thread_id": thread}})
    assert [m.type for m in state.values["messages"]].count("human") == 2  # memory kept both turns


RESPONSE_KEYS = {"session_id", "mode", "status", "reply_markdown", "evidence", "sources", "warnings", "errors",
                 "incomplete", "notice"}
EVIDENCE_KEYS = {"tool", "tool_call_id", "input", "status", "artifact"}


def test_response_contract_is_stable():
    client = _client([tool_call("rank_airports", {"region": "anything"}, "c1"), AIMessage(content="ok")])

    body = client.post("/api/chat", json={"message": "rank"}).json()

    assert set(body) == RESPONSE_KEYS
    assert body["mode"] == "agent" and body["status"] == "complete" and body["errors"] == []
    assert set(body["evidence"][0]) == EVIDENCE_KEYS
    assert set(body["evidence"][0]["artifact"]) == {"result_type", "data", "provenance", "windows", "definitions",
                                                    "warnings", "coverage_notes", "confidence", "formula_version"}


def test_previous_turn_warnings_and_sources_do_not_leak_into_the_next_turn():
    client = _client([
        tool_call("rank_airports", {"region": "anything"}, "c1"), AIMessage(content="first"),
        tool_call("list_metrics", {}, "c2"), AIMessage(content="second"),
    ])
    first = client.post("/api/chat", json={"message": "rank"}).json()
    assert any(w.startswith("Small sample: DDD") for w in first["warnings"]) and first["sources"]

    second = client.post("/api/chat", json={"session_id": first["session_id"], "message": "what metrics?"}).json()

    assert [e["tool"] for e in second["evidence"]] == ["list_metrics"]
    assert second["warnings"] == [] and second["sources"] == []  # nothing carried over from turn 1


def test_sessions_are_isolated():
    client = _client([AIMessage(content="a"), AIMessage(content="b")])
    a = client.post("/api/chat", json={"message": "one"}).json()
    b = client.post("/api/chat", json={"message": "two"}).json()

    assert a["session_id"] != b["session_id"]
    rt = client.app.state.runtime
    state = rt.agent().get_state({"configurable": {"thread_id": rt.sessions[b["session_id"]]["thread"]}})
    assert [m.content for m in state.values["messages"] if m.type == "human"] == ["two"]


def test_tool_validation_error_is_returned_as_error_evidence():
    client = _client([tool_call("get_long_haul_share", {"airport": "TOOLONG"}, "c1"), AIMessage(content="Sorry.")])

    body = client.post("/api/chat", json={"message": "x"}).json()

    [ev] = body["evidence"]
    assert ev["status"] == "error" and ev["artifact"] is None and "airport" in ev["error"]
    assert body["reply_markdown"] == "Sorry."
    assert body["status"] == "completed_with_tool_errors" and body["errors"][0].startswith("get_long_haul_share:")


def test_engine_error_message_reaches_the_model_and_evidence():
    client = _client([tool_call("rank_airports", {"region": "anything", "weights": {"made_up": 1}}, "c1"),
                      AIMessage(content="Invalid weights.")])

    [ev] = client.post("/api/chat", json={"message": "x"}).json()["evidence"]
    assert ev["status"] == "error" and "ScoringInputError" in ev["error"] and "made_up" in ev["error"]


def test_model_call_limit_marks_turn_incomplete(monkeypatch):
    monkeypatch.setenv("AGENT_MAX_MODEL_CALLS", "2")
    client = _client([tool_call("list_metrics", {}, f"c{i}") for i in range(10)])

    body = client.post("/api/chat", json={"message": "loop"}).json()

    assert body["incomplete"] is True and "Analysis incomplete" in body["reply_markdown"]
    assert body["status"] == "incomplete"
    assert "Model call limits exceeded" not in body["reply_markdown"]
    assert len(body["evidence"]) == 2


def test_input_limits_and_turn_cap(monkeypatch):
    client = _client([AIMessage(content="ok")] * 3)
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 2001}).status_code == 422
    assert client.post("/api/chat", json={"session_id": "not-a-uuid", "message": "hi"}).status_code == 422

    monkeypatch.setattr(main, "MAX_TURNS", 1)
    sid = client.post("/api/chat", json={"message": "one"}).json()["session_id"]
    assert client.post("/api/chat", json={"session_id": sid, "message": "two"}).status_code == 409


def test_missing_key_gives_503_and_demo_still_works(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    svc = AnalyticsService(DataLayer(FakeTraffic(), FakeAirports(), FakeOps(), None, None))
    client = TestClient(main.create_app(service=svc))

    resp = client.post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 503 and "demo" in resp.json()["detail"]

    demo = client.post("/api/demo/q1").json()
    assert demo["mode"] == "demo" and "AI agent not used" in demo["label"]
    assert demo["evidence"][0]["artifact"]["result_type"] == "ranking"
    assert client.post("/api/demo/q9").status_code == 422
