from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from inboxtriage.digest import (
    DigestItem,
    DigestData,
    fetch_digest_data,
    generate_natural_overview,
    generate_digest_markdown,
)
from inboxtriage.digest_delivery import deliver_to_file
from inboxtriage.models import Base, Classification, Message


def test_empty_digest_handling():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        data = fetch_digest_data(session=session, hours=24)
        assert data.total_count == 0
        md = generate_digest_markdown(data)
        assert "All clear. No classified emails arrived" in md


def test_digest_grouping_and_latest_classification(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc)

    with Session(engine) as session:
        m1 = Message(
            gmail_id="m1",
            sender="boss@corp.com",
            subject="Sign contract ASAP",
            created_at=now - timedelta(hours=2),
        )
        m2 = Message(
            gmail_id="m2",
            sender="colleague@corp.com",
            subject="FYI Team Lunch notes",
            created_at=now - timedelta(hours=3),
        )
        session.add_all([m1, m2])
        session.commit()

        # m1 has two classifications; only the latest should appear
        c1_old = Classification(
            message_id=m1.id,
            category="can_wait",
            confidence=0.6,
            reasoning="Initial thought",
            prompt_version="v1",
            created_at=now.replace(tzinfo=None) - timedelta(hours=3),
        )
        c1_new = Classification(
            message_id=m1.id,
            category="urgent_action",
            confidence=0.95,
            extracted_deadline=date(2026, 11, 5),
            extracted_actions=json.dumps(["Review contract", "Sign"]),
            reasoning="Legal requirement with strict deadline",
            prompt_version="v1",
            created_at=now.replace(tzinfo=None) - timedelta(hours=1),
        )
        c2 = Classification(
            message_id=m2.id,
            category="fyi",
            confidence=0.8,
            reasoning="Informational only",
            prompt_version="v1",
            created_at=now.replace(tzinfo=None) - timedelta(hours=2),
        )
        session.add_all([c1_old, c1_new, c2])
        session.commit()

        data = fetch_digest_data(session=session, hours=24, now=now)
        assert data.total_count == 2
        assert len(data.items_by_category["urgent_action"]) == 1
        assert len(data.items_by_category["fyi"]) == 1
        assert len(data.items_by_category["can_wait"]) == 0

        urgent_item = data.items_by_category["urgent_action"][0]
        assert urgent_item.subject == "Sign contract ASAP"
        assert urgent_item.deadline == "2026-11-05"
        assert "Review contract" in urgent_item.actions

        md = generate_digest_markdown(data)
        assert "1 email needing urgent attention, 1 FYI." in md
        assert "## 🚨 Urgent Action (1)" in md
        assert "## ℹ️ FYI (1)" in md
        assert "Sign contract ASAP" in md
        assert "Review contract" in md

        # Test delivery to file
        target = tmp_path / "test_digest.md"
        out_path = deliver_to_file(md, str(target))
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == md

