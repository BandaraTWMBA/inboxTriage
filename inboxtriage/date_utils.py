"""
Normalizes relative date expressions from the LLM into ISO 8601 strings.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

_WEEKDAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_MONTH_DAY_RE = re.compile(
    r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+(\d{1,2})(?:st|nd|rd|th)?",
    re.IGNORECASE,
)

_MONTH_NUM = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def normalize_deadline(
    raw: Optional[str],
    reference: Optional[date] = None,
) -> Optional[str]:
    """
    Convert a raw date expression to ISO 8601 (YYYY-MM-DD).

    Args:
        raw:       The LLM's extracted_deadline string.
        reference: "Today" for relative dates. Defaults to date.today().
                   Pass a fixed date in tests for determinism.

    Returns:
        ISO date string, or None if input is empty/unparseable.
    """
    if not raw:
        return None

    raw = raw.strip()
    today = reference or date.today()

    # Already ISO
    if _ISO_RE.match(raw):
        try:
            date.fromisoformat(raw)
            return raw
        except ValueError:
            return None

    lower = raw.lower()

    # today / tonight
    if lower in ("today", "tonight"):
        return today.isoformat()

    # tomorrow
    if lower == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    # yesterday
    if lower == "yesterday":
        return (today - timedelta(days=1)).isoformat()

    # "next <weekday>" / "this <weekday>" / bare "<weekday>"
    for prefix in ("next ", "this ", ""):
        for name, num in _WEEKDAY_MAP.items():
            if lower == f"{prefix}{name}".strip():
                days_ahead = (num - today.weekday()) % 7
                if prefix == "next ":
                    # "next <weekday>" means the following week's instance
                    days_ahead += 7
                elif days_ahead == 0 and prefix in ("next ", ""):
                    days_ahead = 7
                return (today + timedelta(days=days_ahead)).isoformat()

    # "in N days/weeks"
    m = re.match(r"in\s+(\d+)\s+(day|days|week|weeks)", lower)
    if m:
        n = int(m.group(1))
        delta = timedelta(days=n) if "day" in m.group(2) else timedelta(weeks=n)
        return (today + delta).isoformat()

    # "Month Day" — e.g. "November 15th", "Nov 15"
    m = _MONTH_DAY_RE.search(lower)
    if m:
        month_str = m.group(1)[:3].lower()
        day_num = int(m.group(2))
        month_num = _MONTH_NUM.get(month_str)
        if month_num:
            try:
                candidate = date(today.year, month_num, day_num)
            except ValueError:
                return None
            if (candidate - today).days < -1:
                candidate = date(today.year + 1, month_num, day_num)
            return candidate.isoformat()

    # Unparseable — return None, never hallucinate a date
    return None

