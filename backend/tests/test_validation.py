import pytest

from app.data.validation import (
    DataValidationError,
    month_range,
    shift_month,
    validate_airport_codes,
    validate_service_classes,
)


def test_airport_codes_are_normalized_and_deduplicated():
    assert validate_airport_codes(["lax", " SNA", "LAX"]) == ["LAX", "SNA"]


@pytest.mark.parametrize("bad", ["LA", "LAXX", "LA'", "LAX;DROP", "", "l@x"])
def test_invalid_airport_codes_are_rejected(bad):
    with pytest.raises(DataValidationError):
        validate_airport_codes([bad])


def test_empty_and_oversized_code_lists_are_rejected():
    with pytest.raises(DataValidationError):
        validate_airport_codes([])
    with pytest.raises(DataValidationError):
        validate_airport_codes([f"A{i:02d}" for i in range(31)])


def test_month_helpers():
    assert shift_month("2026-01", -1) == "2025-12"
    assert shift_month("2025-08", 11) == "2026-07"
    assert month_range("2025-11", "2026-02") == ["2025-11", "2025-12", "2026-01", "2026-02"]
    assert len(month_range("2024-08", "2026-07")) == 24


@pytest.mark.parametrize("start,end", [("2026-07", "2026-06"), ("2026-13", "2026-12"), ("26-07", "2026-07")])
def test_invalid_month_ranges(start, end):
    with pytest.raises(DataValidationError):
        month_range(start, end)


def test_service_classes_must_be_explicit_and_known():
    assert validate_service_classes(["f", "L"]) == frozenset({"F", "L"})
    with pytest.raises(DataValidationError):
        validate_service_classes([])
    with pytest.raises(DataValidationError):
        validate_service_classes(["F", "X"])
