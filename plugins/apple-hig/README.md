# apple-hig

Thorough distillation of Apple's complete Human Interface Guidelines across all six platforms (iOS, iPadOS, macOS, tvOS, visionOS, watchOS) — component-by-component best practices, hard specs (tap targets, type sizes, color tokens), per-platform deltas, and choose-the-right-component decision tables, with a synced reference corpus that tracks Apple's updates.

## Installation

Install via the marketplace this plugin is published to:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install apple-hig@cypherpoet-toolchest
```

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [apple-human-interface-guidelines](skills/apple-human-interface-guidelines/SKILL.md) | Design guidance distilled from the full Apple HIG — components, layout, platform conventions, accessibility, and hard specs for all six Apple platforms. | Yes |

## Where This Sits Among the Apple Plugins

| Question | Plugin |
|---|---|
| How should this screen look / behave / feel native? | **this plugin** |
| Will this pass App Review? Keyword/metadata strategy? | [mobile-dev](https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/mobile-dev) (`apple-app-store-best-practices`) |
| How do I get the build submitted through App Store Connect? | [app-store-connect-kit](https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/app-store-connect-kit) |
| What are the store screenshot dimensions / capture flow? | [apple-app-store-screenshots](https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/apple-app-store-screenshots) |
