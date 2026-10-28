# Requirements: Airport Investment Intelligence Agent

**Source of truth:** `FDE Exam 2.pdf` (Deloitte Digital, Forward Deployed Engineer exam, created July 2026). The PDF has 3 pages: a cover page, one page with the assignment, and a blank page. All requirements below come from page 2.

**Labels used in this document**

| Label | Meaning |
|---|---|
| **[EXPLICIT]** | Stated directly in the PDF (quoted where practical). |
| **[INTERPRETATION]** | A reasonable reading of PDF wording that the PDF does not spell out. |
| **[ASSUMPTION]** | A working assumption we would need to state openly in the deliverables. |
| **[OPTIONAL]** | An enhancement. Either the PDF calls it a bonus, or we propose it and it is not required. |
| **[TO VERIFY]** | A factual claim about data or APIs that we have not checked yet. |

Status: approved in Phase 1 (NOTES.md D-012). No architecture, technology stack, or data source has been chosen. Later decisions are recorded in `NOTES.md`.

---

## 1. Business Goal

### 1.1 The firm's objective [EXPLICIT]
> "We are a firm that invests in airport modernization projects in the US. We are exploring how AI agents can help analysts identify promising airport investment opportunities. The goal of the agent is to help us identify airports where renovations will be most profitable based on increased flight and passenger capacity."

Key points:
- **Who:** an investment firm that funds airport modernization projects.
- **Where:** airports in the US only.
- **Users:** analysts. The agent supports their work and does not make the investment decision.
- **Value hypothesis:** a renovation pays off when it unlocks more flights and passengers. Profitability is tied to "increased flight and passenger capacity."
- **Framing:** "exploring how AI agents can help". This reads as a proof of concept, not a production system. [INTERPRETATION]

### 1.2 Decisions the agent should help analysts make [INTERPRETATION]
Based on the goal and the four example questions:
1. **Screening:** which airports in a region are worth a closer look (for example, terminal expansion candidates in New England).
2. **Comparison:** how two or more airports differ on an operational measure (for example, LAX vs. Santa Ana congestion).
3. **Profiling:** facts about one airport's traffic mix (for example, the share of long-haul flights from Anchorage).
4. **Diagnosis:** where demand appears to exceed capacity at an airport, and what could explain it (for example, unmet demand at SFO).

### 1.3 Business goal vs. what public aviation data can measure
This gap is the main credibility issue in the assignment and should be stated openly in the solution.

| Business concept | Measurable with public aviation data? | Notes |
|---|---|---|
| **Renovation profitability** (ROI, IRR, revenue uplift) | **No, not directly.** | Measuring it would need project costs, airport financials, concession and aeronautical revenue, financing terms, and regulatory constraints. None of these is implied by "public aviation data." We must **not** invent profitability figures. [ASSUMPTION] The agent can rank **operational indicators that relate to the investment thesis** (demand, growth, capacity pressure). It cannot rank profitability. |
| **Increased flight capacity** | **Partially.** | Flight counts and schedules may be available. Capacity (what the airport *could* handle) is harder to find and may come from separate benchmark data or need a proxy. [TO VERIFY] |
| **Increased passenger capacity** | **Partially.** | Passenger volumes (enplanements) may be published. Terminal passenger capacity is often not available in a standard machine-readable form. [TO VERIFY] |
| **Demand exceeding capacity** ("unmet demand") | **Not directly observable.** | Can only be inferred through proxies (delays, load factors, growth vs. flat capacity, schedule constraints). See Section 5. |

**Implication [INTERPRETATION]:** the agent's output should be presented as *"indicators of capacity pressure and growth that support or weaken an investment thesis"*, not as *"most profitable airports."* The design document must make this scoping explicit (see Requirement NFR-3). *(Adopted as NOTES.md D-010. The business goal itself is unchanged, D-011.)*

---

## 2. Explicit Functional Requirements

### 2.1 Core capability [EXPLICIT]
> "Build an AI-powered agent that can answer questions such as: …"

