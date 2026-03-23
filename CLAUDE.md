# CLAUDE.md

## Project

Public collection of reusable AI agent skills — self-contained instruction sets copied into agent environments (Claude, Gemini, etc.). The private sibling lives at `private-custom-agent-skills`.

## Architecture

- `skills/<skill-name>/SKILL.md` — Each skill is a folder with a required `SKILL.md` containing YAML frontmatter (`name`, `description`) and markdown instructions.
- Skills may optionally include `assets/`, `references/`, and `scripts/` subdirectories.
- `docs/CATALOG.md` — Index of all skills with descriptions.

## Creating and Improving Skills

Use `/writing-skills` when creating or editing skills. For iterative improvement and description optimization, use `/skill-creator`.

## Conventions

- Skill folder names use **kebab-case**.
- No build system, tests, or linting — this is a pure documentation/prompt-engineering repo.
- New skills go in `skills/` (not globally), unless specified otherwise.

## Workflow

- When adding a new skill, update `docs/CATALOG.md` with its entry.
