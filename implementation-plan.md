# Implementation Plan: Phase Roadmap

**Status:** approved roadmap (Phase 1). This is a **high-level phase roadmap** for organizing work and Git commits. It is **not** a finalized technical plan. No technology stack, data source, scoring formula, or AI framework has been selected (NOTES.md D-005).

**References:** `FDE Exam 2.pdf` (source of truth), `requirements.md`, `CLAUDE.md`, `NOTES.md`.

## Ground rules
- Phases run one at a time. **Each phase starts only after explicit user approval** (CLAUDE.md §2).
- **Git commits are made only after the user has reviewed and approved a phase.** Each phase normally ends with one commit, which may be split if the user asks. The commit messages below are suggestions.
- Phases 3–9 are **proposed** and will be revised after Phase 2 data research.
- The time budget is about 24 hours in total (PDF: "Timeframe: 24 hours"). Time estimates are indicative only.
- Work that does not fit is listed as known gaps, not rushed (PDF: "clarity, reasoning, and thoughtful design over completeness or polish").

## Overview

| # | Phase | Status | Indicative time |
|---|---|---|---|
| 1 | Requirements & Project Setup | **Completed** (approved for finalization, D-012) | ~1 h |
| 2 | Data Sources Research | **Approved / not started** | ~2 h (time-boxed, D-009) |
| 3 | Architecture & Scoring Design | Pending | ~1.5 h |
| 4 | Project Foundation | Pending | ~1 h |
| 5 | Aviation Data Integration | Pending | ~3 h |
| 6 | Deterministic Analytics Engine | Pending | ~3 h |
| 7 | AI Agent & Conversation | Pending | ~4 h |
| 8 | Chat UI & End-to-End Integration | Pending | ~3 h |
| 9 | Testing, Documentation & Delivery | Pending | ~3 h |
| | Buffer for blockers and rework | n/a | ~2.5 h |
| | **Total** | | **~24 h** |

---

## Phase 1: Requirements & Project Setup
- **Status:** Completed. Approved for finalization (NOTES.md D-012).
- **Goal:** Understand the assignment, separate explicit requirements from interpretations, and set the working rules.
- **Deliverables:** `requirements.md`, `CLAUDE.md`, `NOTES.md`, `implementation-plan.md`.
- **Acceptance criteria:**
  - Every PDF requirement and all four example questions are captured.
  - Ambiguities, risks, and the MVP checklist are documented.
  - Working rules and the decision log exist.
- **Dependencies:** None.
- **Suggested commit:** `docs: add requirements analysis, working rules, decision log, and phase roadmap`

## Phase 2: Data Sources Research
- **Status:** Approved / not started (D-008). Time-boxed to ~2 h (D-009).
- **Goal:** Check, using real requests or downloads, which public aviation data can support Q1–Q4, and find blockers early.
- **Deliverables:**
  - `data-sources-research.md`: the data feasibility report.
  - A feasibility matrix covering question × source × fields × coverage × freshness × access/limits × gaps.
  - A feasibility verdict for each of Q1–Q4 (answerable / proxy only / not supportable).
  - Updated assumptions A-001–A-010 in NOTES.md.
- **Acceptance criteria:**
  - Every claim about a source is backed by a real request, a sample, or official documentation, or is labelled unverified.
  - Blockers (keys, rate limits, paywalls) are identified.
  - Recommended sources and alternatives are presented for approval. Nothing is selected silently.
- **Dependencies:** Phase 1.
- **Suggested commit:** `docs: add public aviation data feasibility research`

## Phase 3: Architecture & Scoring Design
- **Status:** Pending (proposed).
- **Goal:** Decide the architecture, stack, data access approach, metric definitions, scoring methodology, and how responsibilities split between AI and deterministic code. Decisions are based on Phase 2 evidence.
- **Deliverables:**
  - A design proposal: options, tradeoffs, and a recommendation for each major decision.
  - Metric definitions (congestion, long haul, unmet-demand proxy, expansion indicator).
  - Scoring formulas and weights.
  - Approved decisions recorded in NOTES.md.
  - First draft of `architecture.md`, the design/architecture document required by the PDF (requirements.md D-2). It is finalized in Phase 9.
- **Acceptance criteria:**
  - Open decisions O-002–O-014 are resolved or explicitly deferred, with user approval.
  - Each metric can be computed from data verified in Phase 2.
  - LLM and deterministic responsibilities are clearly separated (CLAUDE.md §5).
- **Dependencies:** Phase 2.
- **Suggested commit:** `docs: add architecture and scoring methodology design`

