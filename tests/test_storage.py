"""Tests for storage layer."""

from pathlib import Path

from collector.storage import SessionEntry, Storage


def test_append_and_read(tmp_path: Path):
    store = Storage(base_dir=tmp_path / "sessions")
    entry = SessionEntry(
        timestamp="2026-02-25T12:00:00Z",
        session_id="abc123",
        url="https://claude.ai/code/session_abc123",
        cwd="/home/user",
        source="startup",
    )
    store.append(entry)

    entries = store.read_all()
    assert len(entries) == 1
    assert entries[0].session_id == "abc123"
    assert entries[0].url == "https://claude.ai/code/session_abc123"


def test_read_latest(tmp_path: Path):
    store = Storage(base_dir=tmp_path / "sessions")
    for i in range(5):
        store.append(
            SessionEntry(
                timestamp=f"2026-02-25T{i:02d}:00:00Z",
                session_id=f"id_{i}",
                url=f"https://claude.ai/code/session_id_{i}",
            )
        )

    latest = store.read_latest(1)
    assert len(latest) == 1
    assert latest[0].session_id == "id_4"

    latest3 = store.read_latest(3)
    assert len(latest3) == 3
    assert latest3[0].session_id == "id_2"


def test_clean(tmp_path: Path):
    store = Storage(base_dir=tmp_path / "sessions")
    for i in range(10):
        store.append(
            SessionEntry(
                timestamp=f"2026-02-25T{i:02d}:00:00Z",
                session_id=f"id_{i}",
                url=f"https://claude.ai/code/session_id_{i}",
            )
        )

    removed = store.clean(keep_last=3)
    assert removed == 7
    assert store.count() == 3

    entries = store.read_all()
    assert entries[0].session_id == "id_7"
    assert entries[-1].session_id == "id_9"


def test_clean_nothing_to_remove(tmp_path: Path):
    store = Storage(base_dir=tmp_path / "sessions")
    for i in range(3):
        store.append(
            SessionEntry(
                timestamp=f"2026-02-25T{i:02d}:00:00Z",
                session_id=f"id_{i}",
                url=f"https://claude.ai/code/session_id_{i}",
            )
        )

    removed = store.clean(keep_last=5)
    assert removed == 0
    assert store.count() == 3


def test_read_txt(tmp_path: Path):
    store = Storage(base_dir=tmp_path / "sessions")
    store.append(
        SessionEntry(
            timestamp="2026-02-25T12:00:00Z",
            session_id="abc123",
            url="https://claude.ai/code/session_abc123",
        )
    )
    txt = store.read_txt()
    assert "2026-02-25T12:00:00Z" in txt
    assert "https://claude.ai/code/session_abc123" in txt


def test_empty_storage(tmp_path: Path):
    store = Storage(base_dir=tmp_path / "sessions")
    assert store.read_all() == []
    assert store.read_latest(1) == []
    assert store.read_txt() == ""
    assert store.count() == 0


def test_session_entry_from_text_line():
    entry = SessionEntry.from_text_line(
        "2026-02-25T12:00:00Z https://claude.ai/code/session_abc123"
    )
    assert entry is not None
    assert entry.timestamp == "2026-02-25T12:00:00Z"
    assert entry.session_id == "abc123"
    assert entry.url == "https://claude.ai/code/session_abc123"


def test_session_entry_from_text_line_empty():
    assert SessionEntry.from_text_line("") is None
    assert SessionEntry.from_text_line("   ") is None
