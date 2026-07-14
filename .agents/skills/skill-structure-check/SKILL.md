---
name: skill-structure-check
description: >
  Audit this repo's plugin skills and generated dual-harness artifacts for
  structural drift. Checks skill size, Contents indexes, installed-copy-safe
  links, fact-check classification and sources, vendored copies, ownership
  markers, Codex manifests, and plugin classification. Use after creating,
  editing, vendoring, or restructuring a skill; before opening a PR that touches
  skills; or whenever the user asks to audit, lint, or verify skill structure.
  Runs a deterministic local script and reports — it never edits files.
---

# Skill Structure Check

Keep this file as the canonical rule contract and remediation guide. The bundled
[script](scripts/check-skill-structure.py) implements these rules and points back
here instead of restating them.

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
| ERROR | `SKILL.md` over 500 lines | The always-loaded body must stay a lean router; move topical or once-needed depth to `references/`. |
| ERROR | a Contents link whose anchor does not resolve | A `**Contents:**` jump-line or `## Contents` section drifted from the headings it indexes. |
| ERROR | a relative skill-file link that escapes its plugin | A sparse-clone install contains only one plugin, so cross-plugin links must be absolute GitHub URLs. |
| ERROR | dual-harness drift | Vendored copies, ownership markers, generated Codex manifests, and plugin classification must match `scripts/dual-harness.json`. |
| WARN | `SKILL.md` 450–500 lines | The router is approaching the hard limit; plan the split. |
| ADVISORY | a reference file over 300 lines with no navigable Contents index | Large references need either a one-line `**Contents:**` index or a populated `## Contents` section. Short references do not. |
| ADVISORY | fact-check manifest drift | Every real skill unit must appear exactly once in weekly/monthly/never; listed units must exist; every non-never unit must declare `## Primary Sources`. Skipped when the repo has no manifest. |

The skill-level routing table in `SKILL.md` is a soft convention — not machine-checked here.

## Acting on Findings

- **Oversized `SKILL.md`** — extract topical sections into `references/<topic>.md` and leave a routing table in the body. Follow `skill-creator`'s progressive-disclosure guidance.
- **Missing or stale Contents index** — add or repair a one-line `**Contents:** [Section](#anchor) · …` after the introduction, or retain an existing populated `## Contents` section. Anchors use GitHub-style normalization: lowercase, punctuation removed, spaces changed to hyphens, and duplicate headings suffixed `-1`, `-2`, and so on.
- **Escaping relative link** — use an absolute GitHub URL for another plugin; keep links within the current plugin relative.
- **Dual-harness drift** — edit the authoritative source or config, then run `python3 scripts/sync_dual_harness.py`. Never hand-edit a vendored copy, ownership marker, or `.codex-plugin/plugin.json`.
- **Fact-check drift** — place each `<plugin>/<skill>` unit in exactly one tier, remove or rename orphaned entries, and add `## Primary Sources` to every fact-checked unit. Tier definitions live in the `skill-fact-check` skill's Manifest reference.

Thresholds are implementation constants in the script. Change the rule here first, then update the implementation and tests in the same change.
