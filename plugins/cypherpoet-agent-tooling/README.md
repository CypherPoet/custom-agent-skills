# cypherpoet-agent-tooling

Bundle of Claude Code agent-tooling plugins for docs search, memory consolidation, and session handoff/harvest.

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install cypherpoet-agent-tooling@cypherpoet-toolchest
```

This is a convenience bundle — it ships no skills of its own. Installing it pulls in the plugins below. Install any of them individually if you only want one.

## Dependencies

Installed automatically with this plugin:

| Plugin | Version | Description |
|---|---|---|
| [cypherpoet-claude-docs-search](../cypherpoet-claude-docs-search) | `latest` | Look up answers about Claude Code features and behavior in the official Claude Code documentation. |
| [cypherpoet-claude-memory-consolidation](../cypherpoet-claude-memory-consolidation) | `latest` | Audit and consolidate Claude's per-project auto-memory directory, deduping, repairing, and pruning with per-cluster approval. |
| [cypherpoet-session-handoff](../cypherpoet-session-handoff) | `latest` | Write a structured handoff document so a fresh agent can resume long-running work without losing context. |
| [cypherpoet-session-harvest](../cypherpoet-session-harvest) | `latest` | Run a pre-exit sweep of a conversation for learnings worth preserving in project memory. |
