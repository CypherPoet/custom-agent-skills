# Project Setup

Module entry points, build tooling, and framework integration *around* a Three.js project. The canonical scene boot is in [../SKILL.md#setup](../SKILL.md#setup); this file covers which entry point to import, how to bundle, and TypeScript / React integration.

## Module Entry Points

`three` ships several entry points. Pick the one that matches your renderer and your tooling:

- `three` — WebGL build. Default for legacy projects.
- `three/webgpu` — WebGPU build. Default for new projects targeting the modern path. Includes `WebGPURenderer`, `MeshStandardNodeMaterial`, and node-material classes.
- `three/tsl` — Shading language nodes (`uniform`, `texture`, `positionLocal`, `Fn`, etc.). Pairs with `three/webgpu`.
- `three/addons/...` — Examples and add-ons (loaders, controls, helpers, post-processing passes). The old path `three/examples/jsm/...` still works but is being phased out — prefer `three/addons/`.

## Install, Bundle, and Frameworks

- **Install & bundle.** `npm install three`, then bundle with Vite (hot-reload, ESM, TS, tree-shaking out of the box; Webpack/esbuild work too). The CDN importmap in [../assets/scene-template.html](../assets/scene-template.html) is for zero-tooling demos — the `import` statements are identical either way.
- **TypeScript.** Install `@types/three` separately — `three` doesn't bundle its own declarations (`npm i -D @types/three`; keep its version aligned with `three`). Then `import * as THREE from "three"` (or `"three/webgpu"`).
- **React.** Use [react-three-fiber](https://github.com/pmndrs/react-three-fiber) + [drei](https://github.com/pmndrs/drei) rather than mounting Three.js directly. The fundamentals in these references apply unchanged; r3f-specific APIs (`useFrame`, `<Canvas>`, drei helpers) are out of scope.

## See Also

- [SKILL.md](../SKILL.md) — canonical scene boot, shared laws, topic routing.
- [fundamentals.md](./fundamentals.md) — cameras, renderer configuration, scene graph, math.
