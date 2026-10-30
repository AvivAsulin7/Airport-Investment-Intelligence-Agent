"""AnalyticsService envelope tests with a fake data layer (offline, no network, no LLM)."""

import json

import pytest

from app.data.airports import Airport, Resolution
from app.data.bts_api import MonthlyTraffic, TrafficSeries
from app.data.layer import DataLayer
from app.data.operations import DepartureCounts, OperationsResult
from app.data.provenance import Provenance
from app.data.validation import DataValidationError, month_range
from app.engine.service import AnalyticsService

API = Provenance("public_api", "fake api", "u", "SODA", "t", "2024-08..2026-07", cache_status="live")
SNAP = Provenance("public_dataset_snapshot", "fake snapshot", "u", "file", "t", "2026-07", cache_status="snapshot")

# airport -> (hub, growth, load factor, eligible departures, delayed)
FIXTURE = {
    "AAA": ("L", 0.02, 0.85, 9000, 2500),
    "BBB": ("M", 0.05, 0.80, 4000, 900),
    "CCC": ("S", 0.08, 0.75, 1200, 300),
    "DDD": ("N", 0.15, 0.70, 40, 15),  # small sample
}


class FakeTraffic:
    def latest_month(self):
        return "2026-07"

    def fetch_monthly_traffic(self, airports, start, end):
        rows = []
        for a in airports:
            _, g, lf, *_ = FIXTURE[a]
            for m in month_range(start, end):
                pax = 1000 * (1 + g) if m >= "2025-08" else 1000.0
                rows.append(MonthlyTraffic(a, m, pax, pax / lf, 10.0 * (1 + g if m >= "2025-08" else 1), None, None, None))
        return TrafficSeries(rows, month_range(start, end), {}, API)


class FakeOps:
    def get(self, airports):
        dep = {a: DepartureCounts(a, FIXTURE[a][3] + 10, 10, 0, FIXTURE[a][3], FIXTURE[a][4],
                                  FIXTURE[a][3], 15.0 * FIXTURE[a][3], FIXTURE[a][3], 0.0) for a in airports}
        return OperationsResult(dep, {a: None for a in airports}, "2026-07", SNAP)


class FakeAirports:
    provenance = SNAP

    def _ap(self, code):
        return Airport(code, code, code, "ZZ", "XX", "P", FIXTURE[code][0], 1000, 900)

    def resolve_region(self, query, primary_only=True):
        return Resolution([self._ap(c) for c in FIXTURE], "fake region")

    def require(self, codes):
        return [self._ap(c) for c in codes]

    def with_hub(self, hub):
        return [self._ap(c) for c in FIXTURE if FIXTURE[c][0] == hub]


@pytest.fixture
def svc():
    return AnalyticsService(DataLayer(FakeTraffic(), FakeAirports(), FakeOps(), None, None))


def test_small_sample_warning_survives_at_every_level(svc):
    r = svc.rank(region="anything")
    serialized = json.loads(json.dumps(r))  # exactly what a tool artifact will carry

    d = serialized["data"]
    assert d["small_sample_airports"] == [{
        "airport": "DDD", "eligible_departures": 40, "threshold": 300, "period": "2026-07",
        "affected_metrics": ["delay_rate", "cancellation_rate", "avg_taxi_out_min", "avg_dep_delay_min"],
    }]
    assert any(w.startswith("Small sample: DDD has 40 eligible departures") for w in serialized["warnings"])
    ddd = next(s for s in d["airports"] if s["airport"] == "DDD")
    assert ddd["status"] == "ranked"  # warned, not excluded (D-029, D-049)
    assert any(f.startswith("low_sample") for f in ddd["flags"])


def test_interpretation_separates_relative_score_from_verified_opportunity(svc):
    text = svc.rank(region="anything")["data"]["interpretation"]
    assert "not a verified investment opportunity" in text and "relative" in text


def test_hub_filter_narrows_the_group_without_changing_the_methodology(svc):
    filtered = svc.rank(region="anything", hub_classes=["l", "M", "S"])
    explicit = svc.rank(airports=["AAA", "BBB", "CCC"])

    fd, ed = filtered["data"], explicit["data"]
    assert fd["candidate_group"]["hub_filter"] == {"hub_classes": ["L", "M", "S"], "excluded_airports": ["DDD"]}
    assert [(s["airport"], s["score"]) for s in fd["airports"]] == [(s["airport"], s["score"]) for s in ed["airports"]]
    assert fd["weights_used"] == ed["weights_used"]
    assert fd["small_sample_airports"] == []


def test_invalid_hub_class_is_rejected(svc):
    with pytest.raises(DataValidationError):
        svc.rank(region="anything", hub_classes=["X"])


def test_compare_and_profile_carry_small_sample_warnings(svc):
    c = svc.compare(["AAA", "DDD"])
    assert [s["airport"] for s in c["data"]["small_sample_airports"]] == ["DDD"]
    assert c["confidence"] == "low" and any(w.startswith("Small sample: DDD") for w in c["warnings"])
