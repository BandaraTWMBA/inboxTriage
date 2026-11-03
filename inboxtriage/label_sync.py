"""
Manages InboxTriage/* Gmail labels.
- Creates the four labels on first run if missing, caches their IDs.
- apply_label() removes any existing InboxTriage/* label and applies the new one.
- Labels are purely additive — no archive, move, or mark-as-read.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

CATEGORY_TO_LABEL: dict[str, str] = {
    "urgent_action": "InboxTriage/Urgent",
    "fyi":           "InboxTriage/FYI",
    "can_wait":      "InboxTriage/Can-Wait",
    "low_priority":  "InboxTriage/Low-Priority",
}

# Module-level cache: label_name → gmail label id
_label_id_cache: dict[str, str] = {}


def ensure_labels_exist(gmail_service) -> dict[str, str]:
    """
    Create missing InboxTriage/* labels and return {label_name: label_id}.
    Results are cached — safe to call multiple times.
    """
    global _label_id_cache
    if _label_id_cache:
        return _label_id_cache

    # Fetch all existing labels
    result = gmail_service.users().labels().list(userId="me").execute()
    existing = {lbl["name"]: lbl["id"] for lbl in result.get("labels", [])}

    cache: dict[str, str] = {}
    for category, label_name in CATEGORY_TO_LABEL.items():
        if label_name in existing:
            cache[label_name] = existing[label_name]
            logger.debug("Label exists: %s → %s", label_name, existing[label_name])
        else:
            try:
                created = (
                    gmail_service.users()
                    .labels()
                    .create(
                        userId="me",
                        body={
                            "name": label_name,
                            "labelListVisibility": "labelShow",
                            "messageListVisibility": "show",
                        },
                    )
                    .execute()
                )
                cache[label_name] = created["id"]
                logger.info("Created label: %s → %s", label_name, created["id"])
            except Exception as exc:
                logger.error("Failed to create label %s: %s", label_name, exc)
                raise RuntimeError(
                    f"Could not create Gmail label '{label_name}': {exc}"
                ) from exc

    _label_id_cache = cache
    return cache


def apply_label(gmail_service, gmail_message_id: str, category: str) -> bool:
    """
    Apply the correct InboxTriage/* label for `category`.
    Removes any prior InboxTriage/* label first — a message should never
    carry two InboxTriage labels at the same time.

    Returns True on success, False on failure.
    """
    label_map = ensure_labels_exist(gmail_service)

    target_label_name = CATEGORY_TO_LABEL.get(category)
    if not target_label_name:
        logger.error("Unknown category '%s'", category)
        return False

    target_id = label_map.get(target_label_name)
    if not target_id:
        logger.error("No cached label ID for '%s'", target_label_name)
        return False

    try:
        # Get current labels on this message
        msg = (
            gmail_service.users()
            .messages()
            .get(userId="me", id=gmail_message_id, format="metadata", metadataHeaders=[])
            .execute()
        )
        current_ids: list[str] = msg.get("labelIds", [])

        # Find any InboxTriage/* labels to remove
        all_it_ids = set(label_map.values())
        to_remove = [lid for lid in current_ids if lid in all_it_ids]

        modify_body: dict = {"addLabelIds": [target_id]}
        if to_remove:
            modify_body["removeLabelIds"] = to_remove

        gmail_service.users().messages().modify(
            userId="me", id=gmail_message_id, body=modify_body
        ).execute()

        logger.info(
            "Label '%s' applied to %s (removed %d old)",
            target_label_name, gmail_message_id, len(to_remove),
        )
        return True

    except Exception as exc:
        logger.error("Label apply failed for %s: %s", gmail_message_id, exc)
        return False

