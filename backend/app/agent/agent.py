"""LangChain agent factory and turn-result extraction.

create_agent + in-memory checkpointer + tool-error middleware + model-call limit (Phase 4),
and extraction of this turn's tool artifacts as evidence (architecture.md §10.1).
"""

import json
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolErrorMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.settings import Settings

# Text ModelCallLimitMiddleware(exit_behavior="end") appends when the limit is hit (observed, langchain 1.4.7).
LIMIT_MARKER = "Model call limits exceeded"
INCOMPLETE_NOTE = (
    "Analysis incomplete: the agent reached its tool-call limit for this question. "
    "The evidence gathered so far is shown; please narrow the question."
)


def build_chat_model(settings: Settings) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    # No temperature: current Claude models reject non-default sampling params.
    return ChatAnthropic(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        reasoning_effort=settings.llm_effort,
    )


def _tool_error_content(exc: Exception, request: Any) -> str:
    """Validation-type errors are returned verbatim so the model can correct itself; anything
    else is reported by type only (raw messages may carry internal detail)."""
    from app.agent.tools import USER_FACING_ERRORS

    if isinstance(exc, USER_FACING_ERRORS):
        return json.dumps({"ok": False, "error": {"code": type(exc).__name__, "message": str(exc)}})
    return json.dumps({"ok": False, "error": {"code": "TOOL_ERROR", "type": type(exc).__name__}})


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
    """Split this turn's messages (after the last HumanMessage) into reply text and evidence.

    Evidence items keep the full deterministic artifact untouched; sources and warnings are
    aggregated from the artifacts, never from model text.
    """
    last_human = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
    turn = messages[last_human + 1 :]
    call_args = {tc["id"]: tc["args"] for m in turn if isinstance(m, AIMessage) for tc in m.tool_calls}
    evidence = []
    for m in turn:
        if not isinstance(m, ToolMessage):
            continue
        item = {
            "tool": m.name,
            "tool_call_id": m.tool_call_id,
            "input": call_args.get(m.tool_call_id),
            "status": m.status,
            "artifact": m.artifact,
        }
        if m.status == "error":
            item["error"] = m.content if isinstance(m.content, str) else json.dumps(m.content)
        evidence.append(item)

    sources, warnings, seen = [], [], set()
    for ev in evidence:
        art = ev["artifact"] or {}
        for p in art.get("provenance", []):
            key = (p.get("source_type"), p.get("name"), p.get("observation_period"))
            if key not in seen:
                seen.add(key)
                sources.append(p)
        warnings += art.get("warnings", [])

    ai_messages = [m for m in turn if isinstance(m, AIMessage)]
    reply = _text_only(ai_messages[-1]) if ai_messages else ""
    hit_limit = reply.startswith(LIMIT_MARKER)
    incomplete = hit_limit or bool(ai_messages and ai_messages[-1].tool_calls)
    if incomplete:
        reply = INCOMPLETE_NOTE if hit_limit or not reply else reply + "\n\n" + INCOMPLETE_NOTE
    errors = [f"{ev['tool']}: {ev['error']}" for ev in evidence if ev["status"] == "error"]
    if incomplete:
        status = "incomplete"
    elif errors:
        status = "completed_with_tool_errors"
    else:
        status = "complete"
    return {
        "reply": reply,
        "evidence": evidence,
        "sources": sources,
        "warnings": list(dict.fromkeys(warnings)),
        "incomplete": incomplete,
        "status": status,
        "errors": errors,
    }
