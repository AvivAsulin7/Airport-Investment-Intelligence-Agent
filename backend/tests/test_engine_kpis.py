import pytest

from app.data.bts_api import MonthlyTraffic
from app.data.operations import DepartureCounts
from app.data.validation import month_range
from app.engine.kpis import operational_kpis, traffic_kpis, traffic_windows

W = traffic_windows("2026-07")


def _rows(prior_pax=100.0, cur_pax=110.0, seats=200.0, prior_dep=10.0, cur_dep=12.0, skip=()):
    rows = []
    for m in month_range("2024-08", "2026-07"):
        if m in skip:
            continue
        cur = m >= "2025-08"
        rows.append(MonthlyTraffic("AAA", m, cur_pax if cur else prior_pax, seats, cur_dep if cur else prior_dep, None, None, None))
    return rows


def test_windows_are_trailing_12_and_prior_12():
    assert W.current_label == "2025-08..2026-07"
    assert W.prior_label == "2024-08..2025-07"


def test_traffic_kpi_formulas():
    k = traffic_kpis(_rows(), W)

    assert k["passenger_growth"].value == pytest.approx(1320 / 1200 - 1)
    assert (k["passenger_growth"].numerator, k["passenger_growth"].denominator) == (1320, 1200)
    assert k["departure_growth"].value == pytest.approx(144 / 120 - 1)
    assert k["load_factor"].value == pytest.approx(1320 / 2400)
    assert k["passengers_t12m"].value == 1320


def test_negative_growth_keeps_sign():
    k = traffic_kpis(_rows(prior_pax=100.0, cur_pax=90.0), W)
    assert k["passenger_growth"].value == pytest.approx(-0.10)


def test_missing_month_makes_growth_null_with_reason():
    k = traffic_kpis(_rows(skip=("2025-01",)), W)

    assert k["passenger_growth"].value is None
    assert "2025-01" in k["passenger_growth"].missing_reason
    assert k["load_factor"].value is not None  # current window is complete


def test_zero_prior_traffic_and_zero_seats():
    k = traffic_kpis(_rows(prior_pax=0.0, seats=0.0), W)

    assert k["passenger_growth"].value is None and k["passenger_growth"].missing_reason == "no traffic in the prior window"
    assert k["load_factor"].value is None and k["load_factor"].missing_reason == "no seats reported"


def _counts(rows=1000, cancelled=20, eligible=980, delayed=245, taxi_n=980, taxi_sum=17640.0):
    return DepartureCounts("AAA", rows, cancelled, 5, eligible, delayed, taxi_n, taxi_sum, eligible, 9800.0)


def test_operational_kpi_formulas():
    k = operational_kpis(_counts(), "2026-07")

    assert k["delay_rate"].value == pytest.approx(245 / 980)
    assert (k["delay_rate"].numerator, k["delay_rate"].denominator) == (245, 980)
    assert k["cancellation_rate"].value == pytest.approx(20 / 1000)
    assert k["avg_taxi_out_min"].value == pytest.approx(18.0)
    assert not k["delay_rate"].flags


def test_low_sample_is_a_warning_not_an_exclusion():
    below = operational_kpis(_counts(eligible=299, delayed=60, taxi_n=299), "2026-07")
    at = operational_kpis(_counts(eligible=300, delayed=60, taxi_n=300), "2026-07")

    assert below["delay_rate"].value == pytest.approx(60 / 299)
    assert any(f.startswith("low_sample") for f in below["delay_rate"].flags)
    assert not at["delay_rate"].flags
    assert operational_kpis(_counts(eligible=100, taxi_n=100), "2026-07", min_flights_warning=50)["delay_rate"].flags == []


def test_zero_denominators_and_missing_airport():
    k = operational_kpis(_counts(rows=0, cancelled=0, eligible=0, delayed=0, taxi_n=0, taxi_sum=0.0), "2026-07")
    assert k["delay_rate"].value is None and k["delay_rate"].missing_reason == "no eligible departures"
    assert k["cancellation_rate"].value is None

    missing = operational_kpis(None, "2026-07")
    assert all(v.value is None and "reporting carriers" in v.missing_reason for v in missing.values())
