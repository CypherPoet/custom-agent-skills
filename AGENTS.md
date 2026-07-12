# AGENTS.md

The definitive project rules for this repo. Read by **Codex** directly and by **Claude Code** through the `@AGENTS.md` import in [`CLAUDE.md`](CLAUDE.md). Keep everything here harness-neutral; where a detail differs between harnesses, state it for **both**.

## Project

Public collection of reusable AI agent skills, packaged as **both** Claude Code and Codex plugins and distributed through each harness's plugin marketplace. Skills use the shared agent-skills [`SKILL.md`](https://agentskills.io/) format, so a skill body runs on either harness unchanged.

## Map

- [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) — **source of truth** for how plugins and skills are built here: dual-harness manifests, vendoring, the two marketplaces, skill conventions.
- [`docs/CATALOG.md`](docs/CATALOG.md) — generated cross-plugin index (one row per plugin).
- [`scripts/dual-harness.json`](scripts/dual-harness.json) + [`scripts/sync_dual_harness.py`](scripts/sync_dual_harness.py) — the single config + generator for every dual-harness artifact (vendored skills, `.codex-plugin/` manifests, the Codex marketplace).
- [`docs/automated-routines/skill-fact-check-manifest.json`](docs/automated-routines/skill-fact-check-manifest.json) — per-skill fact-check volatility tiers.

## Architecture

- `plugins/<plugin-name>/` — one themed plugin, **self-contained**: install pulls only this directory (Claude Code `git-subdir` sparse-clone; Codex marketplace fetch), so a plugin ships every skill it needs. Each carries two manifests — `.claude-plugin/plugin.json` (hand-authored, the source of truth) and `.codex-plugin/plugin.json` (**generated**: the Claude manifest mirrored, plus `"skills": "./skills/"`) — over a shared `skills/<name>/SKILL.md`.
- **Composition is by vendoring, not dependencies.** A skill shared across plugins is copied into each plugin that ships it — no plugin references another (neither harness can resolve a cross-plugin reference at install). `scripts/sync_dual_harness.py` owns every vendored copy, every `.codex-plugin/` manifest, and `.agents/plugins/marketplace.json`. Rationale and the full workflow live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).
- **Two marketplaces.** The Claude Code marketplace is the separate [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) repo; the Codex marketplace is `.agents/plugins/marketplace.json` in **this** repo. A few Claude-Code-specific plugins ship to Claude only — the split, with reasons, is in [`scripts/dual-harness.json`](scripts/dual-harness.json).

## Working In This Repo

- **After editing a vendored skill's source or any `.claude-plugin/plugin.json`, run `python scripts/sync_dual_harness.py`** to regenerate the vendored copies, Codex manifests, and marketplace. **Never hand-edit a generated file** — any `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, or a vendored skill copy. Edit the source and re-sync.
- **Bump a plugin's `version`** whenever a content change should reach installed users — pushing to `main` alone won't (version is each harness's update cache key). Keep the `.codex-plugin` version in step by re-running the sync after the bump.
- **Before a PR that touches skills**, run the repo-local `skill-structure-check` skill — it audits skill structure and fails on any dual-harness drift (`scripts/sync_dual_harness.py --check`).
- **Creating plugins/skills:** see [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md). Scaffold via Claude Code `/plugin-dev:create-plugin` or Codex `$plugin-creator`; author skills with `/skill-creator`.

## Maintainer Skills (Claude Code)

Marketplace and catalog tooling from the **`cypherpoet-marketplace-kit`** plugin (enabled in `.claude/settings.json`) — Claude-only, since it manages the Claude marketplace. All run locally (no tokens, no CI):

- **`marketplace-publish`** — publish or remove one plugin on `cypherpoet-toolchest` by opening a PR. Manual-only (`disable-model-invocation`); outward-facing side effect.
- **`marketplace-sync-check`** — read-only audit of local plugins against the published `marketplace.json` and the local [`docs/CATALOG.md`](docs/CATALOG.md).
- **`catalog-refresh`** — regenerate `docs/CATALOG.md`'s table from the manifests (model-invokable; deterministic local script, never commits). Local catalog only.
- **`marketplace-publish-check`** — read-only check of whether the branch diff needs a `marketplace-publish` (plugin added/removed, or `name`/`description`/`homepage` edited). Model-invokable; drives the `marketplace-publish` label at PR time.
- **`skill-fact-check`** — scheduled routine that re-checks skills' time-sensitive facts against primary sources and opens a PR with cited corrections. Volatility tiers in the manifest above.

## Marketplace Surface

- **Claude Code** (`cypherpoet-toolchest`): a PR touches the marketplace surface when it adds/removes a `plugins/<name>/` directory or edits `name`/`description`/`homepage` in a `.claude-plugin/plugin.json` — a version-only bump does **not** count. Run `marketplace-publish-check`; apply the `marketplace-publish` label if it reports a needed publish (a merged label triggers the remote publish PR; a weekly run backstops unlabelled merges). Running `marketplace-publish` by hand is the fallback.
- **Codex** (`.agents/plugins/marketplace.json`): regenerated by `scripts/sync_dual_harness.py` and committed here — no separate publish step. Consumers add it with `codex plugin marketplace add CypherPoet/custom-agent-skills`.
