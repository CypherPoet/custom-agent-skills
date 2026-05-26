# Manifest (`.claude-plugin/plugin.json`)

Field reference and templates for this repo. The manifest sits at exactly `plugins/<plugin-name>/.claude-plugin/plugin.json`. The component directories (`skills/`, `commands/`, `agents/`, `hooks/`) live at the plugin root — **not** under `.claude-plugin/`.

## Required fields

Every plugin in this repo ships these four fields, in this order:

| Field | Value |
|---|---|
| `$schema` | Always `"https://json.schemastore.org/claude-code-plugin.json"`. Enables IDE validation. |
| `name` | Kebab-case, equal to the plugin folder name. Conventionally `cypherpoet-<theme>`. |
| `description` | One sentence, ~8–12 words, plain English. No markdown, no emoji. |
| `author` | Always `{ "name": "CypherPoet" }`. |

## Minimal template (skills-only, default)

This is the exact shape used across every existing plugin in this repo:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin.json",
  "name": "cypherpoet-<theme>",
  "description": "<one-sentence description>.",
  "author": { "name": "CypherPoet" }
}
```

When the plugin's layout matches the auto-discovery defaults (`skills/`, `commands/`, `agents/`, `hooks/hooks.json`), this is all that's needed. Auto-discovery finds the components — declaring custom paths would shadow it, not supplement it.

## `version` — opt-in

Default: omit. The commit SHA serves as the version, so updates flow automatically every time `main` advances. `claude plugin validate` will warn about the missing field — that warning is expected.

When the user wants explicit, gated releases for this plugin, include a `version` field with a semver string (typical starting value `0.1.0`). Updates then reach consumers only when the maintainer bumps the field.

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin.json",
  "name": "cypherpoet-<theme>",
  "version": "0.1.0",
  "description": "<one-sentence description>.",
  "author": { "name": "CypherPoet" }
}
```

## Optional fields (not used in this repo today)

`homepage`, `repository`, `license`, `keywords` are valid manifest fields. None of the existing plugins use them — the marketplace catalog covers discovery and the repo's top-level `LICENSE` covers licensing. Only add when the user specifically asks.

## When path overrides *are* needed

Auto-discovery covers the defaults. Add explicit entries only when the layout deviates:

- **MCP servers**: always need an explicit `mcpServers` block — there's no auto-discovery for them. See [mcp.md](mcp.md).
- **Hooks at a non-default path**: add `"hooks": "./path/to/hooks.json"`. Prefer keeping the default `hooks/hooks.json` instead.
- **Categorized command/agent layouts**: if commands live under nested directories (e.g. `commands/git/`, `commands/test/`), add an explicit `"commands": ["./commands/git", "./commands/test"]` array. Same idea for agents.

## Multi-component template (with MCP)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin.json",
  "name": "cypherpoet-<theme>",
  "description": "<one-sentence description>.",
  "author": { "name": "CypherPoet" },
  "mcpServers": {
    "<server-name>": {
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/server.py"
    }
  }
}
```

Note the `${CLAUDE_PLUGIN_ROOT}` prefix — never hardcode an absolute path here. The plugin lands at unpredictable paths on consumers' machines.

## Validation

Run `claude plugin validate plugins/<name>` after creating the manifest. A missing-`version` warning is the only expected diagnostic when version was intentionally omitted; anything else means something needs a closer look.
