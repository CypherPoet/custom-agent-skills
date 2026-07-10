---
name: remote-branch-sync
description: >
  Use whenever the user asks to sync with the remote, pull in the latest,
  get up to date with main/origin, refresh local branches, or catch a branch
  up before continuing work — including terse asks like "sync with the
  remote", "pull latest from main", "update my branch", or "get current".
  Fetches with prune, fast-forwards what is safe, integrates the default
  branch into feature work only when asked, and reports divergence instead
  of guessing at a resolution.
---

# Remote Branch Sync

Bring local git state up to date with the remote, safely. The core promise: after this skill runs, the user knows exactly how their local branches relate to the remote — and nothing was rebased, merged, or discarded without them asking for it.

## Step 1: Survey before touching anything

```bash
git fetch --all --prune
git status -sb
git branch -vv
```

Identify the default branch (`git symbolic-ref refs/remotes/origin/HEAD --short`, falling back to `git remote show origin`) and note:

- Uncommitted changes in the working tree
- Ahead/behind counts for the current branch
- Branches whose upstream is now `[gone]`

**If the working tree is dirty, stop and report before any branch movement.** Never stash silently — the user may not remember the stash exists, and a sync that hides work is worse than one that waits.

## Step 2: Update the current branch

- Upstream set and behind only → `git pull --ff-only`.
- Ahead only → nothing to pull; report the unpushed commits (pushing is out of scope unless asked).
- **Diverged → report both sides and ask.** Rebase vs merge is a project-convention decision, not a guess; check the project's CLAUDE.md for a stated preference before asking.

## Step 3: "Pull in the latest from main"

When the ask includes catching up with the default branch while on feature work:

1. Update the local default branch without leaving the current checkout: `git fetch origin <default>:<default>`. This refspec fast-forwards the local default and refuses in two cases: the branch is checked out in another worktree, or the update isn't a fast-forward because the local default has diverged (carries commits not on the remote). Either way, **report and stop — don't force it** (`+<default>:<default>` would silently discard the divergent local commits). For the worktree case, update it from that worktree instead (`git -C <worktree> pull --ff-only`); for divergence, surface it and let the user decide.
2. Integrate into the current branch per the project's convention (rebase or merge). If no convention is discoverable, ask once and reuse the answer for the rest of the session.

**Worktree guardrail:** when the session runs in a worktree, syncing means fetching and fast-forwarding local refs — never fast-forward-and-push the default branch from the main checkout on the feature's behalf; feature work reaches the default branch through its PR.

## Step 4: Report

Close with a short summary: what was fetched, how many remote-tracking refs were pruned, what the current branch did (e.g. `main a1b2c3d → e4f5a6b, fast-forward`), any divergence awaiting a decision, and how many local branches are now `[gone]`. If there are `[gone]` branches or stale worktrees, point the user at [worktree-cleanup](../worktree-cleanup/SKILL.md) rather than cleaning up inline — deletion deserves its own approval flow.
