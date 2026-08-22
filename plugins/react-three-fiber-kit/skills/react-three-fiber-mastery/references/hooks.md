# Hooks

The four core R3F hooks — `useThree` (state access), `useFrame` (render loop), `useLoader` (suspense-based asset loading), `useGraph` (named-node graphs) — plus the global exports (`addEffect`, `createPortal`, `applyProps`, `invalidate`, `advance`, ...). Everything here targets R3F v9 on React 19; legacy v8 idioms are labeled as such.

> Canvas props, render defaults, and the color-management flags mirrored in state: see [canvas-and-project-setup.md](./canvas-and-project-setup.md). Shared stack setup: [../SKILL.md](../SKILL.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Hook Rules](#hook-rules) | Canvas-context placement, the component split required around a root, and automatic cleanup of frame, state, and loader consumers on unmount |
| [useThree](#usethree) | Selective root-state subscriptions, renderer and viewport fields, event and performance controls, non-reactive reads, mutable-object boundaries, projection updates, and replacing defaults |
| [useFrame](#useframe) | Live state, delta, and XR callbacks, allocation-free ref mutation, external-store reads, negative ordering, and positive-priority render takeover for multiple passes |
| [useLoader](#useloader) | Suspense and error boundaries, parallel assets, URL-keyed sharing, preload and eviction, cached-resource ownership and cloning, loader configuration and progress, v9 instances, and named graphs |
| [useGraph](#usegraph) | Memoized node and material lookup after ordinary or skeleton-safe cloning plus the non-hook `buildGraph` equivalent |
| [Global and Additional Exports](#global-and-additional-exports) | Portal rendering, imperative prop application, global frame effects, manual loop control, graph building, roots, and advanced or test utilities |
| [Common Mistakes](#common-mistakes) | Canvas hook scope, narrow selectors and fresh reads, mutable camera state, delta-scaled frame work and render priorities, Suspense and error boundaries, shared-loader cloning and disposal, loop-specific invalidation, deprecated pointer naming, and v9 loader instances |
| [See Also](#see-also) | Canvas state setup, asset loading, animation, render-loop performance, stack setup, and the official hooks API |

## Hook Rules

R3F hooks read the root store from context, and that context exists only **inside `<Canvas>`**. Calling `useThree`/`useFrame`/`useLoader`/`useGraph` in a component that renders the Canvas (rather than under it) throws `R3F: Hooks can only be used within the Canvas component!`. Split the tree:

```jsx
import { Canvas, useThree } from '@react-three/fiber'

function Scene() {
  const camera = useThree((state) => state.camera) // OK — under <Canvas>
  return <mesh>{/* ... */}</mesh>
}

export default function App() {
  // useThree() here would throw — this component is outside the Canvas root
  return (
    <Canvas>
      <Scene />
    </Canvas>
  )
}
```

All hook subscriptions (frame callbacks, state selectors, loader cache entries' consumers) clean themselves up on unmount — no manual teardown.

## useThree

Accesses the root state store. Called bare it returns the whole state object and re-renders the component on **every** state change; called with a selector it re-renders only when the selected slice changes. Always prefer selectors.

```jsx
import { useThree } from '@react-three/fiber'

const gl = useThree((state) => state.gl)
const { width, height } = useThree((state) => state.viewport)
```

### State Fields

| Field | Shape | Notes |
|---|---|---|
| `gl` | `THREE.WebGLRenderer` | The renderer. (R3F v10 alphas rename this to `state.renderer` to cover WebGPU — forward-looking, not v9.) |
| `scene` | `THREE.Scene` | Root scene. |
| `camera` | `THREE.PerspectiveCamera \| THREE.OrthographicCamera` | Default camera (or the one you supplied). |
| `raycaster` | `THREE.Raycaster` | Used by the event system. |
| `pointer` | `THREE.Vector2` | Normalized pointer coords, −1..1. |
| `mouse` | `THREE.Vector2` | **Deprecated** alias — use `pointer`. |
| `clock` | `THREE.Clock` | Running clock; `clock.elapsedTime` for absolute time. |
| `linear` | `boolean` | `true` when automatic sRGB conversion is off (Canvas `linear`). |
| `flat` | `boolean` | `true` when tone mapping is `NoToneMapping` (Canvas `flat`). |
| `legacy` | `boolean` | `true` when `THREE.ColorManagement` is disabled (Canvas `legacy`). |
| `frameloop` | `'always' \| 'demand' \| 'never'` | Current render-loop mode. |
| `performance` | `{ current, min, max, debounce, regress() }` | Adaptive-quality knob. Defaults `current: 1, min: 0.5, max: 1, debounce: 200`. Call `regress()` on load spikes (e.g. controls `change`); `current` drops toward `min`, recovers after `debounce` ms. Components read `current` to scale dpr/resolution. |
| `size` | `{ width, height, top, left }` | Canvas size in **pixels**. |
| `viewport` | `{ width, height, initialDpr, dpr, factor, distance, aspect, getCurrentViewport(camera?, target?, size?) }` | Size in **three.js units** at `distance` from the camera. `factor = size.width / viewport.width` (pixels per unit). `getCurrentViewport` recomputes at an arbitrary target point. |
| `xr` | `{ connect, disconnect }` | Internal WebXR loop bindings. |
| `events` | `{ connected, handlers, connect(target), disconnect, update() }` | Event manager; `connect(domNode)` rebinds events to another element, `update()` forces a raycast without pointer movement (e.g. after the camera moves over a hoverable object). |

`onPointerMissed` (the Canvas-level miss handler) also lives on state and is swappable via `set`.

### Methods

| Method | Purpose |
|---|---|
| `set(partial)` | Merge values into the store — how you swap defaults (camera, events, ...). |
| `get()` | **Non-reactive** fresh read of the whole state. Use inside callbacks/loops instead of stale closures. |
| `invalidate()` | Request a frame when `frameloop="demand"`. Coalesced — calling it n times does not render n times. |
| `advance(timestamp, runGlobalEffects?)` | Step exactly one frame when `frameloop="never"` (you drive the loop). |
| `setSize(width, height, top?, left?)` | Resize the canvas state. |
| `setDpr(dpr)` | Set pixel ratio (number or `[min, max]`). |
| `setFrameloop(frameloop)` | Switch loop mode at runtime. |
| `setEvents(events)` | Merge into the event-manager config. |

```jsx
// demand-rendering idiom: mutate, then ask for one frame
const invalidate = useThree((state) => state.invalidate)
const handleChange = () => {
  meshRef.current.rotation.y += 0.1
  invalidate()
}
```

See [performance.md](./performance.md) for the full on-demand rendering and `regress()` playbook.

### Selectors and the Reactivity Boundary

Store reactivity stops at the store's own fields. Selecting **into a three.js object** does not subscribe to that object's internals:

```jsx
// ✗ never updates — zoom is a property of the camera object, not a store field
const zoom = useThree((state) => state.camera.zoom)

// ✓ re-renders only if the camera object itself is replaced (via set())
const camera = useThree((state) => state.camera)
```

Three.js objects are mutable and R3F does not proxy them. To react to `camera.zoom`, either read it fresh each frame in `useFrame`, or read imperatively at event time via `get()`:

```jsx
const get = useThree((state) => state.get)
const onClick = () => {
  const { camera } = get() // always current, no subscription
  console.log(camera.zoom)
}
```

After imperatively changing camera projection values (`zoom`, `fov`, `near`, `far`), call `camera.updateProjectionMatrix()` yourself.

### Swapping Defaults via set()

Replace store defaults from inside the tree; R3F propagates the change everywhere (events, `useThree` consumers):

```jsx
import { useEffect, useMemo } from 'react'
import { useThree } from '@react-three/fiber'
import * as THREE from 'three'

function OrthoSwitch() {
  const set = useThree((state) => state.set)
  const camera = useMemo(() => new THREE.OrthographicCamera(-2, 2, 2, -2, 0.1, 100), [])
  useEffect(() => {
    set({ camera })
  }, [set, camera])
  return null
}
```

For cameras specifically, prefer drei's `<PerspectiveCamera makeDefault />` / `<OrthographicCamera makeDefault />`, which do this for you — see [staging-and-drei.md](./staging-and-drei.md).

## useFrame

Subscribes a callback to the render loop; it runs every frame, just before R3F renders.

```jsx
useFrame((state, delta, xrFrame) => { /* ... */ }, renderPriority?)
```

- `state` — the live root state (same shape as `useThree`, always fresh — no stale closure problem).
- `delta` — seconds since the last frame. Scale all motion by it for refresh-rate independence.
- `xrFrame` — the `XRFrame` when presenting in WebXR, otherwise `undefined`.
- `renderPriority` — optional number, default `0`. See below.

```jsx
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function Spinner() {
  const ref = useRef(null)
  useFrame((state, delta) => {
    ref.current.rotation.y += delta                       // rate-independent
    ref.current.position.y = Math.sin(state.clock.elapsedTime)
  })
  return (
    <mesh ref={ref}>
      <boxGeometry />
      <meshStandardMaterial color="hotpink" />
    </mesh>
  )
}
```

### The Rules

1. **Never call setState inside useFrame.** Not React state, not zustand set — nothing that schedules a render, 60+ times per second. Mutate objects through refs instead.
2. **Use `delta`, not fixed increments.** `rotation.y += 0.01` runs 2.4× faster on a 144 Hz display.
3. **Don't allocate in the loop.** `new THREE.Vector3()` per frame is GC pressure; hoist a reusable temp outside the callback and `.set()` it.
4. **Read fast external state imperatively**, not through reactive bindings:

```jsx
// zustand: transient read, zero re-renders
useFrame((_, delta) => {
  ref.current.position.x += useStore.getState().speed * delta
})
```

Full doctrine (isolation, lerp-toward-target, mount/unmount costs): [performance.md](./performance.md) and [animation.md](./animation.md).

### Render Priorities

| Priority | Effect |
|---|---|
| `0` (default) | Callback runs before render; R3F renders automatically afterward. |
| `> 0` | **Takes over the render loop.** Automatic rendering is disabled for the whole root — you must call `gl.render(...)` yourself. Multiple takeover callbacks run in ascending order (`1`, then `2`, ...). |
| `< 0` | Does **not** take over. Purely orders callbacks among themselves: `-2` runs before `-1` runs before `0`. |

Takeover — the multi-pass / HUD idiom:

```jsx
function RenderPasses({ hudScene, hudCamera }) {
  useFrame(({ gl, scene, camera }) => {
    gl.autoClear = true
    gl.render(scene, camera)          // main pass
  }, 1)
  useFrame(({ gl }) => {
    gl.autoClear = false
    gl.clearDepth()
    gl.render(hudScene, hudCamera)    // overlay pass, runs after priority 1
  }, 2)
  return null
}
```

This is also how `@react-three/postprocessing`'s `<EffectComposer>` replaces the default render — see [postprocessing.md](./postprocessing.md).

Negative priorities — ordering without takeover (e.g. update a camera rig before things that read the camera):

```jsx
useFrame(() => rig.update(), -1)  // first
useFrame(() => { /* reads camera; runs at 0, still auto-renders */ })
```

## useLoader

Suspense-based wrapper around any three.js loader class (anything with a `.load` method). Suspends while loading; results are cached.

```jsx
import { Suspense } from 'react'
import { useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

function Model() {
  const gltf = useLoader(GLTFLoader, '/model.glb')
  return <primitive object={gltf.scene} />
}

export default function Scene() {
  return (
    <Suspense fallback={null}>
      <Model />
    </Suspense>
  )
}
```

Signature: `useLoader(LoaderClassOrInstance, urlOrUrls, extensions?, onProgress?)`.

- The component **suspends** — a `<Suspense>` boundary in a parent is required. Load errors surface to the nearest **error boundary**, also at the parent level.
- Multiple URLs load in parallel and return an array: `const [albedo, normal] = useLoader(THREE.TextureLoader, ['/albedo.png', '/normal.png'])`.
- Loading UI: drei's `useProgress` + `<Html>` or `<Loader />` — see [loading-assets.md](./loading-assets.md).

### Caching, Preloading, Eviction

The cache is **keyed by URL** (per loader). Two components loading `/model.glb` share one parsed result — one network fetch, one parse.

```jsx
useLoader.preload(GLTFLoader, '/model.glb')   // module scope: warm the cache before mount
useLoader.clear(GLTFLoader, '/model.glb')     // evict an entry (e.g. the asset changed on disk)
```

**Shared-cache caveat:** because results are shared, mutating a cached asset (re-coloring a material, transforming `gltf.scene`, calling `.dispose()`) affects **every** consumer of that URL. To customize per-instance, clone first — `scene.clone()`, drei's `<Clone />`, or `SkeletonUtils.clone` for skinned meshes (see [useGraph](#usegraph)).

### Extensions Callback — Draco Idiom

The third argument receives the loader instance for one-time configuration:

```jsx
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'

useLoader(GLTFLoader, '/compressed.glb', (loader) => {
  const dracoLoader = new DRACOLoader()
  dracoLoader.setDecoderPath('/draco-gltf/')
  loader.setDRACOLoader(dracoLoader)
})
```

(drei's `useGLTF` wires Draco/Meshopt automatically — prefer it for GLTF; see [loading-assets.md](./loading-assets.md).)

### onProgress

The fourth argument is passed to the loader as its progress handler (a `ProgressEvent` per URL):

```jsx
useLoader(GLTFLoader, url, undefined, (event) => {
  console.log((event.loaded / event.total) * 100, '% loaded')
})
```

For UI, prefer drei's `useProgress`, which aggregates across all in-flight loaders.

### Loader Instances (v9)

v9 accepts a pre-constructed loader **instance**, not just the class — for pooling or reusing an expensively configured loader across call sites:

```jsx
const gltfLoader = new GLTFLoader()   // module scope, configured once
gltfLoader.setDRACOLoader(dracoLoader)

function Model({ url }) {
  const gltf = useLoader(gltfLoader, url)
  return <primitive object={gltf.scene} />
}
```

### Automatic { nodes, materials } Graph

Any loader result with a `.scene` property (GLTF) gets a memoized, name-indexed graph attached:

```jsx
const { nodes, materials, scene } = useLoader(GLTFLoader, '/model.glb')
return (
  <group dispose={null}>
    <mesh geometry={nodes.Hull.geometry} material={materials.Paint} />
  </group>
)
```

This is the foundation `gltfjsx` builds on. Node/material names must be unique within the asset.

## useGraph

Builds the same memoized `{ nodes, materials }` collection from **any** `Object3D` — most useful after cloning, since clones don't carry the graph `useLoader` attached to the original:

```jsx
import { useMemo } from 'react'
import { useGraph } from '@react-three/fiber'
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js'

function Soldier({ scene }) {           // scene from useGLTF/useLoader
  const clone = useMemo(() => SkeletonUtils.clone(scene), [scene])
  const { nodes, materials } = useGraph(clone)
  return <primitive object={clone} />
}
```

`SkeletonUtils.clone` (not `scene.clone()`) is required for skinned meshes — plain clones share skeletons. The non-hook version, `buildGraph(object)`, is exported for use outside components.

## Global and Additional Exports

All importable from `@react-three/fiber`:

| Export | Purpose |
|---|---|
| `addEffect(cb)` | Run `cb` before every frame of the global loop. Returns an unsubscribe function. |
| `addAfterEffect(cb)` | Same, after every frame. |
| `addTail(cb)` | Run `cb` when **all** canvases stop rendering (idle — relevant with `frameloop="demand"`). |
| `invalidate()` | Global form of `state.invalidate()` — requests a frame on every demand-mode root. |
| `advance(timestamp, runGlobalEffects?)` | Global form of `state.advance` — steps every `frameloop="never"` root. |
| `flushGlobalEffects(type, timestamp)` | Manually run the global effect queues (`'before' \| 'after' \| 'tail'`) when you drive your own loop and passed `runGlobalEffects: false`. |
| `createPortal(children, container, state?)` | Render JSX into a different scene-graph container (re-parenting). |
| `applyProps(object, props)` | Imperatively apply R3F-style props (set-shorthand, pierced keys) to a three.js object. |
| `buildGraph(object)` | Non-hook `{ nodes, materials }` builder behind `useGraph`. |
| `flushSync(fn)` | Synchronous flush of the fiber renderer's updates (testing/advanced). |
| `act` | Test helper; in v9 prefer `import { act } from 'react'`. |
| `useInstanceHandle(ref)` | Ref to the internal instance descriptor. Internal/advanced — rarely needed in app code. |
| `extend`, `createRoot`, `events` | Catalog registration and Canvas-less roots — covered in [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md) and [canvas-and-project-setup.md](./canvas-and-project-setup.md). |

### Global Effects — stats.js Idiom

`addEffect`/`addAfterEffect` run outside any component, tied to the global loop — ideal for instrumentation:

```jsx
import { addEffect, addAfterEffect } from '@react-three/fiber'
import Stats from 'stats.js'

const stats = new Stats()
document.body.appendChild(stats.dom)
addEffect(() => stats.begin())
addAfterEffect(() => stats.end())
```

### createPortal — Re-Parenting

Declaratively mount part of the JSX tree under a different `Object3D` than its React parent — another scene (render targets), the camera (heads-up elements), any container:

```jsx
import { createPortal, useThree } from '@react-three/fiber'

function HeadsUp({ children }) {
  const camera = useThree((state) => state.camera)
  return (
    <>
      {/* the camera must itself be in the scene graph, or its children never render */}
      <primitive object={camera} />
      {createPortal(<group position={[0, 0, -2]}>{children}</group>, camera)}
    </>
  )
}
```

The optional third argument injects state overrides for everything inside the portal (own `events`, `camera`, etc.) — the mechanism behind drei's `<Hud>` and render-target views.

### applyProps — Imperative Prop Application

Applies props with the full JSX semantics (`.set()` shorthand, pierced/dashed keys) outside of JSX — useful in effects or when integrating imperative animation libraries:

```jsx
import { applyProps } from '@react-three/fiber'

applyProps(materialRef.current, { color: 'hotpink', 'emissive-r': 1 })
```

### Driving Your Own Loop (frameloop="never")

```jsx
import { advance } from '@react-three/fiber'

function loop(timestamp) {
  advance(timestamp)              // steps every <Canvas frameloop="never">
  requestAnimationFrame(loop)
}
requestAnimationFrame(loop)
```

Pass `runGlobalEffects: false` and call `flushGlobalEffects('before' | 'after', timestamp)` yourself if you need to interleave work between the effect queues and rendering.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `R3F: Hooks can only be used within the Canvas component!` | The hook is called in a component that renders `<Canvas>` instead of living under it. Move the hook into a child component of the Canvas. |
| Component re-renders on every frame/resize after `const state = useThree()` | Bare `useThree()` subscribes to everything. Select the slice: `useThree((s) => s.camera)`. |
| `useThree((s) => s.camera.zoom)` never updates | Reactivity stops at store fields — three.js internals aren't proxied. Read fresh in `useFrame` or via `get()`; after changing projection values, call `camera.updateProjectionMatrix()`. |
| Stale values inside event handlers or `useFrame`-adjacent callbacks | Closures capture old state. Use `get()` (from `useThree((s) => s.get)`) or the `state` argument `useFrame` passes you — both are always current. |
| Janky/frozen UI, React DevTools shows 60 renders/s | setState inside `useFrame` (or `onPointerMove`). Mutate via refs; read external stores with `getState()` in the loop. |
| Animation speed differs across monitors | Fixed per-frame increments. Multiply by `delta`: `ref.current.rotation.y += speed * delta`. |
| Screen goes black after adding `useFrame(cb, 1)` | Any positive priority disables automatic rendering for the whole root. Render yourself: `useFrame(({ gl, scene, camera }) => gl.render(scene, camera), 1)`. |
| Used a negative priority expecting to take over rendering | Negative priorities only order callbacks (`-2` before `-1`); they never disable auto-render. Use a positive priority to take over. |
| "A component suspended while responding to synchronous input" / blank canvas with `useLoader` | No `<Suspense>` boundary. Wrap the loading component (not the hook call) in `<Suspense fallback={...}>` in a parent. |
| Loader failure shows nothing, app silently blank | Errors propagate like render errors. Add an error boundary above the Suspense boundary. |
| Tinting one model instance re-colors every copy | `useLoader` results are cached and shared by URL. Clone before mutating: `scene.clone()`, drei `<Clone />`, or `SkeletonUtils.clone` + `useGraph` for skinned meshes. |
| Disposed a loaded asset on unmount; other consumers break or GPU resources vanish | Never `.dispose()` cached loader results — the cache owns them. Evict explicitly with `useLoader.clear(Loader, url)` when truly done. |
| `invalidate()` seems to do nothing | Only meaningful with `frameloop="demand"` (with `"always"` frames render anyway; with `"never"` use `advance(timestamp)`). |
| Reading `state.mouse` | Deprecated. Use `state.pointer` (same normalized `Vector2`). |
| v8 habit: expecting `useLoader` to only take a class | Fine, but v9 also accepts a configured loader **instance** — use it to pool Draco-configured GLTF loaders instead of reconfiguring per call site. |

## See Also

- [canvas-and-project-setup.md](./canvas-and-project-setup.md) — Canvas props that seed this state: `frameloop`, `dpr`, `linear`/`flat`/`legacy`, `events`.
- [loading-assets.md](./loading-assets.md) — drei `useGLTF`/`useTexture`/`useProgress`, gltfjsx workflow, Suspense patterns.
- [animation.md](./animation.md) — `useFrame` animation recipes, `useAnimations`, springs.
- [performance.md](./performance.md) — demand rendering, `performance.regress()`, transient subscriptions, loop hygiene.
- [../SKILL.md](../SKILL.md) — skill overview and shared setup.
- Official hooks docs: https://r3f.docs.pmnd.rs/api/hooks
