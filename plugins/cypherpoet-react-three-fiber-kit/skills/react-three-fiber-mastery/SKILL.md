---
name: react-three-fiber-mastery
description: >
  Use whenever the user is working with React Three Fiber or the pmndrs
  ecosystem: @react-three/fiber, drei, @react-three/postprocessing, rapier,
  gltfjsx, leva. Trigger on <Canvas>, useFrame, useThree, useGLTF, drei helpers,
  or "three.js in React / Next.js / Expo" — even when the library is never
  named. Covers R3F v9 + React 19. For plain Three.js questions beneath the
  React layer, defer to threejs-mastery.
---

# React Three Fiber Mastery

## Overview

Comprehensive React Three Fiber (R3F) reference covering modern best practices. The body of this file is shared setup, cross-cutting laws, a topic routing table, and the mistakes that bite across every topic. Topical depth lives in [references/](./references/) — one file per topic, each ending in its own Common Mistakes table.

R3F is a React **renderer** for three.js — not a wrapper or binding. Every three.js object is available as camelCase JSX with no feature lag and no per-frame overhead; React's scheduler is only involved when the component tree changes, never in the render loop. The discipline that follows from this is the core of the skill: **declare structure in JSX, mutate motion via refs in `useFrame`**.

**Going below the reconciler?** For Three.js itself — materials theory, lighting/IBL, GLTF internals, TSL/GLSL shading technique, `WebGPURenderer` specifics — use the sibling **`threejs-mastery`** skill (the `cypherpoet-threejs-kit` dependency). This skill stays at the React layer: the reconciler, hooks, events, drei, and the pmndrs ecosystem.

## When to Use

Trigger this skill when the user:

- Mentions React Three Fiber, R3F, `@react-three/fiber`, drei, or any `@react-three/*` package.
- Uses `<Canvas>`, `useFrame`, `useThree`, `useLoader`, `useGLTF`, `useTexture`, `useAnimations`, or JSX like `<mesh>` / `<boxGeometry>` / `<meshStandardMaterial>`.
- Asks about 3D rendering inside a React, Next.js, Expo, or React Native app.
- Describes a problem in those terms without naming the library — "my spinning cube stutters when state updates", "model won't load in my React scene", "TypeScript can't find my custom element", "OrbitControls fight my gizmo".
- Runs `npx gltfjsx`, or works with `@react-three/postprocessing`, `@react-three/rapier`, `@react-spring/three`, leva, or zustand-driven 3D state.
- Migrates an R3F v8 / React 18 codebase forward.

## Setup

Current stack: **React 19 + `@react-three/fiber` v9 + drei v10** on three ≥ 0.159. Install:

```bash
npm install three @types/three @react-three/fiber @react-three/drei
```

The canonical scene — declarative structure, ref-mutation animation, Suspense for assets:

```jsx
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Environment } from "@react-three/drei";
import { Suspense, useRef } from "react";

function SpinningBox(props) {
  const meshRef = useRef(null);
  useFrame((state, delta) => {
    meshRef.current.rotation.y += delta;      // mutate — never setState here
  });
  return (
    <mesh ref={meshRef} castShadow {...props}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="hotpink" />
    </mesh>
  );
}

export default function App() {
  return (
    <Canvas shadows camera={{ position: [3, 3, 5], fov: 50 }}>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={1.2} castShadow />
      <Suspense fallback={null}>
        <SpinningBox position={[0, 0.5, 0]} />
        <Environment preset="city" />
      </Suspense>
      <mesh rotation-x={-Math.PI / 2} receiveShadow>
        <planeGeometry args={[10, 10]} />
        <meshStandardMaterial color="#999" />
      </mesh>
      <OrbitControls makeDefault enableDamping />
    </Canvas>
  );
}
```

`<Canvas>` installs sensible defaults — sRGB output, ACES tone mapping, `dpr` clamped to `[1, 2]`, a `PerspectiveCamera` at `[0, 0, 5]`, antialiasing — and resizes to **fill its parent element**, so the parent must have real dimensions. Full prop reference: [canvas-and-project-setup.md](./references/canvas-and-project-setup.md).

## Starting a New Project

### Verify the Latest Release

The pmndrs ecosystem moves fast. Before pinning versions, check the current releases:

