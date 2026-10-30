"""Parsers for the supplementary public files, on tiny synthetic fixtures (no downloads)."""

import zipfile

from app.data.sources import bts_ontime, bts_t100, faa_enplanements


def _ontime(origin="AAA", dest="BBB", cancelled="0.00", diverted="0.00", depdel15="0.00", taxi="10.00",
            depdelay="-2.00", arrdel15="0.00", nas=""):
    return {
        "FlightDate": "2026-07-01", "Origin": origin, "Dest": dest, "Cancelled": cancelled, "Diverted": diverted,
        "DepDel15": depdel15, "TaxiOut": taxi, "DepDelay": depdelay, "ArrDel15": arrdel15,
        "CarrierDelay": "", "WeatherDelay": "", "NASDelay": nas, "SecurityDelay": "", "LateAircraftDelay": "",
    }


def test_ontime_departure_counts_follow_p029_definitions():
    rows = [
        _ontime(depdel15="1.00", taxi="20.00", depdelay="30.00"),
        _ontime(depdel15="0.00"),
        _ontime(cancelled="1.00", depdel15="", taxi="", depdelay=""),
        _ontime(cancelled="1.00", depdel15="1.00"),  # cancelled with a DepDel15 value: excluded
        _ontime(diverted="1.00", depdel15="1.00"),  # diverted departed: included
    ]

    dep, _, periods = bts_ontime.aggregate_rows(rows)

    [a] = dep
    assert periods == {"2026-07"}
    assert a["rows"] == 5 and a["cancelled"] == 2 and a["diverted"] == 1
    assert a["depdel15_eligible"] == 3 and a["depdel15_delayed"] == 2
    assert a["taxi_out_n"] == 3 and a["taxi_out_sum_min"] == 40.0


def test_ontime_arrival_causes_are_keyed_by_destination():
    _, arr, _ = bts_ontime.aggregate_rows([_ontime(arrdel15="1.00", nas="45.00"), _ontime(dest="CCC")])

    by = {r["airport"]: r for r in arr}
    assert by["BBB"]["arrdel15_delayed"] == 1 and by["BBB"]["nas_delay_min"] == 45.0
    assert by["CCC"]["arr_rows"] == 1


def _t100(origin="AAA", dest="BBB", cls="F", dist="3100", performed="10", seats="1000", pax="800"):
    return {
        "YEAR": "2026", "MONTH": "7", "ORIGIN": origin, "DEST": dest, "DEST_COUNTRY": "US", "CLASS": cls,
        "DEPARTURES_SCHEDULED": performed, "DEPARTURES_PERFORMED": performed, "SEATS": seats,
        "PASSENGERS": pax, "FREIGHT": "0", "DISTANCE": dist,
    }


def test_t100_aggregates_over_carriers_and_keeps_classes_separate():
    rows = [_t100(), _t100(performed="5"), _t100(cls="G", performed="7", seats="0", pax="0")]

    segs, periods, warnings = bts_t100.aggregate_rows(rows)

    assert periods == {"2026-07"} and not warnings
    by_class = {s["service_class"]: s for s in segs}
    assert by_class["F"]["departures_performed"] == 15 and by_class["F"]["distance_miles"] == 3100
    assert by_class["G"]["departures_performed"] == 7


def test_t100_flags_inconsistent_distances():
    _, _, warnings = bts_t100.aggregate_rows([_t100(dist="3100"), _t100(cls="L", dist="3200")])
    assert warnings == ["inconsistent distance for AAA-BBB"]


def _xlsx(path, rows):
    strings, sheet_rows = [], []
    for r_i, row in enumerate(rows, start=1):
        cells = []
        for c_i, val in enumerate(row):
            ref = f"{chr(65 + c_i)}{r_i}"
            if isinstance(val, str):
                strings.append(val)
                cells.append(f'<c r="{ref}" t="s"><v>{len(strings) - 1}</v></c>')
            else:
                cells.append(f'<c r="{ref}"><v>{val}</v></c>')
        sheet_rows.append(f'<row r="{r_i}">{"".join(cells)}</row>')
    sst = "".join(f"<si><t>{s}</t></si>" for s in strings)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/sharedStrings.xml", f"<sst>{sst}</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f"<worksheet><sheetData>{''.join(sheet_rows)}</sheetData></worksheet>")


def test_faa_enplanements_parser_is_header_driven(tmp_path):
    header = ["Rank", "RO", "ST", "Locid", "City", "Airport Name", "S/L", "Hub", "CY 25 Enplanements",
              "CY 24 Enplanements", "% Change"]
    rows = [header, [1, "NE", "MA", "AAA", "Town", "Alpha Intl", "P", "M", 1000, 900, 0.11],
            [2, "NE", "VT", "BBB", "Village", "Beta Muni", "CS", "None", 50, 60, -0.16],
            ["", "", "", "Total", "", "", "", "", 1050, 960, ""]]
    path = tmp_path / "f.xlsx"
    _xlsx(path, rows)

    records, meta = faa_enplanements.parse_enplanements(faa_enplanements.read_xlsx_rows(path))

    assert meta == {"current_year": "2025", "prior_year": "2024"}
    assert [r["code"] for r in records] == ["AAA", "BBB"]
    assert records[0]["faa_region"] == "NE" and records[0]["enplanements_current"] == "1000"
    assert records[1]["hub"] == ""
