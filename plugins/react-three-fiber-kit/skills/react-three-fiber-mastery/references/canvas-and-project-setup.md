# Canvas & Project Setup

How to get a React Three Fiber project running and configure the `<Canvas>` root: install commands and version pairing, the full Canvas prop surface, the render defaults it installs, bundler setup (Vite/Next.js/React Native), WebGPU, custom tree-shakable roots, and StrictMode behavior in v9. Skill overview: [../SKILL.md](../SKILL.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Install & Version Pairing](#install--version-pairing) | Fiber, React, drei, and three compatibility ranges, the frozen React 18 line, and the verified current stack |
| [Minimal App](#minimal-app) | Canvas-owned renderer, scene, and camera creation, three.js JSX mapping, ref-driven animation, wrapper props, and required parent sizing |
| [Canvas Props](#canvas-props) | Renderer, camera, scene, shadow, raycast, frame, resize, color, event, lifecycle, and fallback configuration plus the v9 asynchronous renderer callback |
| [Render Defaults](#render-defaults) | Renderer settings, modern color and tone-mapping pipeline, camera, scene, raycaster, shadow type, and clamped pixel ratio installed by Canvas |
| [Camera Setup](#camera-setup) | Perspective, orthographic, and supplied cameras, constructor-time props, automatic projection updates, manual sizing, and runtime default-camera replacement |
| [Shadows](#shadows) | Shadow-map algorithm selection, required light and mesh flags, custom map properties, and the boundary with drei’s soft-shadow helpers |
| [Frameloop](#frameloop) | Continuous, demand, and manually advanced rendering, coalesced invalidation requests, and control integration |
| [Color Management Flags](#color-management-flags) | Independent legacy input, linear output, and tone-mapping switches, practical recipes, and v9 custom-texture color-space handling |
| [Event Wiring](#event-wiring) | Canvas-level event configuration (per-object handlers and the raycast/propagation model live in events-and-interaction.md) |
| [onCreated & Fallback](#oncreated--fallback) | `onCreated` root-state access and graceful handling when WebGL initialization fails |
| [Bundler Setup](#bundler-setup) | Zero-config Vite, Next.js three transpilation and client-only rendering, and React Native’s Expo GL entry point and Metro asset extensions |
| [WebGPU](#webgpu) | Async WebGPU renderer initialization and JSX registration, WebGL fallback and backend detection, TSL shading, swallowed failures, duplicate factories, manual disposal, and the v10 state rename |
| [Custom Tree-Shakable Roots](#custom-tree-shakable-roots) | Selective `extend`, async `createRoot` configuration, manual event and resize wiring, rendering, and unmount disposal |
| [StrictMode in v9](#strictmode-in-v9) | v9 inherits `<StrictMode>` from the parent React tree across the renderer boundary |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## Install & Version Pairing

```bash
npm install three @types/three @react-three/fiber
npm install @react-three/drei        # optional but near-universal helper library
```

| Fiber major | React | Status |
|---|---|---|
| `@react-three/fiber@9` (9.7.x) | React 19 (peer `>=19 <19.3`) | **Current** |
| `@react-three/fiber@8` | React 18 | Frozen — last release 8.18.0 (2025-02-19), no maintenance line |

Version rules that decide whether an install works at all:

- **fiber@9 ↔ react@19, fiber@8 ↔ react@18.** No cross-pairing.
- The `<19.3` upper cap exists because React 19.2 changed reconciler internals; fiber 9.5.0+ bundles its own reconciler to span React 19.0–19.2. Keep fiber current when bumping React patch minors.
- **drei@10 hard-requires fiber ^9 + react ^19.** drei 10 cannot be used with fiber 8 / React 18.
- three: fiber 9.7.x accepts `three >=0.156` (open-ended); drei 10.7.x requires `>=0.159`.
- Verified current stack (2026-08): react 19.2.x · @react-three/fiber 9.7.x · @react-three/drei 10.7.x · three 0.185.x.

## Minimal App

`<Canvas>` creates the WebGL renderer, a default scene, and a default camera, then renders its children into that scene. Three.js classes appear as camelCase JSX: `<mesh>`, `<boxGeometry />`, `<meshStandardMaterial />` — see [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md).

```tsx
import { createRoot } from 'react-dom/client'
import { Canvas, useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import type { Mesh } from 'three'

function Spinner() {
  const meshRef = useRef<Mesh>(null!)
  useFrame((state, delta) => {
    meshRef.current.rotation.y += delta
  })
  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="hotpink" />
    </mesh>
  )
}

createRoot(document.getElementById('root')!).render(
  <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
    <ambientLight intensity={0.5} />
    <directionalLight position={[5, 5, 5]} />
    <Spinner />
  </Canvas>,
)
```

Canvas renders a wrapper `<div>` that stretches to 100% of its parent; extra props (`style`, `className`, `id`) land on that div. A zero-height parent means a zero-height canvas:

```css
html, body, #root {
  height: 100%;
  margin: 0;
}
```

## Canvas Props

| Prop | Meaning | Default |
|---|---|---|
| `children` | three.js JSX elements rendered into the scene | — |
| `fallback` | DOM JSX shown when GL is unsupported | — |
| `gl` | Props into the default `WebGLRenderer`, **or** a sync/async callback receiving constructor props: `gl={(props) => new WebGLRenderer(props)}`, `gl={async (props) => renderer}` (v9) | `{}` |
| `camera` | Props into the default camera, or your own `THREE.Camera` instance | `{ fov: 75, near: 0.1, far: 1000, position: [0, 0, 5] }` |
| `scene` | Props into the default scene, or your own `THREE.Scene` | `{}` |
| `shadows` | `true` = PCFSoft; `'basic' \| 'percentage' \| 'soft' \| 'variance'`; or props into `gl.shadowMap` | `false` |
| `raycaster` | Props into the default `THREE.Raycaster` | `{}` |
| `frameloop` | `'always' \| 'demand' \| 'never'` | `'always'` |
| `resize` | react-use-measure options | `{ scroll: true, debounce: { scroll: 50, resize: 0 } }` |
| `orthographic` | Use an orthographic default camera | `false` |
| `dpr` | Pixel ratio: number or clamp range `[min, max]` | `[1, 2]` |
| `legacy` | `true` disables global color management (`THREE.ColorManagement.enabled = false`) | `false` |
| `linear` | Switch off automatic sRGB color space + gamma correction | `false` |
| `flat` | `THREE.NoToneMapping` instead of `THREE.ACESFilmicToneMapping` | `false` |
| `events` | Event-manager factory `(state) => EventManager` | `import { events } from '@react-three/fiber'` |
| `eventSource` | HTMLElement or ref where pointer events subscribe | `gl.domElement.parentNode` |
| `eventPrefix` | Coordinate source for pointer x/y: `'offset'`, `'client'`, `'page'`, `'layer'`, `'screen'` | `'offset'` |
| `onCreated` | `(state) => {}` — fires after the canvas is rendered (not yet committed) | — |
| `onPointerMissed` | `(event) => {}` — pointer up/click that hit no object | — |

The v9 `gl` callback change is breaking: in v8 the callback received the canvas element (`gl={(canvas) => new WebGLRenderer({ canvas })}`); in v9 it receives the assembled **constructor props** (canvas included) and may return a Promise — that async form is the WebGPU entry point (see [WebGPU](#webgpu)).

## Render Defaults

What `<Canvas>` installs when you pass nothing:

| Piece | Default |
|---|---|
| Renderer | `WebGLRenderer` with `antialias: true`, `alpha: true`, `powerPreference: "high-performance"` |
| Output color space | `THREE.SRGBColorSpace` |
| Tone mapping | `THREE.ACESFilmicToneMapping` |
| Color management | `THREE.ColorManagement.enabled = true` |
| Camera | `PerspectiveCamera` (fov 75, near 0.1, far 1000, position `[0, 0, 5]`) — or `OrthographicCamera` with `orthographic` |
| Scene / Raycaster | one of each |
| Shadow map | `THREE.PCFSoftShadowMap` when shadows are enabled |
| dpr | clamped to `[1, 2]` |

These defaults are why R3F scenes look "correct" out of the box: sRGB output plus ACES filmic tone mapping is the modern three.js color pipeline. Override deliberately via `gl`, `flat`, `linear`, `legacy` — not by mutating the renderer mid-frame.

## Camera Setup

```tsx
// Tune the default perspective camera
<Canvas camera={{ position: [0, 2, 8], fov: 50, near: 0.1, far: 200 }}>

// Orthographic: zoom instead of fov
<Canvas orthographic camera={{ zoom: 80, position: [0, 0, 100] }}>

// Bring your own instance
import * as THREE from 'three'
const camera = new THREE.PerspectiveCamera(35, 1, 0.5, 500)
<Canvas camera={camera}>
```

- Camera props are applied at construction time. Changing the `camera` prop object later does **not** re-drive the camera — mutate `state.camera` in an effect, or use drei's `<PerspectiveCamera makeDefault>` for a declarative camera that lives inside the tree (see [staging-and-drei.md](./staging-and-drei.md)).
- R3F keeps the camera's aspect (and orthographic frustum) in sync with canvas size on resize. Opt out with `camera={{ manual: true }}` when you compute projection yourself.
- To swap the default camera at runtime: `set({ camera: myCamera })` via `useThree` — see [hooks.md](./hooks.md).

## Shadows

The `shadows` prop enables `gl.shadowMap` and picks the algorithm:

| Value | shadowMap.type |
|---|---|
| `true` or `"soft"` | `THREE.PCFSoftShadowMap` |
| `"basic"` | `THREE.BasicShadowMap` (fastest, hard edges) |
| `"percentage"` | `THREE.PCFShadowMap` |
| `"variance"` | `THREE.VSMShadowMap` (soft, works with shadow blur; casters must also receive) |
| object | spread onto `gl.shadowMap`, e.g. `shadows={{ type: THREE.BasicShadowMap }}` |

```tsx
<Canvas shadows>
  <directionalLight castShadow position={[5, 8, 5]} shadow-mapSize={[2048, 2048]} />
  <mesh castShadow>{/* caster */}</mesh>
  <mesh receiveShadow>{/* ground */}</mesh>
</Canvas>
```

Enabling the map is step one of three: lights need `castShadow`, meshes need `castShadow`/`receiveShadow`. Soft-shadow helpers (`SoftShadows`, `AccumulativeShadows`, `ContactShadows`) live in drei — see [staging-and-drei.md](./staging-and-drei.md).

## Frameloop

| Mode | Behavior |
|---|---|
| `'always'` | Render every frame (default) |
| `'demand'` | Render only when React commits changes or `invalidate()` is called; multiple calls coalesce into one frame |
| `'never'` | No automatic loop — drive frames yourself with `advance(timestamp)` |

```tsx
import { Canvas, invalidate } from '@react-three/fiber'

<Canvas frameloop="demand">{/* ... */}</Canvas>

// After any imperative mutation outside React:
controlsRef.current.addEventListener('change', invalidate)
```

`invalidate()` *requests* a frame; it does not render synchronously. Both `invalidate` and `advance` are available as global exports and on the `useThree` state. Drei controls call `invalidate` automatically in demand mode. Full demand-rendering doctrine (and the `performance.regress` system): [performance.md](./performance.md).

## Color Management Flags

Three flags, three distinct switches — they are not synonyms:

| Flag | Exact effect when `true` |
|---|---|
| `legacy` | `THREE.ColorManagement.enabled = false` — disables global color management; hex/named colors are no longer treated as sRGB inputs |
| `linear` | Switches off automatic sRGB output color space + gamma correction (linear output) |
| `flat` | `gl.toneMapping = THREE.NoToneMapping` instead of `ACESFilmicToneMapping` |

Recipes:

```tsx
// Pixel-exact 2D / sprite / UI-style rendering — colors match CSS values
<Canvas flat linear>

// Keep the sRGB pipeline but stop ACES from dulling saturated colors
<Canvas flat>

// Per-material opt-out instead of scene-wide (e.g. for bloom-driven emissives)
<meshBasicMaterial toneMapped={false} />
```

Texture color-space handling changed in v9: automatic sRGB conversion of texture *props* was removed; built-in materials annotate color textures themselves, and data textures (normal/roughness/displacement) are no longer corrupted. For custom materials set `texture.colorSpace = THREE.SRGBColorSpace` (or `texture-colorSpace={THREE.SRGBColorSpace}` in JSX) — details in [loading-assets.md](./loading-assets.md) and [migration-v8-to-v9.md](./migration-v8-to-v9.md).

## Event Wiring

Canvas-level event configuration (per-object handlers and the raycast/propagation model live in [events-and-interaction.md](./events-and-interaction.md)):

```tsx
function App() {
  const containerRef = useRef<HTMLDivElement>(null!)
  return (
    <div ref={containerRef}>
      <HtmlOverlay />
      <Canvas
        eventSource={containerRef}
        eventPrefix="client"
        onPointerMissed={() => deselectAll()}
      >
        {/* ... */}
      </Canvas>
    </div>
  )
}
```

- `eventSource` — where pointer listeners attach. Default is the canvas's parent element. Point it at a shared ancestor when DOM overlays cover the canvas, so pointer events still reach the scene.
- `eventPrefix` — which DOM event coordinates feed the raycast math. Default `'offset'` pairs with the default source; use `'client'` when `eventSource` is a larger page region.
- `events` — a factory `(state) => EventManager` replacing the default manager (custom intersection filtering/sorting, custom `compute`). Import the default as `import { events } from '@react-three/fiber'` and wrap it.
- `onPointerMissed` on Canvas fires for clicks that hit no object — the standard "click empty space to deselect" hook. The same prop also exists on individual objects.

## onCreated & Fallback

```tsx
import * as THREE from 'three'

<Canvas
  onCreated={(state) => {
    state.scene.background = new THREE.Color('#0a0a0a')
    state.gl.setClearColor('#0a0a0a')
  }}
  fallback={<div>WebGL is not supported on this device.</div>}
>
```

- `onCreated` runs once with the full root state (`gl`, `scene`, `camera`, `size`, …) after the canvas is rendered but before it is committed — the place for one-time imperative renderer/scene setup that has no declarative equivalent.
- `fallback` renders plain DOM JSX when a GL context cannot be created (headless environments, blocked WebGL, ancient hardware). Without it, an unsupported environment throws.

## Bundler Setup

**Vite** — zero config. `npm create vite@latest my-app -- --template react-ts`, install the packages, done.

**Next.js** (13.1+) — three ships ESM that must be transpiled, and Canvas needs the DOM:

```js
// next.config.js
module.exports = {
  transpilePackages: ['three'],
}
```

```tsx
// app/scene.tsx — App Router: Canvas and every R3F hook are client-side
'use client'
import { Canvas } from '@react-three/fiber'
```

**React Native** — import from the native entry point, add the GL backend, and teach Metro about model assets:

```bash
npm install three @react-three/fiber
expo install expo-gl
```

```jsx
import { Canvas } from '@react-three/fiber/native'
```

```js
// metro.config.js
const { getDefaultConfig } = require('expo/metro-config')
const config = getDefaultConfig(__dirname)
config.resolver.assetExts.push('glb', 'gltf', 'png', 'jpg')
module.exports = config
```

## WebGPU

v9 supports `THREE.WebGPURenderer` through the async `gl` callback. Import three from `three/webgpu` (the classic `three` entry stays WebGL-only), and `await renderer.init()` before returning:

```tsx
import * as THREE from 'three/webgpu'
import { Canvas, extend, type ThreeToJSXElements } from '@react-three/fiber'

declare module '@react-three/fiber' {
  interface ThreeElements extends ThreeToJSXElements<typeof THREE> {}
}

extend(THREE as any)

export default function App() {
  return (
    <Canvas
      gl={async (props) => {
        const renderer = new THREE.WebGPURenderer(props as any)
        await renderer.init()
        return renderer
      }}
    >
      <Scene />
    </Canvas>
  )
}
```

- `ThreeToJSXElements` maps the whole `three/webgpu` namespace into `ThreeElements`, and `extend(THREE as any)` registers it as the JSX catalog — both are required because the WebGPU build exposes node materials and classes the default catalog doesn't know.
- `WebGPURenderer` falls back to WebGL2 automatically where WebGPU is unavailable — **silently**; see the lifecycle gotchas below.
- In v9 the renderer still lives at `state.gl` regardless of backend. **R3F v10 (alpha)** makes WebGPU first-class and renames `state.gl` → `state.renderer`; drei v11 alphas pair with it. Teach v9 as current, flag the rename when writing forward-compatible code.
- Under WebGPU, custom shading is TSL/node-material based — GLSL `ShaderMaterial` belongs to the WebGL path. See [shaders-and-custom-materials.md](./shaders-and-custom-materials.md).

### WebGPU Lifecycle Gotchas

Four failure modes of the async-factory path, all verified against the installed fiber 9.6.1 + three r185 sources (2026-07); none is caught by React error boundaries or surfaced by R3F:

- **A rejected `gl` factory is swallowed.** Canvas's internal effect calls its async configure path fire-and-forget with no catch, and R3F's error channel is only wired by the `render()` call that sits *after* the failed await — so if `renderer.init()` throws, neither `onCreated` nor any app error boundary ever fires. The canvas stays permanently blank with only an `unhandledrejection`. If init can fail on your tiering path, catch inside the factory, surface app state yourself (flip to a fallback/unsupported screen), then rethrow.
- **The WebGL2 auto-fallback is silent.** Unless `forceWebGL: true` is passed, the `WebGPURenderer` constructor installs a `getFallback` that swaps in the WebGL backend when WebGPU init throws (adapter acquired but `requestDevice` fails, blocklists, driver resets). The init promise still *resolves*; the only signal is a console warning. If app state depends on which backend runs, verify after init: `renderer.backend.isWebGPUBackend === true`.
- **Unmount never disposes a WebGPURenderer.** R3F's unmount cleanup calls WebGL-only APIs (`renderLists.dispose()`, `forceContextLoss()` — both absent on `WebGPURenderer`) and never calls `gl.dispose()`, so every Canvas unmount orphans a live `GPUDevice`. Own disposal yourself on real unmounts — and remember StrictMode's *simulated* unmounts run effect cleanup while the renderer is still live, so a naive dispose-in-cleanup breaks dev.
- **The factory can run twice during init.** The configure path checks `state.gl` *before* awaiting the factory, and the layout effect that calls it re-runs on every commit — a commit landing inside the init window (resize, zoom, devtools toggle) re-invokes the factory and constructs a second renderer on the same canvas, leaking the loser. Memoize the in-flight promise per canvas: `WeakMap<HTMLCanvasElement, Promise<Renderer>>` keyed on the `canvas` in the factory's props.

## Custom Tree-Shakable Roots

`<Canvas>` is a convenience wrapper. `createRoot` gives you the same reconciler against a canvas element you own — and lets you shrink the bundle by registering only the three.js classes you use:

```jsx
import * as THREE from 'three'
import { extend, createRoot, events } from '@react-three/fiber'

extend(THREE)
// or selectively, for tree-shaking:
// extend({ Mesh: THREE.Mesh, BoxGeometry: THREE.BoxGeometry, MeshStandardMaterial: THREE.MeshStandardMaterial })

const root = createRoot(document.querySelector('canvas'))
await root.configure({ events, camera: { position: [0, 0, 50] } })

window.addEventListener('resize', () =>
  root.configure({ size: { width: window.innerWidth, height: window.innerHeight } }),
)

root.render(<App />)
// root.unmount() tears down and disposes
```

- `root.configure()` accepts the same options as Canvas props (`gl`, `camera`, `events`, `shadows`, `size`, …) and is async in v9 (the `gl` callback may be async).
- Nothing is automatic here: no resize observer, no default event connection unless you pass `events`. Wire both yourself.
- `extend` merges classes into the JSX catalog; `extend(THREE)` registers everything (no tree-shaking), a selective object keeps unused three modules out of the bundle. The v9 factory form `const Component = extend(Class)` returns a typed component directly — preferred for libraries; see [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md).

## StrictMode in v9

v9 inherits `<StrictMode>` from the parent React tree across the renderer boundary. In v8 it did not, so codebases added a second `<StrictMode>` inside Canvas — delete the now-redundant inner one when migrating. Expect dev-mode effects inside Canvas to double-invoke like the rest of a StrictMode tree; keep them idempotent:

```tsx
// v8 (legacy): StrictMode did not cross into the Canvas renderer
<StrictMode>
  <Canvas>
    <StrictMode>   {/* needed in v8 — DELETE in v9 */}
      <Scene />
    </StrictMode>
  </Canvas>
</StrictMode>

// v9: inherited automatically
<StrictMode>
  <Canvas>
    <Scene />
  </Canvas>
</StrictMode>
```

Full breaking-change list: [migration-v8-to-v9.md](./migration-v8-to-v9.md).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Blank page; canvas element has 0 height | Canvas stretches to its parent — set `html, body, #root { height: 100% }` or size the wrapper div |
| "Hooks can only be used within the Canvas component!" | `useThree`/`useFrame`/`useLoader` ran outside the Canvas tree — move the call into a component rendered as a Canvas child |
| Changing the `camera` prop after mount does nothing | Camera props are constructor-time config — mutate `state.camera` in an effect or use drei `<PerspectiveCamera makeDefault>` |
| v8 idiom `gl={(canvas) => new WebGLRenderer({ canvas })}` gets wrong args in v9 | The v9 callback receives constructor props: `gl={(props) => new WebGLRenderer(props)}` (sync or async) |
| `shadows` set on Canvas but nothing casts | The prop only enables the shadow map — also set `castShadow` on the light and `castShadow`/`receiveShadow` on meshes |
| `frameloop="demand"` scene freezes after imperative mutations | Call `invalidate()` after changes made outside React; drei controls do this automatically |
| Scene colors look duller/darker than the same CSS values | ACES tone mapping + sRGB output at work — use `flat linear` for pixel-exact color, or `toneMapped={false}` on specific materials |
| Dev-mode effects inside Canvas double-invoke after upgrading to v9 | StrictMode is now inherited across the Canvas boundary — that's expected dev behavior; make effects idempotent and delete any now-redundant `<StrictMode>` inside Canvas |
| Next.js: ESM import errors from `three`, or Canvas crashes during SSR | Add `transpilePackages: ['three']` to next.config.js and mark the scene component `'use client'` |
| React Native: Metro can't resolve `.glb`/`.gltf` assets | Push `'glb', 'gltf', 'png', 'jpg'` onto `config.resolver.assetExts` in metro.config.js |
| WebGPU canvas stays black | Return the renderer from the async `gl` callback only after `await renderer.init()` |
| Blank canvas plus an `unhandledrejection` when `renderer.init()` fails | R3F swallows async `gl` factory rejections and no error boundary fires — catch inside the factory, surface app state, then rethrow (see [WebGPU Lifecycle Gotchas](#webgpu-lifecycle-gotchas)) |
| App state says WebGPU but frames render on WebGL2 | three's silent `getFallback` swapped backends at init — verify `renderer.backend.isWebGPUBackend` after init |
| GPU device count climbs across route changes / remounts | R3F's unmount cleanup is WebGL-only and never disposes a `WebGPURenderer` — dispose it yourself on real unmounts |
| Code targeting the v10 alpha reads `state.gl` as undefined | v10 renames `state.gl` → `state.renderer`; on v9 (current) keep `state.gl` |
| Raw `dpr={window.devicePixelRatio}` tanks performance on mobile | Keep a clamp range — the default `dpr={[1, 2]}` stops 3×+ displays from overpaying fill rate |
| drei 10 install fails / peer conflicts on a React 18 project | drei 10 requires fiber ^9 + React 19; on React 18 stay on drei 9 + fiber 8 (frozen, legacy) or upgrade React |

## See Also

- [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md) — the JSX object model: `args`, `attach`, `primitive`, `extend` typing.
- [hooks.md](./hooks.md) — `useThree` root state (`gl`, `camera`, `size`, `viewport`), `set`/`get`, `invalidate`/`advance`.
- [performance.md](./performance.md) — demand rendering in depth, dpr scaling, performance regression.
- [migration-v8-to-v9.md](./migration-v8-to-v9.md) — every v8 → v9 breaking change in one place.
- [../SKILL.md](../SKILL.md) — skill overview and file map.
- Official: [Canvas API](https://r3f.docs.pmnd.rs/api/canvas) · [Installation](https://r3f.docs.pmnd.rs/getting-started/installation) · [v9 migration guide](https://r3f.docs.pmnd.rs/tutorials/v9-migration-guide)
