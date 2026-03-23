---
name: emoji-commits
description: Use Gitmoji to make commits more expressive. Use this skill whenever the user wants to commit changes, write a commit message, uses /commit, or asks for help with git commits — even if they don't mention emoji. Also use when reviewing commit message style or setting up commit conventions for a project.
---

# Emoji Commits

Prefix every commit message with a categorized emoji from the [Gitmoji](https://gitmoji.dev/) standard. This makes git history scannable at a glance — you can tell a bug fix from a new feature or a refactor without reading the message.

## Workflow

1. **Read staged changes** — run `git diff --cached` to understand what's being committed.
2. **Identify the primary intent** — is this a feature, bug fix, refactor, docs update, etc.?
3. **Pick the emoji** — map the intent to a Gitmoji. For the most common ones, use this quick reference:

| Emoji | When to use |
|-------|-------------|
| ✨ | Introduce new features |
| 🐛 | Fix a bug |
| ♻️ | Refactor code |
| 📝 | Add or update documentation |
| ✅ | Add, update, or pass tests |
| 🔧 | Add or update configuration files |
| 🔥 | Remove code or files |
| ⚡️ | Improve performance |
| 🎨 | Improve structure / format of the code |
| 💄 | Add or update the UI and style files |

For the full list (50+ emojis), consult `references/gitmoji.md`.

4. **Compose the message** — format: `<emoji> <concise message explaining the why>`
5. **Present for approval** — show the proposed message and wait for confirmation.
6. **Commit** — run `git commit -m "<emoji> <message>"`.

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

**Ambiguous case — refactor that also fixes a bug:**
The commit both restructures the auth module and fixes a token expiry bug. Pick the primary intent:
```
🐛 Fix token expiry by restructuring auth module
```
If the concerns are truly independent, suggest splitting into two commits instead.

