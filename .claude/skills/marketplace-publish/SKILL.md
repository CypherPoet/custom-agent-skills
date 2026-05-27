---
name: marketplace-publish
description: Publish one or more plugins from this source repo to a Claude Code marketplace by opening a pull request on the marketplace repo. Use whenever the user wants to add a new plugin to the marketplace, register/publish a plugin, push a plugin (or several) to the catalog, or update an already-listed plugin's catalog entry (its name, description, or homepage) — phrasings like "publish the X plugin", "add X to the marketplace", "register these plugins", "list X in the toolchest", or "the marketplace entry for X is stale". Plugins live separately from the marketplace, so publishing means opening a PR on the marketplace repo. NOT needed for ordinary content edits to an already-listed plugin — those reach consumers automatically.
---

# marketplace-publish

Publish one plugin from this source repo to a marketplace **catalog** by opening a pull request on the marketplace repo. Works for a single plugin or a set, in one PR. Runs on your local `gh` credentials — no GitHub Actions, no tokens.

Follow the procedure below with your normal tools (`gh`, `git`, `jq`); it's deliberately plain rather than a script so you can adapt to how many plugins are being published and to anything unusual in the catalog.

## When this is needed (and when it isn't)

A marketplace `marketplace.json` lists each plugin with a `git-subdir` source and **no pinned version**, so Claude Code resolves every install to the latest commit on this repo's default branch. That means **editing a plugin's skills/content reaches consumers automatically** — you do *not* republish for content changes.

A marketplace's **catalog** only needs a change when you:
- **add** a new plugin to it,
- **remove** one, or
- **change a plugin's catalog metadata** — its `name`, `description`, or homepage.

If the user is only editing an already-listed plugin's instructions, tell them no publish is needed.

## Before you start

- `gh` is authenticated (`gh auth status`) with write access to the marketplace repo.
- Each plugin to publish exists at `plugins/<name>/.claude-plugin/plugin.json` with non-empty `name` and `description` (these are copied verbatim into the catalog entry). If a plugin doesn't exist yet, scaffold it with [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) and run `claude plugin validate plugins/<name>` to confirm it's well-formed.

## Which marketplace

Infer the target from this repo's `origin` remote (`custom-agent-skills` → `CypherPoet/cypherpoet-toolchest`), or use one the user names.

## Procedure

The goal: **one PR on the marketplace repo** that adds or updates the chosen plugins' entries in `.claude-plugin/marketplace.json`.

1. **Build each entry.** For every plugin being published, read its `plugins/<name>/.claude-plugin/plugin.json` for `name`, `description`, and `homepage`. Form the catalog entry (the source `url` is *this* repo, paths point into `plugins/`):
   ```json
   {
     "name": "<plugin>",
     "source": { "source": "git-subdir", "url": "https://github.com/<owner>/<this-repo>.git", "path": "plugins/<plugin>" },
     "description": "<from plugin.json>",
     "homepage": "<from plugin.json>"
   }
   ```
   The manifest is the source of truth for `description` and `homepage`. Precedence:
   - **`description`** — always present (the pre-flight check enforced it); copy verbatim.
   - **`homepage`** — if the field is present in the manifest, copy verbatim. Only when it's absent, derive the fallback `https://github.com/<owner>/<this-repo>/tree/main/plugins/<plugin>`.

   To resolve `<owner>/<this-repo>` for the fallback, prefer `gh repo view --json nameWithOwner -q .nameWithOwner` on the source repo — it returns the canonical `owner/repo` regardless of remote protocol. If you fall back to `git remote get-url origin`, normalize the output: HTTPS form `https://github.com/<owner>/<repo>.git` and SSH form `git@github.com:<owner>/<repo>.git` both reduce to `<owner>/<repo>` after stripping the prefix and trailing `.git`. Never interpolate the raw remote string into the URL — an SSH origin produces a broken link like `https://github.com/git@github.com:CypherPoet/custom-agent-skills.git/tree/main/...`.

2. **Clone the marketplace** shallowly to a temp dir, e.g. `gh repo clone <marketplace> /tmp/mkt-publish -- --depth 1`.

3. **Merge into the catalog.** In `/tmp/mkt-publish/.claude-plugin/marketplace.json`, add each entry to `plugins[]` — replacing any existing entry with the same `name` — and keep the array sorted by `name`. `jq` does this cleanly; for a single entry held in `$ENTRY`:
   ```bash
   jq --argjson e "$ENTRY" '.plugins = (((.plugins // []) | map(select(.name != $e.name))) + [$e] | sort_by(.name))' \
     marketplace.json > tmp && mv tmp marketplace.json
   ```
   Apply once per plugin (or fold several into one jq pass). Confirm the result still parses (`jq empty`).

4. **Show the diff and confirm.** Run `git -C /tmp/mkt-publish diff` and show the user before anything is pushed. If there's no change, say so and stop.

5. **Open the PR** on the marketplace repo using local creds:
   ```bash
   git -C /tmp/mkt-publish switch -c publish/<slug>-$(date +%Y%m%d%H%M%S)
   git -C /tmp/mkt-publish commit -am "➕ Publish <plugins> to the marketplace catalog"
   git -C /tmp/mkt-publish push -u origin HEAD
   gh pr create --repo <marketplace> --title "➕ Publish <plugins>" \
     --body "Adds/updates the listed plugin entries in marketplace.json, sourced from this repo via git-subdir."
   ```

6. **Report the PR URL** and clean up the temp clone.

Re-running for an already-listed plugin just updates its entry — the operation is idempotent.

## After publishing

Review and merge the PR on the marketplace repo; once merged, `/plugin install <name>@<marketplace>` resolves the entry. To see what's listed vs. what's local at any point, use the `marketplace-sync-check` skill.
