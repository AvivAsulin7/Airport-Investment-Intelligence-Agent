import pytest

from app.data.bts_api import BtsTrafficClient, check_connectivity
from app.data.validation import shift_month
from app.settings import get_settings


@pytest.mark.live
def test_bts_api_is_reachable():
    result = check_connectivity(get_settings())

    assert result["reachable"] is True, result
    assert result["status_code"] == 200
    assert result["source_type"] == "public_api"
    assert result["latest_month"] and len(result["latest_month"]) == 7


@pytest.mark.live
def test_live_24_month_traffic_window():
    client = BtsTrafficClient(get_settings())
    latest = client.latest_month()

    series = client.fetch_monthly_traffic(["ORD", "DEN"], shift_month(latest, -23), latest)

    assert series.provenance.source_type == "public_api" and series.provenance.cache_status == "live"
    assert len(series.requested_months) == 24
    assert series.missing_months == {}, series.missing_months
    assert len(series.rows) == 48
    assert all(r.passengers and r.seats and r.departures for r in series.rows)
