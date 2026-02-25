"""CLI entry point for claude-remote-collector."""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone

from collector import config, storage, wrapper
from collector.capture import URL_PATTERN
from collector.notifier import notify as send_notify


def cmd_install(args: argparse.Namespace) -> None:
    print(wrapper.install(args.shell))


def cmd_uninstall(args: argparse.Namespace) -> None:
    print(wrapper.uninstall(args.shell))


def cmd_status(args: argparse.Namespace) -> None:
    store = storage.Storage()
    print("Shell wrappers:")
    print(wrapper.status())
    print(f"\nSessions: {store.count()}")
    print(f"Storage:  {store.base_dir}")


def cmd_list(args: argparse.Namespace) -> None:
    store = storage.Storage()
    entries = store.read_all()
    if not entries:
        print("No sessions collected yet.")
        return

    n = args.n
    if n and n > 0:
        entries = entries[-n:]

    if args.json:
        import json

        for e in entries:
            print(json.dumps(e.to_dict()))
    else:
        for e in entries:
            print(e.to_text_line())


def cmd_latest(args: argparse.Namespace) -> None:
    store = storage.Storage()
    entries = store.read_latest(1)
    if not entries:
        print("No sessions collected yet.", file=sys.stderr)
        sys.exit(1)
    entry = entries[0]
    if args.url_only:
        print(entry.url)
    else:
        print(entry.to_text_line())


def cmd_tail(args: argparse.Namespace) -> None:
    store = storage.Storage()
    txt_file = store.txt_file

    if not txt_file.exists():
        txt_file.touch()

    print(f"Watching {txt_file} for new sessions... (Ctrl+C to stop)")

    last_size = txt_file.stat().st_size
    content = txt_file.read_text()
    if content:
        print(content, end="")

    try:
        while True:
            current_size = txt_file.stat().st_size
            if current_size > last_size:
                with open(txt_file) as f:
                    f.seek(last_size)
                    new_content = f.read()
                    if new_content:
                        print(new_content, end="", flush=True)
                last_size = current_size
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


def cmd_clean(args: argparse.Namespace) -> None:
    store = storage.Storage()
    keep = args.keep
    removed = store.clean(keep_last=keep)
    if removed:
        print(f"Removed {removed} old entries (kept last {keep}).")
    else:
        print(f"Nothing to clean ({store.count()} entries, keeping {keep}).")


def cmd_record(args: argparse.Namespace) -> None:
    url = args.url.strip()
    if not URL_PATTERN.fullmatch(url):
        print(f"Invalid session URL: {url}", file=sys.stderr)
        sys.exit(1)
    session_id = url.split("session_", 1)[-1]
    entry = storage.SessionEntry(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        session_id=session_id,
        url=url,
        cwd=os.getcwd(),
        source=args.source,
    )
    store = storage.Storage()
    store.append(entry)

    # Auto-notify if --notify flag or auto_notify config
    cfg = config.load_config()
    should_notify = args.notify or cfg.get("notify", {}).get("auto_notify", False)
    if should_notify and cfg.get("notify", {}).get("enabled", False):
        result = send_notify(entry, cfg)
        if not result.success:
            print(f"Notify failed: {result.message}", file=sys.stderr)


def cmd_notify(args: argparse.Namespace) -> None:
    cfg = config.load_config()
    if not cfg.get("notify", {}).get("enabled", False):
        print("Notifications are disabled. Enable with:", file=sys.stderr)
        print("  claude-remote-collector config set notify.enabled true", file=sys.stderr)
        sys.exit(1)

    if args.url:
        url = args.url.strip()
        if not URL_PATTERN.fullmatch(url):
            print(f"Invalid session URL: {url}", file=sys.stderr)
            sys.exit(1)
        session_id = url.split("session_", 1)[-1]
        entry = storage.SessionEntry(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            session_id=session_id,
            url=url,
        )
    else:
        store = storage.Storage()
        entries = store.read_latest(1)
        if not entries:
            print("No sessions to notify about.", file=sys.stderr)
            sys.exit(1)
        entry = entries[0]

    result = send_notify(entry, cfg)
    if result.success:
        print(f"[{result.method}] {result.message}")
    else:
        print(f"[{result.method}] Failed: {result.message}", file=sys.stderr)
        sys.exit(1)


