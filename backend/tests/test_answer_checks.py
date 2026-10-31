"""Offline tests for the prose checks used by the paid real-model tests."""

from .answer_checks import (
    ORDINARY_WORDS,
    format_problems,
    has_table,
    hebrew_share,
    is_concise,
    is_mainly_hebrew,
    ungrounded_numbers,
)

# A real browser reply under the earlier prompt (Florida ranking, abridged): sections, bullets, raw values.
VERBOSE = """**Short answer:** No Florida airport stands out.

- **Best-supported leads:** SFB (50.91) has a load factor of 0.8418 and MCO a delay rate of 0.3281.
- **Ranked higher, but weaker evidence:** VRB rests on only 81 departures.

I can re-run the ranking with different weights."""

SUMMARY = ("Boston Logan (BOS) ranks first among New England airports on the composite indicator, "
           "driven by passenger growth and a high load factor. Bradley (BDL) is second. "
           "Several smaller airports carry low-sample warnings, so treat their scores with caution. "
           "Data covers 2025-08..2026-07 traffic and July 2026 operations.")


def test_short_summary_is_concise():
    assert is_concise(SUMMARY)


def test_empty_long_or_tabular_reply_is_not_concise():
    assert not is_concise("")
    assert not is_concise(" ".join(["word"] * 200))
    table = SUMMARY + "\n\n| Airport | Score |\n|---|---|\n| BOS | 70 |"
    assert has_table(table) and not is_concise(table)


def test_verbose_sectioned_reply_with_raw_fractions_breaks_every_format_rule():
    problems = format_problems(VERBOSE)
    assert "heading or bold section label" in problems and "bullet list" in problems
    assert "closing offer of further analysis" in problems
    assert any(p.startswith("raw fraction ['0.8418', '0.3281']") for p in problems)


def test_ordinary_answers_have_a_lower_word_limit_than_rankings():
    ninety, one_twenty = " ".join(["word"] * 90), " ".join(["word"] * 120)
    assert is_concise(ninety, ORDINARY_WORDS) and not is_concise(one_twenty, ORDINARY_WORDS)
    assert is_concise(one_twenty)  # within the 130-word ranking/comparison limit


def test_percentages_weights_and_a_single_bullet_are_not_flagged():
    assert format_problems("Load factor is 84.2%, growth 0.6%, weight 0.25.\n\n- One note only.") == []


def test_hebrew_reply_with_airport_codes_counts_as_hebrew():
    reply = "כ-38% מהטיסות היוצאות מ-ANC הן טיסות ארוכות (מעל 3,000 מייל), לפי נתוני יולי 2026."
    assert is_mainly_hebrew(reply)


ARTIFACT = {"data": {"share": 0.2604513926, "departures": 267187.0, "passengers": 36012345.0, "rank": 5},
            "windows": {"traffic": "2025-08..2026-07"}, "definitions": {"threshold": "3,000 statute miles"}}


def test_numbers_traceable_to_evidence_are_grounded():
    reply = ("LAX ranks 5, with 26.0% (26.045%) of delay minutes from late aircraft, about 267,000 departures "
             "and 36.0M passengers over 2025-08..2026-07, using a 3,000-mile threshold.")
    assert ungrounded_numbers(reply, [ARTIFACT]) == []
    assert ungrounded_numbers("Passengers are 4.98% below 2019.", [{"vs_2019": -0.0498, "window": "2019"}]) == []


def test_misrounded_or_invented_numbers_are_flagged():
    assert ungrounded_numbers("Late aircraft caused 26.1% of delay minutes.", [ARTIFACT]) == ["26.1"]
    assert ungrounded_numbers("About 270,000 departures, 41% growth.", [ARTIFACT]) == ["41"]


def test_english_or_mixed_reply_is_not_hebrew():
    assert not is_mainly_hebrew(SUMMARY)
    assert not is_mainly_hebrew("שלום. " + SUMMARY)
    assert hebrew_share("") == 0.0
