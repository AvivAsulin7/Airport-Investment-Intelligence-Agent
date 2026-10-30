"""Focused paid verification of the Phase 7 fixes (opt-in RUN_LLM_TESTS=1), via the real /api/chat.

One session, two turns: a ranking, then a hub-size follow-up asking for an exact count.
Checks: hub classes stated correctly, exact integer preserved, no general-knowledge airport claims,
stable response contract, per-turn evidence. Run with -s to print replies and token usage.
"""

import os
import re

import pytest
from fastapi.testclient import TestClient

from app import main
from app.settings import get_settings

settings = get_settings()
pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not settings.llm_configured, reason="ANTHROPIC_API_KEY not configured"),
    pytest.mark.skipif(os.getenv("RUN_LLM_TESTS") != "1", reason="paid LLM tests need explicit opt-in: RUN_LLM_TESTS=1"),
    pytest.mark.skipif(not (settings.data_processed_dir / "manifest.json").is_file(), reason="snapshots not built"),
]

HUB_WORDS = {"M": "medium", "S": "small"}
# Phrases that would indicate general-knowledge descriptions not provided by any tool.
UNSUPPORTED = ["general aviation", "gateway", "home to", "known for", "located near", "serves as a", "tourist",
               "military", "built in", "opened in", "expansion project", "renovation project"]


def _artifacts(body, result_type):
    return [e["artifact"] for e in body["evidence"] if e["artifact"] and e["artifact"]["result_type"] == result_type]


def _find_count(body, airport):
    for art in body["evidence"]:
        a = art["artifact"] or {}
        d = a.get("data", {})
        if a.get("result_type") == "comparison":
            v = d.get("values", {}).get("departures_t12m", {}).get(airport)
            if v and v.get("value") is not None:
                return int(v["value"])
        if a.get("result_type") == "demand_profile" and d.get("airport") == airport:
            return int(d["subject_metrics"]["departures_t12m"]["value"])
    return None


def test_ranking_follow_up_hubs_exact_counts_and_grounded_descriptions():
    client = TestClient(main.create_app())
    t1 = client.post("/api/chat", json={"message": "Rank the New England airports as terminal expansion candidates."})
    assert t1.status_code == 200, t1.text
    b1 = t1.json()
    assert set(b1) == {"session_id", "mode", "status", "reply_markdown", "evidence", "sources", "warnings", "errors",
                       "incomplete", "notice"}
    assert b1["status"] == "complete" and _artifacts(b1, "ranking")

    t2 = client.post("/api/chat", json={
        "session_id": b1["session_id"],
        "message": "Keep only the medium and small hubs from that ranking. For each, say whether it is a medium "
                   "or small hub, and give the exact number of departures in the last 12 months for the "
                   "top-ranked one.",
    })
    assert t2.status_code == 200, t2.text
    b2 = t2.json()
    reply = b2["reply_markdown"]

    # Per-turn evidence; memory used (the follow-up refers to "that ranking").
    assert b2["session_id"] == b1["session_id"] and b2["status"] == "complete"
    ranks = _artifacts(b2, "ranking")
    assert ranks, "follow-up did not re-rank with a hub filter"
    group = ranks[-1]["data"]["candidate_group"]
    assert group["hub_filter"]["hub_classes"] == ["M", "S"]

    # Hub classes stated consistently with the tool's hub_classes.
    for code, hub in group["hub_classes"].items():
        for line in (ln for ln in reply.splitlines() if code in ln):
            said = {k for k, w in HUB_WORDS.items() if re.search(rf"\b{w}\b", line, re.I)}
            if len(said) == 1:
                assert said == {hub}, (code, hub, line)

    # Exact count for the top-ranked airport, as returned by a tool.
    top = next(s["airport"] for s in ranks[-1]["data"]["airports"] if s["rank"] == 1)
    count = _find_count(b2, top)
    assert count is not None, "no tool returned the departures count"
    assert f"{count:,}" in reply or str(count) in reply, (top, count)

    # No general-knowledge airport descriptions.
    hits = [p for p in UNSUPPORTED if p in reply.lower() or p in b1["reply_markdown"].lower()]
    assert not hits, hits

    # Token usage from the server-side thread (no secrets).
    rt = client.app.state.runtime
    thread = rt.sessions[b1["session_id"]]["thread"]
    msgs = rt.agent().get_state({"configurable": {"thread_id": thread}}).values["messages"]
    ai = [m for m in msgs if m.type == "ai"]
    usage = [m.usage_metadata or {} for m in ai]
    inp, out = sum(u.get("input_tokens", 0) for u in usage), sum(u.get("output_tokens", 0) for u in usage)
    models = {m.response_metadata.get("model_name") for m in ai}
    print(f"\nTURN 1 tools: {[(e['tool'], e['input']) for e in b1['evidence']]}\nTURN 1 reply:\n{b1['reply_markdown']}")
    print(f"\nTURN 2 tools: {[(e['tool'], e['input']) for e in b2['evidence']]}\nTURN 2 reply:\n{reply}")
    print(f"\ntop={top} exact_departures={count:,}  models={models}  model_calls={len(ai)}  "
          f"input_tokens={inp}  output_tokens={out}  est_cost=${inp * 2e-6 + out * 1e-5:.3f}")
    assert models == {settings.llm_model}
