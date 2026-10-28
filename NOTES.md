# NOTES.md: Decision Log

Format: each entry has an ID, a date, the decision, and the reason. Status values: **Decided**, **Proposed** (awaiting approval), or **Open**.

---

## 1. Decisions already made

| ID | Date | Decision | Reason |
|---|---|---|---|
| D-001 | 2026-10-28 | `FDE Exam 2.pdf` is the single source of truth for requirements. | Avoids scope drift. Requirements are traceable. |
| D-002 | 2026-10-28 | Work in phases. Each phase needs explicit user approval before it starts. | User instruction. Keeps major choices visible and reviewable. |
| D-003 | 2026-10-28 | `requirements.md` was created as the requirements analysis (draft, under user review). | Phase 1 deliverable. |
| D-004 | 2026-10-28 | Project working rules are in `CLAUDE.md`. Decisions are logged in this file. | User instruction. |
| D-005 | 2026-10-28 | No architecture, technology stack, data source, scoring formula, or AI framework has been chosen yet. | Data feasibility must be verified first (requirements.md §8.2). |
| D-006 | 2026-10-28 | Next phase: time-boxed public data source research and verification for Q1–Q4. **Approved, see D-008.** | Data availability is the highest risk (requirements.md R-1). |
| D-007 | 2026-10-28 | **Phase 1 is provisionally approved** (requirements.md, CLAUDE.md, NOTES.md). The user approved it based on summaries, and a full review of the documents may still follow. | User approval. |
| D-008 | 2026-10-28 | **Phase 2 is approved:** feasibility research on public aviation data sources. | User approval. Addresses risk R-1. |
| D-009 | 2026-10-28 | **Phase 2 is time-boxed to about 2 hours.** Verify the most useful data sources first and find blockers (access, keys, rate limits, coverage gaps) early. | Fits the 24-hour budget. Surfaces blockers before the architecture is chosen. |
| D-010 | 2026-10-28 | **The agent will use evidence-based investment opportunity indicators.** It will not claim to calculate actual investment profitability or ROI without enough financial data. Resolves O-001. | Public aviation data does not support profitability or ROI figures (requirements.md §1.3). Invented profitability numbers would be a credibility risk. |
| D-011 | 2026-10-28 | **The business goal stays unchanged:** help analysts identify promising airport modernization investments, based on increased flight and passenger capacity. D-010 changes how results are framed, not the goal. | User instruction. The PDF is the source of truth. |
| D-012 | 2026-10-28 | **Phase 1 is approved for finalization** and committed. Supersedes the provisional status in D-007. | User approval. |
| D-013 | 2026-10-28 | Document names: Phase 2 produces `data-sources-research.md`. The PDF's design/architecture document is `architecture.md`, drafted in Phase 3 and finalized in Phase 9. | User instruction. Keeps naming consistent with implementation-plan.md. |
| D-014 | 2026-10-28 | `FDE Exam 2.pdf` is kept locally and excluded from Git via `.gitignore`. | User instruction. The assignment document is not uploaded to the repository. |

## 2. Decisions still open

| ID | Decision | Ref | Impact |
|---|---|---|---|
| ~~O-001~~ | ~~How to frame "most profitable" vs. measurable indicators.~~ **Resolved by D-010 / D-011.** The specific indicators are still open (see O-003). | OQ-1 | High |
| O-002 | Definition of the "unmet flight demand" proxy, and how far "why" explanations may go. | OQ-2 | High |
| O-003 | Terminal-expansion KPI: inputs, normalization, weights. | OQ-3 | High |
| O-004 | Definition of "congestion" (delay-based, utilization-based, or composite). | OQ-4 | High |
| O-005 | Long-haul threshold (distance or duration), and whether cargo flights are included. | OQ-5 | High |
| O-006 | Entity resolution: "LA" (LAX only or the LA-area system?), "Santa Ana" (SNA?), and the eligible-airport rule for regions. | OQ-6 | Medium |
| O-007 | Whether public bulk datasets count as "public APIs", and whether to fetch live or use a cache/snapshot. | OQ-7 | High |
| O-008 | Target time window and data freshness. | OQ-8 | Medium |
| O-009 | Form of the chat interface (web, CLI, notebook). | OQ-9 | Low–Medium |
| O-010 | LLM provider and AI framework, and how reviewers supply keys. | OQ-10 | Medium |
| O-011 | Behaviour for out-of-scope or unsupported questions. | OQ-11 | Medium |
| O-012 | How far to generalize beyond the four example questions. | OQ-12 | Medium |
| O-013 | Whether to attempt voice (bonus). | OQ-13 | Low |
| O-014 | Architecture and technology stack. | §8.2 step 6 | High |

## 3. Assumptions requiring verification

| ID | Assumption | How to verify | Status |
|---|---|---|---|
| A-001 | Public sources provide per-airport passenger volumes (enplanements) and trends for US airports. | Real request or download from candidate sources | Unverified |
| A-002 | Public sources provide per-airport delay / on-time data usable for a congestion metric. | Same as A-001 | Unverified |
| A-003 | Public sources provide flight- or route-level departures from ANC with destinations or distances. | Same as A-001 | Unverified |
| A-004 | Public data distinguishes cargo flights from passenger flights. | Same as A-001 | Unverified |
| A-005 | Terminal/gate capacity data is **not** available in a standard machine-readable public form. | Search and check candidate sources | Unverified |
| A-006 | Airport capacity or throughput benchmarks exist publicly, so a utilization metric could be built. | Search and check candidate sources | Unverified |
| A-007 | "Santa Ana" refers to John Wayne Airport (SNA). | Airport reference data | Unverified |
| A-008 | Anchorage has significant cargo traffic, enough to change a long-haul percentage materially. | Data from A-003 / A-004 | Unverified |
| A-009 | Chosen data sources are usable within a one-day build (keys obtainable, rate limits acceptable, free access). | Sign-up and test calls | Unverified |
| A-010 | Some official statistics are published with a reporting lag (not real-time). | Source documentation | Unverified |

## 4. Future decisions and rejected alternatives

Log each future decision here with: the date, the decision, the alternatives considered, why the alternatives were rejected, and links to related IDs.

### Decisions
_None yet._

### Rejected alternatives
_None yet._