- **FR-0:** The system is an *AI-powered agent* that answers natural-language questions about US airports in the context of investment analysis.
- The phrase "questions **such as**" means the four questions are **examples**, not a closed list. [INTERPRETATION] The agent should handle these four questions and reasonable variations of them (other airports, regions, or metrics of the same kind).

### 2.2 The four example questions [EXPLICIT, preserved verbatim]

| ID | Question (verbatim) | Capability it tests [INTERPRETATION] |
|---|---|---|
| **Q1** | "Which airports in New England are strong candidates for terminal expansion?" | **Regional screening and ranking.** Resolve a region (New England) to a set of airports, apply a defined scoring KPI for "terminal expansion candidacy," and return a ranked list with an explanation. This is the question that most directly reflects the business goal and exercises the deterministic scoring requirement. |
| **Q2** | "Compare LA and Santa Ana airport congestion levels." | **Pairwise comparison on a defined metric.** Resolve informal names ("LA", "Santa Ana") to specific airports, define "congestion" in measurable terms, and present a side-by-side comparison. Tests entity resolution, metric definition, and comparison logic. |
| **Q3** | "What is the percentage of long haul flights out of Anchorage airport?" | **Factual, computed metric for one airport.** Needs a precise definition of "long haul," flight-level or route-level data with distances, and a deterministic calculation. Tests data retrieval, definitions, and accurate arithmetic (not LLM estimation). |
| **Q4** | "What is the unmet flight demand in SFO airport and why?" | **Inference and explanation.** "Unmet demand" is not directly observable, so the agent must estimate it with proxies and explain likely causes. Tests reasoning, honest uncertainty, and resistance to stating unsupported causes. The "why" part is the riskiest for hallucination. |

### 2.3 Agent behaviours [EXPLICIT]
> "The Agent Should:"

| ID | Requirement (verbatim) | Notes |
|---|---|---|
| **FR-1** | "Use public APIs to gather airport/aviation data" | Data must come from public sources, accessed programmatically. Open question: does a public downloadable dataset (not a live REST API) count? See OQ-7. |
| **FR-2** | "Rank or compare airports based on your defined logic or KPI" | We define the logic and KPIs. "Rank **or** compare" covers both Q1 (ranking) and Q2 (comparison). The phrase "your defined" means the definitions are ours and must be documented. |
| **FR-3** | "Explain its reasoning clearly" | Each answer should show which data, definitions, and calculations led to the result, in language an analyst can follow. |
| **FR-4** | "Support conversational follow-up questions" | The agent keeps context across turns. For example, after Q1, "Why is #2 ranked above #3?" or "Now include passenger growth" should work without the user restating everything. [INTERPRETATION] |

---

## 3. Explicit Non-Functional and Design Requirements

| ID | Requirement | Source | Notes |
|---|---|---|---|
| **NFR-1** | **Deterministic scoring/ranking logic.** "Include some deterministic scoring or ranking logic (not only LLM output)" | [EXPLICIT] | At least one scoring or ranking step must be computed by code: reproducible, inspectable, and the same output for the same input. The LLM should not produce the scores or rankings itself. "Some" sets a minimum, but the scoring KPI is central to Q1 and Q2, so in practice the core ranking and comparison metrics should be deterministic. [INTERPRETATION] |
| **NFR-2** | **Chat interface.** "Include a chat interface to talk with the agent (voice is a bonus)" | [EXPLICIT] | A chat interface is required. The form (web UI, CLI, notebook, and so on) is not specified. See OQ-9. **Voice is [OPTIONAL]**, explicitly labeled a bonus. |
| **NFR-3** | **Communicate assumptions, uncertainty, and scoping.** "Clearly communicate assumption, uncertainty and scoping" | [EXPLICIT] | Applies to **agent responses**, for example: "long haul is defined as …", "data covers period X", "unmet demand is a proxy estimate". It also applies to the **design document**. [INTERPRETATION] |
| **NFR-4** | **Time constraint.** "Timeframe: 24 hours" / "intended to be achievable in approximately one day" | [EXPLICIT] | Scope must fit about one day of work. |
| **NFR-5** | **Evaluation emphasis.** "Prioritize clarity, reasoning, and thoughtful design over completeness or polish." | [EXPLICIT] | A narrower, well-reasoned, honest solution is preferred over broad coverage or visual polish. This supports a focused MVP and explicitly allows incompleteness when it is acknowledged. |
| **NFR-6** | **AI-powered.** "Build an AI-powered agent" | [EXPLICIT] | AI (presumably an LLM) must play a real role, for example in understanding questions, orchestrating tools, and generating explanations. The design document must say where and how AI is used (D-2c). |

