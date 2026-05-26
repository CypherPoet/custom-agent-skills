# Hooks (`hooks/hooks.json` + `scripts/`)

A plugin's hooks live in `plugins/<plugin>/hooks/hooks.json`. The file is auto-discovered at that path — no manifest entry needed. Anywhere else and the manifest has to point at it explicitly.

Hooks let a plugin observe and react to Claude Code events. The `command` each hook runs is typically a small script under `scripts/` — keep the shell glue thin, do real work in the script.

## Why `${CLAUDE_PLUGIN_ROOT}` is mandatory

When the plugin is installed on a consumer's machine, its on-disk path is unpredictable (different home directory, different marketplace cache, different OS, etc.). Hardcoding an absolute path from this source repo will fail for everyone but you.

`${CLAUDE_PLUGIN_ROOT}` is the harness-provided variable that resolves to the plugin's actual root at runtime. **Every** command path referenced from `hooks.json` must start with it.

## `hooks.json` shape

```json
{
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<optional matcher — e.g. tool name regex>",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/<hook-name>.sh"
          }
        ]
      }
    ]
  }
}
```

Common event names: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `Notification`. Check the Claude Code hooks docs for the full list and matcher semantics — they evolve.

## Companion script convention

Pair each hook entry with a script at `scripts/<hook-name>.sh`:

- Shebang `#!/usr/bin/env bash` (or `#!/usr/bin/env python3` for Python).
- `set -euo pipefail` at the top of bash scripts — fail fast on errors and undefined variables.
- Mark executable: `chmod +x scripts/<name>.sh`.
- Read JSON event data from stdin; write JSON or plain text to stdout depending on the event.

## Minimal example

`hooks/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/log-bash.sh"
          }
        ]
      }
    ]
  }
}
```

`scripts/log-bash.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Read the event payload from stdin. Use printf, not echo —
# echo interprets backslash sequences and mangles JSON containing
# \n, \t, or Windows paths like C:\Users\foo before jq sees it.
event=$(cat)

# Extract the bash command (if any) and append it to a per-plugin log.
bash_command=$(printf '%s' "$event" | jq -r '.tool_input.command // empty')
if [[ -n "$bash_command" ]]; then
  log_dir="${HOME}/.cache/<plugin-name>"
  mkdir -p "$log_dir"
  printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$bash_command" >> "$log_dir/bash.log"
fi

# Default-allow: exit 0 with no stdout. (Claude Code treats a clean
# exit + empty output as "no decision, proceed normally".)
exit 0
```

### Returning a decision from a PreToolUse hook

To deny a tool call (or ask the user), emit a JSON object on stdout with the current `hookSpecificOutput` shape:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Plugin policy: that command isn't allowed here."
  }
}
```

`permissionDecision` is one of `allow`, `deny`, or `ask`. The older top-level `{"decision":"block"|"approve"}` form is deprecated — Claude Code may silently ignore it. Use `hookSpecificOutput` for any hook that wants to influence the decision.

The exact stdin schema, decision keys, and exit-code semantics differ per event — consult the Claude Code hooks documentation for the version you're targeting before promising specific behavior to the user. As a rule of thumb: emit nothing and exit 0 to let Claude Code proceed; emit `hookSpecificOutput` JSON when the hook needs to deny, ask, or modify.
