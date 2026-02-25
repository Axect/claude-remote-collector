"""ntfy.sh push notification backend."""

from __future__ import annotations

import urllib.error
import urllib.request

from collector.notifier import Notifier, NotifyResult
from collector.storage import SessionEntry


class NtfyNotifier(Notifier):
    name = "ntfy"

    def __init__(self, topic: str, server: str = "https://ntfy.sh", priority: str = "default"):
        self.topic = topic
        self.server = server.rstrip("/")
        self.priority = priority

    @classmethod
    def from_config(cls, config: dict) -> NtfyNotifier:
        return cls(
            topic=config.get("topic", ""),
            server=config.get("server", "https://ntfy.sh"),
            priority=config.get("priority", "default"),
        )

    def send(self, entry: SessionEntry) -> NotifyResult:
        if not self.topic:
            return NotifyResult(
                success=False,
                method=self.name,
                message="ntfy topic not configured. Run: claude-remote-collector config set notify.ntfy.topic YOUR_TOPIC",
            )

        url = f"{self.server}/{self.topic}"
        body = entry.url.encode("utf-8")

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Title", f"Claude Session: {entry.session_id}")
        req.add_header("Click", entry.url)
        req.add_header("Tags", "link,claude")
        if self.priority != "default":
            req.add_header("Priority", self.priority)

        try:
            with urllib.request.urlopen(req, timeout=10):
                return NotifyResult(
                    success=True,
                    method=self.name,
                    message=f"Sent to ntfy topic '{self.topic}'",
                )
        except urllib.error.HTTPError as e:
            return NotifyResult(
                success=False,
                method=self.name,
                message=f"ntfy error: {e.code} {e.reason}",
            )
        except (urllib.error.URLError, OSError) as e:
            return NotifyResult(
                success=False,
                method=self.name,
                message=f"Network error: {e}",
            )
