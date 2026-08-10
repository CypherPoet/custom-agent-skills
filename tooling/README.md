# `@cypherpoet/plugin-sync`

`@cypherpoet/plugin-sync` generates Codex plugin manifests and checks repository consistency for the public and private CypherPoet skill repositories. It is not a replacement for Claude Code's or Codex's platform validation.

## Inputs and Outputs

| Path | Role |
|---|---|
| `plugins/<name>/.claude-plugin/plugin.json` | Authored package identity shared by both harnesses. |
| `plugin-registry.json` | Authored harness classification, Codex card metadata, and vendoring relationships. |
| `plugins/<name>/skills/` | Authored skill content, except for copies declared as vendored. |
| `plugins/<name>/.codex-plugin/plugin.json` | Generated Codex manifest for the shared package. |
| Declared vendoring targets | Generated copies of their source skill. |

The generator composes the Codex manifest from the Claude manifest and registry entry. It validates all planned output before it writes generated manifests or vendored copies. A bad plugin therefore cannot leave a partial generation update.

Run it through the repository commands:

```shell
npm run sync
npm run sync:check
```

`sync` writes generated output. `sync:check` reports drift without writing.

## Validation Ownership

The checks have deliberately separate jobs:

| Check | Owner | What It Proves |
|---|---|---|
| `npm run validate:claude` | Claude Code's pinned `claude plugin validate --strict` command | Every authored Claude plugin satisfies the installed Claude validator. |
| Codex submission preflight in this package | Codex's documented final-directory rules | Generated interface values satisfy the currently documented local checks before submission. |
| Repository policy checks in this package | CypherPoet | Authored metadata follows this repository's additional choices, including populated capabilities and prompts, HTTPS homepage composition, and cross-plugin display-name uniqueness. |
| `npm run sync:check` | `@cypherpoet/plugin-sync` | Generated manifests and vendored copies match their authored sources. |
| `npm run structure:check` | CypherPoet | Skill structure, links, reference indexes, and fact-check classifications follow repository policy. |
| `npm run versions:check` | CypherPoet | Shipped plugin changes carry a new version. |

`npm test` runs these repository checks and the official strict Claude validator. Codex does not currently provide a stable local plugin-validation command. The bundled `plugin-creator` helper is not vendored into this package or treated as a repository gate; this preflight mirrors only the published submission contract.

The implementation keeps Codex's [final-directory submission rules](https://developers.openai.com/plugins/deploy/submission-errors#final-directory-submission) separate from CypherPoet policy so an upstream platform change is not mistaken for a local authoring choice.

## Shared Plugin Directory

Both harnesses install the same plugin directory. Claude Code reads `.claude-plugin/plugin.json`, Codex reads the generated `.codex-plugin/plugin.json`, and both use the same `skills/` directory.

Harness-specific metadata remains with the shared skill. The generator does not parse or rewrite `SKILL.md` frontmatter, so a Claude field such as `disable-model-invocation` remains unchanged. Codex-specific presentation and invocation policy belong in `agents/openai.yaml`. Each harness interprets its own fields and ignores metadata it does not own.

## Package Structure

| Module | Responsibility |
|---|---|
| `src/sync.ts` | Repository orchestration and all-or-nothing application of a prepared plan. |
| `src/codex-manifest.ts` | Claude manifest parsing and Codex manifest composition. |
| `src/vendored-skills.ts` | Vendored skill synchronization and drift detection. |
| `src/codex-submission-preflight.ts` | Codex submission checks and separately named CypherPoet policy checks. |
| `src/claude-plugin-validation.ts` | Invocation of Claude Code's official strict validator for authored plugins. |

TypeScript is the authored implementation. Compiled files under `dist/` are committed so the private repository can install an exact public Git commit without building this package.

## Development

After changing the package source, run:

```shell
npm run build
npm test
```

`npm run build:check` verifies that committed JavaScript and declarations match the TypeScript source. Keep the package at `0.1.0` until its first release is intentionally tagged.
