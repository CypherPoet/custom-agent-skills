# Custom Agent Skills

[![X](https://img.shields.io/badge/-%40cypher__poet-181717?style=flat&logo=x&logoColor=white&labelColor=000000)](https://x.com/cypher_poet) [![PayPal](https://img.shields.io/badge/-PayPal-181717?style=flat&logo=paypal&logoColor=white&labelColor=003087)](https://www.paypal.com/ncp/payment/L6M553P28YPDY) [![Cash App](https://img.shields.io/badge/-Cash_App-181717?style=flat&logo=cashapp&logoColor=white&labelColor=00C244)](https://cash.app/$CypherPoet) [![Buy Me a Coffee](https://img.shields.io/badge/-Buy_Me_a_Coffee-181717?style=flat&logo=buymeacoffee&logoColor=000000&labelColor=FFDD00)](https://buymeacoffee.com/cypherpoet) [![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## About

A curated collection of reusable AI agent skills, packaged as Claude Code and Codex plugins. Each plugin holds a focused set of related skills — install only the themes you need.

**[Browse the Plugin Catalog &rarr;](docs/CATALOG.md)**

## Installation

This repo publishes its plugins for both **Claude Code** and **Codex** via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace — one repo carrying both harness catalogs.

**Claude Code:**

```shell
# Subscribe to the marketplace once
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install whichever plugins you want
/plugin install cypherpoet-git-flow@cypherpoet-toolchest
/plugin install cypherpoet-blender-kit@cypherpoet-toolchest
# ...etc
```

**Codex** (same marketplace repo — it carries both harness catalogs):

```shell
codex plugin marketplace add CypherPoet/cypherpoet-toolchest
codex plugin add cypherpoet-git-flow@cypherpoet-toolchest
```


## Repository Structure

```
.
├── plugins/                  # Self-contained published plugins
├── docs/
│   ├── CATALOG.md            # Cross-plugin index
│   ├── PLUGIN-CONVENTIONS.md # Plugin architecture and contributor workflow
│   └── automated-routines/   # Maintenance routine configuration
├── scripts/                  # Plugin registry and sync generator
├── tests/                    # Repository health suite
├── .github/                  # CI (Verify workflow)
├── .agents/skills/           # Codex maintainer skills
└── .claude/                  # Claude Code maintainer config and skills
```

Claude plugin anatomy (component dirs, manifest fields, auto-discovery) follows the [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference). This repo's specific conventions live in [`docs/PLUGIN-CONVENTIONS.md`](docs/PLUGIN-CONVENTIONS.md).

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.
