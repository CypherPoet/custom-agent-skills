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

This is a convenience bundle — it ships no skills of its own. Installing it pulls in the plugins below. Install any of them individually if you only want one.

## Dependencies

Installed automatically with this plugin:

| Plugin | Version | Description |
|---|---|---|
| [cypherpoet-changelog-maintenance](../cypherpoet-changelog-maintenance) | `latest` | Maintain a project's `CHANGELOG.md` in Keep-a-Changelog format. |
| [cypherpoet-emoji-commits](../cypherpoet-emoji-commits) | `latest` | Write expressive git commit messages with Gitmoji. |
