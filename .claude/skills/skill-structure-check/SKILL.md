---
name: skill-structure-check
description: Audit this repo's plugin skills for structural drift. Checks skill size and relative Markdown links that would break in a standalone plugin installation. Use after creating, editing, or restructuring a skill, before opening a PR that touches skills, or whenever the user says "audit the skills", "check skill structure", "is this skill too big", or "lint the skills". Runs a deterministic local script and reports — it never edits files.
---

# Skill Structure Check

Keep this file as the canonical rule contract and remediation guide. The shared
repository tooling implements these rules instead of restating them in a second
skill-specific script.

## Run It

```shell
npm run structure:check
```

This command is report-only and uses strict mode: errors and warnings fail. Run
it before opening a PR that adds or edits a skill.

## What It Checks

| Severity | Rule | Why |
|---|---|---|
| ERROR | `SKILL.md` over 500 lines | The always-loaded body must stay a lean router; move topical or once-needed depth to `references/`. |
| ERROR | a relative link that escapes its plugin — in **any** `.md` under that plugin, at any depth | A standalone installation contains only that plugin, so links leaving it must use absolute GitHub URLs. The check walks the whole plugin rather than listing known locations, so it cannot drift from the rule. |
| WARN | `SKILL.md` 450–500 lines | The router is approaching the hard limit; plan the split. |

The skill-level routing table in `SKILL.md` is a soft convention — not machine-checked here.

## Acting on Findings

- **Oversized `SKILL.md`** — extract topical sections into `references/<topic>.md` and leave a routing table in the body. `threejs-kit` and `mobile-dev` are worked examples; follow `skill-creator`'s progressive-disclosure guidance.
- **Escaping relative link** — use an absolute GitHub URL for another plugin; keep links within the current plugin relative.

Thresholds are implementation constants in `tooling/src/skill-structure.ts`. Change the rule here first, then update the implementation and tests in the same change.
