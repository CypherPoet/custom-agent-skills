# Plugin Catalog

This repo publishes the following plugins via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace.

| Plugin | Description | Components |
|---|---|---|
| [cypherpoet-app-store-connect-kit](../plugins/cypherpoet-app-store-connect-kit/README.md) | Hands-on App Store Connect submission workflow and console navigation. | 1 skill |
| [cypherpoet-apple-app-icons](../plugins/cypherpoet-apple-app-icons/README.md) | Apple app icons end to end: design one that converts in the App Store (tap-through, audit, A/B testing) and ship it correctly — Icon Composer Liquid Glass .icon plus an appiconset fallback for older OS versions. | 1 skill |
| [cypherpoet-apple-app-store-screenshots](../plugins/cypherpoet-apple-app-store-screenshots/README.md) | Apple App Store screenshot and app preview specifications. | 1 skill |
| [cypherpoet-apple-human-interface-guidelines](../plugins/cypherpoet-apple-human-interface-guidelines/README.md) | Thorough distillation of Apple's complete Human Interface Guidelines across all six platforms (iOS, iPadOS, macOS, tvOS, visionOS, watchOS) — component-by-component best practices, hard specs (tap targets, type sizes, color tokens), per-platform deltas, and choose-the-right-component decision tables, with a synced reference corpus that tracks Apple's updates. | 1 skill |
| [cypherpoet-blender-kit](../plugins/cypherpoet-blender-kit/README.md) | Blender mastery — modeling, materials, rigging, geometry nodes, rendering, and export via bpy, driven through the official Blender MCP server or the headless CLI. | 1 skill |
| [cypherpoet-changelog-maintenance](../plugins/cypherpoet-changelog-maintenance/README.md) | Maintain a project's CHANGELOG.md in Keep-a-Changelog format. | 1 skill |
| [cypherpoet-claude-docs-search](../plugins/cypherpoet-claude-docs-search/README.md) | Look up answers about Claude Code features and behavior in the official Claude Code documentation. | 1 skill |
| [cypherpoet-claude-memory-consolidation](../plugins/cypherpoet-claude-memory-consolidation/README.md) | Audit and consolidate Claude's per-project auto-memory directory, deduping, repairing, and pruning with per-cluster approval. | 1 skill |
| [cypherpoet-emoji-commits](../plugins/cypherpoet-emoji-commits/README.md) | Write expressive git commit messages with Gitmoji. | 1 skill |
| [cypherpoet-excalidraw-kit](../plugins/cypherpoet-excalidraw-kit/README.md) | Comprehensive Excalidraw mastery: authoring .excalidraw scene files by hand (the JSON format, element model, arrow/text binding, and a diagrams-that-argue design methodology), plus the @excalidraw/excalidraw developer API (React component, initialData, the convertToExcalidrawElements skeleton API, restore, SVG/PNG/clipboard export, and Mermaid-to-Excalidraw), shipped with scripts to validate a scene, render it to PNG, and insert icon-library elements — grounded in the official Excalidraw documentation. | 1 skill |
| [cypherpoet-expo-kit](../plugins/cypherpoet-expo-kit/README.md) | Expo / React Native prototyping. | 1 skill |
| [cypherpoet-git-flow](../plugins/cypherpoet-git-flow/README.md) | Bundle of git commit and changelog hygiene plugins: emoji commits and changelog maintenance. | 2 skills |
| [cypherpoet-git-hygiene](../plugins/cypherpoet-git-hygiene/README.md) | Keep local git state tidy: sync branches with the remote, and clean up stale branches and worktrees with per-item approval. | 2 skills |
| [cypherpoet-google-filament-kit](../plugins/cypherpoet-google-filament-kit/README.md) | Comprehensive working knowledge of Google Filament, the real-time physically-based rendering engine — the PBR material model and lighting/IBL, the material definition language and matc compiler, the core engine API (Engine/Scene/View/Renderer/Camera, resources, gltfio), and per-binding setup for C++, Web (JS/WASM), and Android, distilled from the official documentation with a synced reference corpus that tracks Filament releases. | 1 skill |
| [cypherpoet-marketplace-kit](../plugins/cypherpoet-marketplace-kit/README.md) | Maintainer toolkit for running a plugin marketplace with Claude Code and Codex catalogs — publish plugins, audit marketplace and catalog sync, and regenerate the local catalog. | 5 skills |
| [cypherpoet-mobile-dev](../plugins/cypherpoet-mobile-dev/README.md) | iOS App Store publishing best practices. | 2 skills |
| [cypherpoet-react-three-fiber-kit](../plugins/cypherpoet-react-three-fiber-kit/README.md) | React Three Fiber (R3F) + drei tooling for declarative Three.js in React. | 3 skills |
| [cypherpoet-session-handoff](../plugins/cypherpoet-session-handoff/README.md) | Write a structured handoff document so a fresh agent can resume long-running work without losing context. | 1 skill |
| [cypherpoet-session-harvest](../plugins/cypherpoet-session-harvest/README.md) | Harvest a session's learnings into their right homes: a memory, a suggested repo edit (CLAUDE.md/AGENTS.md, docs, or a hook), or a PR that improves one of your own agent skills. | 2 skills |
| [cypherpoet-sf-symbols-kit](../plugins/cypherpoet-sf-symbols-kit/README.md) | Apple SF Symbols end to end: find the right symbol with natural language, export clean recolorable SVGs at any of the 9 weights, browse an HTML gallery, build full icon sets, and convert your own SVG art into importable custom SF Symbol templates. | 1 skill |
| [cypherpoet-svg-tools](../plugins/cypherpoet-svg-tools/README.md) | SVG optimization and cleanup. | 1 skill |
| [cypherpoet-swift-xcode-kit](../plugins/cypherpoet-swift-xcode-kit/README.md) | Swift and Xcode development kit: SwiftUI best practices and 2027 SDK migration, UIKit multi-window modernization, XCTest-to-Swift-Testing migration, security-hardening audits of Xcode build settings, C -fbounds-safety guidance, and on-device/simulator UI verification. | 7 skills |
| [cypherpoet-threejs-kit](../plugins/cypherpoet-threejs-kit/README.md) | Three.js / WebGPU / WebGL tooling. | 2 skills |
| [cypherpoet-webgl-kit](../plugins/cypherpoet-webgl-kit/README.md) | Raw WebGL2 + GLSL shader tooling. | 1 skill |

## Installing

**Claude Code** — via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
/plugin marketplace add CypherPoet/cypherpoet-toolchest
/plugin install <plugin-name>@cypherpoet-toolchest
```

**Codex** — the same marketplace repo carries the Codex catalog:

```shell
codex plugin marketplace add CypherPoet/cypherpoet-toolchest
codex plugin add <plugin-name>@cypherpoet-toolchest
```

A few plugins are Claude Code only (the `claude-*` plugins) — see [`scripts/plugin-registry.json`](../scripts/plugin-registry.json).
