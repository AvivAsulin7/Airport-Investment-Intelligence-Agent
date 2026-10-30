"""Input validation shared by the data sources: airport codes, months, service classes."""

import re

AIRPORT_CODE_RE = re.compile(r"^[A-Z0-9]{3}$")
MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
MAX_AIRPORTS = 30

# T-100 service classes (eCFR 14 CFR 291.45; data-sources-research.md §2.2).
SERVICE_CLASSES = {
    "F": "scheduled passenger/cargo",
    "G": "scheduled all-cargo",
    "L": "non-scheduled passenger/cargo",
    "P": "non-scheduled all-cargo",
}
PASSENGER_CLASSES = frozenset({"F", "L"})
CARGO_ONLY_CLASSES = frozenset({"G", "P"})


class DataValidationError(ValueError):
    """Invalid input to the data layer (bad code, month, class, ...)."""


def validate_airport_codes(codes: list[str]) -> list[str]:
    if not codes:
        raise DataValidationError("at least one airport code is required")
    cleaned = []
    for code in codes:
        c = str(code).strip().upper()
        if not AIRPORT_CODE_RE.match(c):
            raise DataValidationError(f"invalid airport code: {code!r}")
        if c not in cleaned:
            cleaned.append(c)
    if len(cleaned) > MAX_AIRPORTS:
        raise DataValidationError(f"at most {MAX_AIRPORTS} airports per request")
    return cleaned


def parse_month(month: str) -> tuple[int, int]:
    m = MONTH_RE.match(month or "")
    if not m:
        raise DataValidationError(f"invalid month {month!r}; expected YYYY-MM")
    return int(m.group(1)), int(m.group(2))


def shift_month(month: str, delta: int) -> str:
    y, m = parse_month(month)
    idx = y * 12 + (m - 1) + delta
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def month_range(start: str, end: str) -> list[str]:
    """Inclusive list of YYYY-MM months from start to end."""
    sy, sm = parse_month(start)
    ey, em = parse_month(end)
    n = (ey * 12 + em) - (sy * 12 + sm)
    if n < 0:
        raise DataValidationError(f"start month {start} is after end month {end}")
    return [shift_month(start, i) for i in range(n + 1)]


def validate_service_classes(classes: list[str] | set[str] | frozenset[str]) -> frozenset[str]:
    """Classes must be given explicitly so passenger and cargo are never mixed silently."""
    if not classes:
        raise DataValidationError("service classes must be specified explicitly")
    cleaned = frozenset(str(c).strip().upper() for c in classes)
    unknown = cleaned - SERVICE_CLASSES.keys()
    if unknown:
        raise DataValidationError(f"unknown service classes: {sorted(unknown)}; allowed: {sorted(SERVICE_CLASSES)}")
    return cleaned
