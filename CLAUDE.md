# CLAUDE.md

## Project

Public collection of reusable AI agent skills, packaged as Claude Code plugins that can be distributed through [plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).

## Architecture

- `plugins/<plugin-name>/` — Each themed Claude Code plugin. Self-contained — a `git-subdir` sparse-clone fetches only this directory when a consumer installs the plugin. Plugin shape follows the [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference); this repo's deltas live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).
- `docs/CATALOG.md` — Top-level cross-reference index. One row per plugin, linking to its `README.md` and listing its components. Updated only when adding a *new* plugin.
- `.claude/skills/` — Repo-local maintainer skills (see below).

## Creating Plugins or Skills

- **New plugin** — run [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md), then apply the deltas in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) and add a row to `docs/CATALOG.md`.
- **New or revised skill** — run [`/skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator). It handles drafts, evals, and description optimization.

## Maintainer Skills

Repo-local skills in `.claude/skills/` for managing the marketplace, all on local `gh` creds (no tokens, no CI):

- **`marketplace-publish`** — publish one plugin to `cypherpoet-toolchest` by opening a PR.
- **`marketplace-sync-check`** — read-only audit of which local plugins are / aren't in the catalog.
