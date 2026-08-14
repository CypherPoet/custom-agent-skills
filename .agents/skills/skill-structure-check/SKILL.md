---
name: skill-structure-check
description: Audit this repo's plugin skills and vendored copies for structural drift. Checks skill size, Contents jump-lines, installed-copy-safe links, and vendored copies. Use after creating, editing, vendoring, or restructuring a skill, before opening a PR that touches skills, or whenever the user says "audit the skills", "check skill structure", "is this skill too big", "lint the skills", or "did I break a Contents link". Runs a deterministic local script and reports — it never edits files.
---

# Skill Structure Check

Keep this file as the canonical rule contract and remediation guide. The shared
repository tooling implements these rules instead of restating them in a second
skill-specific script.

## Run It

```shell
npm run structure:check
```

This command is report-only and uses strict mode: ERRORs, WARNINGs, and
ADVISORYs all fail. Run it before opening a PR that adds or edits a skill.

## What It Checks

| Severity | Rule | Why |
|---|---|---|
| ERROR | `SKILL.md` over 500 lines | The always-loaded body must stay a lean router; move topical or once-needed depth to `references/`. |
| ERROR | a `**Contents:**` link whose anchor does not resolve | The jump-line drifted from the headings it indexes. |
| ERROR | a relative link that escapes its plugin — in **any** `.md` under that plugin, at any depth | A sparse-clone install contains only one plugin, so cross-plugin links must be absolute GitHub URLs. The check walks the whole plugin rather than listing known locations, so it can't drift from the rule. |
| ERROR | vendoring drift | Generated copies must match `vendored-skills.json`, including detection of undeclared byte-identical copies. |
| WARN | `SKILL.md` 450–500 lines | The router is approaching the hard limit; plan the split. |
| ADVISORY | a reference file over 300 lines with no `**Contents:**` jump-line | Large references need the jump-line to stay navigable without loading the whole file. Short references do not. |

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

- **Oversized `SKILL.md`** — extract topical sections into `references/<topic>.md` and leave a routing table in the body. `threejs-kit` and `mobile-dev` are worked examples; follow `skill-creator`'s progressive-disclosure guidance.
- **Missing or stale Contents index** — add or repair the jump-line per [The Contents Index Format](#the-contents-index-format).
- **Escaping relative link** — use an absolute GitHub URL for another plugin; keep links within the current plugin relative.
- **Vendoring drift** — edit the authoritative source or `vendored-skills.json`, then run `npm run sync`. Never hand-edit a vendored target. A retired copy is removed automatically when git shows it clean; otherwise the sync refuses and tells you why.

Thresholds are implementation constants in `tooling/src/skill-structure.ts`. Change the rule here first, then update the implementation and tests in the same change.
