from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from inboxtriage.db import get_session, init_db
from inboxtriage.gmail_client import list_recent_messages
from inboxtriage.models import Message


def upsert_message(session, payload: dict) -> Message:
    stmt = sqlite_insert(Message).values(
        gmail_id=payload["gmail_id"],
        thread_id=payload.get("thread_id"),
        sender=payload.get("sender"),
        subject=payload.get("subject"),
        body=payload.get("body"),
        received_at=payload.get("received_at"),
        raw_labels=payload.get("raw_labels"),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Message.gmail_id],
        set_=dict(
            thread_id=payload.get("thread_id"),
            sender=payload.get("sender"),
            subject=payload.get("subject"),
            body=payload.get("body"),
            received_at=payload.get("received_at"),
            raw_labels=payload.get("raw_labels"),
        ),
    )
    session.execute(stmt)
    return session.scalar(select(Message).where(Message.gmail_id == payload["gmail_id"]))


def sync_recent_messages(lookback_days: int = 1, max_results: int = 20):
    init_db()
    service = None
    try:
        from inboxtriage.auth import build_gmail_service
        service = build_gmail_service()
    except Exception:
        service = None

    if service is None:
        raise RuntimeError("Gmail service could not be initialized. Check credentials and OAuth flow.")

    session = get_session()
    try:
        messages = list_recent_messages(service=service, lookback_days=lookback_days, max_results=max_results)
        for message in messages:
            if not message.get("gmail_id"):
                continue
            upsert_message(session, message)
        session.commit()
        return len(messages)
    finally:
        session.close()


if __name__ == "__main__":
    count = sync_recent_messages()
    print(f"Synced {count} messages")
