---
name: catalog-refresh
description: >
  Regenerate docs/CATALOG.md's plugin table deterministically from the plugin
  manifests, fixing missing, stale, or mis-counted rows. Use when the user asks
  to refresh the local catalog, or after a plugin's name, description, or
  component count changes. The write-capable counterpart to
  marketplace-sync-check; touches only the local catalog table — never the
  published marketplace, never commits.
---

# catalog-refresh

Regenerate the plugin table in `docs/CATALOG.md` from the plugin manifests. The local catalog is *deterministically derivable* from `plugins/` — every row's `name`, `description`, and `Components` count comes straight from a `plugin.json` and the plugin's directory — so it can be rebuilt mechanically instead of hand-edited.

This is the **actuator** half of the local-catalog pair: [`marketplace-sync-check`](../marketplace-sync-check/SKILL.md) *reports* `docs/CATALOG.md` drift (missing / stale / orphan rows), and this skill *fixes* it. The audit stays read-only and safe to run anytime; this writer regenerates the table deterministically from the manifests, so it's safe to run on request or right after a manifest change — the output is a reviewable diff, and it still never commits or touches the published marketplace.

**Scope — local catalog only.** This rewrites `docs/CATALOG.md` and nothing else. It does **not** touch the published marketplace (`marketplace.json` on the marketplace repo), commit, or open a PR. The marketplace is a deliberate, per-plugin publish — for that, use `marketplace-publish`.

The regeneration logic is a bundled script — Python 3 standard library only, no installs, no network. Run it and relay what it prints; don't reimplement it inline.

## Run it

With your working directory anywhere in the target repo, run the bundled script. `scripts/` below is relative to **this skill's directory** — your harness shows the skill's location when it loads; prefix the commands with it:

```shell
# Dry-run: report drift and show the diff, write nothing (exit 1 if stale)
python3 scripts/refresh_catalog.py --check

# Regenerate the table in place
python3 scripts/refresh_catalog.py
```

The script finds the repo root via git and walks every directory under `plugins/`. It reads the Claude manifest when present and otherwise reads the Codex manifest, so Claude-only, Codex-only, and multi-platform plugins all appear once. It derives the `description` and `Components` count, sorts by name, and replaces **only** the markdown table — the intro line and `## Installing` section are left untouched. Component counting (the order skills → commands → agents → hooks → MCP servers, singular vs plural, dropping zeros) follows `docs/PLUGIN-CONVENTIONS.md` → Top-Level Catalog.

It's idempotent: on an already-current catalog it prints `already in sync` and writes nothing. A manifest with no `description` is reported as a warning (the catalog can't ship a blank cell) — populate it and re-run.

## After running

The skill changes the working tree but does not commit. **Review the diff** (`git diff docs/CATALOG.md`), then commit it yourself — typically alongside the plugin change that caused the drift (a new plugin, a renamed skill, an edited description). If `--check` reported `already in sync`, there's nothing to do.

If the description also needs to reach the **published** catalog (you edited a plugin's manifest `description`), that's a separate step — run `marketplace-publish <name>` to refresh the marketplace entry.

## Primary Sources

None declared yet — the fact-check routine falls back to vendor-primary sources per claim. Add entries as `- [Name](url) — what it's authoritative for.`
