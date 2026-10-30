import json

import httpx
import pytest

from app.data.bts_api import BtsApiUnavailable, BtsTrafficClient
from app.data.validation import DataValidationError
from app.settings import get_settings


def _row(code, month, pax="100", seats="200", dep="10"):
    return {
        "origin_airport_code": code,
        "reporting_month": f"{month}-01T00:00:00.000",
        "total_passengers": pax,
        "total_seats": seats,
        "total_departures": dep,
        "domestic_departures": dep,
        "outbound_international": "0",
        "total_freight_lbs": "5",
    }


def _client(handler, **kw):
    return BtsTrafficClient(get_settings(), client=httpx.Client(transport=httpx.MockTransport(handler)), **kw)


def test_builds_whitelisted_soql_and_parses_rows():
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=[_row("AAA", "2026-06"), _row("AAA", "2026-07", pax="")])

    series = _client(handler).fetch_monthly_traffic(["aaa"], "2026-06", "2026-07")

    assert "origin_airport_code in('AAA')" in seen["params"]["$where"]
    assert "between '2026-06-01T00:00:00' and '2026-07-01T00:00:00'" in seen["params"]["$where"]
    assert [(r.month, r.passengers) for r in series.rows] == [("2026-06", 100.0), ("2026-07", None)]
    assert series.provenance.source_type == "public_api"
    assert series.provenance.cache_status == "live"
    assert series.missing_months == {}


def test_reports_missing_months_instead_of_filling_them():
    series = _client(lambda r: httpx.Response(200, json=[_row("AAA", "2026-07")])).fetch_monthly_traffic(
        ["AAA", "BBB"], "2026-06", "2026-07"
    )

    assert series.missing_months == {"AAA": ["2026-06"], "BBB": ["2026-06", "2026-07"]}


def test_invalid_input_never_reaches_the_api():
    def handler(request):
        raise AssertionError("API must not be called")

    with pytest.raises(DataValidationError):
        _client(handler).fetch_monthly_traffic(["LA'X"], "2026-06", "2026-07")
    with pytest.raises(DataValidationError):
        _client(handler).fetch_monthly_traffic(["LAX"], "2026-07", "2026-06")


def test_duplicate_rows_are_summed_with_a_warning():
    rows = [_row("AAA", "2026-07", pax="100"), _row("AAA", "2026-07", pax="50")]
    series = _client(lambda r: httpx.Response(200, json=rows)).fetch_monthly_traffic(["AAA"], "2026-07", "2026-07")

    assert series.rows[0].passengers == 150.0
    assert series.warnings


def test_memory_cache_avoids_a_second_call():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(200, json=[_row("AAA", "2026-07")])

    client = _client(handler)
    client.fetch_monthly_traffic(["AAA"], "2026-07", "2026-07")
    second = client.fetch_monthly_traffic(["AAA"], "2026-07", "2026-07")

    assert len(calls) == 1
    assert second.provenance.cache_status == "memory_cache"


def test_retries_once_then_uses_labelled_recorded_fallback(tmp_path):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503)

    fallback = tmp_path / "fb.json"
    fallback.write_text(json.dumps({"retrieved_at": "2026-10-30T00:00:00+00:00", "rows": [_row("AAA", "2026-07")]}))

    series = _client(handler, fallback_path=fallback).fetch_monthly_traffic(["AAA"], "2026-07", "2026-07")

    assert len(calls) == 2
    assert series.provenance.source_type == "recorded_api_fallback"
    assert series.provenance.cache_status == "recorded_fallback"
    assert series.provenance.retrieved_at == "2026-10-30T00:00:00+00:00"
    assert any("recorded" in w for w in series.warnings)


def test_outage_without_fallback_raises():
    with pytest.raises(BtsApiUnavailable):
        _client(lambda r: httpx.Response(500)).fetch_monthly_traffic(["AAA"], "2026-07", "2026-07")


def test_latest_month():
    client = _client(lambda r: httpx.Response(200, json=[{"latest_month": "2026-07-01T00:00:00.000"}]))
    assert client.latest_month() == "2026-07"