---

## 4. Required Deliverables [EXPLICIT]

| ID | Deliverable | Required content |
|---|---|---|
| **D-1** | **Source code** | The working agent, including the chat interface, data access, and deterministic scoring logic. |
| **D-2** | **Short design/architecture document** (`architecture.md`, NOTES.md D-013) | Must explain: |
| D-2a | | **Scoring methodology:** KPI definitions, inputs, formulas, weights, normalization, and limitations. |
| D-2b | | **Key tradeoffs:** what was chosen, what was rejected, and why (for example, data recency vs. availability, simplicity vs. accuracy, LLM vs. deterministic responsibilities). |
| D-2c | | **Where/how AI is used:** which parts are LLM-driven and which are deterministic, and how hallucination is limited. |

Not specified in the PDF (see OQ-10): run instructions/README, a hosted demo, tests, a demo video, or how to submit. **[ASSUMPTION]:** a README with setup and run steps is the minimum needed for reviewers to evaluate D-1, but the PDF does not require one.

---

## 5. Data and Feasibility Questions

> No data source below has been verified. Candidate sources are listed only as **leads to investigate**. None is claimed to provide the stated data until checked. [TO VERIFY]

### 5.1 Data needed per example question

| Q | Data needed | Concepts that need definitions | Feasibility concerns |
|---|---|---|---|
| **Q1** New England terminal expansion | List of commercial-service airports in CT, ME, MA, NH, RI, VT. Per-airport passenger volume (enplanements) and its trend over time. Flight operations volume and trend. Ideally some capacity or utilization indicator (gates, terminal size, runway capacity). Optionally delay data as a stress signal. | "New England" (the six states, which is standard), the eligible airport set, **"terminal expansion candidate"**, and **"investment attractiveness."** | Terminal capacity (gates, square footage, design passengers per hour) is probably **not** available through a public API in a standard form. The KPI may have to rely on demand and growth proxies instead of true utilization. |
| **Q2** LA vs. Santa Ana congestion | Per-airport operational data: delays (arrival/departure), possibly taxi times, flight counts, and (if available) capacity or throughput benchmarks to compute utilization. | **"LA"** (LAX alone, or LA-area airports?), **"Santa Ana"** (assumed to be John Wayne Airport, SNA [TO VERIFY mapping]), **"congestion"**, and the time window. | Comparing airports of very different sizes needs normalized metrics (rates or ratios, not raw counts). Real-time vs. historical data gives different answers. |
| **Q3** Anchorage long-haul % | List of departing flights or routes from ANC, with origin–destination distance (or block time) per flight. Count of flights over the long-haul threshold. | **"Long haul"** (distance or duration threshold; no single universal standard), **"flights"** (passenger only, or including cargo?), **"out of"** (departures only), the time window, and whether flights are scheduled or operated. | **Material ambiguity:** Anchorage is widely described as a major cargo transit point [TO VERIFY]. Including or excluding cargo flights could change the percentage a lot. Flight-level data with destinations is needed. Some public flight-tracking sources have coverage gaps or rate limits [TO VERIFY]. |
| **Q4** SFO unmet demand and why | Proxies such as delays and cancellations, load factors (if available), traffic growth vs. capacity, schedule or slot constraints, and possibly runway or weather-related capacity constraints. | **"Unmet flight demand"** (no standard measurable definition) and the scope of "why." | **Not directly measurable.** Any number is a modeled proxy estimate and must be labeled as such. The "why" is causal: the agent can only point to *evidence consistent with* causes found in data. It must not state causes from LLM background knowledge as fact. This question is the main hallucination risk. |

