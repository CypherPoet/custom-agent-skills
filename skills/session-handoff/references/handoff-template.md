# Handoff Template

This file is the canonical layout for handoff documents. `scripts/create_handoff.py` reads everything below the `# 🤝 Handoff:` line as the template body and substitutes the `{{placeholder}}` tokens at scaffold time. Edit the body to change the structure that gets emitted — there is no separate copy of this template inside the script.

## Why this structure

The document is ordered for the **resuming agent**, not the author. The agent's reading priority is: (1) what to do right now, (2) what constrains how, (3) what already shipped. So the top of the document is `Next Action` → metadata → state summary → important context → pending work → constraints. "What was completed" lives near the bottom because it's reference data once a session is over, not first-read material.

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

{{chain_section}}{{plan_section}}## 📍 Current State Summary

[TODO: One paragraph: what was being worked on, current status, and where things left off]

## 💡 Important Context

[TODO: The single most important section. Critical information the next agent MUST know to continue effectively — non-obvious constraints, decisions still under negotiation, things that would change the next action if missed.]

**Assumptions made this session** (optional — include only if any are load-bearing):
- [TODO: e.g. "Assuming the partial schedule data drops before next session"]

## 🚧 Pending Work

### Immediate Next Steps

1. [TODO: Most critical next action — should expand on the 🎯 Next Action line at the top]
2. [TODO: Second priority]
3. [TODO: Third priority]

### Blockers / Open Questions

- [ ] [TODO: List any blockers or open questions, or delete this section if none]

### Deferred Items

- [TODO: Items deferred and why. If more than 3, number them in priority order.]

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- [TODO: Things that might trip up a new agent — edge cases, quirks, non-obvious behavior, "do NOT do X" rules]

### 🧰 Skills to Use

| Skill | When to invoke | Why |
|-------|---------------|-----|
| [TODO: skill-name or plugin:skill-name] | [TODO: trigger condition for the resuming agent] | [TODO: why this skill fits this work] |

> Forward-looking only — list skills the resuming agent should consult, not a log of what was used.

## 🧠 Codebase Understanding

### Architecture Overview

[TODO: Key architectural insights discovered during this session. If unchanged from the previous handoff, say so and link rather than duplicating.]

### Critical Files

| File | Purpose | Relevance |
|------|---------|-----------|
| [TODO: path/to/file] | [What this file does] | [Why it matters for the next step — including "don't reintroduce X" warnings] |

### Key Patterns Discovered

[TODO: Important patterns, conventions, or idioms found in this codebase that the next agent should follow]

## 🏁 Work Completed

### Tasks Finished

- [x] [TODO: List completed tasks]

### Files Modified

{{modified_files_section}}

### Decisions Made

- **[TODO: Decision in one line]** — [TODO: Why this option won. Mention alternatives only if they're load-bearing for the rationale.]

## 🌐 Environment State

### Tools/Services Used

- [TODO: List relevant tools and their configuration]

### Active Processes

- [TODO: Note any running processes, servers, etc., or delete this section if none]

### Environment Variables

- [TODO: List relevant env var NAMES only — never include actual values/secrets]

## 📚 Related Resources

- [TODO: Add links to relevant docs and files]

---

**Security Reminder**: Before finalizing, run `validate_handoff.py` to check for accidental secret exposure.
