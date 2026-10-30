"""Minimal BTS Socrata (SODA) API client.

Phase 4 scope: a live connectivity check only. The full traffic-metrics client
(whitelisted SoQL, cache, recorded fallback) is Phase 5.
"""

from datetime import datetime, timezone

import httpx

from app.settings import Settings


def check_connectivity(settings: Settings) -> dict:
    """Ask the live BTS API for its latest reporting month.

    Returns a provenance-style dict; never raises on network errors.
    """
    params = {"$select": "max(reporting_month) AS latest_month"}
    headers = {"X-App-Token": settings.bts_app_token} if settings.bts_app_token else {}
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        resp = httpx.get(settings.bts_api_base, params=params, headers=headers, timeout=settings.http_timeout_s)
        resp.raise_for_status()
        latest = resp.json()[0].get("latest_month")
        return {
            "reachable": True,
            "status_code": resp.status_code,
            "latest_month": latest[:7] if latest else None,
            "source_type": "public_api",
            "url": str(resp.request.url),
            "retrieved_at": retrieved_at,
        }
    except (httpx.HTTPError, ValueError, IndexError, KeyError) as exc:
        return {
            "reachable": False,
            "error": type(exc).__name__,
            "source_type": "public_api",
            "url": settings.bts_api_base,
            "retrieved_at": retrieved_at,
        }