### 5.2 Concepts that require our own definitions
Each of these must be written down as a definition that the code applies and the agent cites in its answers:

1. **Congestion:** for example, delay-based (average delay, % on-time), utilization-based (operations ÷ capacity), or a composite. Choice pending.
2. **Long-haul flight:** a distance or duration threshold. There is no single industry-wide standard, so the threshold is our choice and must be stated.
3. **Unmet demand:** a proxy-based indicator, not an observed quantity.
4. **Terminal expansion suitability:** a composite KPI (for example, demand level, demand growth, capacity pressure). Inputs and weights pending.
5. **Investment attractiveness:** how the operational indicators relate to the business goal. This is explicitly *not* a profitability figure (Section 1.3).
6. **Region and airport scope:** which airports are "in" a region (all public-use airports, only commercial-service airports, or only primary airports?).
7. **Time window:** which period the metrics cover (latest month, latest full year, multi-year trend).

### 5.3 Areas where public data is likely insufficient [TO VERIFY]
- **Financial and profitability data:** not expected from aviation data APIs. Out of scope for quantitative claims.
- **Terminal and gate capacity:** may exist in planning documents or PDFs rather than APIs.
- **Unmet demand:** inherently unobservable. Proxies only.
- **Causal explanations ("why"):** data can support or contradict hypotheses but rarely proves causes.
- **Data latency:** some official statistics are published with a reporting lag, so "current" figures may be months old.
- **Access constraints:** free tiers, API keys, rate limits, and coverage gaps could limit what a one-day build can retrieve.

### 5.4 Candidate source categories to investigate (not verified)
- US government aviation statistics (for example, federal transportation statistics and FAA publications on enplanements, operations, on-time performance, and route-level traffic).
- Open flight-tracking or flight-schedule APIs (free or freemium).
- Open airport reference datasets (codes, locations, states, airport type).

For each candidate, check: actual fields available, geographic and time coverage, freshness, access method (API vs. file download), authentication, rate limits, and licensing.

---

## 6. Open Questions and Ambiguities

Ordered roughly by impact on correctness and credibility.

| ID | Question | Why it matters | Impact |
|---|---|---|---|
| **OQ-1** | How do we bridge "most profitable" (business goal) and the measurable operational indicators? *(Resolved: NOTES.md D-010.)* | If we imply profitability we cannot support, the solution loses credibility. If we ignore the goal, it looks off-target. | **High** |
| **OQ-2** | How is "unmet flight demand" defined, and how strong a claim can the agent make about "why"? | No standard definition exists. Overclaiming causes would be fabrication. | **High** |
| **OQ-3** | What KPI and weights define "terminal expansion candidate"? | The core deterministic scoring logic. Weights are subjective and must be justified. Terminal (landside) capacity differs from airside (runway/flight) capacity. | **High** |
| **OQ-4** | How is "congestion" defined? | Different definitions (delays vs. utilization) can produce opposite rankings for LAX vs. SNA. | **High** |
| **OQ-5** | Long-haul threshold, and are cargo flights included? | Directly changes the Q3 number, possibly a lot at Anchorage. | **High** |
| **OQ-6** | Does "LA" mean LAX only or the LA-area airport system? Is "Santa Ana" SNA? | Wrong entity resolution means a wrong answer. The agent could also state its interpretation or ask the user to clarify. | Medium |
| **OQ-7** | Do public downloadable datasets (bulk files) count as "public APIs," or must data be fetched live from a REST API at query time? | Affects data freshness, reliability, demo stability, and how literally FR-1 is met. A hybrid (cached or pre-fetched public data) may be defensible but should be stated. | **High** |
| **OQ-8** | What time window and data freshness do we target (real-time, latest month, annual)? | Changes answers to Q2, Q3, and Q4. Affects which sources are usable. | Medium |
| **OQ-9** | What form should the chat interface take (web UI, CLI, notebook)? | The PDF says only "chat interface." Affects reviewer experience and build time. | Low–Medium |
| **OQ-10** | Submission format: README/run instructions, hosted demo, tests, demo recording? Which LLM provider is acceptable, and are reviewers expected to supply API keys? | Reviewers must be able to run or see the solution. Not specified in the PDF. | Medium |
| **OQ-11** | How should the agent handle questions outside its data or definitions (non-US airports, unsupported metrics)? | Part of "clearly communicate … scoping." Refusing or redirecting gracefully is better than guessing. | Medium |
| **OQ-12** | How general must the agent be beyond the four example questions? | "Questions such as" implies some generalization. Too narrow looks hard-coded; too broad is not feasible in 24 hours. | Medium |
| **OQ-13** | Should voice be attempted? | Explicit bonus only. Competes for time with core requirements. | Low |

