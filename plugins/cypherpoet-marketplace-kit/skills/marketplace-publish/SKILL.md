---
name: marketplace-publish
description: >
  Publish one or more of this repo's plugins to its marketplace — both the
  Claude Code and Codex catalogs in the marketplace repo — by opening a PR
  there. Use to add a new plugin to the marketplace or update an already-listed
  plugin's catalog entry (name, description, homepage, Codex category). Not
  needed for ordinary content edits to a listed plugin — those reach consumers
  automatically.
disable-model-invocation: true
---

# marketplace-publish

**Verified:** 2026-07-17

Publish one plugin from this source repo to a marketplace **catalog** by opening a pull request on the marketplace repo. Works for a single plugin or a set, in one PR. Runs on your local `gh` credentials — no GitHub Actions, no tokens.

A marketplace repo carries **two catalog files**, one per harness: `.claude-plugin/marketplace.json` (Claude Code) and `.agents/plugins/marketplace.json` (Codex). One publish run keeps both in step — a dual-harness plugin gets an entry in each; a Claude-only plugin gets a Claude entry alone.

Follow the procedure below with your normal tools (`gh`, `git`, `jq`); it's deliberately plain rather than a script so you can adapt to how many plugins are being published and to anything unusual in the catalog.

**Manual-only on every harness.** Claude Code enforces this via the `disable-model-invocation` frontmatter flag, Codex via `policy.allow_implicit_invocation: false` in [`agents/openai.yaml`](agents/openai.yaml). On any harness with neither, apply the same rule yourself — run this skill only on the user's explicit request, never proactively.

## When this is needed (and when it isn't)

This skill changes only the marketplace **catalog** (`marketplace.json`) — it does **not** ship plugin content. Content updates are gated by each plugin's `version` in `plugin.json` (Claude Code's update cache key; the `git-subdir` commit SHA is only the fallback when no version is set), so reaching existing installs with edited content means **bumping that plugin's `version`**, not republishing the catalog.

A marketplace's **catalog** only needs a change when you:
- **add** a new plugin to it,
- **remove** one,
- **change a plugin's catalog metadata** — its `name`, `description`, or homepage, or
- **change a plugin's harness classification or Codex `category`** in the source repo's `scripts/plugin-registry.json` (these drive the Codex catalog entry).

If the user is only editing an already-listed plugin's instructions, tell them no publish is needed.

## Before you start

- `gh` is authenticated (`gh auth status`) with write access to the marketplace repo.
- Each plugin to publish exists at `plugins/<name>/.claude-plugin/plugin.json`. If a plugin doesn't exist yet, scaffold it with Claude Code's [`/plugin-dev:create-plugin`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/plugin-dev/commands/create-plugin.md) or Codex's `$plugin-creator`, then confirm it's well-formed — `claude plugin validate plugins/<name>` where the `claude` CLI exists; otherwise check the manifest parses and carries `name`, `version`, and `description`. **Removals differ by cause**: a plugin **deleted** from the source repo has no manifest to read — skip this check and step 1 for it; step 3's removal commands are its whole path. A plugin **reclassified Claude-only** still exists and still has its manifest: only its Codex entry is removed (step 3), and if the same change also edited its `name`/`description`/`homepage`, run steps 1–3 for its Claude entry as usual — don't let the reclassification swallow a concurrent Claude-catalog update.
- Run `npm run sync:check` in a dual-harness source repo. This verifies the generated Codex manifest and vendored skills before the plugin path is published.

## Which marketplace

Resolve this repo's `owner/repo` (`gh repo view --json nameWithOwner -q .nameWithOwner`, or a normalized `git remote get-url origin`) and look it up in the bundled registry [`references/marketplaces.md`](../../references/marketplaces.md) (at runtime, resolve that link relative to this skill's directory — it lives at the plugin root, two levels up from this SKILL.md). Each row supplies both the marketplace target and its user-facing Codex display name. If there's no row for this repo, ask the user for both values — and offer to add a row so the next run resolves them automatically.

## Procedure

The goal: **one PR on the marketplace repo** that adds or updates the chosen plugins' entries in both catalog files — `.claude-plugin/marketplace.json` (Claude Code) and `.agents/plugins/marketplace.json` (Codex).

