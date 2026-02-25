"""Tests for config module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from collector import config


def test_load_config_defaults(tmp_path: Path):
    """Loading config without a file returns defaults."""
    fake_config = tmp_path / "config.toml"
    with patch.object(config, "CONFIG_FILE", fake_config):
        cfg = config.load_config()
    assert cfg["notify"]["enabled"] is False
    assert cfg["notify"]["backend"] == "telegram"
    assert cfg["notify.telegram"]["bot_token"] == ""


def test_load_config_from_file(tmp_path: Path):
    """Loading config reads TOML values."""
    fake_config = tmp_path / "config.toml"
    fake_config.write_text(
        '[notify]\nenabled = true\nbackend = "telegram"\n\n'
        '[notify.telegram]\nbot_token = "123:ABC"\nchat_id = "999"\n'
    )
    with patch.object(config, "CONFIG_FILE", fake_config):
        cfg = config.load_config()
    assert cfg["notify"]["enabled"] is True
    assert cfg["notify.telegram"]["bot_token"] == "123:ABC"
    assert cfg["notify.telegram"]["chat_id"] == "999"


def test_set_value(tmp_path: Path):
    """set_value writes and persists config."""
    fake_config = tmp_path / "config.toml"
    with patch.object(config, "CONFIG_FILE", fake_config):
        config.set_value("notify.telegram.bot_token", "test_token")
        cfg = config.load_config()
    assert cfg["notify.telegram"]["bot_token"] == "test_token"


def test_set_value_boolean(tmp_path: Path):
    """set_value parses booleans correctly."""
    fake_config = tmp_path / "config.toml"
    with patch.object(config, "CONFIG_FILE", fake_config):
        config.set_value("notify.enabled", "true")
        cfg = config.load_config()
    assert cfg["notify"]["enabled"] is True


def test_get_value(tmp_path: Path):
    """get_value retrieves by dotted key."""
    fake_config = tmp_path / "config.toml"
    with patch.object(config, "CONFIG_FILE", fake_config):
        config.set_value("notify.telegram.chat_id", "12345")
        cfg = config.load_config()
        val = config.get_value(cfg, "notify.telegram.chat_id")
    assert val == "12345"


def test_get_value_missing():
    """get_value returns None for missing keys."""
    cfg = config._deep_copy_defaults()
    val = config.get_value(cfg, "nonexistent.key")
    assert val is None


def test_roundtrip(tmp_path: Path):
    """Config survives write/read roundtrip."""
    fake_config = tmp_path / "config.toml"
    with patch.object(config, "CONFIG_FILE", fake_config):
        config.set_value("notify.enabled", "true")
        config.set_value("notify.backend", "ntfy")
        config.set_value("notify.ntfy.topic", "my-topic")
        cfg = config.load_config()
    assert cfg["notify"]["enabled"] is True
    assert cfg["notify"]["backend"] == "ntfy"
    assert cfg["notify.ntfy"]["topic"] == "my-topic"
