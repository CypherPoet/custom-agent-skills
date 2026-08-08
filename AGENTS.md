Harness-neutral by default. Where a detail differs between harnesses, state it for **both**.

## Project

Public collection of reusable AI agent skills, packaged as **both** Claude Code and Codex plugins and distributed through each harness's plugin marketplace. Skills use the shared agent-skills [`SKILL.md`](https://agentskills.io/) format.

Composition is by **vendoring, not dependencies**: neither harness resolves a reference to a skill in another plugin, so a shared skill is physically copied into each plugin that ships it.

## Map

- [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) — **source of truth** for how plugins and skills are built here.
- [`scripts/plugin-registry.json`](scripts/plugin-registry.json) — harness targeting, Codex categories, skill-sharing edges.
- [`tooling/`](tooling/) — shared generator and Codex interface validator package used by both source repositories.
- [`scripts/sync_plugins.py`](scripts/sync_plugins.py) — thin compatibility launcher for the shared package.
- [`docs/CATALOG.md`](docs/CATALOG.md) — generated cross-plugin index.
- [`docs/automated-routines/skill-fact-check-manifest.json`](docs/automated-routines/skill-fact-check-manifest.json) — per-skill fact-check volatility tiers.

## Working In This Repo

- **Never hand-edit a generated file** — any `.codex-plugin/plugin.json` or vendored skill copy. Edit the source, then re-sync.
- Run `python3 -m pip install -r requirements-tooling.txt` after checkout and whenever the tooling pin changes.
- Run `python3 scripts/sync_plugins.py` after editing a `.claude-plugin/plugin.json`, the registry, or the source of a vendored skill.
- **Bump a plugin's `version` whenever its content should reach installed users** — merging to `main` alone won't ship it. Re-run the sync after any bump; the health suite fails when content changed without one.
- Run the repo-local `skill-structure-check` skill before a PR that touches skills.
- Run `python3 -m unittest discover -s tests` before any PR; [`.github/workflows/verify.yml`](.github/workflows/verify.yml) runs the same suite on every PR and push to `main`.
- Run `marketplace-publish-check` when opening a PR, and apply the `marketplace-publish` label if it reports a needed publish. A merged label publishes automatically — the manual-only `marketplace-publish` skill is the fallback, and never self-triggers.
- Scaffold with whatever your harness offers — no scaffolder emits a repo-conformant plugin on its own. Finish against [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).
- [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) holds mechanisms and rationale; this file holds the imperatives. Neither restates the other.
