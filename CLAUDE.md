# CLAUDE.md: Project Working Instructions

Project: **Airport Investment Intelligence Agent**, a 24-hour take-home assignment for the Deloitte Digital Forward Deployed Engineer position.

Key files:
- `FDE Exam 2.pdf`: the original assignment. **Single source of truth for requirements.**
- `requirements.md`: requirements analysis (explicit requirements, interpretations, open questions, acceptance checklist, risks).
- `NOTES.md`: decision log (decisions made, open decisions, assumptions to verify, rejected alternatives).
- `implementation-plan.md`: phase roadmap (9 phases, statuses, and the 24-hour budget).

Note: `FDE Exam 2.pdf` is kept local only. It is excluded via `.gitignore` and must not be committed.

## 1. Source of truth and labelling
- The PDF is the source of truth. If `requirements.md`, `NOTES.md`, or anything else conflicts with the PDF, the PDF wins. Flag the conflict instead of resolving it silently.
- Always label claims as one of: **explicit requirement**, **interpretation**, **assumption**, **optional feature**, or **unverified claim**. Use the labels defined in `requirements.md`.
- Do not add requirements that are not in the PDF without labelling them as interpretations or optional features.

## 2. Phased, approval-gated workflow
- Work incrementally, one approved phase at a time.
- **Do not start the next phase without explicit user approval.**
- Do not silently choose the **architecture, technology stack, data sources, scoring formulas, or AI framework**. Propose them and wait for approval.
- Before implementing a major decision, explain it: the options considered, the tradeoffs, the recommendation, and the reasoning.
- At the end of each phase, summarize:
  1. the work completed,
  2. outstanding risks,
  3. decisions that need user approval.

## 3. Scope and priorities
- Prioritize a credible, working MVP within the assignment's timeframe of about 24 hours.
- The PDF says to prioritize "clarity, reasoning, and thoughtful design over completeness or polish". Follow it.
- Keep the four example questions as key capability checks:
  1. "Which airports in New England are strong candidates for terminal expansion?"
  2. "Compare LA and Santa Ana airport congestion levels."
  3. "What is the percentage of long haul flights out of Anchorage airport?"
  4. "What is the unmet flight demand in SFO airport and why?"
- **Do not claim** that all example questions can be answered accurately until data feasibility has been verified.

## 4. Data integrity (non-negotiable)
- Never invent aviation data, API responses, API capabilities, metrics, or investment profitability figures.
- Do not state that an API or dataset provides a field until it has been verified with a real request or documentation. Until then, label it unverified.
- Every number shown to a user must come from retrieved data or deterministic computation, never from LLM background knowledge.

## 5. Deterministic logic vs. AI
- Keep deterministic scoring and ranking separate from LLM-generated explanations.
- The LLM may interpret questions, orchestrate tools, and explain results. It must not produce scores, rankings, or metric values itself.
- Make scoring logic inspectable and reproducible: same inputs, same outputs.

## 6. Communicating uncertainty
- Agent outputs and documentation must state the following clearly:
  - assumptions and metric definitions (for example, the long-haul threshold or how congestion is defined),
  - uncertainty and the limits of proxies (for example, that "unmet demand" is an estimate),
  - data source and freshness (which period the data covers),
  - scope limitations (what the agent cannot answer, and why).
- Frame outputs as investment **indicators**, not profitability claims, unless the user approves a different framing.

## 7. Engineering practices
- Keep the implementation simple, modular, testable, and easy to demonstrate.
- Avoid unnecessary dependencies, abstractions, and premature optimization.
- After each implementation phase, run the relevant checks (tests, lint, a manual run of the example questions where applicable) and report the results honestly, including failures.

## 8. Security
- Never commit credentials, API keys, or secrets. Use environment variables or a local file that git ignores, and provide an example template with placeholders only.
- Check staged changes for secrets before any commit.

## 9. Decision logging
- Record important technical decisions and rejected alternatives in `NOTES.md`, including the date and the reason.
- When an assumption is verified or disproved, update `NOTES.md` and, if relevant, `requirements.md`.
