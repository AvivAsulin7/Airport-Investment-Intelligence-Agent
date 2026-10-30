"""Load processed public-dataset snapshots and their manifest (provenance + checksums)."""

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.data.provenance import Provenance


class SnapshotError(RuntimeError):
    """Snapshots missing, incomplete, or failing checksum validation."""


@dataclass
class SnapshotStore:
    directory: Path
    manifest: dict

    @classmethod
    def load(cls, directory: Path, verify: bool = True) -> "SnapshotStore":
        path = directory / "manifest.json"
        if not path.is_file():
            raise SnapshotError(f"no manifest at {path}; run backend/scripts/build_snapshots.py")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        store = cls(directory, manifest)
        if verify:
            store.verify()
        return store

    def verify(self) -> None:
        for key, ds in self.manifest["datasets"].items():
            for fname, meta in ds["files"].items():
                f = self.directory / fname
                if not f.is_file():
                    raise SnapshotError(f"{key}: missing file {fname}")
                if hashlib.sha256(f.read_bytes()).hexdigest() != meta["sha256"]:
                    raise SnapshotError(f"{key}: checksum mismatch for {fname}")

    def has(self, dataset: str) -> bool:
        return dataset in self.manifest["datasets"]

    def provenance(self, dataset: str) -> Provenance:
        if not self.has(dataset):
            raise SnapshotError(f"dataset {dataset!r} not in manifest")
        ds = self.manifest["datasets"][dataset]
        return Provenance(
            source_type=ds["source_type"],
            name=ds["name"],
            url=ds["url"],
            retrieval_method=ds["retrieval_method"],
            retrieved_at=ds["retrieved_at"],
            observation_period=ds["observation_period"],
            limitations=tuple(ds["limitations"]) + tuple(ds.get("notes", [])),
            cache_status="snapshot",
        )

    def read_csv(self, fname: str) -> list[dict]:
        with (self.directory / fname).open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def path(self, fname: str) -> Path:
        return self.directory / fname
