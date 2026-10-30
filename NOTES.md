# NOTES.md: Engineering Decision Journal

Project: Airport Investment Intelligence Agent (Deloitte Digital FDE take-home, 24 h).
Source of truth for requirements: `FDE Exam 2.pdf` (D-001). Companion documents: `requirements.md`, `data-sources-research.md`, `architecture.md`, `implementation-plan.md`, `CLAUDE.md`.

---

## 0. How this journal works

**Status values**
| Status | Meaning |
|---|---|
| **APPROVED** | The user explicitly approved it in the conversation. |
| **PROPOSED** | Recommended by the assistant, awaiting user approval. **Not** to be treated as decided. |
| **IMPLEMENTED** | Approved, and present in verified code, with test or check evidence. *(No decision has this status yet: no application code exists.)* |
| **REVISITED** | An earlier decision that was later changed or superseded. The original text is kept, with a pointer to its replacement. |

**Provenance of alternatives:**
- **[discussed]**: the alternative was raised in the conversation or the documents at the time.
- **[retrospective]**: the alternative was identified later, while writing this journal, for completeness.

**ID rules:**
- IDs are stable and never reused.
- `D-xxx` = a user decision, either approved or later revisited.
- `P-xxx` = an assistant proposal.
- The user's labels D1–D10 (from the Phase 3 revision request) are mapped to IDs in §1.

**Entry template (for every meaningful decision; CLAUDE.md §10 requires it for Phases 4–9):**
1. ID and title
2. Phase and status
3. Context / problem
4. Alternatives, in plain English, with pros and cons
5. Selected approach
6. Why it was selected
7. Why the alternatives were rejected
8. Tradeoffs and accepted risks
9. Validation / testing
10. Time and scope impact
11. Interview line (first person)

Small process decisions use the compact table in §2.1. That is a deliberate choice: they have no meaningful technical alternatives.

---

## 1. Chronological decision history

| Date | ID | Title | Phase | Status | User label |
|---|---|---|---|---|---|
| 2026-10-28 | D-001 | PDF is the single source of truth | 1 | APPROVED | |
| 2026-10-28 | D-002 | Phased, approval-gated workflow | 1 | APPROVED | |
| 2026-10-28 | D-003 | requirements.md created (Phase 1 deliverable) | 1 | APPROVED (via D-012) | |
| 2026-10-28 | D-004 | Working rules in CLAUDE.md, decisions in NOTES.md | 1 | APPROVED | |
| 2026-10-28 | D-005 | Do not choose a stack before data is verified | 1 | REVISITED (stack chosen: D-022 to D-024) | |
| 2026-10-28 | D-006 | Next phase = data research | 1 | APPROVED (via D-008) | |
| 2026-10-28 | D-007 | Phase 1 provisionally approved | 1 | REVISITED (superseded by D-012) | |
| 2026-10-28 | D-008 | Phase 2 approved | 2 | APPROVED | |
| 2026-10-28 | D-009 | Phase 2 time-boxed to about 2 h | 2 | APPROVED | |
| 2026-10-28 | D-010 | Investment *indicators*, not profitability or ROI | 1–2 | APPROVED | |
| 2026-10-28 | D-011 | Business goal unchanged | 1–2 | APPROVED | |
| 2026-10-28 | D-012 | Phase 1 approved for finalization | 1 | APPROVED | |
| 2026-10-28 | D-013 | Document names (data-sources-research.md, architecture.md) | 1 | APPROVED | |
| 2026-10-28 | D-014 | Assignment PDF kept local (gitignored) | 1 | APPROVED | |
| 2026-10-28 | D-026 | Git: the user stages, commits, and pushes manually | 1–2 | APPROVED (recorded retroactively; rule in CLAUDE.md §9) | |
| 2026-10-29 | D-015 | Phase 2 completed and approved; Phase 3 may start | 2 | APPROVED | |
| 2026-10-29 | D-016 | Data strategy 1: BTS-centric hybrid | 2 | APPROVED | D6 |
| 2026-10-29 | D-017 | Genuine public API use; files never called APIs | 2 | APPROVED | D6 |
| 2026-10-29 | D-018 | Analysis windows (12-month API, 1 month files) | 2 | APPROVED | D6/D7 |
| 2026-10-29 | D-019 | Small processed snapshots with provenance | 2 | APPROVED | D6 |
| 2026-10-29 | D-020 | FAA capacity PDFs as context only | 2 | APPROVED | D7 |
| 2026-10-29 | D-021 | Observed demand vs. pressure indicators vs. unmet demand | 2 | APPROVED | D7 |
| 2026-10-30 | P-001 to P-018 | Phase 3 rev 1 proposals | 3 | PROPOSED; P-001 (UI), P-002, P-003, P-004, P-005 REVISITED | |
| 2026-10-30 | D-022 | Frontend: React + TypeScript + Vite | 3 | APPROVED | D1 |
| 2026-10-30 | D-023 | Backend: Python + FastAPI | 3 | APPROVED | D2 |
| 2026-10-30 | D-024 | Orchestration: LangChain | 3 | APPROVED | D3 |
| 2026-10-30 | D-025 | Four PDF questions = evaluation scenarios, not limits | 3 | APPROVED | D10 |
| 2026-10-30 | D-027 | Maintain this decision journal through Phases 4–9 | 3 | APPROVED | |
| 2026-10-30 | P-019 | Structured artifacts + non-blocking numeric check | 3 | PROPOSED (supersedes P-005) | D4 |
| 2026-10-30 | P-020 | Revised 24 h budget with a 3 h contingency | 3 | PROPOSED | D5 |
| 2026-10-30 | P-021 | No-key "data explorer" mode | 3 | PROPOSED (supersedes P-004) | D8 |
| 2026-10-30 | P-022 | Model: `claude-opus-5-5` default, configurable | 3 | PROPOSED (supersedes P-003) | D9 |
| 2026-10-30 | P-023 | FastAPI serves the built SPA; Vite proxy in dev | 3 | PROPOSED | |
| 2026-10-30 | P-024 | LangChain tool design: thin `@tool` wrappers, `content_and_artifact` | 3 | PROPOSED | D3 |
| 2026-10-30 | P-025 | `.gitignore` fix (stop ignoring NOTES.md, add secret rules) | 3 | REVISITED → approved as D-036 | |
| 2026-10-30 | D-028 | All KPI calculations, derived comparisons, normalization, and scoring in deterministic Python | 3 (review) | APPROVED | review #2 |
| 2026-10-30 | D-029 | 300 flights/month = configurable data-quality **warning**, not an exclusion | 3 (review) | APPROVED | review #4 |
| 2026-10-30 | D-030 | Code-generated evidence rendered by React is preferred over scanning LLM text | 3 (review) | APPROVED (direction) | review #5 (D4) |
| 2026-10-30 | D-031 | 24 h budget approved as a planning target, 3 h contingency, all four scenarios kept viable | 3 (review) | APPROVED | review #6 (D5) |
| 2026-10-30 | D-032 | No-key mode limited to a clearly labelled deterministic demo | 3 (review) | APPROVED | review #7 (D8) |
| 2026-10-30 | D-033 | Model configurable; ID and SDK compatibility verified in the Phase 4 smoke test; fallback documented | 3 (review) | APPROVED | review #8 (D9) |
| 2026-10-30 | D-034 | Single FastAPI server serves the built React app for review; Vite proxy in dev | 3 (review) | APPROVED | review #9 |
| 2026-10-30 | D-035 | Pydantic tool input schemas; LangChain error, artifact, memory, and loop behaviour confirmed in Phase 4 | 3 (review) | APPROVED | review #10 |
| 2026-10-30 | D-036 | Fix the NOTES.md ignore rule safely (history kept, secrets ignored) | 3 (review) | APPROVED; `.gitignore` edited, commit pending with the user | review #11 |
| 2026-10-30 | D-037 | Do not commit processed snapshots until licensing and provenance checks are done | 3 (review) | APPROVED | review #12 |
| 2026-10-30 | D-038 | Update implementation-plan.md after the remaining design decisions are approved | 3 (review) | APPROVED | review #13 |
| 2026-10-30 | — | Runtime BTS API + separately labelled snapshots reaffirmed | 3 (review) | APPROVED (reaffirms D-016/D-017) | review #1 |
| 2026-10-30 | P-026 | Optional non-blocking text number check (deferred, not in the MVP baseline) | 3 (review) | PROPOSED (optional) | |
| 2026-10-30 | P-027 | Exact scoring specification v1 (refines P-006 to P-009) | 3 (review) | PROPOSED (awaiting review) | review #3 |
| 2026-10-30 | P-028 | Model fallback order for the Phase 4 smoke test | 3 (review) | PROPOSED | review #8 |
| 2026-10-30 | D-039 | Scoring v1 approved for the MVP: option A (candidate-group min-max), default weights, coverage rules, minimum 3 per KPI, small-sample warnings, tie-break; subject to precise field definitions | 3 (close) | APPROVED | close #1–#5 |
| 2026-10-30 | P-029 | Precise field, denominator, and edge-case definitions (delay rate, traffic fields, edge cases) | 3 (close) | PROPOSED (for confirmation) | close #2, #4, #6 |
| 2026-10-30 | D-040 | P-010 to P-018 approved (July 2026 route data subject to availability; mismatched windows reported) | 3 (close) | APPROVED | close #7 |
| 2026-10-30 | D-041 | Drop the post-hoc number scanner P-026; test artifact propagation LangChain → FastAPI → React | 3 (close) | APPROVED | close #8 |
| 2026-10-30 | D-042 | LangChain tools with Pydantic validation (P-024) and in-memory sessions (P-016) approved; single-server reaffirmed (D-034) | 3 (close) | APPROVED | close #10 |
| 2026-10-30 | D-043 | Update implementation-plan.md now (executes D-038) | 3 (close) | APPROVED; plan updated 2026-10-30 | close #14 |
| 2026-10-30 | D-044 | Generic `aggregate_metrics` tool over trusted evidence references (time-boxed, deferrable) | 3 (close) | APPROVED (direction) | close #15 |
| 2026-10-30 | P-030 | Detailed design of `aggregate_metrics` (evidence store, allowed operations, validation) | 3 (close) | PROPOSED | close #15 |
| 2026-10-30 | — | Reaffirmed: configurable model with verification in the Phase 4 smoke test (D-033), minimal labelled no-key demo (D-032), 24 h plan with 3 h contingency (D-031), no datasets in Git before checks (D-037) | 3 (close) | APPROVED (reaffirmations) | close #9, #11, #12, #13 |

---

## 2. Approved decisions

