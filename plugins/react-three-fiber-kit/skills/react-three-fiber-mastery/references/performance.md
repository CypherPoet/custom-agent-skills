# Performance

The pitfalls doctrine from the official R3F docs plus the scaling toolbox: on-demand rendering, instancing, LOD, adaptive quality, and React-state discipline. R3F itself adds no per-frame overhead over vanilla three.js — performance problems come from breaking the rules below, and at scale R3F can outperform hand-rolled three.js because React schedules and batches updates.

> Canvas props (`frameloop`, `dpr`, `performance`): see [canvas-and-project-setup.md](./canvas-and-project-setup.md). Shared setup: see [../SKILL.md](../SKILL.md).

## Table of Contents

| Section | Covers |
|---|---|
| [The Eight Pitfalls](#the-eight-pitfalls) | Expensive object creation and per-frame work multiplied by refresh rate, with rules for sharing, state, deltas, mounting, allocation, and loader caching |
| [On-Demand Rendering](#on-demand-rendering) | Automatic React invalidation, coalesced requests after imperative changes, raw and drei control wiring, sustaining continuous animation, and externally advanced loops |
| [Instancing and the Draw-Call Budget](#instancing-and-the-draw-call-budget) | Draw-call limits, raw matrix updates and culling, declarative instances with fixed capacity and events, and merged instancing for repeated multi-mesh assets |
| [Level of Detail](#level-of-detail) | Camera-distance detail thresholds, required child ordering, and progressive low-resolution fallbacks while higher-detail assets load |
| [Adaptive Quality and Movement Regression](#adaptive-quality-and-movement-regression) | Opt-in quality envelopes, movement-triggered regression and recovery, adaptive pixel ratio and events, sustained-device monitoring, and mobile pixel-ratio clamping |
| [Expensive State Updates: startTransition](#expensive-state-updates-starttransition) | Scheduling unavoidable model mounts, level swaps, and suspending updates without blocking input or the frame loop |
| [React State Discipline](#react-state-discipline) | Isolated animated and display components, narrow root selectors, imperative frame reads, non-rendering Zustand subscriptions, and shallow multi-value selectors |
| [Profiling](#profiling) | In-canvas CPU, GPU, draw, triangle, and memory metrics, lightweight renderer counters, and diagnoses for draw-call, allocation, mount, and fill-rate bottlenecks |
| [Common Mistakes](#common-mistakes) | Per-frame allocation, fixed increments, React updates, and reactive store binding; demand invalidation; mount churn and shared-resource disposal; Zustand 5 subscriptions; instancing and culling; loader caching; and mobile pixel-ratio caps |
| [See Also](#see-also) | Related references and supporting guidance |

## The Eight Pitfalls

Two cost models drive every rule: (a) creating three.js objects is expensive — shader compilation, buffer uploads, GC pressure; (b) the render loop runs 60–120 times per second, so anything done per frame is multiplied by the refresh rate. React re-renders are for *slow, reactive* state; per-frame work mutates refs.

### 1. Object Creation Is Expensive — Share Geometries and Materials

Each mounted geometry allocates and uploads buffers; each material compiles a shader program. Think twice before you mount/unmount things.

```jsx
// Bad: every Sphere mounts its own geometry + material
function Sphere(props) {
  return (
    <mesh {...props}>
      <sphereGeometry args={[1, 32, 32]} />
      <meshLambertMaterial color="red" />
    </mesh>
  )
}

// Good: module-scope singletons shared by all instances — one geometry, one program
import * as THREE from 'three'

const sphereGeometry = new THREE.SphereGeometry(1, 32, 32)
const redMaterial = new THREE.MeshLambertMaterial({ color: 'red' })

function Sphere(props) {
  return <mesh geometry={sphereGeometry} material={redMaterial} {...props} />
}
```

`useMemo(() => new THREE.SphereGeometry(1, 32, 32), [])` works when the asset is per-component-tree rather than global. Colors on module-scope materials are converted correctly because R3F enables `THREE.ColorManagement` (three r150+) unless Canvas `legacy` is set.

R3F auto-disposes objects when their element unmounts — a shared geometry/material dies the first time any consumer unmounts. Mark sharers with `dispose={null}`:

```jsx
<mesh dispose={null} geometry={sphereGeometry} material={redMaterial} />
```

For *many* similar objects, sharing is not enough — use [instancing](#instancing-and-the-draw-call-budget).

### 2. Never setState in Loops or Fast Events

Not in `useFrame`, not in `setInterval`, not in `onPointerMove`. Each setState re-renders the component at frame rate.

```jsx
// Bad: 60–120 re-renders per second
useFrame(() => setX((x) => x + 0.1))

// Good: mutate the ref
useFrame((state, delta) => (ref.current.position.x += delta))
```

Same rule for rapidly-firing events — mutate, don't set:

```jsx
// Bad
<mesh onPointerMove={(e) => setHoverPoint(e.point.toArray())} />

// Good
<mesh onPointerMove={(e) => markerRef.current.position.copy(e.point)} />
```

### 3. Deltas, Not Fixed Values

A fixed increment ties animation speed to the refresh rate — twice as fast on a 120 Hz display, stuttery under load.

```jsx
// Bad: refresh-rate dependent
useFrame(() => (ref.current.rotation.x += 0.01))

// Good: radians per second, identical on every display
useFrame((state, delta) => (ref.current.rotation.x += 0.5 * delta))
```

### 4. Animate Inside the Loop, Not Through React State

Drive transitions by converging toward a target every frame — or hand it to `@react-spring/three` — never by pumping React state.

```jsx
// Good: lerp toward a target inside the loop; `active` can be plain React state
useFrame((state, delta) => {
  ref.current.position.x = THREE.MathUtils.lerp(ref.current.position.x, active ? 2 : 0, 0.1)
})
```

A fixed lerp factor is itself frame-rate dependent; `THREE.MathUtils.damp(current, target, lambda, delta)` (or `maath`'s `easing.damp3`) is the refresh-rate-independent form — see [animation.md](./animation.md). The spring alternative animates outside React entirely:

```jsx
import { useSpring, animated } from '@react-spring/three'

function Toggle({ active }) {
  const { scale } = useSpring({ scale: active ? 1.5 : 1 })
  return (
    <animated.mesh scale={scale}>
      <boxGeometry />
      <meshStandardMaterial />
    </animated.mesh>
  )
}
```

### 5. Never Bind Rapidly-Changing Reactive State to Props

If a store value changes at animation frequency, subscribing to it re-renders the component at animation frequency.

```jsx
// Bad: subscription → re-render per change, potentially hundreds per second
const x = useStore((state) => state.x)
return <mesh position-x={x} />

// Good: read imperatively inside the loop — fresh value, zero subscriptions
useFrame(() => (ref.current.position.x = useStore.getState().x))
return <mesh ref={ref} />
```

See [React State Discipline](#react-state-discipline) for the full zustand v5 pattern set.

### 6. Do Not Mount/Unmount Indiscriminately

Unmounting throws away compiled programs and uploaded buffers; remounting pays the full price again — visible as a frame hitch. Prefer visibility toggles, which cost nothing:

```jsx
// Bad: buffers destroyed and re-created, materials re-compiled on every toggle
{stage === 1 && <Stage1 />}

// Good: everything stays resident on the GPU
<Stage1 visible={stage === 1} />
```

Where mounting/unmounting is genuinely necessary (routes, level swaps), wrap the state change in `startTransition` so React schedules the expensive work without blocking input — see [below](#expensive-state-updates-starttransition).

### 7. Never Allocate in the Render Loop

`new THREE.Vector3()` per frame is 60–120 allocations per second — the GC sweeps show up as periodic hitches. Hoist reusable temps.

```jsx
// Bad: allocation every frame
useFrame(() => {
  ref.current.position.lerp(new THREE.Vector3(x, y, z), 0.1)
})

// Good: one temp, reused forever (safe at module scope — frames are single-threaded)
const tempVec = new THREE.Vector3()

function Follower({ x, y, z }) {
  const ref = useRef(null)
  useFrame(() => {
    ref.current.position.lerp(tempVec.set(x, y, z), 0.1)
  })
  return <mesh ref={ref}>{/* ... */}</mesh>
}
```

The same applies to `new THREE.Color()`, arrays, and closures that capture fresh objects — allocate once, `.set()`/`.copy()` per frame.

### 8. useLoader for Caching — Never Ad-Hoc Loaders in Effects

`useLoader` caches by URL: fifty components loading the same texture share one fetch, one decode, one GPU upload. An ad-hoc loader in `useEffect` re-fetches and re-parses per component instance.

```jsx
// Bad: one fetch + decode per mounted component
useEffect(() => {
  new THREE.TextureLoader().load('/map.jpg', setTexture)
}, [])

// Good: cached, suspends until ready
const texture = useLoader(THREE.TextureLoader, '/map.jpg')
```

Use gltfjsx for models — its immutable JSX graphs let a full model be reused across the app. Caching, preloading, and Draco setup: [loading-assets.md](./loading-assets.md).

## On-Demand Rendering

Scenes that only change on interaction should not render 60 times per second. `frameloop="demand"` renders only when something requests a frame:

```jsx
<Canvas frameloop="demand">{/* ... */}</Canvas>
```

Semantics:

- **React updates render automatically.** Prop/state changes flowing through the reconciler schedule a frame — no manual work.
- **Imperative mutations need `invalidate()`.** Anything mutated outside React (refs in effects, external libraries) must request a frame.
- **Coalescing:** `invalidate()` does not render immediately — it *requests* a frame. Any number of calls before the next frame produce a single render.

```jsx
import { useThree } from '@react-three/fiber'
// outside components: import { invalidate } from '@react-three/fiber' — same coalescing behavior

function Mover() {
  const invalidate = useThree((state) => state.invalidate)
  const ref = useRef(null)

  useEffect(() => {
    ref.current.position.x = 5 // imperative change...
    invalidate()               // ...must request a frame
  }, [invalidate])

  return <mesh ref={ref}>{/* ... */}</mesh>
}
```

Wire camera controls to their `change` event — drei controls (`OrbitControls`, `CameraControls`, etc.) do this automatically; raw three.js controls need it manually:

```jsx
useEffect(() => {
  const controls = controlsRef.current
  controls.addEventListener('change', invalidate)
  return () => controls.removeEventListener('change', invalidate)
}, [invalidate])
```

Under `demand`, `useFrame` callbacks run only when a frame was requested. A continuously animating component must keep the chain alive (call `invalidate()` inside its `useFrame`) or switch the loop back on with `useThree((s) => s.setFrameloop)('always')` while the animation runs.

`frameloop="never"` disables the internal loop entirely; drive frames yourself with `advance(timestamp)` — useful for external loops or deterministic capture.

## Instancing and the Draw-Call Budget

Budget heuristic: **~1000 draw calls** is where most scenes start sagging — well before triangle count matters on modern GPUs. A thousand meshes with one material is a thousand draw calls; one `instancedMesh` with a thousand instances is **one**.

Raw form — `args={[null, null, count]}` (the nulls mean geometry and material come from JSX children), fill matrices with a reused temp `Object3D`, then flag the buffer:

```jsx
import * as THREE from 'three'
import { useLayoutEffect, useRef } from 'react'

const temp = new THREE.Object3D()

function Boxes({ count = 100000 }) {
  const ref = useRef(null)

  useLayoutEffect(() => {
    for (let i = 0; i < count; i++) {
      temp.position.set(Math.random() * 100 - 50, Math.random() * 100 - 50, Math.random() * 100 - 50)
      temp.updateMatrix()
      ref.current.setMatrixAt(i, temp.matrix)
    }
    ref.current.instanceMatrix.needsUpdate = true
  }, [count])

  return (
    <instancedMesh ref={ref} args={[null, null, count]}>
      <boxGeometry />
      <meshStandardMaterial />
    </instancedMesh>
  )
}
```

For per-frame instance animation, run the same `setMatrixAt` loop in `useFrame` and set `instanceMatrix.needsUpdate = true` every frame. Changing `count` via `args` reconstructs the whole mesh. The mesh frustum-culls as a single object using the base geometry's bounds — instances that wander far from the origin can vanish at screen edges; set `frustumCulled={false}` on the `instancedMesh` when instances move.

**drei `<Instances>`/`<Instance>`** — declarative instancing where each instance behaves like a regular component: transforms, per-instance `color`, full pointer events, and it respects parent group transforms:

```jsx
import { Instances, Instance } from '@react-three/drei'

function Bricks({ positions }) {
  return (
    <Instances limit={1000} range={positions.length}>
      <boxGeometry />
      <meshStandardMaterial />
      {positions.map((position, i) => (
        <Instance
          key={i}
          position={position}
          color="tomato"
          onClick={(e) => e.stopPropagation()}
        />
      ))}
    </Instances>
  )
}
```

`limit` sizes the buffers once (instances beyond it are ignored — size for the maximum you will ever show); `range` caps how many are drawn. Keep the material color white when using per-instance `color` — they multiply.

**drei `<Merged>`** — instancing for *multiple different* meshes (e.g. gltfjsx nodes); renders each distinct mesh once regardless of how many times you place it:

```jsx
import { Merged } from '@react-three/drei'

function Machines({ nodes }) {
  return (
    <Merged meshes={[nodes.Screw, nodes.Filament]}>
      {(Screw, Filament) => (
        <>
          <Screw position={[1, 0, 0]} />
          <Filament position={[-1, 0, 0]} />
          <Screw position={[2, 1, 0]} />
        </>
      )}
    </Merged>
  )
}
```

## Level of Detail

Swap geometry complexity by camera distance with drei `<Detailed>` (wraps `THREE.LOD`). Children go highest-detail first; `distances` are the camera-distance thresholds, one per child:

```jsx
import { Detailed } from '@react-three/drei'

<Detailed distances={[0, 15, 40]}>
  <mesh geometry={highPoly} material={material} />
  <mesh geometry={midPoly} material={material} />
  <mesh geometry={lowPoly} material={material} />
</Detailed>
```

Combine with nested `<Suspense>` for progressive model loading — render the low-res model as the `fallback` while the high-res one loads:

```jsx
<Suspense fallback={<Model url="/model-low.glb" />}>
  <Model url="/model-high.glb" />
</Suspense>
```

## Adaptive Quality and Movement Regression

R3F's root state carries a performance envelope: `performance: { current, min, max, debounce, regress() }` (defaults: `current` 1, `min` 0.5, `max` 1, `debounce` 200). Calling `regress()` drops `current` toward `min`; after `debounce` ms without another call it recovers to `max`. Nothing happens automatically — components *opt in* by reading `current` and scaling their quality. Configure the envelope on Canvas: `<Canvas performance={{ min: 0.5 }}>`.

Trigger regression during movement — drei controls take a prop; raw controls wire the event:

```jsx
<OrbitControls regress />
```

```jsx
const regress = useThree((state) => state.performance.regress)
useEffect(() => {
  const controls = controlsRef.current
  controls.addEventListener('change', regress)
  return () => controls.removeEventListener('change', regress)
}, [regress])
```

Respond to regression — drei ships the two standard responders:

```jsx
import { AdaptiveDpr, AdaptiveEvents } from '@react-three/drei'

<Canvas>
  <AdaptiveDpr pixelated />  {/* scales dpr with performance.current; pixelated avoids blur while degraded */}
  <AdaptiveEvents />         {/* pauses event raycasting while regressing */}
</Canvas>
```

Or respond manually — any quality knob works (dpr, shadow map size, effect toggles):

```jsx
function AdaptivePixelRatio() {
  const current = useThree((state) => state.performance.current)
  const setDpr = useThree((state) => state.setDpr)
  useEffect(() => {
    setDpr(window.devicePixelRatio * current)
  }, [current, setDpr])
  return null
}
```

**`<PerformanceMonitor>`** measures actual FPS over time and fires callbacks — use it to find a device's sustainable quality level rather than reacting to movement:

```jsx
import { PerformanceMonitor } from '@react-three/drei'
import { useState } from 'react'

function App() {
  const [dpr, setDpr] = useState(1.5)
  return (
    <Canvas dpr={dpr}>
      <PerformanceMonitor
        onIncline={() => setDpr(2)}
        onDecline={() => setDpr(1)}
        flipflops={3}
        onFallback={() => setDpr(1)}  // after 3 up/down oscillations, lock a floor
      >
        <Scene />
      </PerformanceMonitor>
    </Canvas>
  )
}
```

`onChange={({ factor }) => setDpr(0.5 + 1.5 * factor)}` gives a continuous 0–1 signal instead of stepwise callbacks.

**dpr clamping:** Canvas defaults to `dpr={[1, 2]}` — a clamp range against `window.devicePixelRatio`. Keep it. Passing raw devicePixelRatio on a dpr-3/4 phone multiplies fill cost 9–16× for invisible gains; dpr is usually the single highest-leverage quality knob.

## Expensive State Updates: startTransition

When a setState will trigger expensive work — mounting a model, swapping a level, anything that suspends or builds lots of objects — mark it as a transition so React keeps the frame loop and input responsive while it prepares the update:

```jsx
import { useTransition } from 'react'

function LevelSelect({ setLevel }) {
  const [isPending, startTransition] = useTransition()
  return (
    <Html>
      <button disabled={isPending} onClick={() => startTransition(() => setLevel('cathedral'))}>
        Load cathedral
      </button>
    </Html>
  )
}
```

Outside components, `import { startTransition } from 'react'` and wrap the store update. This is the escape hatch for pitfall 6's "unavoidable mount" case — it does not make mounting cheap, it stops it from blocking.

## React State Discipline

The organizing principle for games and state-heavy apps: **the render loop must never depend on React re-renders.** Components that animate read state imperatively; components that display state subscribe narrowly; the two never share a re-rendering parent.

### Isolate Animated Components

```jsx
// Bad: score state lives in the same component tree node as the animated mesh —
// every point re-renders Scene, and with it the mesh's whole subtree
function Scene() {
  const [score, setScore] = useState(0)
  return (
    <>
      <SpinningLogo />
      <ScoreHud score={score} onHit={() => setScore((s) => s + 1)} />
    </>
  )
}

// Good: state lives in a store; only the HUD subscribes; Scene renders once
import { create } from 'zustand'

const useGame = create((set) => ({
  score: 0,
  addPoint: () => set((state) => ({ score: state.score + 1 })),
}))

function Scene() {
  return (
    <>
      <SpinningLogo />
      <ScoreHud />
    </>
  )
}

function ScoreHud() {
  const score = useGame((state) => state.score)
  return <Html>{score}</Html>
}
```

The same selector discipline applies to `useThree` — subscribe to slices (`useThree((s) => s.camera)`), never the whole state object, or every resize/dpr change re-renders you (see [hooks.md](./hooks.md)).

### Read Stores Imperatively in useFrame

`store.getState()` is a plain function call — fresh value, no subscription, no re-render. The default pattern for anything consumed per frame:

```jsx
function Player() {
  const ref = useRef(null)
  useFrame((state, delta) => {
    const { targetX } = useGame.getState()
    ref.current.position.x = THREE.MathUtils.damp(ref.current.position.x, targetX, 4, delta)
  })
  return <mesh ref={ref}>{/* ... */}</mesh>
}
```

### Transient Subscriptions (subscribeWithSelector)

To react to a specific store change *without* re-rendering — e.g. snap a mesh when a value changes rather than polling every frame — subscribe with a selector and mutate refs in the callback. In zustand v5 the selector form of `subscribe` **requires the `subscribeWithSelector` middleware**; the vanilla `subscribe(listener)` only takes a single whole-state listener:

```jsx
import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

const useGame = create(
  subscribeWithSelector((set) => ({
    playerPosition: [0, 0, 0],
  }))
)

function Enemy() {
  const ref = useRef(null)
  useEffect(
    () =>
      useGame.subscribe(
        (state) => state.playerPosition,
        ([x, y, z]) => ref.current.lookAt(x, y, z)
      ),
    []
  )
  return <mesh ref={ref}>{/* ... */}</mesh>
}
```

### Multi-Value Selectors: useShallow

A selector returning a fresh object re-renders on every store change (new reference each time). Wrap it in `useShallow`:

```jsx
import { useShallow } from 'zustand/react/shallow'

function Hud() {
  const { health, ammo } = useGame(useShallow((s) => ({ health: s.health, ammo: s.ammo })))
  return <Html>{health} / {ammo}</Html>
}
```

**Legacy note (zustand v4):** the second-argument equality overload `useStore(selector, shallow)` is **removed in zustand 5**. Code or examples using `import { shallow } from 'zustand/shallow'` as a second argument are v4-era — migrate to `useShallow`.

## Profiling

`r3f-perf` is the standard in-canvas profiler — FPS, CPU/GPU frame time, draw calls, triangles, and geometry/texture memory:

```jsx
import { Perf } from 'r3f-perf'

<Canvas>
  {import.meta.env.DEV && <Perf position="top-left" />}
  <Scene />
</Canvas>
```

Lighter options: drei `<StatsGl />` / `<Stats />` (FPS meters), and the renderer's own counters — `gl.info.render.calls`, `gl.info.render.triangles`, `gl.info.memory.geometries`, `gl.info.memory.textures` — for asserting the draw-call budget in tests or logs.

What to look at first: draw calls over ~1000 → [instancing](#instancing-and-the-draw-call-budget); sawtooth frame times → allocations in the loop (pitfall 7); a hitch on mount/toggle → shader compiles from mount/unmount churn (pitfalls 1 and 6); steady but low FPS with few calls → fill rate, clamp [dpr](#adaptive-quality-and-movement-regression).

## Common Mistakes

| Mistake | Fix |
|---|---|
| Scene hitches every few seconds with a sawtooth frame-time graph | GC pressure from `new THREE.Vector3()`/`Color`/arrays inside `useFrame` — hoist one temp and `.set()` it per frame |
| Animation runs twice as fast on a 120 Hz monitor | Fixed per-frame increments — multiply by `delta` (units per second) |
| FPS collapses while the pointer moves across the scene | `setState` in `onPointerMove` — mutate refs instead; add drei `<AdaptiveEvents />` |
| Whole component tree re-renders at animation rate | Fast-changing store value bound to a prop (pitfall 5) — read `store.getState()` inside `useFrame` |
| `frameloop="demand"` scene freezes after dragging raw OrbitControls | Controls `change` event not wired to `invalidate()` — add the listener, or use drei controls which do it automatically |
| Visible hitch every time a component mounts or a conditional flips | Shader compile + buffer upload from mount/unmount churn — toggle `visible={}` instead; wrap unavoidable mounts in `startTransition` |
| Shared material/geometry breaks when one consumer unmounts | R3F auto-disposed it — set `dispose={null}` on elements using shared assets |
| `store.subscribe(selector, callback)` misbehaves or callback receives whole state | zustand v5 requires the `subscribeWithSelector` middleware for the selector overload |
| Type error / re-render storm from `useStore(selector, shallow)` after upgrading | The v4 second-arg overload is gone in zustand 5 — wrap the selector in `useShallow` |
| Thousands of simple meshes are slow despite cheap materials | Draw-call bound (~1000 budget) — `<instancedMesh>` or drei `<Instances>`/`<Merged>` |
| Instances disappear at screen edges when they move far from origin | Single-object frustum culling on `instancedMesh` — set `frustumCulled={false}` |
| Texture/model refetched on every mount | Ad-hoc loader in `useEffect` — `useLoader`/`useGLTF` cache by URL |
| Phone runs hot and slow at full retina resolution | Unclamped dpr — keep the default `dpr={[1, 2]}`, let `<PerformanceMonitor>` drive it down further |

## See Also

- [hooks.md](./hooks.md) — `useFrame` priorities and `useThree` selector subscriptions.
- [animation.md](./animation.md) — lerp/damp/spring techniques the loop-discipline rules assume.
- [loading-assets.md](./loading-assets.md) — `useLoader` caching, `useGLTF`, preloading, gltfjsx.
- [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md) — `args` reconstruction semantics, `attach`, disposal.
- [../SKILL.md](../SKILL.md) — version matrix and skill overview.
- Official: [Performance pitfalls](https://r3f.docs.pmnd.rs/advanced/pitfalls) · [Scaling performance](https://r3f.docs.pmnd.rs/advanced/scaling-performance) · [drei performance helpers](https://github.com/pmndrs/drei#performance)
