"""Provenance attached to every dataset the data layer returns (D-017, D-019)."""

from dataclasses import asdict, dataclass, field
from typing import Literal

SourceType = Literal["public_api", "public_dataset_snapshot", "recorded_api_fallback"]


@dataclass(frozen=True)
class Provenance:
    source_type: SourceType
    name: str
    url: str
    retrieval_method: str
    retrieved_at: str
    observation_period: str
    limitations: tuple[str, ...] = field(default_factory=tuple)
    cache_status: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["limitations"] = list(self.limitations)
        return d
