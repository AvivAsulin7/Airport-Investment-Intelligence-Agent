"""Phase 4 smoke tests of LangChain mechanics with a scripted fake model (no LLM, no network)."""

from langchain_core.messages import AIMessage, ToolMessage

from app.agent.agent import build_agent, extract_turn
from app.agent.smoke_tool import lookup_test_value

from .conftest import ToolCallingFakeModel, tool_call


def _agent(replies, max_model_calls=8):
    model = ToolCallingFakeModel(messages=iter(replies))
    return build_agent(model, [lookup_test_value], "test", max_model_calls)


def _ask(agent, text, thread="t1"):
    return agent.invoke({"messages": [{"role": "user", "content": text}]}, config={"configurable": {"thread_id": thread}})


def test_tool_invocation_and_artifact_propagation():
    agent = _agent([tool_call("lookup_test_value", {"key": "beta"}, "c1"), AIMessage(content="Beta is 22.")])

    turn = extract_turn(_ask(agent, "what is beta?")["messages"])

    assert turn["reply"] == "Beta is 22."
    [ev] = turn["evidence"]
    assert ev["tool"] == "lookup_test_value"
    assert ev["input"] == {"key": "beta"}
    assert ev["artifact"] == {"result_type": "smoke_test", "key": "beta", "value": 22, "source_type": "test_fixture"}


def test_artifact_is_not_sent_to_model_content():
    agent = _agent([tool_call("lookup_test_value", {"key": "alpha"}, "c1"), AIMessage(content="ok")])

    msgs = _ask(agent, "alpha?")["messages"]
    tool_msg = next(m for m in msgs if isinstance(m, ToolMessage))

    assert tool_msg.content == "value for alpha is 11"
    assert "test_fixture" not in tool_msg.content


def test_session_memory_and_second_turn_evidence_isolation():
    agent = _agent(
        [
            tool_call("lookup_test_value", {"key": "alpha"}, "c1"),
            AIMessage(content="Alpha is 11."),
            tool_call("lookup_test_value", {"key": "gamma"}, "c2"),
            AIMessage(content="Gamma is 33."),
        ]
    )
    _ask(agent, "alpha?", thread="s1")

    msgs = _ask(agent, "and gamma?", thread="s1")["messages"]
    turn = extract_turn(msgs)

    # The thread kept turn 1 (memory) ...
    assert any(isinstance(m, ToolMessage) and m.artifact and m.artifact["key"] == "alpha" for m in msgs)
    # ... but evidence for this turn contains only turn 2's tool result.
    assert [e["artifact"]["key"] for e in turn["evidence"]] == ["gamma"]
    assert turn["reply"] == "Gamma is 33."


def test_separate_threads_do_not_share_memory():
    agent = _agent([AIMessage(content="one"), AIMessage(content="two")])
    _ask(agent, "first", thread="a")

    msgs = _ask(agent, "second", thread="b")["messages"]

    assert [m.content for m in msgs if m.type == "human"] == ["second"]


def test_invalid_tool_input_becomes_error_tool_message():
    agent = _agent([tool_call("lookup_test_value", {"key": "NOT VALID!"}, "c1"), AIMessage(content="Sorry.")])

    turn = extract_turn(_ask(agent, "bad")["messages"])

    [ev] = turn["evidence"]
    assert ev["status"] == "error"
    assert ev["artifact"] is None
    assert turn["reply"] == "Sorry."


def test_tool_execution_error_is_returned_to_model():
    agent = _agent([tool_call("lookup_test_value", {"key": "delta"}, "c1"), AIMessage(content="Not found.")])

    msgs = _ask(agent, "delta?")["messages"]
    tool_msg = next(m for m in msgs if isinstance(m, ToolMessage))

    assert tool_msg.status == "error"
    assert "KeyError" in tool_msg.content
    assert extract_turn(msgs)["reply"] == "Not found."


def test_model_call_limit_stops_a_looping_agent():
    looping = [tool_call("lookup_test_value", {"key": "alpha"}, f"c{i}") for i in range(20)]
    agent = _agent(looping, max_model_calls=3)

    msgs = _ask(agent, "loop")["messages"]

    ai_calls = [m for m in msgs if isinstance(m, AIMessage) and m.tool_calls]
    assert len(ai_calls) == 3
