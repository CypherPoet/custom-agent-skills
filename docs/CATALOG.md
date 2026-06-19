# Plugin Catalog

This repo publishes the following plugins via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace.

| Plugin | Description | Components |
|---|---|---|
| [cypherpoet-agent-tooling](../plugins/cypherpoet-agent-tooling/README.md) | Bundle of Claude Code agent-tooling plugins for docs search, memory consolidation, and session handoff/harvest. | Bundle of 4 plugins |
| [cypherpoet-app-store-connect-kit](../plugins/cypherpoet-app-store-connect-kit/README.md) | Hands-on App Store Connect submission workflow and console navigation. | 1 skill |
| [cypherpoet-apple-app-icons](../plugins/cypherpoet-apple-app-icons/README.md) | Apple app icons end to end: design one that converts in the App Store (tap-through, audit, A/B testing) and ship it correctly — Icon Composer Liquid Glass .icon plus an appiconset fallback for older OS versions. | 1 skill |
| [cypherpoet-apple-app-store-screenshots](../plugins/cypherpoet-apple-app-store-screenshots/README.md) | Apple App Store screenshot and app preview specifications. | 1 skill |
| [cypherpoet-apple-human-interface-guidelines](../plugins/cypherpoet-apple-human-interface-guidelines/README.md) | Distillation of Apple's Human Interface Guidelines across all six platforms — best practices, hard specs, platform deltas, and decision tables. | 1 skill |
| [cypherpoet-blender-kit](../plugins/cypherpoet-blender-kit/README.md) | Blender 3D modeling and MCP integration. | 1 skill |
| [cypherpoet-claude-docs-search](../plugins/cypherpoet-claude-docs-search/README.md) | Look up answers about Claude Code features and behavior in the official Claude Code documentation. | 1 skill |
| [cypherpoet-claude-memory-consolidation](../plugins/cypherpoet-claude-memory-consolidation/README.md) | Audit and consolidate Claude's per-project auto-memory directory, deduping, repairing, and pruning with per-cluster approval. | 1 skill |
| [cypherpoet-expo-kit](../plugins/cypherpoet-expo-kit/README.md) | Expo / React Native prototyping. | 1 skill |
| [cypherpoet-git-flow](../plugins/cypherpoet-git-flow/README.md) | Git commit and changelog hygiene. | 2 skills |
| [cypherpoet-google-filament-kit](../plugins/cypherpoet-google-filament-kit/README.md) | Working knowledge of Google Filament, the real-time physically-based rendering engine — the material model, lighting/IBL, the material language and matc, the engine API, glTF, and per-binding setup for C++, Web, and Android, distilled from the official v1.72.0 docs. | 1 skill |
| [cypherpoet-marketplace-kit](../plugins/cypherpoet-marketplace-kit/README.md) | Maintainer toolkit for running a Claude Code plugin marketplace — publish plugins, audit marketplace and catalog sync, regenerate the local catalog, and verify dependency-version tags. | 5 skills |
| [cypherpoet-mobile-dev](../plugins/cypherpoet-mobile-dev/README.md) | iOS App Store publishing best practices. | 1 skill |
| [cypherpoet-session-handoff](../plugins/cypherpoet-session-handoff/README.md) | Write a structured handoff document so a fresh agent can resume long-running work without losing context. | 1 skill |
| [cypherpoet-session-harvest](../plugins/cypherpoet-session-harvest/README.md) | Run a pre-exit sweep of a conversation for learnings worth preserving in project memory. | 1 skill |
| [cypherpoet-sf-symbols-kit](../plugins/cypherpoet-sf-symbols-kit/README.md) | Apple SF Symbols end to end: find the right symbol with natural language, export clean recolorable SVGs at any of the 9 weights, browse an HTML gallery, build full icon sets, and convert your own SVG art into importable custom SF Symbol templates. | 1 skill |
| [cypherpoet-svg-tools](../plugins/cypherpoet-svg-tools/README.md) | SVG optimization and cleanup. | 1 skill |
| [cypherpoet-swift-xcode-kit](../plugins/cypherpoet-swift-xcode-kit/README.md) | Swift and Xcode development kit: SwiftUI best practices and 2027 SDK migration, UIKit multi-window modernization, XCTest-to-Swift-Testing migration, security-hardening audits of Xcode build settings, C -fbounds-safety guidance, and on-device/simulator UI verification. | 7 skills |
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
