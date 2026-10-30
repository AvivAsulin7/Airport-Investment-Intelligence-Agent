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
| D-015 | 2026-10-29 | **Phase 2 is completed and approved.** `data-sources-research.md` is accepted. Phase 3 is approved to begin after the user's Phase 2 commit. | User approval. |
| D-016 | 2026-10-29 | **Data strategy: Strategy 1, "BTS-centric hybrid".** The live BTS Socrata API (`r495-tyji`) is used, plus supplementary public aviation data files (T-100 Segment, BTS on-time, FAA enplanements, OurAirports). Resolves O-015. | Best coverage of Q1–Q4 with no keys needed (data-sources-research.md §5). Strategy 2 was rejected and Strategy 3 deferred (see §5 below). |
| D-017 | 2026-10-29 | **The application must genuinely use a public API** (the BTS Socrata SODA API, called by the application). Public file downloads are **supplementary** and must **not** be described as APIs anywhere: UI, answers, README, or `architecture.md`. Resolves O-016 and O-007. | PDF FR-1 ("Use public APIs to gather airport/aviation data"). Honest representation of sources. |
| D-018 | 2026-10-29 | **Analysis window:** 12 months from the BTS API, where the data supports it. **Initially one verified month** of route-level (T-100) and on-time data. On-time delay data may expand to **three months only if feasible** (download size and time). **Every answer and document discloses the time window used.** Resolves O-017 and O-008. | Balances representativeness against the 24-hour budget. One on-time month ≈ 33 MB and took about 356 s to download. |
| D-019 | 2026-10-29 | **Prefer small, reproducible processed snapshots** for the demo, subject to licensing verification (A-011, A-014), recorded provenance (source, URL, retrieval date, data period), and reasonable repository size. **Never commit large raw downloads or credentials.** Resolves O-018. | Demo stability and reproducibility. Repository hygiene. CLAUDE.md §8. |
| D-020 | 2026-10-29 | **The old FAA runway capacity profile PDF values (2014–2019) are not used in the primary scoring model.** They may be referenced only as clearly dated historical context. Resolves O-019. | The values are dated, manually transcribed, and not machine-readable. Using them for scoring would harm credibility. |
| D-021 | 2026-10-29 | **The agent explicitly distinguishes three concepts:** (1) **observed demand** (measured traffic: passengers, departures, seats), (2) **capacity-pressure indicators** (for example, load factor, delays, taxi-out, cancellations), and (3) **unmet demand**, which is **not measured**. Delays and load factors are **never** presented as direct measurements of unmet demand. | Data integrity (CLAUDE.md §4, §6). Q4 is proxy-only (data-sources-research.md §3.5). |

## 2. Decisions still open

| ID | Decision | Ref | Impact |
|---|---|---|---|
| ~~O-001~~ | ~~How to frame "most profitable" vs. measurable indicators.~~ **Resolved by D-010 / D-011.** The specific indicators are still open (see O-003). | OQ-1 | High |
| O-002 | Definition of the "unmet flight demand" proxy, and how far "why" explanations may go. | OQ-2 | High |
| O-003 | Terminal-expansion KPI: inputs, normalization, weights. | OQ-3 | High |
| O-004 | Definition of "congestion" (delay-based, utilization-based, or composite). | OQ-4 | High |
| O-005 | Long-haul threshold (distance or duration), and whether cargo flights are included. | OQ-5 | High |
| O-006 | Entity resolution: "LA" (LAX only or the LA-area system?), "Santa Ana" (SNA?), and the eligible-airport rule for regions. | OQ-6 | Medium |
| ~~O-007~~ | ~~Whether public bulk datasets count as "public APIs", and whether to fetch live or use a cache/snapshot.~~ **Resolved by D-017 / D-019.** | OQ-7 | High |
| ~~O-008~~ | ~~Target time window and data freshness.~~ **Resolved by D-018.** | OQ-8 | Medium |
| O-009 | Form of the chat interface (web, CLI, notebook). | OQ-9 | Low–Medium |
| O-010 | LLM provider and AI framework, and how reviewers supply keys. | OQ-10 | Medium |
| O-011 | Behaviour for out-of-scope or unsupported questions. | OQ-11 | Medium |
| O-012 | How far to generalize beyond the four example questions. | OQ-12 | Medium |
| O-013 | Whether to attempt voice (bonus). | OQ-13 | Low |
| O-014 | Architecture and technology stack. | §8.2 step 6 | High |
| ~~O-015~~ | ~~Data strategy.~~ **Resolved by D-016** (Strategy 1). | data-sources-research.md §5 | High |
| ~~O-016~~ | ~~Whether public file downloads plus a live API satisfy "use public APIs".~~ **Resolved by D-017.** | data-sources-research.md §4 | High |
| ~~O-017~~ | ~~Data window and on-time ingestion volume.~~ **Resolved by D-018.** | §3.3 | Medium |
| ~~O-018~~ | ~~Commit derived snapshots or fetch at setup.~~ **Resolved by D-019** (snapshots preferred, pending A-011 / A-014). | §5 | Medium |
| ~~O-019~~ | ~~Use of FAA capacity-profile PDFs.~~ **Resolved by D-020** (context only, not scoring). | §2.7 | Low–Medium |

## 3. Assumptions requiring verification

