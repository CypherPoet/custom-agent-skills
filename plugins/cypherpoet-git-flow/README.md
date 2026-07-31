# cypherpoet-git-flow

Bundle of git commit and changelog hygiene plugins: emoji commits and changelog maintenance.

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install cypherpoet-git-flow@cypherpoet-toolchest
```

A convenience bundle of git-hygiene skills. Each is also available as its own plugin — install one directly if you only want it.

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [emoji-commits](skills/emoji-commits/SKILL.md) | Write expressive git commit messages with Gitmoji (vendored from [cypherpoet-emoji-commits](https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/cypherpoet-emoji-commits)). | Yes |
| [changelog-maintenance](skills/changelog-maintenance/SKILL.md) | Maintain a project's `CHANGELOG.md` in Keep-a-Changelog format (vendored from [cypherpoet-changelog-maintenance](https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/cypherpoet-changelog-maintenance)). | Yes |
