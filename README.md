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
├── tooling/                  # TypeScript source, compiled package, and package tests
├── package.json              # Contributor commands and dependency contract
├── scripts/                  # Plugin registry
├── tests-node/               # Repository health tests
├── tests/                    # Tests for plugin-owned Python programs
├── .github/                  # CI (Verify workflow)
├── .agents/skills/           # Codex maintainer skills
└── .claude/                  # Claude Code maintainer config and skills
```

Claude plugin anatomy (component dirs, manifest fields, auto-discovery) follows the [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference). This repo's specific conventions live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).

## Contributing

Conventions live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md); [`AGENTS.md`](AGENTS.md) carries the working rules for AI agents.

Marketplace maintenance uses the [`cypherpoet-marketplace-kit`](plugins/cypherpoet-marketplace-kit/README.md) plugin.

Before opening a PR, run the repository health suite:

```shell
npm test
```

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.
