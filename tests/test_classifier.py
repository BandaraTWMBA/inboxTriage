from datetime import date
from unittest.mock import patch

from inboxtriage.classification.agent import classify_email


def _raw(cat="fyi", conf=0.9, deadline=None, actions=None, reasoning="test"):
    return {
        "category": cat,
        "confidence": conf,
        "extracted_deadline": deadline,
        "action_items": actions or [],
        "reasoning": reasoning,
    }


def test_happy_path():
    with patch("inboxtriage.classification.agent._call_gemini", return_value=_raw("fyi")):
        r = classify_email("id1", "a@b.com", "Hi", "Hello")
    assert r is not None
    assert r.category == "fyi"


def test_retry_on_bad_category():
    with patch(
        "inboxtriage.classification.agent._call_gemini",
        side_effect=[_raw("spam"), _raw("low_priority")],
    ):
        r = classify_email("id2", "a@b.com", "Subj", "Body")
    assert r is not None
    assert r.category == "low_priority"


def test_double_failure_returns_none():
    with patch("inboxtriage.classification.agent._call_gemini", return_value=_raw("spam")):
        r = classify_email("id3", "a@b.com", "Subj", "Body")
    assert r is None


def test_very_short_email():
    with patch("inboxtriage.classification.agent._call_gemini", return_value=_raw("fyi")):
        r = classify_email("id4", "x@y.com", "Thanks!", "Thanks!")
    assert r is not None


def test_deadline_gets_normalized():
    with patch(
        "inboxtriage.classification.agent._call_gemini",
        return_value=_raw("urgent_action", deadline="tomorrow"),
    ):
        r = classify_email(
            "id5", "boss@co.com", "Urgent", "Reply by tomorrow",
            reference_date=date(2024, 11, 6),
        )
    assert r is not None
    assert r.extracted_deadline == "2024-11-07"
