---
name: marketplace-publish-check
description: Read-only check of whether the current branch changes fields stored in a Claude or Codex marketplace catalog. Use when opening a source PR to decide whether to apply the marketplace-publish label. Version-only and plugin-card-only changes do not count.
---

# marketplace-publish-check

Report whether the current branch changes the marketplace catalog surface. Platform support comes from manifest presence; there is no separate harness classification.

The catalogs store these plugin fields:

- Claude: manifest presence, `name`, `description`, and `homepage`.
- Codex: manifest presence, `name`, and `interface.category`.

Other Codex interface fields live in the plugin manifest itself. Changing `displayName`, descriptions, capabilities, prompts, colors, or assets requires a plugin version bump but not marketplace publication.

## Run the Check

From anywhere in the source repository, run this skill's bundled script:

```shell
python3 scripts/needs_marketplace_publish.py [base-ref]
```

`base-ref` defaults to `main`. The script compares both platform manifests at the merge base and `HEAD`, so it does not attribute later base-branch changes to the feature branch. It uses only the Python standard library and performs no writes or network requests.

- Exit `1`: one or more catalog entries need publication. Apply the `marketplace-publish` label.
- Exit `0`: no catalog-stored field changed.
- Exit `2`: a manifest or Git comparison could not be read safely; fix that error instead of treating it as publication.

The skill is model-invokable because it only reports. The `marketplace-publish` skill remains manual-only.

## Primary Sources

- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) — Claude marketplace schema and behavior.
- [Codex plugin format](https://developers.openai.com/plugins/build/plugins/) — Codex plugin and marketplace packaging.
