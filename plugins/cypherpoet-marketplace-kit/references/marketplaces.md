# Marketplace mappings registry

Known `source repo → marketplace` mappings for the skills in this kit. `marketplace-sync-check` and `marketplace-publish` resolve the target marketplace by matching the current repo's `origin` (`owner/repo`) against the **Source repo** column.

| Source repo (`origin`) | Marketplace repo (clone target) | Marketplace name (`@name`) |
|---|---|---|
| `CypherPoet/custom-agent-skills` | `CypherPoet/cypherpoet-toolchest` | `cypherpoet-toolchest` |
| `CypherPoet/private-custom-agent-skills` | `CypherPoet/cypherpoet-toolchest-private` | `cypherpoet-toolchest-private` |

**Adding a repo:** append a row. No skill edits needed — the lookup is data-driven.

**No matching row:** the skill asks which marketplace to target rather than guessing. The marketplace name usually equals the marketplace repo's short name, but the `name` field in the marketplace's `marketplace.json` is authoritative.
