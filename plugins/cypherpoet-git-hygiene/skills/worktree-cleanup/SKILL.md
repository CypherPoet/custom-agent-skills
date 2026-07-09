---
name: worktree-cleanup
description: >
  Use whenever the user asks to clean up stale branches AND worktrees, prune
  old worktrees, remove leftover agent-created checkouts (e.g.
  .claude-worktrees), or when a "clean gone branches" ask mentions worktrees —
  "clean up my stale/outdated branches and worktrees", "prune old worktrees",
  "tidy my checkouts". Extends gone-branch cleanup (e.g. /clean_gone) to the
  worktrees attached to those branches: inventories candidates with their
  risk, then removes only what the user approves, item by item.
---

# Worktree Cleanup

Gone-branch cleanup tools handle branches; this skill also retires the **worktrees** those branches live in — including the `.claude-worktrees`-style checkouts that agent sessions create and abandon. The invariant: nothing is deleted without the user seeing it in a candidate list first, and nothing holding unsaved or unpushed work is deleted without an explicit, per-item "yes".

## Step 1: Inventory

```bash
git fetch --prune
git worktree list --porcelain
git branch -vv                       # upstream state; [gone] markers
git branch --merged <default-branch>
git worktree prune --dry-run -v      # orphaned admin entries (dir already deleted)
```

## Step 2: Classify candidates

| Tier | What | Default action |
|---|---|---|
| 🟢 Orphaned admin entries | `git worktree prune --dry-run` hits — the directory is already gone | Prune |
| 🟢 Worktrees on `[gone]` branches | Remote branch deleted (merged PR, typically) | Propose removal |
| 🟡 Worktrees on branches merged into the default branch | Work landed; checkout is residue | Propose removal |
| 🔴 Stale but unmerged | Old mtime, branch never merged, or no upstream at all | Report only — never propose deletion; unmerged work may be the only copy |

For every proposed worktree, check what it's holding before showing it to the user:

```bash
git -C <worktree> status --porcelain      # uncommitted changes?
git -C <worktree> log --oneline @{u}..    # unpushed commits? (no upstream → treat ALL local commits as unpushed)
```

Anything dirty or unpushed gets flagged 🔴 in the candidate list regardless of tier — deleting it destroys work.

## Step 3: Present and get approval

Show one table: path, branch, tier, dirty/unpushed flags, last-commit age. Ask for approval **per item** (or an explicit "all the green ones"). A blanket "clean it up" from before the list existed does not count as approval of the list — the user is approving specific deletions, not the concept of cleanup.

## Step 4: Remove

For each approved item, in this order:

```bash
git worktree remove <path>            # refuses dirty trees — good; --force only with explicit per-item consent
git branch -D <branch>                # after its worktree is gone; only for [gone]/merged branches from the approved list
git worktree prune                    # clear remaining admin entries
```

Never touch the main checkout or the worktree the current session is running in. Close with a summary of what was removed, what was kept and why (especially 🔴 items), and disk space reclaimed if easily available.