```bash
npm view @react-three/fiber version
npm view @react-three/drei version
npm view three version
```

**Audit baseline:** this skill's content was last verified against **@react-three/fiber 9.6.1, @react-three/drei 10.7.7, three 0.185.1 (r185), React 19.2** (2026-07-03). When refreshing for newer releases, diff the [fiber releases](https://github.com/pmndrs/react-three-fiber/releases) and [drei releases](https://github.com/pmndrs/drei/releases) from that baseline instead of re-checking everything — then bump this line (versions + date) as the final step of the audit.

### Version Pairing

The ecosystem majors move in lockstep, and mixing them is the #1 install-time failure:

| React | fiber | drei | Status |
|-------|-------|------|--------|
| 19.x | v9 | v10 | **Current** — all core `@react-three/*` packages require this line |
| 18.x | v8 | v9 | Frozen — fiber 8.18.0 (2025-02-19) was the final v8 release |

`@react-three/postprocessing` v3 and `@react-three/rapier` v2 also require fiber 9 / React 19. `@react-three/xr` is the one permissive outlier (`fiber >=8`, `react >=18`). A React 18 project cannot use drei 10 — upgrade React first or stay on the frozen v8/v9 pair. Details and the full migration path: [migration-v8-to-v9.md](./references/migration-v8-to-v9.md).

R3F **v10 is in alpha** (WebGPU first-class, `state.gl` → `state.renderer`, new scheduler). Teach and write v9 — flag v10 only as the horizon.

## Shared Laws

These cross every topic. Internalize them once.

### Never setState in the Render Loop

React state is for structure and slow/reactive data. Anything that changes per frame is a **mutation on a ref** inside `useFrame`:

```jsx
// ❌ re-renders the component tree 60×/s
useFrame(() => setX((x) => x + 0.1));

// ✅ mutates the three.js object directly
useFrame((state, delta) => (meshRef.current.position.x += delta));
```

The same law bans binding rapidly-changing store state to JSX props — read it imperatively instead: `useFrame(() => (ref.current.position.x = useStore.getState().x))`. See [performance.md](./references/performance.md) for the full doctrine.

### Deltas, Not Fixed Increments

Advance animation by `delta` (seconds since last frame) so speed is refresh-rate independent — `rotation.y += 0.01` runs twice as fast on a 120 Hz display:

```jsx
useFrame((state, delta) => {
  meshRef.current.rotation.y += 1.5 * delta;    // radians per second
});
```

### No Allocation in the Loop

`new THREE.Vector3()` inside `useFrame` allocates 60×/s and triggers GC hitches. Hoist reusable temps:

```jsx
const targetVec = new THREE.Vector3();
useFrame(() => {
  meshRef.current.position.lerp(targetVec.set(x, y, z), 0.1);
});
```

### Suspense Wraps Every Loader

`useLoader`, `useGLTF`, `useTexture`, and `useEnvironment` **suspend**. Anything using them needs a `<Suspense>` boundary above it, and load errors surface through a React error boundary — not try/catch. See [loading-assets.md](./references/loading-assets.md).

### Reconstruction vs Mutation

`args` maps to the constructor — **changing `args` destroys and rebuilds the object**. Props map to `.set()`-style assignment — cheap. Keep `args` stable (`useMemo` the array if computed) and animate via props or ref mutation, never by cycling constructor arguments.

### Disposal Is Automatic — Opt Out for Shared Assets

Unmounting a subtree auto-disposes its geometries/materials/textures. When meshes share module-scope or loader-cached assets (every gltfjsx component does), put `dispose={null}` on the root group so unmounting one instance doesn't destroy the shared GPU resources of the others.

### Hooks Live Inside the Canvas

`useFrame`, `useThree`, `useLoader`, and every drei hook read R3F context — they throw outside `<Canvas>`. State that must cross the boundary goes through a store (zustand) or tunnel, not through hoisting the hook.

## Topics

