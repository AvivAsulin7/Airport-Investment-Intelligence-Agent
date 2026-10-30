"""BTS TranStats T-100 Segment (All Carriers): route-level departures with distance and service class.

There is no API for this table; it is downloaded through the public TranStats form
(verified in Phase 2). The form is an ASP.NET postback and may change (fragility noted).
"""

import csv
import io
import re
import urllib.parse
import zipfile
from collections import defaultdict
from pathlib import Path

import httpx

FORM_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FMG&QO_fu146_anzr=Nv4%20Pn44vr45"
DOWNLOAD_FIELDS = [
    "YEAR",
    "MONTH",
    "ORIGIN",
    "DEST",
    "DEST_COUNTRY",
    "CLASS",
    "DEPARTURES_SCHEDULED",
    "DEPARTURES_PERFORMED",
    "SEATS",
    "PASSENGERS",
    "FREIGHT",
    "DISTANCE",
]
LIMITATIONS = (
    "Monthly route segments for all carriers (US and foreign) reporting T-100; aggregated over carriers.",
    "DISTANCE is the published distance between airports in statute miles (A-016: matches great-circle"
    " statute miles within ~0.3% on 400 sampled routes).",
    "Service classes: F scheduled passenger/cargo, G scheduled all-cargo, L non-scheduled passenger/cargo,"
    " P non-scheduled all-cargo.",
    "Single month; route mix can be seasonal.",
)
SEGMENT_FIELDS = [
    "origin",
    "dest",
    "dest_country",
    "service_class",
    "distance_miles",
    "departures_performed",
    "departures_scheduled",
    "seats",
    "passengers",
    "freight_lbs",
]


class T100Unavailable(RuntimeError):
    pass


def download_month(year: int, month: int, dest: Path, timeout_s: float = 600) -> None:
    """POST the TranStats form for one month; raise T100Unavailable unless a ZIP comes back."""
    with httpx.Client(timeout=timeout_s, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True) as client:
        html = client.get(FORM_URL).text

        def hidden(name: str) -> str:
            m = re.search(rf'id="{name}" value="([^"]*)"', html)
            return m.group(1) if m else ""

        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": hidden("__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": hidden("__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": hidden("__EVENTVALIDATION"),
            "cboGeography": "All",
            "cboYear": str(year),
            "cboPeriod": str(month),
            "btnDownload": "Download",
        }
        data.update({f: "on" for f in DOWNLOAD_FIELDS})
        resp = client.post(FORM_URL, content=urllib.parse.urlencode(data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    if resp.status_code != 200 or not resp.content.startswith(b"PK"):
        raise T100Unavailable(f"no ZIP for {year}-{month:02d} (HTTP {resp.status_code})")
    dest.write_bytes(resp.content)


def aggregate_rows(rows) -> tuple[list[dict], set[str], list[str]]:
    agg = defaultdict(lambda: defaultdict(float))
    distance = {}
    periods, warnings = set(), []
    for r in rows:
        periods.add(f"{int(float(r['YEAR'])):04d}-{int(float(r['MONTH'])):02d}")
        key = (r["ORIGIN"], r["DEST"], r["DEST_COUNTRY"], r["CLASS"])
        dist = float(r["DISTANCE"] or 0)
        if key[:2] in distance and distance[key[:2]] != dist:
            warnings.append(f"inconsistent distance for {key[0]}-{key[1]}")
        distance[key[:2]] = dist
        a = agg[key]
        a["departures_performed"] += float(r["DEPARTURES_PERFORMED"] or 0)
        a["departures_scheduled"] += float(r["DEPARTURES_SCHEDULED"] or 0)
        a["seats"] += float(r["SEATS"] or 0)
        a["passengers"] += float(r["PASSENGERS"] or 0)
        a["freight_lbs"] += float(r["FREIGHT"] or 0)
    out = []
    for (origin, dest, country, cls), a in sorted(agg.items()):
        out.append(
            {
                "origin": origin,
                "dest": dest,
                "dest_country": country,
                "service_class": cls,
                "distance_miles": distance[(origin, dest)],
                **{k: round(a[k], 2) for k in SEGMENT_FIELDS[5:]},
            }
        )
    return out, periods, sorted(set(warnings))


def aggregate_zip(path: Path) -> tuple[list[dict], set[str], list[str]]:
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as fh:
            return aggregate_rows(csv.DictReader(io.TextIOWrapper(fh, encoding="utf8")))
