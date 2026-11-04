from __future__ import annotations

from bs4 import BeautifulSoup


def strip_html(raw_html: str | None) -> str:
    if raw_html is None:
        return ""
    if not raw_html.strip():
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(" ", strip=True)
    return text