---

## 7. MVP Acceptance Checklist

### 7.1 Mandatory (maps to explicit PDF requirements)

| # | Requirement | Acceptance criterion (verifiable) |
|---|---|---|
| M-1 | FR-0 AI-powered agent | A user can type a natural-language question about US airports and get an answer generated through the agent (not a fixed menu only). |
| M-2 | FR-1 Public APIs | Data used in answers comes from at least one public aviation data source accessed programmatically. Each answer (or the docs) names the source(s). The interpretation of "API" is stated (OQ-7). |
| M-3 | FR-2 Rank **or** compare | At least one ranking flow (multiple airports ordered by a defined KPI) **and** one comparison flow (two or more airports on a defined metric) work end to end. |
| M-4 | NFR-1 Deterministic logic | The ranking/comparison scores are computed by code with documented formulas. The same inputs produce the same scores. The LLM does not produce the numeric scores. Verified by running the scoring code directly (for example, a test or script) and matching the agent's reported values. |
| M-5 | FR-3 Clear reasoning | Each ranking/comparison answer shows the metric definition, input values, and how the result follows from them. |
| M-6 | FR-4 Follow-ups | In one session, a follow-up that depends on the previous answer (for example, "why is X ranked first?" or "what about Y instead?") is answered correctly without restating context. |
| M-7 | NFR-2 Chat interface | A reviewer can start the system and have a multi-turn text conversation with the agent. |
| M-8 | NFR-3 Assumptions, uncertainty, scope | Answers state the definitions used (for example, the long-haul threshold), the data period/source, and confidence or limitations where relevant. Questions out of scope or without data get an explicit "can't answer / here's why," not a fabricated answer. |
| M-9 | Q1–Q4 handled | Each of the four example questions gets a response that **either** answers from data using documented definitions **or** explains clearly which parts cannot be answered with available public data, and offers the closest supportable proxy. *Feasibility of exact answers for each question is pending investigation (Section 5). Exact real-world figures are **not** assumed to be achievable for all four.* |
| M-10 | No fabricated numbers | Every numeric value in an answer comes from retrieved data or deterministic computation. None is generated by the LLM from its own knowledge. Verifiable by tracing numbers to tool/data outputs. |
| M-11 | D-1 Source code | The code is in the repository and runs from documented steps. |
| M-12 | D-2a Scoring methodology | The design document defines each KPI with inputs, formula, weights/normalization, and limitations. |
| M-13 | D-2b Key tradeoffs | The design document lists the main tradeoffs and the reasoning behind each. |
| M-14 | D-2c AI usage | The design document states which components use AI, which are deterministic, and how hallucination risk is controlled. |
| M-15 | NFR-4/5 Scope fit | Delivered within about 24 hours. Unimplemented items are listed explicitly as known gaps or future work. |