1. **Build each entry.** For every plugin being published, read its `plugins/<name>/.claude-plugin/plugin.json` for `name`, `description`, and `homepage`. Form the Claude catalog entry (the source `url` is *this* repo, and Claude always installs the authored package under `plugins/`):
   ```json
   {
     "name": "<plugin>",
     "source": { "source": "git-subdir", "url": "https://github.com/<owner>/<this-repo>.git", "path": "plugins/<plugin>" },
     "description": "<from plugin.json>",
     "homepage": "<from plugin.json>"
   }
   ```
   The manifest is the source of truth for `description` and `homepage`. Precedence:
   - **`description`** — copy verbatim. If the field is missing or empty, stop and ask the user to populate it before continuing; the catalog can't ship a blank description.
   - **`homepage`** — if the field is present in the manifest, copy verbatim. If it's absent, derive the fallback `https://github.com/<owner>/<this-repo>/tree/<default-branch>/plugins/<plugin>`, resolving `<default-branch>` the same way step 1's Codex `ref` does — never hardcode `main`.

   To resolve `<owner>/<this-repo>` for the fallback, prefer `gh repo view --json nameWithOwner -q .nameWithOwner` on the source repo — it returns the canonical `owner/repo` regardless of remote protocol. If you fall back to `git remote get-url origin`, normalize the output: HTTPS form `https://github.com/<owner>/<repo>.git` and SSH form `git@github.com:<owner>/<repo>.git` both reduce to `<owner>/<repo>` after stripping the prefix and trailing `.git`. Never interpolate the raw remote string into the URL — an SSH origin produces a broken link like `https://github.com/git@github.com:<owner>/<repo>.git/tree/main/...`.

   **Codex catalog entry.** Read the source repo's `scripts/plugin-registry.json`: a plugin listed under `dual_harness_plugins` also gets a Codex entry, carrying that plugin's `category` from the same file; a plugin under `claude_only_plugins` — or any plugin in a repo with no `scripts/plugin-registry.json` — is Claude-only, so skip its Codex entry and publish to the Claude catalog alone. Codex installs the same `plugins/<plugin>` directory as Claude Code and reads its own manifest and skill metadata there. The Codex entry (`policy` is constant; for `ref`, resolve the source repo's default branch — `gh repo view <owner>/<this-repo> --json defaultBranchRef -q .defaultBranchRef.name` — rather than assuming `main`):
   ```json
   {
     "name": "<plugin>",
     "source": { "source": "git-subdir", "url": "https://github.com/<owner>/<this-repo>.git", "path": "plugins/<plugin>", "ref": "<default-branch>" },
     "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
     "category": "<from plugin-registry.json>"
   }
   ```

   The marketplace repo's CI enforces this same entry shape mechanically: `scripts/catalog-health.mjs` there pins the contract as exported constants (`SOURCE_REPOSITORY_URL`, `SOURCE_DEFAULT_BRANCH`, `EXPECTED_CODEX_POLICY`, `EXPECTED_CODEX_DISPLAY_NAME`). This skill resolves the source URL, default branch, and display name dynamically; the checker verifies them — so a source-repo rename, default-branch rename, display-name change, or any change to the entry shape must update the marketplace checker in the same release, or publish PRs will fail its `catalog-validation` check.

2. **Clone the marketplace** shallowly to a temp dir, e.g. `gh repo clone <marketplace> /tmp/mkt-publish -- --depth 1`.

3. **Merge into the catalog.** Run every command in this step from the clone root (`/tmp/mkt-publish`) — the paths below are all clone-root-relative. In `.claude-plugin/marketplace.json`, add each entry to `plugins[]` — replacing any existing entry with the same `name` — and keep the array sorted by `name`. `jq` does this cleanly; for a single entry held in `$ENTRY`:
   ```bash
   jq --argjson e "$ENTRY" '.plugins = (((.plugins // []) | map(select(.name != $e.name))) + [$e] | sort_by(.name))' \
     .claude-plugin/marketplace.json > tmp && mv tmp .claude-plugin/marketplace.json
   ```
   Apply once per plugin (or fold several into one jq pass).

   Apply the same merge to the Codex catalog at `.agents/plugins/marketplace.json` for every Codex entry built in step 1. If that file doesn't exist yet, create it first as `{"name": "<marketplace-name>", "interface": {"displayName": "<Codex-display-name>"}, "plugins": []}`, where `<marketplace-name>` matches the `name` field in `.claude-plugin/marketplace.json` and `<Codex-display-name>` comes from the mapping registry. If the file already exists, verify that both top-level fields match the mapping before editing plugin entries; do not silently replace an unexpected marketplace identity.

   **Removals.** The merge above only adds or updates — handle removals explicitly (no manifest is read; the plugin may no longer exist in the source repo):
   - A plugin **deleted from the source repo** comes out of **both** catalog files:
     ```bash
     jq --arg n "<plugin>" '.plugins = ((.plugins // []) | map(select(.name != $n)))' \
       .claude-plugin/marketplace.json > tmp && mv tmp .claude-plugin/marketplace.json
     jq --arg n "<plugin>" '.plugins = ((.plugins // []) | map(select(.name != $n)))' \
       .agents/plugins/marketplace.json > tmp && mv tmp .agents/plugins/marketplace.json
     ```
   - A plugin **reclassified from `dual_harness_plugins` to `claude_only_plugins`** comes out of the **Codex catalog only** (run just the second command) — its Claude entry stays published.
   - If `.agents/plugins/marketplace.json` doesn't exist (a marketplace that has never published Codex entries), skip the Codex removal command — don't create the file just to delete from it.

   Confirm both files still parse (`jq empty`).

   If the marketplace generates its **Plugins** table from the catalog — the table is wrapped in `<!-- BEGIN/END:PLUGINS-TABLE -->` markers and the repo ships `scripts/sync-readme-table.mjs` — regenerate it now so the README reflects the new entries: `(cd /tmp/mkt-publish && node scripts/sync-readme-table.mjs)`. Skip this for catalogs without that script. The staged commit in step 6 picks up the regenerated `README.md` alongside the catalog files.

4. **Validate the marketplace manifest.** Run `claude plugin validate --strict /tmp/mkt-publish` to confirm the updated Claude manifest still passes schema checks. If the repository's pinned validator is unavailable, stop and install its locked dependencies; JSON parsing is not a substitute for the platform validator. (The Codex catalog has no stable local validation command — the `jq empty` parse check in step 3 is its repository gate; `codex plugin marketplace add` on the merged repo is the runtime proof.)

5. **Show the diff and confirm.** Stage the publish's files explicitly, then review the staged diff — a first Codex publish creates `.agents/plugins/marketplace.json` as an *untracked* file, which plain `git diff` (and `commit -am`) silently skip:
   ```bash
   git -C /tmp/mkt-publish status --short   # confirm nothing unexpected changed in the clone
   git -C /tmp/mkt-publish add .claude-plugin/marketplace.json .agents/plugins/marketplace.json README.md
   git -C /tmp/mkt-publish diff --staged
   ```
   Stage exactly what this publish touched — drop from the `add` any path that doesn't apply (a Claude-only change with no Codex catalog; a README that wasn't regenerated). Never stage blindly (`add -A`/`add .`): the clone may hold stray files from validation or table generation. Show the user the staged diff before anything is pushed. If there's no staged change, say so and stop.

