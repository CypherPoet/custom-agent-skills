# Scope and inputs

What counts as a unit, what is deliberately excluded, and what each run reads. Look here when deciding whether a file is in scope or where a fact's authority comes from; [Step 1](../SKILL.md#step-1--compute-the-due-set) needs both.

## Scope & exclusions

A **unit** is one skill: its `SKILL.md`, the sibling `references/**`, and its `evals/**`. Its `unit_id` is `<plugin>/<skill>`, its directory is the `SKILL.md`'s parent, and its plugin manifest is `plugins/<plugin>/.claude-plugin/plugin.json`.

Fact-check all three surfaces:

- **`SKILL.md`** — the skill's own body.
- **`references/**`** — roughly 80% of volatile facts live here.
- **`evals/**`** — fixtures encode the same version-sensitive premises as the docs and go stale with them, leaving an eval that contradicts the skill it grades. Corrected under the same evidence gates as any other file, with the reading caveats in [`subagent-procedure.md`](subagent-procedure.md) so a fixture's scenario data isn't mistaken for a stale fact.

Three exclusions, each for its own reason:

- `**/*-workspace/` is regenerable scratch — never read, never edited, never counted.
- **Evals are not units.** A fixture `SKILL.md` under `evals/` is test data, not a skill to schedule.
- **Eval dates are not datelines.** A date inside a fixture is scenario data, not a record of when this unit was verified; counting one would falsely freshen the unit.

The bundled scripts enforce all three.

## Inputs

- **Manifest:** `docs/automated-routines/skill-fact-check-manifest.json` in the repo being checked — maps units to a volatility tier (`weekly`, `monthly`, `never`) and carries the `acknowledged` list. Shape, tiering guidance, and acknowledgment semantics: [`manifest.md`](manifest.md).
- **Datelines** (the freshness cursor) — when a unit's facts were last checked. [`../scripts/datelines.py`](../scripts/datelines.py) is the single source of truth for which forms count:
  - *labelled* — `**Verified:** <date>` (the canonical marker this routine writes), `Last synced: <date>`, the parenthetical audit-baseline date
  - *unlabelled* — inline `verified <date>`, `as of <month>`

  Both age-gate a unit; only labelled ones can auto-merge ([Step 6](../SKILL.md#step-6--datelines)). Bare content dates (`released …`, `Created: …`) count as neither — treating one as a dateline would mark a stale unit fresh forever.
- **Source markers:** `**Source:**` and `**Source of truth:**` — the URL a file declares as the authority for a specific fact. Check this first.
- **Declared source set:** a `## Primary Sources` section at the end of a unit's `SKILL.md` — the skill's own canonical verification sources, one bullet per source saying what it's authoritative for. Prefer these over free-choice research; a placeholder ("None declared yet …") means fall back to vendor-primary sources per claim.
- **Change-signal leads:** an optional per-unit `Change-Signal Sources` block listing secondary leads (e.g. a maintainer's blog) to scan for *what* may have drifted. Leads only — confirm against a primary source, never cite one in an edit.
