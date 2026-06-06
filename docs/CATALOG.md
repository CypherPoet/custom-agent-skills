# Plugin Catalog

This repo publishes the following plugins via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace.

| Plugin | Description | Components |
|---|---|---|
| [cypherpoet-agent-tooling](../plugins/cypherpoet-agent-tooling/README.md) | Agent tooling for Claude Code workflow, memory, and docs. | 5 skills |
| [cypherpoet-app-store-connect-kit](../plugins/cypherpoet-app-store-connect-kit/README.md) | Hands-on App Store Connect submission workflow and console navigation. | 1 skill |
| [cypherpoet-apple-app-icons](../plugins/cypherpoet-apple-app-icons/README.md) | Apple app icons end to end: design one that converts in the App Store (tap-through, audit, A/B testing) and ship it correctly — Icon Composer Liquid Glass .icon plus an appiconset fallback for older OS versions. | 1 skill |
| [cypherpoet-apple-app-store-screenshots](../plugins/cypherpoet-apple-app-store-screenshots/README.md) | Apple App Store screenshot and app preview specifications. | 1 skill |
| [cypherpoet-blender-kit](../plugins/cypherpoet-blender-kit/README.md) | Blender 3D modeling and MCP integration. | 1 skill |
| [cypherpoet-expo-kit](../plugins/cypherpoet-expo-kit/README.md) | Expo / React Native prototyping. | 1 skill |
| [cypherpoet-git-flow](../plugins/cypherpoet-git-flow/README.md) | Git commit and changelog hygiene. | 2 skills |
| [cypherpoet-marketplace-kit](../plugins/cypherpoet-marketplace-kit/README.md) | Maintainer toolkit for running a Claude Code plugin marketplace — publish plugins, audit marketplace and catalog sync, regenerate the local catalog, and verify dependency-version tags. | 5 skills |
| [cypherpoet-mobile-dev](../plugins/cypherpoet-mobile-dev/README.md) | iOS App Store publishing best practices. | 1 skill |
| [cypherpoet-svg-tools](../plugins/cypherpoet-svg-tools/README.md) | SVG optimization and cleanup. | 1 skill |
| [cypherpoet-threejs-kit](../plugins/cypherpoet-threejs-kit/README.md) | Three.js / WebGPU / WebGL tooling. | 1 skill |
| [cypherpoet-webgl-kit](../plugins/cypherpoet-webgl-kit/README.md) | Raw WebGL2 + GLSL shader tooling. | 1 skill |

## Installing

```shell
/plugin marketplace add CypherPoet/cypherpoet-toolchest
/plugin install <plugin-name>@cypherpoet-toolchest
```

For example, to install just the Claude Code tooling skills:

```shell
/plugin install cypherpoet-agent-tooling@cypherpoet-toolchest
```
