---
name: marketplace-publish-check
description: Read-only check of whether the current branch's changes require a marketplace-publish — a plugin added or removed, a plugin's name/description/homepage edited, or its dual-harness classification / Codex category changed in scripts/dual-harness.json (a version-only bump does not count). Run it when opening a PR to decide whether to apply the `marketplace-publish` label, so a needed catalog publish isn't forgotten after merge. Prints the affected plugins; exits non-zero when a publish is needed.
---

# marketplace-publish-check

**Verified:** 2026-07-11

Report whether the changes on the current branch touch the **marketplace catalog surface** — the parts of a plugin the marketplace's catalog files actually store: its presence (added/removed) and its `name` / `description` / `homepage` (the Claude `.claude-plugin/marketplace.json`), plus its dual-harness classification and Codex `category` from `scripts/dual-harness.json` (the Codex `.agents/plugins/marketplace.json`). When they do, a `marketplace-publish` is needed after merge; when they don't (a plain content edit or a version-only bump), it isn't.

Like the kit's other read-only skills, this one is **model-invokable on purpose** — and it's specifically meant to run automatically at PR-creation to drive the `marketplace-publish` label (only `marketplace-publish` itself, the skill with side effects, is manual-only). It never writes, pushes, or publishes — it only reports.

## When this matters

- Opening a PR that adds or removes a `plugins/<name>/` plugin, edits a manifest's `name`/`description`/`homepage`, or changes a plugin's classification or `category` in `scripts/dual-harness.json`.
- Deciding whether a PR should carry the `marketplace-publish` label (which gates the post-merge publish step / routine).

A version-only bump does **not** count — content reaches installs via the `version` key, not a catalog re-publish (see `docs/PLUGIN-CONVENTIONS.md` → Publishing). Neither do plain skill/command/doc edits.

This is the **marketplace** surface only. Component-count changes that affect `docs/CATALOG.md` are a separate concern handled by `catalog-refresh`.

## Run the check

```shell
python3 "${CLAUDE_PLUGIN_ROOT}/skills/marketplace-publish-check/scripts/needs_marketplace_publish.py" [base-ref]
```

`base-ref` defaults to `main`. The script locates the repo root via git, diffs every `plugins/*/.claude-plugin/plugin.json` plus `scripts/dual-harness.json` between the base and `HEAD`, and compares only the catalog fields — so a manifest that changed for an unrelated reason (a version bump) is correctly ignored. Stdlib only; no `jq`, no network.

- **Exit 1** — a publish is needed. It lists the affected plugins and why: `added` / `removed` / `changed <fields>` for the Claude catalog fields, and `added to the Codex catalog surface` / `left the Codex catalog surface` / `changed Codex <fields>` for classification or `dual-harness.json` entry changes (a plugin with several reasons joins them with `;`). Apply the `marketplace-publish` label to the PR.
- **Exit 0** — no catalog-surface change; no label, no publish.

## After labeling

The `marketplace-publish` label flags the PR so that, once merged, the catalog gets refreshed via the `marketplace-publish` skill (or a label-gated publish routine, if configured). This skill only **detects and reports** — it never runs the publish itself.

## Primary Sources

- [Plugin marketplaces (Claude Code docs)](https://code.claude.com/docs/en/plugin-marketplaces) — authoritative for which manifest fields the marketplace catalog copies.
