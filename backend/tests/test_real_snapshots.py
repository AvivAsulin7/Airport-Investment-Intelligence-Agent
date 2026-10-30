"""Checks against the real processed snapshots (skipped unless build_snapshots.py has been run)."""

import pytest

from app.data.layer import load_data_layer
from app.data.validation import CARGO_ONLY_CLASSES, PASSENGER_CLASSES
from app.settings import get_settings

settings = get_settings()
pytestmark = pytest.mark.skipif(
    not (settings.data_processed_dir / "manifest.json").is_file(), reason="snapshots not built"
)


@pytest.fixture(scope="module")
def layer():
    return load_data_layer(settings)


def test_manifest_provenance_is_complete(layer):
    for key, ds in layer.snapshots.manifest["datasets"].items():
        for field in ("source_type", "name", "url", "retrieval_method", "retrieved_at", "observation_period", "limitations"):
            assert ds.get(field), (key, field)
    assert layer.snapshots.manifest["datasets"]["ontime"]["source_type"] == "public_dataset_snapshot"


def test_new_england_resolves_from_data(layer):
    res = layer.airports.resolve_region("New England")

    assert len(res.airports) >= 5
    assert {a.state for a in res.airports} <= {"CT", "ME", "MA", "NH", "RI", "VT"}
    assert all(a.is_primary for a in res.airports)


def test_operations_cover_large_airports_and_flag_gaps(layer):
    ops = layer.operations.get(["LAX", "SNA", "SFO"])

    for code in ("LAX", "SNA", "SFO"):
        d = ops.departures[code]
        assert d is not None and d.depdel15_eligible > 0 and d.taxi_out_n > 0


def test_routes_keep_passenger_and_cargo_separate(layer):
    pax = layer.routes.segments_from("ANC", PASSENGER_CLASSES)
    cargo = layer.routes.segments_from("ANC", CARGO_ONLY_CLASSES)

    assert pax.segments and all(s.service_class in PASSENGER_CLASSES for s in pax.segments)
    assert all(s.service_class in CARGO_ONLY_CLASSES for s in cargo.segments)
    assert pax.observation_period == layer.snapshots.manifest["datasets"]["t100_segments"]["observation_period"]