| ID | Assumption | How to verify | Status |
|---|---|---|---|
| A-001 | Public sources provide per-airport passenger volumes (enplanements) and trends for US airports. | Real request or download from candidate sources | **Verified (live):** BTS SODA `r495-tyji` (monthly 2014→2026-07) and the FAA CY2025 enplanements xlsx. |
| A-002 | Public sources provide per-airport delay / on-time data usable for a congestion metric. | Same as A-001 | **Verified (live):** BTS on-time monthly ZIP (DepDel15, TaxiOut, delay causes…). Reporting carriers only, bulk file rather than API. |
| A-003 | Public sources provide flight- or route-level departures from ANC with destinations or distances. | Same as A-001 | **Verified (live):** T-100 Segment (All Carriers) via TranStats form POST (DISTANCE, DEPARTURES_PERFORMED). |
| A-004 | Public data distinguishes cargo flights from passenger flights. | Same as A-001 | **Verified:** T-100 `CLASS` field (live). Code meanings F/G/L/P are from documentation (eCFR / BTS guide). |
| A-005 | Terminal/gate capacity data is **not** available in a standard machine-readable public form. | Search and check candidate sources | **Supported (not found in time box).** Not proven absent. |
| A-006 | Airport capacity or throughput benchmarks exist publicly, so a utilization metric could be built. | Search and check candidate sources | **Partially:** FAA Airport Capacity Profiles exist as PDFs (LAX 2014, SFO 2019, BOS 2019, SNA 2014 appendix). Values not extracted. Dated. |
| A-007 | "Santa Ana" refers to John Wayne Airport (SNA). | Airport reference data | **Verified (live):** OurAirports KSNA municipality "Santa Ana". FAA lists SNA city "Santa Ana". |
| A-008 | Anchorage has significant cargo traffic, enough to change a long-haul percentage materially. | Data from A-003 / A-004 | **Verified (live, Dec 2025 probe):** all-cargo classes G+P = 4,330 of 6,872 ANC departures performed. |
| A-009 | Chosen data sources are usable within a one-day build (keys obtainable, rate limits acceptable, free access). | Sign-up and test calls | **Mostly:** BTS/FAA/OurAirports need no keys. OpenSky history needs an account (403 anonymous). The on-time download is slow (356 s per month). The T-100 form postback is fragile. |
| A-010 | Some official statistics are published with a reporting lag (not real-time). | Source documentation | **Verified (live):** latest BTS T-100 and on-time month = July 2026, as of 2026-10-28 (about a 3-month lag). |
| A-011 | Automated POSTs to the TranStats download form are acceptable (terms, rate limits). | Terms of use / BTS docs | Unverified |
| A-012 | BTS SODA `r495-tyji` includes foreign carriers. The meaning of truncated `outbound_international_N` fields is unknown. | Dataset docs | Unverified |
| A-013 | FAA TAF per-airport values (locid format, field semantics) are usable as a demand-forecast proxy. | Parse the TAF xlsx properly | Unverified (file and headers verified only) |
| A-014 | OurAirports license permits redistribution of derived data. | License page | Unverified |

## 4. Phase 2 research findings (2026-10-28, approved 2026-10-29, see D-015)

Details are in `data-sources-research.md`. The approved choices from these findings are D-016 to D-021.

- **Verified live, no key needed:**
  - BTS SODA API `r495-tyji` (monthly per-airport traffic, 2014→2026-07)
  - TranStats T-100 Segment (All Carriers) via form POST (route-level, with DISTANCE and CLASS)
  - BTS on-time monthly ZIP (delays and causes)
  - FAA CY2025 enplanements xlsx (state, FAA region, hub)
  - FAA NAS status / ASWS (real-time snapshot only)
  - OurAirports CSV
  - FAA capacity-profile PDFs and the TAF zip (files exist, values not extracted)
- **Blockers / not usable:**
  - OpenSky historical flights (403 without an account)
  - legacy FAA ASWS host (DNS failure)
  - FAA ATADS/ASPM (503 at test time)
  - BTS Socrata on-time "datasets" (charts with national aggregates only)
  - no machine-readable terminal capacity data found
- **Feasibility (preliminary):** Q1 proxy ranking · Q2 delay-based comparison · Q3 directly measurable once definitions are set · Q4 proxy only, with data-backed "why".
- **Risks surfaced:**
  - T-100 form fragility
  - on-time download size and time (about 356 s per month)
  - "LA" ambiguity
  - the "public API" interpretation (O-016)

## 5. Future decisions and rejected alternatives

Log each future decision here with: the date, the decision, the alternatives considered, why the alternatives were rejected, and links to related IDs.

### Decisions
_None yet._

### Rejected alternatives
| Date | Alternative | Why rejected | Related |
|---|---|---|---|
| 2026-10-29 | Strategy 2, "Live-API-first, minimal files" | Too weak for Q2–Q4: no delay history, no true long-haul %, weak "why". | D-016 |
| 2026-10-29 | Strategy 3, "Hybrid + OpenSky" (for the MVP) | Requires account registration and OAuth credentials for reviewers. Airports are estimated, and passenger vs. cargo is ambiguous. Adds little over T-100. Deferred, not used in the MVP. | D-016 |
| 2026-10-29 | FAA capacity-profile PDF values as primary scoring inputs | Dated (2014–2019), manually transcribed, and not machine-readable. | D-020 |
| 2026-10-29 | Presenting downloaded public files as "APIs" | Misrepresents sources. Violates honest reporting of FR-1. | D-017 |
