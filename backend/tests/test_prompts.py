"""System-prompt guards (offline): concise default answers, no forced response language."""

import re

from app.agent.prompts import SYSTEM_PROMPT


def test_default_answer_is_a_short_executive_summary():
    assert "3-5 sentences" in SYSTEM_PROMPT
    assert "Do not repeat the evidence tables" in SYSTEM_PROMPT


def test_prompt_does_not_force_a_response_language():
    # Hebrew questions should still get Hebrew answers: no instruction pins English (or any language).
    assert not re.search(r"\b(answer|respond|reply|write)\b[^.]*\bin (English|Hebrew)\b", SYSTEM_PROMPT, re.I)


def test_grounding_and_warning_rules_remain():
    for phrase in ("Never invent", "Never hide or contradict a warning", "Unmet demand is not measured",
                   "not a verified investment opportunity"):
        assert phrase in SYSTEM_PROMPT
