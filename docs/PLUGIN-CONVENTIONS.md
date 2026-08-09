# Plugin Conventions

This document defines the repository-specific rules for plugins that ship on both Claude Code and Codex. It does not restate general plugin anatomy. Start with Claude Code's [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) or Codex's [`$plugin-creator`](https://github.com/openai/skills/blob/main/skills/.system/plugin-creator/SKILL.md), then apply the rules below.

Use these sources for component types, discovery, hooks, MCP configuration, and other harness-level behavior:

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [`plugin-dev` toolkit](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/README.md) — the `/plugin-dev:create-plugin` workflow plus the seven authoring skills (plugin structure, and skill / command / agent / hook / MCP / settings development)
- [Codex: Build skills](https://learn.chatgpt.com/docs/build-skills) / [Build plugins](https://learn.chatgpt.com/docs/build-plugins) — the Codex plugin and skill format.
- [Codex final-directory submission contract](https://developers.openai.com/plugins/deploy/submission-errors#final-directory-submission) — the authoritative field limits and supported values enforced for the generated Codex interface.
- [Codex `plugin-creator`](https://github.com/openai/skills/blob/main/skills/.system/plugin-creator/SKILL.md) — useful scaffolding and a local preflight helper. It is not the final-directory submission service and does not replace this repository's cross-harness validation.

## Start Here

Plugin metadata has two authored sources and one generated result:

| Path | Edit It? | What It Owns | After an Edit |
|---|---|---|---|
| `plugins/<name>/.claude-plugin/plugin.json` | Yes | Shared package identity, including the name, version, description, author, URLs, license, and keywords. | Bump the version when shipped output changes, then run the sync. |
| [`scripts/plugin-registry.json`](../scripts/plugin-registry.json) | Yes | Harness targeting, Codex presentation metadata, and vendoring relationships. | Bump affected versions, run the sync, and check [Publishing](#publishing). |
| `plugins/<name>/.codex-plugin/plugin.json` or `codex-plugins/<name>/.codex-plugin/plugin.json` | No | The complete Codex manifest generated from the two authored sources. | Edit an authored source instead. |

The generator performs this composition:

```text
Claude manifest + registry entry -> sync_plugins.py -> Codex manifest
```

The generated Codex manifest repeats values from its sources because an installed plugin must be self-contained. This repetition does not create a second source of truth. Do not read metadata back from generated output or edit it by hand.

Most Codex manifests stay inside the authored plugin directory. If Claude-only package metadata would make that directory invalid on Codex, set `"codexProjection": true` on the registry entry. The sync then creates a complete Codex package at `codex-plugins/<name>` and the Codex marketplace points there. The authored package under `plugins/<name>` remains the Claude source of truth.

The generator derives values only when they have the same meaning on both harnesses. It derives `longDescription`, `developerName`, and `websiteURL` from the Claude manifest. Friendly titles, short card copy, categories, capabilities, and starter prompts require author judgment, so they are authored once in the registry.

For skill content, edit the skill in its owner plugin. Then bump every affected plugin version and run the sync. For marketplace listings, use the [publishing flow](#publishing).

## Plugin Folder

- Folder name, conventionally `cypherpoet-<theme>` (kebab-case). Use a `-kit` suffix for single-topic kits (e.g., `cypherpoet-blender-kit`).
- The folder name must equal the manifest `name` field.

## Manifest

Confirm these fields on the scaffolded `plugin.json` (match a sibling under `plugins/*/.claude-plugin/plugin.json`):

- `"$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json"`.
- `"name"` — equals the plugin folder name.
- `"version": "0.1.0"` for new plugins. Both harnesses use this value as the update cache key. Pushing to `main` does not update an existing installation. Use PATCH for fixes, MINOR for additive changes, and MAJOR for breaking changes. Before 1.0, use MINOR by default for a user-visible change.
- `"description"` — one sentence ending in a period, using supported text and at most 1,024 characters. Line feeds are allowed. The per-plugin README and Claude marketplace catalog copy it verbatim. The Codex catalog entry has no description. See [Marketplaces](#marketplaces).
- `"author": { "name": "CypherPoet" }` (no email field).
- `"homepage"` — `https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/<name>`.
- `"repository"` — `https://github.com/CypherPoet/custom-agent-skills.git`.
- `"license": "MIT"`.
- `"keywords"` — 4–6 lowercase kebab-case tags, leading with `"claude-code"` and the plugin's domain (`git`, `blender`, `svg`, …).

## Dual-Harness Plugins

Portable plugins target **both** Claude Code and Codex. Each plugin is self-contained because an installation fetches only that plugin's directory. If a plugin needs a skill from another plugin, it must [vendor](#vendoring) a copy.

If a plugin is useful only on Claude Code, list it under `claude_only_plugins` in the registry and give a reason. Judge the plugin by its purpose, not whether its files parse on Codex. Keep this exception list short.

The shared [`cypherpoet-agent-skills-tooling`](../tooling/) package generates and validates plugins for this repository and the private sibling. Complete the developer setup in the README's [Prerequisites](../README.md#prerequisites) before running it. The public repository installs its local package; the private sibling pins the same package to an exact public commit.

### Manifests

The [source table](#start-here) defines how the manifest is composed. The generator also sets `skills` to `"./skills/"`. It validates all final interfaces before it writes any Codex manifest or projection. One invalid plugin therefore prevents every generated package write instead of leaving a partial update.

A Codex projection is needed only when Claude and Codex cannot use the same package directory. The current case is a manual-only skill, which the two harnesses express differently:

- The authored Claude package keeps `disable-model-invocation: true` in `SKILL.md`.
- The generated Codex package keeps `policy.allow_implicit_invocation: false` in `agents/openai.yaml` and omits the Claude-only field that Codex rejects.

Before it generates that Codex package, the tooling parses the complete Codex policy and confirms the manual-only setting. Each package therefore keeps its harness's own invocation control.

#### Codex Interface Contract

| Field | Contract |
|---|---|
| `displayName` | Required, one line, at most 30 characters, and globally unique after Unicode and whitespace normalization. |
| `shortDescription` | Required, one line, and at most 30 characters. |
| `longDescription` | Derived from `description`; required and at most 4,000 characters. Line feeds are allowed. |
| `developerName` | Derived from `author.name`; required, one line, and at most 80 characters. |
| `category` | Must be `Productivity`, `Creativity`, `Developer Tools`, `Business & Operations`, `Data & Analytics`, `Communication`, `Education & Research`, `Security`, `Finance`, `Healthcare`, `Travel`, `Entertainment`, or `Other`. |
| `capabilities` | 1–20 unique, free-form strings. Each value is one line and at most 120 characters. `Interactive`, `Read`, and `Write` are current choices, not a closed enumeration. |
| `defaultPrompt` | 1–3 unique starter prompts. Each prompt is one line, at most 128 characters, and has no app `@mention`. |
| `websiteURL` | Derived from `homepage`; must be an absolute HTTPS URL with a host, no credentials, supported URL characters, and at most 1,024 characters. The source `homepage` can contain 2,048 characters, but this derived field makes 1,024 the effective repository limit. |

All strings reject surrounding whitespace and unsupported control or invisible characters. Normalized uniqueness checks use NFKC Unicode normalization and folded whitespace. They ignore case for display names and capabilities, but starter-prompt comparison remains case-sensitive. Only `longDescription` permits line feeds.

### Vendoring

When a plugin needs a skill authored elsewhere, copy that skill into the plugin. This copy is a **vendored skill**. Declare the relationship under `vendored_skills` in `plugin-registry.json`, then run the sync.

- The skill is authored **once**, in its owner plugin. Every target is a byte-identical generated copy (minus dev-only `evals/` and `*-workspace/`). Edit the source, never a copy.
- Targets vendor from the **original source**, never from another vendored copy.
- Removing an edge retires the copy on the next sync. The generator deletes a clean copy and refuses to delete a modified copy.
- A byte-identical, unregistered copy is an error. To adopt a retired copy as authored, keep it and change its content.
- A vendored copy ships inside a different plugin, so any link it makes to *another* plugin must be an absolute GitHub URL ([Cross-Plugin Links](#cross-plugin-links)).
- Vendored copies are tiered `never` in the [fact-check manifest](#fact-check-tiering): the routine corrects the authoritative source, and the sync propagates the fix.

A **curated bundle** is a plugin that vendors several skills, such as `git-flow`. Keep a bundle only when all members support the same harnesses. Otherwise, use the standalone plugins.

### Marketplaces

The separate [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace repo carries **two catalog files**, maintained together by the `marketplace-publish` flow (see [Publishing](#publishing)):

- `.claude-plugin/marketplace.json` — the Claude Code catalog. Consumers: `/plugin marketplace add CypherPoet/cypherpoet-toolchest`.
- `.agents/plugins/marketplace.json` — the Codex catalog (`git-subdir` entries pointing at `plugins/<name>` or a generated `codex-plugins/<name>` projection, plus each plugin's `category` from [`scripts/plugin-registry.json`](../scripts/plugin-registry.json)). Consumers: `codex plugin marketplace add CypherPoet/cypherpoet-toolchest`.

The Codex catalog's top-level `name` is `cypherpoet-toolchest`. Its user-facing `interface.displayName` is `CypherPoet Toolchest`. Each plugin title comes from its generated `interface.displayName`.

## Validate

Run both plugin-specific checks:

```shell
claude plugin validate plugins/<plugin-name>
cypherpoet-sync-plugins --check
```

The first command validates the authored Claude manifest. The second validates the generated Codex manifest and reports generation drift without writing files. Resolve every warning or error before you open a PR.

Codex's bundled `plugin-creator` validator is a useful scaffold check, not the final submission service. For a manual-only skill, keep Claude Code's `disable-model-invocation: true`, set Codex's `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, and enable `codexProjection` for its plugin. Run the Codex validator against `codex-plugins/<name>`, not the authored Claude package. This preserves both harness controls and produces validator-clean Codex input.

Use the [final-directory submission contract](https://developers.openai.com/plugins/deploy/submission-errors#final-directory-submission) for Codex interface limits. [`AGENTS.md`](../AGENTS.md) defines the complete repository gate, including tests and `skill-structure-check`.

## Per-Plugin README

Each plugin ships a `README.md` at its root. The name `CATALOG.md` is reserved for the top-level catalog. `/plugin-dev:create-plugin` generates a README template. Add the installation commands and component tables shown below.

````markdown
# <plugin-name>

<one-sentence description, identical to the manifest description, ending in a period>

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install <plugin-name>@cypherpoet-toolchest
```

On Codex, add the same marketplace: `codex plugin marketplace add CypherPoet/cypherpoet-toolchest`, then `codex plugin add <plugin-name>@cypherpoet-toolchest`.

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [<skill-name>](skills/<skill-name>/SKILL.md) | <one-sentence summary>. | <Yes / No> |
````

`Model-Invocable` is `No` for a skill the agent cannot reach on its own — Claude Code's `disable-model-invocation: true`, or Codex's `policy.allow_implicit_invocation: false` in `agents/openai.yaml` — and `Yes` otherwise. A `No` row tells a reader the skill only ever fires when they invoke it by name.

Every plugin here is currently skills-only, so that template is the whole README. A plugin that ships other component types adds a section per type, in a two-column shape:

| Section | First column |
|---|---|
| `## Commands` | `[/<plugin-name>:<command>](commands/<command>.md)` |
| `## Agents` | `[<agent-name>](agents/<agent-name>.md)` |
| `## Hooks` | `` `<EventName>` ``, under a line pointing at `[hooks/hooks.json](hooks/hooks.json)` |
| `## MCP Servers` | `` `<server-name>` `` |

Include only the types the plugin actually ships. Append a row whenever a component is added — the per-plugin README is its primary index, and PR review treats a missing row as a defect.

A plugin's `## Skills` table lists every shipped skill, including [vendored skills](#vendoring). Refresh the table when the sync adds or removes a skill.

## Top-Level Catalog

Every plugin gets a row in [CATALOG.md](CATALOG.md). Use text such as `5 skills`, `1 skill`, or `2 commands, 1 hook` in the `Components` column. Order component types as skills, commands, agents, hooks, and MCP servers. Omit zero values.

Do not edit the catalog by hand. The [`catalog-refresh`](../plugins/cypherpoet-marketplace-kit/skills/catalog-refresh/SKILL.md) skill regenerates it, and `marketplace-sync-check` reports drift.

## Publishing

Plugin updates and marketplace updates are separate operations:

| Change | Required Action |
|---|---|
| Shipped content or a generated manifest value | Bump the plugin version and run the sync. Existing installations use the version as their update key. |
| Codex `displayName`, `shortDescription`, `capabilities`, or `defaultPrompt` | Bump the version and run the sync. No catalog publication is required. |
| Codex `category` | Bump the version, run the sync, and publish the marketplace because the Codex catalog also stores the category. |
| Add or remove `codexProjection` | Bump the version, run the sync, and publish the marketplace because the Codex source path changes. |
| Catalog identity or marketplace presentation | Publish the marketplace. If the same edit changes a plugin manifest, also follow the version rule above. |

A fresh installation always fetches the latest content from `main`, but an existing installation updates only after a version bump.

Marketplace publishing is label-driven. Run `marketplace-publish-check` when you open the source PR. If it reports a required publish, apply the `marketplace-publish` label. Merging the labelled PR updates both marketplace catalog files. The manual-only `marketplace-publish` skill is the fallback. Scaffolding alone never publishes.

## Skill Conventions

Skills use the standard [`SKILL.md`](https://agentskills.io/) format. Author them with Claude Code's [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) or Codex's [`skill-creator`](https://github.com/openai/skills/tree/main/skills/.system/skill-creator).

The repo-local [`skill-structure-check`](../.claude/skills/skill-structure-check/SKILL.md) is the rule contract and remediation guide for repository structure. `*-workspace/` directories under `skills/` are transient evaluation scratch and are not shipped.

### Primary Sources

Every fact-checked skill ends with a `## Primary Sources` section. Use one vendor-primary source per bullet and state what each source controls, such as versions, specifications, or API syntax. Do not use blogs, aggregators, or forums as primary sources.

If no source is available yet, keep this placeholder: `None declared yet — the fact-check routine falls back to vendor-primary sources per claim.` The [`skill-fact-check`](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/SKILL.md) procedure defines how the routine uses this section and any per-fact source markers.

### Fact-Check Tiering

When you create, rename, or remove a skill, update its `<plugin>/<skill>` entry in the [`skill-fact-check` manifest](automated-routines/skill-fact-check-manifest.json). The [tier reference](../plugins/cypherpoet-marketplace-kit/skills/skill-fact-check/references/manifest.md#tiers) defines each tier. List every vendored copy as `never` and keep only the authoritative source researchable.

Each unit must appear exactly once. The strict structure check fails for missing, orphaned, or duplicate entries and for fact-checked skills without [Primary Sources](#primary-sources).

### Cross-Plugin Links

An installation contains only one plugin directory. A relative link into a sibling plugin therefore works in this monorepo but fails after installation.

Use an absolute GitHub URL for every cross-plugin link. Keep links within the same plugin relative. `skill-structure-check` applies this rule to every Markdown file under a plugin.
