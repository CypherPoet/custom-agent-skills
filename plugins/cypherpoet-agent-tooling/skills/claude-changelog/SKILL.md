---
name: claude-changelog
description: >
  Use when the user asks about the Claude Code changelog, release notes,
  or version history for Claude Code (the CLI tool) itself — including
  casual questions about recent changes, what's new, or whether a
  specific feature shipped. Triggers for queries like "claude changelog",
  "what changed in claude code", "latest claude code release", "claude
  code release notes", "what's new in claude code", "any recent updates
  to claude code", "has anything changed in claude", or "what version of
  claude code am I on". The skill fetches releases from GitHub and
  renders a readable HTML or Markdown summary. Not for general project
  changelogs, codebase diffs, or "what's new" questions about the user's
  own code.
---

# Claude Changelog

Fetch Claude Code release notes from GitHub, summarize them in practical terms, and present them in the user's preferred format — either a polished HTML page or a clean Markdown file.

## Why this exists

Claude Code release notes live on GitHub and tend to be technical and terse — commit-style descriptions that don't immediately convey what changed for you as a user. This skill bridges that gap: it pulls the raw notes, rewrites them in human terms, and gives you a nicely formatted output you can actually enjoy reading.

## Workflow

### Step 1: Determine preferences

Check whether the user's message already specifies a format or output location. For example:
- "show me the changelog as markdown" → format is Markdown, ask only about directory
- "save the changelog to ~/Desktop" → directory is ~/Desktop, ask only about format
- "claude changelog as markdown in /tmp" → both specified, skip questions entirely

If either preference is missing, use `AskUserQuestion` to prompt. Ask only what's needed — if the user specified one preference, ask only about the other. Questions:

- **Format**: "HTML" (styled webpage opened in browser) or "Markdown" (`.md` file). Default recommendation: HTML.
- **Output directory**: Where to save the file. Default: current working directory.

### Step 2: Fetch releases

Use the GitHub CLI to pull structured release data:

```bash
gh api repos/anthropics/claude-code/releases --jq '.[:3]'
```

Default to the **latest 3 releases**. If the user asks for a specific number (e.g., "last 5 releases", "just the latest one"), adjust the slice accordingly.

Extract from each release:
- `tag_name` — the version (e.g., `v2.1.78`)
- `published_at` — when it shipped
- `body` — the raw release notes in markdown

If the `gh` command fails (not installed, not authenticated, network issue), tell the user what went wrong and suggest they run `gh auth login` or check their connection. Don't try to work around it with cached data.

### Step 3: Summarize practically

Now rewrite the changelog in terms a working developer actually cares about. The goal is to answer: **"What does this mean for my day-to-day workflow?"**

Group changes into these categories (matching the template's design system):
- **Features** (green) — things you can now do that you couldn't before
- **Fixes** (blue) — bugs that were squashed
- **Security** (red) — security-relevant changes, vulnerabilities patched, permission fixes
- **Performance** (purple) — speed improvements, memory reductions, efficiency gains
- **Platform** (yellow) — platform-specific changes (VS Code, JetBrains, tmux, WSL, Windows, etc.)

If a change is a **breaking change**, call it out prominently within whichever category it belongs to — bold it and prefix with "**Breaking:**". Breaking changes aren't their own category; they're a severity modifier on an existing one.

For each item, translate the technical description into a practical one-liner. For example:
- Technical: "Added `StopFailure` hook event"
- Practical: "You can now run custom scripts when a hook fails — useful for cleanup or alerts"

Skip items that are purely internal or have no user-facing impact. If a release has very few changes, don't force categories — just list them.

Print the summary to the conversation.

### Step 4: Generate the output file

The output filename is `claude-changelog.<ext>` where `<ext>` matches the chosen format. Save it to the directory from Step 1.

#### HTML format

Read the template file at `assets/template.html` (relative to this skill's directory). This is a self-contained HTML page with the full CSS design system already in place — dark editorial theme, custom fonts, grain overlay, staggered animations, and color-coded change indicators.

Fill in the dynamic content at the `<!-- PLACEHOLDER -->` comments in the template:

1. **`header-meta`**: Replace with spans showing the release count, version range, and generation date. Separate with `<span class="dot"></span>` dividers.

2. **`summary-cards`**: Count all changes across fetched releases. Create 4 cards using the classes `card-feature`, `card-fix`, `card-security`, `card-perf` with totals for new features, bug fixes, security fixes, and performance improvements.

3. **`practical-items`**: Curate 8–12 of the most impactful changes into `<li>` elements inside `.practical-list`. Each gets a tag:
   - `<span class="tag tag-action">Action</span>` (green) — things the user should do or try
   - `<span class="tag tag-security">Security</span>` (red) — security-relevant changes
   - `<span class="tag tag-fix">Fix</span>` (blue) — notable bug fixes
   - `<span class="tag tag-perf">Perf</span>` (purple) — performance improvements

4. **`release-articles`**: One `<article class="release">` per version, newest first. The first release includes `<span class="release-tag">Latest</span>`. Each change in `.release-changes` gets a color-coded dot:
   - `<span class="change-icon feat"></span>` (green) — new features
   - `<span class="change-icon fix"></span>` (blue) — bug fixes
   - `<span class="change-icon security"></span>` (red) — security fixes
   - `<span class="change-icon perf"></span>` (purple) — performance improvements
   - `<span class="change-icon platform"></span>` (yellow) — platform-specific (VSCode, tmux, WSL, etc.)

5. **Raw notes**: Add a `<details>` block at the end of each article with the original GitHub release body:
   ```html
   <details>
     <summary>Raw release notes</summary>
     <div class="raw-notes">[original markdown body from GitHub]</div>
   </details>
   ```

Save the filled template to the output directory. Then open it in the user's default browser — on macOS use `open`, on Linux use `xdg-open`.

#### Markdown format

Write a clean `.md` file with the same content structure:

```markdown
# Claude Code Changelog

*Covering v2.1.76 — v2.1.78 (March 10–17, 2026)*

---

## v2.1.78 — March 17, 2026

### Features
- ...

### Fixes
- ...

### Security
- ...

### Performance
- ...

### Platform
- ...

<details>
<summary>Raw release notes</summary>

(original body from GitHub)

</details>

---

## v2.1.77 — March 14, 2026
...
```

After saving, tell the user where the file is. Don't open it in a browser — Markdown is meant to be read in an editor or rendered by GitHub/VS Code.

### Step 5: Confirm

Tell the user the file is saved and where to find it.

## Notes

- Always fetch fresh data from GitHub — don't rely on any local cache
- The HTML is self-contained except for Google Fonts loaded via `<link>` in the template — all CSS/JS is inline
- If the user asks about a specific version, fetch just that one release using `gh api repos/anthropics/claude-code/releases/tags/<tag>`
