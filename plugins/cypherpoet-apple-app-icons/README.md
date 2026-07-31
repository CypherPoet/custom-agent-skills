# cypherpoet-apple-app-icons

Apple app icons end to end: design one that converts in the App Store (tap-through, audit, A/B testing) and ship it correctly — Icon Composer Liquid Glass .icon plus an appiconset fallback for older OS versions.

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install cypherpoet-apple-app-icons@cypherpoet-toolchest
```

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [apple-app-icons](skills/apple-app-icons/SKILL.md) | Design an icon that earns the tap (small-size clarity, light/dark contrast, audit rubric, iOS A/B testing, designer brief), then author a Liquid Glass `.icon`, add an `.appiconset` fallback, wire both into Xcode, and debug centering / edge-frame / alpha issues. | Yes |
