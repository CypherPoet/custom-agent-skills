# Plugin Conventions

This guide covers this repository's authoring choices. Use the platform documentation for manifest fields and component behavior:

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code `plugin-dev` toolkit](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/README.md)
- [Codex plugin format](https://developers.openai.com/plugins/build/plugins/)
- [Codex skill format](https://developers.openai.com/plugins/build/skills/)

The [`@cypherpoet/plugin-sync` README](../tooling/README.md) explains generated vendored copies and validation ownership.

## Authoring Workflow

1. Create `plugins/<name>` and scaffold the configuration for each platform the plugin supports.
2. Author `.claude-plugin/plugin.json` for Claude support and `.codex-plugin/plugin.json` for Codex support.
3. Keep shared skills under `skills/`. For a new Codex-supported skill, author `agents/openai.yaml` with its Codex presentation and policy metadata.
4. Add a relationship to [`vendored-skills.json`](../vendored-skills.json) only when another plugin must ship a generated copy of a skill.
5. Update the plugin README and repository catalog when applicable.
6. Run `npm test` before opening a pull request.

Both platform manifests are authored files. Edit the manifest belonging to the platform whose behavior or presentation you want to change. Only vendored skill targets are generated.

## Platform Support

Manifest presence declares support:

| Files Present | Supported Platforms |
|---|---|
| `.claude-plugin/plugin.json` | Claude Code |
| `.codex-plugin/plugin.json` | Codex |
| Both | Claude Code and Codex |

A plugin needs at least one platform manifest. The manifest `name` must match the plugin directory. A plugin can add another platform later by adding that platform's configuration; no central classification is required.

Harness-specific metadata can coexist in the same plugin. Claude-specific skill fields belong in `SKILL.md`, while Codex-specific skill presentation and invocation policy belong in `agents/openai.yaml`.

## Versions and Metadata

Use `0.1.0` for a new plugin. Use PATCH for fixes, MINOR for additive changes, and MAJOR for breaking changes. Before 1.0, use MINOR by default for user-visible changes.

All manifests for one plugin share a release version. When shipped content or either platform manifest changes, bump every manifest that plugin supports to the same new version. A merge to `main` does not update an existing installation without that bump.

Descriptions and other presentation fields may differ because each platform owns its own manifest contract. Repository metadata uses these shared values:

- Author name is `CypherPoet`.
- Homepages point to the plugin under this repository's `main` branch.
- Repository URL is `https://github.com/CypherPoet/custom-agent-skills.git`.
- License is `MIT`.

Follow the linked platform documentation rather than copying platform field limits into this guide.

## Vendoring

Each installed plugin is self-contained. If it ships a skill owned elsewhere, add the authoritative `source` and generated `targets` to [`vendored-skills.json`](../vendored-skills.json), then run `npm run sync`.

- Edit the source skill, never a generated target.
- Vendor from the original source, not another generated copy.
- The sync removes a retired clean copy and refuses to remove a modified copy.
- An undeclared byte-identical copy is an error.
- Use absolute GitHub URLs for links that leave the installed plugin.
- Put vendored copies in the fact-check tier `never`; research and correct their source.

A curated bundle, such as `git-flow`, is an ordinary plugin that vendors several skills.

## Validation

Install the locked dependencies after checkout:

```shell
npm ci
```

Use focused checks while authoring:

```shell
npm run validate:claude
npm run sync:check
npm run structure:check
npm run versions:check
```

`validate:claude` runs Claude Code's pinned official validator in strict mode. `sync:check` checks only vendored copies. Repository health checks manifest discovery, names, versions, shared-version consistency, and Codex's 64-character combined `plugin-name:skill-name` limit. The combined identity uses the skill frontmatter `name`; Claude-only plugins are outside that Codex limit.

Codex does not currently expose a stable repository validation command. The optional local `plugin-creator` scaffold preflight can provide packaging feedback during release review, but it is non-authoritative, does not define Codex's submission contract, and is not a repository gate. Do not duplicate the platform schema in repository tooling.

Before a pull request, run the combined gate:

```shell
npm test
```

## Marketplace Publishing

The [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) repository has one catalog per platform. Catalog membership is deliberate and independent of source support.

| Change | Required Action |
|---|---|
| Shipped content or any platform manifest field | Bump every supported manifest to one shared version. |
| Claude `name`, `description`, or `homepage` | Publish the Claude catalog entry. |
| Add or remove a Claude manifest | Add or remove the Claude catalog entry. |
| Codex `name` or `interface.category` | Publish the Codex catalog entry. |
| Add or remove a Codex manifest | Add or remove the Codex catalog entry. |
| Other Codex interface metadata | Bump the shared version; no catalog publication is needed. |

Run `marketplace-publish-check` when opening a source pull request. Apply the `marketplace-publish` label only when it requests publication. The manual-only `marketplace-publish` skill is the fallback.

## README, Catalog, and Skills

Each plugin has a `README.md`; `CATALOG.md` is reserved for the repository-wide catalog. Include installation commands for every supported platform and list every shipped component, including vendored skills.

Do not hand-edit [`CATALOG.md`](CATALOG.md). The `catalog-refresh` skill regenerates it, and `marketplace-sync-check` reports drift.

Skills use the shared [`SKILL.md`](https://agentskills.io/) format. The repository's [`skill-structure-check`](../.claude/skills/skill-structure-check/SKILL.md) documents structure and remediation.

Every fact-checked skill ends with a `## Primary Sources` section. When a skill is created, renamed, or removed, update its `<plugin>/<skill>` entry in the [fact-check manifest](automated-routines/skill-fact-check-manifest.json). Each unit appears exactly once. Development-only `*-workspace/` and `evals/` directories do not ship.
