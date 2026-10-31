"""Paid end-to-end agent checks with the real model (Phase 7). Opt-in: RUN_LLM_TESTS=1.

One controlled run: Q1 + one follow-up in the same session, then Q2, Q3, Q4. Uses the async path
(ainvoke) and the real data layer. Asserts tool usage and evidence, not exact prose.
Run with -s to print replies and token usage.
"""

import asyncio
import json
import os
import uuid

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.agent import build_agent, build_chat_model, extract_turn
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import build_tools
from app.data.layer import load_data_layer
from app.engine.service import AnalyticsService
from app.settings import get_settings

from .answer_checks import MAX_WORDS, ORDINARY_WORDS, format_problems, ungrounded_numbers

settings = get_settings()
pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not settings.llm_configured, reason="ANTHROPIC_API_KEY not configured"),
    pytest.mark.skipif(os.getenv("RUN_LLM_TESTS") != "1", reason="paid LLM tests need explicit opt-in: RUN_LLM_TESTS=1"),
    pytest.mark.skipif(not (settings.data_processed_dir / "manifest.json").is_file(), reason="snapshots not built"),
]

USAGE = {"input": 0, "output": 0, "model_calls": 0}


@pytest.fixture(scope="module")
def agent():
    service = AnalyticsService(load_data_layer(settings))
    return build_agent(build_chat_model(settings), build_tools(service), SYSTEM_PROMPT, settings.agent_max_model_calls)


def _ask(agent, text, thread):
    result = asyncio.run(agent.ainvoke({"messages": [{"role": "user", "content": text}]},
                                       config={"configurable": {"thread_id": thread}}))
    msgs = result["messages"]
    last_human = max(i for i, m in enumerate(msgs) if isinstance(m, HumanMessage))
    ai = [m for m in msgs[last_human + 1:] if isinstance(m, AIMessage)]
    for m in ai:
        assert (m.response_metadata.get("model_name") or "") in ("", settings.llm_model)
        u = m.usage_metadata or {}
        USAGE["input"] += u.get("input_tokens", 0)
        USAGE["output"] += u.get("output_tokens", 0)
        USAGE["model_calls"] += 1
    turn = extract_turn(msgs)
    json.dumps(turn["evidence"])  # artifacts stay serializable on the real path
    print(f"\n--- Q: {text}\n  tools: {[(e['tool'], e['input'], e['status']) for e in turn['evidence']]}"
          f"\n  reply:\n{turn['reply']}\n  cumulative usage: {USAGE}")
    return turn


def _types(turn):
    return {e["artifact"]["result_type"] for e in turn["evidence"] if e["artifact"]}


def _artifacts(*turns):
    return [e["artifact"] for t in turns for e in t["evidence"] if e["artifact"]]


def answer_problems(turn, max_words, *earlier):
    """Format policy (length, no headings/lists/raw fractions/closing offers) and numeric grounding."""
    problems = format_problems(turn["reply"], max_words)
    ungrounded = ungrounded_numbers(turn["reply"], _artifacts(*earlier, turn))
    print(f"  words={len(turn['reply'].split())} limit={max_words} problems={problems} ungrounded={ungrounded}")
    return problems + [f"ungrounded {ungrounded}"] * bool(ungrounded)


def test_q1_and_follow_up(agent):
    # Both turns run before any assertion, so a failed check on Q1 cannot skip the paid follow-up.
    thread = str(uuid.uuid4())
    t1 = _ask(agent, "Which airports in New England are strong candidates for terminal expansion?", thread)
    t2 = _ask(agent, "Now rank only the medium and small hub airports from that list.", thread)
    checks = {
        "q1 tool": "ranking" in _types(t1) and not t1["incomplete"],
        "q1 small-sample warning in evidence": any(a["result_type"] == "ranking" and a["data"]["small_sample_airports"]
                                                   for a in _artifacts(t1)),
        "q1 answer": not answer_problems(t1, MAX_WORDS),
        "follow-up hub filter": [a["data"]["candidate_group"]["hub_filter"]["hub_classes"]
                                 for a in _artifacts(t2) if a["result_type"] == "ranking"][-1:] == [["M", "S"]],
        "follow-up answer": not answer_problems(t2, MAX_WORDS, t1),  # may cite Q1 evidence
    }
    assert all(checks.values()), checks


def test_q2_lax_vs_santa_ana(agent):
    t = _ask(agent, "Compare LA and Santa Ana airport congestion levels.", str(uuid.uuid4()))
    comps = [e for e in t["evidence"] if e["artifact"] and e["artifact"]["result_type"] == "comparison"]
    assert comps and set(comps[-1]["artifact"]["data"]["airports"]) == {"LAX", "SNA"}
    assert answer_problems(t, MAX_WORDS) == []


def test_q3_anchorage_long_haul(agent):
    t = _ask(agent, "What is the percentage of long haul flights out of Anchorage airport?", str(uuid.uuid4()))
    lh = [e for e in t["evidence"] if e["artifact"] and e["artifact"]["result_type"] == "long_haul"]
    assert lh and lh[-1]["artifact"]["data"]["origin"] == "ANC"
    assert answer_problems(t, ORDINARY_WORDS) == []


def test_q4_sfo_unmet_demand(agent):
    t = _ask(agent, "What is the unmet flight demand in SFO airport and why?", str(uuid.uuid4()))
    prof = [e for e in t["evidence"] if e["artifact"] and e["artifact"]["result_type"] == "demand_profile"]
    assert prof and prof[-1]["artifact"]["data"]["unmet_demand"]["measured"] is False
    assert answer_problems(t, MAX_WORDS) == []  # SFO vs its hub-class peers: a comparison
    print(f"\nTOTAL USAGE {USAGE}; est. cost at $2/$10 per MTok: "
          f"${USAGE['input'] * 2e-6 + USAGE['output'] * 1e-5:.3f}")
