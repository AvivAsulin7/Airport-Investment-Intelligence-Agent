"""Snapshot store, airport resolver and accessors on a tiny synthetic processed directory."""

import csv
import hashlib
import json

import pytest

from app.data.airports import AirportReference
from app.data.operations import OperationsData
from app.data.routes import RouteData
from app.data.snapshots import SnapshotError, SnapshotStore
from app.data.sources import bts_ontime, bts_t100, faa_enplanements
from app.data.validation import DataValidationError

AIRPORTS = [
    ("BIG", "Big Intl", "Bigtown", "MA", "NE", "P", "L", "2000", "1900"),
    ("MID", "Mid Regional", "Midville", "CT", "NE", "P", "S", "500", "450"),
    ("TNY", "Tiny Field", "Tinyton", "VT", "NE", "CS", "", "40", "30"),
    ("LAX", "Los Angeles International", "Los Angeles", "CA", "WP", "P", "L", "9000", "9100"),
    ("SNA", "John Wayne/Orange County", "Santa Ana", "CA", "WP", "P", "M", "800", "780"),
]


def _write(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        w.writerows(rows)
    return {"rows": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _ds(files, period):
    return {"source_type": "public_dataset_snapshot", "name": "x", "url": "u", "retrieval_method": "m",
            "retrieved_at": "2026-10-30T00:00:00+00:00", "observation_period": period, "files": files,
            "limitations": ["lim"], "notes": []}


@pytest.fixture
def store(tmp_path):
    d = tmp_path
    dep_row = ["BIG", 100, 2, 1, 98, 20, 98, 1470.0, 98, 980.0]
    arr_row = ["BIG", 100, 2, 15, 100.0, 10.0, 300.0, 0.0, 50.0]
    seg_rows = [
        ["BIG", "FAR", "DE", "F", 3600, 30, 30, 6000, 5000, 0],
        ["BIG", "MID", "US", "F", 100, 70, 70, 7000, 6000, 0],
        ["BIG", "FAR", "DE", "G", 3600, 50, 50, 0, 0, 9000],
    ]
    manifest = {"datasets": {
        "airports": _ds({"airports_faa.csv": _write(d / "airports_faa.csv", faa_enplanements.FIELDS, AIRPORTS)}, "CY2025"),
        "ontime": _ds({
            "ontime_departures.csv": _write(d / "ontime_departures.csv", bts_ontime.DEPARTURE_FIELDS, [dep_row]),
            "ontime_arrival_causes.csv": _write(d / "ontime_arrival_causes.csv", bts_ontime.ARRIVAL_FIELDS, [arr_row]),
        }, "2026-07"),
        "t100_segments": _ds({"t100_segments.csv": _write(d / "t100_segments.csv", bts_t100.SEGMENT_FIELDS, seg_rows)},
                             "2026-07"),
    }}
    (d / "manifest.json").write_text(json.dumps(manifest))
    return SnapshotStore.load(d)


def test_checksum_mismatch_is_detected(store):
    (store.directory / "airports_faa.csv").write_text("tampered")
    with pytest.raises(SnapshotError):
        SnapshotStore.load(store.directory)


def test_missing_manifest_is_reported(tmp_path):
    with pytest.raises(SnapshotError):
        SnapshotStore.load(tmp_path / "nope")


def test_region_resolution_uses_data_and_primary_filter(store):
    ref = AirportReference(store)

    res = ref.resolve_region("New England")

    assert [a.code for a in res.airports] == ["BIG", "MID"]  # sorted by enplanements, non-primary excluded
    assert "RO=NE" in res.interpretation and "VT" in res.interpretation
    assert [a.code for a in ref.resolve_region("new england", primary_only=False).airports] == ["BIG", "MID", "TNY"]


def test_two_letter_ambiguous_code_prefers_state(store):
    # 'NE' is both an FAA region code and Nebraska; codes resolve as states, names as regions.
    assert ref_interpretation(store, "NE") == "US state NE"


def ref_interpretation(store, q):
    return AirportReference(store).resolve_region(q).interpretation


def test_state_resolution_and_unknown_region(store):
    ref = AirportReference(store)
    assert [a.code for a in ref.resolve_region("California").airports] == ["LAX", "SNA"]
    with pytest.raises(DataValidationError):
        ref.resolve_region("Atlantis")


def test_search_alias_city_and_unknown(store):
    ref = AirportReference(store)
    la = ref.search("LA")
    assert [a.code for a in la.airports] == ["LAX"] and "LAX" in la.interpretation
    assert [a.code for a in ref.search("Santa Ana").airports] == ["SNA"]
    with pytest.raises(DataValidationError):
        ref.search("Nowhere")
    with pytest.raises(DataValidationError):
        ref.require(["ZZZ"])


def test_operations_missing_airport_is_none_not_zero(store):
    ops = OperationsData(store).get(["BIG", "MID"])

    assert ops.departures["BIG"].depdel15_delayed == 20
    assert ops.departures["MID"] is None
    assert ops.arrivals["BIG"].nas_delay_min == 300.0
    assert ops.observation_period == "2026-07"
    assert ops.provenance.source_type == "public_dataset_snapshot"


def test_routes_require_explicit_classes_and_filter_them(store):
    routes = RouteData(store)

    passenger = routes.segments_from("BIG", ["F", "L"])
    assert {s.service_class for s in passenger.segments} == {"F"}
    assert sum(s.departures_performed for s in passenger.segments) == 100
    assert routes.classes_present("BIG") == {"F": 100.0, "G": 50.0}
    with pytest.raises(DataValidationError):
        routes.segments_from("BIG", [])
