# Slash command stubs (`commands/<name>.md`)

A slash command lives at `plugins/<plugin>/commands/<command-name>.md`. Once installed, it becomes `/<plugin-name>:<command-name>` for the user — so pick command names that read well in that fully-qualified form. `/<plugin-name>:deploy` is clear; `/<plugin-name>:do-it` isn't.

## Frontmatter shape

```yaml
---
description: <one-sentence summary of what this command does>
argument-hint: <optional — placeholder text shown in the input, e.g. "<branch-name>">
model: <optional — e.g. "claude-sonnet-4-6" to pin a specific model for this command>
allowed-tools: <optional — comma-separated list of tools the command may use, e.g. "Bash, Read, Edit">
---
```

Only `description` is required. The other fields restrict or hint about the command's runtime — add them only when you have a specific reason.

## Body

The body of the file is the prompt the model runs when the command is invoked. Write it as plain instructions:

```markdown
---
description: Open a PR for the current branch with a generated title and body.
argument-hint: <optional PR title override>
---

Open a pull request for the current branch.

1. Determine the PR base by checking the branch's tracking remote.
2. If the user passed an argument, use it as the PR title; otherwise generate one from the most recent commit subject.
3. Generate a PR body summarizing the commits since the merge-base with `main`.
4. Run `gh pr create --base <base> --title <title> --body <body>` and report the URL back to the user.
```

When the user runs `/<plugin>:<command> something`, that "something" replaces wherever the prompt references the argument. Use `$ARGUMENTS` (or no placeholder — the harness appends the argument to the prompt automatically) if you want to refer to it explicitly.

## Layout patterns

Flat (one file per command, all in `commands/`) is what this repo's plugins will use today and what auto-discovery expects with no manifest configuration. Categorized layouts (`commands/git/commit.md`, `commands/git/push.md`) and hierarchical layouts require explicit `commands` arrays in the manifest — only reach for them when a plugin grows past ~5 commands and they cluster naturally.

## Minimal stub for scaffolding

```markdown
---
description: <one-sentence summary>
---

<instructions to the model — start with an imperative verb>.
```
