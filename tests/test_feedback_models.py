from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from inboxtriage.models import Base, Message, Classification, UserFeedback
from inboxtriage.schemas import FeedbackCreate, FeedbackRead


def test_user_feedback_table_and_relationships():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        msg = Message(
            gmail_id="msg_feedback_001",
            subject="Invoice for review",
            sender="billing@company.com",
            body="Please see invoice attached.",
            received_at=datetime.utcnow(),
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)

        feedback_in = FeedbackCreate(
            message_id=msg.id,
            predicted_category="urgent_action",
            corrected_category="can_wait",
        )

        fb = UserFeedback(
            message_id=feedback_in.message_id,
            predicted_category=feedback_in.predicted_category,
            corrected_category=feedback_in.corrected_category,
        )
        session.add(fb)
        session.commit()
        session.refresh(fb)

        # Test Pydantic validation
        fb_read = FeedbackRead.model_validate(fb)
        assert fb_read.id == fb.id
        assert fb_read.message_id == msg.id
        assert fb_read.predicted_category == "urgent_action"
        assert fb_read.corrected_category == "can_wait"

        # Test relationship
        session.refresh(msg)
        assert len(msg.feedback) == 1
        assert msg.feedback[0].corrected_category == "can_wait"
        assert msg.feedback[0].message.gmail_id == "msg_feedback_001"

