# Plugin Conventions

This repo applies a handful of conventions on top of Claude Code's standard plugin shape. Use [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) as the canonical scaffold workflow, then apply the deltas below before committing.

For plugin anatomy (component types, auto-discovery, `${CLAUDE_PLUGIN_ROOT}` usage, `hooks.json` shape, MCP transport fields, etc.), defer to the canonical sources:
- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [`plugin-dev:plugin-structure`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/plugin-structure) — manifest fields, component patterns, examples
- [`plugin-dev:skill-development`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/skill-development) — skill creation methodology
- [`plugin-dev:hook-development`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/hook-development) — hook patterns and validators
- [`plugin-dev:mcp-integration`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/mcp-integration) — MCP server integration

## Manifest Deltas

`/plugin-dev:create-plugin` produces a working `plugin.json`. This repo additionally requires:

- **`name`** — `cypherpoet-<theme>` (kebab-case). Use a `-kit` suffix for single-topic kits (e.g., `cypherpoet-blender-kit`).
- **`author`** — always `{ "name": "CypherPoet" }`.
- **`version`** — **omit it.** The commit SHA serves as the version, so updates flow automatically every time `main` advances. `claude plugin validate` warns about the missing field — that warning is expected and intentional. Only set `version` if you specifically want gated releases for a plugin.
- **`homepage`** — `"https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/<name>"`.
- **`repository`** — `"https://github.com/CypherPoet/custom-agent-skills.git"` (plain URL string; the schema rejects the npm-style `{type, url, directory}` object form).
- **`license`** — `"MIT"`.
- **`keywords`** — 4–6 lowercase kebab-case tags. Always start with `"claude-code"`, then the plugin's domain (`git`, `blender`, `svg`, …), then standout features.

See any existing manifest under `plugins/*/.claude-plugin/plugin.json` for the exact shape and field ordering.

## Per-Plugin README

Each plugin ships a `README.md` at its root, **not** `CATALOG.md` — that name is reserved for the top-level cross-plugin catalog. `/plugin-dev:create-plugin` generates a README template; this repo's specific addition is the Installation snippet:

````markdown
## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install <plugin-name>@cypherpoet-toolchest
```
````

Match the existing `plugins/cypherpoet-git-flow/README.md` (or any sibling) for tone and section structure (`## Skills`, `## Commands`, etc. — one per component type the plugin actually ships, dropped otherwise).

## Top-Level Catalog

After creating a new plugin, add a row to [`docs/CATALOG.md`](CATALOG.md). The `Components` column uses text form: `5 skills`, `1 skill`, `2 commands, 1 hook` — singular for one, plural otherwise. List components in the order skills → commands → agents → hooks → MCP servers, dropping zeros.

Editing an *existing* plugin's content (adding a skill, fixing a typo) needs no catalog change. Only *adding a new plugin* warrants a catalog update.

## Publishing

After the plugin is ready, use the `marketplace-publish` skill to open a PR on the `cypherpoet-toolchest` marketplace. Scaffolding alone never publishes — the catalog only changes when you explicitly publish.

## Skill Development

For new or revised skills inside a plugin, use [`/skill-creator`](https://github.com/anthropics/skills/tree/main/skill-creator). It handles drafts, evals, and description optimization.

Skill folder names are kebab-case matching the `name:` field in `SKILL.md`'s frontmatter. `skills/*-workspace/` (under any plugin) is gitignored scratch space created by `/skill-creator` during eval iteration — not real skills.
