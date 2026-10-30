"""Application settings loaded from environment variables (and an optional repo-root .env).

No secrets are hardcoded. ChatAnthropic reads ANTHROPIC_API_KEY itself; we only
check whether it is present so the app can report whether the LLM is configured.
ANTHROPIC_AUTH_TOKEN is not read by langchain-anthropic 1.7.7 (verified in Phase 4).
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

# Default model chosen for cost (NOTES.md D-047, D-048); always overridable via LLM_MODEL (D-033).
DEFAULT_LLM_MODEL = "claude-sonnet-5-5"


@dataclass(frozen=True)
class Settings:
    llm_model: str
    llm_effort: str
    llm_max_tokens: int
    agent_max_model_calls: int
    bts_api_base: str
    bts_app_token: str | None
    http_timeout_s: float
    frontend_dist: Path
    data_raw_dir: Path
    data_processed_dir: Path

    @property
    def llm_configured(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))


def get_settings() -> Settings:
    return Settings(
        llm_model=os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
        llm_effort=os.getenv("LLM_EFFORT", "medium"),
        llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "16000")),
        agent_max_model_calls=int(os.getenv("AGENT_MAX_MODEL_CALLS", "8")),
        bts_api_base=os.getenv("BTS_API_BASE", "https://data.bts.gov/resource/r495-tyji.json"),
        bts_app_token=os.getenv("BTS_APP_TOKEN") or None,
        http_timeout_s=float(os.getenv("HTTP_TIMEOUT_S", "10")),
        frontend_dist=REPO_ROOT / "frontend" / "dist",
        # Both gitignored: raw downloads (D-019) and processed snapshots until D-037 checks pass.
        data_raw_dir=Path(os.getenv("DATA_RAW_DIR", REPO_ROOT / "data" / "raw")),
        data_processed_dir=Path(os.getenv("DATA_PROCESSED_DIR", REPO_ROOT / "data" / "processed")),
    )