| Topic | Reference | What it covers |
|-------|-----------|----------------|
| Canvas & project setup | [canvas-and-project-setup.md](./references/canvas-and-project-setup.md) | Canvas props/defaults, Vite/Next.js/React Native, WebGPU, custom roots |
| Objects, JSX & TypeScript | [objects-jsx-and-typescript.md](./references/objects-jsx-and-typescript.md) | `args`, shorthand/pierced props, `attach`, `primitive`, `extend`, `ThreeElements` typing |
| Hooks | [hooks.md](./references/hooks.md) | `useThree` state/selectors, `useFrame` priorities, `useLoader` caching, `useGraph` |
| Events & interaction | [events-and-interaction.md](./references/events-and-interaction.md) | Pointer events, occlusion/bubbling, pointer capture, controls catalog, keyboard/scroll |
| Animation | [animation.md](./references/animation.md) | `useFrame` patterns, `useAnimations`/crossfades, morphs, bones, springs, `Float`/`Trail` |
| Loading assets | [loading-assets.md](./references/loading-assets.md) | `useGLTF`, gltfjsx, Draco, textures & color space, Suspense/progress/error UX |
| Performance | [performance.md](./references/performance.md) | The pitfalls doctrine, on-demand rendering, instancing, regression, zustand discipline |
| Staging & drei | [staging-and-drei.md](./references/staging-and-drei.md) | Lights/shadows, `Environment`/`Stage`/`ContactShadows`, the drei helper catalog |
| Shaders & custom materials | [shaders-and-custom-materials.md](./references/shaders-and-custom-materials.md) | drei `shaderMaterial`, uniforms, HMR key, `onBeforeCompile`, instanced attributes |
| Post-processing | [postprocessing.md](./references/postprocessing.md) | `EffectComposer`, Bloom + emissive pairing, selective effects, custom effects |
| Physics | [physics-rapier.md](./references/physics-rapier.md) | `RigidBody`, colliders, forces, sensors, joints, instanced bodies, character control |
| Migration v8 → v9 | [migration-v8-to-v9.md](./references/migration-v8-to-v9.md) | React 19 pairing, breaking changes, TS type renames, ecosystem co-migrations |

## Routing Rules

When the question fits cleanly into one topic, load that reference and answer from it. Non-trivial scenes usually span two or three — load each in turn.

Quick routing cues:

- Fresh project, `<Canvas>` props, Next.js/SSR, React Native/Expo, "blank canvas", WebGPU → **canvas-and-project-setup**.
- `args`, `attach`, `<primitive>`, `extend`, TS errors on JSX elements or removed types (`Object3DNode`, `MeshProps`) → **objects-jsx-and-typescript**.
- `useThree` fields, `useFrame` ordering/priority, `useLoader` semantics → **hooks**.
- Click/hover/drag, raycast filtering, camera controls, `TransformControls`, keyboard movement, scroll-driven scenes → **events-and-interaction**.
- Anything moving over time — GLTF clips, crossfading, springs, smooth-follow, floating idle motion → **animation**.
- `.glb`/`.gltf`/HDR/texture loading, gltfjsx, Suspense/progress bars, washed-out or too-dark textures → **loading-assets**.
- Jank, stutter on interaction, too many draw calls, "re-renders when score updates", frame budget → **performance**.
- "Make it look good" — lighting, shadows, environments, reflections, or "is there a drei helper for X" → **staging-and-drei**.
- Custom GLSL, uniforms from React, shader HMR, patching built-in materials → **shaders-and-custom-materials**.
- Bloom/glow, depth of field, outlines, AO, color grading → **postprocessing**.
- Gravity, collisions, joints, triggers, character controllers → **physics-rapier**.
- Upgrading from v8/React 18, peer-dependency conflicts, renamed TS types → **migration-v8-to-v9**.

