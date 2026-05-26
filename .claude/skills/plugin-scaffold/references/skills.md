# Skill stubs (`skills/<name>/SKILL.md`)

A skill lives at `plugins/<plugin>/skills/<skill-name>/SKILL.md`. The folder name, the YAML `name:` field, and the slug Claude sees must all match — kebab-case throughout.

For anything beyond a stub, use [`/skill-creator`](https://github.com/anthropics/skills/tree/main/skill-creator) — it handles drafts, evals, and description optimization properly. This reference is just for the initial scaffold.

## Frontmatter shape

Two valid styles for the `description` field. Pick based on length.

**Short** — a single line works when the description fits in ~250 characters:

```yaml
---
name: <skill-name>
description: Use this skill whenever <trigger phrasing>. <One-sentence summary of what it does>.
---
```

**Long** — use the YAML block scalar `>` for multi-line descriptions; folds newlines into spaces so the rendered description reads as a single paragraph but stays readable in the file:

```yaml
---
name: <skill-name>
description: >
  Use this skill whenever <trigger phrasing — list common
  phrasings the user might say, plus edge cases and related
  intents>. <One- or two-sentence summary of what the skill
  actually does>. <Optional note on what it does NOT do>.
---
```

## Triggers first, then workflow

The `description:` field is the *only* signal Claude uses to decide whether to invoke the skill. So lead with **when** to trigger, not what the skill does.

**Weak:**
```yaml
description: A skill for writing git commit messages with emoji.
```

**Strong:**
```yaml
description: >
  Use Gitmoji to make commits more expressive. Use this skill
  whenever the user wants to commit changes, write a commit
  message, uses /commit, or asks for help with git commits —
  even if they don't mention emoji.
```

The second one names the user-visible phrasings (`commit`, `/commit`, `write a commit message`) that should fire the skill. The first one only describes the skill's identity — Claude can't easily decide from it whether the current task is a fit.

## Skill body

After the frontmatter, the body holds the actual instructions Claude reads when the skill triggers. For a stub, an H1 title and a placeholder workflow line are enough:

```markdown
# <Skill Name>

<One-line statement of what this skill does and the rough shape of its workflow.>

## Workflow

1. <First step>
2. <Second step>
3. <…>
```

Iterate on the body content with `/skill-creator` — it runs evals, suggests improvements, and lets you measure triggering rate against a held-out test set.

## Optional skill subdirs

A skill folder *may* include these alongside `SKILL.md` — leave them out of the initial scaffold unless the user asks:

| Dir | Purpose |
|---|---|
| `assets/` | Templates, HTML, CSS, images — files the skill copies or substitutes placeholders in. |
| `references/` | Reference material loaded on demand (the same pattern this plugin-scaffold skill uses). |
| `scripts/` | Helper scripts the skill invokes (Python, bash, Node). |
| `evals/` | Test cases (`evals.json`) used by `/skill-creator`. **gitignored as `skills/*-workspace/`** during iteration. |