6. **Open the PR** on the marketplace repo using local creds (committing the staged changes from step 5):
   ```bash
   git -C /tmp/mkt-publish switch -c publish/<slug>-<timestamp>   # e.g. publish/webgl-kit-20260713220541
   git -C /tmp/mkt-publish commit -m "➕ Publish <plugins> to the marketplace catalog"
   git -C /tmp/mkt-publish push -u origin HEAD
   gh pr create --repo <marketplace> --head publish/<slug>-<timestamp> --title "➕ Publish <plugins>" \
     --body "Adds/updates the listed plugin entries in the marketplace catalogs, sourced from this repo via git-subdir."
   ```
   The explicit `--head` keeps `gh pr create` independent of your current directory — without it, gh infers the head branch from whatever git repo the shell happens to sit in (usually the *source* repo, which aborts the command).

7. **Report the PR URL** and clean up the temp clone.

Re-running for an already-listed plugin just updates its entry — the operation is idempotent.

## After publishing

Review and merge the PR on the marketplace repo; once merged, `/plugin install <name>@<marketplace>` (Claude Code) and `codex plugin add <name>@<marketplace>` (Codex, after `codex plugin marketplace add <owner>/<marketplace-repo>`) resolve the entries. To see what's listed vs. what's local at any point, use the `marketplace-sync-check` skill.

## Primary Sources

- [Plugin marketplaces (Claude Code docs)](https://code.claude.com/docs/en/plugin-marketplaces) — authoritative for the Claude `marketplace.json` schema and marketplace commands.
- [Plugins reference (Claude Code docs)](https://code.claude.com/docs/en/plugins-reference) — authoritative for plugin manifest fields.
- [Build plugins (Codex docs)](https://learn.chatgpt.com/docs/build-plugins) — authoritative for the Codex `.agents/plugins/marketplace.json` schema (`source` types, required `policy` + `category`) and `codex plugin marketplace` commands.
