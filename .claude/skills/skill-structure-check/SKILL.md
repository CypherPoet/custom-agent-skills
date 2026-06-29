---
name: skill-structure-check
description: >
  Audit this repo's plugin skills for structural drift. Flags any SKILL.md that
  has grown past ~500 lines (split its depth into references/ files), any stale
  table-of-contents anchor, and — as a non-failing advisory — any large references/
  file (>~300 lines) missing its **Contents:** jump-line. Use after creating,
  editing, or restructuring a skill, before opening a PR that touches skills, or
  whenever the user says "audit the skills", "check skill structure", "is this
  skill too big", "lint the skills", or "did I break a Contents link". Runs a
  deterministic local script and reports — it never edits files.
---

# Skill Structure Check

Keeps this repo's skills structurally consistent as they grow. The convention:

- **`SKILL.md` is a lean router** (<500 lines). When a skill has depth, it splits into `references/` files and routes to them from a table in the SKILL.md — that table is the skill-level table of contents.
- **Large reference files (>~300 lines) carry their own `**Contents:**` jump-line** so the model can navigate them without loading the whole file. Short reference files don't need one.

The deterministic logic lives in [scripts/check-skill-structure.py](scripts/check-skill-structure.py); this skill is *when/why* to run it and *how to act* on what it reports.

## Run It

```shell
python3 .claude/skills/skill-structure-check/scripts/check-skill-structure.py
```

Report-only — it never modifies files. Exits `1` if there are any ERRORs, `0`
otherwise (WARNINGs and ADVISORYs don't fail). Run it before opening a PR that
adds or edits a skill. It finds the repo root on its own, so the working
directory doesn't matter.

## What It Checks

| Severity | Rule | Why |
|---|---|---|
| ERROR | `SKILL.md` over 500 lines | The always-loaded body should stay a router; move depth to `references/`. |
| ERROR | a `**Contents:**` anchor that doesn't resolve | The TOC drifted from the headings — fix the link or the heading. |
| WARN | `SKILL.md` 450–500 lines | Approaching the limit; plan the split now. |
| ADVISORY | `references/*.md` over ~300 lines with no `**Contents:**` line | Large reference files benefit from a jump-line; short ones don't need one. Summarized per skill, non-failing. |

The skill-level routing table in `SKILL.md` is a soft convention — not machine-checked here.

## Acting on Findings

- **SKILL.md too large** → extract topical sections into `references/<topic>.md` and leave a routing table in the body. `cypherpoet-threejs-kit` / `cypherpoet-mobile-dev` are worked examples; follow `/skill-creator`'s progressive-disclosure guidance.
- **Stale anchor** → a heading was renamed or removed; update the Contents link. Anchors are GitHub-style: lowercase, punctuation dropped, spaces → hyphens.
- **Large file missing `**Contents:**` (advisory)** → add a one-line `**Contents:** [Section](#anchor) · …` after the intro, linking the file's `##` headings.

Thresholds live at the top of the script — adjust them there if the convention changes; the script is the source of truth.
