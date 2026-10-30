from fastapi.testclient import TestClient

from app import main


def test_health_reports_llm_and_bts_status(monkeypatch):
    monkeypatch.setattr(main.bts_api, "check_connectivity", lambda s: {"reachable": True, "source_type": "public_api"})
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    resp = TestClient(main.app).get("/api/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_configured"] is False
    assert body["llm_model"]
    assert body["bts_api"]["source_type"] == "public_api"


def test_auth_token_alone_does_not_count_as_configured(monkeypatch):
    # langchain-anthropic reads ANTHROPIC_API_KEY only (verified in Phase 4 cleanup).
    monkeypatch.setattr(main.bts_api, "check_connectivity", lambda s: {"reachable": True})
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "placeholder")

    assert TestClient(main.app).get("/api/health").json()["llm_configured"] is False


def test_default_model_is_sonnet_when_unset(monkeypatch):
    from app.settings import get_settings

    monkeypatch.delenv("LLM_MODEL", raising=False)

    assert get_settings().llm_model == "claude-sonnet-5-5"


def test_model_id_comes_from_env(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "some-configured-model")
    monkeypatch.setattr(main.bts_api, "check_connectivity", lambda s: {"reachable": True})

    assert TestClient(main.app).get("/api/health").json()["llm_model"] == "some-configured-model"
