"""Tests for URL capture utilities."""

from collector.capture import build_url, extract_session_id, extract_urls


def test_build_url():
    url = build_url("01BYeELyC6pRjhnVXDtELLk1")
    assert url == "https://claude.ai/code/session_01BYeELyC6pRjhnVXDtELLk1"


def test_extract_urls_single():
    text = "Visit https://claude.ai/code/session_01BYeELyC6pRjhnVXDtELLk1 to connect."
    urls = extract_urls(text)
    assert urls == ["https://claude.ai/code/session_01BYeELyC6pRjhnVXDtELLk1"]


def test_extract_urls_multiple():
    text = (
        "Session 1: https://claude.ai/code/session_abc123\n"
        "Session 2: https://claude.ai/code/session_def456\n"
    )
    urls = extract_urls(text)
    assert len(urls) == 2
    assert "https://claude.ai/code/session_abc123" in urls
    assert "https://claude.ai/code/session_def456" in urls


def test_extract_urls_none():
    text = "No URLs here."
    assert extract_urls(text) == []


def test_extract_session_id():
    url = "https://claude.ai/code/session_01BYeELyC6pRjhnVXDtELLk1"
    assert extract_session_id(url) == "01BYeELyC6pRjhnVXDtELLk1"


def test_extract_session_id_invalid():
    assert extract_session_id("https://example.com") is None
