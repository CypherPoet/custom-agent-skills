---
name: catalog-refresh
description: Regenerate this repo's docs/CATALOG.md plugin table from the plugin manifests — rebuilding every row's name, description, and component counts (skills/commands/agents/hooks/MCP servers) deterministically from plugins/, so a missing, stale, or mis-counted row is fixed without hand-editing. Use when the user asks to refresh, regenerate, or rebuild the local catalog, or right after a plugin's name, description, or component count changes and docs/CATALOG.md needs to match. The write-capable counterpart to marketplace-sync-check, which only reports the same local-catalog drift. Touches only the local catalog table (the surrounding prose is preserved); never the published marketplace, never commits, never opens a PR.
---

# catalog-refresh

Regenerate the plugin table in `docs/CATALOG.md` from the plugin manifests. The local catalog is *deterministically derivable* from `plugins/` — every row's `name`, `description`, and `Components` count comes straight from a `plugin.json` and the plugin's directory — so it can be rebuilt mechanically instead of hand-edited.

This is the **actuator** half of the local-catalog pair: [`marketplace-sync-check`](../marketplace-sync-check/SKILL.md) *reports* `docs/CATALOG.md` drift (missing / stale / orphan rows), and this skill *fixes* it. The audit stays read-only and safe to run anytime; this writer regenerates the table deterministically from the manifests, so it's safe to run on request or right after a manifest change — the output is a reviewable diff, and it still never commits or touches the published marketplace.

**Scope — local catalog only.** This rewrites `docs/CATALOG.md` and nothing else. It does **not** touch the published marketplace (`marketplace.json` on the marketplace repo), commit, or open a PR. The marketplace is a deliberate, per-plugin publish — for that, use `marketplace-publish`.

The regeneration logic is a bundled script — Python 3 standard library only, no installs, no network. Run it and relay what it prints; don't reimplement it inline.

## Run it

From anywhere in the repo:

```shell
# Dry-run: report drift and show the diff, write nothing (exit 1 if stale)
python3 "${CLAUDE_PLUGIN_ROOT}/skills/catalog-refresh/scripts/refresh_catalog.py" --check

# Regenerate the table in place
python3 "${CLAUDE_PLUGIN_ROOT}/skills/catalog-refresh/scripts/refresh_catalog.py"
```

The script finds the repo root via git, walks every `plugins/*/.claude-plugin/plugin.json`, derives each plugin's `description` (verbatim from the manifest) and `Components` count, sorts by name, and replaces **only** the markdown table — the intro line and `## Installing` section are left untouched. Component counting (the order skills → commands → agents → hooks → MCP servers, singular vs plural, dropping zeros) follows `docs/PLUGIN-CONVENTIONS.md` → Top-Level Catalog.

It's idempotent: on an already-current catalog it prints `already in sync` and writes nothing. A manifest with no `description` is reported as a warning (the catalog can't ship a blank cell) — populate it and re-run.

## After running

The skill changes the working tree but does not commit. **Review the diff** (`git diff docs/CATALOG.md`), then commit it yourself — typically alongside the plugin change that caused the drift (a new plugin, a renamed skill, an edited description). If `--check` reported `already in sync`, there's nothing to do.

If the description also needs to reach the **published** catalog (you edited a plugin's manifest `description`), that's a separate step — run `marketplace-publish <name>` to refresh the marketplace entry.
