"""FastAPI entry point.

- GET  /api/health          LLM configuration status and a live BTS API connectivity check.
- POST /api/chat            LangChain agent turn; returns the reply plus structured evidence (Phase 7).
- POST /api/demo/{scenario} Labelled deterministic demo without an LLM (D-032).
- Serves the built React app (frontend/dist) from the same origin when it exists (D-034).
"""

import logging
import time
import uuid
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent.agent import build_agent, build_chat_model, extract_turn
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import build_tools
from app.data import bts_api
from app.data.layer import load_data_layer
from app.data.snapshots import SnapshotError
from app.engine.service import AnalyticsService
from app.settings import get_settings

log = logging.getLogger("airport_agent")

MAX_TURNS = 30  # P-016
IDLE_SECONDS = 2 * 3600  # P-016


class ChatRequest(BaseModel):
    session_id: str | None = Field(None, pattern=r"^[0-9a-f-]{36}$")
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """Stable /api/chat contract (documented in README.md). Evidence, sources and warnings
    cover the current turn only; conversation memory is kept server-side per session."""

    session_id: str
    mode: Literal["agent"] = "agent"
    status: Literal["complete", "completed_with_tool_errors", "incomplete"]
    reply_markdown: str
    evidence: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    warnings: list[str]
    errors: list[str]
    incomplete: bool
    notice: str | None = None


DEMO_SCENARIOS = {
    "q1": ("Which airports in New England are strong candidates for terminal expansion?",
           "Deterministic ranking of FAA primary airports in the New England region (default weights)."),
    "q2": ("Compare LA and Santa Ana airport congestion levels.",
           "'LA' interpreted as LAX, 'Santa Ana' as SNA; delay-based congestion comparison."),
    "q3": ("What is the percentage of long haul flights out of Anchorage airport?",
           "Long-haul = route distance >= 3,000 statute miles; passenger classes (F+L) plus the all-class figure."),
    "q4": ("What is the unmet flight demand in SFO airport and why?",
           "Observed demand and capacity-pressure indicators vs large-hub peers; unmet demand is not measured."),
}


class _Runtime:
    """Lazily built service, agent and in-memory sessions (no database, P-016)."""

    def __init__(self, service: AnalyticsService | None = None, chat_model=None):
        self._service = service
        self._chat_model = chat_model
        self._agent = None
        self.sessions: dict[str, dict] = {}

    @property
    def service(self) -> AnalyticsService:
        if self._service is None:
            try:
                self._service = AnalyticsService(load_data_layer(get_settings()))
            except SnapshotError as exc:
                raise HTTPException(503, f"Data snapshots unavailable: {exc}") from exc
        return self._service

    def agent(self):
        if self._agent is None:
            settings = get_settings()
            model = self._chat_model
            if model is None:
                if not settings.llm_configured:
                    raise HTTPException(503, "LLM not configured (ANTHROPIC_API_KEY missing). "
                                             "Use the deterministic demo: POST /api/demo/{q1..q4}.")
                model = build_chat_model(settings)
            self._agent = build_agent(model, build_tools(self.service), SYSTEM_PROMPT, settings.agent_max_model_calls)
        return self._agent

    def session(self, session_id: str | None) -> tuple[str, str, str | None]:
        """Return (session_id, thread_id, notice). Idle sessions restart; long ones are refused."""
        now = time.monotonic()
        notice = None
        s = self.sessions.get(session_id) if session_id else None
        if s and now - s["last"] > IDLE_SECONDS:
            s, notice = None, "Previous conversation expired after 2 hours idle; starting a new one."
        if s is None:
            session_id = str(uuid.uuid4())
            s = self.sessions[session_id] = {"thread": str(uuid.uuid4()), "turns": 0, "last": now}
        if s["turns"] >= MAX_TURNS:
            raise HTTPException(409, f"Conversation limit of {MAX_TURNS} turns reached; please start a new chat.")
        s["turns"] += 1
        s["last"] = now
        return session_id, s["thread"], notice


def create_app(service: AnalyticsService | None = None, chat_model=None) -> FastAPI:
    app = FastAPI(title="Airport Investment Intelligence Agent")
    rt = _Runtime(service, chat_model)
    app.state.runtime = rt

    @app.get("/api/health")
    def health() -> dict:
        settings = get_settings()
        return {
            "status": "ok",
            "llm_configured": settings.llm_configured,
            "llm_model": settings.llm_model,
            "bts_api": bts_api.check_connectivity(settings),
        }

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(req: ChatRequest) -> ChatResponse:
        agent = rt.agent()
        session_id, thread, notice = rt.session(req.session_id)
        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": req.message}]},
                config={"configurable": {"thread_id": thread}},
            )
        except HTTPException:
            raise
        except Exception as exc:  # model/provider failure; never leak internals
            ref = uuid.uuid4().hex[:8]
            log.exception("chat failed ref=%s", ref)
            raise HTTPException(502, f"The language model call failed ({type(exc).__name__}, ref {ref}).") from exc
        turn = extract_turn(result["messages"])
        return ChatResponse(
            session_id=session_id,
            status=turn["status"],
            reply_markdown=turn["reply"],
            evidence=turn["evidence"],
            sources=turn["sources"],
            warnings=turn["warnings"],
            errors=turn["errors"],
            incomplete=turn["incomplete"],
            notice=notice,
        )

    @app.post("/api/demo/{scenario}")
    def demo(scenario: Literal["q1", "q2", "q3", "q4"]) -> dict:
        """Fixed, labelled deterministic presets (no LLM, not conversational, D-032)."""
        svc = rt.service
        if scenario == "q1":
            tool, env = "rank_airports", svc.rank(region="New England")
        elif scenario == "q2":
            la = svc.data.airports.search("LA").airports[0].code
            sa = svc.data.airports.search("Santa Ana").airports[0].code
            tool, env = "compare_airports", svc.compare([la, sa])
        elif scenario == "q3":
            tool, env = "get_long_haul_share", svc.long_haul("ANC")
        else:
            tool, env = "get_demand_pressure_profile", svc.demand_profile("SFO")
        question, caption = DEMO_SCENARIOS[scenario]
        return {
            "mode": "demo",
            "label": "Deterministic demo - AI agent not used. Fixed example analysis; no free-form questions.",
            "scenario": scenario,
            "question": question,
            "caption": caption,
            "evidence": [{"tool": tool, "status": "success", "artifact": env}],
            "sources": env["provenance"],
            "warnings": env["warnings"],
        }

    dist = get_settings().frontend_dist
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="spa")
    return app


app = create_app()
