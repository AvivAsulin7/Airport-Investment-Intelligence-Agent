"""Build the processed public-dataset snapshots used by the data layer (Phase 5).

Downloads raw public files into data/raw/ (gitignored; reused if already present),
aggregates them into small CSVs in data/processed/ (gitignored until D-037 checks),
and writes data/processed/manifest.json with provenance for every dataset.

Usage (from backend/):
    .venv/Scripts/python scripts/build_snapshots.py [--month 2026-07] [--t100-fallback-months 6]
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.bts_api import BtsTrafficClient  # noqa: E402
from app.data.sources import bts_ontime, bts_t100, faa_enplanements  # noqa: E402
from app.data.validation import shift_month  # noqa: E402
from app.settings import get_settings  # noqa: E402

ONTIME_DEPARTURES = "ontime_departures.csv"
ONTIME_ARRIVALS = "ontime_arrival_causes.csv"
T100_SEGMENTS = "t100_segments.csv"
AIRPORTS = "airports_faa.csv"
BTS_FALLBACK = "bts_api_fallback.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def download(url: str, dest: Path, timeout_s: float = 900) -> str:
    """Download unless the raw file is already cached; return the retrieval timestamp."""
    stamp = dest.with_suffix(dest.suffix + ".retrieved_at")
    if dest.is_file() and stamp.is_file():
        print(f"  reuse cached raw file {dest.name}")
        return stamp.read_text().strip()
    print(f"  downloading {url}")
    with httpx.stream("GET", url, timeout=timeout_s, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True) as r:
        r.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)
    ts = now()
    stamp.write_text(ts)
    return ts


def raw_info(path: Path) -> dict:
    """Size and checksum of a raw download, so a later re-download can be compared byte-for-byte."""
    return {path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}}


def entry(name, url, method, retrieved_at, period, files, limitations, notes=None, raw=None):
    return {
        "source_type": "public_dataset_snapshot",
        "name": name,
        "url": url,
        "retrieval_method": method,
        "retrieved_at": retrieved_at,
        "observation_period": period,
        "files": files,
        "raw_files": raw or {},
        "limitations": list(limitations),
        "notes": notes or [],
    }


def build_airports(raw: Path, out: Path) -> dict:
    print("[FAA enplanements]")
    xlsx = raw / "faa_cy2025_commercial_service_enplanements.xlsx"
    ts = download(faa_enplanements.URL, xlsx)
    records, meta = faa_enplanements.parse_enplanements(faa_enplanements.read_xlsx_rows(xlsx))
    write_csv(out / AIRPORTS, faa_enplanements.FIELDS, records)
    print(f"  {len(records)} airports")
    return entry(
        "FAA CY2025 Commercial Service Enplanements",
        faa_enplanements.URL,
        "public file download (XLSX)",
        ts,
        f"CY{meta['current_year']} (prior column CY{meta['prior_year']})",
        {AIRPORTS: {"rows": len(records), "sha256": sha256(out / AIRPORTS)}},
        faa_enplanements.LIMITATIONS,
        [f"enplanements_current = CY{meta['current_year']}, enplanements_prior = CY{meta['prior_year']}"],
        raw_info(xlsx),
    )


def build_ontime(raw: Path, out: Path, month: str) -> dict:
    print("[BTS on-time]")
    y, m = int(month[:4]), int(month[5:])
    url = bts_ontime.URL_TEMPLATE.format(year=y, month=m)
    zpath = raw / f"ontime_{month}.zip"
    ts = download(url, zpath)
    dep, arr, periods = bts_ontime.aggregate_zip(zpath)
    if periods != {month}:
        raise RuntimeError(f"on-time file covers {sorted(periods)}, expected {month}")
    write_csv(out / ONTIME_DEPARTURES, bts_ontime.DEPARTURE_FIELDS, dep)
    write_csv(out / ONTIME_ARRIVALS, bts_ontime.ARRIVAL_FIELDS, arr)
    print(f"  {len(dep)} origin airports, {len(arr)} destination airports")
    return entry(
        "BTS Reporting Carrier On-Time Performance",
        url,
        "public file download (monthly ZIP)",
        ts,
        month,
        {
            ONTIME_DEPARTURES: {"rows": len(dep), "sha256": sha256(out / ONTIME_DEPARTURES)},
            ONTIME_ARRIVALS: {"rows": len(arr), "sha256": sha256(out / ONTIME_ARRIVALS)},
        },
        bts_ontime.LIMITATIONS,
        raw=raw_info(zpath),
    )


def build_t100(raw: Path, out: Path, month: str, fallback_months: int) -> dict:
    """Try the target month first, then earlier months; never fabricate a period."""
    print("[BTS T-100 Segment, All Carriers]")
    attempts = []
    for back in range(fallback_months + 1):
        candidate = shift_month(month, -back)
        zpath = raw / f"t100_segment_all_carriers_{candidate}.zip"
        stamp = zpath.with_suffix(".zip.retrieved_at")
        try:
            if zpath.is_file() and stamp.is_file():
                print(f"  reuse cached raw file {zpath.name}")
                ts = stamp.read_text().strip()
            else:
                print(f"  requesting {candidate} via TranStats form")
                bts_t100.download_month(int(candidate[:4]), int(candidate[5:]), zpath)
                ts = now()
                stamp.write_text(ts)
            segments, periods, warnings = bts_t100.aggregate_zip(zpath)
            if periods != {candidate} or not segments:
                raise bts_t100.T100Unavailable(f"file covers {sorted(periods)} with {len(segments)} rows")
            break
        except (bts_t100.T100Unavailable, httpx.HTTPError) as exc:
            attempts.append(f"{candidate}: {type(exc).__name__}: {exc}")
            print(f"  unavailable: {attempts[-1]}")
    else:
        raise RuntimeError("no T-100 month available: " + "; ".join(attempts))
    write_csv(out / T100_SEGMENTS, bts_t100.SEGMENT_FIELDS, segments)
    notes = list(warnings)
    if candidate != month:
        notes.append(f"Requested {month} was unavailable; latest verified available month {candidate} used.")
    notes += [f"unavailable attempt: {a}" for a in attempts]
    print(f"  {len(segments)} route/class rows for {candidate}")
    return entry(
        "BTS T-100 Segment (All Carriers)",
        bts_t100.FORM_URL,
        "public TranStats download form (ASP.NET POST; not an API)",
        ts,
        candidate,
        {T100_SEGMENTS: {"rows": len(segments), "sha256": sha256(out / T100_SEGMENTS)}},
        bts_t100.LIMITATIONS,
        notes,
        raw_info(zpath),
    )


def build_bts_fallback(out: Path, airports_csv: Path) -> dict:
    """Record a 24-month live API response for FAA primary airports (labelled fallback, never 'live')."""
    print("[BTS API recorded fallback]")
    settings = get_settings()
    client = BtsTrafficClient(settings)
    latest = client.latest_month()
    with airports_csv.open(encoding="utf-8") as fh:
        primary = [r["code"] for r in csv.DictReader(fh) if r["service_level"] == "P"]
    rows = []
    for i in range(0, len(primary), 30):
        series = client.fetch_monthly_traffic(primary[i : i + 30], shift_month(latest, -23), latest)
        rows += [
            {
                "origin_airport_code": r.airport,
                "reporting_month": f"{r.month}-01T00:00:00.000",
                "total_passengers": r.passengers,
                "total_seats": r.seats,
                "total_departures": r.departures,
                "domestic_departures": r.domestic_departures,
                "outbound_international": r.international_departures,
                "total_freight_lbs": r.freight_lbs,
            }
            for r in series.rows
        ]
    ts = now()
    path = out / BTS_FALLBACK
    path.write_text(json.dumps({"retrieved_at": ts, "latest_month": latest, "rows": rows}), encoding="utf-8")
    print(f"  {len(rows)} airport-months for {len(primary)} primary airports")
    return {
        "source_type": "recorded_api_fallback",
        "name": "Recorded BTS SODA API response (r495-tyji)",
        "url": settings.bts_api_base,
        "retrieval_method": "SODA JSON API, recorded for outage fallback only",
        "retrieved_at": ts,
        "observation_period": f"{shift_month(latest, -23)}..{latest}",
        "files": {BTS_FALLBACK: {"rows": len(rows), "sha256": sha256(path)}},
        "limitations": ["Used only if the live API is unavailable; always labelled as recorded, never as live."],
        "notes": [],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--month", default="2026-07", help="target month for on-time and T-100 (YYYY-MM)")
    p.add_argument("--t100-fallback-months", type=int, default=6)
    p.add_argument("--skip-bts-fallback", action="store_true")
    args = p.parse_args()

    settings = get_settings()
    raw, out = settings.data_raw_dir, settings.data_processed_dir
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    datasets = {
        "airports": build_airports(raw, out),
        "ontime": build_ontime(raw, out, args.month),
        "t100_segments": build_t100(raw, out, args.month, args.t100_fallback_months),
    }
    if not args.skip_bts_fallback:
        datasets["bts_api_fallback"] = build_bts_fallback(out, out / AIRPORTS)
    manifest = {"built_at": now(), "target_month": args.month, "datasets": datasets}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest written: {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
