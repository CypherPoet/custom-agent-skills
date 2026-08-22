# Migrating v8 → v9

The complete `@react-three/fiber` v8 → v9 migration: version and peer-dependency requirements, every breaking and behavioral change, the TypeScript type renames, and the ecosystem moves (three, zustand, React 19) that bite during the same upgrade. v9 + React 19 + drei 10 + three 0.185.x is the current stack; every v8/React-18 idiom below is labeled legacy.

> New-project setup on the current stack: see [../SKILL.md](../SKILL.md) and [canvas-and-project-setup.md](./canvas-and-project-setup.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Version Requirements](#version-requirements) | React 19 peer limits, reconciler compatibility across React minors, the frozen React 18 line, and the current three release pairing |
| [Ecosystem Pairing](#ecosystem-pairing) | Compatibility matrix and peer ranges for React, Fiber, Drei, postprocessing, Rapier, XR, Zustand, Leva, and three.js |
| [Migration Checklist](#migration-checklist) | Coordinated package upgrades followed by sweeps for removed types, buffer attributes, Canvas callbacks, StrictMode, color space, tests, and ecosystem changes |
| [Breaking and Behavioral Changes](#breaking-and-behavioral-changes) | `gl` constructor props, inherited StrictMode, removed automatic sRGB conversion, one-time Suspense side effects, `args` and `primitive` swap ordering, and React's `act` |
| [TypeScript Migration](#typescript-migration) | Canvas, intrinsic-element, and custom-element type replacements, React 19 module augmentation, and factory extension without global JSX declarations |
| [bufferAttribute Requires Constructor Args](#bufferattribute-requires-constructor-args) | Constructor-based arrays and item sizes, derived counts, and memoization to avoid reconstruction on each render |
| [New v9 Features](#new-v9-features) | Pooled loader instances, component-returning `extend`, asynchronous renderer factories, WebGPU registration and initialization, and the retained `state.gl` name |
| [v9.6: Stable Uniform References](#v96-stable-uniform-references) | Copy-in uniform semantics, stable material identities for hot reload and React Compiler, pierced value props, and fixed-shape per-frame updates |
| [Ecosystem Moves That Bite During Migration](#ecosystem-moves-that-bite-during-migration) | Second-UV channels and naming, addon import paths, Zustand shallow selectors and transient subscriptions, and React 19 refs as ordinary props |
| [The v10 Horizon](#the-v10-horizon) | Alpha-only WebGPU-first rendering, the `state.gl` to `state.renderer` rename, external frame scheduling, and paired drei alphas |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## Version Requirements

- **v9 requires React 19.** The peer range is `react >=19 <19.3` (same for `react-dom`). The upper cap exists because React minors can change the internal reconciler protocol — React 19.2 did.
- **fiber 9.5.0+ bundles its own reconciler**, so one fiber release spans React 19.0–19.2. Practical rule: skip the intermediate releases and install the latest 9.7.x directly. Pairing fiber 9.0–9.4 with React 19.2 produces reconciler-internals crashes.
- **The v8 line is frozen.** Last publish: 8.18.0 on 2025-02-19 — the same day 9.0.0 shipped. There is no maintenance branch. A project pinned to React 18 stays on fiber 8.18.0 + drei 9 permanently; every new feature and fix lands in v9 only.
- three peers are open-ended (`three >=0.156` for fiber, `>=0.159` for drei), so upgrade three to current (0.185.x) in the same pass.

## Ecosystem Pairing

Verified against the npm registry (2026-08-08):

| Package | Current major | react peer | fiber peer | three peer |
|---|---|---|---|---|
| @react-three/fiber | 9.7.x | >=19 <19.3 | — | >=0.156 |
| @react-three/drei | 10.7.x | ^19 | ^9.0.0 | >=0.159 |
| @react-three/postprocessing | 3.0.x | ^19.0 | ^9.0.0 | >=0.156.0 |
| @react-three/rapier | 2.2.x | ^19 | ^9.0.4 | >=0.159.0 |
| @react-three/xr | 6.6.x | >=18 | >=8 | * |
| zustand | 5.0.x | >=18 | — | — |
| leva | 0.10.x | ^18 \|\| ^19 | — | — |

Read the table as one hard rule: **fiber 9, drei 10, postprocessing 3, and rapier 2 all require React 19** — they move as a block. `@react-three/xr` is the permissive outlier (fiber >=8, react >=18, any three) and works on either side of the migration.

Legacy pairing (label any such code as legacy): React 18 ↔ fiber 8.18.0 ↔ drei 9, with the previous majors of the companions (@react-three/postprocessing 2.x, @react-three/rapier 1.x). drei 10 cannot be used with fiber 8/React 18 — its peers hard-require fiber ^9 and react ^19.

## Migration Checklist

```bash
npm install react@^19.2 react-dom@^19.2
npm install three@^0.185.0 @types/three@^0.185.0
npm install @react-three/fiber@^9 @react-three/drei@^10
npm install @react-three/postprocessing@^3 @react-three/rapier@^2   # if used
```

Then sweep the codebase in this order:

1. TypeScript types — `Props`/`MeshProps`/`Object3DNode`/global JSX augmentation are gone ([TypeScript Migration](#typescript-migration)).
2. `<bufferAttribute>` usage — `count`/`array`/`itemSize` props become `args` ([bufferAttribute Requires Constructor Args](#bufferattribute-requires-constructor-args)).
3. Canvas `gl` callbacks — the argument changed from canvas to constructor props ([Breaking and Behavioral Changes](#breaking-and-behavioral-changes)).
4. Remove any duplicate `<StrictMode>` inside `<Canvas>` — it is now inherited.
5. Set `colorSpace` manually on color textures fed to custom materials/shaders.
6. Test files — `act` now comes from `react`.
7. Ecosystem sweeps: `uv2` → `uv1`, `three/examples/jsm` → `three/addons`, zustand 4 → 5, drop `forwardRef` where convenient ([Ecosystem Moves](#ecosystem-moves-that-bite-during-migration)).

## Breaking and Behavioral Changes

### gl Callback Receives Constructor Props

In v8 the `gl` callback received the canvas element. In v9 it receives the default constructor props (canvas included), and may return a Promise (async renderer constructors — see [New v9 Features](#new-v9-features)):

```jsx
import * as THREE from "three";

// v8 (legacy): callback received the canvas element
<Canvas gl={(canvas) => new THREE.WebGLRenderer({ canvas, antialias: true })} />

// v9: callback receives constructor props — spread them into your renderer
<Canvas gl={(props) => new THREE.WebGLRenderer({ ...props, antialias: true })} />
```

### StrictMode Is Inherited

In v8, `<Canvas>` created a detached React root, so an app-level `<StrictMode>` never reached the scene — you had to redeclare it inside the Canvas. v9 inherits StrictMode from the parent renderer:

```jsx
// v8 (legacy): StrictMode had to be redeclared inside Canvas to cover the scene
<StrictMode>
  <Canvas>
    <StrictMode>
      <Scene />
    </StrictMode>
  </Canvas>
</StrictMode>

// v9: declare once at the app root — it now covers the scene too
<StrictMode>
  <Canvas>
    <Scene />
  </Canvas>
</StrictMode>
```

This is breaking in practice: scenes that never ran under StrictMode before now do, so dev-mode double-invoked effects will surface latent bugs (effects without cleanup, non-idempotent mounts). Remove any duplicate inner `<StrictMode>`.

### Automatic sRGB Texture Conversion Removed

v8 assumed every texture prop was a color texture and force-annotated it as sRGB — corrupting data textures (normal, roughness, displacement maps). v9 matches vanilla three.js: built-in materials annotate their color slots automatically; everything else is left untouched.

```jsx
import * as THREE from "three";
import { useLoader } from "@react-three/fiber";

const texture = useLoader(THREE.TextureLoader, "/diffuse.jpg");

// Built-in material color slots: still handled automatically
<meshStandardMaterial map={texture} />

// Custom materials / shader uniforms: annotate color textures manually
texture.colorSpace = THREE.SRGBColorSpace;
```

The declarative form works too — `colorSpace` is a plain property, so set it as a JSX prop on the element that holds the texture (e.g. `<texture ... colorSpace={THREE.SRGBColorSpace} />`). Data textures need no annotation — leaving them linear is the fix v9 delivers.

### Suspense Side Effects Fire Once

In v8, `attach` and constructor side effects could fire repeatedly — without cleanup — while a tree suspended. v9 initializes them only when the tree actually connects to the screen. If anything relied on those double-firings (mount counters, work done per suspension retry), that behavior is gone.

### args / primitive Swap Ordering

Changing `args` (which reconstructs the object) or swapping the `object` on `<primitive>` now updates in the correct order relative to structured children, and a three.js object shared by multiple `<primitive>` mounts no longer updates out of order. No code change is usually needed — but re-test any code that accidentally depended on the old ordering.

### act Comes From React

```jsx
// v8 (legacy)
import { act } from "@react-three/fiber";

// v9
import { act } from "react";
```

## TypeScript Migration

Every removed type has a direct replacement:

| v8 type (removed) | v9 replacement |
|---|---|
| `Props` (Canvas props) | `CanvasProps` |
| `MeshProps`, `GroupProps`, … (per-element prop types) | `ThreeElements["mesh"]`, `ThreeElements["group"]`, … |
| `Node`, `Object3DNode<T, P>`, `BufferGeometryNode`, `MaterialNode`, `LightNode` | `ThreeElement<typeof T>` |
| global `JSX.IntrinsicElements` augmentation | `declare module "@react-three/fiber"` augmentation of `ThreeElements` |

React 19 deprecated the global JSX namespace, which is why the augmentation target moved. Before/after for a custom element:

```tsx
// v8 (legacy)
import { ReactThreeFiber, extend } from "@react-three/fiber";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

extend({ OrbitControls });

declare global {
  namespace JSX {
    interface IntrinsicElements {
      orbitControls: ReactThreeFiber.Object3DNode<OrbitControls, typeof OrbitControls>;
    }
  }
}
```

```tsx
// v9
import { extend, type ThreeElement } from "@react-three/fiber";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

extend({ OrbitControls });

declare module "@react-three/fiber" {
  interface ThreeElements {
    orbitControls: ThreeElement<typeof OrbitControls>;
  }
}
```

Component prop types:

```tsx
// v8 (legacy)
import type { MeshProps } from "@react-three/fiber";
type BoxProps = MeshProps & { active: boolean };

// v9
import type { ThreeElements } from "@react-three/fiber";
type BoxProps = ThreeElements["mesh"] & { active: boolean };
```

Or skip the augmentation entirely with the v9 factory form of `extend` — types are inferred and nothing leaks into the JSX namespace (see [New v9 Features](#new-v9-features)). Full typing patterns live in [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md).

## bufferAttribute Requires Constructor Args

v8 code set `count`/`array`/`itemSize` as props after construction. In v9, `THREE.BufferAttribute` must be built from constructor `args` (count derives from `array.length / itemSize`):

```jsx
// v8 (legacy) — renders an empty/broken geometry under v9
<bufferAttribute
  attach="attributes-position"
  count={positions.length / 3}
  array={positions}
  itemSize={3}
/>

// v9
<bufferAttribute attach="attributes-position" args={[positions, 3]} />
```

Remember the general rule: changing `args` reconstructs the object, so memoize the typed array (`useMemo`) rather than recreating it every render.

## New v9 Features

### useLoader Accepts Loader Instances

Pass a preconfigured instance instead of the class — one shared loader (pooling) instead of per-class-and-config internals:

```jsx
import { useLoader } from "@react-three/fiber";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("/draco-gltf/");
const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);

function Model() {
  const gltf = useLoader(gltfLoader, "/model.glb");
  return <primitive object={gltf.scene} />;
}
```

The class form still works (with the extensions callback for configuration) — see [loading-assets.md](./loading-assets.md).

### Factory extend

`extend(Class)` now returns a component directly. Backwards compatible with the catalog form; recommended for libraries because nothing is registered in the global JSX catalog:

```jsx
import { extend, useThree } from "@react-three/fiber";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const Controls = extend(OrbitControls);

function Scene() {
  const camera = useThree((state) => state.camera);
  const gl = useThree((state) => state.gl);
  return <Controls args={[camera, gl.domElement]} />;
}
```

### Async gl and WebGPU

The `gl` callback may return a Promise, which makes async renderer constructors possible:

```tsx
import * as THREE from "three/webgpu";
import { Canvas, extend, type ThreeToJSXElements } from "@react-three/fiber";

declare module "@react-three/fiber" {
  interface ThreeElements extends ThreeToJSXElements<typeof THREE> {}
}

extend(THREE as any);

export function App() {
  return (
    <Canvas
      gl={async (props) => {
        const renderer = new THREE.WebGPURenderer(props as any);
        await renderer.init();
        return renderer;
      }}
    >
      {/* scene */}
    </Canvas>
  );
}
```

Note the state field is still `state.gl` in v9 even when it holds a `WebGPURenderer` — the `state.renderer` rename is a v10 change ([The v10 Horizon](#the-v10-horizon)).

## v9.6: Stable Uniform References

Since v9.6.0 ("Sunset X", 2026-04-13), a `uniforms` object passed as a prop to a shader material is **copied into** the material's existing uniforms instead of replacing them — the same copy semantics R3F applies to `position`/`rotation` props. Consequences:

- `material.uniforms` keeps a stable identity across renders. Don't expect the material to hold the exact object you passed.
- Fixes HMR uniform desync and plays correctly with React Compiler auto-memoization.
- Individual uniform values can be driven inline via piercing:

```jsx
<shaderMaterial
  vertexShader={vertexShader}
  fragmentShader={fragmentShader}
  uniforms={{ uTime: { value: 0 } }}
  uniforms-uTime-value={elapsed}
/>
```

Treat the uniform *set* as fixed at construction (standard three.js shader practice — the compiled program's uniforms don't change shape); update values per frame via a ref inside `useFrame`, not via React state. drei's `shaderMaterial` flat-prop workflow (`ref.current.uTime = x`) is unaffected. Full shader workflow: [shaders-and-custom-materials.md](./shaders-and-custom-materials.md).

## Ecosystem Moves That Bite During Migration

These are not fiber changes, but they land in the same upgrade window and produce the most confusing symptoms.

### three r151/r152: UV channels and uv2 → uv1

three **r151** stopped `aoMap`/`lightMap` from auto-reading a second UV set — maps now select their UV set via `texture.channel` (default `0` = the base `uv`, `1` = the second set) — and **r152** renamed the second UV attribute `uv2` → `uv1`:

```jsx
// Legacy (three < r151): aoMap auto-read the `uv2` attribute
geometry.setAttribute("uv2", geometry.attributes.uv);

// Current (three r151+): a bake sharing the base UVs needs nothing (channel 0).
// For a separate AO/lightmap layout, author `uv1` and select it:
geometry.setAttribute("uv1", aoUvAttribute); // BufferAttribute of the AO UVs
material.aoMap.channel = 1;
material.needsUpdate = true; // if the material already rendered — a channel change needs a recompile
```

Symptom of a half-done migration: you rename `uv2` → `uv1` but forget `channel = 1`, so `aoMap` reads the base `uv` and the second set is ignored.

### three/examples/jsm → three/addons

```jsx
// Legacy
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

// Current
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
```

Prefer drei wrappers where they exist ([staging-and-drei.md](./staging-and-drei.md) catalogs them).

### zustand 4 → 5

Two API moves break R3F's common transient-state patterns:

```jsx
// v4 (legacy): shallow comparison as the second argument
import { shallow } from "zustand/shallow";
const { x, y } = useStore((s) => ({ x: s.x, y: s.y }), shallow);

// v5: wrap the selector with useShallow
import { useShallow } from "zustand/react/shallow";
const { x, y } = useStore(useShallow((s) => ({ x: s.x, y: s.y })));
```

```jsx
// v5: store.subscribe(selector, callback) requires the subscribeWithSelector middleware
import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

const useStore = create(subscribeWithSelector((set) => ({ health: 100 })));

useStore.subscribe(
  (s) => s.health,
  (health) => {
    // transient update — runs outside React, pair with ref mutation
  }
);
```

Without the middleware, `subscribe` only accepts a single listener that receives the whole state. `getState()` reads inside `useFrame` are unchanged and remain the right per-frame pattern ([performance.md](./performance.md)).

### React 19: ref Is a Prop

`forwardRef` is unnecessary in new code — `ref` arrives as a regular prop:

```jsx
// Legacy (React 18)
const Box = forwardRef((props, ref) => <mesh ref={ref} {...props} />);

// React 19
function Box({ ref, ...props }) {
  return <mesh ref={ref} {...props} />;
}
```

Existing `forwardRef` code still works — don't churn it mechanically, but stop writing new instances.

## The v10 Horizon

v10 exists only as alphas on npm (10.0.0-alpha.x; alpha.1 released 2026-01-17). Known direction:

- **WebGPU first-class**: supports both `WebGLRenderer` and `WebGPURenderer`; `state.gl` is renamed to **`state.renderer`**.
- **New scheduler** with advanced `useFrame` scheduling, including `useFrame` usable outside `<Canvas>`.
- **drei v11 alphas** pair with fiber 10 alphas.

Teach and write v9 as current: `state.gl` is correct today, `state.renderer` does not exist in v9, and alpha APIs may still change. Keep `useThree` access behind selectors (`useThree((s) => s.gl)`) so the eventual rename is a one-line sweep.

## Common Mistakes

| Mistake | Fix |
|---|---|
| `npm install @react-three/fiber@9` on a React 18 app fails with `ERESOLVE` (peer `react >=19 <19.3`) | Upgrade React to 19 first. A project staying on React 18 remains on the frozen legacy line: fiber 8.18.0 + drei 9. |
| Upgraded to React 19.2 but fiber crashes with reconciler-internals errors | fiber 9.0–9.4 targets React 19.0–19.1 only; install 9.5+ (bundles its own reconciler; 9.7.x is current). |
| drei 10 won't install / breaks on a fiber 8 project | drei 10 hard-requires fiber ^9 + react ^19; fiber 8 stays with drei 9. |
| Geometry from `<bufferAttribute count array itemSize />` renders nothing after upgrade | v9 builds attributes from constructor args: `<bufferAttribute attach="attributes-position" args={[array, itemSize]} />`. |
| Color textures look washed out or too dark in custom shaders after upgrade | v9 no longer force-annotates texture props as sRGB; set `texture.colorSpace = THREE.SRGBColorSpace` on color maps fed to custom materials. Data textures stay linear — leave them. |
| `gl={(canvas) => new WebGLRenderer({ canvas })}` throws or renders black | The callback now receives constructor props: `gl={(props) => new WebGLRenderer({ ...props })}`. |
| TS: `no exported member 'MeshProps'` / `'Object3DNode'` / `'Props'` | `ThreeElements["mesh"]` for element props, `ThreeElement<typeof X>` for custom elements, `CanvasProps` for Canvas. |
| Custom element JSX types stopped resolving despite a `JSX.IntrinsicElements` augmentation | React 19 dropped the global JSX namespace; augment `interface ThreeElements` via `declare module "@react-three/fiber"`, or use factory `extend`. |
| Effects inside `<Canvas>` suddenly double-invoke in dev after upgrading | Expected: v9 inherits the app-level `<StrictMode>` into the scene. Remove any duplicate `<StrictMode>` inside `<Canvas>` and fix non-idempotent effects. |
| `aoMap`/`lightMap` silently has no effect on current three | Maps default to channel 0 (the base `uv`); for a separate AO set, author `uv1` and set `material.aoMap.channel = 1` (renamed from `uv2` in three r152). |
| Imports from `three/examples/jsm/...` fail to resolve | Use `three/addons/...` (or the drei wrapper). |
| zustand v5: `useStore(selector, shallow)` type error | Wrap the selector: `useStore(useShallow(selector))` from `zustand/react/shallow`. |
| zustand v5: `store.subscribe(selector, cb)` fires with the whole state | Selector-based subscribe requires the `subscribeWithSelector` middleware. |
| Tests fail on `import { act } from "@react-three/fiber"` | v9: `import { act } from "react"`. |
| Code copied from v10 alpha docs reads `state.renderer` | v9 is current — the field is `state.gl`; the rename lands in v10. |

## See Also

- [canvas-and-project-setup.md](./canvas-and-project-setup.md) — Canvas props, `gl` configuration, WebGPU setup on the current stack.
- [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md) — `ThreeElements`/`ThreeElement` typing, `args`, `attach`, `extend` in depth.
- [shaders-and-custom-materials.md](./shaders-and-custom-materials.md) — drei `shaderMaterial` workflow and uniform handling post-v9.6.
- [loading-assets.md](./loading-assets.md) — `useLoader` (class and instance forms), Draco, gltfjsx.
- [../SKILL.md](../SKILL.md) — version pairing summary and setup.
- Official v9 migration guide: https://r3f.docs.pmnd.rs/tutorials/v9-migration-guide
