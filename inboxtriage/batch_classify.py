"""
Classify all unclassified messages, store results, apply Gmail labels.

Usage:
    python -m inboxtriage.batch_classify
    python -m inboxtriage.batch_classify --dry-run
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import date

from sqlalchemy import exists, not_, select

from inboxtriage.auth import build_gmail_service
from inboxtriage.classifier import classify_email
from inboxtriage.db import get_session_factory, init_db
from inboxtriage.label_sync import apply_label, ensure_labels_exist
from inboxtriage.models import Classification, Message
from inboxtriage.schemas import PROMPT_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("batch_classify")


def run_batch(dry_run: bool = False) -> None:
    init_db()  # ensure Classification table exists
    SessionFactory = get_session_factory()

    # Build Gmail service (needed for label sync)
    gmail_service = None
    if not dry_run:
        gmail_service = build_gmail_service()
        ensure_labels_exist(gmail_service)

    # ── Find unclassified messages ────────────────────────────
    with SessionFactory() as session:
        stmt = select(Message).where(
            not_(
                exists(
                    select(Classification.id).where(
                        Classification.message_id == Message.id
                    )
                )
            )
        )
        messages = session.scalars(stmt).all()
        # Detach from session — we'll use separate sessions per write
        messages = list(messages)

    logger.info("Found %d unclassified messages.", len(messages))

    success = 0
    failed = 0

    for msg in messages:
        logger.info("Classifying: gmail_id=%s  subject=%r", msg.gmail_id, msg.subject)

        result = classify_email(
            gmail_id=msg.gmail_id,
            sender=msg.sender or "",
            subject=msg.subject or "",
            body=msg.body or "",
        )

        if result is None:
            logger.error("SKIPPED %s — failed twice.", msg.gmail_id)
            failed += 1
            continue

        if dry_run:
            print(f"\n[DRY RUN] {msg.gmail_id} — {msg.subject}")
            print(result.model_dump_json(indent=2))
            success += 1
            continue

        # ── 1. Store classification in DB ─────────────────────
        with SessionFactory() as session:
            row = Classification(
                message_id=msg.id,
                category=result.category,
                confidence=result.confidence,
                extracted_deadline=(
                    date.fromisoformat(result.extracted_deadline)
                    if result.extracted_deadline
                    else None
                ),
                extracted_actions=json.dumps(result.action_items),
                reasoning=result.reasoning,
                prompt_version=PROMPT_VERSION,
            )
            session.add(row)
            session.commit()
            logger.info("Stored: %s → %s (%.2f)", msg.gmail_id, result.category, result.confidence)

        # ── 2. Apply Gmail label (only after DB write) ────────
        ok = apply_label(gmail_service, msg.gmail_id, result.category)
        if not ok:
            logger.warning("DB OK but label sync failed for %s", msg.gmail_id)

        success += 1

    logger.info("Done: %d classified, %d failed.", success, failed)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify unclassified emails")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    run_batch(dry_run=args.dry_run)

