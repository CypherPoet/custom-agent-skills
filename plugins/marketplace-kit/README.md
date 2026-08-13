# marketplace-kit

Maintainer toolkit for running a plugin marketplace with Claude Code and Codex catalogs — publish plugins, audit marketplace and catalog sync, and regenerate the local catalog.

> **Primarily the maintainer's own tooling.** Although published to a public marketplace, this kit exists to maintain the [`custom-agent-skills`](https://github.com/CypherPoet/custom-agent-skills) and `private-custom-agent-skills` repos. The skills are repo-agnostic — they infer the target marketplace from the repo's `origin` (see [`references/marketplaces.md`](references/marketplaces.md)) — so anyone running a plugin marketplace with Claude Code (and optionally Codex) catalogs can reuse them, but they assume this repo family's conventions (`plugins/`, `docs/CATALOG.md`, a `git-subdir`-sourced marketplace).

## Installation

Install via the marketplace this plugin is published to:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install marketplace-kit@cypherpoet-toolchest
```

On Codex, add the same marketplace: `codex plugin marketplace add CypherPoet/cypherpoet-toolchest`, then `codex plugin add marketplace-kit@cypherpoet-toolchest`.

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [catalog-refresh](skills/catalog-refresh/SKILL.md) | Regenerate the local `docs/CATALOG.md` plugin table from the manifests — the write-capable counterpart to `marketplace-sync-check`. | Yes |
| [marketplace-publish](skills/marketplace-publish/SKILL.md) | Publish one or more plugins to a marketplace — both its Claude and Codex catalog files — by opening a PR on the marketplace repo. | No |
| [marketplace-publish-check](skills/marketplace-publish-check/SKILL.md) | Read-only check of whether the current branch's changes require a `marketplace-publish` (Claude or Codex catalog surface) — drives the PR label. | Yes |
| [marketplace-sync-check](skills/marketplace-sync-check/SKILL.md) | Read-only audit of local `plugins/` against the published marketplace catalogs (Claude + Codex) and the local `docs/CATALOG.md`. | Yes |
| [keeping-skills-current](skills/keeping-skills-current/SKILL.md) | Configure and run source-bounded reviews that report relevant corrections and improvements for project-owned skills. | No |
