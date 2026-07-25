---
name: threejs-mastery
description: >
  Use whenever the user is working with Three.js: scenes, WebGPU/WebGL
  rendering, geometry, materials, lighting, textures, TSL or GLSL shaders,
  animation, loaders, raycasting, controls, or post-processing. Trigger on
  .glb/.gltf files, NodeMaterial, OrbitControls, EffectComposer, or any Three.js
  API — even when "Three.js" is never named. Treats WebGPURenderer + TSL as the
  primary path, WebGLRenderer + GLSL as the fallback.
---

# Three.js Mastery

## Overview

Comprehensive Three.js reference covering modern best practices. The body of this file is shared setup, cross-cutting laws, a topic routing table, and the mistakes that bite across every topic. Topical depth lives in [references/](./references/) — one file per topic, each ending in its own Common Mistakes table.

Two rendering paths exist, and this skill treats them as primary/fallback:

- **Primary: `WebGPURenderer` + TSL.** Recommended for new code. Async initialization, node-based shading, modern post-processing pipeline. Works by default in Chrome/Edge 113+, Safari 26+, and Firefox 141+.
- **Fallback: `WebGLRenderer` + GLSL.** The compatibility path. Same scene graph, same API surface for materials/lights/loaders, classic `ShaderMaterial` + `EffectComposer`. Use when you need to support older browsers or you're porting existing code.

The two share the vast majority of the API. Specific differences are called out in the relevant reference file.

**Going below the framework?** For raw WebGL2 / GLSL intricacies *beneath* Three.js — hand-rolling the GL pipeline, deep GLSL technique, or dropping down when you hit a framework limit — use the sibling **`webgl-mastery`** skill (the `cypherpoet-webgl-kit` dependency). This skill stays at the scene-graph / app level; `webgl-mastery` covers the layer underneath.

## When to Use

Trigger this skill when the user:

- Mentions Three.js, `THREE`, `three.js`, or works with `.glb`/`.gltf`/`.hdr`/`.exr` files.
- Asks about WebGPU or WebGL 3D rendering in the browser.
- Names a class or addon (`Scene`, `Mesh`, `ShaderMaterial`, `MeshStandardMaterial`, `MeshStandardNodeMaterial`, `OrbitControls`, `GLTFLoader`, `EffectComposer`, `RenderPipeline`, `PostProcessing`, `Raycaster`, `AnimationMixer`, `BufferGeometry`, `InstancedMesh`, etc.).
- Describes a problem in those terms even without naming Three.js — e.g. "my GLB model looks washed out", "wave effect on vertices", "click detection on a 3D scene", "bloom effect", "raycasting performance".
- Wants to set up a new 3D scene in the browser or migrate an existing one to modern APIs.

## Setup

The canonical scene boot uses `WebGPURenderer` with async initialization. The full HTML version is in [assets/scene-template.html](./assets/scene-template.html) — copy-paste ready.

```javascript
import * as THREE from "three/webgpu";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.set(0, 0, 5);

const renderer = new THREE.WebGPURenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

await renderer.init();              // REQUIRED before the first render

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const sun = new THREE.DirectionalLight(0xffffff, 1.2);
sun.position.set(5, 5, 5);
scene.add(sun);

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const delta = clock.getDelta();
  controls.update();
  renderer.render(scene, camera);
});
```

### WebGL Fallback

When you need broader compatibility, swap `WebGPURenderer` for `WebGLRenderer`. Everything else stays the same — drop the `await renderer.init()` call:

```javascript
import * as THREE from "three";   // not "three/webgpu"

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
// ...no init() needed
```

You can also feature-detect at runtime: try `WebGPURenderer`, fall back to `WebGLRenderer` on failure or unsupported environments.

## Starting a New Project

### Verify the Latest Release

Three.js ships ~monthly and the API surface for TSL and `WebGPURenderer` is still evolving. Before pinning a version, check the current release:

```bash
npm view three version
```

