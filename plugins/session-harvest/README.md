# session-harvest

Harvest a session's learnings into their right homes: project memory, a suggested repo edit, or a PR that improves one of your own agent skills.

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install session-harvest@cypherpoet-toolchest
```

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [session-harvest](skills/session-harvest/SKILL.md) | Pre-exit sweep of a conversation for learnings worth preserving in memory. | Yes |
| [skill-harvest](skills/skill-harvest/SKILL.md) | Route session/project learnings into the user's own skill repos as approved PRs. | Yes |