### 2.1 Process decisions (compact)
| ID | Decision | Context | Reason | Interview line |
|---|---|---|---|---|
| D-001 | `FDE Exam 2.pdf` is the single source of truth | Avoid scope drift in a 24 h exercise | Requirements are traceable | "Every requirement traces back to the brief, and anything beyond it is labelled as an interpretation or an option." |
| D-002 / D-006 / D-008 / D-012 / D-015 | Phases run one at a time and need explicit approval; phase approvals recorded | The user wanted control over major choices | Keeps decisions visible and reviewable | "I worked in approval-gated phases, so the client saw each major decision before code existed." |
| D-003 / D-004 / D-013 | Document set: requirements.md, CLAUDE.md, NOTES.md, data-sources-research.md, architecture.md (drafted in Phase 3, finalized in Phase 9) | Need a durable record | Consistency and naming | — |
| D-007 → D-012 | Phase 1 provisionally approved, then approved for finalization | The user approved from summaries first | Honest record of approval strength | — |
| D-014 | The assignment PDF stays local (`.gitignore` line 1) | The user did not want it uploaded | User instruction | — |
| D-026 | The assistant never runs `git add`, `commit`, or `push`. The user does. | The user instruction "from now on don't commit yourself" (2026-10-28) | Ownership of history | "I kept a human in control of the repository history." |
| D-027 | Maintain this journal with the full template for Phases 4–9 | Phase 3 revision request | Interview readiness, traceability | — |

### D-005: Do not choose a stack before data is verified (REVISITED)
- **Phase / status:** 1, APPROVED, then **REVISITED** on 2026-10-30 when D-022 to D-024 chose the stack after data verification.
- **Context:** the risk was locking in tools before knowing whether public data could support the questions.
- **Alternatives:**
  - *[discussed]* Choose the stack up front. Pro: faster start. Con: the stack might not fit the data access needs.
  - *[selected]* Defer until after Phase 2.
- **Why:** data availability was the top risk (requirements R-1).
- **Tradeoff:** about 2 h of research before any code.
- **Validation:** Phase 2 confirmed the data supports Q1–Q4 (as indicators or direct measurements). The stack was then chosen.
- **Interview line:** "I deliberately verified the data before choosing technology, because the data shaped what the agent could honestly answer."

### D-009: Time-box Phase 2 to about 2 hours
- **Phase / status:** 2, APPROVED.
- **Context:** open-ended API research can consume the budget.
- **Alternatives:**
  - *[retrospective]* Unbounded research. Pro: more sources. Con: schedule risk.
  - *[retrospective]* No research (assume APIs). Con: high risk of building on unavailable data.
- **Selected:** 2 h, with blockers found first.
- **Tradeoff:** some items were left unverified (TAF values, licences, DB1B).
- **Validation:** research completed within the box. Unverified items are listed (A-011 to A-014).
- **Interview line:** "I time-boxed discovery and explicitly listed what I didn't verify instead of guessing."

### D-010 / D-011: Investment indicators, not profitability; goal unchanged
- **Phase / status:** 1–2, APPROVED.
- **Context:** the PDF asks for airports where renovations "will be most profitable", but public aviation data has no costs, revenues, or financing data (requirements §1.3).
- **Alternatives:**
  - *[discussed]* Estimate profitability with assumed revenue per passenger and costs. Pro: matches the wording. Con: invented figures that are indefensible.
  - *[discussed]* Ignore the profitability framing. Con: off-target.
  - *[selected]* Evidence-based opportunity indicators tied to the capacity thesis.
- **Why rejected:** inventing financial inputs violates data integrity (CLAUDE.md §4).
- **Tradeoff:** the answer is "where demand pressure is strongest", not "which is most profitable", and this is stated openly.
- **Validation (planned):** scenario checks that no reply claims profitability or ROI.
- **Impact:** narrows scope and saves time.
- **Interview line:** "The brief asked about profitability, but the data couldn't support it, so I reframed the output as transparent demand-pressure indicators and said so explicitly."

### D-016 / D-017 / D-019: Live public API vs. public dataset snapshots (user label **D6**)
- **Phase / status:** 2, APPROVED.
- **Context:** FR-1 requires "public APIs". The one verified, keyless JSON API (BTS Socrata `r495-tyji`) covers monthly airport traffic but **not** delays, route distances, or service classes. Those exist only as public **files** (BTS on-time ZIP, the T-100 form download, the FAA xlsx).
- **Alternatives:**
  - *[discussed]* **Live API only** (Strategy 2). Pro: the most literal reading of FR-1. Con: Q2 to Q4 become weak (no delay history, no true long-haul %).
  - *[discussed]* **Files only.** Pro: the richest data. Con: does not genuinely use a public API.
  - *[discussed]* **API + OpenSky** (Strategy 3). Con: requires account registration, airports are estimated, passenger vs. cargo is ambiguous.
  - *[selected]* **Hybrid:** the live BTS API at runtime for traffic KPIs, plus small processed snapshots of public files for the delay and route metrics.
- **Why:** it is the only option that both genuinely uses an API and can answer Q2 and Q3 credibly.
- **Rules (D-017):** snapshots are never called APIs. Every result carries `source_type`.
- **Provenance and freshness:**
  - A manifest records the URL, retrieval date, data period, and checksum.
  - The live API shows a ~3-month publication lag (latest month 2026-07 as of 2026-10-28).
- **Licensing:** A-011 (TranStats automated download) and A-014 (OurAirports) are unverified. Snapshots are committed only after those checks (D-037, approved 2026-10-30; `data/processed/` is gitignored until then).
- **Reproducibility:** `scripts/build_snapshots.py` regenerates the snapshots from the public sources.
- **Outages:** API timeout → labelled recorded fallback. Snapshots are unaffected.
- **Tradeoffs:**
  - Two data paths.
  - Snapshots go stale.
  - The T-100 form download is fragile.
  - The on-time file is large (~33 MB per month, ~356 s download).
- **Validation (planned):**
  - Tests check `source_type` on every artifact.
  - A live smoke test of the BTS API.
  - Manifest checks.
- **Impact:** about 1 h for the snapshot builder (Phase 5).
- **Interview line:** "The only true public API covered traffic, not delays or route distances, so I used it live at runtime and supplemented it with clearly labelled public dataset snapshots. I never blurred the two."

### D-018: Analysis windows
- **Phase / status:** 2, APPROVED.
- **Context:** sources have different periods and sizes.
- **Alternatives:**
  - *[discussed]* 12 months of everything. Con: ~12 × 33 MB of on-time data, too slow.
  - *[discussed]* 3 months of on-time data. Allowed "if feasible".
  - *[selected]* A 12-month API window, 1 verified month of route and on-time data, with every window disclosed.
- **Tradeoff:** single-month data is seasonal. This is flagged and lowers confidence.
- **Validation (planned):** every artifact carries `windows`, and tests assert it.
- **Interview line:** "I matched data depth to the time budget and made every time window visible next to the numbers."

### D-020: FAA runway capacity PDFs are context only
- **Phase / status:** 2, APPROVED.
- **Context:** the only public capacity numbers found are PDFs from 2014–2019.
- **Alternatives:**
  - *[discussed]* Transcribe them into a utilization metric. Con: dated, manual, and covers few airports.
  - *[selected]* Context links only, clearly dated.
- **Tradeoff:** no utilization-based congestion measure.
- **Interview line:** "I chose not to build a score on decade-old hand-copied numbers."

### D-021: Separate observed demand, pressure indicators, and unmet demand
- **Phase / status:** 2, APPROVED.
- **Context:** Q4 asks for "unmet flight demand", which cannot be observed.
- **Alternatives:**
  - *[discussed]* Produce one "unmet demand" number from proxies. Con: it implies a measurement that does not exist.
  - *[selected]* Three explicit blocks, with "unmet demand: not measured".
- **Why:** honesty about the limits of what can be measured. Delays and load factor have several causes (architecture §6.1).
- **Validation (planned):** a wording check in the Q4 scenario evaluation.
- **Interview line:** "I separated what we observe from what we infer, and said plainly that unmet demand isn't measurable with this data."

### D-022: Frontend: React + TypeScript + Vite (user label **D1**)
- **Phase / status:** 3, **APPROVED** by explicit user decision on 2026-10-30. It overrides P-001's plain HTML/JS UI proposal.
- **Context:** the chat UI must render conversational text **and** structured evidence (ranking tables, comparisons, long-haul cards, sources, warnings).
- **Alternatives:**
  - *[discussed]* **Plain HTML/JS** (P-001). Pro: no build step, about 3–4 h faster, fewer dependencies. Con: hand-built DOM updates for complex typed evidence, which gets messy and is harder to extend.
  - *[discussed]* **Streamlit.** Pro: the fastest chat UI. Con: merges UI and backend, so the API contract is less clear and there is less layout control.
  - *[selected]* **React + TypeScript + Vite.** Pro:
    - component model (one component per evidence type),
    - TS types mirror the backend schemas, so contract errors are caught at build time,
    - a fast dev server with an `/api` proxy,
    - industry-standard, which is credible for an FDE deliverable.
    Con: Node toolchain, build step, more setup time.
- **Why selected:** the user chose React despite the extra setup time, prioritizing a maintainable, typed UI that renders deterministic evidence clearly.
- **Tradeoffs / risks:** about +2–3 h compared with plain HTML (absorbed in P-020). Reviewers need Node to build. Mitigation: FastAPI serves the built SPA (P-023).
- **Validation (planned):** `tsc` type-check, `vite build`, and E2E runs of the Q1–Q4 scenarios.
- **Impact:** Phase 4 +0.5 h, Phase 8 +0.5–1 h.
- **Interview line:** "I used React with TypeScript because the UI isn't just chat: it renders typed evidence tables from the backend, and typed components keep that contract honest."

### D-023: Backend: Python + FastAPI (user label **D2**)
- **Phase / status:** 3, **APPROVED** on 2026-10-30. Consistent with P-001's backend part.
- **Context:** the backend does the data processing (CSV, ZIP, XLSX, aggregation), calls the public API, runs deterministic analytics, and hosts the agent.
- **Alternatives:**
  - *[discussed]* **Node.js (TypeScript) backend.** Pro: one language end to end. Con:
    - the data processing needs extra libraries (zip, xlsx, csv),
    - the Phase 2 probes (written in Python with the standard library) would have to be rewritten,
    - weaker data and numeric ecosystem.
  - *[selected]* **Python + FastAPI.** Pro:
    - the Phase 2 stdlib probes (T-100 form POST, on-time aggregation, xlsx parsing) can be reused,
    - strong data and API-integration ecosystem,
    - Pydantic gives schemas for both the API and the tool inputs,
    - LangChain's primary SDK is Python,
    - async HTTP,
    - matches the role's Python expectations.
- **Why Node was rejected:** more rewriting and more dependencies for the data-heavy work.
- **Tradeoffs:** two languages in the repo (Python + TS), with types mirrored by hand.
- **Validation (planned):** pytest suite and FastAPI TestClient.
- **Impact:** saves time compared with Node for the data layer.
- **Interview line:** "The heavy lifting is data processing and API integration, which Python does well, and FastAPI with Pydantic gave me validated contracts for both HTTP and the agent's tools."

