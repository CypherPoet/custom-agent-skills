---
name: skill-structure-check
description: >
  Audit this repo's plugin skills and generated dual-harness artifacts for
  structural drift. Checks skill size, Contents jump-lines, installed-copy-safe
  links, fact-check classification and sources, vendored copies, Codex
  manifests, and plugin classification. Use after creating, editing,
  vendoring, or restructuring a skill, before opening a PR that touches skills,
  or whenever the user says "audit the skills", "check skill structure", "is
  this skill too big", "lint the skills", or "did I break a Contents link".
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
otherwise; with `--strict` (how the CI health suite runs it) WARNINGs and
ADVISORYs fail too. Run it before opening a PR that adds or edits a skill. It
finds the repo root on its own, so the working directory doesn't matter.

## What It Checks

| Severity | Rule | Why |
|---|---|---|
| ERROR | `SKILL.md` over 500 lines | The always-loaded body must stay a lean router; move topical or once-needed depth to `references/`. |
| ERROR | a `**Contents:**` link whose anchor does not resolve | The jump-line drifted from the headings it indexes. |
| ERROR | a relative skill-file link that escapes its plugin | A sparse-clone install contains only one plugin, so cross-plugin links must be absolute GitHub URLs. |
| ERROR | plugin-sync drift | Vendored copies, generated Codex manifests, and plugin classification must match `scripts/plugin-registry.json` — including an undeclared byte-identical copy of a declared source. |
| WARN | `SKILL.md` 450–500 lines | The router is approaching the hard limit; plan the split. |
| ADVISORY | a reference file over 300 lines with no `**Contents:**` jump-line | Large references need the jump-line to stay navigable without loading the whole file. Short references do not. |
| ADVISORY | fact-check manifest drift | Every real skill unit must appear exactly once in weekly/monthly/never; listed units must exist; every non-never unit must declare `## Primary Sources`. Skipped when the repo has no manifest. |

The skill-level routing table in `SKILL.md` is a soft convention — not machine-checked here.

## The Contents Index Format

There is exactly one index format, so authors and the checker never disagree:
a single line, placed after the file's introduction,

```markdown
**Contents:** [First Section](#first-section) · [Second Section](#second-section)
```

- One line, starting `**Contents:**`, with markdown links joined by ` · `.
- Every link targets an in-file heading anchor, GitHub-normalized: lowercase,
  punctuation removed, spaces changed to hyphens, duplicate headings suffixed
  `-1`, `-2`, and so on.
- Code fences are ignored on both sides: a fenced example jump-line is not the
  file's index, and a fenced `## heading` does not satisfy an anchor.
- An old-style `## Contents` section is not recognized as an index — convert it
  to a jump-line.

## Acting on Findings

- **Oversized `SKILL.md`** — extract topical sections into `references/<topic>.md` and leave a routing table in the body. `cypherpoet-threejs-kit` and `cypherpoet-mobile-dev` are worked examples; follow `skill-creator`'s progressive-disclosure guidance.
- **Missing or stale Contents index** — add or repair the jump-line per [The Contents Index Format](#the-contents-index-format).
- **Escaping relative link** — use an absolute GitHub URL for another plugin; keep links within the current plugin relative.
- **Plugin-sync drift** — edit the authoritative source or registry, then run `python3 scripts/sync_plugins.py`. Never hand-edit a vendored copy or a `.codex-plugin/plugin.json`. A retired copy is removed automatically when git shows it clean; otherwise the sync refuses and tells you why.
- **Fact-check drift** — place each `<plugin>/<skill>` unit in exactly one tier, remove or rename orphaned entries, and add `## Primary Sources` to every fact-checked unit. Tier definitions live in the `skill-fact-check` skill's Manifest reference.

Thresholds are implementation constants in the script. Change the rule here first, then update the implementation and tests in the same change.
