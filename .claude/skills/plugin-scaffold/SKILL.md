---
name: plugin-scaffold
description: >
  Use whenever the user wants to start, create, or add a new plugin
  in this repo: "scaffold a plugin", "new plugin for X", "set up a
  plugin that …", "add a plugin called …", "scaffold a plugin with
  a slash command / agent / hook / MCP server". Creates the manifest,
  README, and the first item of any component type (skills, slash
  commands, subagents, hooks, MCP servers) under `plugins/<name>/`,
  following this repo's conventions and the [plugins-reference](https://code.claude.com/docs/en/plugins-reference)
  best practices. Local only — no commits, no marketplace changes;
  for publishing, hand off to the marketplace-publish skill.
---

# plugin-scaffold

Create the files for a new plugin under `plugins/<name>/`, matching this repo's conventions and the [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference) best practices, so it's ready to fill in and later publish. **Local only**: no commits, no marketplace changes.

## Repo conventions (match these exactly)

A plugin lives at `plugins/<plugin-name>/`. Only `.claude-plugin/plugin.json` and `README.md` are required; every other directory is optional and only created when the user picks that component type.

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json        # manifest — see references/manifest.md
├── README.md              # purpose, install, component index — see references/readme.md
├── skills/                # optional — see references/skills.md
│   └── <skill-name>/SKILL.md
├── commands/              # optional — see references/commands.md
│   └── <command>.md
├── agents/                # optional — see references/agents.md
│   └── <agent>.md
├── hooks/                 # optional — see references/hooks.md
│   └── hooks.json
└── scripts/               # any helper scripts referenced from hooks / MCP entries
    └── …
```

Repo-specific rules the scaffold always honors:

- **Plugin folder name**: kebab-case, conventionally `cypherpoet-<theme>` (use a `-kit` suffix for single-topic kits, e.g. `cypherpoet-blender-kit`). Confirm by glancing at a sibling under `plugins/`.
- **Skill / command / agent file or folder names**: kebab-case, matching their `name:` frontmatter.
- **Author**: always `{"name": "CypherPoet"}` in the manifest.
- **`version` is opt-in.** Default is to omit it — the commit SHA serves as the version (matches all existing plugins; `claude plugin validate` warns about the absence, which is expected). Include a semver string only when the user explicitly wants gated releases for this plugin.
- **`${CLAUDE_PLUGIN_ROOT}` for portable paths.** Any path referenced from a hook command or MCP server config *must* start with `${CLAUDE_PLUGIN_ROOT}/`. Consumers install the plugin at unpredictable paths on their machines, so absolute paths in this source repo will break for everyone else.
- **Auto-discovery does the heavy lifting.** When `skills/`, `commands/`, `agents/`, and `hooks/hooks.json` sit at default locations, the manifest doesn't need to declare them. Only add explicit path entries for components that deviate (MCP servers always need an `mcpServers` block; categorized command/agent layouts may need explicit arrays).

## Workflow

1. **Gather inputs in one round.** Ask for:
   - Plugin name (must be `cypherpoet-<theme>` kebab-case).
   - One-sentence plugin description (8–12 words, no markdown, no emoji).
   - Whether to include a `version` field in the manifest. Default *no*. If yes, ask for the initial version string (default `0.1.0`).
   - Which component types the plugin ships — multi-select from: skills, slash commands, subagents, hooks, MCP servers. Default skills-only when the user is unsure.
   - For each picked component type, the first item's identifier + a one-line description. The shape of "identifier" varies:
     - **Skills, slash commands, subagents** → a kebab-case name (file/folder name + `name:` frontmatter).
     - **Hooks** → the event name (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, etc.) and what the hook should do; the hook isn't "named" — it's bound to an event.
     - **MCP servers** → the server's logical name (used as the key in `mcpServers`), its transport (`stdio` / `http` / `sse`), and a brief description.

2. **Propose the file plan.** Enumerate every file you'll create and every existing file you'll modify (the manifest, the README, each component stub, the top-level `docs/CATALOG.md` row). Wait for the user's go-ahead.

3. **Create the chosen component dirs.** For each picked component, read the matching reference file and drop in a minimal starter that the user (or `/skill-creator`) can grow:
   - **Skills** → `skills/<name>/SKILL.md`. See [references/skills.md](references/skills.md) — frontmatter shape, triggers-first description style, optional subdirs.
   - **Slash commands** → `commands/<name>.md`. See [references/commands.md](references/commands.md) — frontmatter (`description`, optional `argument-hint`, `model`, `allowed-tools`) and the prompt body.
   - **Subagents** → `agents/<name>.md`. See [references/agents.md](references/agents.md) — frontmatter and a stub system prompt.
   - **Hooks** → `hooks/hooks.json` plus a companion script under `scripts/<name>.sh`. See [references/hooks.md](references/hooks.md) — event names, matcher syntax, `${CLAUDE_PLUGIN_ROOT}` rule, and the current `hookSpecificOutput` decision schema.
   - **MCP servers** — no separate file is created in this step; the server entries are written directly into the manifest's `mcpServers` block in step 4. See [references/mcp.md](references/mcp.md) — `type` field (not `transport`), transport-specific fields, and the `${CLAUDE_PLUGIN_ROOT}` rule.

4. **Write the manifest.** See [references/manifest.md](references/manifest.md) for the field reference. The default 4-field manifest (`$schema`, `name`, `description`, `author`) covers every layout that relies on auto-discovery. On top of that, add:
   - A `version` field if the user opted in (step 1).
   - An `mcpServers` block if the user picked MCP servers (step 1). This must be written into the manifest in this same pass — MCP servers aren't auto-discovered. See [references/mcp.md](references/mcp.md).

5. **Create the plugin's `README.md`.** See [references/readme.md](references/readme.md) for the template. Sections: H1 plugin name, one-sentence description, **Installation**, then one `## Skills` / `## Commands` / `## Agents` / `## Hooks` / `## MCP Servers` block per component type the plugin actually ships — each a small table linking into the relevant file.

6. **Update [docs/CATALOG.md](../../../docs/CATALOG.md).** Add an alphabetically-placed row pointing at `plugins/<name>/README.md`. The `Components` column uses the text form `<N> <type>` — e.g., `3 skills`, `1 skill`, `2 commands, 1 hook`. List components in the order skills → commands → agents → hooks → MCP servers, dropping zeros.

7. **Validate.** Run `claude plugin validate plugins/<name>`. A missing-`version` warning is expected when version was omitted — call this out so the user doesn't try to "fix" it.

8. **Do not commit.** Tell the user the files are staged in their working tree to review.

## Naming and style rules

- Kebab-case everywhere: plugin folder = manifest `name`; component file/folder = its `name:` frontmatter.
- Plugin descriptions are one ~8–12-word sentence; no markdown, no emoji.
- Skill `description:` field puts **triggers first** (when Claude should invoke the skill), then a brief workflow summary. Use the YAML block scalar `>` form for descriptions longer than one line so the file stays readable.
- Slash-command names become `/<plugin-name>:<command-name>` once installed — pick names that read well in that context.
- Agent `description:` describes invocation *context*, not just the agent's job.

## Follow-up

Once the plugin's content is ready and the user wants it in the marketplace, point them at the **marketplace-publish** skill — that's what opens the catalog PR. Scaffolding alone never publishes anything.
