"""
Single-shot email classifier using Gemini 2.5 Flash with structured output.
Retry once on validation failure, log and return None on double failure.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from pydantic import ValidationError

from inboxtriage.config import get_settings
from inboxtriage.date_utils import normalize_deadline
from inboxtriage.schemas import EmailClassification

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────
MAX_BODY_CHARS = 4_000   # truncate very long emails
MODEL_NAME = "gemini-2.5-flash"
PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "classify_v1.txt"

# Gemini response_schema — mirrors EmailClassification
_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["urgent_action", "fyi", "can_wait", "low_priority"],
        },
        "confidence": {"type": "number"},
        "extracted_deadline": {"type": "string", "nullable": True},
        "action_items": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reasoning": {"type": "string"},
    },
    "required": ["category", "confidence", "action_items", "reasoning"],
}


# ── Helpers ────────────────────────────────────────────────────

def _load_prompt_template() -> str:
    return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")


def _build_prompt(sender: str, subject: str, body: str) -> str:
    template = _load_prompt_template()
    truncated = body[:MAX_BODY_CHARS] if body else "(no body)"
    return template.format(sender=sender, subject=subject, body=truncated)


def _call_gemini(prompt: str) -> dict:
    """Call Gemini and return the parsed JSON dict."""
    settings = get_settings()
    genai.configure(api_key=settings["google_api_key"])

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=_RESPONSE_SCHEMA,
            temperature=0.1,
        ),
    )
    response = model.generate_content(prompt)
    return json.loads(response.text)


def _validate(raw: dict, reference_date=None) -> EmailClassification:
    """Validate raw Gemini output → EmailClassification, normalizing the deadline."""
    raw["extracted_deadline"] = normalize_deadline(
        raw.get("extracted_deadline"), reference=reference_date
    )
    return EmailClassification(**raw)


# ── Public API ─────────────────────────────────────────────────

def classify_email(
    gmail_id: str,
    sender: str,
    subject: str,
    body: str,
    reference_date=None,
) -> Optional[EmailClassification]:
    """
    Classify one email via Gemini structured output.

    Retries once with a corrective message on validation failure.
    Returns None (and logs) if both attempts fail.
    """
    prompt = _build_prompt(sender=sender, subject=subject, body=body or "")

    for attempt in (1, 2):
        try:
            raw = _call_gemini(prompt)
            result = _validate(raw, reference_date=reference_date)
            logger.info(
                "Classified %s → %s (conf=%.2f, attempt=%d)",
                gmail_id, result.category, result.confidence, attempt,
            )
            return result

        except (ValidationError, KeyError, ValueError) as exc:
            if attempt == 1:
                logger.warning(
                    "Validation failed for %s (attempt 1): %s — retrying.",
                    gmail_id, exc,
                )
                prompt += (
                    f"\n\n[CORRECTION: Previous response failed validation: {exc}. "
                    "Return ONLY valid JSON matching the schema.]"
                )
            else:
                logger.error(
                    "Classification failed TWICE for %s: %s — skipping.", gmail_id, exc
                )
                return None

        except Exception as exc:
            logger.error(
                "Unexpected error for %s (attempt %d): %s", gmail_id, attempt, exc
            )
            if attempt == 2:
                return None
            time.sleep(2)

    return None

