---
name: session-handoff
description: "Write a structured handoff document so a fresh agent can pick up long-running work without losing context. Use when the user says 'create handoff', 'save state', 'I need to pause', 'context is getting full', or when resuming with 'load handoff', 'resume from', 'continue where we left off'."
---

# Handoff

Creates structured handoff documents so a fresh AI agent can continue long-running work with the original context, decisions, and next steps intact.

The generated document is ordered for the **resuming agent**, not the author — the load-bearing instructions (🎯 Next Action, Important Context, Pending Work) sit near the top, and "what already shipped" is at the bottom because it's reference data once a session is over.

## Mode Selection

**Creating a handoff?** User wants to save current state or pause work — follow the CREATE workflow below.

**Resuming from a handoff?** User wants to continue previous work or mentions an existing handoff — follow the RESUME workflow below.

## CREATE Workflow

### Step 1: Generate Scaffold

Run the smart scaffold script to create a pre-filled handoff document:

```bash
python scripts/create_handoff.py [task-slug]
```

Example: `python scripts/create_handoff.py implementing-user-auth`

**For continuation handoffs** (linking to previous work):
```bash
python scripts/create_handoff.py "auth-part-2" --continues-from 2024-01-15-auth.md
```

The script will:
- Create `.claude/handoffs/` directory if needed
- Generate timestamped filename
- Pre-fill: timestamp, project path, git branch, repo URL, open-PR URL (when available), recent commits, modified files
- Add handoff chain links if continuing from previous
- Detect a Claude Code session plan at `~/.claude/plans/<slug>.md` and link to it if present
- Output file path for editing

### Step 1.5: Confirm Session Plan Reference

If `create_handoff.py` reports an `Active Session Plan` was detected, ask the user once:

> "I found a session plan at `<path>`. Should the handoff link to it as essential context for the resuming agent?"

- **Yes** → leave the `📋 Active Session Plan` section in place and fill in the `Status` TODO.
- **No** → remove the entire `📋 Active Session Plan` section before continuing.

This is a quick confirmation, not a discussion — the section is link-only and lightweight, so the bar for keeping it is low. The plan typically captures authored intent that the resuming agent should not have to re-derive.

### Step 2: Complete the Handoff Document

Open the generated file and fill in all `[TODO: ...]` placeholders. Prioritize in this order:

1. **🎯 Next Action** (top of document) — Single sentence, the FIRST thing the resuming agent should do. This is the single most load-bearing field; a triaging agent may read only this line. Be concrete: include a file path, command, or specific step.
2. **Current State Summary** — What's happening right now, in one paragraph.
3. **Important Context** — Non-obvious constraints, decisions still under negotiation, things that would change the next action if missed.
4. **Immediate Next Steps** — Numbered, ordered. Expands on the 🎯 Next Action line.
5. **Constraints for Resuming Agent** (Potential Gotchas + Skills to Use) — "Do NOT do X" rules; skills the next agent should invoke.
6. **Decisions Made** — Rationale-first. Don't dwell on alternatives unless they're load-bearing for the reasoning.

The template structure (with explanations) lives at [references/handoff-template.md](references/handoff-template.md).

### Step 3: Validate the Handoff

Run the validation script:

```bash
python scripts/validate_handoff.py <handoff-file>
```

The verdict is one of:

- **READY** — Handoff is complete; safe to share.
- **NEEDS_WORK** — Required section missing/unfilled, Next Action still a TODO, or other `[TODO: ...]` placeholders remain. Fix and re-run.
- **BLOCKED** — Potential secret detected. Remove the secret before continuing; the handoff must not ship as-is.

The report also surfaces missing recommended sections (advisory) and referenced files that don't exist on disk (advisory) — these don't block readiness but worth scanning.

### Step 4: Confirm Handoff

Report to user:
- Handoff file location
- Validation verdict and any warnings
- Summary of captured context
- The 🎯 Next Action line as the first thing the next session will do

## RESUME Workflow

### Step 1: Find Available Handoffs

```bash
python scripts/list_handoffs.py
```

Shows all handoffs with dates, titles, and completion status.

### Step 2: Check Staleness

```bash
python scripts/check_staleness.py <handoff-file>
```

