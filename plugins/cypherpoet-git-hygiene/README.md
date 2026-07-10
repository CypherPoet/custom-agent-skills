# cypherpoet-git-hygiene

Keep local git state tidy: sync branches with the remote, and clean up stale branches and worktrees with per-item approval.

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install cypherpoet-git-hygiene@cypherpoet-toolchest
```

## Skills

| Skill | Description |
|---|---|
| [remote-branch-sync](skills/remote-branch-sync/SKILL.md) | Fetch with prune and fast-forward what's safe; report divergence instead of guessing. |
| [worktree-cleanup](skills/worktree-cleanup/SKILL.md) | Retire gone/merged branches and the worktrees attached to them, per-item approved. |
