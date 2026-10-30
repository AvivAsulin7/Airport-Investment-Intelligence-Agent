"""LangChain agent factory and turn-result extraction (Phase 4 foundation).

The domain tools arrive in Phase 7; Phase 4 wires the mechanics with a test tool:
create_agent + in-memory checkpointer + tool-error middleware + model-call limit,
and extraction of this turn's tool artifacts (architecture.md §10.1).
"""

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolErrorMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.settings import Settings


def build_chat_model(settings: Settings) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    # No temperature: current Claude models reject non-default sampling params.
    return ChatAnthropic(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        reasoning_effort=settings.llm_effort,
    )


def _tool_error_content(exc: Exception, request: Any) -> str:
    # Name the exception type only; raw messages may carry internal detail.
    return f'{{"ok": false, "error": {{"code": "TOOL_ERROR", "type": "{type(exc).__name__}"}}}}'


def build_agent(model: BaseChatModel, tools: list, system_prompt: str, max_model_calls: int):
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=InMemorySaver(),
        middleware=[
            ToolErrorMiddleware(on_error=_tool_error_content),
            ModelCallLimitMiddleware(run_limit=max_model_calls, exit_behavior="end"),
        ],
    )


def _text_only(message: AIMessage) -> str:
    """Return only text blocks; thinking and tool-use blocks are excluded."""
    if isinstance(message.content, str):
        return message.content
    return "".join(b.get("text", "") for b in message.content if isinstance(b, dict) and b.get("type") == "text")


def extract_turn(messages: list) -> dict[str, Any]:
    """Split this turn's messages (after the last HumanMessage) into reply text and evidence."""
    last_human = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
    turn = messages[last_human + 1 :]
    call_args = {tc["id"]: tc["args"] for m in turn if isinstance(m, AIMessage) for tc in m.tool_calls}
    evidence = [
        {
            "tool": m.name,
            "tool_call_id": m.tool_call_id,
            "input": call_args.get(m.tool_call_id),
            "status": m.status,
            "artifact": m.artifact,
        }
        for m in turn
        if isinstance(m, ToolMessage)
    ]
    ai_messages = [m for m in turn if isinstance(m, AIMessage)]
    reply = _text_only(ai_messages[-1]) if ai_messages else ""
    return {"reply": reply, "evidence": evidence}