### D-024: Agent orchestration: LangChain (user label **D3**)
- **Phase / status:** 3, **APPROVED** by explicit user decision on 2026-10-30. It overrides P-002's hand-written direct tool-calling loop.
- **Context:** the agent must pick tools, call them with validated parameters, loop until done, keep conversation memory, and report tool errors.
- **The key point: both approaches require us to implement the business tools ourselves.** The airport resolver, BTS client, snapshot loader, and every KPI, ranking, and comparison function are our Python code in either case. LangChain does **not** compute aviation metrics.
- **Alternatives:**
  - *[discussed]* **Direct tool calling with the Anthropic SDK** (P-002). We would hand-write:
    - JSON schemas for each tool,
    - argument validation,
    - the `while stop_reason == "tool_use"` loop,
    - dispatch (name → function),
    - assembling tool_result messages (including parallel calls),
    - per-session history storage and replay,
    - an error-wrapping convention,
    - a side channel to get structured results to the UI.
    Pro: zero framework dependency, full transparency. Con: more boilerplate to write and test, and each piece is reinvented.
  - *[selected]* **LangChain v1** (`create_agent`). It provides:
    - the agent loop,
    - `@tool` schemas from Pydantic (`args_schema`) with validation,
    - `content_and_artifact` for UI-only structured results,
    - `ChatAnthropic` for the provider integration (thinking and effort settings),
    - `InMemorySaver` + `thread_id` for conversation memory,
    - middleware for tool-error handling.
    Pro: less custom plumbing, extensible (more tools or another provider). Con:
    - an added dependency tree (including transitive `langgraph`),
    - abstraction that can hide behaviour,
    - version churn,
    - some behaviours to verify (A-018 to A-021).
  - *[retrospective]* **LangGraph custom graph.** Rejected: not needed for a single agent loop.
  - *[retrospective]* **The Anthropic SDK beta Tool Runner.** Rejected along with P-002, after the user chose LangChain.
- **Why selected:** the user's explicit decision. LangChain trades a dependency and some abstraction for reusable agent infrastructure.
- **Accepted risks:**
  - The interaction of LangChain with model-specific behaviour (adaptive thinking blocks persisted in checkpointer history) must be verified in a Phase 4 spike.
  - Pin versions to avoid churn.
- **Validation (planned):**
  - Tool-layer tests without an LLM.
  - API tests with a fake chat model.
  - A Phase 4 spike: one real tool round-trip with `claude-opus-5-5`.
- **Impact:** about −0.5 to −1 h of loop and memory code, about +0.5 h to learn and verify LangChain specifics. Roughly neutral.
- **Interview line:** "In both designs I wrote the aviation tools myself. LangChain gave me the agent loop, schema-validated tool calling, memory and error middleware, so my code focused on the data and the scoring, not plumbing."

### D-025: The four PDF questions are evaluation scenarios, not hardcoded limits (user label **D10**)
- **Phase / status:** 3, **APPROVED**. The user stated that the app "must support flexible aviation questions … not just four hardcoded examples" and that the questions are to be kept "as evaluation scenarios".
- **Context:** the PDF says "questions **such as**".
- **Alternatives:**
  - *[retrospective]* Hardcode four intents. Pro: fast and reliable for the demo. Con: brittle, and fails on any rephrasing or analogous question, which is not really an agent.
  - *[selected]* Reusable, parameterized tools, with the scenarios composed by the agent:
    - Q1 = resolve region + rank
    - Q2 = resolve + compare
    - Q3 = long-haul share
    - Q4 = demand-pressure profile
- **Validation (planned):** a scenario set with Q1–Q4 plus at least one analogous question each (another region, another pair, another airport, another threshold) plus follow-ups.
- **Interview line:** "I treated the four examples as a test set, not a spec. Each one is a composition of general tools, so 'rank Florida airports' works the same way."

### Phase 3 design-review decisions (2026-10-30)

> **What the user decided vs. what the assistant recommended.** Each entry below separates the **user decision** (the text of the review feedback, paraphrased) from the **assistant's earlier proposal** and the analysis behind it.

#### Review item 1: runtime BTS API plus separately labelled snapshots (reaffirms D-016 / D-017)
- **User decision:** "Keep the BTS public API genuinely used at runtime, and label supplementary snapshots separately."
- **Effect:** no change of direction. The design keeps the live SoQL call for traffic KPIs and `source_type` labels (architecture §4.10).
- **Interview line:** "The API call is in the request path, and the UI labels every number's source type from data, not prose."

#### D-028: All calculations in deterministic Python
- **Phase / status:** 3, **APPROVED** (user review item 2).
- **Original proposal:** design principle 1 and architecture §4 ("numbers come from code").
- **Context:** an LLM can miscalculate or invent numbers. The PDF requires deterministic scoring.
- **Alternatives:**
  - *[retrospective]* Let the LLM compute simple derived figures (differences, percentages). Pro: flexible phrasing. Con: unverifiable arithmetic.
  - *[retrospective]* Use the code-execution sandbox. Con: the logic is still LLM-authored and not reproducible.
  - *[selected]* All KPIs, **derived comparisons** (differences, ratios, percentiles, rank changes), normalization, and scoring run in pure Python engine functions.
- **Tradeoff:** every derived figure the user may want must be anticipated as a tool output.
- **Validation (planned):** engine unit tests. Tool tests check that content numbers are a subset of the artifact.
- **Impact:** `compare_airports` returns absolute and relative differences. `rank_airports` returns `rank_changes`.
- **Interview line:** "Even a simple difference is computed in Python and shipped as evidence, so every number is reproducible."

#### D-029: 300 flights/month is a data-quality warning, not an exclusion
- **Phase / status:** 3, **APPROVED** (review item 4). **Revises the 300-flight part of P-009** (rev 1 and 2: below 300 departed flights → operational KPIs null).
- **Context:** small samples make delay rates noisy, but discarding them hides real data and penalizes small airports.
- **Alternatives:**
  - *[discussed]* Exclude (P-009). Pro: the score is not driven by noise. Con: loses information. 300 is an arbitrary cutoff.
  - *[selected]* Keep the value and add a `low_sample` flag, lower confidence, and make the threshold configurable (`min_flights_warning`, default 300, range 0–5,000).
  - *[retrospective]* Statistical shrinkage. Con: complexity, and harder to explain.
- **Tradeoff:** noisy values can affect the score, but they are visibly flagged.
- **Validation (planned):** tests that the flag is set below the threshold and not at or above it. Values remain in the score.
- **Interview line:** "I didn't silently drop small airports. I kept their data and flagged the sample size so the analyst can judge it."

#### D-030: Code-generated evidence rendered by React over scanning LLM text
- **Phase / status:** 3, **APPROVED as the direction** (review item 5). The exact pipeline (architecture §10.1) and the test plan (§10.2) are **PROPOSED** and are confirmed by the Phase 4 spike (A-022).
- **Original proposals:**
  - **P-005** (rev 1): scan the reply, re-prompt, then warn.
  - **P-019** (rev 2): artifacts first, plus a non-blocking scan.
- **User decision:** prefer structured evidence displayed directly by React over scanning text.
- **Alternatives:** the P-005 scan with a re-prompt, placeholder binding, and artifacts-first (see the P-019 analysis in §3).
- **Selected:**
  - Tool artifacts (`content_and_artifact`) are captured from this turn's `ToolMessage`s.
  - FastAPI validates them with Pydantic and returns `evidence[]`.
  - React renders them through typed, discriminated components.
  - Fallback capture via a `contextvars` collector if artifacts are not preserved.
  - The text scan is deferred (P-026, optional).
- **Accepted risk:** the prose could still contain an untraceable number. Mitigated by prompt rules and by the adjacent authoritative tables.
- **Validation (planned):** see architecture §10.2. Tool-wrapper tests, fake-model FastAPI tests (including a second turn and a failing tool), shared JSON fixtures checked by both Pydantic and `tsc`, and real-model scenarios.
- **Impact:** removes about 1 h of scan work from the baseline.
- **Interview line:** "The numbers on screen never pass through the LLM: tools return structured artifacts, FastAPI forwards them, and React renders them."

#### D-031: 24-hour budget as a planning target (approves P-020)
- **Phase / status:** 3, **APPROVED** (review item 6) as a **planning target** with **3 h contingency**.
- **Added constraint:** **all four scenarios must stay viable** when scope is reduced.
- **Effect on the cut list:** every cut item is optional polish that leaves Q1–Q4 answerable:
  1. Voice
  2. Optional Vitest
  3. P-026 text check
  4. No-key demo → banner only
  5. `rank_changes`
  6. LA-area alternative
  7. Q4 peer percentiles → plain values (Q4 still answered with the three blocks)
  8. 3-month on-time data
- **Validation:** time is tracked per phase in NOTES.md from Phase 4 onward (actual vs. plan).
- **Interview line:** "I planned 21 hours of work with 3 hours of contingency and a cut list that never removed one of the four scenarios."

#### D-032: No-key mode = a labelled deterministic demo (approves P-021 with narrower scope)
- **Phase / status:** 3, **APPROVED** (review item 7).
- **Original proposals:**
  - P-004: presets + structured chat commands.
  - P-021: presets + a weights form.
- **Selected:**
  - Four preset buttons with fixed parameters (`POST /api/demo/{scenario}`), using the same engine, the live BTS API, and evidence components.
  - A persistent banner saying it is not the AI agent.
  - Chat input disabled. No weights form.
- **Rejected:** the structured-command chat (looks conversational) and the weights form (scope creep, blurs the "demo" label).
- **Validation (planned):** an API test for each preset. A manual run with no key: the banner is visible and the chat is disabled.
- **Interview line:** "Without a key the app is honest: it's a fixed deterministic demo of the data and scoring path, not a chatbot."

#### D-033: Configurable model, verified in the Phase 4 smoke test
- **Phase / status:** 3, **APPROVED** (review item 8). The default (`claude-opus-5-5`, P-022) and the fallback order (P-028) remain **PROPOSED**.
- **Context:** model IDs and SDK behaviour change. Docs were verified on 2026-10-30, but runtime compatibility is not yet proven.
- **Smoke test:**
  - Exact ID accepted.
  - One tool call through `create_agent`.
  - Artifact captured.
  - Two-turn memory.
  - Loop limit observed.
- **Fallback (P-028):**
  - A model-specific failure → `claude-sonnet-5-5`.
  - An integration failure → pin or upgrade `langchain-anthropic` within the major version.
  - Record the cause.
- **Interview line:** "Model choice is configuration. I proved the exact ID and SDK path in a smoke test before building on it, with a documented fallback."

