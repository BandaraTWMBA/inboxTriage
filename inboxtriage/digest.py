"""
Digest generation service: collects classified messages from the last 24h,
groups by category, and creates natural-language Markdown summaries.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from inboxtriage.models import Classification, Message


CATEGORY_ORDER = ["urgent_action", "can_wait", "fyi", "low_priority"]
CATEGORY_LABELS = {
    "urgent_action": "🚨 Urgent Action",
    "can_wait": "⏳ Can Wait",
    "fyi": "ℹ️ FYI",
    "low_priority": "💤 Low Priority",
}


@dataclass
class DigestItem:
    message_id: int
    gmail_id: str
    sender: str
    subject: str
    category: str
    confidence: float
    reasoning: str
    deadline: Optional[str] = None
    actions: list[str] = field(default_factory=list)


@dataclass
class DigestData:
    start_time: datetime
    end_time: datetime
    items_by_category: dict[str, list[DigestItem]]
    total_count: int


def fetch_digest_data(session: Session, hours: int = 24, now: Optional[datetime] = None) -> DigestData:
    """
    Fetch classifications from the last `hours` (default 24h).
    If a message has multiple classifications, picks the latest one.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    # Subquery / query all classifications created or associated within cutoff
    # Handling both timezone-aware and naive datetimes safely
    cutoff_naive = cutoff.replace(tzinfo=None)

    stmt = (
        select(Classification, Message)
        .join(Message, Classification.message_id == Message.id)
        .where(Classification.created_at >= cutoff_naive)
        .order_by(desc(Classification.created_at))
    )
    rows = session.execute(stmt).all()

    # Deduplicate by message_id taking the most recent classification
    seen_messages = set()
    items_by_category: dict[str, list[DigestItem]] = {cat: [] for cat in CATEGORY_ORDER}

    for classification, message in rows:
        if classification.message_id in seen_messages:
            continue
        seen_messages.add(classification.message_id)

        actions: list[str] = []
        if classification.extracted_actions:
            try:
                parsed = json.loads(classification.extracted_actions)
                if isinstance(parsed, list):
                    actions = [str(x) for x in parsed]
                elif isinstance(parsed, str):
                    actions = [parsed]
            except Exception:
                actions = [classification.extracted_actions]

        deadline_str = (
            classification.extracted_deadline.isoformat()
            if classification.extracted_deadline
            else None
        )

        item = DigestItem(
            message_id=message.id,
            gmail_id=message.gmail_id,
            sender=message.sender or "Unknown Sender",
            subject=message.subject or "(no subject)",
            category=classification.category,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            deadline=deadline_str,
            actions=actions,
        )

        if item.category in items_by_category:
            items_by_category[item.category].append(item)
        else:
            items_by_category.setdefault(item.category, []).append(item)

    total_count = len(seen_messages)
    return DigestData(
        start_time=cutoff,
        end_time=now,
        items_by_category=items_by_category,
        total_count=total_count,
    )


def generate_natural_overview(items_by_category: dict[str, list[DigestItem]]) -> str:
    """Generate a short, readable natural-language framing sentence."""
    urgent = len(items_by_category.get("urgent_action", []))
    can_wait = len(items_by_category.get("can_wait", []))
    fyi = len(items_by_category.get("fyi", []))
    low = len(items_by_category.get("low_priority", []))

    parts = []
    if urgent > 0:
        parts.append(f"{urgent} email{'s' if urgent > 1 else ''} needing urgent attention")
    if can_wait > 0:
        parts.append(f"{can_wait} that can wait")
    if fyi > 0:
        parts.append(f"{fyi} FYI")
    if low > 0:
        parts.append(f"{low} low-priority/marketing")

    if not parts:
        return "You're all caught up! No classified emails arrived in the last 24 hours."

    return "Today's summary: " + ", ".join(parts) + "."


def generate_digest_markdown(digest_data: DigestData) -> str:
    """Format DigestData into clear Markdown."""
    lines: list[str] = []
    date_str = digest_data.end_time.strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"# 📬 InboxTriage Daily Digest — {date_str}")
    lines.append("")

    if digest_data.total_count == 0:
        lines.append("> **Status:** All clear. No classified emails arrived in the last 24 hours.")
        return "\n".join(lines) + "\n"

    lines.append(f"> {generate_natural_overview(digest_data.items_by_category)}")
    lines.append("")

    for cat in CATEGORY_ORDER:
        items = digest_data.items_by_category.get(cat, [])
        if not items:
            continue

        label = CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())
        lines.append(f"## {label} ({len(items)})")
        lines.append("")

        for item in items:
            lines.append(f"- **{item.subject}**")
            lines.append(f"  - **From:** `{item.sender}`")
            if item.deadline:
                lines.append(f"  - ⏰ **Deadline:** `{item.deadline}`")
            if item.actions:
                actions_str = ", ".join(item.actions)
                lines.append(f"  - 🎯 **Action items:** {actions_str}")
            if item.reasoning:
                lines.append(f"  - 💡 *{item.reasoning}*")
            lines.append("")

    return "\n".join(lines)

