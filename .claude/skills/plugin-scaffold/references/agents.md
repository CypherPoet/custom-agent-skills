# Subagent stubs (`agents/<name>.md`)

A subagent lives at `plugins/<plugin>/agents/<agent-name>.md`. The folder is auto-discovered — no manifest entry needed. Once installed, the agent is referenced as `<plugin-name>:<agent-name>` (or just `<agent-name>` from within the same plugin).

Treat subagents as focused specialists invoked by a parent agent through the `Agent` tool. Keep one agent per file.

## Frontmatter shape

```yaml
---
name: <agent-name>
description: <when to invoke this agent — context-driven, not job-driven>
model: <optional — "sonnet", "haiku", "opus", or a specific model ID>
tools: <optional — comma-separated list of tools the agent may use, e.g. "Read, Glob, Grep, Bash">
---
```

`name` and `description` are required. The other fields constrain the agent's runtime.

## Description: context, not job

The `description:` field tells Claude *when* to delegate to this agent. Lead with the invocation context, not a restatement of the agent's role.

**Weak:**
```yaml
description: A code reviewer that finds bugs.
```

**Strong:**
```yaml
description: >
  Use proactively after the user makes meaningful code changes,
  before they commit. Reviews diffs for correctness bugs, edge
  cases the change misses, and breaking deviations from existing
  patterns. Reports only high-confidence findings.
```

The strong version names *when* to call the agent and *what kind of output* the parent should expect. The weak version restates what the agent's name already implies.

## Body

The body is the agent's system prompt — what it does, how it works, output format. Write in second person ("You are…", "Your job is…"). Keep it focused on the one task the agent is for; cross-references back to the rest of the plugin belong here too.

```markdown
---
name: code-reviewer
description: >
  Reviews diffs for correctness bugs and pattern deviations.
  Use after meaningful code changes, before commit.
---

You are a senior reviewer. Read the current diff and report only correctness bugs and unjustified deviations from existing patterns. Use the `code-review:code-review` skill if it is available.

Output:

- Findings as `[severity] file:line — what's wrong, why it's a bug`.
- A short summary at the end. Empty findings = a short "nothing to flag".
```

## Minimal stub for scaffolding

```markdown
---
name: <agent-name>
description: <when to invoke — context first>
---

You are a <role>. <One-line summary of the task you do>.

<Brief workflow or output format.>
```