#### D-034: Single FastAPI server for review, Vite proxy in dev (approves P-023)
- **Phase / status:** 3, **APPROVED** (review item 9).
- **Alternatives:** two servers with CORS, or Docker *[retrospective]*.
- **Why:** one reviewer command, same origin, no CORS.
- **Tradeoff:** the reviewer must run `npm run build` once (a Node toolchain is required).
- **Validation (planned):** a fresh-clone README run in Phase 9.

#### D-035: Pydantic tool schemas; confirm LangChain behaviours in Phase 4
- **Phase / status:** 3, **APPROVED** (review item 10).
- **Covers:**
  - `args_schema` validation.
  - Business validation in the engine.
  - `@wrap_tool_call` error middleware.
- **Confirm in Phase 4:**
  - Default validation-error handling (A-018).
  - Model compatibility (A-019).
  - `recursion_limit` (A-020).
  - Fake chat model (A-021).
  - Artifact preservation (A-022).
- **Interview line:** "I validated tool inputs with Pydantic and verified the framework's error and memory behaviour empirically before relying on it."

#### D-036: NOTES.md ignore fix (approves P-025)
- **Phase / status:** 3, **APPROVED** (review item 11).
- **Status of the change:** `.gitignore` was edited by the assistant on 2026-10-30. **The commit is pending with the user** (D-026).
- **Problem:** `.gitignore` line 2 `NOTES.md` (added in `3b91e03`) contradicted a tracked file.
- **Fix applied to the working tree:**
  - Removed the `NOTES.md` rule.
  - Kept the PDF rule.
  - Added `.env`, `.env.*`, `!.env.example`, `data/raw/`, `data/processed/` (D-037), `.venv/`, `__pycache__/`, `*.pyc`, `node_modules/`, `frontend/dist/`.
- **History preserved:** no `git rm`, so NOTES.md's commits are untouched.
- **Verified (2026-10-30):**
  - `git check-ignore --no-index NOTES.md` → no match (exit 1).
  - `.env` → ignored (line 5).
  - `.env.example` → allowed by the negation (line 7).
  - The PDF → ignored (line 2).
- **Interview line:** "I fixed a contradictory ignore rule without rewriting history, and added secret rules before any code existed."

#### D-037: No snapshot commits until licensing and provenance checks pass
- **Phase / status:** 3, **APPROVED** (review item 12). Resolves the former OQ-3.
- **Implementation:** `data/processed/` is gitignored for now. Snapshots are built locally by the script. A later decision will un-ignore them after A-011 (TranStats terms) and A-014 (OurAirports licence) are checked and the manifest's provenance is complete.
- **Tradeoff:** until then, reviewers must run the snapshot builder (about 6 minutes per on-time month).
- **Interview line:** "I didn't redistribute third-party data until I'd checked I was allowed to."

#### D-038: Update implementation-plan.md after the remaining approvals
- **Phase / status:** 3, **APPROVED** (review item 13).
- **Effect:** implementation-plan.md is intentionally **not** updated yet. It will reflect D-022 to D-038, the scoring decision, and the D-031 budget once the remaining proposals (§5.1) are decided.
- **Update 2026-10-30:** executed by **D-043**. The plan has been updated.

### Phase 3 closing decisions (2026-10-30)

> User decisions are quoted or paraphrased from the closing instruction. Assistant analysis is marked as such.

#### D-039: Scoring v1 for the MVP (approves P-027 option A, P-006 to P-009 as refined)
- **Phase / status:** 3, **APPROVED** for the MVP, *subject to precise field and denominator definitions* (P-029).
- **User decision (close items 1–5):**
  1. Use option A, candidate-group min-max. Scores are **relative expansion-opportunity signals, not profitability forecasts or proof of terminal capacity shortages**.
  2. Approve the KPI weights and scoring rules.
  3. Keep:
     - coverage-weighted averaging,
     - the 60% coverage threshold,
     - a minimum of 3 airports per KPI,
     - small-sample warnings,
     - deterministic tie-breaking.
  4. Explicitly handle:
     - zero total user weights,
     - zero available KPI weight,
     - missing data,
     - equal min and max,
     - negative growth,
     - groups of fewer than 3 airports.
  5. Explain that rankings depend on the group and that scores with different coverage are not perfectly comparable.
- **Previous proposals:**
  - P-006 (eligibility).
  - P-007 (weights .30 / .25 / .15 / .20 / .10).
  - P-008 (min-max).
  - P-009 (missing data, including the 300-flight exclusion, revisited by D-029).
  - P-027 (the exact v1 spec with options A, B, and C).
- **Alternatives** *[discussed]*:
  - **(B) National reference range (P5–P95).** Pro: comparable across queries. Con: +1 h, clipping, still a parameter choice.
  - **(C) Hand-set fixed ranges.** Con: invented bounds.
  - **Percentile rank.** Con: loses magnitude.
  - **Equal weights.**
- **Why A:** simplest, nothing invented, explainable ("100 = best in this group"). Its limits are disclosed (architecture §7.1c).
- **Rejected:** B was deferred as a documented upgrade. C was rejected for data integrity.
- **Accepted risks:**
  - Group-relative scores can reorder when the group changes.
  - Coverage differences reduce comparability.
  - Both are disclosed in every ranking artifact.
- **Validation (planned, Phase 6):**
  - The §9 worked examples as unit tests (B 55.0 / A 51.1 / D 50.0 / C 45.0, and C 70.0 / A 54.7 / D 50.0 / B 30.0).
  - Each edge case in architecture §7.1b.
  - A test that adding an airport changes ranges, demonstrating the disclosed relativity.
- **Impact:** within Phase 6 (2.5 h).
- **Interview line:** "My ranking is a transparent, group-relative opportunity signal: min-max per KPI, weighted by coverage, with every contribution visible. I was explicit that it isn't a profit forecast and that a different comparison group can change the order."

#### P-029: Precise field, denominator, and edge-case definitions (for confirmation)
- **Phase / status:** 3, PROPOSED. Written to satisfy D-039's condition and close item 6.
- **Verification run on 2026-10-30 (read-only requests, no application code):**
  - The BTS API `r495-tyji` totals **equal the T-100 Segment (All Carriers) sums over service classes F, G, L, and P** for Dec 2025:
    - ANC: 6,872 departures / 185,000 passengers / 248,666 seats
    - SFO: 15,751 / 2,231,280 / 2,655,117
    - SNA: 4,334 / 462,326 / 582,506
  - `domestic_departures + outbound_international = total_departures`.
  - **API departures include all-cargo classes** (ANC G + P = 4,330 of 6,872).
  - **Seats and passengers come essentially from the passenger-capable classes F and L.** ANC P-class seats = 137, a negligible anomaly.
  - On-time Jul 2026, SFO: `DepDel15` is blank only on cancelled rows (156 of the 159 cancelled). No blank `TaxiOut` on non-cancelled rows. 92 diverted.
  - BTS field definitions quoted from the Fields page (architecture §6.0).
- **Proposed definitions (architecture §6.0a and §7.1b):**
  - **Delay rate = departure delay at the origin:** `Origin=X, Cancelled=0, DepDel15=1` ÷ `Origin=X, Cancelled=0, DepDel15 not blank`. Cancellations are excluded. Diverted flights are included.
  - **Cancellation rate:** `Cancelled=1` ÷ all rows with `Origin=X`.
  - **Taxi-out:** the mean over non-cancelled rows with a value.
  - **Delay causes:** arrival records into X, labelled as such.
  - **Flight growth:** API `total_departures`, **all classes including cargo**. This is disclosed. Passenger-only departure growth is not available from the API.
  - **Load factor:** Σ passengers ÷ Σ seats from the API (≈ passenger-service load factor).
  - **Edge cases:** zero or negative weights → `INVALID_INPUT`; zero available weight → score null; all KPIs dropped → raw table only; equal min/max → 50 with a warning; negative growth kept signed; fewer than 3 airports → comparison only; prior = 0 → growth null; seats = 0 → load factor null.
- **Alternatives** *[retrospective]*:
  - **Arrival delay rate.** Rejected: it reflects upstream airports.
  - **A combined departure + arrival rate.** Rejected: it mixes causes.
  - **Counting cancellations as delays.** Rejected: double-counts with the cancellation rate.
  - **Estimating passenger-only departures with a T-100 class ratio applied to the API series.** Rejected: an invented estimate across periods.
- **Accepted risk:** flight growth at cargo-heavy airports (ANC) partly reflects cargo. ANC is not in Q1's New England group, but the caveat is shown generally.
- **Validation (planned):** fixture tests encoding these exact numerators and denominators, including cancelled-with-DepDel15 rows (3 such rows exist at SFO) and diverted rows.
- **Interview line:** "Before approving the scores I checked the fields themselves: the API's departures include cargo flights, and the delay indicator is blank only for cancellations. So I defined delay rate on departed, non-cancelled flights and disclosed that flight growth includes cargo."

#### D-040: Approve P-010 to P-018
- **Phase / status:** 3, **APPROVED** (close item 7).
- **What is approved:**
  - P-010: delay-based congestion, no composite score.
  - P-011: "LA" → LAX by default, stated, with the LA-area option offered.
  - P-012: long haul ≥ 3,000 statute mi, F+L by default, all-class variant always shown, adjustable.
  - P-013: Q4 three-block profile.
  - P-014: July 2026 snapshots, **with T-100 July 2026 subject to availability verification (A-015). If it is unavailable, use the nearest available month and report the mismatched window clearly.**
  - P-015: user weights over a fixed registry.
  - P-016: in-memory sessions.
  - P-017: explicit out-of-scope answers.
  - P-018: no voice in the MVP.
- **Previous reasoning:** see each P-entry in §3 (kept).
- **Validation (planned):** scenario evaluation Q1–Q4, the window-mismatch warning test, and an out-of-scope question test.
- **Interview line:** "Each scenario's interpretation (LA = LAX, a 3,000-mile threshold, passenger classes) was a stated, adjustable choice, not a hidden assumption."

#### D-041: Drop the post-hoc number scanner; test artifact propagation
- **Phase / status:** 3, **APPROVED** (close item 8). **P-026 is REVISITED (dropped).**
- **Original proposals:** P-005 (scanner with a re-prompt) → P-019 (non-blocking scan) → P-026 (an optional scan).
- **User decision:** drop P-026. Use Python-generated structured evidence and **test** that LangChain artifacts reach React correctly.
- **Why:**
  - The scanner's false positives and negatives (rounding, units, restated inputs, coincidental matches) make it unreliable.
  - Artifacts-first already guarantees the on-screen numbers.
