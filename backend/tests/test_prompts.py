"""System-prompt guards (offline): concise default answers, no forced response language."""

import re

from app.agent.prompts import SYSTEM_PROMPT


def test_default_answer_is_a_short_summary_not_a_copy_of_the_evidence():
    assert "60-100 words" in SYSTEM_PROMPT and "Up to 130 words only for a ranking or a comparison" in SYSTEM_PROMPT
    assert "do not reproduce it" in SYSTEM_PROMPT and "2-4 most decision-relevant metrics" in SYSTEM_PROMPT
    assert "No headings" in SYSTEM_PROMPT and "no closing offers" in SYSTEM_PROMPT
    assert "Never drop a material warning" in SYSTEM_PROMPT


def test_prompt_uses_display_values_and_forbids_raw_fractions():
    assert "Quote them exactly as given" in SYSTEM_PROMPT and "never show raw fractions" in SYSTEM_PROMPT
    assert "Quote values as the tools return them" not in SYSTEM_PROMPT  # the instruction that caused 0.8418


def test_prompt_does_not_force_a_response_language():
    # Hebrew questions should still get Hebrew answers: no instruction pins English (or any language).
    assert not re.search(r"\b(answer|respond|reply|write)\b[^.]*\bin (English|Hebrew)\b", SYSTEM_PROMPT, re.I)


def test_grounding_and_warning_rules_remain():
    for phrase in ("Never invent", "Never hide or contradict a warning", "Unmet demand is not measured",
                   "not a verified investment opportunity"):
        assert phrase in SYSTEM_PROMPT
