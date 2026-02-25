"""Interactive setup wizards for notification backends."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

from collector import config
from collector.notifier import get_notifier
from collector.storage import SessionEntry


def run_setup(backend: str) -> None:
    """Run the interactive setup wizard for the given backend."""
    wizards = {
        "telegram": setup_telegram,
        "webhook": setup_webhook,
        "ntfy": setup_ntfy,
    }
    if backend not in wizards:
        print(f"Unknown backend: {backend}", file=sys.stderr)
        print(f"Available: {', '.join(wizards)}", file=sys.stderr)
        sys.exit(1)
    wizards[backend]()


def setup_telegram() -> None:
    """Interactive Telegram bot setup wizard."""
    print("=== Telegram Notification Setup ===\n")

    # Step 1: Bot token
    print("Step 1: Create a Telegram bot")
    print("  1. Open Telegram and search for @BotFather")
    print("  2. Send /newbot and follow the instructions")
    print("  3. Copy the bot token (looks like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)")
    print()

    bot_token = _prompt("Bot token: ").strip()
    if not bot_token or ":" not in bot_token:
        print("Invalid bot token format. Expected format: 123456:ABC...", file=sys.stderr)
        sys.exit(1)

    # Validate token by calling getMe
    print("\nValidating bot token...", end=" ", flush=True)
    bot_info = _telegram_get_me(bot_token)
    if bot_info is None:
        print("FAILED")
        print("Could not validate bot token. Check the token and try again.", file=sys.stderr)
        sys.exit(1)
    bot_name = bot_info.get("username", "unknown")
    print(f"OK (@{bot_name})")

    # Step 2: Auto-detect chat_id
    print(f"\nStep 2: Get your chat ID")
    print(f"  Send any message to @{bot_name} in Telegram, then press Enter here.")
    _prompt("Press Enter after sending a message...")

    print("Detecting chat ID...", end=" ", flush=True)
    chat_id = _telegram_detect_chat_id(bot_token)
    if chat_id is None:
        print("FAILED")
        print("\nCould not auto-detect chat ID.", file=sys.stderr)
        chat_id = _prompt("Enter chat ID manually: ").strip()
        if not chat_id:
            print("No chat ID provided. Aborting.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"OK (chat_id: {chat_id})")

    # Step 3: Message template
    print("\nStep 3: Message template")
    default_template = "\U0001f517 New Claude session:\n{url}"
    print(f"  Default: {default_template!r}")
    custom = _prompt("Custom template (Enter to keep default): ").strip()
    template = custom if custom else default_template

    # Step 4: Save config
    print("\nSaving configuration...", end=" ", flush=True)
    config.set_value("notify.enabled", "true")
    config.set_value("notify.backend", "telegram")
    config.set_value("notify.telegram.bot_token", bot_token)
    config.set_value("notify.telegram.chat_id", chat_id)
    config.set_value("notify.telegram.message_template", template)
    print("OK")

    # Step 5: Test message
    print("\nSending test message...", end=" ", flush=True)
    cfg = config.load_config()
    notifier = get_notifier(cfg)
    test_entry = SessionEntry(
        timestamp="2026-01-01T00:00:00Z",
        session_id="test_setup",
        url="https://claude.ai/code/session_test_setup",
    )
    result = notifier.send(test_entry)
    if result.success:
        print("OK")
        print(f"\nSetup complete! Check your Telegram for the test message.")
    else:
        print("FAILED")
        print(f"  Error: {result.message}", file=sys.stderr)
        print("  Config was saved. You can fix and retry with: claude-remote-collector notify")

    # Step 6: Auto-notify option
    print()
    auto = _prompt("Enable auto-notify on session capture? (Y/n): ").strip().lower()
    if auto != "n":
        config.set_value("notify.auto_notify", "true")
        print("Auto-notify enabled. New sessions will be sent to Telegram automatically.")
    else:
        print("Auto-notify disabled. Use 'claude-remote-collector notify' to send manually.")

    print(f"\nConfig saved to: {config.CONFIG_FILE}")


def setup_webhook() -> None:
    """Interactive webhook setup wizard."""
    print("=== Webhook Notification Setup ===\n")

    url = _prompt("Webhook URL: ").strip()
    if not url or not url.startswith(("http://", "https://")):
        print("Invalid URL. Must start with http:// or https://", file=sys.stderr)
        sys.exit(1)

    method = _prompt("HTTP method (POST/GET) [POST]: ").strip().upper() or "POST"

    config.set_value("notify.enabled", "true")
    config.set_value("notify.backend", "webhook")
    config.set_value("notify.webhook.url", url)
    config.set_value("notify.webhook.method", method)

    # Test
    print("\nSending test request...", end=" ", flush=True)
    cfg = config.load_config()
    notifier = get_notifier(cfg)
    test_entry = SessionEntry(
        timestamp="2026-01-01T00:00:00Z",
        session_id="test_setup",
        url="https://claude.ai/code/session_test_setup",
    )
    result = notifier.send(test_entry)
    if result.success:
        print("OK")
    else:
        print(f"FAILED ({result.message})")

    auto = _prompt("\nEnable auto-notify? (Y/n): ").strip().lower()
    if auto != "n":
        config.set_value("notify.auto_notify", "true")

    print(f"\nSetup complete! Config saved to: {config.CONFIG_FILE}")


def setup_ntfy() -> None:
    """Interactive ntfy.sh setup wizard."""
    print("=== ntfy.sh Notification Setup ===\n")
    print("ntfy.sh sends push notifications to your phone.")
    print("Install the ntfy app: https://ntfy.sh\n")

    topic = _prompt("Topic name (e.g. claude-sessions): ").strip()
    if not topic:
        print("Topic is required.", file=sys.stderr)
        sys.exit(1)

    server = _prompt("Server URL [https://ntfy.sh]: ").strip() or "https://ntfy.sh"
    priority = _prompt("Priority (min/low/default/high/max) [default]: ").strip() or "default"

    config.set_value("notify.enabled", "true")
    config.set_value("notify.backend", "ntfy")
    config.set_value("notify.ntfy.topic", topic)
    config.set_value("notify.ntfy.server", server)
    config.set_value("notify.ntfy.priority", priority)

    # Test
    print("\nSending test notification...", end=" ", flush=True)
    cfg = config.load_config()
    notifier = get_notifier(cfg)
    test_entry = SessionEntry(
        timestamp="2026-01-01T00:00:00Z",
        session_id="test_setup",
        url="https://claude.ai/code/session_test_setup",
    )
    result = notifier.send(test_entry)
    if result.success:
        print("OK")
        print(f"Check your ntfy app for topic '{topic}'")
    else:
        print(f"FAILED ({result.message})")

    auto = _prompt("\nEnable auto-notify? (Y/n): ").strip().lower()
    if auto != "n":
        config.set_value("notify.auto_notify", "true")

    print(f"\nSetup complete! Config saved to: {config.CONFIG_FILE}")


# --- Helper functions ---


def _prompt(msg: str) -> str:
    """Read input from the user. Exits on EOF."""
    try:
        return input(msg)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)


def _telegram_get_me(token: str) -> dict | None:
    """Validate a Telegram bot token by calling getMe."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("ok"):
                return data.get("result", {})
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        pass
    return None


def _telegram_detect_chat_id(token: str, retries: int = 3, delay: float = 2.0) -> str | None:
    """Poll getUpdates to detect the chat ID from the most recent message."""
    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=5&timeout=5"
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read())
                if data.get("ok") and data.get("result"):
                    # Return the chat_id from the most recent message
                    for update in reversed(data["result"]):
                        msg = update.get("message", {})
                        chat = msg.get("chat", {})
                        chat_id = chat.get("id")
                        if chat_id:
                            return str(chat_id)
        except (urllib.error.URLError, json.JSONDecodeError, OSError):
            pass
        time.sleep(delay)
    return None
