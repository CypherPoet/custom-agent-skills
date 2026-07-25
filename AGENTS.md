Harness-neutral by default. Where a detail differs between harnesses, state it for **both**.

## Project

Public collection of reusable AI agent skills, packaged as **both** Claude Code and Codex plugins and distributed through each harness's plugin marketplace. Skills use the shared agent-skills [`SKILL.md`](https://agentskills.io/) format.

Composition is by **vendoring, not dependencies**: a skill shared across plugins is physically copied into each plugin that ships it, and no plugin ever references another.

## Map

- [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) — **source of truth** for how plugins and skills are built here.
- [`scripts/plugin-registry.json`](scripts/plugin-registry.json) — harness targeting, Codex categories, skill-sharing edges.
- [`scripts/sync_plugins.py`](scripts/sync_plugins.py) — generates every derived artifact from that registry.
- [`docs/CATALOG.md`](docs/CATALOG.md) — generated cross-plugin index.
- [`docs/automated-routines/skill-fact-check-manifest.json`](docs/automated-routines/skill-fact-check-manifest.json) — per-skill fact-check volatility tiers.

## Working In This Repo

- **Never hand-edit a generated file** — any `.codex-plugin/plugin.json` or vendored skill copy. Edit the source, then re-sync.
- Run `python3 scripts/sync_plugins.py` after editing a vendored skill's source or any `.claude-plugin/plugin.json`.
- **Bump a plugin's `version` whenever its content should reach installed users** — merging to `main` alone won't ship it. Re-run the sync after any bump; the health suite fails when content changed without one.
- Run the repo-local `skill-structure-check` skill before a PR that touches skills.
- Run `python3 -m unittest discover -s tests` before any PR; [`.github/workflows/verify.yml`](.github/workflows/verify.yml) runs the same suite on every PR and push to `main`.
- Run `marketplace-publish-check` when opening a PR, and apply the `marketplace-publish` label if it reports a needed publish. A merged label publishes automatically — the manual-only `marketplace-publish` skill is the fallback, and never self-triggers.
- Scaffold plugins via Claude Code `/plugin-dev:create-plugin` or Codex `$plugin-creator`; author skills with `/skill-creator`.