- **Accepted risk:** prose may still contain an untraceable number. Mitigated by prompt rules and the authoritative tables beside it.
- **Validation (planned):** the architecture §10.2 test matrix (tool tuple, fake-model FastAPI tests including a second turn and a failing tool, shared fixtures checked by Pydantic and `tsc`, real-model scenarios).
- **Impact:** removes optional scope (about 1 h).
- **Interview line:** "Rather than auditing the LLM's prose, I tested the pipe: the artifact a tool creates is exactly what React renders."

#### D-042: LangChain tools with Pydantic validation, in-memory sessions, single server (approves P-024, P-016; reaffirms D-034)
- **Phase / status:** 3, **APPROVED** (close item 10).
- **Approved:**
  - Thin `@tool` wrappers with `args_schema` and `content_and_artifact` over the pure engine.
  - `@wrap_tool_call` error middleware.
  - `InMemorySaver` sessions (30 turns, 2 h idle).
  - FastAPI serves the built SPA.
- **Remaining implementation-time checks (Phase 4):** A-018 to A-022.
- **Interview line:** "LangChain handled the loop, validation, and memory. My tools stayed thin wrappers over a pure Python engine I could test without any LLM."

#### D-043: Update implementation-plan.md now
- **Phase / status:** 3, **APPROVED** (close item 14). Executes D-038. **Done 2026-10-30** (a documentation change, not implementation).
- **Content:**
  - React + FastAPI + LangChain.
  - Phase budgets (D-031).
  - Phase 4 smoke tests.
  - The essential-requirements list.
  - The optional cut list.

#### D-044: Generic `aggregate_metrics` tool over trusted evidence references (user decision, close item 15)
- **Phase / status:** 3, **APPROVED as the design direction**, **time-boxed and deferrable**. Detailed design is **P-030 (PROPOSED)**.
- **Context: why domain-specific tools alone limit flexibility** (assistant analysis):
  - Each domain tool answers a fixed shape of question (rank, compare, long-haul, profile).
  - Natural follow-ups often combine results: "average growth across these airports", "which has the highest taxi-out", "total passengers for BOS + BDL + PVD".
  - Without a combining tool, the agent must either refuse or do the arithmetic itself.
- **Alternatives:**
  - *[discussed]* **Let the LLM do the arithmetic itself.**
    - Pro: maximum flexibility, zero build time.
    - Con:
      - unverifiable,
      - errors in rounding, units, or omitted airports,
      - the model may retype numbers from memory or invent inputs,
      - conflicts with D-028 and CLAUDE.md §4–5.
    - **Rejected for investment-related numbers.**
  - *[retrospective]* **A general expression or code tool** (a sandboxed Python or math evaluator).
    - Pro: flexible.
    - Con: accepts arbitrary code or expressions, the inputs are still model-supplied, and there is a security and validation burden.
    - Rejected by the user's constraint ("must not accept arbitrary code or unrestricted mathematical expressions").
  - *[retrospective]* **Add more domain tools for each new question shape.** Pro: very reliable. Con: unbounded scope, and slow.
  - *[selected]* **A small `aggregate_metrics` tool:**
    - operations avg / sum / min / max,
    - inputs only as **references** to evidence already produced by our tools (`evidence_ids`) plus a registry metric id,
    - values read server-side from a per-session evidence store,
    - no model-typed numbers.
- **Why deterministic Python for investment numbers:**
  - Analysts may act on these figures. They must be reproducible, traceable to a source and window, and testable.
  - LLM arithmetic offers none of these guarantees.
- **Tradeoff:**

  | | LLM arithmetic | Expression tool | `aggregate_metrics` | Domain tools only |
  |---|---|---|---|---|
  | Flexibility | High | High | **Medium** | Low |
  | Reliability | Low | Medium | **High** | High |
  | Complexity | None | High | **Low–medium** | Grows |
  | Delivery time | 0 | 2+ h | **≤ 1 h** | Grows |

- **Rules (from the user):**
  - Only validated numeric data already retrieved by the application.
  - No arbitrary code or expressions.
  - The model must not invent input values.
  - LangChain composes the domain tools and this tool.
  - Unsupported data or calculations → explain the limitation rather than inventing a number.
- **Priority / scope:**
  - Q1–Q4 come first.
  - Built in Phase 7 only after Q1–Q4 pass end to end, capped at about 1 h.
  - Otherwise **deferred**, with the tradeoff documented. It is item 3 in the cut list (it never affects Q1–Q4).
- **Implementation plan (P-030):** architecture §5.1.
  - The evidence store flattens artifacts into `{evidence_id, airport, metric_id, value, unit, window, source_type}`.
  - Validation: evidence exists in the session, the metric exists, there is a single window and unit, the operation is allowed per metric (sum only for counts; avg labelled "unweighted mean"), and nulls are excluded and counted.
  - The output artifact lists every input with its evidence ID and inherits provenance.
- **Testing plan:**
  - Unit tests for each operation, the allowed and disallowed metric/operation pairs, nulls, mixed-window and unit rejection, and unknown evidence IDs.
  - Store flattening for each result type.
  - A fake-model agent test composing `get_traffic_metrics` → `aggregate_metrics`, with the result equal to direct Python computation.
  - A real-model check of one aggregate follow-up.
- **Risks:**
  - The model may try to pass numbers. The schema has no numeric value fields, so it cannot.
  - "avg of rates" may be misread as a system rate, so it is labelled "unweighted mean".
  - Time overrun, handled by deferral.
- **Interview line:** "To keep flexibility without letting the LLM do math, I added one small aggregation tool that only works on references to data my own tools had already retrieved, so the model can say *what* to combine but never supply the numbers."

---

## 3. Proposed decisions awaiting approval

> None of these are approved. P-006 to P-018 come from Phase 3 rev 1 and remain PROPOSED unless noted in §4.

### P-027: Exact scoring specification v1 (refines P-006 to P-009), **awaiting user review**
- **Update 2026-10-30 (close):** **APPROVED with option A as D-039**, subject to the precise definitions in P-029. The original text is kept below.
- **Phase / status:** 3, PROPOSED (original). The user asked to see the exact formulas, ranges, weights, directions, missing-data rules, and two worked examples **before** approving. Full text in architecture §7.1a, §7.3, and §9.
- **Summary:**
  - Eligibility: FAA primary airports in the region, or the user's list.
  - A KPI is dropped if fewer than 3 airports have it.
  - **Candidate-group min-max** (range reported).
  - All KPIs are "higher = stronger".
  - Default weights .30 / .25 / .15 / .20 / .10.
  - Coverage-weighted score with no imputation. Coverage < 0.60 → listed as "insufficient data", not scored.
  - `low_sample` warning (D-029).
  - At least 3 ranked airports, otherwise a comparison.
  - Deterministic tie-break.
- **Changes vs. rev 2:**
  - The KPI-usable minimum rises from 2 to 3 values.
  - The ranking minimum rises from 2 to 3 airports.
  - The 300-flight rule becomes a warning.
  - Two worked examples now include the missing-data and low-sample cases.
- **Normalization options presented:**
  - (A) Candidate-group min-max, recommended.
  - (B) National reference range (P5–P95 of all FAA primary airports), a data-derived alternative, about +1 h.
  - (C) Hand-set fixed ranges, not recommended because the bounds would be invented.
- **Scores are relative to the candidate group:** adding or removing an airport can change other airports' scores and even their order. This is disclosed in every ranking artifact.

### KPI and scoring methodology (user label **D7**): P-006, P-007, P-008, P-009, P-010, P-011, P-012, P-014, P-015
- **Phase / status:** 3, PROPOSED.
- **Update 2026-10-30:** P-006 to P-009 are refined by **P-027**. P-009's 300-flight exclusion is **REVISITED** by D-029 (now a warning).
- **Update 2026-10-30 (close):**
  - P-006 to P-009 → **APPROVED via D-039**.
  - P-010, P-011, P-012, P-014, P-015 → **APPROVED via D-040**. P-014 is subject to the A-015 availability check.
- **Context:** we need defensible, testable definitions for the metrics, the expansion-opportunity ranking, normalization, missing data, and user weights (architecture §6–§7).
- **Proposed approach and alternatives:**
  - **P-006 Eligibility:** FAA primary airports in the region.
    - *[discussed]* All commercial-service airports (con: tiny-base growth noise).
    - *[discussed]* A size threshold (con: an invented cutoff).
  - **P-007 Default weights:** pax growth .30, load factor .25, flight growth .15, delay rate .20, taxi-out .10.
    - *[discussed]* Equal weights (con: ignores relevance).
    - *[discussed]* Growth-only (con: ignores pressure).
  - **P-008 Normalization:** candidate-set min-max.
    - *[discussed]* Fixed-range (pro: comparable across sets; con: requires bounds we would have to invent).
    - *[discussed]* Percentile (pro: robust to outliers; con: loses magnitude).
    - Raw values are always shown.
  - **P-009 Missing data:** no imputation, coverage-weighted re-normalization.
    - Coverage < 0.6 → not ranked. Fewer than 300 departed flights → operational KPIs null (A-017).
    - *[discussed]* Neutral-50 imputation (con: hides gaps).
    - *[discussed]* Exclude the airport (con: loses information).
  - **P-010 Congestion:** delay-based rates, no composite score for 2–5 airports.
    - *[discussed]* Utilization-based (no current data, D-020).
    - *[discussed]* A composite congestion index (con: arbitrary for 2 airports).
  - **P-011 "LA":** LAX by default, with the interpretation stated and the LA-area alternative offered.
    - *[discussed]* Ask the user first (con: an extra turn).
  - **P-012 Long haul:** ≥ 3,000 statute miles, classes F+L, all-class variant always shown, adjustable.
    - *[discussed]* 2,500 or 4,000 miles.
    - *[discussed]* Cargo included by default (con: ANC is about 63% cargo; Dec 2025 probe).
  - **P-014 Snapshot months:** July 2026, aligned with the end of the 12-month window.
    - *[discussed]* Dec 2025 T-100 (already tested; con: period mismatch).
  - **P-015 User-defined KPIs:** weights over a fixed registry plus thresholds.
    - *[discussed]* Custom formulas (con: hard to validate in 24 h).
- **Tradeoffs / risks:**
  - Min-max scores are relative to the set.
  - Weights are a judgment call (mitigated by transparency and user override).
  - Single-month operational data.
- **Validation (planned):**
  - Unit tests for each formula and edge case.
  - The worked examples (architecture §9) as tests: ranking B>A>C under default weights, C>A>B under growth weights, coverage 0.70 → score 50.0, long-haul 9.5% / 26.8%, delay rates 25.0% / 25.0%.
- **Impact:** within Phase 6.
- **Interview line:** "My scoring is a transparent weighted index over observable indicators. Every contribution is shown, weights can be changed in chat, and I don't impute missing data."

