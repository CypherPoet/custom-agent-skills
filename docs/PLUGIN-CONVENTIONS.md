# Plugin Conventions

This repo applies a handful of conventions on top of Claude Code's standard plugin shape. Use [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) as the canonical scaffold workflow, then apply the deltas below. Don't commit until the staged files have been reviewed.

For plugin anatomy (component types, auto-discovery, `${CLAUDE_PLUGIN_ROOT}` usage, `hooks.json` shape, MCP transport fields, etc.), defer to the canonical sources:

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [`plugin-dev:plugin-structure`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/plugin-structure) — manifest fields, component patterns, examples
- [`plugin-dev:skill-development`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/skill-development) — skill creation methodology
- [`plugin-dev:hook-development`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/hook-development) — hook patterns and validators
- [`plugin-dev:mcp-integration`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/mcp-integration) — MCP server integration

## Plugin Folder

- Folder name, conventionally `cypherpoet-<theme>` (kebab-case). Use a `-kit` suffix for single-topic kits (e.g., `cypherpoet-blender-kit`).
- The folder name must equal the manifest `name` field (this is a Claude Code platform requirement; restated here so the repo convention is unambiguous).

## Manifest Deltas

`/plugin-dev:create-plugin` produces a working `plugin.json`. This repo additionally requires:

- **`author`** — always `{ "name": "CypherPoet" }`.
- **`version`** — **omit it.** The commit SHA serves as the version, so updates flow automatically every time `main` advances. `claude plugin validate` warns about the missing field — that warning is expected and intentional. Only set `version` if you specifically want gated releases for a plugin.
- **`homepage`** — `"https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/<name>"`.
- **`repository`** — `"https://github.com/CypherPoet/custom-agent-skills.git"` (plain URL string; the schema rejects the npm-style `{type, url, directory}` object form).
- **`license`** — `"MIT"`.
- **`keywords`** — 4–6 lowercase kebab-case tags. Always start with `"claude-code"`, then the plugin's domain (`git`, `blender`, `svg`, …), then standout features.

See any existing manifest under `plugins/*/.claude-plugin/plugin.json` for the exact shape and field ordering.

## Validate

After scaffolding and applying the deltas, run:

```shell
claude plugin validate plugins/<plugin-name>
```

A single `version: No version specified` warning is expected (the SHA-as-version convention). Anything else means something needs a closer look — fix it before opening a PR.

## Per-Plugin README

Each plugin ships a `README.md` at its root, **not** `CATALOG.md` — that name is reserved for the top-level cross-plugin catalog. `/plugin-dev:create-plugin` generates a README template; this repo's specific additions are the Installation snippet and the per-component-type table format:

````markdown
# <plugin-name>

<one-sentence description, identical to the manifest description, ending in a period>

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install <plugin-name>@cypherpoet-toolchest
```

## Skills

| Skill | Description |
|---|---|
| [<skill-name>](skills/<skill-name>/SKILL.md) | <one-sentence summary>. |

## Commands

| Command | Description |
|---|---|
| [/<plugin-name>:<command>](commands/<command>.md) | <one-sentence summary>. |

## Agents

| Agent | Description |
|---|---|
| [<agent-name>](agents/<agent-name>.md) | <one-sentence summary>. |

## Hooks

| Hook | Description |
|---|---|
| `<EventName>` | <what the hook does>. See [hooks/hooks.json](hooks/hooks.json). |

## MCP Servers

| Server | Description |
|---|---|
| `<server-name>` | <what the server provides>. |
````

Only include the section per component type the plugin actually ships — drop the rest. A skills-only plugin's README has just `## Skills`. Replace `<plugin-name>` placeholder with the actual slug when copying the install command.

## Top-Level Catalog

After creating a new plugin, add a row to [CATALOG.md](CATALOG.md). The `Components` column uses text form: `5 skills`, `1 skill`, `2 commands, 1 hook` — singular for one, plural otherwise. List components in the order skills → commands → agents → hooks → MCP servers, dropping zeros.

Editing an *existing* plugin's content (adding a skill, fixing a typo) needs no catalog change. Only *adding a new plugin* warrants a catalog update.

## Publishing

After the plugin is ready, use the `marketplace-publish` skill to open a PR on the `cypherpoet-toolchest` marketplace. Scaffolding alone never publishes — the catalog only changes when you explicitly publish.

## Skill Conventions

For new or revised skills inside a plugin, use [`/skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator). It handles drafts, evals, and description optimization.

- **Folder name** — kebab-case, matching the `name:` field in `SKILL.md`'s frontmatter. The two must agree.
- **`description:` field** — this is the trigger blurb Claude reads to decide whether to invoke the skill. Write it for matching (likely user phrasings, edge cases, related intents), not for humans. Long descriptions should use the YAML `>` block scalar so the file stays readable.
- **Optional subdirs** — a skill folder may also include `assets/` (output templates), `references/` (supporting docs loaded on demand), `scripts/` (helper executables), and `evals/` (eval test cases). Only create them when the skill actually needs them.
- **Workspace scratch** — `*-workspace/` directories under any `skills/` folder (including the repo-local `.claude/skills/`) are gitignored. These are transient directories created during eval iteration; they are not real skills.