## Phase 4: Project Foundation
- **Status:** Pending (proposed).
- **Goal:** Set up a minimal project skeleton based on the approved design.
- **Deliverables:**
  - Project structure and a minimal dependency list.
  - Configuration that keeps secrets out of git (env template with placeholders, ignore rules).
  - A basic test setup.
  - Run instructions (a stub is enough at this stage).
- **Acceptance criteria:**
  - The project installs and runs an empty or "hello" entry point.
  - Tests run.
  - No secrets are tracked.
  - Only the dependencies justified in Phase 3 are added.
- **Dependencies:** Phase 3.
- **Suggested commit:** `chore: set up project foundation and configuration`

## Phase 5: Aviation Data Integration
- **Status:** Pending (proposed).
- **Goal:** Retrieve and normalize data from the approved public sources (PDF FR-1).
- **Deliverables:**
  - Data access modules for each source.
  - Airport and region reference handling (entity resolution).
  - The caching or snapshot approach, if approved (O-007).
  - Source and freshness metadata attached to the data.
- **Acceptance criteria:**
  - Real data is retrieved for the airports needed by Q1–Q4, as far as Phase 2 found feasible.
  - Errors and missing data are handled explicitly.
  - Data period and source are kept for citation in answers.
- **Dependencies:** Phases 3 and 4.
- **Suggested commit:** `feat: integrate public aviation data sources`

## Phase 6: Deterministic Analytics Engine
- **Status:** Pending (proposed).
- **Goal:** Implement the approved metrics and the scoring/ranking/comparison logic in code (PDF: "deterministic scoring or ranking logic").
- **Deliverables:**
  - Metric calculations.
  - Ranking and comparison functions.
  - Structured outputs that include inputs, definitions, and limitations.
  - Unit tests.
- **Acceptance criteria:**
  - The same inputs always produce the same outputs.
  - Formulas match the design document.
  - Tests cover the core scoring.
  - No LLM is involved in producing any score or metric value.
- **Dependencies:** Phase 5 (and the Phase 3 formulas).
- **Suggested commit:** `feat: add deterministic scoring and comparison engine`

## Phase 7: AI Agent & Conversation
- **Status:** Pending (proposed).
- **Goal:** Add an AI agent that interprets questions, calls the data and analytics tools, explains its reasoning, and supports follow-ups (PDF FR-0, FR-3, FR-4).
- **Deliverables:**
  - Agent orchestration.
  - Tool interfaces to the Phase 5 and Phase 6 modules.
  - Conversation memory.
  - Grounding rules (numbers only come from tools).
  - Behaviour for out-of-scope questions and for stating assumptions and uncertainty.
- **Acceptance criteria:**
  - Q1–Q4 produce grounded responses, or honest statements of limitation (requirements.md M-9, M-10).
  - Follow-ups work in a multi-turn session (M-6).
  - Assumptions, data freshness, and scope are stated (M-8).
- **Dependencies:** Phase 6.
- **Suggested commit:** `feat: add AI agent with tool use and conversational follow-ups`

## Phase 8: Chat UI & End-to-End Integration
- **Status:** Pending (proposed).
- **Goal:** Give reviewers a chat interface to use the agent end to end (PDF: "chat interface"). Voice is a bonus only if time allows.
- **Deliverables:**
  - A chat interface of the approved form (O-009).
  - End-to-end wiring.
  - Optional voice, only if explicitly approved and time remains.
- **Acceptance criteria:**
  - A reviewer can start the app and have a multi-turn conversation (M-7).
  - Q1–Q4 run end to end through the UI.
- **Dependencies:** Phase 7.
- **Suggested commit:** `feat: add chat interface and end-to-end integration`

## Phase 9: Testing, Documentation & Delivery
- **Status:** Pending (proposed).
- **Goal:** Verify the MVP against the acceptance checklist and complete the deliverables.
- **Deliverables:**
  - Final run of the tests and the example questions.
  - Final `architecture.md`, started in Phase 3, covering scoring methodology, key tradeoffs, and where/how AI is used.
  - README with setup and run steps.
  - A list of known gaps and future work.
  - Final NOTES.md update.
- **Acceptance criteria:**
  - Every mandatory item M-1–M-15 in requirements.md §7.1 is verified, or explicitly listed as a gap.
  - No secrets are in the repository.
  - A fresh setup runs from the README.
- **Dependencies:** Phase 8.
- **Suggested commit:** `docs: finalize design document, README, and delivery checks`
