# Implementation Plan: Phase Roadmap

**Status:** updated 2026-10-30 at the close of Phase 3 (D-043). This plan reflects the approved architecture:
- React + TypeScript + Vite (D-022)
- Python + FastAPI (D-023)
- LangChain (D-024)
- A single-server review setup (D-034)
- A live BTS API with labelled snapshots (D-016, D-017)

The budget is the approved **24 h planning target with 3 h contingency** (D-031). Detailed design is in `architecture.md`, and the decisions are in `NOTES.md`.

## Ground rules
- One phase at a time. **Each phase starts only after explicit user approval** (CLAUDE.md §2).
- **The user makes all Git commits manually** after reviewing a phase (D-026, CLAUDE.md §9). The commit messages below are suggestions.
- Every phase updates the NOTES.md decision journal, including **actual vs. planned time** from Phase 4 onward (D-027, D-031).
- **The four assignment scenarios (Q1–Q4) must remain viable whenever scope is reduced** (D-031). They are evaluation scenarios, not hardcoded paths (D-025).
- Design statements are not implementation evidence. A decision is marked IMPLEMENTED only with code plus a check result.

## Overview and budget

| # | Phase | Status | Original h | Planned h |
|---|---|---|---|---|
| 1 | Requirements & Project Setup | **Completed** (D-012) | 1.0 | 1.0 |
| 2 | Data Sources Research | **Completed** (D-015) | 2.0 | 2.0 |
| 3 | Architecture & Scoring Design | **Completed** (committed `3f29efd`) | 1.5 | 2.0 |
| 4 | Project Foundation + smoke tests | **Approved.** Real-LLM smoke tests **PASS with `claude-sonnet-5-5`** (2026-10-30, D-047), after earlier blocks for no key and then no credits. | 1.0 | 1.5 |
| 5 | Aviation Data Integration | **Approved** (P-038 to P-045; Sonnet default D-048) | 3.0 | 3.0 |
| 6 | Deterministic Analytics Engine | **Implemented, awaiting review** (84 offline + 7 live tests pass) | 3.0 | 2.5 |
| 7 | LangChain Agent & Conversation | Pending | 4.0 | 3.0 |
| 8 | React Chat UI & End-to-End Integration | Pending | 3.0 | 3.5 |
| 9 | Testing, Documentation & Delivery | Pending | 3.0 | 2.5 |
| | **Contingency** | Reserved | 2.5 | **3.0** |
| | **Total** | | 24.0 | **24.0** |

Estimates for Phases 1–3 are approximate (actual times were not tracked precisely). Phase 4 onward records actual times.

## Essential requirements (never cut)
1. **The live BTS public API is called at runtime** for traffic KPIs. Snapshots are labelled as datasets, never as APIs (FR-1, D-017).
2. **Deterministic Python** for all KPIs, derived comparisons, normalization, and scoring, with unit tests (NFR-1, D-028, D-039).
3. **A LangChain agent** using our Python tools, with Pydantic-validated inputs and conversational follow-ups via in-memory sessions (FR-0, FR-4, D-024, D-042).
4. **A React chat UI** that renders Python-generated evidence (tables and cards), sources, windows, and warnings (NFR-2, D-030).
5. **Q1–Q4 answerable end to end**, with disclosed assumptions, windows, and uncertainty (NFR-3, M-9).
6. **`architecture.md` finalized** (scoring methodology, tradeoffs, AI usage) and a **README** with run steps (D-1, D-2).
7. No secrets in Git. No processed or raw datasets in Git until the D-037 checks pass.

## Optional cut list (cut in this order before touching anything essential; none of these breaks Q1–Q4)
1. Voice (bonus, already excluded, P-018/D-040).
2. Optional frontend Vitest/RTL test.
3. `aggregate_metrics` generic tool (D-044; time-boxed ≤ 1 h, only after Q1–Q4 pass).
4. No-key deterministic demo → banner only (D-032).
5. `rank_changes` diff.
6. "LA-area" alternative offer (LAX default stays).
7. Q4 peer percentiles → plain values (the three-block Q4 answer stays).
8. 3-month on-time data (not planned; 1 month stays).

