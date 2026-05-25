# Custom Agent Skills

[![X](https://img.shields.io/badge/-%40cypher__poet-181717?style=flat&logo=x&logoColor=white&labelColor=000000)](https://x.com/cypher_poet) [![PayPal](https://img.shields.io/badge/-PayPal-181717?style=flat&logo=paypal&logoColor=white&labelColor=003087)](https://www.paypal.com/ncp/payment/L6M553P28YPDY) [![Cash App](https://img.shields.io/badge/-Cash_App-181717?style=flat&logo=cashapp&logoColor=white&labelColor=00C244)](https://cash.app/$CypherPoet) [![Buy Me a Coffee](https://img.shields.io/badge/-Buy_Me_a_Coffee-181717?style=flat&logo=buymeacoffee&logoColor=000000&labelColor=FFDD00)](https://buymeacoffee.com/cypherpoet) [![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## About

A curated collection of reusable AI agent skills, packaged as Claude Code plugins. Each plugin holds a focused set of related skills — install only the themes you need.

**[Browse the Plugin Catalog &rarr;](docs/CATALOG.md)**

## Installation

This repo publishes its plugins via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) Claude Code marketplace.

```shell
# Subscribe to the marketplace once
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install whichever plugins you want
/plugin install cypherpoet-agent-tooling@cypherpoet-toolchest
/plugin install cypherpoet-git-flow@cypherpoet-toolchest
# ...etc
```

Each commit to `main` becomes a new version — Claude Code picks up updates automatically on `/plugin marketplace update` or background refresh.

## Themed Plugins

| Plugin | Description |
|---|---|
| [cypherpoet-agent-tooling](plugins/cypherpoet-agent-tooling/CATALOG.md) | Agent tooling for Claude Code workflow, memory, and docs |
| [cypherpoet-blender-kit](plugins/cypherpoet-blender-kit/CATALOG.md) | Blender 3D modeling and MCP integration |
| [cypherpoet-expo-kit](plugins/cypherpoet-expo-kit/CATALOG.md) | Expo / React Native prototyping |
| [cypherpoet-git-flow](plugins/cypherpoet-git-flow/CATALOG.md) | Git commit and changelog hygiene |
| [cypherpoet-mobile-dev](plugins/cypherpoet-mobile-dev/CATALOG.md) | iOS App Store publishing best practices |
| [cypherpoet-svg-tools](plugins/cypherpoet-svg-tools/CATALOG.md) | SVG optimization and cleanup |
| [cypherpoet-threejs-kit](plugins/cypherpoet-threejs-kit/CATALOG.md) | Three.js / WebGPU / WebGL tooling |

## Repository Structure

```
.
├── plugins/                # Themed Claude Code plugins
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json # Plugin manifest
│       ├── CATALOG.md      # Per-plugin skill catalog
│       └── skills/
│           └── <skill-name>/
│               ├── SKILL.md        # Skill instructions (required)
│               ├── assets/         # Output templates (optional)
│               ├── references/     # Supporting documentation (optional)
│               └── scripts/        # Helper scripts (optional)
├── docs/CATALOG.md         # Top-level cross-reference index
└── README.md
```

## Creating a New Skill

Use the `/skill-creator` skill within Claude Code to draft a new skill. After it's ready, place the skill folder under the appropriate `plugins/<plugin-name>/skills/` directory (or open a discussion if a new plugin is warranted) and update the plugin's `CATALOG.md`.

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.
