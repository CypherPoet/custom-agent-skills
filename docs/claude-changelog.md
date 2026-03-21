# claude-changelog

Fetch Claude Code release notes from GitHub, summarize them in practical terms, and present them as a polished HTML page or clean Markdown file.

## Purpose

Claude Code release notes on GitHub tend to be terse, commit-style descriptions. This skill bridges that gap: it pulls the raw notes, rewrites them in human-friendly language grouped by category (features, fixes, security, performance, platform), and outputs a formatted file you can read or share.

## Usage

Invoke the skill when asking about Claude Code releases:

> "What's new in Claude Code?"
> "Show me the latest Claude Code changelog"
> "Any recent updates to Claude Code?"

The skill will ask for two preferences (if not already specified):

1. **Format** — HTML (styled webpage opened in browser) or Markdown (`.md` file)
2. **Output directory** — where to save the file (defaults to current working directory)

You can specify both inline:

> "Claude changelog as markdown in ~/Desktop"

## Examples

**Latest releases as HTML**
> "Show me the Claude Code changelog"
> → Fetches the 3 most recent releases, generates a styled HTML page, and opens it in the browser.

**Specific number of releases**
> "Last 5 Claude Code releases as markdown"
> → Fetches 5 releases and writes a `claude-changelog.md` file.

**Specific version**
> "What changed in Claude Code v2.1.78?"
> → Fetches that single release and summarizes it.

## Configuration

Requires the [GitHub CLI](https://cli.github.com/) (`gh`) to be installed and authenticated. The skill fetches release data from `anthropics/claude-code` via `gh api`.

No other setup is needed. The HTML output is self-contained (inline CSS/JS) except for Google Fonts loaded via `<link>`.

## Changelog

| Version | Notes |
|---------|-------|
| 1.0 | Initial skill — GitHub fetch, HTML template with dark editorial theme, Markdown output, category-based grouping |
