"""Storage layer for session link management."""

from __future__ import annotations

import fcntl
import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DIR = Path.home() / ".claude-remote-sessions"

URL_PREFIX = "https://claude.ai/code/session_"


@dataclass
class SessionEntry:
    timestamp: str
    session_id: str
    url: str
    cwd: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "url": self.url,
            "cwd": self.cwd,
            "source": self.source,
        }

    def to_text_line(self) -> str:
        return f"{self.timestamp} {self.url}"

    @classmethod
    def from_dict(cls, d: dict) -> SessionEntry:
        return cls(
            timestamp=d.get("timestamp", ""),
            session_id=d.get("session_id", ""),
            url=d.get("url", ""),
            cwd=d.get("cwd", ""),
            source=d.get("source", ""),
        )

    @classmethod
    def from_text_line(cls, line: str) -> SessionEntry | None:
        line = line.strip()
        if not line:
            return None
        parts = line.split(" ", 1)
        if len(parts) != 2:
            return None
        timestamp, url = parts
        session_id = url.removeprefix(URL_PREFIX) if url.startswith(URL_PREFIX) else ""
        return cls(timestamp=timestamp, session_id=session_id, url=url)


class Storage:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or DEFAULT_DIR
        self.txt_file = self.base_dir / "sessions.txt"
        self.jsonl_file = self.base_dir / "sessions.jsonl"
        self.lock_file = self.base_dir / ".lock"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def append(self, entry: SessionEntry) -> None:
        """Append an entry to both files under a single lock."""
        with open(self.lock_file, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                with open(self.txt_file, "a") as f:
                    f.write(entry.to_text_line() + "\n")
                with open(self.jsonl_file, "a") as f:
                    f.write(json.dumps(entry.to_dict()) + "\n")
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def read_all(self) -> list[SessionEntry]:
        if not self.jsonl_file.exists():
            return []
        with open(self.lock_file, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_SH)
            try:
                content = self.jsonl_file.read_text()
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
        entries = []
        for line in content.splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(SessionEntry.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError):
                    continue
        return entries

    def read_latest(self, n: int = 1) -> list[SessionEntry]:
        entries = self.read_all()
        return entries[-n:]

    def read_txt(self) -> str:
        if not self.txt_file.exists():
            return ""
        return self.txt_file.read_text()

    def clean(self, keep_last: int = 10) -> int:
        entries = self.read_all()
        if len(entries) <= keep_last:
            return 0
        removed = len(entries) - keep_last
        kept = entries[-keep_last:]

        with open(self.lock_file, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                self.jsonl_file.write_text(
                    "\n".join(json.dumps(e.to_dict()) for e in kept) + "\n"
                )
                self.txt_file.write_text(
                    "\n".join(e.to_text_line() for e in kept) + "\n"
                )
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
        return removed

    def count(self) -> int:
        return len(self.read_all())
