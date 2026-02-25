# Bash wrapper function for Claude Code
# Captures remote session URLs from terminal output after session ends.
#
# Installation:
#   Add to ~/.bashrc:
#     source /path/to/claude-wrapper.bash

claude() {
    local tmpfile
    tmpfile=$(mktemp /tmp/claude-capture.XXXXXX)

    # Ensure tmpfile is cleaned up on exit/error/interrupt
    trap 'rm -f "$tmpfile"' EXIT INT TERM

    # Build properly quoted command string
    local cmd="command claude"
    local arg
    for arg in "$@"; do
        cmd+=" $(printf '%q' "$arg")"
    done

    # Run claude inside `script` to capture TUI output
    command script -q -c "$cmd" "$tmpfile"
    local exit_code=$?

    # Extract remote session URL (POSIX-compatible grep)
    local url
    url=$(grep -Eo 'https://claude\.ai/code/session_[^[:space:]]+' "$tmpfile" | head -1)

    if [[ -n "$url" ]]; then
        command claude-remote-collector record --url "$url" 2>/dev/null
    fi

    trap - EXIT INT TERM
    rm -f "$tmpfile"
    return $exit_code
}
