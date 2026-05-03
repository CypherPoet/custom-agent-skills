---
name: session-handoff
description: "Write a structured handoff document so a fresh agent can pick up long-running work without losing context. Use when the user says 'create handoff', 'save state', 'I need to pause', 'context is getting full', or when resuming with 'load handoff', 'resume from', 'continue where we left off'."
---

# Handoff

Creates structured handoff documents so a fresh AI agent can continue long-running work with the original context, decisions, and next steps intact.

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
- Pre-fill: timestamp, project path, git branch, recent commits, modified files
- Add handoff chain links if continuing from previous
- Output file path for editing

### Step 2: Complete the Handoff Document

Open the generated file and fill in all `[TODO: ...]` sections. Prioritize these sections:

1. **Current State Summary** - What's happening right now
2. **Important Context** - Critical info the next agent MUST know
3. **Immediate Next Steps** - Clear, actionable first steps
4. **Decisions Made** - Choices with rationale (not just outcomes)

Use the template structure in [references/handoff-template.md](references/handoff-template.md) for guidance.

### Step 3: Validate the Handoff

Run the validation script and read its report:

```bash
python scripts/validate_handoff.py <handoff-file>
```

Detected secrets block the handoff — fix them before continuing. A score below 70 means required sections are still incomplete; close the gaps and re-run.

### Step 4: Confirm Handoff

Report to user:
- Handoff file location
- Validation score and any warnings
- Summary of captured context
- First action item for next session

## RESUME Workflow

### Step 1: Find Available Handoffs

List handoffs in the current project:

```bash
python scripts/list_handoffs.py
```

This shows all handoffs with dates, titles, and completion status.

### Step 2: Check Staleness

Before loading, run the staleness check and read its verdict:

```bash
python scripts/check_staleness.py <handoff-file>
```

The script reports a level (FRESH / SLIGHTLY_STALE / STALE / VERY_STALE) and flags specific drift — commits, branch mismatch, missing files. Treat STALE/VERY_STALE as a signal to verify context carefully or start a fresh handoff.

### Step 3: Load the Handoff

Read the relevant handoff document completely before taking any action.

If handoff is part of a chain (has "Continues from" link), also read the linked previous handoff for full context.

### Step 4: Verify Context

Follow the checklist in [references/resume-checklist.md](references/resume-checklist.md):

1. Verify project directory and git branch match
2. Check if blockers have been resolved
3. Validate assumptions still hold
4. Review modified files for conflicts
5. Check environment state

### Step 5: Begin Work

Start with "Immediate Next Steps" item #1 from the handoff document.

Reference these sections as you work:
- "Critical Files" for important locations
- "Key Patterns Discovered" for conventions to follow
- "Potential Gotchas" to avoid known issues

### Step 6: Update or Chain Handoffs

As you work:
- Mark completed items in "Pending Work"
- Add new discoveries to relevant sections
- For long sessions: create a new handoff with `--continues-from` to chain them

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
- Links to its predecessor
- Can mark older handoffs as superseded
- Provides context breadcrumbs for new agents

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
| `validate_handoff.py <file>` | Check completeness, quality, and security |
| `check_staleness.py <file>` | Assess if handoff context is still current |

### references/

- [handoff-template.md](references/handoff-template.md) - Complete template structure with guidance
- [resume-checklist.md](references/resume-checklist.md) - Verification checklist for resuming agents
