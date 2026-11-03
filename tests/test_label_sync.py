"""Tests for label application — mock Gmail API."""
from unittest.mock import MagicMock

import inboxtriage.label_sync as ls


def _mock_service(existing_labels: dict, msg_labels: list):
    """Create a mock Gmail service with pre-set labels and message state."""
    svc = MagicMock()

    # users().labels().list()
    svc.users().labels().list().execute.return_value = {
        "labels": [{"name": n, "id": i} for n, i in existing_labels.items()]
    }

    # users().messages().get()
    svc.users().messages().get().execute.return_value = {"labelIds": msg_labels}

    # users().messages().modify() — just succeed
    svc.users().messages().modify().execute.return_value = {}

    return svc


ALL_LABELS = {
    "InboxTriage/FYI": "LBL_FYI",
    "InboxTriage/Urgent": "LBL_URG",
    "InboxTriage/Can-Wait": "LBL_CW",
    "InboxTriage/Low-Priority": "LBL_LP",
}


def test_removes_old_label_and_adds_new():
    """Message has FYI → reclassified to urgent_action → old removed, new added."""
    ls._label_id_cache = {}  # reset cache

    svc = _mock_service(ALL_LABELS, msg_labels=["LBL_FYI", "INBOX"])

    ok = ls.apply_label(svc, "msg_001", "urgent_action")
    assert ok is True

    body = svc.users().messages().modify.call_args[1]["body"]
    assert "LBL_URG" in body["addLabelIds"]
    assert "LBL_FYI" in body["removeLabelIds"]


def test_no_prior_label():
    """Message has no InboxTriage labels → only add, no remove."""
    ls._label_id_cache = {}

    svc = _mock_service(ALL_LABELS, msg_labels=["INBOX", "UNREAD"])

    ok = ls.apply_label(svc, "msg_002", "fyi")
    assert ok is True

    body = svc.users().messages().modify.call_args[1]["body"]
    assert "LBL_FYI" in body["addLabelIds"]
    assert not body.get("removeLabelIds")

