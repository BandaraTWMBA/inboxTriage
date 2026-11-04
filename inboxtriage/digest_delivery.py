"""
Digest delivery options: local file writing, webhook, or email.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def deliver_to_file(content: str, output_path: Optional[str] = None) -> Path:
    """Save the digest markdown to a local file."""
    if output_path is None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dest_dir = Path("reports")
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / f"digest_{today}.md"
    else:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(content, encoding="utf-8")
    logger.info("Saved digest to %s", target.resolve())
    return target

