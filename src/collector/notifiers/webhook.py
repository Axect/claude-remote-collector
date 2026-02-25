"""Generic webhook notification backend."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from collector.notifier import Notifier, NotifyResult
from collector.storage import SessionEntry


class WebhookNotifier(Notifier):
    name = "webhook"

    def __init__(self, url: str, method: str = "POST"):
        self.url = url
        self.method = method.upper()

    @classmethod
    def from_config(cls, config: dict) -> WebhookNotifier:
        return cls(
            url=config.get("url", ""),
            method=config.get("method", "POST"),
        )

    def send(self, entry: SessionEntry) -> NotifyResult:
        if not self.url:
            return NotifyResult(
                success=False,
                method=self.name,
                message="Webhook URL not configured. Run: claude-remote-collector config set notify.webhook.url YOUR_URL",
            )

        payload = json.dumps(entry.to_dict()).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method=self.method,
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return NotifyResult(
                    success=True,
                    method=self.name,
                    message=f"Webhook {self.method} {self.url} → {resp.status}",
                )
        except urllib.error.HTTPError as e:
            return NotifyResult(
                success=False,
                method=self.name,
                message=f"Webhook error: {e.code} {e.reason}",
            )
        except (urllib.error.URLError, OSError) as e:
            return NotifyResult(
                success=False,
                method=self.name,
                message=f"Network error: {e}",
            )
