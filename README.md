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
│       ├── SKILL.md     # Main instruction file (required)
│       ├── scripts/     # Helper scripts (optional)
│       ├── templates/   # Reference templates (optional)
│       └── resources/   # Additional assets (optional)
├── docs/                # Detailed skill documentation
│   └── README.md        # Documentation index
└── README.md
```

## 🚀 Getting Started

### Installing a Skill

To install a skill from this repo into your agent environment, copy the skill folder to your agent's skills directory. For example:

```bash
# Claude Code
cp -r skills/<skill-name> ~/.claude/skills/

# Gemini CLI / Antigravity
cp -r skills/<skill-name> ~/.gemini/antigravity/skills/
```

### Creating a New Skill

Use the `/skill-creator` skill within your agent environment to create and iterate on skills.

## 📚 Documentation

Full documentation for each skill lives in the [`docs/`](docs/) directory. See the [documentation index](docs/README.md) for a complete listing.

## 📝 License

Private — personal use only.
