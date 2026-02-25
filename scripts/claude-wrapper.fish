# Fish shell wrapper function for Claude Code
# Captures remote session URLs from terminal output after session ends.
#
# Installation:
#   source /path/to/claude-wrapper.fish
#   OR copy the function to ~/.config/fish/functions/claude.fish

function claude --wraps=claude --description "Claude Code with remote link capture"
    set -l tmpfile (mktemp /tmp/claude-capture.XXXXXX)

    # Run claude inside `script` to capture TUI output
    command script -q -c "command claude $argv" $tmpfile
    set -l exit_code $status

    # Extract remote session URL from captured output (POSIX-compatible grep)
    set -l url (grep -Eo 'https://claude\.ai/code/session_[^[:space:]]+' $tmpfile | head -1)

    if test -n "$url"
        command claude-remote-collector record --url "$url" 2>/dev/null
    end

    rm -f $tmpfile
    return $exit_code
end
