"""Telegram Bot API notification backend."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from collector.notifier import Notifier, NotifyResult
from collector.storage import SessionEntry


class TelegramNotifier(Notifier):
    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str, message_template: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.message_template = message_template

    @classmethod
    def from_config(cls, config: dict) -> TelegramNotifier:
        return cls(
            bot_token=config.get("bot_token", ""),
            chat_id=config.get("chat_id", ""),
            message_template=config.get(
                "message_template", "🔗 New Claude session:\n{url}"
            ),
        )

    def send(self, entry: SessionEntry) -> NotifyResult:
        if not self.bot_token or not self.chat_id:
            return NotifyResult(
                success=False,
                method=self.name,
                message="Telegram not configured. Run: claude-remote-collector config set notify.telegram.bot_token YOUR_TOKEN",
            )

        text = self.message_template.format(
            url=entry.url,
            session_id=entry.session_id,
            timestamp=entry.timestamp,
            cwd=entry.cwd,
        )

        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return NotifyResult(
                        success=True,
                        method=self.name,
                        message=f"Sent to Telegram chat {self.chat_id}",
                    )
                return NotifyResult(
                    success=False,
                    method=self.name,
                    message=f"Telegram API returned status {resp.status}",
                )
        except urllib.error.HTTPError as e:
            return NotifyResult(
                success=False,
                method=self.name,
                message=f"Telegram API error: {e.code} {e.reason}",
            )
        except (urllib.error.URLError, OSError) as e:
            return NotifyResult(
                success=False,
                method=self.name,
                message=f"Network error: {e}",
            )
