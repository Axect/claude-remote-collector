"""Install/uninstall shell wrapper functions for fish, bash, and zsh."""

from __future__ import annotations

import shutil
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
STABLE_DIR = Path.home() / ".claude-remote-collector"

MARKER = "# claude-remote-collector"


def _ensure_stable_scripts() -> Path:
    """Copy wrapper scripts to a stable location (~/.claude-remote-collector/)."""
    STABLE_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("claude-wrapper.fish", "claude-wrapper.bash", "claude-wrapper.zsh"):
        src = SCRIPTS_DIR / name
        if src.exists():
            dest = STABLE_DIR / name
            shutil.copy2(src, dest)
    return STABLE_DIR


def _source_line(shell: str) -> str:
    script = STABLE_DIR / f"claude-wrapper.{shell}"
    return f'source "{script}"  {MARKER}'


def install_fish() -> str:
    _ensure_stable_scripts()
    dest_dir = Path.home() / ".config" / "fish" / "functions"
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = STABLE_DIR / "claude-wrapper.fish"
    dest = dest_dir / "claude.fish"
    shutil.copy2(src, dest)
    return f"[fish]  Installed: {dest}"


def install_bash() -> str:
    _ensure_stable_scripts()
    rc = Path.home() / ".bashrc"
    return _add_source_line(rc, "bash")


def install_zsh() -> str:
    _ensure_stable_scripts()
    rc = Path.home() / ".zshrc"
    return _add_source_line(rc, "zsh")


def _add_source_line(rc: Path, shell: str) -> str:
    line = _source_line(shell)
    if rc.exists() and MARKER in rc.read_text():
        return f"[{shell}]  Already configured in {rc}"
    with open(rc, "a") as f:
        f.write(f"\n{line}\n")
    return f"[{shell}]  Added source line to {rc}"


def uninstall_fish() -> str:
    dest = Path.home() / ".config" / "fish" / "functions" / "claude.fish"
    if dest.exists():
        dest.unlink()
        return f"[fish]  Removed: {dest}"
    return "[fish]  Not installed"


def uninstall_bash() -> str:
    rc = Path.home() / ".bashrc"
    return _remove_source_line(rc, "bash")


def uninstall_zsh() -> str:
    rc = Path.home() / ".zshrc"
    return _remove_source_line(rc, "zsh")


def _remove_source_line(rc: Path, shell: str) -> str:
    if not rc.exists():
        return f"[{shell}]  Not installed"
    lines = rc.read_text().splitlines()
    filtered = [l for l in lines if MARKER not in l]
    if len(filtered) == len(lines):
        return f"[{shell}]  Not installed"
    # Remove trailing blank lines left behind
    while filtered and filtered[-1].strip() == "":
        filtered.pop()
    rc.write_text("\n".join(filtered) + "\n")
    return f"[{shell}]  Removed source line from {rc}"


def status_fish() -> str:
    dest = Path.home() / ".config" / "fish" / "functions" / "claude.fish"
    return f"[fish]  {'Installed' if dest.exists() else 'Not installed'}"


def status_bash() -> str:
    rc = Path.home() / ".bashrc"
    installed = rc.exists() and MARKER in rc.read_text()
    return f"[bash]  {'Installed' if installed else 'Not installed'}"


def status_zsh() -> str:
    rc = Path.home() / ".zshrc"
    installed = rc.exists() and MARKER in rc.read_text()
    return f"[zsh]   {'Installed' if installed else 'Not installed'}"


SHELLS = {
    "fish": (install_fish, uninstall_fish, status_fish),
    "bash": (install_bash, uninstall_bash, status_bash),
    "zsh": (install_zsh, uninstall_zsh, status_zsh),
}


def install(shell: str) -> str:
    results = []
    targets = SHELLS.keys() if shell == "all" else [shell]
    for s in targets:
        if s in SHELLS:
            results.append(SHELLS[s][0]())
    return "\n".join(results)


def uninstall(shell: str) -> str:
    results = []
    targets = SHELLS.keys() if shell == "all" else [shell]
    for s in targets:
        if s in SHELLS:
            results.append(SHELLS[s][1]())
    return "\n".join(results)


def status() -> str:
    return "\n".join(fn() for _, _, fn in SHELLS.values())
