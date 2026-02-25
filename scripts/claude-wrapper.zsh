# Zsh wrapper function for Claude Code
# Captures remote session URLs from terminal output.
# Records on startup (so you can access running sessions) with exit fallback.
#
# Installation:
#   Add to ~/.zshrc:
#     source /path/to/claude-wrapper.zsh

claude() {
    local tmpfile
    tmpfile=$(mktemp /tmp/claude-capture.XXXXXX)

    # Ensure tmpfile is cleaned up on exit/error/interrupt
    trap 'rm -f "$tmpfile" "$tmpfile.recorded"' EXIT INT TERM

    # Start detached background watcher to capture URL on startup
    # I/O redirected to avoid terminal interference with script(1)
    sh -c '
        tmpfile="$1"
        i=0
        while [ $i -lt 60 ]; do
            if [ -f "$tmpfile" ] && [ -s "$tmpfile" ]; then
                url=$(grep -Eo "https://claude\.ai/code/session_[^[:space:]]+" "$tmpfile" 2>/dev/null | head -1)
                if [ -n "$url" ]; then
                    claude-remote-collector record --url "$url" --source startup --notify 2>/dev/null
                    touch "$tmpfile.recorded"
                    break
                fi
            fi
            sleep 0.5
            i=$((i + 1))
        done
    ' _ "$tmpfile" </dev/null >/dev/null 2>/dev/null &
    local watcher_pid=$!
    disown $watcher_pid 2>/dev/null

    # Build properly quoted command string
    local cmd="command claude"
    local arg
    for arg in "$@"; do
        cmd+=" ${(q)arg}"
    done

    # Run claude inside `script` to capture TUI output
    # -f flushes after each write so the background watcher can read in real-time
    command script -qf -c "$cmd" "$tmpfile"
    local exit_code=$?

    # Kill watcher if still running
    kill $watcher_pid 2>/dev/null

    # Record on exit only if startup watcher didn't capture it
    if [ ! -f "$tmpfile.recorded" ]; then
        local url
        url=$(grep -Eo 'https://claude\.ai/code/session_[^[:space:]]+' "$tmpfile" | head -1)
        if [[ -n "$url" ]]; then
            command claude-remote-collector record --url "$url" --source exit --notify 2>/dev/null
        fi
    fi

    trap - EXIT INT TERM
    rm -f "$tmpfile" "$tmpfile.recorded"
    return $exit_code
}
