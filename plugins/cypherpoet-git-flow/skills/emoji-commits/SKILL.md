---
name: emoji-commits
description: >
  Use this skill whenever the user wants to commit changes, write a commit
  message, uses /commit, or asks for help with git commits — even if they don't
  mention emoji. Also use when reviewing commit message style or setting up
  commit conventions for a project. Uses Gitmoji to make commits more expressive.
---

# Emoji Commits

Prefix every commit message with a categorized emoji from the [Gitmoji](https://gitmoji.dev/) standard. This makes git history scannable at a glance — you can tell a bug fix from a new feature or a refactor without reading the message.

## Workflow

1. **Read staged changes** — run `git diff --cached` to understand what's being committed.
2. **Identify the primary intent** — is this a feature, bug fix, refactor, docs update, etc.?
3. **Check the repo's voice** — run `git log --oneline -15`. History wins over the reference table: match an established house prefix even when it isn't in the table (e.g. a repo that sweeps with 🧹), and note whether messages carry a scope.
4. **Pick the emoji** — unless step 3 found an established prefix for this kind of change, map the intent to a Gitmoji from `references/gitmoji.md`.
5. **Compose the message** — format: `<emoji> <concise message explaining the why>`, mirroring the repo's scoping when history uses one (`<emoji> <Area>: <summary>`, `<emoji> <type>(<scope>): <summary>`, …).
6. **Present for approval** — show the proposed message and wait for confirmation. In an unattended run there is no one to ask: skip this step and commit directly.
7. **Commit** — run `git commit -m "<emoji> <message>"`.

Use the actual Unicode emoji character, not the `:shortcode:` — it's more portable across Git clients, terminals, and GitHub.

## Examples

**New feature added:**
```
✨ Add search bar with autocomplete support
```

**Bug fix:**
```
🐛 Fix null pointer when user profile is missing
```

**Documentation update:**
```
📝 Update API reference with new rate limit endpoints
```

**Same change in a repo whose history scopes messages (step 3):**
```
📝 Docs: update API reference with new rate limit endpoints
```

**Ambiguous case — refactor that also fixes a bug:**
The commit both restructures the auth module and fixes a token expiry bug. Pick the primary intent:
```
🐛 Fix token expiry by restructuring auth module
```
If the concerns are truly independent, suggest splitting into two commits instead.