def cmd_config(args: argparse.Namespace) -> None:
    if args.config_action == "show":
        cfg = config.load_config()
        for section_key in sorted(cfg.keys()):
            if section_key == "_root":
                continue
            section = cfg[section_key]
            if not isinstance(section, dict):
                continue
            print(f"[{section_key}]")
            for k, v in section.items():
                # Mask sensitive values
                display = _mask_sensitive(k, v)
                print(f"  {k} = {display}")
            print()
    elif args.config_action == "set":
        config.set_value(args.key, args.value)
        print(f"Set {args.key} = {args.value}")
    elif args.config_action == "get":
        cfg = config.load_config()
        val = config.get_value(cfg, args.key)
        if val is not None:
            print(val)
        else:
            print(f"Key not found: {args.key}", file=sys.stderr)
            sys.exit(1)
    elif args.config_action == "path":
        print(config.CONFIG_FILE)


def _mask_sensitive(key: str, value: object) -> str:
    """Mask sensitive config values like tokens."""
    s = str(value)
    if key in ("bot_token",) and len(s) > 8:
        return s[:4] + "***" + s[-4:]
    return s


def cmd_setup(args: argparse.Namespace) -> None:
    from collector.setup import run_setup

    run_setup(args.backend)


def cmd_path(args: argparse.Namespace) -> None:
    store = storage.Storage()
    if args.jsonl:
        print(store.jsonl_file)
    else:
        print(store.txt_file)


SHELL_CHOICES = ["fish", "bash", "zsh", "all"]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="claude-remote-collector",
        description="Collect and manage Claude Code remote session links.",
    )
    sub = parser.add_subparsers(dest="command")

    # install
    p_install = sub.add_parser("install", help="Install shell wrapper")
    p_install.add_argument(
        "shell", choices=SHELL_CHOICES, help="Target shell (or 'all')"
    )

    # uninstall
    p_uninstall = sub.add_parser("uninstall", help="Remove shell wrapper")
    p_uninstall.add_argument(
        "shell", choices=SHELL_CHOICES, help="Target shell (or 'all')"
    )

    # status
    sub.add_parser("status", help="Show wrapper and collection status")

    # list
    p_list = sub.add_parser("list", help="Show collected session links")
    p_list.add_argument("-n", type=int, default=0, help="Show last N entries")
    p_list.add_argument("--json", action="store_true", help="Output as JSONL")

    # latest
    p_latest = sub.add_parser("latest", help="Show the most recent session link")
    p_latest.add_argument(
        "--url-only", action="store_true", help="Print only the URL"
    )

    # tail
    sub.add_parser("tail", help="Watch for new session links in real time")

    # clean
    p_clean = sub.add_parser("clean", help="Remove old entries")
    p_clean.add_argument(
        "--keep", type=int, default=10, help="Number of recent entries to keep"
    )

    # record (called by shell wrappers)
    p_record = sub.add_parser("record", help="Record a session URL (used by shell wrappers)")
    p_record.add_argument("--url", required=True, help="Session URL to record")
    p_record.add_argument("--source", default="wrapper", help="Source label (startup/exit/wrapper)")
    p_record.add_argument("--notify", action="store_true", help="Send notification after recording")

    # setup (interactive wizard)
    p_setup = sub.add_parser("setup", help="Interactive notification setup wizard")
    p_setup.add_argument(
        "backend", choices=["telegram", "webhook", "ntfy"],
        help="Notification backend to configure",
    )

    # notify
    p_notify = sub.add_parser("notify", help="Send latest session link via configured backend")
    p_notify.add_argument("--url", default=None, help="Specific URL to notify (default: latest)")

    # config
    p_config = sub.add_parser("config", help="Manage notification settings")
    config_sub = p_config.add_subparsers(dest="config_action")

    config_sub.add_parser("show", help="Show all config values")
    config_sub.add_parser("path", help="Print config file path")

    p_config_get = config_sub.add_parser("get", help="Get a config value")
    p_config_get.add_argument("key", help="Config key (e.g. notify.telegram.bot_token)")

    p_config_set = config_sub.add_parser("set", help="Set a config value")
    p_config_set.add_argument("key", help="Config key (e.g. notify.telegram.bot_token)")
    p_config_set.add_argument("value", help="Value to set")

    # path
    p_path = sub.add_parser("path", help="Print the storage file path")
    p_path.add_argument("--jsonl", action="store_true", help="Print JSONL file path")

    args = parser.parse_args()

    commands = {
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "status": cmd_status,
        "list": cmd_list,
        "latest": cmd_latest,
        "tail": cmd_tail,
        "clean": cmd_clean,
        "record": cmd_record,
        "setup": cmd_setup,
        "notify": cmd_notify,
        "config": cmd_config,
        "path": cmd_path,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
