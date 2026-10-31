"""Paid real-model checks beyond Q1-Q4 (Phase 9). Opt-in: RUN_LLM_TESTS=1.

A Hebrew question (reply language follows the user) and one novel supported question (a region that
is not one of the PDF examples). Shares the harness and usage counter with test_live_agent.py.
"""

import uuid

from .answer_checks import MAX_WORDS, ORDINARY_WORDS, is_mainly_hebrew
from .test_live_agent import USAGE, _ask, agent, answer_problems, pytestmark  # noqa: F401 (fixture + gating)


def test_hebrew_long_haul_question(agent):  # noqa: F811
    t = _ask(agent, "מה אחוז הטיסות הארוכות (long haul) שיוצאות משדה התעופה של אנקורג'?", str(uuid.uuid4()))
    lh = [e for e in t["evidence"] if e["artifact"] and e["artifact"]["result_type"] == "long_haul"]
    assert lh and lh[-1]["artifact"]["data"]["origin"] == "ANC"
    assert is_mainly_hebrew(t["reply"])
    assert answer_problems(t, ORDINARY_WORDS) == []


def test_novel_florida_ranking(agent):  # noqa: F811
    t = _ask(agent, "Which Florida airports look like the strongest candidates for terminal expansion?",
             str(uuid.uuid4()))
    ranks = [e for e in t["evidence"] if e["artifact"] and e["artifact"]["result_type"] == "ranking"]
    assert ranks and not t["incomplete"]
    assert "FL" in ranks[-1]["artifact"]["data"]["candidate_group"]["interpretation"]
    assert answer_problems(t, MAX_WORDS) == []
    print(f"\nTOTAL USAGE (all paid modules so far) {USAGE}; est. cost at $2/$10 per MTok: "
          f"${USAGE['input'] * 2e-6 + USAGE['output'] * 1e-5:.3f}")
