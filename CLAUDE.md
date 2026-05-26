# CLAUDE.md

## Project

Public collection of reusable AI agent skills, packaged as Claude Code plugins that can be distributed through [plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).

## Architecture

- `plugins/<plugin-name>/` — Each themed Claude Code plugin. Self-contained — a `git-subdir` sparse-clone fetches only this directory when a consumer installs the plugin.
  - `.claude-plugin/plugin.json` — Plugin manifest. Core fields: `$schema`, `name`, `description`, `author`. Recommended consumer-facing metadata (every plugin ships these): `homepage` and `repository` pointing at the plugin's directory on GitHub, `license: "MIT"`, and a `keywords` array (4–6 tags, always including `"claude-code"`). `version` is optional — when omitted, the commit SHA serves as the version so updates flow automatically (current convention across all plugins). Plugins that prefer explicit releases may set a semver string instead.
  - `skills/<skill-name>/SKILL.md` — Each skill is a folder with required YAML frontmatter (`name`, `description`) and markdown instructions.
  - The `description:` field is the trigger blurb Claude reads to decide when to invoke the skill — write it for matching, not for humans.
  - Skills may optionally include `assets/`, `references/`, `scripts/`, and `evals/` (used by `/skill-creator` for iteration) subdirectories.
  - `README.md` — Per-plugin overview: purpose, install instructions, and an index of the plugin's skills (and any other components it ships). Travels with the plugin during sparse-clone.
- `docs/CATALOG.md` — Top-level cross-reference index. Single table listing each plugin and linking into its own `README.md`.

## Creating and Improving Skills

Use `/skill-creator` when creating, editing, or iterating on skills. New skill folders go under the appropriate `plugins/<plugin-name>/skills/` directory.

## Conventions

- Plugin folder names: `cypherpoet-<theme>` (kebab-case). Use `-kit` suffix for single-topic plugins (e.g., `cypherpoet-blender-kit`).
- Skill folder names: kebab-case, matching the `name:` field in `SKILL.md`'s frontmatter.
- `skills/*-workspace/` (under any plugin) are gitignored scratch directories created by `/skill-creator` during eval iteration — not real skills.

## Workflow

- When adding a new skill, update the host plugin's `plugins/<plugin>/README.md`. The top-level `docs/CATALOG.md` only needs an update if a *new plugin* is added.
- When adding a new plugin, also add an entry to the top-level `docs/CATALOG.md`, then publish it with the `marketplace-publish` skill (it opens a PR on the marketplace). Nothing auto-syncs — the catalog changes only when you explicitly publish. Editing an *already-listed* plugin's content needs no republish (the catalog tracks `main` by commit SHA).

## Maintainer skills

Repo-local skills in `.claude/skills/` (maintainer tooling — not published plugins) for managing the marketplace, all on local `gh` creds (no tokens, no CI):

- **`plugin-scaffold`** — create a new plugin's files locally; no commit, no publish.
- **`marketplace-publish`** — publish one plugin to `cypherpoet-toolchest` by opening a PR.
- **`marketplace-sync-check`** — read-only audit of which local plugins are / aren't in the catalog.
