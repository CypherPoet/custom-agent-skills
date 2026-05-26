# Manifest (`.claude-plugin/plugin.json`)

Field reference and templates for this repo. The manifest sits at exactly `plugins/<plugin-name>/.claude-plugin/plugin.json`. The component directories (`skills/`, `commands/`, `agents/`, `hooks/`) live at the plugin root — **not** under `.claude-plugin/`.

## Fields

Two groups: the four core fields every plugin in this repo ships, and the four metadata fields that make the plugin self-describing for consumers.

### Core

| Field | Value | Validator |
|---|---|---|
| `$schema` | Always `"https://json.schemastore.org/claude-code-plugin.json"`. Enables IDE validation; ignored at runtime. | Optional |
| `name` | Kebab-case, equal to the plugin folder name. Conventionally `cypherpoet-<theme>`. | **Required** |
| `description` | One sentence, ~8–12 words, plain English. No markdown, no emoji. | Optional (warn) |
| `author` | Always `{ "name": "CypherPoet" }`. | Optional (warn) |

### Recommended metadata

| Field | Value | Why |
|---|---|---|
| `homepage` | `"https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/<plugin-name>"` | Where consumers land for docs — the plugin's directory on GitHub. Carries the per-plugin URL since `repository` can't. |
| `repository` | Plain URL string: `"https://github.com/CypherPoet/custom-agent-skills.git"`. The schema rejects the npm-style `{type, url, directory}` object form — `claude plugin validate` errors with `"expected string, received object"`. | Where source lives + where to file issues. |
| `license` | `"MIT"` (SPDX identifier) | Echoes the repo's top-level `LICENSE` so the plugin is self-contained on terms. |
| `keywords` | Array of 4–6 lowercase kebab-case tags, e.g. `["claude-code", "git", "changelog", "gitmoji"]` | Marketplace discoverability. Always include `"claude-code"` plus the plugin's domain (`git`, `blender`, `svg`, …) and any standout features. |

## Canonical template

The shape every new plugin starts from — core + metadata, skills-only, auto-discovery for components:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin.json",
  "name": "cypherpoet-<theme>",
  "description": "<one-sentence description>.",
  "author": { "name": "CypherPoet" },
  "homepage": "https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/cypherpoet-<theme>",
  "repository": "https://github.com/CypherPoet/custom-agent-skills.git",
  "license": "MIT",
  "keywords": ["claude-code", "<theme>", "<more-tags>"]
}
```

When the plugin's layout matches the auto-discovery defaults (`skills/`, `commands/`, `agents/`, `hooks/hooks.json`), this is all that's needed. Auto-discovery finds the components — declaring custom paths would shadow it, not supplement it.

## `version` — opt-in

Default: omit. The commit SHA serves as the version, so updates flow automatically every time `main` advances. `claude plugin validate` will warn about the missing field — that warning is expected.

When the user wants explicit, gated releases for this plugin, include a `version` field with a semver string (typical starting value `0.1.0`) inserted after `name`. Updates then reach consumers only when the maintainer bumps the field.

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
  "homepage": "https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/cypherpoet-<theme>",
  "repository": "https://github.com/CypherPoet/custom-agent-skills.git",
  "license": "MIT",
  "keywords": ["claude-code", "<theme>"],
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
