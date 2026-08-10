# Plugin Conventions

This guide covers the choices made by this repository. Use the platform documentation for general plugin fields and component behavior:

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code `plugin-dev` toolkit](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/README.md)
- [Codex: Build skills](https://learn.chatgpt.com/docs/build-skills) and [Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Codex final-directory submission rules](https://developers.openai.com/plugins/deploy/submission-errors#final-directory-submission)

The [`@cypherpoet/plugin-sync` README](../tooling/README.md) explains generation and validation ownership. This document stays focused on authoring.

## Authoring Workflow

1. Scaffold with the authoring tools available in Claude Code or Codex.
2. Put the plugin under `plugins/<name>` and author its Claude manifest and skills there.
3. Classify the plugin and add its Codex card metadata in [`plugin-registry.json`](../plugin-registry.json).
4. Add any skill-sharing relationships under `vendored_skills` in the registry.
5. Run `npm run sync` to generate the Codex manifest and vendored copies.
6. Update the plugin README and generated top-level catalog when applicable.
7. Run `npm test` before opening a pull request.

Do not edit a generated `.codex-plugin/plugin.json` or a vendored skill copy. Change its authored source and run the sync.

## Metadata Sources

Plugin metadata has two authored sources:

| Authored Path | What It Owns |
|---|---|
| `plugins/<name>/.claude-plugin/plugin.json` | Shared name, version, description, author, homepage, repository, license, and keywords. |
| `plugin-registry.json` | Harness classification, Codex display name, short description, category, capabilities, starter prompts, and vendoring. |

The generated Codex manifest combines them. Its repeated values make an installed plugin self-contained; they are not another source of truth.

Friendly card metadata belongs in the registry because it requires author judgment. The generator derives `longDescription`, `developerName`, and `websiteURL` from the shared Claude manifest because those values have the same meaning on both harnesses.

## Plugin Manifest

The plugin folder name must equal the manifest `name`. Use a `cypherpoet-<theme>` name and reserve `-kit` for a focused toolkit.

Author these Claude manifest values consistently with sibling plugins:

- `"$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json"`
- `"version": "0.1.0"` for a new plugin
- A one-sentence `description` ending in a period
- `"author": { "name": "CypherPoet" }`
- `"homepage": "https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/<name>"`
- `"repository": "https://github.com/CypherPoet/custom-agent-skills.git"`
- `"license": "MIT"`
- Four to six lowercase keywords, beginning with `claude-code` and the plugin domain

Both harnesses use `version` as an update key. Use PATCH for fixes, MINOR for additive changes, and MAJOR for breaking changes. Before 1.0, use MINOR by default for a user-visible change. A merge to `main` does not update an existing installation without a version bump.

## Harness Support

Portable plugins belong under `dual_harness_plugins`. A normal dual-harness plugin uses one directory: Claude Code reads the authored `.claude-plugin/plugin.json`, Codex reads the generated `.codex-plugin/plugin.json`, and both read the same skills.

Use `claude_only_plugins` only when the plugin's purpose is specific to Claude Code. Record a reason and judge support by what the plugin does, not whether another harness can parse its files.

Harness-specific skill metadata can coexist in the shared package. Keep Claude Code fields in `SKILL.md` and Codex fields in `agents/openai.yaml`; the sync does not reinterpret or remove either harness's fields.

## Codex Interface Metadata

Author `displayName`, `shortDescription`, `capabilities`, and `defaultPrompt` under the registry entry's `interface` object. Author `category` beside it.

The generator checks Codex's documented submission rules and these additional repository choices:

- Every plugin has at least one capability and one starter prompt.
- Capabilities and starter prompts are unique after normalization.
- Display names are unique across the repository after normalization.
- The shared homepage is HTTPS and becomes the Codex website URL.

See the [official Codex submission rules](https://developers.openai.com/plugins/deploy/submission-errors#final-directory-submission) for platform limits. See [Validation Ownership](../tooling/README.md#validation-ownership) for which checker owns each rule.

## Vendoring

Each installed plugin is self-contained. If one plugin ships a skill owned by another, declare a `source` and its `targets` under `vendored_skills`, then run `npm run sync`.

- Edit the source skill, never a generated target.
- Vendor from the original source, not another vendored copy.
- The sync removes a retired clean copy and refuses to remove a modified copy.
- An undeclared byte-identical copy is an error.
- Use absolute GitHub URLs for links that leave the installed plugin.
- Put vendored copies in the fact-check tier `never`; research and correct their source.

A curated bundle, such as `git-flow`, is an ordinary plugin that vendors several skills. Keep a bundle only when its members support the same harnesses.

## Validation

Install the locked dependencies once after checkout:

```shell
npm ci
```

Use these focused commands while authoring:

```shell
npm run validate:claude
npm run sync:check
npm run structure:check
npm run versions:check
```

`validate:claude` runs the pinned official Claude validator in strict mode against every authored plugin. `sync:check` checks generated Codex manifests and repository consistency; it is not a complete platform validator. Codex's bundled helper is not a repository gate; the local submission preflight follows the published contract.

Before a pull request, run the combined gate:

```shell
npm test
```

## Per-Plugin README

Each plugin has a `README.md`; `CATALOG.md` is reserved for the repository-wide catalog. Copy the manifest description and include installation commands for both harnesses.

List every shipped skill, including vendored skills:

```markdown
## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [<skill-name>](skills/<skill-name>/SKILL.md) | <one-sentence summary>. | <Yes / No> |
```

`Model-Invocable` is `No` when Claude Code has `disable-model-invocation: true` or Codex has `policy.allow_implicit_invocation: false`. Add similar component tables only for commands, agents, hooks, or MCP servers the plugin actually ships.

## Marketplace Publishing

The [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) repository has one catalog per harness. Both catalogs point to the authored plugin directory; the Codex catalog also stores the registry category.

Use this decision table:

| Change | Required Action |
|---|---|
| Shipped content or generated manifest value | Bump the plugin version and run the sync. |
| Codex display name, short description, capabilities, or starter prompts | Bump the version and run the sync. No catalog publication is needed. |
| Codex category | Bump the version, run the sync, and publish the marketplace. |
| Catalog identity or marketplace presentation | Publish the marketplace; also bump a plugin when its manifest changed. |

Run `marketplace-publish-check` when opening a source pull request. Apply the `marketplace-publish` label only when it requests publication. The manual-only `marketplace-publish` skill is the fallback.

## Catalog and Skill Maintenance

Do not hand-edit [`CATALOG.md`](CATALOG.md). The `catalog-refresh` skill regenerates it, and `marketplace-sync-check` reports drift.

Skills use the shared [`SKILL.md`](https://agentskills.io/) format. The repository's [`skill-structure-check`](../.claude/skills/skill-structure-check/SKILL.md) documents structure and remediation.

Every fact-checked skill ends with a `## Primary Sources` section. Use vendor-primary sources and state what each source controls. If none is available yet, use: `None declared yet — the fact-check routine falls back to vendor-primary sources per claim.`

When a skill is created, renamed, or removed, update its `<plugin>/<skill>` entry in the [fact-check manifest](automated-routines/skill-fact-check-manifest.json). Each unit appears exactly once. `*-workspace/` and `evals/` are development-only and do not ship.

Keep links inside one plugin relative. Use an absolute GitHub URL for every cross-plugin link because an installation contains only one plugin directory.
