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

## Manifest

Use [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) to scaffold a working `plugin.json`. Recommended defaults this repo applies on top:

- Set `"author": { "name": "CypherPoet" }` (no email field).
- Set `"version": "0.1.0"` for new plugins. Bump per semver as the plugin evolves: PATCH for fixes, MINOR for additive changes, MAJOR for breaking changes (pre-1.0, treat MINOR as the default bump for anything user-visible). This is Claude Code's update cache key — resolved from `plugin.json` first, with the `git-subdir` commit SHA only as the fallback when no version is set — so existing installs update *only* when you bump it; pushing new commits to `main` alone won't reach them.
- Add `"license": "MIT"`.
- Add `"keywords"`: 4–6 lowercase kebab-case tags, leading with `"claude-code"` and the plugin's domain (`git`, `blender`, `svg`, …).

See any existing manifest under `plugins/*/.claude-plugin/plugin.json` for canonical shape and the standard fields (`$schema`, `homepage`, `repository`) worth including for catalog and IDE support.

## Dependencies

A plugin can require another via the manifest `dependencies` array; Claude Code auto-installs them. **Default to the bare-string form:**

```jsonc
"dependencies": ["cypherpoet-webgl-kit"]
```

Every plugin here lives in one repo, and a consumer always installs from `main` — so a bare-string dependency hands them the *current, coherent set*: the dependent and its dependency at the versions that ship together. No tags, nothing to maintain. Each plugin still carries its own `version`, and bumping it ships updates exactly as described under [Manifest](#manifest); bare-string only means you don't *constrain* which version of the dependency is pulled.

**Only pin a version range — `{ "name": "...", "version": "~0.1.0" }` — when the dependency lives in a *different repo* or releases on a cadence you can't bump in the same commit**, so "latest" is no longer guaranteed to be the version you built against. That's the only case the constraint earns its cost. A version constraint on a `git-subdir` dependency resolves against **git tags** on the source repo (the one the `git-subdir` source fetches from, *not* the marketplace repo); with no satisfying tag the install hard-fails with `no-matching-tag` — there is no soft "check only" mode for git sources. So if you pin, you must tag every release of the depended-on plugin. Once its version is on `main`, run from its directory:

```shell
claude plugin tag --push   # creates <plugin-name>--v<version> on the source repo, then pushes it
```

Re-tag on every bump — an untagged bump is invisible to the range, which silently keeps resolving to the older tag. Mind the pre-1.0 interaction with the "MINOR is the default bump" rule above: a `~0.1.0` range only matches `0.1.x`, so a MINOR bump of the depended-on plugin (to `0.2.0`) won't be picked up until the dependent ships a widened constraint. See [Constrain plugin dependency versions](https://code.claude.com/docs/en/plugin-dependencies) for the full mechanics.

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

## Dependencies

Installed automatically with this plugin:

| Plugin | Version | Description |
|---|---|---|
| [<dep-name>](../<dep-name>) | `latest` | <one-sentence description, from the dependency's manifest>. |

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

The optional `## Dependencies` section (right after Installation) lists the plugins this one pulls in. Include it only when the manifest declares `dependencies`, mirror that array — `plugin.json` is the source of truth — and refresh the table when the array changes. The `Version` column shows `latest` for a bare-string dependency or the semver range for a pinned one; see [Dependencies](#dependencies) for when each applies.

When copying the install command, replace **all** placeholders: `<plugin-name>` with the plugin's slug, `<marketplace-owner>/<marketplace-repo>` with the GitHub path of the marketplace repo, and `<marketplace-name>` with the marketplace's `name` field from its `marketplace.json` (often the same as the repo name). For plugins published to this repo's marketplace (the default for everything currently in `plugins/`), those resolve to a fixed pair: `CypherPoet/cypherpoet-toolchest` and `cypherpoet-toolchest`. The shipped READMEs already use those values verbatim — the placeholder form only matters when scaffolding for a *different* marketplace.

## Top-Level Catalog

After creating a new plugin, add a row to [CATALOG.md](CATALOG.md). The `Components` column uses text form: `5 skills`, `1 skill`, `2 commands, 1 hook` — singular for one, plural otherwise. List components in the order skills → commands → agents → hooks → MCP servers, dropping zeros.

Refresh the catalog row whenever a plugin's component counts change (adding a skill bumps `5 skills` → `6 skills`) or a new plugin lands. In-place edits that don't shift the counts (typo fixes, prose tweaks, internal refactors) need no catalog change.

Rather than hand-editing, regenerate the whole table from the manifests by invoking the [`catalog-refresh`](../plugins/cypherpoet-marketplace-kit/skills/catalog-refresh/SKILL.md) skill (from the `cypherpoet-marketplace-kit` plugin); `marketplace-sync-check` reports when a refresh is due.

## Publishing

After the plugin is ready, use the `marketplace-publish` skill to open a PR on the marketplace this repo publishes to. Scaffolding alone never publishes — the catalog only changes when you explicitly publish.

A plugin's `version` (in `plugin.json`) is Claude Code's update cache key, so edits to a plugin's **content** (skills, commands, agents, scripts) reach existing installs only when you **bump that version** — pushing commits to `main` alone won't update them (a *fresh* install always pulls `main`'s latest). Separately, the catalog stores its own copy of each plugin's `name`, `description`, and `homepage` — editing any of those manifest fields requires running `marketplace-publish` again to refresh the entry. Content ships on a version bump; catalog metadata ships on a re-publish.

## Skill Conventions

For skills inside a plugin, use [`/skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) — it handles drafts, evals, description optimization, and the general skill structure conventions.

The repo-local **`skill-structure-check`** skill ([`.claude/skills/skill-structure-check`](../.claude/skills/skill-structure-check/SKILL.md)) audits skill structure across the repo — `SKILL.md` stays under ~500 lines (split topical or once-needed depth into `references/` files past that, routed from a table in the SKILL.md that serves as the skill-level table of contents), large `references/` files (>~300 lines) carry their own `**Contents:**` jump-line, any `**Contents:**` anchors resolve, and every cross-plugin link is an absolute URL rather than a dead relative path ([Cross-Plugin Links](#cross-plugin-links)). Short reference files don't need a jump-line. Run it (or ask Claude to) before opening a PR that touches skills; it's report-only and its bundled `scripts/check-skill-structure.py` is the source of truth for the rules.

### Primary Sources

Every skill the fact-check routine covers (see [Fact-Check Tiering](#fact-check-tiering)) ends its `SKILL.md` with a **`## Primary Sources`** section — the skill's declared set of canonical verification sources, one bullet per source:

```markdown
## Primary Sources

- [Three.js releases](https://github.com/mrdoob/three.js/releases) — release channel; authoritative for versions.
- [Three.js documentation](https://threejs.org/docs/) — official API reference; authoritative for API syntax.
```

Each bullet says what the source is authoritative for (releases/versions, specs, API syntax, …). **Vendor-primary only** — official docs, release channels, spec registries; no blogs, aggregators, or forums (mirroring the `skill-fact-check` rule). The [`skill-fact-check`](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/SKILL.md) routine reads this section as the skill's declared source set when verifying its claims; a per-fact inline `**Source:**` / `**Source of truth:**` marker (used next to specific tables/values, mostly in `references/`) still takes precedence for that fact. A skill with nothing citable yet keeps the section as a placeholder — `None declared yet — the fact-check routine falls back to vendor-primary sources per claim.` — so there's a slot to fill in later. This section complements `## See Also` (related skills, tutorials, community links); a canonical doc URL may legitimately appear in both.

### Fact-Check Tiering

When creating (or renaming/removing) a skill, classify its unit — `<plugin>/<skill>` — in [`docs/automated-routines/skill-fact-check-manifest.json`](automated-routines/skill-fact-check-manifest.json): **weekly** for fast-drifting external facts, **monthly** (the default) for everything else, **never** for evergreen methodology with no external facts. Every unit is listed explicitly; an unlisted unit still safely defaults to monthly, and `skill-structure-check` reports untiered or orphaned entries as a non-failing advisory. Tier definitions live in the `skill-fact-check` skill's [Manifest reference](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/SKILL.md#manifest-reference).

### Cross-Plugin Links

A skill's `SKILL.md` and `references/*.md` ship via a `git-subdir` sparse-clone that fetches **only** that plugin's own directory. A relative link that climbs out of the plugin into a sibling — `[threejs-mastery](../../../cypherpoet-threejs-kit/skills/threejs-mastery/SKILL.md)` — resolves when browsing this monorepo but is a **dead path in an installed copy**, because the sibling plugin isn't on disk. So **a link from one plugin's skill to a different plugin's file must be an absolute GitHub URL** — `https://github.com/CypherPoet/custom-agent-skills/blob/main/plugins/<plugin>/skills/<skill>/…` — which resolves in both contexts and matches how these See Also sections already link external docs. In-plugin links (`./references/…`, `../SKILL.md`, `../assets/…`) stay relative — they ship together in the sparse-clone. `check-skill-structure.py` enforces this: any skill-file link that resolves outside its own plugin is an ERROR.

This covers skill markdown, not the per-plugin `README.md` — its [Dependencies table](#per-plugin-readme) deliberately uses `../<dep-name>` relative links aimed at GitHub-repo browsing.

`*-workspace/` directories under any `skills/` folder are gitignored: they're transient eval-iteration scratch, not real skills.
