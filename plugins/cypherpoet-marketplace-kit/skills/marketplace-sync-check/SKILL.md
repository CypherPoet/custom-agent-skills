---
name: marketplace-sync-check
description: >
  Read-only audit of whether this repo's plugins/ match the places that index
  them: both published marketplace catalogs plus the local docs/CATALOG.md. Use
  for "is everything published", "is the catalog up to date", "did I forget to
  publish anything", or a pre/post-publish double-check. Reports drift; never
  edits any file or repo.
---

# marketplace-sync-check

**Verified:** 2026-07-11

Report drift between this source repo's local `plugins/` and the places that index them: the **published marketplace catalogs** (Claude `.claude-plugin/marketplace.json` and Codex `.agents/plugins/marketplace.json`, both in the marketplace repo) and the **local catalog** (`docs/CATALOG.md`, in this repo). **Read-only** — never edit a catalog, never commit, never open a PR. Just report what's out of sync and point at the right fix for each gap.

This is a plain procedure to run with your normal tools (`gh`, `jq`) — adapt as needed.

The two surfaces drift independently and are *not* reconciled the same way:

- The **marketplace catalogs** are a *deliberate subset* — a plugin appears only once someone chooses to publish it, so unpublished plugins showing as `NEW` is expected, not a mistake. Fixes go through `marketplace-publish` (a PR on the marketplace repo, which maintains both harness catalogs together).
- The **local catalog** should mirror `plugins/` *exactly* — the refresh rule is "new plugin → add a row" (`docs/PLUGIN-CONVENTIONS.md`), so a missing or stale row *is* an oversight. Fixes go through the `catalog-refresh` skill (regenerate the table) or a hand edit, never a publish.

## Marketplace Catalogs (Claude + Codex)

1. **Pick the marketplace.** Resolve this repo's `owner/repo` (`gh repo view --json nameWithOwner -q .nameWithOwner`, or a normalized `git remote get-url origin`) and look it up in the bundled registry [`references/marketplaces.md`](../../references/marketplaces.md) (at runtime, resolve that link relative to this skill's directory — it lives at the plugin root, two levels up from this SKILL.md). If there's no row for this repo, ask the user which marketplace to target — and offer to add a row so the next run resolves it automatically.

2. **Fetch the live catalogs** (raw file contents; the Codex file may 404 on a marketplace that hasn't published Codex entries yet — report that rather than erroring):
   ```bash
   gh api repos/<marketplace>/contents/.claude-plugin/marketplace.json -H "Accept: application/vnd.github.raw"
   gh api repos/<marketplace>/contents/.agents/plugins/marketplace.json -H "Accept: application/vnd.github.raw"
   ```

3. **Scope to this repo's entries.** A marketplace may aggregate several sources, so only compare catalog entries whose `source.url` points at *this* repo.

4. **Compare the Claude catalog** against local `plugins/*/.claude-plugin/plugin.json` (by `name`, `description`, and `homepage` — the fields `marketplace-publish` propagates) and report four buckets:
   - **NEW** — exists in `plugins/`, not in the catalog.
   - **CHANGED** — listed, but the catalog `description` or `homepage` differs from the local manifest.
   - **REMOVED** — listed (sourced from this repo) but no longer in `plugins/`.
   - **invalid** — a local `plugin.json` that doesn't parse.

   When comparing `homepage`, mirror `marketplace-publish`'s fallback rule: if the local manifest has no `homepage` (or it's empty), derive the expected fallback `https://github.com/<owner>/<this-repo>/tree/<default-branch>/plugins/<name>` (resolving the source repo's default branch, as `marketplace-publish` does) and compare against *that* instead of treating the field as a mismatch. This keeps the two skills symmetric — a plugin published with the fallback URL stays in sync until the manifest itself changes.

5. **Compare the Codex catalog** independently against local `plugins/*/.codex-plugin/plugin.json`. Manifest presence declares Codex support. Expected entries use the `git-subdir` source pointing at the shared plugin directory, the source repository's resolved default branch, `interface.category` from the Codex manifest, and the constant policy (`installation: AVAILABLE`, `authentication: ON_INSTALL`). Report:
   - **NEW** — a Codex manifest exists locally but the plugin is not published in the Codex catalog. This is expected until someone chooses to publish it.
   - **CHANGED** — the catalog `name`, `category`, source, or policy differs from the authored Codex manifest and repository contract.
   - **REMOVED** — a Codex catalog entry exists but its source Codex manifest no longer does. Remove only the Codex entry when the Claude manifest remains.
   - **invalid** — the Codex manifest does not parse or lacks the data needed to build an entry.

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

- **Marketplace** (either catalog) `NEW`/`CHANGED` → `marketplace-publish <name>`. `REMOVED` → remove the entry only from the platform whose manifest disappeared; deleting the whole plugin removes both. `NEW` is expected for anything not yet deliberately published, so do not frame it as a mistake.
- **`docs/CATALOG.md`** missing / stale / orphan rows → regenerate the table with the `catalog-refresh` skill (or fix by hand) and commit it — a normal docs change. **Not** `marketplace-publish`; the local catalog isn't the marketplace.

**Do not modify anything** unless the user explicitly asks.

## Primary Sources

- [Plugin marketplaces (Claude Code docs)](https://code.claude.com/docs/en/plugin-marketplaces) — authoritative for the Claude `marketplace.json` schema and semantics.
- [Build plugins (Codex docs)](https://learn.chatgpt.com/docs/build-plugins) — authoritative for the Codex `.agents/plugins/marketplace.json` schema (`source` types, required `policy` + `category`).
