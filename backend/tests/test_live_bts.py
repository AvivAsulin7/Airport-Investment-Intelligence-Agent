import pytest

from app.data.bts_api import check_connectivity
from app.settings import get_settings


@pytest.mark.live
def test_bts_api_is_reachable():
    result = check_connectivity(get_settings())

    assert result["reachable"] is True, result
    assert result["status_code"] == 200
    assert result["source_type"] == "public_api"
    assert result["latest_month"] and len(result["latest_month"]) == 7
