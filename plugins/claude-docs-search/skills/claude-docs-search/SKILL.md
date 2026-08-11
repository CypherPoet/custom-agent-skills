---
name: claude-docs-search
description: >
  Use whenever the user asks about Claude Code itself — features, setup,
  configuration, permissions, hooks, MCP servers, skills, settings, subagents,
  plugins, CLI flags, or troubleshooting — including "how do I X in Claude Code"
  and "does Claude Code support X", even when "docs" is never said. Looks up
  answers in the official Claude Code documentation. Not for general coding
  questions, the Claude API/SDK, or the user's own project code.
---

# Claude Code Docs Search

**Verified:** 2026-07-17

Look up answers in the official Claude Code documentation by fetching current, authoritative markdown directly from the docs site.

## Why This Exists

Claude Code's documentation is updated frequently — new features, changed settings, renamed flags. Your training data may not reflect the latest state. Rather than guessing and risking an outdated or wrong answer, this skill teaches you to check the source of truth first.

Every docs page is served as clean markdown when you append `.md` to its URL — for example `https://code.claude.com/docs/en/hooks.md`. These pages are large (often tens of thousands of tokens each), so the whole game is to fetch **only the one page you actually need** and let `WebFetch` extract just the relevant part — not to pull a big index or several full pages into context. Every fetch you can skip is context you keep.

## Workflow

### Step 1: Go Straight To The Page When You Know It

Most Claude Code questions map to a single, obviously-named page, and the slug usually mirrors the topic. When you can already name the page, skip discovery entirely and fetch it directly (Step 3) — loading an index first is overhead you'd pay on every single question.

Common mappings:

- Hooks → `hooks.md` (concepts) or `hooks-guide.md` (step-by-step setup)
- Settings, config, environment variables → `settings.md`
- Permissions and permission modes → `permissions.md`, `permission-modes.md`
- MCP servers → `mcp.md`
- Subagents → `sub-agents.md`
- Skills → `skills.md`
- Plugins → `plugins.md`
- CLI flags and commands → `cli-reference.md`

The pattern generalizes: the page slug is usually just the topic name. If a direct fetch comes back empty or the slug 404s, your guess was slightly off — fall back to discovery (Step 2).

### Step 2: Discover The Page (Only When You're Unsure)

When you genuinely can't name the page, don't pull down the full docs map — it's a ~24k-token index and you need only a few lines of it. Instead, fetch the compact index and let `WebFetch` do the filtering, so only the relevant candidates come back:

```
URL: https://code.claude.com/docs/llms.txt
Prompt: Which 1–3 pages are most relevant to: "<the user's question>"? Return their .md URLs and nothing else.
```

`llms.txt` lists every page with a one-line description — enough to pick the right one, at a fraction of the map's size. (If a question needs section-level detail to choose between similar pages, the fuller map at `https://code.claude.com/docs/en/claude_code_docs_map.md` is available as a fallback — but reach for it rarely, since it's the expensive option.)

### Step 3: Fetch The Page

Fetch the chosen page as markdown, and pass the user's question as the prompt so `WebFetch` returns just the relevant section instead of the whole page:

```
URL: https://code.claude.com/docs/en/<page-name>.md
Prompt: <rephrase the user's question to extract exactly the relevant information>
```

Prefer a single page — one well-chosen page usually has everything you need. Only fetch a second when the question genuinely spans topics (e.g. "how do hooks interact with permissions?"). The `.md` suffix is what gives you clean markdown instead of the rendered HTML site.

### Step 4: Answer The Question

Synthesize what you found into a clear, direct answer. Then cite the source so the user can read more:

> For the full details, see: https://code.claude.com/docs/en/<page-name>

Share the URL **without** the `.md` suffix — that gives the user the nicely rendered page.

## When Not To Use This Skill

- **General coding questions** — "how do I write a Python decorator?" has nothing to do with Claude Code docs
- **Claude API / Anthropic SDK** — those live at `docs.anthropic.com`, not `code.claude.com`
- **User's own project** — questions about their codebase, their code, their bugs
- **Already known with high confidence** — if you're certain about a simple, stable fact (e.g., "Claude Code uses `claude` as the CLI command"), you don't need to look it up every time. Use your judgment — when in doubt, look it up.

## Primary Sources

- [Claude Code docs map](https://code.claude.com/docs/en/claude_code_docs_map.md) — the index this skill fetches; authoritative for page slugs and the docs URL scheme.
