"""Configuration management for notification backends."""

from __future__ import annotations

import tomllib
from pathlib import Path

from collector.storage import DEFAULT_DIR

CONFIG_FILE = DEFAULT_DIR / "config.toml"

DEFAULT_CONFIG: dict = {
    "notify": {
        "enabled": False,
        "backend": "telegram",
        "auto_notify": False,
    },
    "notify.telegram": {
        "bot_token": "",
        "chat_id": "",
        "message_template": "🔗 New Claude session:\n{url}",
    },
    "notify.webhook": {
        "url": "",
        "method": "POST",
    },
    "notify.ntfy": {
        "topic": "",
        "server": "https://ntfy.sh",
        "priority": "default",
    },
}


def load_config() -> dict:
    """Load config from TOML file, merged with defaults."""
    config = _deep_copy_defaults()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            user = tomllib.load(f)
        _merge(config, _flatten(user))
    return config


def _deep_copy_defaults() -> dict:
    return {k: dict(v) for k, v in DEFAULT_CONFIG.items()}


def _flatten(toml_data: dict, prefix: str = "") -> dict:
    """Flatten nested TOML dict into dotted-key sections."""
    result: dict = {}
    for key, value in toml_data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten(value, full_key))
        else:
            result[full_key] = value
    return result


def _merge(config: dict, flat: dict) -> None:
    """Merge flat dotted keys into section-based config dict."""
    for dotted_key, value in flat.items():
        parts = dotted_key.rsplit(".", 1)
        if len(parts) == 2:
            section, key = parts
            if section in config:
                config[section][key] = value
            else:
                config[section] = {key: value}
        else:
            # top-level key — store under root
            config.setdefault("_root", {})[dotted_key] = value


def get_value(config: dict, dotted_key: str) -> str | None:
    """Get a config value by dotted key (e.g. 'notify.telegram.bot_token')."""
    parts = dotted_key.rsplit(".", 1)
    if len(parts) == 2:
        section, key = parts
        section_data = config.get(section, {})
        if key in section_data:
            return str(section_data[key])
    return None


def set_value(dotted_key: str, value: str) -> None:
    """Set a config value and write back to TOML file."""
    config = load_config()

    # Parse boolean/numeric values
    parsed: str | bool | int = value
    if value.lower() in ("true", "false"):
        parsed = value.lower() == "true"
    elif value.isdigit():
        parsed = int(value)

    parts = dotted_key.rsplit(".", 1)
    if len(parts) == 2:
        section, key = parts
        if section not in config:
            config[section] = {}
        config[section][key] = parsed

    _write_config(config)


def _write_config(config: dict) -> None:
    """Write config dict as TOML to config file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    for section_key in sorted(config.keys()):
        if section_key == "_root":
            continue
        section = config[section_key]
        if not isinstance(section, dict):
            continue
        lines.append(f"[{section_key}]")
        for k, v in section.items():
            lines.append(f"{k} = {_toml_value(v)}")
        lines.append("")

    CONFIG_FILE.write_text("\n".join(lines))


def _toml_value(v: object) -> str:
    """Format a Python value as a TOML literal."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        if "\n" in v:
            # Use TOML multiline basic string for values with newlines
            return f'"""\n{v}"""'
        # Escape backslashes and quotes for TOML basic string
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return f'"{v}"'
