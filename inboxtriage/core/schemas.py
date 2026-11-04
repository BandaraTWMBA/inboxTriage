from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, field_validator

VALID_CATEGORIES = {"urgent_action", "fyi", "can_wait", "low_priority"}
PROMPT_VERSION = "v1"


class EmailClassification(BaseModel):
    category: Literal["urgent_action", "fyi", "can_wait", "low_priority"]
    confidence: float
    extracted_deadline: Optional[str] = None
    action_items: list[str]
    reasoning: str

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be 0.0–1.0, got {v}")
        return v

    @field_validator("extracted_deadline", mode="before")
    @classmethod
    def empty_deadline_to_none(cls, v):
        if v in ("", "null", "None"):
            return None
        return v

