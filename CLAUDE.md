# CLAUDE.md

## Project

Public collection of reusable AI agent skills — self-contained instruction sets copied into agent environments (Claude, Gemini, etc.). The private sibling lives at `private-custom-agent-skills`.

## Architecture

- `skills/<skill-name>/SKILL.md` — Each skill is a folder with a required `SKILL.md` containing YAML frontmatter (`name`, `description`) and markdown instructions.
- The `description:` field is the trigger blurb Claude reads to decide when to invoke the skill — write it for matching, not for humans.
- Skills may optionally include `assets/`, `references/`, `scripts/`, and `evals/` (used by `/skill-creator` for iteration) subdirectories.
- `docs/CATALOG.md` — Index of all skills with descriptions.

## Creating and Improving Skills

Use `/skill-creator` when creating, editing, or iterating on skills.

## Conventions

- Skill folder names use **kebab-case**.
- New skills go in `skills/` (not globally), unless specified otherwise.
- `skills/*-workspace/` are gitignored scratch directories created by `/skill-creator` during eval iteration — not real skills.

## Workflow

- When adding a new skill, update `docs/CATALOG.md` with its entry. Keep rows sorted alphabetically by skill name.
