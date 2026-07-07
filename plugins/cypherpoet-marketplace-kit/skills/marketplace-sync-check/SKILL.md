---
name: marketplace-sync-check
description: Audit whether this repo's local plugins/ match the two places that index them — its published Claude Code marketplace catalog (marketplace.json) AND its local docs/CATALOG.md. Use whenever the user asks what's published, whether the marketplace or the catalog docs are up to date, what's missing or stale, which plugins aren't listed yet, whether docs/CATALOG.md is current, or to double-check before/after publishing — phrasings like "is everything published", "check marketplace sync", "is the catalog up to date", "what's out of date in the catalog", "did I forget to publish anything", "is docs/CATALOG.md in sync", "diff my plugins against the marketplace". This is READ-ONLY — it reports drift and never edits any file or repo.
---

# marketplace-sync-check

Report drift between this source repo's local `plugins/` and the two places that index them: the **published marketplace catalog** (`marketplace.json`, in the marketplace repo) and the **local catalog** (`docs/CATALOG.md`, in this repo). **Read-only** — never edit either catalog, never commit, never open a PR. Just report what's out of sync and point at the right fix for each gap.

This is a plain procedure to run with your normal tools (`gh`, `jq`) — adapt as needed.

The two surfaces drift independently and are *not* reconciled the same way:

- The **marketplace catalog** is a *deliberate subset* — a plugin appears only once someone chooses to publish it, so unpublished plugins showing as `NEW` is expected, not a mistake. Fixes go through `marketplace-publish` (a PR on the marketplace repo).
- The **local catalog** should mirror `plugins/` *exactly* — the refresh rule is "new plugin → add a row" (`docs/PLUGIN-CONVENTIONS.md`), so a missing or stale row *is* an oversight. Fixes go through the `catalog-refresh` skill (regenerate the table) or a hand edit, never a publish.

## Marketplace catalog (`marketplace.json`)

1. **Pick the marketplace.** Resolve this repo's `owner/repo` (`gh repo view --json nameWithOwner -q .nameWithOwner`, or a normalized `git remote get-url origin`) and look it up in the bundled registry [`references/marketplaces.md`](../../references/marketplaces.md) (at runtime, read `${CLAUDE_PLUGIN_ROOT}/references/marketplaces.md`). If there's no row for this repo, ask the user which marketplace to target — and offer to add a row so the next run resolves it automatically.

2. **Fetch the live catalog** (raw file contents):
   ```bash
   gh api repos/<marketplace>/contents/.claude-plugin/marketplace.json -H "Accept: application/vnd.github.raw"
   ```

3. **Scope to this repo's entries.** A marketplace may aggregate several sources, so only compare catalog entries whose `source.url` points at *this* repo.

4. **Compare** those against local `plugins/*/.claude-plugin/plugin.json` (by `name`, `description`, and `homepage` — the fields `marketplace-publish` propagates) and report four buckets:
   - **NEW** — exists in `plugins/`, not in the catalog.
   - **CHANGED** — listed, but the catalog `description` or `homepage` differs from the local manifest.
   - **REMOVED** — listed (sourced from this repo) but no longer in `plugins/`.
   - **invalid** — a local `plugin.json` that doesn't parse.

   When comparing `homepage`, mirror `marketplace-publish`'s fallback rule: if the local manifest has no `homepage` (or it's empty), derive the expected fallback `https://github.com/<owner>/<this-repo>/tree/main/plugins/<name>` and compare against *that* instead of treating the field as a mismatch. This keeps the two skills symmetric — a plugin published with the fallback URL stays in sync until the manifest itself changes.

## Local catalog (`docs/CATALOG.md`)

Compare every `plugins/<name>` against the rows in `docs/CATALOG.md`. Each row carries a linked `name`, a `description`, and a `Components` count. Report three buckets:

- **missing row** — a plugin in `plugins/` with no row. Per the refresh rule the local catalog should list *every* plugin, so this is real drift, not a deliberate omission like marketplace `NEW`.
- **stale row** — the row exists, but its `description` differs from the plugin's manifest `description`, or its `Components` text differs from the plugin's actual components.
- **orphan row** — a row whose plugin no longer exists in `plugins/`.

The manifest is the source of truth for `description` (the row should match it verbatim, same as the marketplace check). Derive each plugin's component counts from its directory and compare to the row's `Components` text — the format rules (singular vs plural, the order skills → commands → agents → hooks → MCP servers, dropping zeros) live in `docs/PLUGIN-CONVENTIONS.md`:

- **skills** — subdirectories under `plugins/<name>/skills/` (each holds a `SKILL.md`)
- **commands** — `.md` files under `plugins/<name>/commands/`
- **agents** — `.md` files under `plugins/<name>/agents/`
- **hooks** — hook entries in `plugins/<name>/hooks/hooks.json`
- **MCP servers** — entries in the plugin's `.mcp.json` (or `mcpServers` in `plugin.json`)

## Reporting

Present both surfaces plainly, each clearly labelled, and stop. Then hand off — don't fix anything yourself:

- **Marketplace** `NEW`/`CHANGED` → `marketplace-publish <name>`; `REMOVED` → a manual catalog PR on the marketplace repo to drop the entry. `NEW` is expected for anything not yet deliberately published, so don't frame it as a mistake.
- **`docs/CATALOG.md`** missing / stale / orphan rows → regenerate the table with the `catalog-refresh` skill (or fix by hand) and commit it — a normal docs change. **Not** `marketplace-publish`; the local catalog isn't the marketplace.

**Do not modify anything** unless the user explicitly asks.

## Primary Sources

- [Plugin marketplaces (Claude Code docs)](https://code.claude.com/docs/en/plugin-marketplaces) — authoritative for `marketplace.json` schema and semantics.
