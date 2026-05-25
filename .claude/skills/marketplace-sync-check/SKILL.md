---
name: marketplace-sync-check
description: Audit whether this repo's local plugins/ match what's published in its Claude Code marketplace catalog. Use whenever the user asks what's published, whether the marketplace is up to date, what's missing or stale, which plugins aren't listed yet, or to double-check the catalog before/after publishing — phrasings like "is everything published", "check marketplace sync", "what's out of date in the catalog", "did I forget to publish anything", "diff my plugins against the marketplace". This is READ-ONLY: it reports drift and never edits any file or repo.
---

# marketplace-sync-check

Report drift between this source repo's local `plugins/` and what its marketplace catalog actually lists. **Read-only** — never edit `marketplace.json`, never commit, never open a PR. Just report what's out of sync and point at `marketplace-publish` for gaps the user wants to close.

This is a plain procedure to run with your normal tools (`gh`, `jq`) — adapt as needed.

## Procedure

1. **Pick the marketplace** from this repo's `origin` remote (`custom-agent-skills` → `CypherPoet/cypherpoet-toolchest`), or use one the user names.

2. **Fetch the live catalog** (raw file contents):
   ```bash
   gh api repos/<marketplace>/contents/.claude-plugin/marketplace.json -H "Accept: application/vnd.github.raw"
   ```

3. **Scope to this repo's entries.** A marketplace may aggregate several sources, so only compare catalog entries whose `source.url` points at *this* repo.

4. **Compare** those against local `plugins/*/.claude-plugin/plugin.json` (by `name` and `description`) and report four buckets:
   - **NEW** — exists in `plugins/`, not in the catalog.
   - **CHANGED** — listed, but the catalog `description` differs from the local one.
   - **REMOVED** — listed (sourced from this repo) but no longer in `plugins/`.
   - **invalid** — a local `plugin.json` that doesn't parse.

5. **Present it plainly and stop.** NEW does *not* mean "you forgot" — publishing is deliberate and per-plugin, so unpublished plugins are expected to show until the user chooses to publish them. For anything they want to reconcile, hand off: `marketplace-publish <name>` for NEW/CHANGED; a manual catalog PR to drop a REMOVED entry. **Do not modify anything** unless the user explicitly asks.
