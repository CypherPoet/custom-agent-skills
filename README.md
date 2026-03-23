[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/cypherpoet)

# 🛠️ Custom Agent Skills

A curated collection of custom AI agent skills for extending coding assistant capabilities.

## 📖 Overview

This repository stores reusable, portable skills that can be installed into AI coding agents to extend their capabilities for specialized tasks.

Each skill is a self-contained folder with a `SKILL.md` instruction file and any supporting scripts, templates, or resources the skill needs.

## 📂 Repository Structure

```
.
├── skills/              # Individual skill folders
│   └── <skill-name>/
├── docs/                # Skill catalog and documentation
└── README.md
```

## 🚀 Getting Started

### Installing a Skill

Use the [`skills`](https://github.com/vercel-labs/skills) CLI to install skills from this repo:

```bash
# Install a specific skill globally for Claude Code
npx skills add CypherPoet/custom-agent-skills -g -a claude-code -s <skill-name>

# Install a specific skill globally for all detected agents
npx skills add CypherPoet/custom-agent-skills -g -s <skill-name>

# List available skills without installing
npx skills add CypherPoet/custom-agent-skills -l
```

### Creating a New Skill

Use the `/skill-creator` skill within your agent environment to create and iterate on skills.

## 📚 Documentation

Full documentation for each skill lives in the [`docs/`](docs/) directory. See the [documentation index](docs/README.md) for a complete listing.

## 📝 License

Private — personal use only.
