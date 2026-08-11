# Custom Agent Skills

[![X](https://img.shields.io/badge/-%40cypher__poet-181717?style=flat&logo=x&logoColor=white&labelColor=000000)](https://x.com/cypher_poet) [![PayPal](https://img.shields.io/badge/-PayPal-181717?style=flat&logo=paypal&logoColor=white&labelColor=003087)](https://www.paypal.com/ncp/payment/L6M553P28YPDY) [![Cash App](https://img.shields.io/badge/-Cash_App-181717?style=flat&logo=cashapp&logoColor=white&labelColor=00C244)](https://cash.app/$CypherPoet) [![Buy Me a Coffee](https://img.shields.io/badge/-Buy_Me_a_Coffee-181717?style=flat&logo=buymeacoffee&logoColor=000000&labelColor=FFDD00)](https://buymeacoffee.com/cypherpoet) [![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## About

A curated collection of reusable AI agent skills, packaged as Claude Code and Codex plugins. Each plugin holds a focused set of related skills — install only the themes you need.

**[Browse the Plugin Catalog &rarr;](docs/CATALOG.md)**

## Prerequisites

Contributors need Node.js and npm. The supported Node.js version is declared in [`package.json`](package.json) and enforced in CI. Install the locked dependencies after checkout:

```shell
npm ci
```

The full test suite also needs Python 3 because some plugins contain Python programs. The test runner detects `python3`, `python`, and the Windows `py -3` launcher; set `PYTHON` only when none of those names selects the correct interpreter.

## Repository Structure

```
.
├── plugins/                  # Self-contained published plugins
├── docs/
│   ├── CATALOG.md            # Cross-plugin index
│   ├── PLUGIN-CONVENTIONS.md # Plugin architecture and contributor workflow
│   └── automated-routines/   # Maintenance routine configuration
├── tooling/
│   ├── src/                  # Authoritative plugin-sync TypeScript
│   ├── test/                 # Package behavior tests
│   └── dist/                 # Committed build for Git-tag consumers
├── vendored-skills.json      # Authoritative skill-copy relationships
├── package.json              # plugin-sync manifest and contributor commands
├── tests-node/               # Repository health tests
├── tests/                    # Tests for plugin-owned Python programs
├── .github/                  # CI (Verify workflow)
├── .agents/skills/           # Codex maintainer skills
└── .claude/                  # Claude Code maintainer config and skills
```

Claude plugin anatomy (component dirs, manifest fields, auto-discovery) follows the [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference). This repo's specific conventions live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).

## Architecture

This repository has two deliverables: the Claude Code and Codex plugins under `plugins/`, and the `@cypherpoet/plugin-sync` Node package. The package is marked `private` to prevent registry publishing and supplies vendoring and shared checks to this repository and its private sibling. The plugins ship through their marketplaces; the Node package ships from immutable `plugin-sync-v*` Git tags.

`package.json` is the Node package boundary: it defines the package metadata, public library export, command-line binaries, and contributor scripts. `tooling/` is that package's implementation directory, not another nested package.

The authoritative TypeScript lives in [`tooling/src/`](tooling/src/). Files ending in `-cli.ts` are thin command adapters; the domain modules hold the behavior, and [`index.ts`](tooling/src/index.ts) defines the public library surface. For example, `npm run sync`, `npm run sync:check`, and the installed `cypherpoet-plugin-sync` binary enter through [`plugin-sync-cli.ts`](tooling/src/plugin-sync-cli.ts), which delegates vendoring to [`sync.ts`](tooling/src/sync.ts) and [`vendored-skills.ts`](tooling/src/vendored-skills.ts). TypeScript compiles into the committed [`tooling/dist/`](tooling/dist/) tree so a repository pinned to a package tag does not need to build it.

See [`tooling/README.md`](tooling/README.md) for the command map, authored-versus-generated file ownership, validation boundaries, and release workflow.

## Contributing

Conventions live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md); [`AGENTS.md`](AGENTS.md) carries the working rules for AI agents.

Marketplace maintenance uses the [`marketplace-kit`](plugins/marketplace-kit/README.md) plugin.

Before opening a PR, run the repository health suite:

```shell
npm test
```

For focused checks, use `npm run validate:claude` for Claude's official strict validator and `npm run sync:check` for vendored-copy consistency.

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.
