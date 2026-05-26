# Plugin `README.md`

Every plugin has a `README.md` at its root. The README is the consumer's first stop after they install the plugin: it should answer *what is this for*, *how do I install it*, and *what's inside*.

This file is **not** `CATALOG.md` — that older name is a vestige from when the repo held a single skills catalog. The per-plugin `README.md` plays the docs role; the cross-plugin index at `docs/CATALOG.md` (repo root) is the catalog and keeps its name.

## Section structure

In order:

1. **H1** — the plugin name (matches the manifest `name` and the folder name).
2. **Description** — one sentence, sentence-case, identical to the manifest `description` field. Plain text, no formatting.
3. **Installation** — the marketplace add + install snippet.
4. **One section per component type the plugin ships** — Skills / Commands / Agents / Hooks / MCP Servers. Each is a small table linking to the source file. Skip the sections for component types the plugin doesn't ship.

Keep the README dense and scannable. Don't restate the manifest description, don't write an "Overview" preamble, don't add badges.

## Template

The outer fence below is 4 backticks so the inner 3-backtick code fences pass through cleanly. Drop the outer fence when copying.

````markdown
# <plugin-name>

<one-sentence description from plugin.json>

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
| [<skill-name>](skills/<skill-name>/SKILL.md) | <one-sentence description>. |

## Commands

| Command | Description |
|---|---|
| [/<plugin-name>:<command>](commands/<command>.md) | <one-sentence description>. |

## Agents

| Agent | Description |
|---|---|
| [<agent-name>](agents/<agent-name>.md) | <one-sentence description>. |

## Hooks

| Event | Action |
|---|---|
| `<EventName>` | <what the hook does>. See [hooks/hooks.json](hooks/hooks.json). |

## MCP Servers

| Server | Description |
|---|---|
| `<server-name>` | <what the server provides>. |
````

Only include the component-type sections the plugin actually ships — drop the rest. A skills-only plugin's README has just `## Skills`.

## Style notes

- Per-row descriptions in the tables are sentence-case, ending in a period. Match the brevity of the existing per-plugin READMEs — typically one short clause, not a sentence with subordinate clauses.
- Skill descriptions in the README table are abridged for scannability; the full trigger blurb lives in the skill's frontmatter `description` field.
- The Installation block's `marketplace add` line is safe to re-run; the `# Skip if you've already added this marketplace` comment makes that explicit so consumers don't think it's mandatory.
- The README is what travels with the plugin during a sparse-clone install — assume the reader sees only this file and the rest of the plugin's directory, not the rest of the repo.
