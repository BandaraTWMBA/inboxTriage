"""
Top-level inboxtriage package.
Exposes modular subpackages (core, ingestion, classification, evaluation)
and backward-compatible convenience imports.
"""
from __future__ import annotations

from inboxtriage.core.config import get_settings
from inboxtriage.core.db import get_engine, get_session, get_session_factory, init_db
from inboxtriage.core.models import Base, Classification, Message
from inboxtriage.core.schemas import EmailClassification
from inboxtriage.ingestion.auth import build_gmail_service
from inboxtriage.ingestion.client import list_recent_messages, parse_message_payload
from inboxtriage.ingestion.html_cleaner import strip_html
from inboxtriage.ingestion.service import sync_recent_messages, upsert_message
from inboxtriage.classification.agent import classify_email
from inboxtriage.classification.batch_runner import run_batch
from inboxtriage.classification.date_normalizer import normalize_deadline
from inboxtriage.classification.label_manager import apply_label, ensure_labels_exist
from inboxtriage.evaluation.runner import run_evaluation

__version__ = "0.2.0"

__all__ = [
    "get_settings",
    "get_engine",
    "get_session_factory",
    "init_db",
    "get_session",
    "Base",
    "Message",
    "Classification",
    "EmailClassification",
    "build_gmail_service",
    "list_recent_messages",
    "parse_message_payload",
    "strip_html",
    "sync_recent_messages",
    "upsert_message",
    "classify_email",
    "run_batch",
    "normalize_deadline",
    "apply_label",
    "ensure_labels_exist",
    "run_evaluation",
]