### P-013: Q4 three-block demand-pressure profile
- **Status:** PROPOSED (original). **APPROVED via D-040 (2026-10-30).**
- **Approach:** observed demand / pressure indicators with peer percentiles / "unmet demand: not measured", plus the delay-cause ranking as "evidence consistent with …".
- **Alternative** *[discussed]*: a single unmet-demand estimate. Conflicts with D-021.
- **Validation (planned):** a wording check and the evidence present in the Q4 scenario.
- **Interview line:** "For 'unmet demand and why', I showed the evidence and its limits instead of manufacturing a number."

### P-016 / P-017 / P-018: Sessions, out-of-scope behaviour, voice
- **Update 2026-10-30 (close):** all three **APPROVED via D-040**. P-016 is also confirmed by D-042.
- **P-016:** in-memory, append-only sessions (30 turns, 2 h idle), implemented with the LangChain `InMemorySaver`.
  - *[discussed]* A persistent store (con: infrastructure for no requirement).
- **P-017:** unsupported questions get an explicit "not available" answer, plus the closest supported analysis via `list_metrics`.
  - *[discussed]* A best-effort LLM answer (con: hallucination risk).
- **P-018:** voice (a bonus in the PDF) is not in the MVP. Reconsider only if Phase 8 finishes early.

### P-019: Structured numeric outputs vs. a post-hoc number check (user label **D4**)
- **Phase / status:** 3, PROPOSED. **Supersedes P-005.**
- **Update 2026-10-30:** **REVISITED.** The artifacts-first direction is approved as **D-030**. The non-blocking text scan is split out as the optional **P-026** and removed from the MVP baseline. The analysis below is kept as the original reasoning.
- **Context:** M-10 requires that no numbers are fabricated. Rev 1 proposed **P-005**: scan the LLM reply for numbers, re-prompt once if any are unmatched, then warn.
- **Problems found with P-005:**
  - **False positives:** rounding (25.47% vs "about 25%"), units (0.255 vs 25.5%), thousands separators, restated user inputs ("3,000 miles"), years and dates, rank ordinals, and derived phrasing ("roughly double").
  - **False negatives:** a fabricated number can coincidentally match some value in a large artifact.
  - **Derived calculations:** differences or ratios computed by the LLM are not in the artifacts, even when correct.
  - **Re-prompt:** adds latency and cost and may still fail.
- **Alternatives:**
  - *[discussed]* **Post-hoc check with a blocking re-prompt** (P-005). Con: as listed above.
  - *[retrospective]* **Placeholder binding.** The LLM writes `{{LAX.delay_rate}}` and the backend substitutes the value. Pro: a strong guarantee. Con: the model must follow the placeholder syntax reliably, the prose is awkward, and it takes extra build time.
  - *[selected, proposed]* **Structured results first.**
    - React renders all authoritative numbers directly from tool artifacts (engine output). The LLM cannot alter them.
    - The system prompt forbids new calculations and asks the model to quote tool values or refer to the tables.
    - Derived figures (differences, percentiles) are computed by tools.
    - Plus a **non-blocking** numeric check (an ignore list, rounding and % tolerance) that shows a small UI notice and does not re-prompt.
- **Tradeoffs:** a fabricated number in prose is still possible, but it is flagged, and the tables beside it are always correct.
- **Validation (planned):**
  - Unit tests for the extractor and matcher (rounding, %, separators, ignore list).
  - Scenario runs that report unmatched counts.
  - Artifact-equality tests (artifact numbers equal the engine output).
- **Impact:** about 1 h (Phase 7), cuttable to "artifacts only" (−0.5 h).
- **Interview line:** "Instead of policing the LLM's prose after the fact, I made code-generated tables the source of truth on screen. The text check is a safety net, not the guarantee."

### P-020: 24-hour schedule and contingency (user label **D5**)
- **Update 2026-10-30:** **APPROVED as D-031** (a planning target with 3 h contingency, all four scenarios kept viable). The original proposal is kept below.
- **Phase / status:** 3, PROPOSED (original). Supersedes the rev 1 suggestion (§4, OQ-P3-4) of funding P-004/P-005 from the buffer, which would have left only about **0.5 h**.
- **Context:** React and LangChain add real setup and learning cost. A 0.5 h buffer is unrealistic for integration surprises (LangChain + thinking, Vite proxy, data downloads at ~356 s per month).
- **Alternatives:**
  - *[discussed]* A 0.5 h buffer with all extras. Con: no room for failure.
  - *[selected, proposed]* At least 2 h of contingency (3.0 h proposed), with explicit cut lists.
- **Revised budget (estimates; actual times are not tracked precisely):**

| # | Phase | Original | Proposed |
|---|---|---|---|
| 1 | Requirements & setup | 1.0 | 1.0 (done) |
| 2 | Data research | 2.0 | 2.0 (done) |
| 3 | Architecture & scoring design (2 revisions) | 1.5 | 2.0 |
| 4 | Foundation: Vite React-TS + FastAPI skeleton, env, pytest, **LangChain + Claude spike** | 1.0 | 1.5 |
| 5 | Data integration: BTS client, snapshot builder, resolver, fallback | 3.0 | 3.0 |
| 6 | Deterministic engine + unit tests | 3.0 | 2.5 |
| 7 | LangChain agent: tools, prompt, memory, middleware, numeric check | 4.0 | 3.0 |
| 8 | React chat UI + evidence components + E2E | 3.0 | 3.5 |
| 9 | Testing, architecture.md final, README, delivery | 3.0 | 2.5 |
| | **Contingency** | 2.5 | **3.0** |
| | **Total** | 24.0 | **24.0** |

- **Cut order (optional features cut before any essential requirement):**
  1. Voice (already out).
  2. Optional frontend Vitest test.
  3. No-key mode → banner only (−1 h).
  4. Numeric check → artifacts-only (−0.5 h).
  5. `rank_changes` diff.
  6. The LA-area alternative.
  7. Peer percentiles in Q4 → plain values.
  8. 3-month on-time expansion (not planned anyway).
- **Never cut:**
  - Live BTS API use.
  - The deterministic engine and its tests.
  - The chat UI.
  - Follow-ups.
  - Disclosures of assumptions, windows, and uncertainty.
  - architecture.md.
  - README.
- **Interview line:** "I planned with a 3-hour contingency and a written cut list, so if something slipped I'd drop polish, not requirements."

### P-021: No-key mode (user label **D8**)
- **Update 2026-10-30:** **REVISITED.** Approved in narrower form as **D-032**: presets only and no weights form. The original proposal is kept below.
- **Phase / status:** 3, PROPOSED (original). **Supersedes P-004** (rev 1: presets plus structured commands in the chat box).
- **Context:** a reviewer may lack an LLM key.
- **Can be shown without a key:**
  - The live BTS API call.
  - Deterministic results for the four preset scenarios, plus a Q1 weights form.
  - Evidence tables, provenance, windows, and warnings.
- **Requires a key:**
  - Free-text questions.
  - Interpreting new phrasing.
  - Follow-ups.
  - Narrative explanations.
  - Any question other than the presets.
- **Alternatives:**
  - *[discussed]* An error page only. Con: nothing can be verified.
  - *[discussed]* Structured text commands in the chat (P-004). Con: looks like chat but isn't, which risks misrepresentation, and needs a parser.
  - *[selected, proposed]* A clearly labelled "data explorer mode (AI unavailable)" with buttons and a form.
- **Must not** be presented as a conversational agent.
- **Validation (planned):** API tests for `/api/scenarios/*`, and a manual run with no key.
- **Impact:** about 1 h. Cut candidate #3.
- **Interview line:** "Without a key, reviewers can still verify the data and scoring path, and the UI says clearly it's not the AI agent."

### P-022: LLM model selection (user label **D9**)
- **Update 2026-10-30:** configurability and Phase 4 verification are **APPROVED as D-033**. The **default `claude-opus-5-5` remains PROPOSED**. The fallback order is P-028.
- **Update 2026-10-30 (close):** the user reaffirmed: "Do not assume a model is available merely because it is named in the design." **Availability is unverified at runtime** until the Phase 4 smoke test. The ID was verified only against documentation.
- **Phase / status:** 3, PROPOSED. **Supersedes P-003** (same model, now verified, plus LangChain configuration).
- **Verification:** `claude-opus-5-5`, `claude-sonnet-5-5`, and `claude-haiku-5-5` were confirmed on the Anthropic models overview page (2026-10-30). The LangChain Anthropic docs use `claude-opus-5-5`.
- **Alternatives:**

  | Model | Quality | Latency | Price per MTok in/out |
  |---|---|---|---|
  | Opus 5.5 | Highest | Moderate | $4 / $20 |
  | Sonnet 5.5 | High | Fast | $2 / $10 |
  | Haiku 5.5 | Lower | Fastest | from $0.10 / $0.50 |

