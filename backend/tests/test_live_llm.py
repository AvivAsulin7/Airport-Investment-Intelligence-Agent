"""Real-model smoke tests (D-033). Skipped unless an Anthropic key is configured."""

import pytest

from app.agent.agent import build_agent, build_chat_model, extract_turn
from app.agent.smoke_tool import lookup_test_value
from app.settings import get_settings

settings = get_settings()
pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not settings.llm_configured, reason="ANTHROPIC_API_KEY not configured"),
]

PROMPT = "Use the lookup_test_value tool to answer. Reply briefly."


def _agent():
    return build_agent(build_chat_model(settings), [lookup_test_value], PROMPT, settings.agent_max_model_calls)


def _ask(agent, text, thread):
    return agent.invoke({"messages": [{"role": "user", "content": text}]}, config={"configurable": {"thread_id": thread}})


def test_model_id_accepted_and_tool_called_with_artifact():
    turn = extract_turn(_ask(_agent(), "What is the test value for key beta?", "llm-1")["messages"])

    assert turn["evidence"], "model did not call the tool"
    assert turn["evidence"][0]["artifact"]["value"] == 22
    assert turn["reply"]


def test_follow_up_uses_session_memory_and_thinking_round_trips():
    agent = _agent()
    _ask(agent, "What is the test value for key alpha?", "llm-2")

    turn = extract_turn(_ask(agent, "Now do the same for gamma.", "llm-2")["messages"])

    assert [e["artifact"]["key"] for e in turn["evidence"] if e["artifact"]] == ["gamma"]
