"""Real-model smoke tests (D-033). These make paid API calls.

Skipped unless an Anthropic key is configured AND RUN_LLM_TESTS=1 is set (explicit opt-in).
Run with -s to see the model actually used and token usage per test.
"""

import os

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from app.agent.agent import build_agent, build_chat_model, extract_turn
from app.agent.smoke_tool import lookup_test_value
from app.settings import get_settings

settings = get_settings()
pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not settings.llm_configured, reason="ANTHROPIC_API_KEY not configured"),
    pytest.mark.skipif(os.getenv("RUN_LLM_TESTS") != "1", reason="paid LLM tests need explicit opt-in: RUN_LLM_TESTS=1"),
]

PROMPT = "Use the lookup_test_value tool to answer. Reply briefly."


def _agent():
    return build_agent(build_chat_model(settings), [lookup_test_value], PROMPT, settings.agent_max_model_calls)


def _ask(agent, text, thread):
    return agent.invoke({"messages": [{"role": "user", "content": text}]}, config={"configurable": {"thread_id": thread}})


def _report(messages):
    """Assert the configured model answered; print model and token usage (no secrets)."""
    ai = [m for m in messages if isinstance(m, AIMessage)]
    models = {m.response_metadata.get("model_name") or m.response_metadata.get("model") for m in ai}
    assert models == {settings.llm_model}, models
    usage = [m.usage_metadata or {} for m in ai]
    print(
        f"\n  model={sorted(models)} model_calls={len(ai)} "
        f"input_tokens={sum(u.get('input_tokens', 0) for u in usage)} "
        f"output_tokens={sum(u.get('output_tokens', 0) for u in usage)}"
    )


def test_model_id_accepted_and_tool_called_with_artifact():
    messages = _ask(_agent(), "What is the test value for key beta?", "llm-1")["messages"]
    turn = extract_turn(messages)

    _report(messages)
    assert turn["evidence"], "model did not call the tool"
    assert turn["evidence"][0]["input"] == {"key": "beta"}
    assert turn["evidence"][0]["artifact"]["value"] == 22
    assert turn["reply"]
    print(f"  reply: {turn['reply'][:200]!r}")


def test_follow_up_uses_session_memory_and_thinking_round_trips():
    agent = _agent()
    _ask(agent, "What is the test value for key alpha?", "llm-2")

    messages = _ask(agent, "Now do the same for gamma.", "llm-2")["messages"]
    turn = extract_turn(messages)

    _report(messages)
    # Memory: the thread still holds turn 1's tool result alongside turn 2's.
    keys_in_thread = [m.artifact["key"] for m in messages if isinstance(m, ToolMessage) and m.artifact]
    assert keys_in_thread == ["alpha", "gamma"]
    # The follow-up ("the same") was resolved from context into the right tool call.
    assert [e["artifact"]["key"] for e in turn["evidence"] if e["artifact"]] == ["gamma"]
    assert turn["reply"]
    print(f"  reply: {turn['reply'][:200]!r}")
