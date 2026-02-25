"""Tests for CLI commands."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from collector import storage


def test_record_valid_url(tmp_path: Path):
    store = storage.Storage(base_dir=tmp_path / "sessions")

    with patch("collector.cli.storage.Storage", return_value=store):
        from collector.cli import cmd_record
        import argparse

        args = argparse.Namespace(
            url="https://claude.ai/code/session_01XNYXVWynq7cb6rsR4inaM3",
            source="wrapper",
            notify=False,
        )
        cmd_record(args)

    entries = store.read_all()
    assert len(entries) == 1
    assert entries[0].session_id == "01XNYXVWynq7cb6rsR4inaM3"
    assert entries[0].url == "https://claude.ai/code/session_01XNYXVWynq7cb6rsR4inaM3"
    assert entries[0].source == "wrapper"


def test_record_with_source(tmp_path: Path):
    store = storage.Storage(base_dir=tmp_path / "sessions")

    with patch("collector.cli.storage.Storage", return_value=store):
        from collector.cli import cmd_record
        import argparse

        args = argparse.Namespace(
            url="https://claude.ai/code/session_01XNYXVWynq7cb6rsR4inaM3",
            source="startup",
            notify=False,
        )
        cmd_record(args)

    entries = store.read_all()
    assert len(entries) == 1
    assert entries[0].source == "startup"


def test_record_invalid_url():
    import argparse
    from collector.cli import cmd_record

    args = argparse.Namespace(
        url="https://example.com/not-a-session",
        source="wrapper",
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_record(args)
    assert exc_info.value.code == 1


def test_record_cli_integration(tmp_path: Path):
    """Test the record command via subprocess."""
    result = subprocess.run(
        [
            sys.executable, "-m", "collector.cli",
            "record", "--url", "https://claude.ai/code/session_testABC123"
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


import pytest
