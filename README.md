# claude-remote-collector

Automatically collect Claude Code remote session links whenever you start a new session.

When Claude Code starts with remote control enabled, it displays a URL like:

```
https://claude.ai/code/session_01XNYXVWynq7cb6rsR4inaM3
```

This tool captures that URL and saves it to a text file so you never lose a session link.

## How It Works

A thin shell wrapper function shadows the `claude` command. It runs Claude Code inside `script(1)` to capture terminal output, then extracts the remote session URL after the session ends and records it via the Python CLI with proper file locking.

```
[claude wrapper] → script(1) → claude CLI → grep URL → claude-remote-collector record --url ...
```

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone and install
git clone <repo-url> && cd claude-remote-collector
uv sync

# Install the shell wrapper for your shell
uv run claude-remote-collector install fish   # Fish
uv run claude-remote-collector install bash   # Bash
uv run claude-remote-collector install zsh    # Zsh
uv run claude-remote-collector install all    # All shells
```

Or install manually without the CLI:

```bash
# Fish — copy function file
cp scripts/claude-wrapper.fish ~/.config/fish/functions/claude.fish

# Bash — source in .bashrc
echo 'source "/path/to/scripts/claude-wrapper.bash"  # claude-remote-collector' >> ~/.bashrc

# Zsh — source in .zshrc
echo 'source "/path/to/scripts/claude-wrapper.zsh"  # claude-remote-collector' >> ~/.zshrc
```

## Usage

After installation, just use `claude` as normal. Session links are captured automatically on exit.

### CLI Commands

```bash
# Check installation status
claude-remote-collector status

# List all collected session links
claude-remote-collector list
claude-remote-collector list -n 5        # Last 5 entries
claude-remote-collector list --json      # JSONL output

# Get the most recent link
claude-remote-collector latest
claude-remote-collector latest --url-only

# Watch for new links in real time
claude-remote-collector tail

# Clean old entries (keep last N)
claude-remote-collector clean --keep 20

# Show storage file path
claude-remote-collector path
claude-remote-collector path --jsonl

# Record a URL manually (used internally by shell wrappers)
claude-remote-collector record --url "https://claude.ai/code/session_..."
```

### Storage Format

Links are stored in `~/.claude-remote-sessions/`:

**sessions.txt** — one line per session:
```
2026-02-25T12:00:00Z https://claude.ai/code/session_01XNYXVWynq7cb6rsR4inaM3
```

**sessions.jsonl** — structured data:
```json
{"timestamp":"2026-02-25T12:00:00Z","session_id":"01XNYXVWynq7cb6rsR4inaM3","url":"https://claude.ai/code/session_01XNYXVWynq7cb6rsR4inaM3","cwd":"/home/user/project","source":"wrapper"}
```

## Uninstall

```bash
# Remove shell wrapper
uv run claude-remote-collector uninstall fish   # or bash, zsh, all

# (Optional) Remove collected data
rm -rf ~/.claude-remote-sessions
rm -rf ~/.claude-remote-collector
```

## Development

```bash
uv sync
uv run pytest tests/ -v
```

## Project Structure

```
claude-remote-collector/
├── pyproject.toml
├── src/collector/
│   ├── cli.py           # CLI entry point (install/list/latest/tail/clean/record)
│   ├── capture.py       # URL pattern matching
│   ├── storage.py       # Dual-file storage with atomic fcntl locking
│   └── wrapper.py       # Shell wrapper install/uninstall/status
├── scripts/
│   ├── claude-wrapper.fish    # Fish wrapper (trap, POSIX grep, proper quoting)
│   ├── claude-wrapper.bash    # Bash wrapper
│   ├── claude-wrapper.zsh     # Zsh wrapper
│   └── install-wrapper.sh     # Standalone install script
└── tests/
```

## License

MIT
