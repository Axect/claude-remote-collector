"""Tests for setup wizard module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from collector import config, setup


def test_telegram_get_me_success():
    """getMe returns bot info on valid token."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "ok": True,
        "result": {"username": "testbot"},
    }).encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = setup._telegram_get_me("123:ABC")
    assert result is not None
    assert result["username"] == "testbot"


def test_telegram_get_me_invalid():
    """getMe returns None on invalid token."""
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
        result = setup._telegram_get_me("invalid")
    assert result is None


def test_telegram_detect_chat_id_success():
    """detect_chat_id finds chat_id from getUpdates response."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {"message": {"chat": {"id": 12345}, "text": "hello"}},
        ],
    }).encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        chat_id = setup._telegram_detect_chat_id("123:ABC", retries=1, delay=0)
    assert chat_id == "12345"


def test_telegram_detect_chat_id_empty():
    """detect_chat_id returns None when no messages found."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [],
    }).encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        chat_id = setup._telegram_detect_chat_id("123:ABC", retries=1, delay=0)
    assert chat_id is None


def test_setup_telegram_full_flow(tmp_path: Path):
    """Test full Telegram setup flow with mocked I/O and API calls."""
    fake_config = tmp_path / "config.toml"

    # Mock user inputs in order
    inputs = iter([
        "123456:ABC-DEF",           # bot token
        "",                          # press Enter after sending msg
        "",                          # keep default template
        "y",                         # auto-notify
    ])

    # Mock getMe response
    mock_getme_resp = MagicMock()
    mock_getme_resp.read.return_value = json.dumps({
        "ok": True,
        "result": {"username": "testbot"},
    }).encode()
    mock_getme_resp.__enter__ = MagicMock(return_value=mock_getme_resp)
    mock_getme_resp.__exit__ = MagicMock(return_value=False)

    # Mock getUpdates response
    mock_updates_resp = MagicMock()
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [{"message": {"chat": {"id": 99999}, "text": "hi"}}],
    }).encode()
    mock_updates_resp.__enter__ = MagicMock(return_value=mock_updates_resp)
    mock_updates_resp.__exit__ = MagicMock(return_value=False)

    # Mock sendMessage response (test message)
    mock_send_resp = MagicMock()
    mock_send_resp.status = 200
    mock_send_resp.__enter__ = MagicMock(return_value=mock_send_resp)
    mock_send_resp.__exit__ = MagicMock(return_value=False)

    def urlopen_side_effect(req, **kwargs):
        url = req if isinstance(req, str) else req.full_url
        if "getMe" in url:
            return mock_getme_resp
        elif "getUpdates" in url:
            return mock_updates_resp
        else:
            return mock_send_resp

    with (
        patch.object(config, "CONFIG_FILE", fake_config),
        patch("builtins.input", lambda msg: next(inputs)),
        patch("urllib.request.urlopen", side_effect=urlopen_side_effect),
    ):
        setup.setup_telegram()

    # Verify config was written correctly
    with patch.object(config, "CONFIG_FILE", fake_config):
        cfg = config.load_config()
    assert cfg["notify"]["enabled"] is True
    assert cfg["notify"]["backend"] == "telegram"
    assert cfg["notify.telegram"]["bot_token"] == "123456:ABC-DEF"
    assert str(cfg["notify.telegram"]["chat_id"]) == "99999"
    assert cfg["notify"]["auto_notify"] is True
