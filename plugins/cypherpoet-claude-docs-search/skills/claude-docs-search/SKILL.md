---
name: claude-docs-search
description: >
  Use this skill whenever the user asks about Claude Code features, setup,
  configuration, permissions, hooks, MCP servers, skills, settings,
  subagents, plugins, troubleshooting, keyboard shortcuts, CLI flags,
  environment variables, or any other Claude Code behavior. Also use when
  the user asks "how do I do X in Claude Code", "does Claude Code support
  X", "what's the command for X", or seems confused about how a Claude
  Code feature works — even if they don't explicitly say "docs". Looks up
  answers in the official Claude Code documentation. Do NOT use for
  general coding questions, the Claude API/SDK (as opposed to Claude Code
  itself), or questions about the user's own project code.
---

# Claude Code Docs Search

Look up answers in the official Claude Code documentation by fetching current, authoritative markdown directly from the docs site.

## Why this exists

Claude Code's documentation is updated frequently — new features, changed settings, renamed flags. Your training data may not reflect the latest state. Rather than guessing and risking an outdated or wrong answer, this skill teaches you to check the source of truth first.

The Claude Code docs site serves every page as clean markdown when you append `.md` to the URL. There's also a comprehensive **docs map** that lists every page with its section headings, so you can quickly pinpoint exactly which page has the information you need without fetching them all.

## Workflow

### Step 1: Fetch the docs map

Use `WebFetch` to retrieve the docs map:

```
URL: https://code.claude.com/docs/en/claude_code_docs_map.md
Prompt: List all documentation pages and their section headings
```

This returns a structured index of all 75+ docs pages, organized by category (Getting Started, Core Concepts, Configuration, etc.), with nested section headings for each page. Scan this to understand what's available.

### Step 2: Identify relevant pages

Based on the user's question, pick **1–3 pages** whose titles and section headings best match what they're asking about.

For example:
- "How do I set up hooks?" → fetch `hooks-guide.md`
- "What permissions does auto mode grant?" → fetch `permission-modes.md` and possibly `permissions.md`
- "How do I connect an MCP server?" → fetch `mcp.md`

Prefer fewer pages. One well-chosen page usually has everything you need. Only fetch multiple if the question genuinely spans topics (e.g., "how do hooks interact with permissions?").

### Step 3: Fetch the relevant pages

Use `WebFetch` to retrieve each selected page as markdown:

```
URL: https://code.claude.com/docs/en/<page-name>.md
Prompt: <rephrase the user's question to extract the relevant information>
```

The `.md` suffix is what gives you clean markdown instead of the rendered HTML site. Every page linked in the docs map supports this.

If a page is very long and you only need a specific section, tailor your `WebFetch` prompt to extract just that section.

### Step 4: Answer the question

Synthesize what you found into a clear, direct answer. Then cite the source so the user can read more:

> For the full details, see: https://code.claude.com/docs/en/<page-name>

Use the URL **without** the `.md` suffix when sharing with the user — that gives them the nicely rendered version.

## When not to use this skill

- **General coding questions** — "how do I write a Python decorator?" has nothing to do with Claude Code docs
- **Claude API / Anthropic SDK** — those live at `docs.anthropic.com`, not `code.claude.com`
- **User's own project** — questions about their codebase, their code, their bugs
- **Already known with high confidence** — if you're certain about a simple, stable fact (e.g., "Claude Code uses `claude` as the CLI command"), you don't need to look it up every time. Use your judgment — when in doubt, look it up.
