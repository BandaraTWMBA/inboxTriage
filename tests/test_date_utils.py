from datetime import date

from inboxtriage.date_utils import normalize_deadline

REF = date(2024, 11, 6)  # a Wednesday


def test_already_iso():
    assert normalize_deadline("2024-12-25", REF) == "2024-12-25"


def test_today():
    assert normalize_deadline("today", REF) == "2024-11-06"


def test_tomorrow():
    assert normalize_deadline("tomorrow", REF) == "2024-11-07"


def test_next_friday():
    # REF is Wed Nov 6 → next Friday = Nov 15 (skip this Fri Nov 8)
    assert normalize_deadline("next Friday", REF) == "2024-11-15"


def test_this_friday():
    assert normalize_deadline("this Friday", REF) == "2024-11-08"


def test_bare_weekday():
    # bare "Monday" → upcoming Monday = Nov 11
    assert normalize_deadline("Monday", REF) == "2024-11-11"


def test_in_3_days():
    assert normalize_deadline("in 3 days", REF) == "2024-11-09"


def test_in_2_weeks():
    assert normalize_deadline("in 2 weeks", REF) == "2024-11-20"


def test_month_day():
    assert normalize_deadline("November 15th", REF) == "2024-11-15"


def test_past_month_wraps_year():
    # Oct 1 is already past Nov 6 → wraps to 2025
    assert normalize_deadline("October 1st", REF) == "2025-10-01"


def test_none_returns_none():
    assert normalize_deadline(None, REF) is None


def test_empty_returns_none():
    assert normalize_deadline("", REF) is None


def test_unparseable_returns_none():
    assert normalize_deadline("sometime soon", REF) is None

