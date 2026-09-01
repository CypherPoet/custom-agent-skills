# teach

Build a persistent, mission-driven learning workspace with short interactive lessons, trusted resources, and durable learning records.

This plugin packages Matt Pocock's [`teach` skill](https://github.com/mattpocock/skills/tree/main/skills/productivity/teach) for Claude Code and Codex. The imported skill is explicit-invocation only: it does not activate automatically.

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Claude Code
/plugin marketplace add CypherPoet/cypherpoet-toolchest
/plugin install teach@cypherpoet-toolchest

# Codex
codex plugin marketplace add CypherPoet/cypherpoet-toolchest
codex plugin add teach@cypherpoet-toolchest
```

## Usage

- Claude Code: `/teach <what you want to learn>`
- Codex: `$teach <what you want to learn>`

The skill creates a stateful teaching workspace organized around a concrete mission, trusted resources, short HTML lessons, reusable lesson assets, reference documents, and learning records.

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [teach](skills/teach/SKILL.md) | Teach a new skill or concept through a persistent learning workspace. | No |

## Attribution

The skill is redistributed from upstream revision [`3216582`](https://github.com/mattpocock/skills/commit/321658273cb1d20b76026717d027d505790106d4) under the MIT License. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

