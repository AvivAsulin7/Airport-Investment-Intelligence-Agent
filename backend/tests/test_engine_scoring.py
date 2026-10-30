"""Scoring v1 tests, including the architecture.md §9 worked examples (fictional data)."""

import pytest

from app.engine.scoring import ScoringInputError, rank_airports, validate_weights

# §9 Example 1 input: D has no on-time KPIs; A is flagged low-sample upstream.
EXAMPLE = {
    "A": {"passenger_growth": 0.08, "load_factor": 0.84, "departure_growth": 0.03, "delay_rate": 0.22, "avg_taxi_out_min": 15},
    "B": {"passenger_growth": 0.02, "load_factor": 0.88, "departure_growth": 0.01, "delay_rate": 0.30, "avg_taxi_out_min": 20},
    "C": {"passenger_growth": 0.12, "load_factor": 0.76, "departure_growth": 0.06, "delay_rate": 0.18, "avg_taxi_out_min": 12},
    "D": {"passenger_growth": 0.07, "load_factor": 0.82, "departure_growth": 0.035, "delay_rate": None, "avg_taxi_out_min": None},
}
GROWTH_WEIGHTS = {"passenger_growth": 0.5, "departure_growth": 0.2, "load_factor": 0.2, "delay_rate": 0.1, "avg_taxi_out_min": 0}


def _by(result):
    return {s.airport: s for s in result.airports}


def test_example_1_default_weights():
    r = rank_airports(EXAMPLE, flags={"A": ["low_sample: 240 departed flights < 300"]})

    s = _by(r)
    assert r.status == "ranked"
    assert [x.airport for x in r.airports] == ["B", "A", "D", "C"]
    assert s["B"].score == pytest.approx(55.0)
    assert s["A"].score == pytest.approx(51.0833, abs=1e-3)
    assert s["D"].score == pytest.approx(50.0) and s["D"].coverage == pytest.approx(0.70)
    assert s["C"].score == pytest.approx(45.0)
    assert any(f.startswith("partial") for f in s["D"].flags)
    assert any(f.startswith("low_sample") for f in s["A"].flags)
    assert s["A"].kpis["load_factor"].normalized == pytest.approx(66.667, abs=1e-3)
    ranges = {k.metric: (k.low, k.high) for k in r.ranges}
    assert ranges["passenger_growth"] == (0.02, 0.12) and ranges["delay_rate"] == (0.18, 0.30)
    assert "relative" in r.interpretation and "not profitability" in r.interpretation


def test_example_2_growth_weights_change_the_ranking():
    previous = {"B": 1, "A": 2, "D": 3, "C": 4}
    r = rank_airports(EXAMPLE, GROWTH_WEIGHTS, previous_ranks=previous)

    s = _by(r)
    assert [x.airport for x in r.airports] == ["C", "A", "D", "B"]
    assert s["C"].score == pytest.approx(70.0)
    assert s["A"].score == pytest.approx(54.6667, abs=1e-3)
    assert s["D"].score == pytest.approx(50.0) and s["D"].coverage == pytest.approx(0.90)
    assert s["B"].score == pytest.approx(30.0)
    assert r.rank_changes == {"C": 3, "A": 0, "D": 0, "B": -3}
    assert "avg_taxi_out_min" not in r.weights_used  # zero weight is excluded


def test_contributions_sum_to_score():
    for s in rank_airports(EXAMPLE).airports:
        assert sum(c.contribution for c in s.kpis.values() if c.contribution is not None) == pytest.approx(s.score)


def test_equal_values_normalize_to_50():
    vals = {a: {"passenger_growth": 0.05, "load_factor": lf} for a, lf in [("A", 0.8), ("B", 0.9), ("C", 0.7)]}
    r = rank_airports(vals, {"passenger_growth": 1, "load_factor": 1})

    assert all(s.kpis["passenger_growth"].normalized == 50.0 for s in r.airports)
    assert any("all values equal" in w for w in r.warnings)


def test_kpi_with_fewer_than_three_values_is_dropped_and_weights_rescaled():
    vals = {a: {"passenger_growth": g, "delay_rate": d} for a, g, d in
            [("A", 0.1, 0.2), ("B", 0.2, 0.3), ("C", 0.3, None), ("D", 0.4, None)]}
    r = rank_airports(vals, {"passenger_growth": 0.5, "delay_rate": 0.5})

    assert r.weights_used == {"passenger_growth": 1.0}
    assert any("delay_rate dropped" in w for w in r.warnings)
    assert all(s.coverage == pytest.approx(1.0) for s in r.airports)