---

## Phase 1: Requirements & Project Setup
- **Status:** Completed (D-012).
- **Deliverables:** `requirements.md`, `CLAUDE.md`, `NOTES.md`, `implementation-plan.md`.
- **Commit:** done (`21001b7`).

## Phase 2: Data Sources Research
- **Status:** Completed (D-015).
- **Deliverables:** `data-sources-research.md`, with NOTES.md updated. Approved data decisions: D-016 to D-021.
- **Commit:** done (`3b91e03`).

## Phase 3: Architecture & Scoring Design
- **Status:** Completed. The design is approved (D-022 to D-044). The user's Phase 3 commit is pending.
- **Deliverables:** `architecture.md` (DRAFT rev 4; finalized in Phase 9), the NOTES.md decision journal, `.gitignore` fix (D-036), the CLAUDE.md journal rule, and this plan.
- **Open for confirmation:** P-029 (precise field and edge-case definitions), P-030 (aggregate tool design), P-022 (default model), and P-028 (fallback order). These are checked in Phase 4–7 as noted below.
- **Suggested commit:** `docs: finalize phase 3 architecture, scoring design, and decision journal`

## Phase 4: Project Foundation + Smoke Tests (1.5 h)
- **Status (2026-10-30):** implemented and awaiting user review. Smoke-test results are in NOTES.md §3b. All checks pass except the real-model checks (#1 and the thinking round-trip in #3), which are **BLOCKED** until `ANTHROPIC_API_KEY` is set. Smoke test #4's middleware was implemented with the built-in `ToolErrorMiddleware` (P-031). Smoke test #5's loop limit was implemented with `ModelCallLimitMiddleware` (P-032).
- **Goal:** a minimal skeleton, plus empirical verification of the risky integration assumptions **before** building on them.
- **Deliverables:**
  - `backend/` (FastAPI app with `/api/health`, settings from env, pytest setup).
  - `frontend/` (Vite React-TS template, `/api` dev proxy, typed API client stub).
  - FastAPI serving the built SPA (D-034).
  - `.env.example` with placeholders only. *(Later removed in the Phase 5 review, D-046. Variables are documented in README.md and the root `.env` is the only local config file.)*
  - Pinned dependency versions.
  - A README stub.
- **Smoke tests (record the results in NOTES.md):**
  1. **Model ID and SDK compatibility** (D-033): `ChatAnthropic(model=LLM_MODEL)` accepts the configured ID. One `create_agent` run with one tool call succeeds. Apply the fallback order P-028 if it fails, and record why.
  2. **Artifact propagation** (A-022): a `content_and_artifact` tool's artifact is present on the returned `ToolMessage`. Otherwise switch to the `contextvars` collector.
  3. **Memory** (A-019): a 2-turn conversation with the same `thread_id` recalls turn-1 tool output, and thinking blocks round-trip without error.
  4. **Validation errors** (A-018): invalid tool args → observed default behaviour. Confirm the `@wrap_tool_call` middleware returns a structured error.
  5. **Loop limit** (A-020): `recursion_limit` stops a looping run as expected.
  6. **Fake chat model** (A-021): available for no-LLM API tests.
  7. **Live BTS API** reachable from the backend (`/api/health`).
- **Acceptance criteria:**
  - The backend starts, and `/api/health` returns 200.
  - `npm run build` succeeds, and the SPA is served by FastAPI.
  - pytest runs.
  - Smoke-test outcomes are documented, including failures and the fallback chosen.
  - No secrets are tracked.
- **Dependencies:** Phase 3 commit and user approval.
- **Suggested commit:** `chore: set up FastAPI + React foundation and LangChain smoke tests`

## Phase 5: Aviation Data Integration (3.0 h)
- **Status (2026-10-30):** implemented and awaiting user review. Details are in NOTES.md §3c.
  - The live BTS API client and snapshots are built for July 2026 (T-100 July 2026 available, A-015 verified).
  - The snapshots exactly match the live API for the same month (ANC, SFO, SNA).
  - Tests: 48 offline passed (including 4 against the real snapshots), and 2 live passed. The real-LLM tests need `RUN_LLM_TESTS=1`. They **pass with `claude-sonnet-5-5`** (2026-10-30).
  - The builder lives at `backend/scripts/build_snapshots.py` (P-042). OurAirports is deferred (P-043).
- **Goal:** retrieve and prepare all approved data with provenance.
- **Deliverables:**
  - **BTS API client** (`r495-tyji`): whitelisted SoQL, timeout and retry, TTL cache, labelled recorded fallback.
  - **`scripts/build_snapshots.py`**: on-time July 2026 (download verified in Phase 2), T-100 Segment All Carriers **July 2026, subject to availability verification (A-015)**, FAA CY2025 enplanements, and an optional OurAirports subset (A-014). Raw files go to the gitignored `data/raw/`. Small processed files plus `manifest.json` (URL, retrieval date, data period, checksum) go to the gitignored `data/processed/` (D-037).
  - Snapshot loader with manifest validation.
  - Airport and region resolver (FAA region / state, primary airports; "LA" → LAX with a note, P-011).
  - Licensing and provenance check notes for A-011 and A-014 (a prerequisite for ever committing snapshots).
- **Acceptance criteria:**
  - Live API rows are retrieved for the Q1–Q4 airports.
  - Snapshots are built and validated.
  - **If July 2026 T-100 is unavailable, an alternative month is used and the window mismatch is reported clearly** (D-040).
  - Data-layer tests pass (recorded fixtures, no network).
- **Dependencies:** Phase 4.
- **Suggested commit:** `feat: add BTS API client, snapshot builder, and airport resolver`

## Phase 6: Deterministic Analytics Engine (2.5 h)
- **Status (2026-10-30):** implemented in `backend/app/engine/` and awaiting review. Details and scenario results are in NOTES.md §3d.
  - Both §9 worked examples pass exactly.
  - Q1–Q4 run end to end on real data (live API plus July 2026 snapshots).
  - Open item: OQ-13 (small-airport noise in the Q1 ranking). **Resolved by D-049:** methodology kept, small-sample warnings surfaced in `data.small_sample_airports` and the top-level `warnings`, the interpretation text strengthened, and an optional `hub_classes` filter added. 89 offline tests pass.
- **Goal:** implement the approved formulas (D-039; definitions P-029) as pure Python.
- **Deliverables:**
  - Metric registry.
  - KPI functions (§6 of architecture.md).
  - Scoring v1:
    - candidate-group min-max,
    - minimum 3 values per KPI,
    - coverage-weighted score with the 0.60 threshold,
    - `low_sample` warnings (D-029),
    - edge cases (§7.1b),
    - tie-break,
    - `rank_changes`.
  - Comparison (with derived differences, D-028).
  - Long-haul share (P-012).
  - Demand-pressure profile (P-013).
  - Confidence rules.
- **Acceptance criteria:**
  - Unit tests pass, including the architecture §9 worked examples:
    - B 55.0 / A 51.1 / D 50.0 / C 45.0
    - C 70.0 / A 54.7 / D 50.0 / B 30.0
    - long-haul 9.5% / 26.8%
    - delay rates 25.0% / 25.0%
  - The edge cases in §7.1b are tested.
  - No LLM or LangChain imports in the engine.
- **Dependencies:** Phase 5 (data accessors). It can start in parallel with fixtures.
- **Suggested commit:** `feat: add deterministic KPI, scoring, and comparison engine`

## Phase 7: LangChain Agent & Conversation (3.0 h)
- **Goal:** a LangChain agent that composes our tools to answer Q1–Q4 and analogous questions.
- **Deliverables:**
  - `create_agent` with `ChatAnthropic` (configurable model, D-033).
  - Thin `@tool` wrappers with Pydantic `args_schema` and `content_and_artifact` (D-042).
  - `@wrap_tool_call` error middleware.
  - `InMemorySaver` sessions (P-016).
  - System prompt: grounding, D-021 wording, out-of-scope behaviour (P-017), no LLM arithmetic.
  - `/api/chat` with evidence extraction (architecture §10.1).
  - `/api/demo/{scenario}` no-key demo (D-032).
  - **Stretch, ≤ 1 h, only after Q1–Q4 pass:** `aggregate_metrics` with the session evidence store (D-044, P-030). Otherwise deferred and documented.
- **Acceptance criteria:**
  - Fake-model tests: single, parallel, and failing tool calls. Evidence equals direct engine output. A second turn returns only that turn's evidence (D-041).
  - **Async path:** if `/api/chat` uses `agent.ainvoke`, repeat the artifact-extraction and memory tests on the async path. Phase 4 verified the synchronous `invoke` path only (A-022).
  - **Real-model smoke tests** (`RUN_LLM_TESTS=1 pytest -m llm`) pass with the configured `LLM_MODEL`. **Done 2026-10-30 with `claude-sonnet-5-5`: 2/2 PASS** (tool call, artifact, memory). Re-run only if the model or the LangChain versions change.
  - **Model for Phase 7 scenario runs:** `claude-sonnet-5-5` (D-047, cost). Keep the paid scenario runs to the minimum needed (Q1–Q4 plus one analogous question each, plus follow-ups).
  - Real-model runs of Q1–Q4 return evidence and disclosures.
  - Follow-ups work.
- **Dependencies:** Phase 6.
- **Suggested commit:** `feat: add LangChain agent, tools, sessions, and chat API`

## Phase 8: React Chat UI & End-to-End Integration (3.5 h)
- **Goal:** the reviewer-facing chat with typed evidence rendering.
- **Deliverables:**
  - ChatPanel and MessageBubble.
  - `EvidenceRenderer` (ranking, comparison, long-haul, demand profile, traffic, operations, airports, metrics, aggregate, error).
  - SourcesList (API live / API fallback / dataset snapshot).
  - Warnings and confidence badges.
  - ModeBanner (agent vs. labelled deterministic demo).
  - Preset buttons in demo mode, with chat input disabled.
  - Shared JSON evidence fixtures type-checked by `tsc`.
- **Acceptance criteria:**
  - Q1–Q4 plus one analogous question each run end to end through the UI with the built SPA served by FastAPI.
  - Follow-ups work.
  - The no-key demo is clearly labelled and non-conversational.
- **Dependencies:** Phase 7.
- **Suggested commit:** `feat: add React chat UI with evidence rendering`

## Phase 9: Testing, Documentation & Delivery (2.5 h)
- **Goal:** verify against the requirements.md §7.1 checklist and finish the deliverables.
- **Deliverables:**
  - Full test run.
  - The scenario evaluation (Q1–Q4 plus analogous questions plus follow-ups) recorded in NOTES.md.
  - **Final `architecture.md`.**
  - README:
    - setup,
    - snapshot build time (~6 min per on-time month),
    - key configuration,
    - the no-key demo,
    - known limitations.
  - A known-gaps list.
  - The final NOTES.md (outcomes and interview preparation).
- **Acceptance criteria:**
  - M-1 to M-15 are verified or listed as gaps.
  - A fresh setup runs from the README.
  - No secrets, and no datasets committed unless D-037 is satisfied.
- **Dependencies:** Phase 8.
- **Suggested commit:** `docs: finalize architecture, README, and delivery checks`
