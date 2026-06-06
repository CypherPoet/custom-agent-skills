# CLAUDE.md

## Project

Public collection of reusable AI agent skills, packaged as Claude Code plugins that can be distributed through [plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).

## Architecture

- `plugins/<plugin-name>/` — Each themed Claude Code plugin. Self-contained — a `git-subdir` sparse-clone fetches only this directory when a consumer installs the plugin. Plugin shape follows the [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference); this repo's deltas live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).
- `docs/CATALOG.md` — Top-level cross-reference index. One row per plugin, linking to its `README.md` and listing its components. Refresh rule lives in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) (new plugin → add row; component counts shift → bump the count; pure prose edits → no change).
- Maintainer skills (marketplace + catalog tooling) — provided by the **`cypherpoet-marketplace-kit`** plugin, enabled in `.claude/settings.json` (not repo-local; see [Maintainer Skills](#maintainer-skills)).

## Creating Plugins Or Skills

See [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) — it covers the canonical scaffold workflow (via `/plugin-dev:create-plugin`), the repo's manifest deltas, the validate step, the catalog update, and the skill conventions (including `/skill-creator` for drafts/evals/iteration).

**Updating a plugin:** bump its `version` in `plugin.json` whenever a content change should reach already-installed users — pushing to `main` alone won't (`version` is Claude Code's update cache key).

## Maintainer Skills

These come from the **`cypherpoet-marketplace-kit`** plugin (enabled in `.claude/settings.json`), not repo-local copies — this repo and the private sibling install the same published source. All run locally (no tokens, no CI):

- **`marketplace-publish`** — publish one plugin to `cypherpoet-toolchest` by opening a PR. Manual-only (`disable-model-invocation`); it has an outward-facing side effect, so Claude shouldn't auto-run it.
- **`marketplace-sync-check`** — read-only audit of local plugins against both the published marketplace catalog (`marketplace.json`) and the local [`docs/CATALOG.md`](docs/CATALOG.md).
- **`catalog-refresh`** — regenerate `docs/CATALOG.md`'s plugin table from the manifests; the write-capable counterpart to `marketplace-sync-check`. Manual-only (`disable-model-invocation`); run it after a plugin's `name`/`description`/component counts change. Local-catalog only — never the marketplace.
- **`dependency-tag-check`** — read-only audit of git-tag coverage for version-constrained plugin dependencies. Manual-only (`disable-model-invocation`); run it after pinning/bumping a constrained dependency.
- **`marketplace-publish-check`** — read-only check of whether the current branch's diff needs a `marketplace-publish` (plugin added/removed, or `name`/`description`/`homepage` edited). **Model-invokable** — unlike the manual-only skills above, it's read-only and meant to auto-run at PR-creation to drive the `marketplace-publish` label.

## Marketplace Label

A PR touches the **marketplace catalog surface** when it adds/removes a `plugins/<name>/` directory or edits `name`/`description`/`homepage` in a `plugins/*/.claude-plugin/plugin.json` — a version-only bump does **not** count (that's content, gated by the version key). When opening such a PR, run `marketplace-publish-check` and apply the `marketplace-publish` label if it reports a needed publish, so the post-merge `marketplace-publish` isn't missed. (The `docs/CATALOG.md` refresh is a separate surface — see `catalog-refresh`.)
