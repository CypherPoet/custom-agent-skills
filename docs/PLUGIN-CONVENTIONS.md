# Plugin Conventions

This repo applies a handful of conventions on top of the standard plugin shape, and ships every plugin for **both Claude Code and Codex** (see [Dual-Harness Plugins](#dual-harness-plugins)). Scaffold with your harness's toolkit — Claude Code's [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) or Codex's [`$plugin-creator`](https://github.com/openai/skills/blob/main/skills/.system/plugin-creator/SKILL.md) — then apply the deltas below. Don't commit until the staged files have been reviewed.

For plugin anatomy (component types, auto-discovery, `${CLAUDE_PLUGIN_ROOT}` usage, `hooks.json` shape, MCP transport fields, etc.), defer to the canonical sources:

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [`plugin-dev` toolkit](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/README.md) — Claude's plugin-authoring toolkit: the `/plugin-dev:create-plugin` workflow plus all seven authoring skills (the four linked below, plus command/agent/settings development)
- [Codex: Build skills](https://learn.chatgpt.com/docs/build-skills) / [Build plugins](https://learn.chatgpt.com/docs/build-plugins) — the Codex plugin + skill format
- [Codex `plugin-creator`](https://github.com/openai/skills/blob/main/skills/.system/plugin-creator/SKILL.md) — the `$plugin-creator` scaffolder spec: the `.codex-plugin/plugin.json` shape, name normalization, and Codex marketplace entry format
- [`plugin-dev:plugin-structure`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/plugin-structure) — manifest fields, component patterns, examples
- [`plugin-dev:skill-development`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/skill-development) — skill creation methodology
- [`plugin-dev:hook-development`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/hook-development) — hook patterns and validators
- [`plugin-dev:mcp-integration`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/mcp-integration) — MCP server integration

Scaffold with whichever toolkit your harness gives you. What neither one knows is this repo's shape: a plugin's source of truth is its `.claude-plugin/plugin.json` plus an entry in [`scripts/plugin-registry.json`](../scripts/plugin-registry.json), and [`scripts/sync_plugins.py`](../scripts/sync_plugins.py) derives every `.codex-plugin/plugin.json` and Codex catalog entry from those. So a scaffolder's Codex manifest is a starting point that the sync will regenerate — `plugin-creator` doubles as the spec for what that generated output must conform to (manifest shape, name normalization, `policy`/`category` fields).

## Plugin Folder

- Folder name, conventionally `cypherpoet-<theme>` (kebab-case). Use a `-kit` suffix for single-topic kits (e.g., `cypherpoet-blender-kit`).
- The folder name must equal the manifest `name` field (this is a Claude Code platform requirement; restated here so the repo convention is unambiguous).

## Manifest

A working `plugin.json` needs the standard fields (see the [plugins reference](https://code.claude.com/docs/en/plugins-reference)); [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) generates one in Claude Code. Recommended defaults this repo applies on top:

- Set `"author": { "name": "CypherPoet" }` (no email field).
- Set `"version": "0.1.0"` for new plugins. Bump per semver as the plugin evolves: PATCH for fixes, MINOR for additive changes, MAJOR for breaking changes (pre-1.0, treat MINOR as the default bump for anything user-visible). This is each harness's update cache key (Claude Code resolves it from `plugin.json` first, with the `git-subdir` commit SHA only as the fallback when no version is set) — so existing installs update *only* when you bump it; pushing new commits to `main` alone won't reach them.
- Add `"license": "MIT"`.
- Add `"keywords"`: 4–6 lowercase kebab-case tags, leading with `"claude-code"` and the plugin's domain (`git`, `blender`, `svg`, …).

See any existing manifest under `plugins/*/.claude-plugin/plugin.json` for canonical shape and the standard fields (`$schema`, `homepage`, `repository`) worth including for catalog and IDE support.

## Dual-Harness Plugins

Plugins target **both** Claude Code and Codex. Each plugin is **self-contained**: install pulls only its own directory (Claude Code `git-subdir` sparse-clone; Codex marketplace fetch), so a plugin must physically ship every skill it needs. Neither harness resolves a reference to a skill in another plugin, and Codex has no plugin-to-plugin dependency mechanism — so composition is by **vendoring** (copying a skill into each plugin that ships it), never dependencies.

[`scripts/plugin-registry.json`](../scripts/plugin-registry.json) is the single source of truth; [`scripts/sync_plugins.py`](../scripts/sync_plugins.py) generates every derived artifact and, with `--check`, fails on drift (the repo-local `skill-structure-check` runs this check). **After editing a `.claude-plugin/plugin.json`, the registry, or the source of a vendored skill, run `python3 scripts/sync_plugins.py`.** Never hand-edit a generated file.

### Manifests

A dual-harness plugin carries two manifests over a shared `skills/` directory:

- `.claude-plugin/plugin.json` — hand-authored, the source of truth (see [Manifest](#manifest)).
- `.codex-plugin/plugin.json` — **generated** from the Claude manifest: the same `name`/`version`/`description`/`author`/`homepage`/`repository`/`license`/`keywords`, plus `"skills": "./skills/"` (no `$schema`). Don't edit it.

A plugin whose function is Claude-Code-specific runs on Claude only: list it in `plugin-registry.json`'s `claude_only_plugins` (with a reason) and it gets no `.codex-plugin/` manifest.

### Vendoring

When a plugin needs a skill authored elsewhere — its own skill functionally builds on it, or it curates a set — the source skill is **copied (vendored)** into the plugin. Declare the edge in `plugin-registry.json` under `vendored_skills` (`source` → `targets`) and run the sync.

- The skill is authored **once**, in its owner plugin. Every target is a byte-identical generated copy (minus dev-only `evals/` and `*-workspace/`). Edit the source, never a copy.
- The generator keeps no state of its own; git is the safety net. Removing an edge retires the copy on the next sync run — deleted only when `git status` under it is clean (committed content is always recoverable), refused otherwise. A skill directory byte-identical to a declared source but not a declared target is flagged as an undeclared copy, so to adopt a retired copy as authored, keep the directory and change its content (even one line).
- Targets vendor from the **original source**, never from another vendored copy.
- A vendored copy ships inside a different plugin, so any link it makes to *another* plugin must be an absolute GitHub URL ([Cross-Plugin Links](#cross-plugin-links)) — the copy inherits the source's links, and well-formed skills already satisfy this.
- Vendored copies are tiered `never` in the [fact-check manifest](#fact-check-tiering): the routine corrects the authoritative source, and the sync propagates the fix.

A **curated bundle** — a plugin that ships several skills it doesn't author (e.g. `git-flow` = `emoji-commits` + `changelog-maintenance`) — is just an ordinary plugin that vendors them. Keep a bundle only when its members share harness-applicability; one whose members split across Claude-only and dual-harness is better dissolved into its already-standalone members.

### Marketplaces

The separate [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace repo carries **two catalog files**, maintained together by the `marketplace-publish` flow (see [Publishing](#publishing)):

- `.claude-plugin/marketplace.json` — the Claude Code catalog. Consumers: `/plugin marketplace add CypherPoet/cypherpoet-toolchest`.
- `.agents/plugins/marketplace.json` — the Codex catalog (`git-subdir` entries pointing back at this repo, plus each plugin's `category` from [`scripts/plugin-registry.json`](../scripts/plugin-registry.json)). Consumers: `codex plugin marketplace add CypherPoet/cypherpoet-toolchest`.

## Validate

After scaffolding and applying the deltas, run:

```shell
claude plugin validate plugins/<plugin-name>
```

No warnings or errors expected. Anything else means something needs a closer look — fix it before opening the PR **on this repo** (a separate publish PR happens later on the marketplace repo via `marketplace-publish`).

## Per-Plugin README

Each plugin ships a `README.md` at its root, **not** `CATALOG.md` — that name is reserved for the top-level cross-plugin catalog. `/plugin-dev:create-plugin` generates a README template; this repo's specific additions are the Installation snippet and the per-component-type table format:

````markdown
# <plugin-name>

<one-sentence description, identical to the manifest description, ending in a period>

## Installation

Install via the marketplace this plugin is published to:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add <marketplace-owner>/<marketplace-repo>

# Install this plugin
/plugin install <plugin-name>@<marketplace-name>
```

On Codex, add the same marketplace: `codex plugin marketplace add <marketplace-owner>/<marketplace-repo>`, then `codex plugin add <plugin-name>@<marketplace-name>`.

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

Configured in [hooks/hooks.json](hooks/hooks.json):

| Event | Description |
|---|---|
| `<EventName>` | <what the hook does>. |

## MCP Servers

| Server | Description |
|---|---|
| `<server-name>` | <what the server provides>. |
````

Only include the section per component type the plugin actually ships — drop the rest. A skills-only plugin's README has just `## Skills`. Append a row to the matching table whenever a component is added — the per-plugin README is its primary index, and PR review treats a missing row as a defect.

A plugin's `## Skills` table lists **every** skill it ships, including any vendored in from another plugin ([Vendoring](#vendoring)) — refresh it whenever the sync adds or removes one.

When copying the install command, replace **all** placeholders: `<plugin-name>` with the plugin's slug, `<marketplace-owner>/<marketplace-repo>` with the GitHub path of the marketplace repo, and `<marketplace-name>` with the marketplace's `name` field from its `marketplace.json` (often the same as the repo name). For plugins published to this repo's marketplace (the default for everything currently in `plugins/`), those resolve to a fixed pair: `CypherPoet/cypherpoet-toolchest` and `cypherpoet-toolchest`. The shipped READMEs already use those values verbatim — the placeholder form only matters when scaffolding for a *different* marketplace.

## Top-Level Catalog

After creating a new plugin, add a row to [CATALOG.md](CATALOG.md). The `Components` column uses text form: `5 skills`, `1 skill`, `2 commands, 1 hook` — singular for one, plural otherwise. List components in the order skills → commands → agents → hooks → MCP servers, dropping zeros.

Refresh the catalog row whenever a plugin's component counts change (adding a skill bumps `5 skills` → `6 skills`) or a new plugin lands. In-place edits that don't shift the counts (typo fixes, prose tweaks, internal refactors) need no catalog change.

Rather than hand-editing, regenerate the whole table from the manifests by invoking the [`catalog-refresh`](../plugins/cypherpoet-marketplace-kit/skills/catalog-refresh/SKILL.md) skill (from the `cypherpoet-marketplace-kit` plugin); `marketplace-sync-check` reports when a refresh is due.

## Publishing

After the plugin is ready, use the `marketplace-publish` skill to open a PR on the marketplace this repo publishes to. One publish maintains both catalog files there — the Claude entry and, for dual-harness plugins, the Codex entry (see [Marketplaces](#marketplaces)). Scaffolding alone never publishes — the catalogs only change when you explicitly publish.

A plugin's `version` (in `.claude-plugin/plugin.json`) is each harness's update cache key, so edits to a plugin's **content** (skills, scripts) reach existing installs only when you **bump that version** — pushing commits to `main` alone won't update them (a *fresh* install always pulls `main`'s latest). Re-run `scripts/sync_plugins.py` after a bump so the generated `.codex-plugin` version matches. Separately, the catalogs store their own copy of each plugin's `name`, `description`, and `homepage` (Claude) and its classification + `category` (Codex) — editing any of those requires running `marketplace-publish` again to refresh the entry. Content ships on a version bump; catalog metadata ships on a re-publish.

## Skill Conventions

Skills inside a plugin follow the standard [`SKILL.md`](https://agentskills.io/) format. [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) automates the tedious parts — drafts, evals, description optimization, and the general skill structure conventions — and is worth using wherever it's installed.

The repo-local **`skill-structure-check`** skill audits skill structure across the repo. Its [`SKILL.md`](../.claude/skills/skill-structure-check/SKILL.md) is the canonical rule contract and remediation guide; the bundled Python script implements that contract. Run the skill before opening a PR that touches skills.

### Primary Sources

Every skill the fact-check routine covers (see [Fact-Check Tiering](#fact-check-tiering)) ends its `SKILL.md` with a **`## Primary Sources`** section — the skill's declared set of canonical verification sources, one bullet per source:

```markdown
## Primary Sources

- [Three.js releases](https://github.com/mrdoob/three.js/releases) — release channel; authoritative for versions.
- [Three.js documentation](https://threejs.org/docs/) — official API reference; authoritative for API syntax.
```

Each bullet says what the source is authoritative for (releases/versions, specs, API syntax, …). **Vendor-primary only** — official docs, release channels, spec registries; no blogs, aggregators, or forums. The [`skill-fact-check`](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/SKILL.md) routine reads this section as the skill's declared source set — how it consumes it, and how it interplays with per-fact `**Source:**` markers and `## Change-Signal Sources` leads, is defined in that skill's verification procedure (don't restate it here). A skill with nothing citable yet keeps the section as a placeholder — `None declared yet — the fact-check routine falls back to vendor-primary sources per claim.` — so there's a slot to fill in later. This section complements `## See Also` (related skills, tutorials, community links); a canonical doc URL may legitimately appear in both.

### Fact-Check Tiering

When creating (or renaming/removing) a skill, classify its unit — `<plugin>/<skill>` — into a tier in [`docs/automated-routines/skill-fact-check-manifest.json`](automated-routines/skill-fact-check-manifest.json); the tier definitions live in the `skill-fact-check` skill's [Manifest reference](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/SKILL.md#manifest-reference) (don't restate them here). Every unit is listed exactly once; an unlisted unit still safely defaults to monthly, and `skill-structure-check` reports untiered, orphaned, or double-listed entries — and fact-checked units missing their [Primary Sources](#primary-sources) section — as non-failing advisories (the CI health suite runs the checker with `--strict`, where they do fail).

### Cross-Plugin Links

A skill's `SKILL.md` and `references/*.md` ship via a `git-subdir` sparse-clone that fetches **only** that plugin's own directory. A relative link that climbs out of the plugin into a sibling — `[threejs-mastery](../../../cypherpoet-threejs-kit/skills/threejs-mastery/SKILL.md)` — resolves when browsing this monorepo but is a **dead path in an installed copy**, because the sibling plugin isn't on disk. So **a link from one plugin's skill to a different plugin's file must be an absolute GitHub URL** — `https://github.com/CypherPoet/custom-agent-skills/blob/main/plugins/<plugin>/skills/<skill>/…` — which resolves in both contexts and matches how these See Also sections already link external docs. In-plugin links (`./references/…`, `../SKILL.md`, `../assets/…`) stay relative — they ship together in the sparse-clone. `check-skill-structure.py` enforces this: any skill-file link that resolves outside its own plugin is an ERROR.

The same rule covers the per-plugin `README.md`: it ships in the sparse-clone install alongside the skills, so a cross-plugin relative link there is just as dead in an installed copy — use an absolute GitHub URL there too. (`check-skill-structure.py` enforces this too: a README link that resolves outside its own plugin is the same ERROR as in a skill file.)

`*-workspace/` directories under any `skills/` folder are gitignored: they're transient eval-iteration scratch, not real skills.
