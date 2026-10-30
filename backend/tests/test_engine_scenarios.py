"""Acceptance scenarios Q1–Q4 against the real Phase 5 data layer (live BTS API + built snapshots).

These assert structure and invariants, not hardcoded answers; the same calls work for other
airports and regions. Marked `live` (network); skipped if snapshots are not built.
"""

import pytest

from app.data.layer import load_data_layer
from app.engine.service import AnalyticsService
from app.settings import get_settings

settings = get_settings()
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not (settings.data_processed_dir / "manifest.json").is_file(), reason="snapshots not built"),
]


@pytest.fixture(scope="module")
def svc():
    return AnalyticsService(load_data_layer(settings))


def _source_types(result):
    return {p["source_type"] for p in result["provenance"]}


def test_q1_new_england_ranking(svc):
    r = svc.rank(region="New England")
    d = r["data"]

    assert r["result_type"] == "ranking" and d["status"] == "ranked"
    assert set(d["candidate_group"]["airports"]) == {a.code for a in svc.data.airports.resolve_region("New England").airports}
    ranked = [s for s in d["airports"] if s["status"] == "ranked"]
    assert len(ranked) >= 3 and [s["rank"] for s in ranked] == list(range(1, len(ranked) + 1))
    assert all(ranked[i]["score"] >= ranked[i + 1]["score"] for i in range(len(ranked) - 1))
    assert all(s["coverage"] >= 0.6 for s in ranked)
    assert {"public_api", "public_dataset_snapshot"} <= _source_types(r)
    assert r["windows"]["operations"] == "2026-07" and "not profitability" in d["interpretation"]
    assert any("Periods differ" in w for w in r["warnings"])


def test_q2_lax_vs_sna_congestion(svc):
    lax = svc.data.airports.search("LA").airports[0].code
    sna = svc.data.airports.search("Santa Ana").airports[0].code
    r = svc.compare([lax, sna])
    d = r["data"]

    assert (lax, sna) == ("LAX", "SNA") and d["baseline"] == "LAX"
    for m in ("delay_rate", "cancellation_rate", "avg_taxi_out_min"):
        for a in ("LAX", "SNA"):
            v = d["values"][m][a]
            assert v["value"] is not None and v["denominator"] > 0
            assert v["value"] == pytest.approx(v["numerator"] / v["denominator"])
    assert d["values"]["departures_t12m"]["LAX"]["value"] > d["values"]["departures_t12m"]["SNA"]["value"]
    assert "score" not in d  # comparison, no composite


def test_q3_anchorage_long_haul(svc):
    r = svc.long_haul("ANC")
    d = r["data"]

    assert d["threshold_miles"] == 3000 and d["primary"]["service_classes"] == ["F", "L"]
    p, a = d["primary"], d["all_classes"]
    assert p["share"] == pytest.approx(p["numerator"] / p["denominator"])
    assert a["denominator"] == sum(c["departures"] for c in d["by_class"].values())
    assert a["share"] != p["share"]  # cargo materially changes the answer at ANC
    assert r["windows"]["routes"] == "2026-07" and _source_types(r) == {"public_dataset_snapshot"}
    assert svc.long_haul("ANC", threshold_miles=4000)["data"]["primary"]["numerator"] <= p["numerator"]


def test_q4_sfo_demand_pressure(svc):
    r = svc.demand_profile("SFO")
    d = r["data"]

    assert d["unmet_demand"]["measured"] is False
    assert len(d["peers"]) >= 3 and "SFO" not in d["peers"]
    for m, pos in d["capacity_pressure"].items():
        assert pos["percentile"] is None or 0 <= pos["percentile"] <= 100, m
    assert sum(c["share"] for c in d["delay_causes"]) == pytest.approx(1.0)
    assert d["observed_demand"]["passengers_2019"]["window"] == "2019-01..2019-12"
    assert {"public_api", "public_dataset_snapshot"} <= _source_types(r)


def test_generality_other_region_and_airport(svc):
    assert svc.rank(region="Florida")["data"]["status"] == "ranked"
    assert svc.long_haul("SEA")["data"]["primary"]["denominator"] > 0
    assert svc.compare(["BOS", "BDL", "PVD"])["data"]["baseline"] == "BOS"
