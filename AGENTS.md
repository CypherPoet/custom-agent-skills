# AGENTS.md

The definitive project rules for this repo. Read by **Codex** directly and by **Claude Code** through the `@AGENTS.md` import in [`CLAUDE.md`](CLAUDE.md). Keep everything here harness-neutral; where a detail differs between harnesses, state it for **both**.

## Project

Public collection of reusable AI agent skills, packaged as **both** Claude Code and Codex plugins and distributed through each harness's plugin marketplace. Skills use the shared agent-skills [`SKILL.md`](https://agentskills.io/) format, so a skill body runs on either harness unchanged.

## Map

- [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) — **source of truth** for how plugins and skills are built here: dual-harness manifests, vendoring, the marketplace catalogs, skill conventions.
- [`docs/CATALOG.md`](docs/CATALOG.md) — generated cross-plugin index (one row per plugin).
- [`scripts/plugin-registry.json`](scripts/plugin-registry.json) + [`scripts/sync_plugins.py`](scripts/sync_plugins.py) — the plugin registry (harness targeting + skill-sharing edges) and the generator for every derived artifact (vendored skills, `.codex-plugin/` manifests); the config's per-plugin `category` also feeds the Codex catalog entries at publish time.
- [`docs/automated-routines/skill-fact-check-manifest.json`](docs/automated-routines/skill-fact-check-manifest.json) — per-skill fact-check volatility tiers.

## Architecture

- `plugins/<plugin-name>/` — one themed plugin, **self-contained**: install pulls only this directory (Claude Code `git-subdir` sparse-clone; Codex marketplace fetch), so a plugin ships every skill it needs. A dual-harness plugin carries two manifests — `.claude-plugin/plugin.json` (hand-authored, the source of truth) and `.codex-plugin/plugin.json` (**generated**: the Claude manifest mirrored, plus `"skills": "./skills/"`) — over a shared `skills/<name>/SKILL.md`; a Claude-only plugin carries just the Claude manifest.
- **Composition is by vendoring, not dependencies.** A skill shared across plugins is copied into each plugin that ships it — no plugin references another (neither harness can resolve a cross-plugin reference at install). `scripts/sync_plugins.py` owns every vendored copy and every `.codex-plugin/` manifest. Rationale and the full workflow live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).
- **One marketplace repo, two catalogs.** The separate [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) repo carries the Claude catalog (`.claude-plugin/marketplace.json`) and the Codex catalog (`.agents/plugins/marketplace.json`), both maintained by the `marketplace-publish` flow — consumers add the **same repo** on either harness. A few Claude-Code-specific plugins ship to Claude only — the split, with reasons, is in [`scripts/plugin-registry.json`](scripts/plugin-registry.json).

## Working In This Repo

- **After editing a vendored skill's source or any `.claude-plugin/plugin.json`, run `python3 scripts/sync_plugins.py`** to regenerate the vendored copies and Codex manifests. **Never hand-edit a generated file** — any `.codex-plugin/plugin.json` or vendored skill copy. Edit the source and re-sync.
- **Bump a plugin's `version`** whenever a content change should reach installed users — pushing to `main` alone won't (version is each harness's update cache key). Keep the `.codex-plugin` version in step by re-running the sync after the bump.
- **Before a PR that touches skills**, run the repo-local `skill-structure-check` skill — it audits skill structure and fails on any plugin-sync drift (`scripts/sync_plugins.py --check`).
- **Before any PR**, run the repo health suite: `python3 -m unittest discover -s tests`. The `Verify` workflow (`.github/workflows/verify.yml`) runs the same suite on every PR and push to `main`; it runs the structure checker in `--strict` mode, so warnings and advisories fail CI there.
- **Creating plugins/skills:** see [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md). Scaffold via Claude Code `/plugin-dev:create-plugin` or Codex `$plugin-creator`; author skills with `/skill-creator`.

## Maintainer Skills (Claude Code)

Marketplace and catalog tooling from the **`cypherpoet-marketplace-kit`** plugin (enabled in `.claude/settings.json`) — the kit runs on Claude Code, and the catalogs it maintains serve both harnesses. All run locally (no tokens, no CI):

- **`marketplace-publish`** — publish or remove one plugin on `cypherpoet-toolchest` (both its Claude and Codex catalogs) by opening a PR. Manual-only (`disable-model-invocation`); outward-facing side effect.
- **`marketplace-sync-check`** — read-only audit of local plugins against both published catalogs and the local [`docs/CATALOG.md`](docs/CATALOG.md).
- **`catalog-refresh`** — regenerate `docs/CATALOG.md`'s table from the manifests (model-invokable; deterministic local script, never commits). Local catalog only.
- **`marketplace-publish-check`** — read-only check of whether the branch diff needs a `marketplace-publish` (plugin added/removed, `name`/`description`/`homepage` edited, or dual-harness classification/`category` changed). Model-invokable; drives the `marketplace-publish` label at PR time.
- **`skill-fact-check`** — scheduled routine that re-checks skills' time-sensitive facts against primary sources and opens a PR with cited corrections. Volatility tiers in the manifest above.

## Marketplace Surface

Both catalogs live in the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace repo; consumers add it with `/plugin marketplace add CypherPoet/cypherpoet-toolchest` (Claude Code) or `codex plugin marketplace add CypherPoet/cypherpoet-toolchest` (Codex).

A PR here touches the **marketplace catalog surface** when it adds/removes a `plugins/<name>/` directory, edits `name`/`description`/`homepage` in a `.claude-plugin/plugin.json` (the Claude catalog fields), or changes a plugin's dual-harness classification/`category` in `scripts/plugin-registry.json` (the Codex catalog fields) — a version-only bump does **not** count. Run `marketplace-publish-check`; apply the `marketplace-publish` label if it reports a needed publish (a merged label triggers the remote publish PR; a weekly run backstops unlabelled merges by reconciling both catalog files). Running `marketplace-publish` by hand is the fallback.
