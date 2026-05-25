---
name: plugin-scaffold
description: Scaffold a brand-new Claude Code plugin inside this repo — its manifest, catalog entry, and a first skill — following this repo's conventions. Use whenever the user wants to start, create, or add a new plugin here: "scaffold a plugin", "new plugin for X", "set up a plugin that …", "add a plugin called …". Creates files locally only; it does not commit and does not publish to any marketplace (that's the marketplace-publish skill's job, offered as the follow-up).
---

# plugin-scaffold

Create the files for a new plugin under `plugins/<name>/`, matching this repo's layout, so it's ready to fill in and later publish. **Local only**: no commits, no marketplace changes.

## Repo conventions (match these exactly)

A plugin lives at `plugins/<plugin-name>/`:

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json        # manifest: name, description, author. NO version (commit SHA is the version).
├── CATALOG.md             # per-plugin index of its skills
└── skills/
    └── <skill-name>/
        └── SKILL.md        # YAML frontmatter (name, description) + instructions
```

- Plugin folder name: kebab-case, conventionally `cypherpoet-<theme>` (use a `-kit` suffix for single-topic kits, e.g. `cypherpoet-blender-kit`). Confirm the prevailing convention by glancing at a sibling under `plugins/`.
- Skill folder name: kebab-case, matching the skill's `name:` frontmatter.

## Steps

1. **Gather inputs** (ask in one round if not already clear): plugin name, one-line plugin description, the first skill's name, and a one-line description of what that skill does / when it triggers.
2. **Propose the file plan** — list every file you'll create — and proceed once it looks right.
3. **Create the files:**
   - `plugins/<name>/.claude-plugin/plugin.json` — match a sibling plugin's manifest shape exactly (`$schema`, `name`, `description`, `author`; **no** `version`).
   - `plugins/<name>/skills/<skill>/SKILL.md` — valid YAML frontmatter (`name`, `description`) then a short instruction body. For anything beyond a stub, invoke the `skill-creator` skill to author it soundly rather than hand-rolling.
   - `plugins/<name>/CATALOG.md` — a heading + a one-row skills table linking to the skill's `SKILL.md` (mirror a sibling plugin's `CATALOG.md`).
4. **Update `docs/CATALOG.md`** — add a row for the new plugin to the top-level cross-reference table.
5. **Validate:** `claude plugin validate plugins/<name>` (a missing-`version` warning is expected and intended).
6. **Do not commit.** Tell the user the files are staged in their working tree to review.

## Follow-up

Once the plugin's content is ready and they want it in the marketplace, point them to the **marketplace-publish** skill — that's what opens the catalog PR. Scaffolding alone never publishes anything.
