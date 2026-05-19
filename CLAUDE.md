# CLAUDE.md

## Project

Public collection of reusable AI agent skills, packaged as Claude Code plugins distributed via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace. The private sibling lives at `private-custom-agent-skills`.

## Architecture

- `plugins/<plugin-name>/` — Each themed Claude Code plugin. Self-contained — a `git-subdir` sparse-clone fetches only this directory when a consumer installs the plugin.
  - `.claude-plugin/plugin.json` — Plugin manifest (name, description, author). No `version` field; commit SHA serves as the version so updates flow automatically.
  - `skills/<skill-name>/SKILL.md` — Each skill is a folder with required YAML frontmatter (`name`, `description`) and markdown instructions.
  - The `description:` field is the trigger blurb Claude reads to decide when to invoke the skill — write it for matching, not for humans.
  - Skills may optionally include `assets/`, `references/`, `scripts/`, and `evals/` (used by `/skill-creator` for iteration) subdirectories.
  - `CATALOG.md` — Per-plugin index of skills, with one-line descriptions and links to each `SKILL.md`. Travels with the plugin during sparse-clone.
- `docs/CATALOG.md` — Top-level cross-reference index. Single table listing each plugin and linking into its own `CATALOG.md`.

## Creating and Improving Skills

Use `/skill-creator` when creating, editing, or iterating on skills. New skill folders go under the appropriate `plugins/<plugin-name>/skills/` directory.

## Conventions

- Plugin folder names: `cypherpoet-<theme>` (kebab-case). Use `-kit` suffix for single-topic plugins (e.g., `cypherpoet-blender-kit`).
- Skill folder names: kebab-case, matching the `name:` field in `SKILL.md`'s frontmatter.
- `skills/*-workspace/` (under any plugin) are gitignored scratch directories created by `/skill-creator` during eval iteration — not real skills.

## Workflow

- When adding a new skill, update the host plugin's `plugins/<plugin>/CATALOG.md`. The top-level `docs/CATALOG.md` only needs an update if a *new plugin* is added.
- When adding a new plugin, also add an entry to the top-level `docs/CATALOG.md`. The marketplace's auto-sync workflow will pick up the new plugin within a 6-hour cron cycle, or immediately on push if dispatch is wired.
