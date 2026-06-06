---
name: marketplace-publish-check
description: Read-only check of whether the current branch's changes require a marketplace-publish — a plugin added or removed, or a plugin's name/description/homepage edited (a version-only bump does not count). Run it when opening a PR to decide whether to apply the `marketplace-publish` label, so a needed catalog publish isn't forgotten after merge. Prints the affected plugins; exits non-zero when a publish is needed.
---

# marketplace-publish-check

Report whether the changes on the current branch touch the **marketplace catalog surface** — the parts of a plugin the marketplace `marketplace.json` actually stores: its presence (added/removed) and its `name` / `description` / `homepage`. When they do, a `marketplace-publish` is needed after merge; when they don't (a plain content edit or a version-only bump), it isn't.

Unlike the other maintainer skills here, this one is **model-invokable on purpose**: it's read-only and meant to run automatically at PR-creation to drive the `marketplace-publish` label. It never writes, pushes, or publishes — it only reports.

## When this matters

- Opening a PR that adds or removes a `plugins/<name>/` plugin, or edits a manifest's `name`/`description`/`homepage`.
- Deciding whether a PR should carry the `marketplace-publish` label (which gates the post-merge publish step / routine).

A version-only bump does **not** count — content reaches installs via the `version` key, not a catalog re-publish (see [`docs/PLUGIN-CONVENTIONS.md`](../../../docs/PLUGIN-CONVENTIONS.md) → Publishing). Neither do plain skill/command/doc edits.

This is the **marketplace** surface only. Component-count changes that affect `docs/CATALOG.md` are a separate concern handled by `catalog-refresh`.

## Run the check

```shell
python3 .claude/skills/marketplace-publish-check/scripts/needs_marketplace_publish.py [base-ref]
```

`base-ref` defaults to `main`. The script locates the repo root via git, diffs every `plugins/*/.claude-plugin/plugin.json` between the base and `HEAD`, and compares only the catalog fields — so a manifest that changed for an unrelated reason (a version bump) is correctly ignored. Stdlib only; no `jq`, no network.

- **Exit 1** — a publish is needed. It lists the affected plugins and why (`added` / `removed` / `changed <fields>`). Apply the `marketplace-publish` label to the PR.
- **Exit 0** — no catalog-surface change; no label, no publish.

## After labeling

The `marketplace-publish` label flags the PR so that, once merged, the catalog gets refreshed via the `marketplace-publish` skill (or a label-gated publish routine, if configured). This skill only **detects and reports** — it never runs the publish itself.
