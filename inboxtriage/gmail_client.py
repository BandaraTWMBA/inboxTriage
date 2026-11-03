from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta
from typing import Any

from inboxtriage.auth import build_gmail_service
from inboxtriage.html_utils import strip_html


def parse_message_payload(message_detail: dict[str, Any]) -> dict[str, Any]:
    payload = message_detail.get("payload", {})
    headers = payload.get("headers", [])
    headers_map = {h.get("name", "").lower(): h.get("value", "") for h in headers if h.get("name")}

    body_parts: list[str] = []

    def collect_parts(part: dict[str, Any]):
        mime_type = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data")
        if data:
            raw = base64.urlsafe_b64decode(data + "==")
            text = raw.decode("utf-8", errors="replace")
            if mime_type.startswith("text/"):
                body_parts.append(text)
        for subpart in part.get("parts", []):
            collect_parts(subpart)

    for part in payload.get("parts", []):
        collect_parts(part)

    if not body_parts and payload.get("body", {}).get("data"):
        data = payload["body"]["data"]
        raw = base64.urlsafe_b64decode(data + "==")
        body_parts.append(raw.decode("utf-8", errors="replace"))

    message_text = "\n".join(body_parts)
    clean_body = strip_html(message_text)

    received_at = None
    internal_date = message_detail.get("internalDate")
    if internal_date:
        try:
            received_at = datetime.fromtimestamp(int(internal_date) / 1000)
        except (TypeError, ValueError):
            received_at = None

    return {
        "gmail_id": message_detail.get("id"),
        "thread_id": message_detail.get("threadId"),
        "sender": headers_map.get("from") or headers_map.get("sender") or "unknown",
        "subject": headers_map.get("subject") or "",
        "body": clean_body,
        "received_at": received_at,
        "raw_labels": json.dumps(message_detail.get("labelIds", [])),
    }


def list_recent_messages(service=None, lookback_days: int = 1, max_results: int = 20):
    service = service or build_gmail_service()
    now = datetime.utcnow()
    query = f"after:{int((now - timedelta(days=lookback_days)).timestamp())}"
    response = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = response.get("messages", [])
    results = []
    for msg in messages:
        detail = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        results.append(parse_message_payload(detail))
    return results