def test_coverage_below_60_percent_is_listed_not_scored():
    vals = dict(EXAMPLE)
    vals["E"] = {"passenger_growth": None, "load_factor": 0.8, "departure_growth": None, "delay_rate": 0.2, "avg_taxi_out_min": None}
    r = rank_airports(vals)

    e = _by(r)["E"]
    assert e.status == "insufficient_data" and e.score is None and e.rank is None
    assert e.coverage == pytest.approx(0.45)
    assert e.kpis["load_factor"].raw == 0.8  # raw values still shown
    assert r.airports[-1].airport == "E"


def test_fewer_than_three_airports_returns_unranked_values():
    r = rank_airports({"A": EXAMPLE["A"], "B": EXAMPLE["B"]})

    assert r.status == "not_ranked" and "3" in r.reason
    assert all(s.rank is None and s.score is None for s in r.airports)


def test_kpi_with_two_values_is_dropped_before_coverage_is_computed():
    # Only A and B have growth -> KPI dropped -> load factor alone -> everyone has full coverage.
    vals = {a: {"passenger_growth": g, "load_factor": lf} for a, g, lf in
            [("A", 0.1, 0.8), ("B", 0.2, 0.9), ("C", None, 0.7), ("D", None, 0.6)]}
    r = rank_airports(vals, {"passenger_growth": 0.9, "load_factor": 0.1})

    assert r.status == "ranked" and r.weights_used == {"load_factor": 1.0}


def test_fewer_than_three_ranked_after_coverage_is_not_ranked():
    # Every KPI has >= 3 values, but only A and B reach 60% coverage.
    vals = {
        "A": {"passenger_growth": 0.1, "departure_growth": 0.1, "load_factor": 0.8},
        "B": {"passenger_growth": 0.2, "departure_growth": 0.2, "load_factor": 0.9},
        "C": {"passenger_growth": 0.3, "departure_growth": None, "load_factor": 0.7},
        "D": {"passenger_growth": None, "departure_growth": 0.3, "load_factor": 0.6},
    }
    r = rank_airports(vals, {"passenger_growth": 0.45, "departure_growth": 0.45, "load_factor": 0.1})

    assert {s.airport: round(s.coverage, 2) for s in r.airports} == {"A": 1.0, "B": 1.0, "C": 0.55, "D": 0.55}
    assert r.status == "not_ranked" and "coverage" in r.reason


def test_no_usable_kpi_is_not_ranked():
    vals = {a: {"passenger_growth": None} for a in "ABC"}
    r = rank_airports(vals, {"passenger_growth": 1})
    assert r.status == "not_ranked" and "no KPI" in r.reason


def test_ties_break_by_passengers_then_code():
    vals = {a: {"passenger_growth": g} for a, g in [("X", 0.1), ("Y", 0.1), ("Z", 0.0), ("W", 0.1)]}
    r = rank_airports(vals, {"passenger_growth": 1}, tiebreak={"X": 100, "Y": 500, "W": 100, "Z": 1})

    assert [s.airport for s in r.airports] == ["Y", "W", "X", "Z"]
    assert any("tied" in f for f in _by(r)["W"].flags)


def test_negative_growth_is_normalized_naturally():
    vals = {a: {"passenger_growth": g} for a, g in [("A", -0.034), ("B", 0.0), ("C", 0.066)]}
    s = _by(rank_airports(vals, {"passenger_growth": 1}))

    assert s["A"].kpis["passenger_growth"].normalized == 0.0 and s["A"].kpis["passenger_growth"].raw == -0.034
    assert s["B"].kpis["passenger_growth"].normalized == pytest.approx(34.0)


def test_passenger_volume_uses_log10():
    vals = {a: {"passengers_t12m": p} for a, p in [("A", 1_000), ("B", 100_000), ("C", 10_000_000)]}
    s = _by(rank_airports(vals, {"passengers_t12m": 1}))
    assert s["B"].kpis["passengers_t12m"].normalized == pytest.approx(50.0)


@pytest.mark.parametrize("weights", [{"passenger_growth": 0}, {"passenger_growth": -1}, {"made_up": 1},
                                     {"passenger_growth": float("nan")}, {}])
def test_invalid_weights_are_rejected(weights):
    with pytest.raises(ScoringInputError):
        validate_weights(weights)


def test_weights_are_normalized_and_echoed():
    assert validate_weights({"passenger_growth": 3, "load_factor": 1}) == {"passenger_growth": 0.75, "load_factor": 0.25}
