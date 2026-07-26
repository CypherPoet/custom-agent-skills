# Plugin Conventions

This repo applies a handful of conventions on top of the standard plugin shape, and ships every plugin for **both Claude Code and Codex** (see [Dual-Harness Plugins](#dual-harness-plugins)). Scaffold with Claude Code's [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md), then apply the deltas below. Don't commit until the staged files have been reviewed.

For plugin anatomy (component types, auto-discovery, `${CLAUDE_PLUGIN_ROOT}` usage, `hooks.json` shape, MCP transport fields, etc.), defer to the canonical sources:

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [`plugin-dev` toolkit](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/README.md) — the `/plugin-dev:create-plugin` workflow plus the seven authoring skills (plugin structure, and skill / command / agent / hook / MCP / settings development)
- [Codex: Build skills](https://learn.chatgpt.com/docs/build-skills) / [Build plugins](https://learn.chatgpt.com/docs/build-plugins) — the Codex plugin + skill format
- [Codex `plugin-creator`](https://github.com/openai/skills/blob/main/skills/.system/plugin-creator/SKILL.md) — the spec the **generated** Codex artifacts must match. It's a spec, not a tool run here: [`scripts/sync_plugins.py`](../scripts/sync_plugins.py) writes the `.codex-plugin/plugin.json` (manifest shape, name normalization), and the publish flow writes the marketplace entry (`policy`, `category`) — see [Marketplaces](#marketplaces).

## Plugin Folder

- Folder name, conventionally `cypherpoet-<theme>` (kebab-case). Use a `-kit` suffix for single-topic kits (e.g., `cypherpoet-blender-kit`).
- The folder name must equal the manifest `name` field.

## Manifest

Confirm these fields on the scaffolded `plugin.json` (match a sibling under `plugins/*/.claude-plugin/plugin.json`):

- `"$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json"`.
- `"name"` — equals the plugin folder name.
- `"version": "0.1.0"` for new plugins. **This is each harness's update cache key** — the version resolves from `plugin.json` first, with the `git-subdir` commit SHA only as the fallback when no version is set. So existing installs update *only* when you bump it; pushing new commits to `main` alone won't reach them. Bump per semver: PATCH for fixes, MINOR for additive changes, MAJOR for breaking changes (pre-1.0, treat MINOR as the default for anything user-visible).
- `"description"` — one sentence ending in a period. The per-plugin README and the Claude marketplace catalog copy it verbatim (the Codex catalog entry carries no description; see [Marketplaces](#marketplaces)).
- `"author": { "name": "CypherPoet" }` (no email field).
- `"homepage"` — `https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/<name>`.
- `"repository"` — `https://github.com/CypherPoet/custom-agent-skills.git`.
- `"license": "MIT"`.
- `"keywords"` — 4–6 lowercase kebab-case tags, leading with `"claude-code"` and the plugin's domain (`git`, `blender`, `svg`, …).

## Dual-Harness Plugins

Plugins target **both** Claude Code and Codex. Each plugin is **self-contained**: install pulls only its own directory (Claude Code `git-subdir` sparse-clone; Codex marketplace fetch), so a plugin must physically ship every skill it needs. Neither harness resolves a reference to a skill in another plugin, and Codex has no plugin-to-plugin dependency mechanism — so composition is by **vendoring** (copying a skill into each plugin that ships it), never dependencies.

[`scripts/plugin-registry.json`](../scripts/plugin-registry.json) is the single source of truth; [`scripts/sync_plugins.py`](../scripts/sync_plugins.py) generates every derived artifact and, with `--check`, fails on drift (the repo-local `skill-structure-check` runs this check).

### Manifests

A dual-harness plugin carries two manifests over a shared `skills/` directory:

- `.claude-plugin/plugin.json` — hand-authored, the source of truth (see [Manifest](#manifest)).
- `.codex-plugin/plugin.json` — **generated** from the Claude manifest: the same `name`/`version`/`description`/`author`/`homepage`/`repository`/`license`/`keywords`, plus `"skills": "./skills/"` (no `$schema`).

Dual-harness is the default. A plugin whose function is Claude-Code-specific runs on Claude only: list it in `plugin-registry.json`'s `claude_only_plugins` (with a reason) and it gets no `.codex-plugin/` manifest. Judge by skill **content**, not shape — `claude-docs-search`'s `SKILL.md` parses fine on Codex, but it searches Claude Code's own documentation, so it belongs on the list. Keep that list short; anything portable ships to both.

### Vendoring

When a plugin needs a skill authored elsewhere — its own skill functionally builds on it, or it curates a set — the source skill is **copied (vendored)** into the plugin. Declare the edge in `plugin-registry.json` under `vendored_skills` (`source` → `targets`) and run the sync.

- The skill is authored **once**, in its owner plugin. Every target is a byte-identical generated copy (minus dev-only `evals/` and `*-workspace/`). Edit the source, never a copy.
- Targets vendor from the **original source**, never from another vendored copy.
- The generator keeps no state of its own; git is the safety net. Removing an edge retires the copy on the next sync run — deleted only when `git status` under it is clean, refused otherwise. A skill directory byte-identical to a declared source but not a declared target is flagged as an undeclared copy, so to adopt a retired copy as authored, keep the directory and change its content (even one line).
- A vendored copy ships inside a different plugin, so any link it makes to *another* plugin must be an absolute GitHub URL ([Cross-Plugin Links](#cross-plugin-links)).
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

No warnings or errors expected. Anything else means something needs a closer look — fix it before opening the PR **on this repo** (a separate publish PR happens later on the marketplace repo).

That's the plugin-specific check. It doesn't replace the repo-wide PR gates — the test suite, `sync_plugins.py --check`, and `skill-structure-check` — which [`AGENTS.md`](../AGENTS.md) requires on every PR.

## Per-Plugin README

Each plugin ships a `README.md` at its root, **not** `CATALOG.md` — that name is reserved for the top-level cross-plugin catalog. `/plugin-dev:create-plugin` generates a README template; this repo's additions are the Installation snippet and the per-component-type tables:

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

On Codex, add the same marketplace: `codex plugin marketplace add CypherPoet/cypherpoet-toolchest`, then `codex plugin add <plugin-name>@cypherpoet-toolchest`.

## Skills

| Skill | Description |
|---|---|
| [<skill-name>](skills/<skill-name>/SKILL.md) | <one-sentence summary>. |
````

Every plugin here is currently skills-only, so that template is the whole README. A plugin that ships other component types adds a section per type, same two-column shape:

| Section | First column |
|---|---|
| `## Commands` | `[/<plugin-name>:<command>](commands/<command>.md)` |
| `## Agents` | `[<agent-name>](agents/<agent-name>.md)` |
| `## Hooks` | `` `<EventName>` ``, under a line pointing at `[hooks/hooks.json](hooks/hooks.json)` |
| `## MCP Servers` | `` `<server-name>` `` |

Include only the types the plugin actually ships. Append a row whenever a component is added — the per-plugin README is its primary index, and PR review treats a missing row as a defect.

A plugin's `## Skills` table lists **every** skill it ships, including any vendored in from another plugin ([Vendoring](#vendoring)) — refresh it whenever the sync adds or removes one.

## Top-Level Catalog

Every plugin gets a row in [CATALOG.md](CATALOG.md). The `Components` column uses text form — `5 skills`, `1 skill`, `2 commands, 1 hook` — singular for one, plural otherwise, ordered skills → commands → agents → hooks → MCP servers, dropping zeros.

Don't hand-edit it: the [`catalog-refresh`](../plugins/cypherpoet-marketplace-kit/skills/catalog-refresh/SKILL.md) skill regenerates the whole table from the manifests, and `marketplace-sync-check` reports when a refresh is due.

## Publishing

Publishing is label-driven: run `marketplace-publish-check` when opening the PR and apply the `marketplace-publish` label if it reports a needed publish — merging a labelled PR publishes automatically. The `marketplace-publish` skill is the manual fallback and never self-triggers.

Either way, one publish maintains both catalog files on the marketplace repo — the Claude entry and, for dual-harness plugins, the Codex entry (see [Marketplaces](#marketplaces)). Scaffolding alone never publishes.

Content and catalog metadata ship on separate tracks, and neither does the other's job:

- **Content** (skills, commands, agents, scripts) reaches existing installs only when you bump the plugin's [`version`](#manifest); a *fresh* install always pulls `main`'s latest. Re-run `scripts/sync_plugins.py` after a bump so the generated `.codex-plugin` version matches.
- **Catalog metadata** — the catalogs store their own copy of each plugin's `name`, `description`, and `homepage` (Claude) and its classification + `category` (Codex), so editing any of those requires running `marketplace-publish` again to refresh the entry.

## Skill Conventions

For skills inside a plugin, use [`/skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) — it handles drafts, evals, description optimization, and the general skill structure conventions.

The repo-local **`skill-structure-check`** skill audits skill structure across the repo. Its [`SKILL.md`](../.claude/skills/skill-structure-check/SKILL.md) is the canonical rule contract and remediation guide; the bundled Python script implements that contract.

`*-workspace/` directories under any `skills/` folder are gitignored: they're transient eval-iteration scratch, not real skills.

### Primary Sources

Every skill the fact-check routine covers (see [Fact-Check Tiering](#fact-check-tiering)) ends its `SKILL.md` with a **`## Primary Sources`** section — the skill's declared set of canonical verification sources, one bullet per source:

```markdown
## Primary Sources

- [Three.js releases](https://github.com/mrdoob/three.js/releases) — release channel; authoritative for versions.
- [Three.js documentation](https://threejs.org/docs/) — official API reference; authoritative for API syntax.
```

Each bullet says what the source is authoritative for (releases/versions, specs, API syntax, …). **Vendor-primary only** — official docs, release channels, spec registries; no blogs, aggregators, or forums. How the [`skill-fact-check`](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/SKILL.md) routine consumes this section, and how it interplays with per-fact `**Source:**` markers and `## Change-Signal Sources` leads, is defined in that skill's verification procedure.

A skill with nothing citable yet keeps the section as a placeholder — `None declared yet — the fact-check routine falls back to vendor-primary sources per claim.` — so there's a slot to fill in later. This section complements `## See Also` (related skills, tutorials, community links); a canonical doc URL may legitimately appear in both.

### Fact-Check Tiering

When creating (or renaming/removing) a skill, classify its unit — `<plugin>/<skill>` — into a tier in [`docs/automated-routines/skill-fact-check-manifest.json`](automated-routines/skill-fact-check-manifest.json); the tier definitions live in the `skill-fact-check` skill's [Manifest reference](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/SKILL.md#manifest-reference).

Every unit is listed exactly once; an unlisted unit still safely defaults to monthly. `skill-structure-check` reports untiered, orphaned, or double-listed entries — and fact-checked units missing their [Primary Sources](#primary-sources) section — as non-failing advisories (the CI health suite runs the checker with `--strict`, where they do fail).

### Cross-Plugin Links

A plugin installs via a `git-subdir` sparse-clone that fetches **only** that plugin's own directory. So a relative link that climbs out into a sibling — `[threejs-mastery](../../../cypherpoet-threejs-kit/skills/threejs-mastery/SKILL.md)` — resolves when browsing this monorepo but is a **dead path in an installed copy**, because the sibling plugin isn't on disk.

**A link from one plugin's files to a different plugin's file must be an absolute GitHub URL** — `https://github.com/CypherPoet/custom-agent-skills/blob/main/plugins/<plugin>/…` — which resolves in both contexts and matches how See Also sections already link external docs. In-plugin links (`./references/…`, `../SKILL.md`, `../assets/…`) stay relative; they ship together in the sparse-clone.

The rule covers every file the sparse-clone carries. `check-skill-structure.py` enforces it on the per-plugin `README.md`, each `SKILL.md`, and each skill's `references/*.md` — a link resolving outside its own plugin is an ERROR in those. It does **not** walk plugin-level `references/`, `commands/`, or `agents/` files, so the rule holds there but nothing catches a violation; extend the checker if a plugin starts shipping them.
