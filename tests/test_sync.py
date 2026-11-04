from datetime import datetime

from sqlalchemy import func, select

from inboxtriage.core.db import get_engine
from inboxtriage.core.models import Base, Message


def test_upsert_logic_reuses_same_message_id():
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(
            Message.__table__.insert(),
            {
                "gmail_id": "abc123",
                "thread_id": "t1",
                "sender": "user@example.com",
                "subject": "Hello",
                "body": "Body",
                "received_at": datetime(2026, 1, 1, 0, 0, 0),
                "raw_labels": "[\"inbox\"]",
            },
        )

    with engine.begin() as conn:
        count_before = conn.execute(
            select(func.count()).select_from(Message).where(Message.gmail_id == "abc123")
        ).scalar_one()
        assert count_before == 1

    with engine.begin() as conn:
        count_after = conn.execute(
            select(func.count()).select_from(Message).where(Message.gmail_id == "abc123")
        ).scalar_one()
        assert count_after == 1
