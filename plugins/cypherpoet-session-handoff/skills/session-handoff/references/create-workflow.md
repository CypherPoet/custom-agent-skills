# CREATE Workflow

The full procedure for authoring a handoff. Invoked from the CREATE mode in [SKILL.md](../SKILL.md); the always-loaded body keeps the focus principle, the scaffold command, and the load-bearing fields, and this file holds the step-by-step.

## Step 0: Establish the next-session focus

Before scaffolding, pin down what the *resuming* session is for — the single outcome the next agent should drive toward. If the user passed an argument when invoking the skill (e.g. `/session-handoff wire up the rate-limit middleware`), treat it as that focus. Otherwise infer the most likely focus from the session and state it in one line for the user to confirm or correct.

This focus is the lens for the whole document: it sets the 🎯 Next Action and decides which pending work, context, and gotchas are relevant enough to include. A handoff with no clear next-session focus drifts into cataloguing the past instead of enabling the future.

## Step 1: Generate Scaffold

Run the smart scaffold script to create a pre-filled handoff document:

```bash
python3 scripts/create_handoff.py [task-slug]
```

Example: `python3 scripts/create_handoff.py implementing-user-auth`

**For continuation handoffs** (linking to previous work):
```bash
python3 scripts/create_handoff.py "auth-part-2" --continues-from 2024-01-15-auth.md
```

The script will:
- Create the handoffs directory (`.agents/handoffs/`) if needed
- Generate timestamped filename
- Pre-fill: timestamp, git branch, repo URL, open-PR URL (when available), recent commits, modified files
- Add handoff chain links if continuing from previous
- Detect a host session plan (Claude Code keeps them at `~/.claude/plans/<slug>.md`) and link to it if present
- Output file path for editing

## Step 1.5: Confirm Session Plan Reference

If `create_handoff.py` reports an `Active Session Plan` was detected, ask the user once:

> "I found a session plan at `<path>`. Should the handoff link to it as essential context for the resuming agent?"

- **Yes** → leave the `📋 Active Session Plan` section in place and fill in the `Status` TODO.
- **No** → remove the entire `📋 Active Session Plan` section before continuing.

This is a quick confirmation, not a discussion — the section is link-only and lightweight, so the bar for keeping it is low. The plan typically captures authored intent that the resuming agent should not have to re-derive.

## Step 2: Complete the Handoff Document

Open the generated file. Before filling the body, gather the canonical artifacts for this work — session plan, PRD/spec, ADRs, related issues, source PR, design docs — and list them in **📚 Source Artifacts** near the top. Write each section assuming the resuming agent has those open, so you only need to capture deltas and non-obvious context. See [Reference, don't duplicate](../SKILL.md#reference-dont-duplicate).

Then fill in the remaining `[TODO: ...]` placeholders, prioritizing in this order:

1. **🎯 Next Action** (top of document) — Single sentence, the FIRST thing the resuming agent should do, in service of the next-session focus from Step 0. This is the single most load-bearing field; a triaging agent may read only this line. Be concrete: include a file path, command, or specific step.
2. **📚 Source Artifacts** — Paths/URLs to PRD, session plan, ADRs, issues, PR, design docs. Write `none` for any line that genuinely has no artifact.
3. **Current State Summary** — What's happening right now, in one paragraph. Describe state, not intent — the linked artifacts cover *what* and *why*.
4. **Important Context** — Non-obvious constraints, decisions still under negotiation, things that would change the next action if missed. Only what the linked artifacts don't already say.
5. **Immediate Next Steps** — Numbered, ordered. Expands on the 🎯 Next Action line.
6. **Constraints for Resuming Agent** (Potential Gotchas + Skills to Use) — "Do NOT do X" rules; skills the next agent should invoke. **For Skills to Use:** scan your currently-loaded skill list and pick ones whose trigger condition matches a step in *Immediate Next Steps*. Forward-looking only — not skills you used this session. If none fit, write `none`.
7. **Decisions Made** — Rationale-first. If an ADR or PR comment already captures the rationale, link to it instead of restating. Inline only when there's no canonical record.

`none` is a valid explicit answer in **Source Artifacts**, **Blockers / Open Questions**, **Deferred Items**, **Potential Gotchas**, and **Skills to Use** — it tells the resuming agent "we considered this and there's nothing" rather than leaving the section ambiguous. Deleting the section throws that signal away.

The template structure (with explanations) lives at [handoff-template.md](handoff-template.md). Author-time nudges (e.g. how to tell when **Deferred Items** should be `none` because the deferred items ARE the handoff's primary work) live in the template body next to their placeholders, so they fire at the moment of filling, not in the always-loaded skill body.

## Step 3: Validate the Handoff

Run the validation script:

```bash
python3 scripts/validate_handoff.py <handoff-file>
```

The verdict is one of:

- **READY** — Handoff is complete; safe to share.
- **NEEDS_WORK** — Required section missing/unfilled, Next Action still a TODO, or other `[TODO: ...]` placeholders remain. Fix and re-run.
- **BLOCKED** — Potential secret detected. Remove the secret before continuing; the handoff must not ship as-is.

The report also surfaces missing recommended sections (advisory) and referenced files that don't exist on disk (advisory) — these don't block readiness but worth scanning.

## Step 4: Confirm Handoff

Report to user:
- Handoff file location
- Validation verdict and any warnings
- Summary of captured context
- The 🎯 Next Action line as the first thing the next session will do

## Step 5: Commit the Handoff

Once validation passes (Step 3), commit the handoff — by default it belongs in version control as a durable, shareable record:

```bash
git add .agents/handoffs/<file> && git commit -m "docs: add session handoff"
```

Commit *after* validation so the secret scan runs first. Skip only if the user explicitly wants an ephemeral/local-only handoff. In a git worktree, commit on the working branch and let it reach the default branch through the normal PR flow rather than committing to the main checkout directly.
