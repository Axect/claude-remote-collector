# Fish shell wrapper function for Claude Code
# Captures remote session URLs from terminal output.
# Records on startup (so you can access running sessions) with exit fallback.
#
# Installation:
#   source /path/to/claude-wrapper.fish
#   OR copy the function to ~/.config/fish/functions/claude.fish

function claude --wraps=claude --description "Claude Code with remote link capture"
    set -l tmpfile (mktemp /tmp/claude-capture.XXXXXX)

    # Start detached background watcher to capture URL on startup
    # Uses sh -c with I/O redirected to avoid terminal interference with script(1)
    command sh -c '
        tmpfile="$1"
        i=0
        while [ $i -lt 60 ]; do
            if [ -f "$tmpfile" ] && [ -s "$tmpfile" ]; then
                url=$(grep -Eo "https://claude\.ai/code/session_[^[:space:]]+" "$tmpfile" 2>/dev/null | head -1)
                if [ -n "$url" ]; then
                    claude-remote-collector record --url "$url" --source startup 2>/dev/null
                    touch "$tmpfile.recorded"
                    break
                fi
            fi
            sleep 0.5
            i=$((i + 1))
        done
    ' _ $tmpfile </dev/null >/dev/null 2>/dev/null &
    set -l watcher_pid $last_pid
    disown $watcher_pid 2>/dev/null

    # Run claude inside `script` to capture TUI output
    # -f flushes after each write so the background watcher can read in real-time
    command script -qf -c "command claude $argv" $tmpfile
    set -l exit_code $status

    # Kill watcher if still running
    kill $watcher_pid 2>/dev/null

    # Record on exit only if startup watcher didn't capture it
    if not test -f "$tmpfile.recorded"
        set -l url (grep -Eo 'https://claude\.ai/code/session_[^[:space:]]+' $tmpfile | head -1)
        if test -n "$url"
            command claude-remote-collector record --url "$url" --source exit 2>/dev/null
        end
    end

    rm -f $tmpfile "$tmpfile.recorded"
    return $exit_code
end
