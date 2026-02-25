"""Tests for notifier module and backends."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from collector.notifier import NotifyResult, get_notifier, notify
from collector.notifiers.ntfy import NtfyNotifier
from collector.notifiers.telegram import TelegramNotifier
from collector.notifiers.webhook import WebhookNotifier
from collector.storage import SessionEntry

SAMPLE_ENTRY = SessionEntry(
    timestamp="2026-02-25T12:00:00Z",
    session_id="01XNYXVWynq7cb6rsR4inaM3",
    url="https://claude.ai/code/session_01XNYXVWynq7cb6rsR4inaM3",
    cwd="/home/user/project",
    source="wrapper",
)


# --- Factory tests ---


def test_get_notifier_telegram():
    cfg = {
        "notify": {"backend": "telegram"},
        "notify.telegram": {"bot_token": "t", "chat_id": "c"},
    }
    n = get_notifier(cfg)
    assert isinstance(n, TelegramNotifier)


def test_get_notifier_webhook():
    cfg = {
        "notify": {"backend": "webhook"},
        "notify.webhook": {"url": "http://example.com"},
    }
    n = get_notifier(cfg)
    assert isinstance(n, WebhookNotifier)


def test_get_notifier_ntfy():
    cfg = {
        "notify": {"backend": "ntfy"},
        "notify.ntfy": {"topic": "test"},
    }
    n = get_notifier(cfg)
    assert isinstance(n, NtfyNotifier)


# --- Telegram tests ---


def test_telegram_not_configured():
    n = TelegramNotifier(bot_token="", chat_id="", message_template="{url}")
    result = n.send(SAMPLE_ENTRY)
    assert result.success is False
    assert "not configured" in result.message


def test_telegram_send_success():
    n = TelegramNotifier(bot_token="123:ABC", chat_id="999", message_template="{url}")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        result = n.send(SAMPLE_ENTRY)

    assert result.success is True
    assert result.method == "telegram"
    # Verify the API call
    call_args = mock_open.call_args
    req = call_args[0][0]
    body = json.loads(req.data)
    assert body["chat_id"] == "999"
    assert SAMPLE_ENTRY.url in body["text"]


def test_telegram_message_template():
    n = TelegramNotifier(
        bot_token="123:ABC",
        chat_id="999",
        message_template="Session {session_id} at {timestamp}: {url}",
    )
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        n.send(SAMPLE_ENTRY)

    req = mock_open.call_args[0][0]
    body = json.loads(req.data)
    assert "01XNYXVWynq7cb6rsR4inaM3" in body["text"]
    assert "2026-02-25T12:00:00Z" in body["text"]


# --- Webhook tests ---


def test_webhook_not_configured():
    n = WebhookNotifier(url="")
    result = n.send(SAMPLE_ENTRY)
    assert result.success is False
    assert "not configured" in result.message


def test_webhook_send_success():
    n = WebhookNotifier(url="http://example.com/hook")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        result = n.send(SAMPLE_ENTRY)

    assert result.success is True
    req = mock_open.call_args[0][0]
    body = json.loads(req.data)
    assert body["url"] == SAMPLE_ENTRY.url
    assert body["session_id"] == SAMPLE_ENTRY.session_id


# --- ntfy tests ---


def test_ntfy_not_configured():
    n = NtfyNotifier(topic="")
    result = n.send(SAMPLE_ENTRY)
    assert result.success is False
    assert "not configured" in result.message


def test_ntfy_send_success():
    n = NtfyNotifier(topic="claude-sessions")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        result = n.send(SAMPLE_ENTRY)

    assert result.success is True
    req = mock_open.call_args[0][0]
    assert req.full_url == "https://ntfy.sh/claude-sessions"
    assert req.get_header("Title") is not None


# --- Convenience function test ---


def test_notify_convenience():
    cfg = {
        "notify": {"backend": "telegram"},
        "notify.telegram": {"bot_token": "t", "chat_id": "c", "message_template": "{url}"},
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = notify(SAMPLE_ENTRY, cfg)

    assert result.success is True
    assert result.method == "telegram"
