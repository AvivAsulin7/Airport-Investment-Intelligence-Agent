"""FAA commercial-service enplanements (annual XLSX): airport metadata and regions.

Columns verified in Phase 2: Rank, RO (FAA region), ST, Locid, City, Airport Name,
S/L (service level), Hub, CY <yy> Enplanements, CY <yy> Enplanements, % Change.
Parsed with the standard library (no openpyxl dependency).
"""

import re
import zipfile
from pathlib import Path

URL = (
    "https://www.faa.gov/airports/planning_capacity/passenger_allcargo_stats/passenger/"
    "arp-cy2025-commercial-service-enplanements.xlsx"
)
LIMITATIONS = (
    "Annual calendar-year enplanements; FAA region (RO) and state (ST) are used for regional filtering.",
    "Locid is the FAA location identifier; for commercial airports it normally equals the IATA code used by BTS.",
)
FIELDS = [
    "code",
    "name",
    "city",
    "state",
    "faa_region",
    "service_level",
    "hub",
    "enplanements_current",
    "enplanements_prior",
]


def _cells(row_xml: str, strings: list[str]) -> dict[str, str]:
    out = {}
    for ref, attrs, inner in re.findall(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', row_xml, re.S):
        v = re.search(r"<v>([^<]*)</v>", inner or "")
        text = v.group(1) if v else "".join(re.findall(r"<t[^>]*>([^<]*)</t>", inner or ""))
        if 't="s"' in attrs and text:
            text = strings[int(text)]
        out[ref] = text
    return out


def read_xlsx_rows(path: Path) -> list[list[str]]:
    """Rows of the first worksheet as lists of strings (shared and inline strings supported)."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        strings = []
        if "xl/sharedStrings.xml" in names:
            sst = z.read("xl/sharedStrings.xml").decode("utf8")
            strings = ["".join(re.findall(r"<t[^>]*>([^<]*)</t>", si)) for si in re.findall(r"<si>(.*?)</si>", sst, re.S)]
        sheet = z.read("xl/worksheets/sheet1.xml").decode("utf8")
    rows = []
    for row_xml in re.findall(r"<row[^>]*>(.*?)</row>", sheet, re.S):
        cells = _cells(row_xml, strings)
        if not cells:
            continue
        cols = sorted(cells, key=lambda c: (len(c), c))
        width = _col_index(cols[-1]) + 1
        row = [""] * width
        for ref, val in cells.items():
            row[_col_index(ref)] = val
        rows.append(row)
    return rows


def _col_index(ref: str) -> int:
    n = 0
    for ch in ref:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def parse_enplanements(rows: list[list[str]]) -> tuple[list[dict], dict]:
    """Return airport records and metadata (which calendar years the two columns hold)."""
    header = rows[0]
    idx = {h.strip(): i for i, h in enumerate(header)}
    required = ["RO", "ST", "Locid", "City", "Airport Name", "S/L", "Hub"]
    missing = [r for r in required if r not in idx]
    year_cols = [h for h in idx if re.fullmatch(r"CY \d{2} Enplanements", h)]
    if missing or len(year_cols) != 2:
        raise ValueError(f"unexpected FAA enplanements header: missing={missing}, year_cols={year_cols}")
    current, prior = sorted(year_cols, reverse=True)
    records = []
    for row in rows[1:]:
        cell = lambda name: row[idx[name]].strip() if idx[name] < len(row) else ""
        code = cell("Locid")
        if not re.fullmatch(r"[A-Z0-9]{3}", code):
            continue
        records.append(
            {
                "code": code,
                "name": cell("Airport Name"),
                "city": cell("City"),
                "state": cell("ST"),
                "faa_region": cell("RO"),
                "service_level": cell("S/L"),
                "hub": "" if cell("Hub") == "None" else cell("Hub"),
                "enplanements_current": cell(current),
                "enplanements_prior": cell(prior),
            }
        )
    meta = {"current_year": f"20{current[3:5]}", "prior_year": f"20{prior[3:5]}"}
    return records, meta
