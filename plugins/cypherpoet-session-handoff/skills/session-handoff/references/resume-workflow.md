# RESUME Workflow

The full procedure for picking up an existing handoff. Invoked from the RESUME mode in [SKILL.md](../SKILL.md); the always-loaded body keeps the entry commands and the verify-before-acting invariant, and this file holds the step-by-step.

## Step 1: Find Available Handoffs

```bash
python3 scripts/list_handoffs.py
```

Shows all handoffs with dates, titles, and completion status.

## Step 2: Check Staleness

```bash
python3 scripts/check_staleness.py <handoff-file>
```

The script reports a level (FRESH / SLIGHTLY_STALE / STALE / VERY_STALE) and flags specific drift — commits, branch mismatch, missing files. Treat STALE/VERY_STALE as a signal to verify context carefully or start a fresh handoff. The verdict lives in the printed report; the script exits 0 whenever it produced one, so a nonzero exit means the check itself failed (e.g. missing file), not that the handoff is stale.

## Step 3: Load the Handoff

Read the handoff document, but you do not need to read it cover to cover. The document is structured so the resuming agent can triage quickly.

If the handoff is part of a chain (has a "Continues from" link), also read the linked predecessor for full context — but only after the current handoff's high-priority sections.

## Step 3.5: Read Strategy

Read this way to keep triage cost low without losing context:

- **Read in full**: 🎯 Next Action, Session Metadata, 📚 Source Artifacts, Current State Summary, Important Context, Pending Work, Constraints for Resuming Agent.
- **Open the linked artifacts** in 📚 Source Artifacts before reading further — the handoff body assumes you have them. Skip ones marked `none`.
- **Skim**: Codebase Understanding, Work Completed. These exist for spot-lookups, not linear reading.
- **Consult on demand**: Environment State.

The 🎯 Next Action line at the top is the load-bearing instruction — everything else fills in the why and the how. Stop reading early once you have enough context to act.

## Step 4: Verify Context

Before executing the next action, sanity-check that the handoff's assumptions still hold:

1. You are in the correct project directory — the handoff lives at `<project>/.agents/handoffs/` (or the legacy `<project>/.claude/handoffs/`), so check that the handoff's path matches your current working directory.
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

## Step 5: Begin Work

Execute the 🎯 Next Action at the top of the handoff. The numbered list under **Immediate Next Steps** expands on it.

Reference these sections as you work:
- **Critical Files** for important locations and "don't reintroduce X" warnings.
- **Key Patterns Discovered** for conventions the previous session established.
- **Potential Gotchas** for known landmines.
- **Skills to Use** for the right tool/skill to invoke at each step.

## Step 6: Chain, Don't Rewrite

The handoff you resumed from is a consumed record, not a live scratchpad. Routine bookkeeping edits to it ("marked item 2 done") add nothing — progress is already visible in commits, the PR, and this session — and they muddy the document's provenance as a point-in-time snapshot.

- **Don't update the resumed handoff as you work.** The one exception is a factual hazard: something in it is now wrong enough to mislead a future reader (a decision got reversed, a gotcha resolved differently than recorded). Correct that in place, and nothing else.
- **When this session pauses with work remaining**, write a *new* handoff with `--continues-from <the-one-you-resumed>` — that's where completed/pending status belongs.
- **When the work is simply finished**, no handoff writing is needed at all; the CLEANUP workflow retires superseded records later.
