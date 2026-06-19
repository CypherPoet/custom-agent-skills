# cypherpoet-google-filament-kit

Comprehensive working knowledge of [Google Filament](https://github.com/google/filament), the real-time physically-based rendering engine — the PBR material model and lighting/IBL, the material definition language and `matc` compiler, the core engine API (`Engine`/`Scene`/`View`/`Renderer`/`Camera`, resources, `gltfio`), and per-binding setup for C++, Web (JS/WASM), and Android, distilled from the official documentation with a synced reference corpus that tracks Filament releases.

## Installation

Install via the marketplace this plugin is published to:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install cypherpoet-google-filament-kit@cypherpoet-toolchest
```

## Skills

| Skill | Description |
|---|---|
| [google-filament-mastery](skills/google-filament-mastery/SKILL.md) | Working knowledge of Google Filament — the PBR material model, lighting/IBL, the material language and `matc`, the engine API, glTF loading, and C++/Web/Android setup, grounded in the official docs. |

## Where This Sits Among the Rendering Plugins

| Question | Plugin |
|---|---|
| Real-time PBR rendering with Google Filament (C++, Web, or Android)? | **this plugin** |
| Raw WebGL / WebGL2 — buffers, shaders, draw calls, the GPU pipeline? | [cypherpoet-webgl-kit](../cypherpoet-webgl-kit) |
| Scene-graph 3D on the web with Three.js? | [cypherpoet-threejs-kit](../cypherpoet-threejs-kit) |
