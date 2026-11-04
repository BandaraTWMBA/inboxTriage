from unittest.mock import MagicMock

import inboxtriage.classification.label_manager as ls


def _mock_service(existing_labels: dict, msg_labels: list):
    svc = MagicMock()

    svc.users().labels().list().execute.return_value = {
        "labels": [{"name": n, "id": i} for n, i in existing_labels.items()]
    }
    svc.users().messages().get().execute.return_value = {"labelIds": msg_labels}
    svc.users().messages().modify().execute.return_value = {}

    return svc


ALL_LABELS = {
    "InboxTriage/FYI": "LBL_FYI",
    "InboxTriage/Urgent": "LBL_URG",
    "InboxTriage/Can-Wait": "LBL_CW",
    "InboxTriage/Low-Priority": "LBL_LP",
}


def test_removes_old_label_and_adds_new():
    ls._label_id_cache = {}

    svc = _mock_service(ALL_LABELS, msg_labels=["LBL_FYI", "INBOX"])

    ok = ls.apply_label(svc, "msg_001", "urgent_action")
    assert ok is True

    body = svc.users().messages().modify.call_args[1]["body"]
    assert "LBL_URG" in body["addLabelIds"]
    assert "LBL_FYI" in body["removeLabelIds"]


def test_no_prior_label():
    ls._label_id_cache = {}

    svc = _mock_service(ALL_LABELS, msg_labels=["INBOX", "UNREAD"])

    ok = ls.apply_label(svc, "msg_002", "fyi")
    assert ok is True

    body = svc.users().messages().modify.call_args[1]["body"]
    assert "LBL_FYI" in body["addLabelIds"]
    assert not body.get("removeLabelIds")
