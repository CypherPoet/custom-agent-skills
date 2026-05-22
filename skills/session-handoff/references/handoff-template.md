# Handoff Template

This file is the canonical layout for handoff documents. `scripts/create_handoff.py` reads everything below the `# 🤝 Handoff:` line as the template body and substitutes the `{{placeholder}}` tokens at scaffold time. Edit the body to change the structure that gets emitted — there is no separate copy of this template inside the script.

## Why this structure

The document is ordered for the **resuming agent**, not the author. The agent's reading priority is: (1) what to do right now, (2) what canonical artifacts to open, (3) what constrains how, (4) what already shipped. So the top of the document is `Next Action` → metadata → source artifacts → state summary → important context → pending work → constraints. "What was completed" lives near the bottom because it's reference data once a session is over, not first-read material.

📚 Source Artifacts sits high so the resuming agent opens the PRD/plan/PR/ADRs *before* reading the handoff body — the rest of the document assumes those are available, and treats restating their content as redundant.

The Read Strategy section in `SKILL.md` tells the resuming agent which sections to read in full vs. skim vs. consult on demand. Keep that guidance in sync if you reorder anything here.

## Placeholders

| Placeholder | Source | Notes |
|---|---|---|
| `{{timestamp}}` | runtime UTC ISO-8601 | always populated |
| `{{branch_line}}` | `git branch --show-current` | falls back to a `[not a git repo or detached HEAD]` message |
| `{{repo_line}}` | `git remote get-url origin` | full `\n- Repo: <url>` line (with leading newline), or empty |
| `{{pr_line}}` | `gh pr view --json url --jq '.url'` | full `\n- Source PR: <url>` line, or empty |
| `{{commits_section}}` | `git log --oneline -5` | bulleted list, last 5 commits, or a `[no recent commits]` sentinel |
| `{{chain_section}}` | `--continues-from` | full `## 🔗 Handoff Chain` block + trailing blank line, or empty |
| `{{plan_section}}` | `~/.claude/plans/<slug>.md` lookup | full `## 📋 Active Session Plan` block + trailing blank line, or empty |
| `{{modified_files_section}}` | `git diff --name-only` (staged + unstaged) | bulleted list of files, or a single sentinel bullet |

Everything below the next `# 🤝 Handoff:` line is the template body.

---

# 🤝 Handoff: [TASK_TITLE - replace this]

> 🎯 **Next Action**: [TODO: One sentence — the FIRST thing the resuming agent should do. Be concrete: include a file path, a command, or a step.]

## 🧾 Session Metadata
- Created: {{timestamp}}
- Branch: {{branch_line}}{{repo_line}}{{pr_line}}

### Recent Commits (for context)
{{commits_section}}

{{chain_section}}{{plan_section}}## 📚 Source Artifacts

The canonical record for this work. Link by path or URL; do not restate their content elsewhere in this handoff. Write `none` for any line that genuinely has no artifact.

- **PRD / spec**: [TODO: path or URL, or "none"]
- **Session plan**: [TODO: path under `~/.claude/plans/`, or "none" — leave as-is if Active Session Plan above already links it]
- **ADRs / design docs**: [TODO: paths, or "none"]
- **Issues / tickets**: [TODO: Linear / Jira / GitHub issue links, or "none"]
- **Source PR**: (auto-linked in Session Metadata above if detected)
- **Other**: [TODO: anything else worth opening before resuming, or "none"]

## 📍 Current State Summary

[TODO: One paragraph: what was being worked on, current status, where things left off. Describe state, not intent — link to the PRD/plan/issue above for *what* and *why*.]

## 💡 Important Context

[TODO: Only what the linked artifacts in 📚 Source Artifacts don't already say — non-obvious constraints, decisions still under negotiation, load-bearing assumptions, things that would change the next action if missed. The single most important section.]

**Assumptions made this session** (optional — include only if any are load-bearing):
- [TODO: e.g. "Assuming the partial schedule data drops before next session"]

## 🚧 Pending Work

### Immediate Next Steps

1. [TODO: Most critical next action — should expand on the 🎯 Next Action line at the top]
2. [TODO: Second priority]
3. [TODO: Third priority]

### Blockers / Open Questions

- [ ] [TODO: List any blockers or open questions, or write "none"]

### Deferred Items

- [TODO: Work *adjacent* to this session's primary effort that you considered and parked — separate tickets, side cleanups, things the resuming agent should know exist but shouldn't tackle as their primary effort. Or "none".]

> If this handoff *exists to track* items deferred from a previous task — i.e., those items are the primary effort, not adjacent to it — write `none` here and put the canonical list in **Immediate Next Steps**.

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- [TODO: Edge cases, quirks, non-obvious behavior, "do NOT do X" rules that might trip up a new agent. Or write "none".]

### 🧰 Skills to Use

Skills the resuming agent should consult for the work ahead. Scan your loaded skill list (or `~/.claude/skills/`) and pick ones whose triggers match upcoming steps — not skills you used this session.

- `[TODO: skill-name or plugin:skill-name]` — **when:** [TODO: trigger condition for the resuming agent]. **why:** [TODO: why this skill fits this work]
- (add more bullets as needed, or write `none` if no skill is recommended)

> Forward-looking only. `none` is a valid answer — the resuming agent reads it as a signal, not an omission.

## 🧠 Codebase Understanding

### Architecture Overview

[TODO: Key architectural insights discovered during this session. If unchanged from the previous handoff or already covered in a linked design doc/ADR/PRD, say so and link rather than duplicating.]

### Critical Files

| File | Purpose | Relevance |
|------|---------|-----------|
| [TODO: path/to/file] | [What this file does] | [Why it matters for the next step — including "don't reintroduce X" warnings] |

### Key Patterns Discovered

[TODO: Important patterns, conventions, or idioms found in this codebase that the next agent should follow]

## 🏁 Work Completed

### Tasks Finished

- [x] [TODO: User-visible outcomes (e.g. "auth middleware lands behind feature flag"). Reference the commits/PR above for the diff — don't restate the commit log here.]

### Files Modified

{{modified_files_section}}

### Decisions Made

- **[TODO: Decision in one line]** — [TODO: Why this option won. If an ADR or PR comment in 📚 Source Artifacts already captures the rationale, link to it instead of restating. Inline only when there's no canonical record. Mention alternatives only if they're load-bearing for the reasoning.]

## 🌐 Environment State

### Tools/Services Used

- [TODO: List relevant tools and their configuration]

### Active Processes

- [TODO: Note any running processes, servers, etc., or delete this section if none]

### Environment Variables

- [TODO: List relevant env var NAMES only — never include actual values/secrets]

---

**Security Reminder**: Before finalizing, run `validate_handoff.py` to check for accidental secret exposure.
