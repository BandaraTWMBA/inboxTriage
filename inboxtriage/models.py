from __future__ import annotations

<<<<<<< Updated upstream
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
=======
import json
from datetime import date, datetime
from typing import Optional

from sqlalchemy import DateTime, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
>>>>>>> Stashed changes


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gmail_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    raw_labels: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
<<<<<<< Updated upstream
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
=======
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ── Feature 02: relationship to classifications ──
    classifications: Mapped[list["Classification"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


# ─────────────────────────────────────────────────────────────
# Feature 02 — Classification Agent
# ─────────────────────────────────────────────────────────────
class Classification(Base):
    __tablename__ = "classifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    # choices: urgent_action | fyi | can_wait | low_priority
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    extracted_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    extracted_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ↑ stored as JSON string: '["Reply", "Attach invoice"]'
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    message: Mapped["Message"] = relationship(back_populates="classifications")
>>>>>>> Stashed changes
