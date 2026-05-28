# Plugin Catalog

This repo publishes the following plugins via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace.

| Plugin | Description | Components |
|---|---|---|
| [cypherpoet-agent-tooling](../plugins/cypherpoet-agent-tooling/README.md) | Agent tooling for Claude Code workflow, memory, and docs. | 5 skills |
| [cypherpoet-blender-kit](../plugins/cypherpoet-blender-kit/README.md) | Blender 3D modeling and MCP integration. | 1 skill |
| [cypherpoet-expo-kit](../plugins/cypherpoet-expo-kit/README.md) | Expo / React Native prototyping. | 1 skill |
| [cypherpoet-git-flow](../plugins/cypherpoet-git-flow/README.md) | Git commit and changelog hygiene. | 2 skills |
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
