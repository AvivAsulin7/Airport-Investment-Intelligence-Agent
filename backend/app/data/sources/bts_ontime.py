"""BTS Reporting Carrier On-Time Performance (monthly ZIP): departure and arrival-cause aggregates.

We store counts and sums per airport, not rates; Phase 6 computes the rates.
Definitions (architecture.md §6.0a, P-029):
- departure delay: Origin=X, Cancelled=0, DepDel15 not blank -> eligible; DepDel15=1 -> delayed
- cancellation: Origin=X, Cancelled=1 over all Origin=X rows
- taxi-out: Origin=X, Cancelled=0, TaxiOut not blank
- delay causes: arrival records Dest=X (cause minutes are attached to delayed arrivals)
"""

import csv
import io
import zipfile
from collections import defaultdict
from pathlib import Path

URL_TEMPLATE = (
    "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)
LIMITATIONS = (
    "Reporting (large US passenger) carriers only; cargo carriers and foreign carriers are not included.",
    "Single month; delay and taxi-out levels are seasonal.",
    "Delay causes are attached to delayed arrivals and are airline-reported attributions.",
)
DEPARTURE_FIELDS = [
    "airport",
    "rows",
    "cancelled",
    "diverted",
    "depdel15_eligible",
    "depdel15_delayed",
    "taxi_out_n",
    "taxi_out_sum_min",
    "dep_delay_n",
    "dep_delay_sum_min",
]
CAUSES = ["CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay"]
ARRIVAL_FIELDS = ["airport", "arr_rows", "arr_cancelled", "arrdel15_delayed"] + [
    f"{c[: -len('Delay')].lower()}_delay_min" for c in CAUSES
]


def _flag(value: str) -> bool | None:
    v = (value or "").strip()
    if v == "":
        return None
    return float(v) == 1.0


def _num(value: str) -> float | None:
    v = (value or "").strip()
    return float(v) if v else None


def aggregate_rows(rows) -> tuple[list[dict], list[dict], set[str]]:
    dep = defaultdict(lambda: defaultdict(float))
    arr = defaultdict(lambda: defaultdict(float))
    periods = set()
    for r in rows:
        periods.add(r["FlightDate"][:7])
        origin, dest = r["Origin"], r["Dest"]
        cancelled = _flag(r["Cancelled"]) is True
        d = dep[origin]
        d["rows"] += 1
        d["cancelled"] += cancelled
        d["diverted"] += _flag(r["Diverted"]) is True
        if not cancelled:
            delayed = _flag(r["DepDel15"])
            if delayed is not None:
                d["depdel15_eligible"] += 1
                d["depdel15_delayed"] += delayed
            taxi = _num(r["TaxiOut"])
            if taxi is not None:
                d["taxi_out_n"] += 1
                d["taxi_out_sum_min"] += taxi
            delay = _num(r["DepDelay"])
            if delay is not None:
                d["dep_delay_n"] += 1
                d["dep_delay_sum_min"] += delay
        a = arr[dest]
        a["arr_rows"] += 1
        a["arr_cancelled"] += cancelled
        if not cancelled and _flag(r["ArrDel15"]) is True:
            a["arrdel15_delayed"] += 1
        for cause in CAUSES:
            minutes = _num(r.get(cause, ""))
            if minutes:
                a[f"{cause[: -len('Delay')].lower()}_delay_min"] += minutes

    def rows_out(agg, fields):
        out = []
        for airport in sorted(agg):
            rec = {"airport": airport}
            rec.update({f: round(agg[airport][f], 2) for f in fields[1:]})
            out.append(rec)
        return out

    return rows_out(dep, DEPARTURE_FIELDS), rows_out(arr, ARRIVAL_FIELDS), periods


def aggregate_zip(path: Path) -> tuple[list[dict], list[dict], set[str]]:
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"))
            return aggregate_rows(reader)
