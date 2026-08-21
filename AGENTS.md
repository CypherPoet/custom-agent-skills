Harness-neutral by default. Where a detail differs between harnesses, state it for **both**.

## Project

Public collection of reusable AI agent skills, packaged as **both** Claude Code and Codex plugins and distributed through each harness's plugin marketplace. Skills use the shared agent-skills [`SKILL.md`](https://agentskills.io/) format.

Composition is by **vendoring, not dependencies**: neither harness resolves a reference to a skill in another plugin, so a shared skill is physically copied into each plugin that ships it.

## Map

- [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) — **source of truth** for the plugin authoring workflow and repository choices.
- [`vendored-skills.json`](vendored-skills.json) — authoritative sources and generated targets for shared skills.
- [`tooling/README.md`](tooling/README.md) — vendoring, manifest checks, and validation ownership for the shared [`@cypherpoet/plugin-sync`](package.json) package.
- [`docs/CATALOG.md`](docs/CATALOG.md) — generated cross-plugin index.
- [`.keeping-skills-current/manifest.json`](.keeping-skills-current/manifest.json) — project-local source-review configuration.
- [`.keeping-skills-current/state.json`](.keeping-skills-current/state.json) — machine-managed source-review state.

## Working In This Repo

- Platform manifests are authored files. Edit `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json` directly for the platform it configures.
- Run `npm run sync` after editing [`vendored-skills.json`](vendored-skills.json) or the source of a vendored skill. Never hand-edit a vendored target.
- Run `npm run validate:claude` for the pinned official strict Claude validation without the rest of the repository suite.
- **Bump every supported manifest to the same version whenever a plugin's shipped content changes** — merging to `main` alone will not update existing installations.
- Run `npm run structure:check` before a PR that touches skills.
- Run `npm test` before any PR; [`.github/workflows/verify.yml`](.github/workflows/verify.yml) runs the same suite on every PR and push to `main`.
- Run `marketplace-publish-check` when opening a PR, and apply the `marketplace-publish` label if it reports a needed publish. A merged label publishes automatically — the manual-only `marketplace-publish` skill is the fallback, and never self-triggers.
- Scaffold with whatever your harness offers — no scaffolder emits a repo-conformant plugin on its own. Finish against [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).
- [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md) holds mechanisms and rationale; this file holds the imperatives. Neither restates the other.
