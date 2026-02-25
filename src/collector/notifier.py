"""Pluggable notification system for session links."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from collector.storage import SessionEntry


@dataclass
class NotifyResult:
    success: bool
    method: str
    message: str


class Notifier(ABC):
    """Base class for notification backends."""

    name: str = ""

    @abstractmethod
    def send(self, entry: SessionEntry) -> NotifyResult:
        """Send a notification for the given session entry."""

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict) -> Notifier:
        """Create a notifier instance from config section dict."""


def get_notifier(config: dict) -> Notifier:
    """Factory: create a notifier from the full config dict."""
    backend = config.get("notify", {}).get("backend", "telegram")
    backend_config = config.get(f"notify.{backend}", {})

    if backend == "telegram":
        from collector.notifiers.telegram import TelegramNotifier

        return TelegramNotifier.from_config(backend_config)
    elif backend == "webhook":
        from collector.notifiers.webhook import WebhookNotifier

        return WebhookNotifier.from_config(backend_config)
    elif backend == "ntfy":
        from collector.notifiers.ntfy import NtfyNotifier

        return NtfyNotifier.from_config(backend_config)
    else:
        raise ValueError(f"Unknown notification backend: {backend}")


def notify(entry: SessionEntry, config: dict) -> NotifyResult:
    """Convenience function: create notifier from config and send."""
    notifier = get_notifier(config)
    return notifier.send(entry)