Or read the [release notes](https://github.com/mrdoob/three.js/releases). When a code example here references a class or node that doesn't exist in your version, the cause is almost always that the symbol was renamed/added/removed in a more recent release — check the changelog before assuming the example is wrong.

[`assets/scene-template.html`](./assets/scene-template.html) pins a specific Three.js version in its importmap — treat it as a fallback, not authoritative current state. Before handing the template (or any importmap snippet) to a user, verify against the latest release: `npm view three version`, the [release feed](https://github.com/mrdoob/three.js/releases), or context7's threejs docs. If the pin is behind by more than two minor releases, bump all three pinned URLs (`three`, `three/tsl`, `three/addons/`) before producing the answer.

**Audit baseline:** this skill's content was last verified against **Three.js r185** (2026-07-24). When refreshing it for a newer release, diff **r185 → current** in the [Migration Guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide) and release notes instead of re-checking everything — then bump this line (release + date) as the final step of the audit.

### Project Setup & Module Entry Points

Module entry points (`three` / `three/webgpu` / `three/tsl` / `three/addons/`), npm + Vite bundling, TypeScript, and React (react-three-fiber) live in [references/project-setup.md](./references/project-setup.md).

## Shared Laws

These cross every topic. Internalize them once.

### Color Space

PBR rendering assumes linear math internally and sRGB on the way out. Stick to these rules:

- `renderer.outputColorSpace = THREE.SRGBColorSpace` is the default. Don't override unless you know why.
- Color/albedo and emissive textures need `texture.colorSpace = THREE.SRGBColorSpace`.
- Data textures (normal, roughness, metalness, AO, displacement) stay at the default (no color space).
- `GLTFLoader` sets these correctly automatically. `TextureLoader` does not — set them yourself.

See [references/textures.md#color-space](./references/textures.md#color-space--the-1-gotcha).

### Frame Delta

Drive everything time-dependent with `clock.getDelta()`, not wall-clock time:

```javascript
const clock = new THREE.Clock();

renderer.setAnimationLoop(() => {
  const delta = clock.getDelta();    // Seconds since last frame
  controls.update();                 // Required when damping is on
  mixer?.update(delta);              // Required for AnimationMixer
  renderer.render(scene, camera);
});
```

`controls.update()` is mandatory whenever `OrbitControls.enableDamping = true` or `autoRotate = true`. `mixer.update(delta)` is mandatory for every `AnimationMixer`, every frame.

### Dispose Lifecycle

GPU resources are not garbage-collected. Anything that owns GPU memory has `.dispose()`:

```javascript
geometry.dispose();
material.dispose();
texture.dispose();
renderTarget.dispose();
```

When discarding a loaded model, traverse and dispose:

```javascript
function disposeModel(model) {
  model.traverse((child) => {
    if (child.isMesh) {
      child.geometry?.dispose();
      const mats = Array.isArray(child.material) ? child.material : [child.material];
      mats.forEach((m) => {
        Object.values(m).forEach((v) => v?.isTexture && v.dispose());
        m.dispose();
      });
    }
  });
  scene.remove(model);
}
```

### Resize

Three handlers must move in lockstep with the canvas size:

```javascript
function onResize() {
  const w = window.innerWidth, h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer?.setSize(w, h);               // EffectComposer (legacy)
  postProcessing?.setSize(w, h);         // PostProcessing (TSL)
}
window.addEventListener("resize", onResize);
```

### Modern Import Alias

All examples and references use `three/addons/...` — the modern alias. The older `three/examples/jsm/...` path still works but is being phased out. Standardize on `three/addons/` everywhere in new code.

### Async Init

`WebGPURenderer` requires `await renderer.init()` before the first `render()`. Forgetting this is the #1 silent failure when porting a scene from WebGL.

## Topics

| Topic | Reference | What it covers |
|-------|-----------|----------------|
| Fundamentals | [fundamentals.md](./references/fundamentals.md) | Cameras, Object3D, scene graph, math utilities, LoadingManager, LOD, merging |
| Geometry | [geometry.md](./references/geometry.md) | Built-in shapes, `BufferGeometry`, attributes, instancing, edges/wireframe, morph targets |
| Materials | [materials.md](./references/materials.md) | PBR (`MeshStandardMaterial`), classic types, node materials (TSL), ShaderMaterial (GLSL) |
| Lighting | [lighting.md](./references/lighting.md) | Light types, shadows tuning, IBL/PMREM/HDR environment lighting |
| Textures | [textures.md](./references/textures.md) | Loaders, color space, filtering, render targets, UVs, compressed textures |
| Loaders | [loaders.md](./references/loaders.md) | GLTF deep dive, Draco/Meshopt/KTX2 compression, OBJ/FBX/STL/PLY, async patterns |
| Animation | [animation.md](./references/animation.md) | `AnimationMixer`, GLTF clips, skeletal/morph targets, blending, procedural patterns |
| Interaction | [interaction.md](./references/interaction.md) | Raycaster, controls catalog (Orbit/Fly/PointerLock/Transform/Drag), selection, screen↔world |
| Shaders (TSL) | [shaders.md](./references/shaders.md) | TSL essentials + recipes (primary), WGSL interop, shader debugging + performance |
| Shaders (GLSL, legacy) | [shaders-glsl.md](./references/shaders-glsl.md) | Raw-GLSL `ShaderMaterial`/`RawShaderMaterial`, `onBeforeCompile`, `ShaderChunk`, GLSL function reference |
| Post-processing | [postprocessing.md](./references/postprocessing.md) | TSL `PostProcessing` pipeline + node passes (primary), `EffectComposer` (legacy) |
| Compute | [compute.md](./references/compute.md) | GPU compute (WebGPU only): storage buffers, `instancedArray`/`attributeArray`, `compute()` dispatch, particles/simulation |
| WebGPU runtime | [webgpu-runtime.md](./references/webgpu-runtime.md) | Device-loss handling and recovery, requesting device limits/features (WebGPU) |
| Project setup | [project-setup.md](./references/project-setup.md) | Module entry points, npm/Vite bundling, TypeScript, React (r3f) |

## Routing Rules

When the user's question fits cleanly into one topic, load that reference and answer from it. When it spans two or three (typical for non-trivial scenes), load each in turn.

Quick routing cues:

- Loading a `.glb`/`.gltf`/`.hdr`/`.exr` → **loaders**. Then check **animation** if it has clips, **lighting** if it's an HDR env, **materials** if textures look wrong.
- Mesh appearance question (color, reflectivity, transparency, normal maps) → **materials**, often with **textures** for color-space issues.
- "Make my mesh shiny / glossy / metallic" → **materials** (PBR `MeshStandardMaterial`).
- "Custom visual effect on a mesh", "wave effect on vertices", "fragment shader", "glitch/dissolve/fresnel/rim" → **shaders** (TSL).
- Raw GLSL, `ShaderMaterial`/`RawShaderMaterial`, `onBeforeCompile`, third-party shader chunks → **shaders-glsl** (legacy path).
- "Bloom", "DOF", "screen effect", "color grading", "post-process X" → **postprocessing** (and possibly **shaders** for the custom-pass body).
- "GPU compute", "particle simulation", "boids/cloth/physics on the GPU", "storage buffers", "`instancedArray`" → **compute** (WebGPU only).
- "Device lost / context lost", "GPU crash recovery", "requesting higher WebGPU limits or features" → **webgpu-runtime**.
- Click/hover/touch detection, "select an object in the scene" → **interaction**.
- Camera controls (orbit, fly, first-person, drag, gizmo) → **interaction**.
- "Why are my shadows wrong?" or "set up nice lighting" → **lighting** (often with **textures** for HDR IBL).
- Building shapes, modifying vertices, instancing thousands of copies → **geometry**.
- Animating a model from GLTF, blending walk/run, morph targets, smooth follow / spring physics → **animation**.
- Setting up a fresh scene, camera math, transforms, `Object3D` hierarchy, LOD, geometry merging → **fundamentals**.

If the user asks something this skill doesn't cover (physics engines, XR/AR, audio), say so plainly — better to point at the right library than to half-answer. For react-three-fiber abstractions above Three core (`<Canvas>`, hooks, drei, the pmndrs ecosystem), route to the sibling **`react-three-fiber-mastery`** skill. For raw WebGL2 / GLSL beneath the framework (hand-written pipeline, deep GLSL technique, framework-limit drop-downs), route to the **`webgl-mastery`** skill.

## Cross-Cutting Common Mistakes

These bite across every topic; topical mistakes live in each reference's own table.

| Mistake | Fix |
|---------|-----|
| `WebGPURenderer` scene renders nothing | Forgot `await renderer.init()` before the first render. Always async-initialize. |
| Loaded GLB looks washed out / overbright | Set `texture.colorSpace = THREE.SRGBColorSpace` on color/albedo/emissive maps. Data textures stay linear. GLTFLoader does this automatically; TextureLoader does not. |
| Animations don't play | Missing `mixer.update(delta)` in the render loop. See [animation.md](./references/animation.md). |
| Damped `OrbitControls` feel skippy | Missing `controls.update()` in the render loop (required whenever damping or autoRotate is on). |
| Post-processing effects don't appear | Render loop still calls `renderer.render()` instead of `composer.render()` / `postProcessing.render()`. |
| Memory grows when swapping models/textures | Every retired geometry/material/texture/render target needs `.dispose()`. Walk the model on teardown. |
| Resize handler updates camera and renderer but effects stay blurry | Composer / postProcessing also need `setSize(w, h)`. |
| Mixing `WebGLRenderer`-only APIs with `WebGPURenderer` and expecting them to work | Some legacy addons (`EffectComposer`, certain shader chunks) target WebGL. For WebGPU, migrate to the TSL equivalents in [postprocessing.md](./references/postprocessing.md) and [shaders.md](./references/shaders.md). |
| Raycaster picks nothing on a canvas that isn't full-screen | NDC coords must use `getBoundingClientRect()`, not `window.innerWidth/Height`. See [interaction.md](./references/interaction.md). |
| TSL node looks correct but the material doesn't update | Reassign to `material.colorNode = …` (don't mutate nodes in place) and set `material.needsUpdate = true`. |
| Transparency/blending looks wrong under `WebGPURenderer` after upgrading to r185 | r185 changed premultiplied-alpha handling ([#33369](https://github.com/mrdoob/three.js/issues/33369)). Set an opaque background: `scene.background = new THREE.Color(...)` or `renderer.setClearColor(color, 1)`. Use a transparent clear only when the canvas must blend with the HTML page. |
| Scene goes black only when devtools or browser automation probes the canvas | `canvas.getContext(type)` on a canvas whose renderer hasn't initialised yet **claims** the canvas's context type, so a pending renderer of the other type (`webgpu` probe vs WebGL2 renderer, or vice versa) fails when it later requests its own context. Probe context types only after the first frame has visibly rendered — on an initialised canvas, `getContext` with the same type returns the existing context and a different type returns `null`, both read-only. |

## Change-Signal Sources

Secondary leads for noticing when this skill's facts drift — the `skill-fact-check` routine consults them to discover *what* may have changed, then confirms every change against the primary sources above (official docs, release notes, the Migration Guide) before editing. These are leads, never authorities: don't cite them as the source for a correction.

- [threejsroadmap.com/blog](https://threejsroadmap.com/blog) — Daniel Greenheck's blog; tracks new releases, TSL/WebGPU shifts, and API changes (roughly 1–2 posts/month).
- [dgreenheck/webgpu-claude-skill](https://github.com/dgreenheck/webgpu-claude-skill) — Greenheck's focused WebGPU + TSL skill; a useful cross-check for compute, WGSL-interop, and device-loss specifics.

## See Also

- [`webgl-mastery` skill](https://github.com/CypherPoet/custom-agent-skills/blob/main/plugins/cypherpoet-webgl-kit/skills/webgl-mastery/SKILL.md) — sibling skill for raw WebGL2 / GLSL beneath Three.js (ships with this plugin).
- [`react-three-fiber-mastery` skill](https://github.com/CypherPoet/custom-agent-skills/blob/main/plugins/cypherpoet-react-three-fiber-kit/skills/react-three-fiber-mastery/SKILL.md) — sibling skill for the React layer above Three.js: `<Canvas>`, hooks, events, drei, and the pmndrs ecosystem.
- [Three.js documentation](https://threejs.org/docs/) — official API reference.
- [Three.js manual](https://threejs.org/manual/) — official tutorials.
- [Three.js examples](https://threejs.org/examples/) — runnable showcases of nearly every API.
- [TSL discussions](https://github.com/mrdoob/three.js/discussions) — Three.js Shading Language threads on GitHub.

## Primary Sources

- [Three.js releases](https://github.com/mrdoob/three.js/releases) — release channel; authoritative for versions.
- [Three.js Migration Guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide) — authoritative for API changes between releases.
- [Three.js documentation](https://threejs.org/docs/) — official API reference; authoritative for API syntax.
