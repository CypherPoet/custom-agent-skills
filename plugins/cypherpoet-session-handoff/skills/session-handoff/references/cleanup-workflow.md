# CLEANUP Workflow

The full procedure for retiring handoffs whose work has demonstrably moved on. Invoked from the CLEANUP mode in [SKILL.md](../SKILL.md); the procedure lives here so the always-loaded skill body stays lean and only carries the entry point and the safety invariant.

Handoffs are committed by default, so they accumulate. Removal is low-stakes — git history is the undo — but the bar for *what* to retire is deliberately high: **completion + supersession, never staleness alone.**

## Step 1: Find Candidates

```bash
python3 scripts/find_cleanup_candidates.py
```

Read-only. Scans the neutral `.agents/handoffs/` and the legacy `.claude/handoffs/`, then groups handoffs into tiers:

- 🔴 **Retire — superseded + complete**: a later handoff `--continues-from` it, and it has no remaining `[TODO:` placeholders. The chain moved past finished work. Strong candidate.
- 🟡 **Retire candidate — very stale + complete**: rated `VERY_STALE`, complete, and standalone (not a chain tip). Old, done, unlikely to resume. Advisory.
- ⚠️ **Keep + review**: superseded but still has unfinished TODOs — never auto-retired. The successor may have moved on before this one's pending work was captured; check before removing.

Each candidate line reports its title, reason, location (neutral/legacy), and whether it's git-tracked (→ `git rm`) or untracked (→ `trash`). Pass `--verbose` to also list what's being kept and why.

The script exits `1` when it finds candidates and `0` when there are none — a found/not-found signal, not an error. Read its output and continue the workflow regardless of the exit code.

## Step 2: Present for Approval

Show the numbered candidates grouped by tier. State the bias plainly: **staleness alone never qualifies a handoff** — an old but unsuperseded record can be the only trace of why a decision was made, and is legitimate to keep. Superseded + complete is the only strong signal; very-stale is advisory. When in doubt, keep.

Ask which to retire — "all / specific numbers (e.g. 1, 3) / skip the very-stale ones / none". **Never delete without explicit per-item approval, and never auto-run this workflow.**

## Step 3: Apply

For each approved candidate, use the removal the detector reported (a handoff may live in `.agents/handoffs/` or the legacy `.claude/handoffs/` — use the path it printed):

- **Tracked** → `git rm <path>`
- **Untracked** → `trash <path>`

Then commit the `git rm`'d set:

```bash
git commit -m "docs: retire superseded/obsolete handoffs"
```

In a git worktree, commit on the working branch and let it reach the default branch through the normal PR flow rather than committing to the main checkout directly. Git history preserves every removed handoff, so a mistaken retire is recoverable with `git restore`.

## Step 4: Report

Tell the user what was retired and what was kept, and note that removed handoffs remain in git history.
