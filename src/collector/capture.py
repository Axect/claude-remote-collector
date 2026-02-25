"""URL capture and construction utilities."""

from __future__ import annotations

import re

URL_PATTERN = re.compile(r"https://claude\.ai/code/session_[\w]+")
URL_PREFIX = "https://claude.ai/code/session_"


def build_url(session_id: str) -> str:
    """Construct a remote session URL from a session ID."""
    return f"{URL_PREFIX}{session_id}"


def extract_urls(text: str) -> list[str]:
    """Extract all Claude Code session URLs from text."""
    return URL_PATTERN.findall(text)


def extract_session_id(url: str) -> str | None:
    """Extract session ID from a URL."""
    if url.startswith(URL_PREFIX):
        return url[len(URL_PREFIX):]
    return None
