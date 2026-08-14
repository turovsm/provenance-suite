from datetime import date

from src.cli.seed_events import (
    derive_full_name,
    parse_date_component,
    parse_event_value,
)


def test_parse_date_component_single_date() -> None:
    s, e, d = parse_date_component("2024.08.15")
    assert s == "2024-08-15"
    assert e == "2024-08-15"
    assert d == date(2024, 8, 15)


def test_parse_date_component_compact_range() -> None:
    s, e, d = parse_date_component("2015.08.1416")
    assert s == "2015-08-14"
    assert e == "2015-08-16"
    assert d == date(2015, 8, 14)


def test_parse_date_component_hyphenated_days() -> None:
    s, e, d = parse_date_component("2015.08.14-16")
    assert s == "2015-08-14"
    assert e == "2015-08-16"


def test_parse_date_component_cross_month() -> None:
    s, e, d = parse_date_component("2020.04.29-05.06")
    assert s == "2020-04-29"
    assert e == "2020-05-06"
    assert d == date(2020, 4, 29)


def test_parse_date_component_fuzzy_xx() -> None:
    s, e, d = parse_date_component("1998.08.xx")
    assert s == "1998-08-xx"
    assert e == "1998-08-xx"
    assert d == date(1998, 8, 1)


def test_parse_event_value_timeline_arrow() -> None:
    raw = "2020.05.02-05.05 (Cancelled) -> 2021.05.02-05.04"
    s, e, orig_s, orig_e, history, add_dates, status, sort_d = parse_event_value(raw)

    assert status == "HELD"
    assert s == "2021-05-02"
    assert e == "2021-05-04"
    assert orig_s == "2020-05-02"
    assert orig_e == "2020-05-05"
    assert len(history) == 2


def test_parse_event_value_non_numeric() -> None:
    s, e, _, _, _, _, status, sort_d = parse_event_value("TBA / Unknown")
    assert status == "UNKNOWN"
    assert s is None

    s, e, _, _, _, _, status, sort_d = parse_event_value("Cancelled")
    assert status == "CANCELLED"


def test_derive_full_name() -> None:
    assert derive_full_name("Comic Market", "C100") == "Comic Market (C100)"
    assert derive_full_name("M3 / Music Media-Mix", "M3-2024") == "M3 (M3-2024)"
    assert derive_full_name("M3 / Music Media-Mix", "M3") == "M3"
