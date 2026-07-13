# cypherpoet-marketplace-kit

Maintainer toolkit for running a plugin marketplace with Claude Code and Codex catalogs — publish plugins, audit marketplace and catalog sync, and regenerate the local catalog.

> **Primarily the maintainer's own tooling.** Although published to a public marketplace, this kit exists to maintain the [`custom-agent-skills`](https://github.com/CypherPoet/custom-agent-skills) and `private-custom-agent-skills` repos. The skills are repo-agnostic — they infer the target marketplace from the repo's `origin` (see [`references/marketplaces.md`](references/marketplaces.md)) — so anyone running a Claude Code plugin marketplace can reuse them, but they assume this repo family's conventions (`plugins/`, `docs/CATALOG.md`, a `git-subdir`-sourced marketplace).

## Installation

Install via the marketplace this plugin is published to:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install cypherpoet-marketplace-kit@cypherpoet-toolchest
```

## Skills

| Skill | Description |
|---|---|
| [catalog-refresh](skills/catalog-refresh/SKILL.md) | Regenerate the local `docs/CATALOG.md` plugin table from the manifests — the write-capable counterpart to `marketplace-sync-check`. |
| [marketplace-publish](skills/marketplace-publish/SKILL.md) | Publish one or more plugins to a marketplace — both its Claude and Codex catalog files — by opening a PR on the marketplace repo. |
| [marketplace-publish-check](skills/marketplace-publish-check/SKILL.md) | Read-only check of whether the current branch's changes require a `marketplace-publish` (Claude or Codex catalog surface) — drives the PR label. |
| [marketplace-sync-check](skills/marketplace-sync-check/SKILL.md) | Read-only audit of local `plugins/` against the published marketplace catalogs (Claude + Codex) and the local `docs/CATALOG.md`. |
| [skill-fact-check](skills/skill-fact-check/SKILL.md) | Re-check the repo family's skills' time-sensitive facts (versions, device specs, URLs, API/CLI syntax) against primary sources and open a PR with high-confidence, cited corrections — the engine behind the scheduled fact-check routine. |