- **Selected (proposed):** Opus 5.5 by default, `effort=medium` set explicitly, and the model, effort, and provider all configurable via env.
- **Why:** multi-tool reasoning and caveat discipline matter more than latency in a demo.
- **Tradeoff:** slower, more expensive responses. The user may choose Sonnet 5.5 for speed (that is the user's call).
- **Model-specific constraints:**
  - Thinking is adaptive and cannot be disabled.
  - No `temperature`.
  - Forced tool choice is not supported (LangChain `create_agent` uses automatic tool choice; to verify, A-019).
- **Validation (planned):** the Phase 4 spike plus scenario runs (record latency and token use).
- **Interview line:** "I defaulted to the strongest current model for tool-heavy reasoning but made it a config switch, and I verified the model ID instead of trusting memory."

### P-023: Serving and dev setup
- **Update 2026-10-30:** **APPROVED as D-034.**
- **Status:** PROPOSED (original).
- **Approach:** in dev, the Vite proxy forwards `/api`. For review, `npm run build` once, then FastAPI serves `frontend/dist` from the same origin. No CORS.
- **Alternatives:**
  - *[retrospective]* Two servers with CORS. Con: more reviewer steps.
  - *[retrospective]* Docker. Con: setup time.
- **Interview line:** "One process to run for the reviewer."

### P-024: LangChain tool design
- **Status:** PROPOSED (original). **APPROVED via D-042 (2026-10-30).**
- **Approach:**
  - Thin `@tool(args_schema=..., response_format="content_and_artifact")` wrappers over a pure engine with no LangChain imports.
  - Content is for the LLM. The artifact is for React.
  - Both are built from one engine result.
  - Business validation in the engine.
  - `@wrap_tool_call` middleware for structured errors.
- **Alternatives:**
  - *[retrospective]* Tools return full JSON to the LLM. Con: token cost, and the UI would depend on LLM echo.
  - *[retrospective]* Put the business logic inside the tools. Con: untestable without LangChain.
- **Validation (planned):** tool tests without an LLM.

### P-025: Git ignore fix for NOTES.md
- **Status:** **APPROVED as D-036.** Applied to the working tree. The commit is pending with the user. See §5.3.

### P-026: Optional non-blocking text number check (deferred)
- **Update 2026-10-30 (close):** **REVISITED: dropped by D-041.** The original text is kept below.
- **Status:** PROPOSED (original), **optional**, not in the MVP baseline (per D-030).
- **What it is:** extract numbers from the reply and match them against artifacts (rounding, % equivalence, ignore list). It shows a small notice, with no re-prompt.
- **Why deferred:**
  - False positives (rounding, units, restated inputs) and false negatives (coincidental matches).
  - The approved artifacts-first approach already guarantees the on-screen numbers.
- **When to reconsider:** only if contingency time remains after Phase 8.
- **Interview line:** "A text scanner is a nice safety net, but I made it optional because structured evidence already guarantees the numbers that matter."

### P-030: Detailed design of `aggregate_metrics`
- **Status:** PROPOSED. The direction is approved by D-044.
- **Design (architecture §5.1):**
  - Args: `evidence_ids` (1–10), `metric` (a registry id), `operation` (avg | sum | min | max), and an optional `airports` filter. **No numeric value fields.**
  - Reads values from the per-session evidence store.
  - Validation: IDs exist, the metric exists, a single window and unit, the operation is allowed for the metric (sum only for additive counts; avg labelled "unweighted mean"), and nulls are excluded and counted.
  - Output: `aggregate` evidence listing every input, with the provenance inherited.
- **Alternatives** *[retrospective]*:
  - Accept the values in the args, validated against the store. Con: still model-typed, and more failure modes.
  - Support weighted means. Con: needs denominators per metric, so deferred.
- **Validation:** see D-044.
- **Impact:** ≤ 1 h stretch in Phase 7, deferrable.

### P-028: Model fallback order for the Phase 4 smoke test
- **Status:** PROPOSED.
- **Order:**
  1. `claude-opus-5-5`.
  2. A model-specific failure → `claude-sonnet-5-5` (verified ID).
  3. An integration failure → pin or upgrade `langchain-anthropic` within 1.x.
- **Alternatives:**
  - *[retrospective]* Fall back to direct SDK calls. Rejected: conflicts with D-024.
  - *[retrospective]* Fall back to another provider. Rejected: untested, and adds a key requirement.
- **Interview line:** "I wrote down the fallback before I needed it, so a compatibility surprise wouldn't turn into a redesign."

---

## 4. Superseded / revisited decisions

| Original | Original content (kept) | Status | Replaced by | Why it changed |
|---|---|---|---|---|
| D-005 | Do not choose a stack before data is verified | REVISITED | D-022 to D-024 | Data verified in Phase 2. The user then chose the stack. |
| D-007 | Phase 1 provisionally approved | REVISITED | D-012 | Full approval given. |
| P-001 (UI part) | Python FastAPI + **static HTML/JS** UI, no build | REVISITED | D-022 (React + TS + Vite); backend part ≈ D-023 | User decision: a maintainable, typed evidence UI justifies the setup time. |
| P-002 | **Manual Claude tool-use loop**, no framework; Tool Runner rejected | REVISITED | D-024 (LangChain) | User decision: reusable agent infrastructure is worth the dependency. |
| P-003 | `claude-opus-5-5`, effort medium (unverified at the time beyond the skill reference) | REVISITED | P-022 | Re-verified against the official models page. LangChain configuration added. |
| P-004 | No-key mode via presets **and structured chat commands** | REVISITED | P-021 | Avoids making a command parser look like chat. Buttons and a form are clearer. |
| P-005 | Numeric grounding check **with an automatic re-prompt** | REVISITED | P-019 | False-positive and false-negative analysis. The structured artifacts are now the primary guarantee. |
| Rev 1 plan note | Fund P-004/P-005 from the buffer (buffer → about 0.5 h) | REVISITED | P-020 → D-031 | Unrealistic with React + LangChain. The buffer is now 3 h. |
| P-009 (part) | Below 300 departed flights → operational KPIs set to null (excluded) | REVISITED | D-029 | User: a configurable warning, not an exclusion |
| P-019 (part) | Non-blocking text number check in the baseline | REVISITED | D-030 + P-026 (optional) | User prefers code-generated evidence over scanning |
| P-020 | Revised budget with 3 h contingency | REVISITED (approved) | D-031 | Approved as a planning target |
| P-021 (part) | No-key presets **+ weights form** | REVISITED | D-032 | User limited the scope to a labelled deterministic demo |
| P-022 (part) | Model selection as one proposal | REVISITED (split) | D-033 (configurable + smoke test, approved); default stays PROPOSED; P-028 fallback | |
| P-023 | Single server + Vite proxy | REVISITED (approved) | D-034 | |
| P-025 | `.gitignore` fix | REVISITED (approved) | D-036 | |
| Rev 2 scoring details | KPI dropped if fewer than **2** values; ranking with at least **2** airports | REVISITED | P-027 (minimum 3) | Min-max on 2 points only yields 0/100 |
| P-026 | Optional non-blocking text number scanner | REVISITED (dropped) | D-041 | User decision. Unreliable. Artifacts-first plus propagation tests instead. |
| P-027 | Scoring spec v1 with options A/B/C | REVISITED (approved) | D-039 (option A) | User approval at Phase 3 close |
| P-006 to P-015 | Individual scoring and scenario proposals | REVISITED (approved) | D-039, D-040 | User approval at Phase 3 close |
| P-024 | LangChain tool design | REVISITED (approved) | D-042 | |
| D-038 | Update the plan later | REVISITED (executed) | D-043 | Plan updated 2026-10-30 |
| Delay rate (rev 1–3 wording) | "count(DepDel15=1) / count(departed), departed = rows − cancelled" | REVISITED (made precise) | P-029 | Denominator now also requires `DepDel15` not blank. Diverted flights explicitly included. Departure vs. arrival stated. |

---

## 5. Open questions, assumptions, and git hygiene

### 5.1 Open questions (need user input)
**Status at Phase 3 close (2026-10-30):** OQ-1, OQ-5, OQ-8, and OQ-9 are **resolved** by D-039, D-042 / D-041, D-040, and D-041. Remaining:
- **OQ-4:** default model (P-022) and fallback order (P-028). Confirmed by the Phase 4 smoke test.
- **OQ-10:** confirm the P-029 precise definitions.
- **OQ-11:** confirm the P-030 aggregate design (or let Phase 7 time decide).

| ID | Question | Related |
|---|---|---|
| OQ-10 | Confirm P-029 (delay rate = departure, cancellations excluded, diverted included; flight growth includes cargo; edge-case behaviours)? | D-039 |
| OQ-11 | Confirm P-030 (`aggregate_metrics` design)? | D-044 |
| OQ-1 | Approve the **exact scoring spec P-027** (formulas, min-max candidate-group normalization, default weights, coverage ≥ 0.60, minimum 3 airports and 3 values per KPI)? Normalization option A, B, or C? | D7 |
| ~~OQ-2~~ | ~~P-019 / P-020~~ → **resolved** by D-030 / D-031 | |
| ~~OQ-3~~ | ~~Commit snapshots before checks?~~ → **resolved** by D-037 (no) | |
| OQ-4 | Approve the **default model `claude-opus-5-5`** (P-022) and the fallback order P-028? | D9 |
| OQ-5 | Approve **P-024** (thin `@tool` wrappers, `content_and_artifact`, error middleware) and the evidence pipeline and test plan (architecture §10.1–10.2)? | D4 |
| ~~OQ-6~~ | ~~.gitignore fix~~ → **resolved** by D-036 (edited; commit pending with the user) | |
| ~~OQ-7~~ | ~~300-flight guard~~ → **resolved** by D-029 (configurable warning) | |
| OQ-8 | Approve P-010 (delay-based congestion), P-011 (LA → LAX by default), P-012 (long haul ≥ 3,000 mi, F+L, all-class variant), P-013 (Q4 three blocks), P-014 (July 2026 snapshots), P-015 (user weights over the registry), P-016 (sessions), P-017 (out-of-scope), P-018 (no voice)? | |
| OQ-9 | Keep P-026 (optional text check) in the cut list, or drop it entirely? | |

### 5.2 Assumptions
| ID | Assumption | Status |
|---|---|---|
| A-001 | Per-airport passenger volumes and trends are available | **Verified (live):** BTS SODA `r495-tyji` (2014→2026-07), FAA CY2025 xlsx |
| A-002 | Per-airport delay data is available | **Verified (live):** BTS on-time ZIP. Reporting carriers only. A file, not an API. |
| A-003 | Route-level departures with distance from ANC | **Verified (live):** T-100 Segment All Carriers via form POST |
| A-004 | Cargo vs. passenger distinguishable | **Verified:** T-100 `CLASS` (live). Code meanings from eCFR / BTS guide. |
| A-005 | No machine-readable terminal capacity data | Supported (not found within the time box) |
| A-006 | Capacity benchmarks exist publicly | Partially: FAA PDFs (2014–2019). Values not extracted. |
| A-007 | "Santa Ana" = SNA | **Verified (live)** |
| A-008 | ANC cargo materially affects long-haul % | **Verified (live):** G+P = 4,330 of 6,872 departures, Dec 2025 |
| A-009 | Sources usable in one day | Mostly. OpenSky needs an account. On-time download is slow. T-100 form is fragile. |
| A-010 | Reporting lag | **Verified:** latest month 2026-07 as of 2026-10-28 |
| A-011 | Automated TranStats form POST is acceptable | Unverified |
| A-012 | `r495-tyji` carrier coverage; truncated international field meanings | **Partially verified (2026-10-30):** the API totals equal the T-100 **Segment (All Carriers)** sums over classes F/G/L/P for Dec 2025 (ANC, SFO, SNA), so coverage = the T-100 All Carriers table. `domestic_departures + outbound_international = total_departures`. The meanings of the truncated `outbound_international_1..4` fields are still unverified (not used). |
| A-013 | FAA TAF per-airport values usable | Unverified (file and headers only) |
| A-014 | OurAirports licence allows redistribution | Unverified |
| A-015 | July 2026 T-100 download works like Dec 2025 | Unverified |
| A-016 | T-100 `DISTANCE` is in statute miles | Unverified |
| A-017 | 300-flight threshold is a reasonable *warning* level | Unverified. Now a configurable warning (D-029). Check the distribution in the snapshot. |
| A-018 | LangChain's default handling of Pydantic tool-arg validation errors (vs. our middleware) | Unverified (Phase 4 spike) |
| A-019 | `create_agent` + `ChatAnthropic` work with `claude-opus-5-5`: automatic tool choice, adaptive thinking blocks round-trip through `InMemorySaver` history | Unverified (Phase 4 spike) |
| A-020 | `recursion_limit` in the run config bounds tool rounds as expected | Unverified (Phase 4 spike) |
| A-021 | A fake chat model is available in langchain-core test utilities for API tests | Unverified (Phase 4) |
| A-023 | API `total_departures` includes all-cargo classes; seats and passengers come from passenger-capable classes | **Verified (2026-10-30):** ANC Dec 2025 G 2,932 + P 1,398 of 6,872 departures. Seats: F 238,358, L 10,171, P 137, G 0. |
| A-024 | On-time `DepDel15` blank ⇔ cancelled; definitions per the BTS Fields page | **Verified (2026-10-30, SFO Jul 2026):** 156 blanks, all cancelled. 3 cancelled rows have a `DepDel15` value (excluded by the `Cancelled=0` rule). No blank `TaxiOut` on non-cancelled rows. |
| A-022 | `ToolMessage.artifact` is preserved on the messages returned by `agent.ainvoke` (and through the checkpointer) for `content_and_artifact` tools | Unverified (Phase 4 spike). Fallback: a `contextvars` collector (architecture §10.1 step 5). |

### 5.3 Why NOTES.md is ignored by Git, and the fix (P-025 → **approved as D-036**, applied to the working tree on 2026-10-30, commit pending with the user)
> **Applied version:** see D-036. It also ignores `data/processed/` until the D-037 checks pass. The proposal text below is kept as written.
- **Exact rule:** `.gitignore` **line 2: `NOTES.md`**.
  - Confirmed with `git check-ignore -v --no-index NOTES.md` → `.gitignore:2:NOTES.md`.
  - The line was added in commit `3b91e03` ("finished phase 2 - collect data sources").
- **Current effect:** NOTES.md is **still tracked**. It was committed earlier, and the same commit `3b91e03` also included a NOTES.md update. Git keeps tracking files that are already tracked even when they match an ignore rule, so `git status` still shows `M NOTES.md`.
  - The rule is contradictory and fragile: if the file is ever removed from the index (`git rm --cached`) or re-created in a fresh clone workflow, it silently stops being versioned.
  - Editors may also show it as ignored.
- **Secret check:** NOTES.md contains no credentials, keys, or tokens. It does contain public URLs and observed public data values.
- **Proposed safe fix (the user applies it; not applied by the assistant):**
  1. Remove line 2 (`NOTES.md`) from `.gitignore`.
  2. Add secret and artifact rules ahead of Phase 4:
     ```
     # Assignment document (local only)
     FDE Exam 2.pdf
     # Secrets
     .env
     .env.*
     !.env.example
     # Raw downloads (large, regenerate via scripts/build_snapshots.py)
     data/raw/
     # Python / Node build artifacts
     .venv/
     __pycache__/
     *.pyc
     node_modules/
     frontend/dist/
     ```
  3. Commit `.gitignore` and NOTES.md together. Verify with `git check-ignore -v --no-index NOTES.md`, which should print nothing.

---

## 6. Rejected alternatives (rationale)
| Date | Alternative | Why rejected | Related |
|---|---|---|---|
| 2026-10-28 | Estimating profitability or ROI | No financial data. Would require invented inputs. | D-010 |
| 2026-10-29 | Strategy 2, live API only | Too weak for Q2–Q4 | D-016 |
| 2026-10-29 | Strategy 3, API + OpenSky (MVP) | Account and OAuth required. Estimated airports. Passenger vs. cargo ambiguous. Deferred. | D-016 |
| 2026-10-29 | FAA capacity-PDF values in scoring | Dated, manual, not machine-readable | D-020 |
| 2026-10-29 | Calling downloaded files "APIs" | Misrepresentation | D-017 |
| 2026-10-29 | A single "unmet demand" number | Not measurable | D-021 |
| 2026-10-30 | Plain HTML/JS UI | User chose React for a typed, maintainable evidence UI | D-022 (supersedes P-001 UI) |
| 2026-10-30 | Streamlit | Merges UI and backend. Less contract clarity. | D-022 |
| 2026-10-30 | Node.js backend | Rewriting data code. More dependencies. Weaker data ecosystem. | D-023 |
| 2026-10-30 | Hand-written direct tool loop | User chose LangChain for reusable orchestration | D-024 (supersedes P-002) |
| 2026-10-30 | LangGraph custom graph, vector DB/RAG, Redis, microservices | No requirement justifies them | D-024, architecture §2 |
| 2026-10-30 | Hardcoded four intents | Brittle, not an agent | D-025 |
| 2026-10-30 | Blocking numeric re-prompt | False positives and negatives, latency | P-019 (supersedes P-005) |
| 2026-10-30 | Fixed-range normalization (as default) | Would require invented bounds | P-008 (proposed) |
| 2026-10-30 | Imputing missing KPIs | Hides gaps | P-009 (proposed) |
| 2026-10-30 | A 0.5 h buffer | Unrealistic | P-020 → D-031 (approved) |
| 2026-10-30 | Excluding operational KPIs below 300 flights | Hides data. Arbitrary cutoff. | D-029 |
| 2026-10-30 | Text-scan number check in the MVP baseline | False positives and negatives. Artifacts-first preferred. | D-030 (scan → optional P-026) |
| 2026-10-30 | No-key structured chat commands or weights form | Looks conversational. Scope creep. | D-032 |
| 2026-10-30 | Hand-set fixed normalization ranges | Invented bounds | P-027 option C (not recommended) |
| 2026-10-30 | Committing processed snapshots now | Licensing and provenance not yet verified | D-037 |
| 2026-10-30 | National reference (P5–P95) normalization for the MVP | +1 h, clipping, parameter choice. Deferred as a documented upgrade. | D-039 |
| 2026-10-30 | Post-hoc number scanner (any form) | Unreliable. Dropped by the user. | D-041 |
| 2026-10-30 | LLM performing arithmetic on investment numbers | Unverifiable, may invent or retype inputs | D-044 |
| 2026-10-30 | Arbitrary code or expression calculator tool | Security and validation burden. Inputs still model-supplied. | D-044 |
| 2026-10-30 | Arrival-based or combined delay rate in scoring | Reflects upstream airports, mixes causes | P-029 |
| 2026-10-30 | Estimating passenger-only departures for the API series | An invented cross-period estimate | P-029 |

---

## 7. Phase 2 research findings (reference)
Details are in `data-sources-research.md`. Approved choices: D-016 to D-021.
- **Verified live, no key needed:**
  - BTS SODA `r495-tyji`
  - TranStats T-100 Segment (All Carriers) via form POST
  - BTS on-time monthly ZIP
  - FAA CY2025 enplanements xlsx
  - FAA NAS status / ASWS (snapshot only)
  - OurAirports CSV
  - FAA capacity-profile PDFs and the TAF zip (files exist; values not extracted)
- **Blockers:**
  - OpenSky history (403 without an account)
  - legacy ASWS host (DNS failure)
  - ATADS/ASPM (503 at test time)
  - BTS Socrata on-time "datasets" (charts only)
  - no terminal capacity data found

---

## 8. Interview preparation
Format: challenge → alternatives → decision → tradeoff → outcome. "Outcome" stays *pending* until there is implementation evidence.

1. **Profitability without financial data.**
   - Alternatives: invent cost and revenue assumptions, or reframe.
   - Decision: transparent demand-pressure indicators (D-010).
   - Tradeoff: does not literally answer "most profitable".
   - Outcome: pending (scenario checks).
2. **"Use public APIs" vs. where the data actually lives.**
   - Alternatives: API only, files only, API + OpenSky, or hybrid.
   - Decision: live BTS API + labelled snapshots (D-016, D-017).
   - Tradeoff: two data paths and stale snapshots.
   - Outcome: pending.
3. **Unmet demand at SFO.**
   - Alternatives: a proxy-based number, or an evidence profile.
   - Decision: three blocks with "not measured" (D-021, P-013).
   - Tradeoff: a less "headline" answer.
   - Outcome: pending.
4. **LangChain vs. direct tool calling.**
   - Alternatives: the manual SDK loop, Tool Runner, LangChain, or a LangGraph graph.
   - Decision: LangChain `create_agent` with our own Python tools (D-024).
   - Tradeoff: dependency and abstraction vs. less plumbing.
   - Outcome: pending (Phase 4 spike A-019).
5. **Keeping numbers honest.**
   - Alternatives: post-hoc scan + re-prompt, placeholders, or artifacts-first.
   - Decision: artifacts rendered by React + a non-blocking check (P-019, proposed).
   - Tradeoff: prose may still contain an untraceable number, but it is flagged.
   - Outcome: pending.
6. **Normalization choice.**
   - Alternatives: min-max, fixed-range, or percentile.
   - Decision: min-max with raw values shown (P-008, proposed).
   - Tradeoff: scores are relative to the set.
   - Outcome: pending.
7. **Anchorage long haul.**
   - Alternatives: include cargo, or passenger-only.
   - Decision: F+L default, with the all-class figure always shown (P-012, proposed).
   - Tradeoff: two numbers to explain.
   - Outcome: pending.
8. **Schedule risk.**
   - Alternatives: a thin buffer with all extras, or a 3 h contingency with a cut list.
   - Decision: P-020, approved as D-031 (planning target).
   - Tradeoff: fewer optional features.
   - Outcome: pending.
9. **Frontend choice.**
   - Alternatives: plain HTML, Streamlit, or React.
   - Decision: React + TS (D-022).
   - Tradeoff: setup time vs. typed, maintainable evidence rendering.
   - Outcome: pending.
10. **Small samples.**
    - Alternatives: exclude below 300 flights, shrinkage, or flag.
    - Decision: keep and flag with a configurable threshold (D-029).
    - Tradeoff: noisy values can move scores but are visible.
    - Outcome: pending.
11. **Getting structured results through an agent framework.**
    - Alternatives: the LLM echoes numbers, scan the text, or artifacts.
    - Decision: LangChain `content_and_artifact` → FastAPI `evidence[]` → typed React components (D-030), with a `contextvars` fallback.
    - Tradeoff: depends on framework behaviour (A-022), verified in a spike.
    - Outcome: pending.
12. **Third-party data redistribution.**
    - Alternatives: commit snapshots now, or after checks.
    - Decision: after licensing and provenance checks (D-037).
    - Tradeoff: reviewers rebuild locally until then.
    - Outcome: pending.
13. **Verifying fields before approving formulas.**
    - Alternatives: trust the field names, or check them against data.
    - Decision: check them (P-029).
    - Finding: the API's departures include cargo, and DepDel15 is blank only for cancellations.
    - Tradeoff: about 20 minutes of checks.
    - Outcome: definitions made precise. Implementation pending.
14. **Flexibility vs. deterministic numbers.**
    - Alternatives: LLM arithmetic, an expression tool, more domain tools, or a reference-only aggregate tool.
    - Decision: `aggregate_metrics` over evidence references, time-boxed (D-044).
    - Tradeoff: medium flexibility, high reliability.
    - Outcome: pending (deferrable).
