import pytest

from app.data.operations import ArrivalCauses
from app.data.routes import RouteSegment
from app.data.validation import DataValidationError
from app.engine.analyses import compare, delay_cause_shares, demand_profile, long_haul_share, peer_position
from app.engine.kpis import MetricValue


def _seg(cls, dist, dep):
    return RouteSegment("XXX", "YYY", "US", cls, dist, dep, dep, 0, 0, 0)


# architecture.md §9 Example 3 (fictional airport X)
SEGMENTS = [
    _seg("F", 1000, 900), _seg("F", 3500, 100),
    _seg("L", 1200, 50),
    _seg("G", 1500, 500), _seg("G", 4000, 300),
    _seg("P", 2000, 50), _seg("P", 5000, 150),
]


def test_long_haul_example_passenger_and_all_classes():
    r = long_haul_share("XXX", SEGMENTS)

    assert (r.primary.numerator, r.primary.denominator) == (100, 1050)
    assert r.primary.share == pytest.approx(100 / 1050)  # 9.5%
    assert r.all_classes.share == pytest.approx(550 / 2050)  # 26.8%
    assert r.primary.service_classes == ["F", "L"]
    assert r.by_class["G"] == {"departures": 800, "long_haul_departures": 300}
    assert "statute miles" in r.definition


def test_threshold_boundary_is_inclusive():
    segs = [_seg("F", 2999, 10), _seg("F", 3000, 10)]
    assert long_haul_share("XXX", segs, 3000).primary.numerator == 10
    assert long_haul_share("XXX", segs, 2999).primary.numerator == 20


def test_cargo_only_selection_and_validation():
    assert long_haul_share("XXX", SEGMENTS, 3000, ["G", "P"]).primary.share == pytest.approx(450 / 1000)
    for bad in (499, 10_001, 3000.5):
        with pytest.raises(DataValidationError):
            long_haul_share("XXX", SEGMENTS, bad)
    with pytest.raises(DataValidationError):
        long_haul_share("XXX", SEGMENTS, 3000, [])


def test_long_haul_zero_denominator():
    r = long_haul_share("XXX", [_seg("G", 4000, 5)], 3000, ["F", "L"])
    assert r.primary.share is None and r.primary.missing_reason


def test_comparison_differences_vs_first_airport():
    per = {
        "P": {"delay_rate": MetricValue("delay_rate", 0.25, 2450, 9800)},
        "Q": {"delay_rate": MetricValue("delay_rate", 0.25, 495, 1980)},
        "R": {"delay_rate": MetricValue("delay_rate", None, missing_reason="no data")},
    }
    r = compare(per, ["P", "Q", "R"], ["delay_rate"])

    assert r.baseline == "P"
    assert r.differences["delay_rate"]["Q"] == {"absolute": 0.0, "relative": 0.0}
    assert r.differences["delay_rate"]["R"] == {"absolute": None, "relative": None}
    assert r.values["delay_rate"]["P"]["numerator"] == 2450


def test_peer_position_needs_three_peers():
    assert peer_position(0.5, [0.1, 0.9]).percentile is None
    p = peer_position(0.5, [0.1, 0.3, 0.9, None])
    assert p.percentile == pytest.approx(200 / 3) and p.rank_desc == 2 and p.peers_with_data == 3


def test_delay_cause_shares_sorted_and_empty():
    arr = ArrivalCauses("SSS", 100, 2, 30, 100.0, 10.0, 300.0, 0.0, 90.0)
    rows = delay_cause_shares(arr)

    assert rows[0]["cause"] == "national_airspace_system" and rows[0]["share"] == pytest.approx(0.6)
    assert sum(r["share"] for r in rows) == pytest.approx(1.0)
    assert delay_cause_shares(ArrivalCauses("SSS", 1, 0, 0, 0, 0, 0, 0, 0)) is None
    assert delay_cause_shares(None) is None


def test_demand_profile_never_measures_unmet_demand():
    def kp(v):
        return {m: MetricValue(m, v) for m in ("passengers_t12m", "passenger_growth", "departures_t12m",
                                                  "departure_growth", "load_factor", "delay_rate",
                                                  "avg_taxi_out_min", "cancellation_rate")}

    peers = {"A": kp(0.1), "B": kp(0.2), "C": kp(0.3)}
    p = demand_profile("SSS", "hub L", kp(0.25), peers, None, MetricValue("passengers_2019", 0.2))

    assert p.unmet_demand["measured"] is False and "not measured" in p.unmet_demand["statement"]
    assert p.capacity_pressure["delay_rate"].percentile == pytest.approx(200 / 3)
    assert p.observed_demand["passengers_2019"]["t12m_vs_2019"] == pytest.approx(0.25)
    assert p.delay_causes is None