Out of scope here, in scope next door: three.js fundamentals beneath the reconciler (PBR/material theory, lighting/IBL technique, GLTF format internals, TSL, raw `WebGPURenderer`) → the sibling **`threejs-mastery`** skill; raw WebGL2/GLSL beneath that → **`webgl-mastery`**. XR/AR sessions (`@react-three/xr`) and the leva debug GUI are named in [migration-v8-to-v9.md](./references/migration-v8-to-v9.md) for version pairing only — for their usage, consult the [official @react-three/xr docs](https://pmndrs.github.io/xr/docs/) and the [leva docs](https://github.com/pmndrs/leva).

## Cross-Cutting Common Mistakes

These bite across every topic; topical mistakes live in each reference's own table.

| Mistake | Fix |
|---------|-----|
| Canvas renders nothing / has zero height | `<Canvas>` fills its parent — give the parent element explicit dimensions (`height: 100vh` or a sized flex/grid cell). |
| `npm install` fails with ERESOLVE on react peer dep | Version pairing: fiber 9 / drei 10 need React 19. On React 18 you're limited to the frozen fiber 8 / drei 9 line. See [migration-v8-to-v9.md](./references/migration-v8-to-v9.md). |
| Scene stutters whenever UI state changes | setState is re-rendering the canvas tree. Isolate animated components, mutate via refs in `useFrame`, read stores with `getState()` in the loop. See [performance.md](./references/performance.md). |
| "R3F: Hooks can only be used within the Canvas component!" | `useThree`/`useFrame`/loader hooks must be in a component rendered *inside* `<Canvas>`. Move the hook down, or bridge state through a store. |
| Animation speed differs between displays | Frame-locked increments. Multiply by `delta`: `ref.current.rotation.y += speed * delta`. |
| Periodic hitches during smooth animation | Allocation inside `useFrame` (e.g. `new THREE.Vector3()` per frame). Hoist temps outside the callback. |
| Model/texture never appears; no error | Missing `<Suspense>` boundary above the component calling `useGLTF`/`useLoader`/`useTexture`. |
| Custom shader texture looks washed out (v9) | v9 removed automatic sRGB conversion of texture props. Set `texture.colorSpace = THREE.SRGBColorSpace` (or `texture-colorSpace={...}` in JSX) for color maps fed to custom materials. See [loading-assets.md](./references/loading-assets.md). |
| TS: augmenting `JSX.IntrinsicElements` stopped working after upgrade | v9 removed the global-JSX pattern. Augment `ThreeElements` via `declare module '@react-three/fiber'` with `ThreeElement<typeof X>`, or use factory `extend`. See [objects-jsx-and-typescript.md](./references/objects-jsx-and-typescript.md). |
| `<bufferAttribute count={...} array={...} itemSize={...}>` silently broken | v8 prop form. In v9, pass constructor args: `<bufferAttribute attach="attributes-position" args={[array, itemSize]} />`. |
| Mesh flashes/resets when a dimension changes | Changing `args` reconstructs the object (constructor semantics). Mutate `scale`/props for animation; keep `args` stable with `useMemo`. |
| Scene frozen with `frameloop="demand"` | Nothing requests frames. Call `invalidate()` after imperative mutations (drei controls do it automatically). See [performance.md](./references/performance.md). |
| `OrbitControls` fights `TransformControls`/drag gizmos | Give orbit `makeDefault`, and the transform gizmo will pause it while dragging. See [events-and-interaction.md](./references/events-and-interaction.md). |
| Unmounting one model instance breaks the others | Shared loader-cached assets were auto-disposed. Put `dispose={null}` on the shared root (gltfjsx does this for you). |

## See Also

- [`threejs-mastery` skill](https://github.com/CypherPoet/custom-agent-skills/blob/main/plugins/cypherpoet-threejs-kit/skills/threejs-mastery/SKILL.md) — sibling skill for Three.js itself beneath the reconciler (ships with this plugin).
- [React Three Fiber documentation](https://r3f.docs.pmnd.rs/) — official docs.
- [drei documentation](https://drei.docs.pmnd.rs/) — the helper catalog, searchable.
- [pmndrs market](https://market.pmnd.rs/) — free models/HDRIs for prototyping.
- [gltfjsx](https://github.com/pmndrs/gltfjsx) — GLTF → JSX component generator (web UI: https://gltf.pmnd.rs/).
- [fiber releases](https://github.com/pmndrs/react-three-fiber/releases) — release notes; check when APIs seem missing.

## Primary Sources

- [React Three Fiber documentation](https://r3f.docs.pmnd.rs/) — authoritative for fiber API syntax.
- [fiber releases](https://github.com/pmndrs/react-three-fiber/releases) — release channel; authoritative for versions.
- [drei documentation](https://drei.docs.pmnd.rs/) — authoritative for helper API syntax.
- [drei releases](https://github.com/pmndrs/drei/releases) — release channel; authoritative for drei versions.
