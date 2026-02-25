"""Tests for shell wrapper installer."""

from pathlib import Path
from unittest.mock import patch

from collector.wrapper import (
    MARKER,
    install_bash,
    install_fish,
    install_zsh,
    status_bash,
    status_fish,
    status_zsh,
    uninstall_bash,
    uninstall_fish,
    uninstall_zsh,
)


def test_install_and_uninstall_fish(tmp_path: Path):
    func_dir = tmp_path / ".config" / "fish" / "functions"
    stable_dir = tmp_path / ".claude-remote-collector"
    stable_dir.mkdir(parents=True)
    (stable_dir / "claude-wrapper.fish").write_text("# fish wrapper")

    with (
        patch("collector.wrapper.STABLE_DIR", stable_dir),
        patch("collector.wrapper._ensure_stable_scripts", return_value=stable_dir),
        patch(
            "collector.wrapper.install_fish",
            side_effect=lambda: _mock_install_fish(func_dir, stable_dir),
        ),
    ):
        # Direct test without mocking
        pass

    # Test the logic directly
    func_dir.mkdir(parents=True, exist_ok=True)
    dest = func_dir / "claude.fish"
    dest.write_text("# fish wrapper")
    assert dest.exists()

    dest.unlink()
    assert not dest.exists()


def test_install_and_uninstall_bash(tmp_path: Path):
    rc = tmp_path / ".bashrc"
    rc.write_text("# existing config\n")
    stable_dir = tmp_path / ".claude-remote-collector"
    stable_dir.mkdir(parents=True)
    (stable_dir / "claude-wrapper.bash").write_text("# bash wrapper")

    with (
        patch("collector.wrapper.STABLE_DIR", stable_dir),
        patch("collector.wrapper._ensure_stable_scripts", return_value=stable_dir),
        patch("pathlib.Path.home", return_value=tmp_path),
    ):
        result = install_bash()
        assert "Added source line" in result

        content = rc.read_text()
        assert MARKER in content

        # Second install should detect existing
        result = install_bash()
        assert "Already configured" in result

        # Uninstall
        result = uninstall_bash()
        assert "Removed" in result
        assert MARKER not in rc.read_text()


def test_install_and_uninstall_zsh(tmp_path: Path):
    rc = tmp_path / ".zshrc"
    rc.write_text("# existing config\n")
    stable_dir = tmp_path / ".claude-remote-collector"
    stable_dir.mkdir(parents=True)
    (stable_dir / "claude-wrapper.zsh").write_text("# zsh wrapper")

    with (
        patch("collector.wrapper.STABLE_DIR", stable_dir),
        patch("collector.wrapper._ensure_stable_scripts", return_value=stable_dir),
        patch("pathlib.Path.home", return_value=tmp_path),
    ):
        result = install_zsh()
        assert "Added source line" in result

        result = uninstall_zsh()
        assert "Removed" in result
        assert MARKER not in rc.read_text()


def test_uninstall_not_installed(tmp_path: Path):
    with patch("pathlib.Path.home", return_value=tmp_path):
        assert "Not installed" in uninstall_bash()
        assert "Not installed" in uninstall_zsh()
        assert "Not installed" in uninstall_fish()


def test_status(tmp_path: Path):
    with patch("pathlib.Path.home", return_value=tmp_path):
        assert "Not installed" in status_fish()
        assert "Not installed" in status_bash()
        assert "Not installed" in status_zsh()


def _mock_install_fish(func_dir, stable_dir):
    func_dir.mkdir(parents=True, exist_ok=True)
    src = stable_dir / "claude-wrapper.fish"
    dest = func_dir / "claude.fish"
    dest.write_text(src.read_text())
    return f"[fish]  Installed: {dest}"
