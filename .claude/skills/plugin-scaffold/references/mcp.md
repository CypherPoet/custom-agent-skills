# MCP servers

MCP (Model Context Protocol) servers expose tools and resources Claude can call. Unlike skills, commands, agents, and hooks, **MCP servers are not auto-discovered** — they must be declared explicitly.

## Two declaration styles

Prefer **embedding in the manifest** for plugins shipping a small number of servers. It keeps the surface area visible in one place and avoids an extra file:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin.json",
  "name": "cypherpoet-<theme>",
  "description": "...",
  "author": { "name": "CypherPoet" },
  "mcpServers": {
    "<server-name>": {
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/server.py"
    }
  }
}
```

For larger sets of servers, use a sibling `.mcp.json` file at the plugin root with the same `mcpServers` shape. **A sibling `.mcp.json` is not auto-discovered** — the manifest must point at it with `"mcpServers": "./.mcp.json"` (relative paths can be omitted but matching the manifest field is mandatory). Document the choice in the plugin's `README.md` so consumers know where to look.

## `${CLAUDE_PLUGIN_ROOT}` is mandatory for local servers

Any `command` or `args` path that points at a file inside the plugin must start with `${CLAUDE_PLUGIN_ROOT}/`. The plugin lands at unpredictable paths on consumers' machines; hardcoded absolute paths will fail. Same rule, same reason as [hooks](hooks.md).

Network-based servers (HTTP / SSE) don't reference local paths — they reference URLs — so this rule doesn't apply to them.

## Transport types

Each server entry declares one transport. Pick based on how the server runs:

### `stdio` — subprocess, talks over stdin/stdout

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/fs-server.py",
      "args": ["--root", "${CLAUDE_PLUGIN_ROOT}/data"],
      "env": {
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

`command` (required), `args` (optional, array), `env` (optional, object) are the standard fields.

### `http` — remote server reached over HTTP

```json
{
  "mcpServers": {
    "issue-tracker": {
      "type": "http",
      "url": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${ISSUE_TRACKER_TOKEN}"
      }
    }
  }
}
```

Claude Code also accepts `"type": "streamable-http"` as an alias for `"http"`.

### `sse` — Server-Sent Events stream

```json
{
  "mcpServers": {
    "live-feed": {
      "type": "sse",
      "url": "https://example.com/mcp/events"
    }
  }
}
```

The field is `type`, not `transport` — that's the manifest field name; `--transport` is only the CLI flag for `claude mcp add`. Getting this wrong is a silent failure: Claude Code parses the entry as a malformed stdio server with no `command` and warns at startup.

## Runtime dependencies

A local stdio server usually needs language-specific dependencies installed (Python packages, Node modules, etc.). The plugin install doesn't install those for the consumer — call them out in the plugin's `README.md` under a Requirements or Setup section so users know what to install before the server will work.

## Minimal stub for scaffolding

The smallest viable entry — local stdio script with no args or env:

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/server.py"
    }
  }
}
```

Add `args`, `env`, or switch to `http`/`sse` only when the actual server needs them.