The script reports a level (FRESH / SLIGHTLY_STALE / STALE / VERY_STALE) and flags specific drift — commits, branch mismatch, missing files. Treat STALE/VERY_STALE as a signal to verify context carefully or start a fresh handoff.

### Step 3: Load the Handoff

Read the handoff document, but you do not need to read it cover to cover. The document is structured so the resuming agent can triage quickly.

If the handoff is part of a chain (has a "Continues from" link), also read the linked predecessor for full context — but only after the current handoff's high-priority sections.

### Step 3.5: Read Strategy

Read this way to keep triage cost low without losing context:

- **Read in full**: 🎯 Next Action, Session Metadata, Current State Summary, Important Context, Pending Work, Constraints for Resuming Agent.
- **Skim**: Codebase Understanding, Work Completed. These exist for spot-lookups, not linear reading.
- **Consult on demand**: Environment State, Related Resources.

The 🎯 Next Action line at the top is the load-bearing instruction — everything else fills in the why and the how. Stop reading early once you have enough context to act.

### Step 4: Verify Context

Before executing the next action, sanity-check that the handoff's assumptions still hold:

1. You are in the correct project directory — the handoff lives at `<project>/.claude/handoffs/`, so check that the handoff's path matches your current working directory.
2. Git branch matches the handoff's `Branch:` (or you understand the deliberate divergence).
3. Listed blockers haven't already been resolved.
4. Files referenced in Critical Files / Files Modified still exist.

**Quick verification commands:**

```bash
git branch --show-current
git status
git log --oneline -10              # compare against the handoff's recent commits
```

**Red flags — stop and reassess before continuing if any apply:**

1. **Files mentioned in the handoff don't exist** — codebase may have changed significantly since the handoff. Investigate before acting.
2. **Branch has diverged substantially** from the handoff's recorded branch — check `git log` for unrelated work.
3. **Assumptions are clearly invalid** — re-evaluate the next action with the user before proceeding.
4. **Blockers marked as unresolved are still blocking** — surface to the user; don't try to engineer around them silently.
5. **Architecture has changed** since the handoff was written — re-explore before continuing implementation.

### Step 5: Begin Work

Execute the 🎯 Next Action at the top of the handoff. The numbered list under **Immediate Next Steps** expands on it.

Reference these sections as you work:
- **Critical Files** for important locations and "don't reintroduce X" warnings.
- **Key Patterns Discovered** for conventions the previous session established.
- **Potential Gotchas** for known landmines.
- **Skills to Use** for the right tool/skill to invoke at each step.

### Step 6: Update or Chain Handoffs

As you work:
- Mark completed items in **Pending Work** as you finish them.
- Add new discoveries to relevant sections (especially **Important Context** and **Potential Gotchas**).
- For long sessions, create a new handoff with `--continues-from` to chain them.

## Handoff Chaining

For long-running projects, chain handoffs together to maintain context lineage:

```
handoff-1.md (initial work)
    ↓
handoff-2.md --continues-from handoff-1.md
    ↓
handoff-3.md --continues-from handoff-2.md
```

Each handoff in the chain:
- Links to its predecessor.
- Can mark older handoffs as superseded.
- Documents only the current session's deltas — relies on the predecessor for stable context (architecture, long-running decisions).

When resuming from a chain, read the most recent handoff first, then reference predecessors as needed.

## Storage Location

Handoffs are stored in: `.claude/handoffs/`

Naming convention: `YYYY-MM-DD-HHMMSS-[slug].md`

Example: `2024-01-15-143022-implementing-auth.md`

## Resources

### scripts/

| Script | Purpose |
|--------|---------|
| `create_handoff.py [slug] [--continues-from <file>]` | Generate new handoff with smart scaffolding |
| `list_handoffs.py [path]` | List available handoffs in a project |
| `validate_handoff.py <file>` | Check completeness and security; emits a structured pass/fail/warn report and a READY/NEEDS_WORK/BLOCKED verdict |
| `check_staleness.py <file>` | Assess if handoff context is still current |

### references/

- [handoff-template.md](references/handoff-template.md) — Canonical template structure with placeholder documentation. The `create_handoff.py` script renders from this file; it is the single source of truth.