### 7.2 Optional enhancements (not required by the PDF)

| # | Enhancement | Source |
|---|---|---|
| O-1 | Voice input/output | [EXPLICIT bonus] |
| O-2 | Clarifying questions for ambiguous entities (for example, "Did you mean LAX or all LA-area airports?") | [OPTIONAL], supports NFR-3 |
| O-3 | User-adjustable KPI weights or thresholds via chat (for example, "use 4,000 miles for long haul") | [OPTIONAL], supports FR-4 |
| O-4 | Citations or links to raw source records in answers | [OPTIONAL], supports FR-3 |
| O-5 | Automated tests for scoring logic | [OPTIONAL], strengthens M-4 evidence |
| O-6 | Hosted demo | [OPTIONAL] |
| O-7 | Charts or tables in the chat UI | [OPTIONAL], explicitly lower priority than clarity ("over … polish") |

---

## 8. Risks and Priorities

### 8.1 Top risks

| # | Risk | Likelihood | Impact | Mitigation direction (no stack chosen) |
|---|---|---|---|---|
| R-1 | **Public data does not support one or more example questions** (especially Q1 terminal capacity and Q4 unmet demand). | High | High | Check data early. Define proxies. Answer honestly with limitations (M-9). |
| R-2 | **LLM fabricates numbers or causes**, especially for Q4 "why" and for well-known airports where the model has background knowledge. | High | High | Keep numeric answers tied to tool/computed outputs (M-10). Require grounding. Label inferences. |
| R-3 | **API access friction**: keys, sign-up delays, rate limits, paywalls, downtime during review. | Medium | High | Identify access requirements in the first hours. Consider caching or a pre-fetched snapshot (subject to OQ-7). |
| R-4 | **Definitional disputes**: reviewers disagree with our definitions of congestion, long haul, or unmet demand. | Medium | Medium | Make definitions explicit, justified, and ideally adjustable. NFR-5 rewards reasoning over the "right" answer. |
| R-5 | **Scope creep / time overrun**: trying to fully generalize, add voice, or polish the UI. | Medium | High | Build to the mandatory checklist first. Add optional items only afterward. |
| R-6 | **Overstating the business claim** ("most profitable") without financial data. | Medium | High | Frame outputs as investment *indicators* (Section 1.3). |
| R-7 | **Entity resolution errors** ("LA", "Santa Ana", region → airports). | Medium | Medium | Deterministic mapping for supported regions/airports. State interpretations in answers. |
| R-8 | **Reviewer cannot run the solution** (missing keys, environment issues). | Medium | High | Clear run instructions. Minimize external setup (relates to OQ-10). |
| R-9 | **Data freshness mismatch**: lagged official statistics vs. "current" questions. | Medium | Low–Medium | State the data period in every answer. |

### 8.2 Proposed investigation order
Architecture and stack are intentionally **not** selected here.

1. **Data source discovery and verification (highest priority, time-boxed).** For each of Q1–Q4, find candidate public sources and confirm with real requests or downloads what fields, coverage, freshness, and access constraints they actually have. Output: a feasibility matrix (question × source × available fields × gaps).
2. **Resolve the high-impact ambiguities (OQ-1 to OQ-7)** using the verified data. Write precise metric definitions (congestion, long haul, unmet-demand proxy, expansion score) that the available data can actually compute.
3. **Decide the "public API" interpretation (OQ-7) and the data freshness target (OQ-8).** This determines data access approach and reliability.
4. **Draft the scoring methodology** (inputs, normalization, weights, limitations) as the core deterministic logic. Keep it in a form that can go into D-2a.
5. **Decide the AI vs. deterministic division of responsibilities** (what the LLM may and may not do) to address R-2.
6. **Only then select the architecture and technology stack**, including the chat interface form (OQ-9) and the LLM provider (OQ-10).
7. Implement the mandatory checklist (Section 7.1), then optional items if time remains.
