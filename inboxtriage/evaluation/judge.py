"""
LLM-as-a-judge for evaluating non-exact-match extraction quality:
- action_items completeness and clarity
- reasoning quality
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import google.generativeai as genai

from inboxtriage.core.config import get_settings

logger = logging.getLogger(__name__)

JUDGE_PROMPT_TEMPLATE = """You are an objective AI evaluation judge evaluating an automated email assistant.
Your task is to score the completeness, accuracy, and conciseness of the extracted action items based on the original email.

Original Email:
From: {sender}
Subject: {subject}
Body:
{body}

Extracted Action Items:
{action_items}

Scoring Rubric (Action Items Completeness):
1 = Completely unacceptable. Missed critical tasks or hallucinated actions not requested in the email.
2 = Poor. Missed major core requests or included significant incorrect actions.
3 = Acceptable / Partial. Captured the main task, but missed specific constraints (e.g. time, deadline, attachments, specifics).
4 = Good. Captured all necessary actions accurately with minimal minor wording issues.
5 = Excellent. Concise, imperative, complete, perfectly capturing all requested tasks with zero hallucinations.

Output strictly a JSON object with this structure:
{{"score": <integer from 1 to 5>, "critique": "<short 1-2 sentence explanation>"}}
"""


def score_action_items(
    sender: str,
    subject: str,
    body: str,
    action_items: list[str],
) -> tuple[int, str]:
    settings = get_settings()
    api_key = settings.get("google_api_key")
    if not api_key:
        return 3, "No API key configured for judge"

    genai.configure(api_key=api_key)
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        sender=sender,
        subject=subject,
        body=body,
        action_items=json.dumps(action_items, indent=2),
    )

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        response = model.generate_content(prompt)
        text = response.text.strip()
        data = json.loads(text)
        score = int(data.get("score", 3))
        critique = str(data.get("critique", ""))
        score = max(1, min(5, score))
        return score, critique
    except Exception as exc:
        logger.warning("LLM judge call failed: %s", exc)
        return 3, f"Judge evaluation encountered error: {exc}"

