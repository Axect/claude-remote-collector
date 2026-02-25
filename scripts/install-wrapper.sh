#!/usr/bin/env bash
# Install the Claude shell wrapper for fish, bash, and/or zsh.
#
# Usage:
#   ./install-wrapper.sh           # auto-detect current shell
#   ./install-wrapper.sh fish      # install fish only
#   ./install-wrapper.sh bash      # install bash only
#   ./install-wrapper.sh zsh       # install zsh only
#   ./install-wrapper.sh all       # install all shells

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

install_fish() {
    local dest_dir="$HOME/.config/fish/functions"
    mkdir -p "$dest_dir"
    cp "$SCRIPT_DIR/claude-wrapper.fish" "$dest_dir/claude.fish"
    echo "[fish]  Installed: $dest_dir/claude.fish"
}

install_bash() {
    local wrapper="$SCRIPT_DIR/claude-wrapper.bash"
    local rc="$HOME/.bashrc"
    local source_line="source \"$wrapper\"  # claude-remote-collector"

    if [[ -f "$rc" ]] && grep -qF "claude-remote-collector" "$rc"; then
        echo "[bash]  Already configured in $rc"
        return
    fi

    echo "" >> "$rc"
    echo "$source_line" >> "$rc"
    echo "[bash]  Added source line to $rc"
}

install_zsh() {
    local wrapper="$SCRIPT_DIR/claude-wrapper.zsh"
    local rc="$HOME/.zshrc"
    local source_line="source \"$wrapper\"  # claude-remote-collector"

    if [[ -f "$rc" ]] && grep -qF "claude-remote-collector" "$rc"; then
        echo "[zsh]   Already configured in $rc"
        return
    fi

    echo "" >> "$rc"
    echo "$source_line" >> "$rc"
    echo "[zsh]   Added source line to $rc"
}

detect_shell() {
    local shell_name
    shell_name=$(basename "$SHELL")
    case "$shell_name" in
        fish|bash|zsh) echo "$shell_name" ;;
        *) echo "unknown" ;;
    esac
}

TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
    TARGET=$(detect_shell)
    if [[ "$TARGET" == "unknown" ]]; then
        echo "Could not detect shell. Please specify: fish, bash, zsh, or all"
        exit 1
    fi
    echo "Detected shell: $TARGET"
fi

case "$TARGET" in
    fish) install_fish ;;
    bash) install_bash ;;
    zsh)  install_zsh ;;
    all)
        install_fish
        install_bash
        install_zsh
        ;;
    *)
        echo "Usage: $0 [fish|bash|zsh|all]"
        exit 1
        ;;
esac

echo ""
echo "Done. Remote session URLs will be saved to ~/.claude-remote-sessions/sessions.txt"
echo ""
echo "To uninstall:"
echo "  fish: rm ~/.config/fish/functions/claude.fish"
echo "  bash: remove the 'claude-remote-collector' line from ~/.bashrc"
echo "  zsh:  remove the 'claude-remote-collector' line from ~/.zshrc"
