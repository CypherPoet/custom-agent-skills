# Animation

Everything that moves: `useFrame` mutation patterns, damping and lerp idioms, GLTF clip playback with drei's `useAnimations`, morph targets, bones, `@react-spring/three`, and drei's `Float`/`Trail` helpers. Applies to R3F v9 + React 19 + drei 10; setup and version pairing live in [../SKILL.md](../SKILL.md).

## Table of Contents

| Section | Covers |
|---|---|
| [The useFrame Mutation Pattern](#the-useframe-mutation-pattern) | Delta-scaled ref mutation, current pointer and store access, component isolation, callback priorities, on-demand invalidation, and pausing without unmounting |
| [Smooth Follow and Lerp](#smooth-follow-and-lerp) | Scalar lerp versus frame-rate-independent damping, delta-correct vector interpolation, and reuse of temporary vectors, quaternions, and colors |
| [Damping with maath](#damping-with-maath) | Allocation-free numeric, vector, Euler, quaternion, color, and spherical damping, target forms, convergence reporting, and camera-rig use |
| [GLTF Clips with useAnimations](#gltf-clips-with-useanimations) | Clip and root binding, action and mixer controls, reset-safe crossfades, continuous locomotion blends, playback direction and looping, and cleaned-up mixer events |
| [Morph Targets](#morph-targets) | Locating blend-shape dictionaries and influence arrays, driving weights from live data, and playing clip-authored morph animation |
| [Skeletal Animation](#skeletal-animation) | Bone lookup and frame mutation, ordering manual overrides after the animation mixer, and attaching and removing props in bone space |
| [React Spring](#react-spring) | Animated element wrappers, preset and custom physics, interruptible lists, chained sequences, and choosing event-driven springs versus continuous frame damping |
| [Drei Float and Trail](#drei-float-and-trail) | `Float` hover and tumble plus `Trail` ribbons with child or external targets, width, length, decay, and attenuation controls |
| [Throttling Expensive Work](#throttling-expensive-work) | Separating per-frame mutations from throttled raycasts, layout, and network work |
| [Other Animation Libraries](#other-animation-libraries) | `framer-motion-3d` (declarative `motion.mesh` variants/gestures) exists but was built against R3F v8 / React 18 |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## The useFrame Mutation Pattern

`useFrame((state, delta, xrFrame) => {...}, renderPriority?)` runs every frame just before render. `delta` is the time since the last frame in seconds. Animate by **mutating three.js objects through refs** — never call `setState` inside the callback, and never bind fast-changing values to JSX props. React re-renders cost far more than a mutation and will stutter the loop (full doctrine: [performance.md](./performance.md)).

```jsx
import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'

function Spinner() {
  const meshRef = useRef(null)

  useFrame((state, delta) => {
    meshRef.current.rotation.y += delta // 1 radian per second at any refresh rate
    meshRef.current.position.y = Math.sin(state.clock.elapsedTime) * 0.5
  })

  return (
    <mesh ref={meshRef}>
      <boxGeometry />
      <meshStandardMaterial color="hotpink" />
    </mesh>
  )
}
```

Rules that keep the loop smooth:

- **Scale every increment by `delta`.** `rotation.y += 0.01` runs twice as fast on a 120 Hz display. `rotation.y += delta * speed` is refresh-rate independent.
- **Read `state.pointer`, not `state.mouse`** — `mouse` is deprecated.
- **Isolate animated components.** A parent re-rendering (score counters, HUD state) re-renders its children and janks their `useFrame` work. Give the animated mesh its own component with no reactive props.
- **Pull external state imperatively.** With zustand, read `useStore.getState()` inside the callback instead of subscribing via the hook — see [performance.md](./performance.md) for transient-subscription patterns.
- Passing a **positive `renderPriority`** disables R3F's automatic render — you are taking over the render call. Negative priorities only order callbacks and do not take over. Details in [hooks.md](./hooks.md).
- Continuous `useFrame` animation assumes `frameloop="always"` (the default). Under `frameloop="demand"` nothing schedules frames for you — call `invalidate()` or switch modes ([performance.md](./performance.md)).

Conditional animation stays cheap by early-returning, not by unmounting the component:

```jsx
useFrame((state, delta) => {
  if (!enabledRef.current) return
  meshRef.current.rotation.y += delta
})
```

## Smooth Follow and Lerp

Move *toward* targets instead of snapping. Two scalar helpers from three.js:

- `THREE.MathUtils.lerp(x, y, t)` — plain interpolation. With a constant `t` per frame this converges **faster at higher frame rates** (more steps per second).
- `THREE.MathUtils.damp(x, y, lambda, delta)` — frame-rate-independent exponential decay toward `y`. Prefer it (or maath, next section) whenever the code must behave identically at 60 and 144 Hz.

```jsx
useFrame((state, delta) => {
  meshRef.current.position.x = THREE.MathUtils.damp(
    meshRef.current.position.x,
    active ? 2 : 0,
    4, // lambda: higher = snappier
    delta,
  )
})
```

For vectors, use `vector.lerp(target, alpha)` with a **temp vector hoisted out of the callback**. Allocating `new THREE.Vector3()` inside `useFrame` creates 60+ garbage objects per second and causes GC hitches:

```jsx
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'

const vec = new THREE.Vector3() // reused every frame, allocated once

function PointerFollower() {
  const meshRef = useRef(null)

  useFrame(({ pointer, viewport }, delta) => {
    vec.set((pointer.x * viewport.width) / 2, (pointer.y * viewport.height) / 2, 0)
    meshRef.current.position.lerp(vec, 1 - Math.exp(-8 * delta))
  })

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.3]} />
      <meshStandardMaterial color="skyblue" />
    </mesh>
  )
}
```

`1 - Math.exp(-lambda * delta)` is the frame-rate-independent alpha; a fixed `lerp(vec, 0.1)` is acceptable for quick prototypes but ties feel to refresh rate. The same hoisted-temp rule applies to `Quaternion.slerp`, `Color.lerp`, and any per-frame math object.

## Damping with maath

`maath` (a pmndrs package; last published 2024-07 but stable and widely used) ships `easing.damp*` helpers that smooth-damp any three.js type in one line. `smoothTime` is roughly the seconds needed to reach the target; each call returns `true` while still moving.

```jsx
import { easing } from 'maath'

useFrame((state, delta) => {
  easing.damp3(meshRef.current.position, [x, y, z], 0.25, delta)
  easing.dampE(meshRef.current.rotation, [0, targetY, 0], 0.2, delta)
  easing.dampC(meshRef.current.material.color, hovered ? 'hotpink' : 'orange', 0.15, delta)
})
```

| Helper | Damps | Target accepts |
|---|---|---|
| `easing.damp(obj, "key", target, smoothTime, delta)` | a numeric property | number |
| `easing.damp2 / damp3 / damp4` | Vector2 / Vector3 / Vector4 | array, scalar, or vector |
| `easing.dampE` | Euler | array or Euler |
| `easing.dampQ` | Quaternion | Quaternion |
| `easing.dampC` | Color | color name, hex, array, or Color |
| `easing.dampS` | Spherical | array or Spherical |

This is the modern replacement for hand-rolled lerp chains: frame-rate independent, allocation-free, and it composes cleanly with camera rigs (`easing.damp3(state.camera.position, ...)` then `camera.lookAt(...)`).

## GLTF Clips with useAnimations

drei's `useAnimations(clips, root?)` binds `AnimationClip`s to a scene graph and returns `{ ref, actions, names, clips, mixer }`. `actions` is keyed by clip name; `names` lists them; `mixer` is the underlying `THREE.AnimationMixer` (drei advances it internally every frame). Pass a root ref/object as the second argument, or attach the returned `ref` yourself:

```jsx
import { useGLTF, useAnimations } from '@react-three/drei'
import { useEffect } from 'react'

function Character(props) {
  const { scene, animations } = useGLTF('/models/character.glb')
  const { ref, actions, names } = useAnimations(animations)

  useEffect(() => {
    actions[names[0]]?.reset().fadeIn(0.3).play()
  }, [actions, names])

  return <primitive ref={ref} object={scene} {...props} />
}
```

Clip names come from the DCC tool — log `names` when an action lookup returns `undefined`. Loading, Suspense, and `useGLTF` caching are covered in [loading-assets.md](./loading-assets.md).

### Action Control Surface

Each `actions[name]` is a `THREE.AnimationAction`:

| Call / property | Effect |
|---|---|
| `action.play()` / `action.stop()` | Start / hard-stop (stop deactivates immediately, no fade) |
| `action.reset()` | Rewind to time 0, unpause, re-enable — the usual prefix before `fadeIn` |
| `action.paused = true` | Freeze at the current time |
| `action.timeScale = 1.5` | Playback speed; `-1` plays in reverse (set `action.time = action.getClip().duration` first when starting from the end) |
| `action.setLoop(THREE.LoopOnce, 1)` | Play once, then emit `finished` |
| `action.setLoop(THREE.LoopRepeat, Infinity)` | Default looping |
| `action.setLoop(THREE.LoopPingPong, reps)` | Alternate forward/backward for `reps` passes |
| `action.clampWhenFinished = true` | Hold the last frame after `LoopOnce` instead of snapping back to frame 0 |
| `action.fadeIn(s)` / `action.fadeOut(s)` | Ramp weight over `s` seconds |
| `action.crossFadeTo(other, s, warp)` | Fade this action out while `other` fades in |
| `action.setEffectiveWeight(w)` | Blend contribution, 0–1 |
| `action.setEffectiveTimeScale(s)` | Set playback speed and cancel any scheduled warping |
| `mixer.timeScale = 0.5` | Global slow motion across every action |

### Crossfading Between Clips

The idiomatic crossfade uses effect cleanup — when the `animation` prop changes, the old action fades out as the new one fades in:

```jsx
function Character({ animation = 'Idle' }) {
  const { scene, animations } = useGLTF('/models/character.glb')
  const { ref, actions } = useAnimations(animations)

  useEffect(() => {
    const action = actions[animation]
    action?.reset().fadeIn(0.5).play()
    return () => {
      action?.fadeOut(0.5)
    }
  }, [animation, actions])

  return <primitive ref={ref} object={scene} />
}
```

`reset()` before `fadeIn()` matters: a previously-finished action sits at its end time with zero weight, and fading it back in without resetting blends in a frozen final pose. The manual variant — fade out everything, then fade in the target — works too:

```jsx
Object.values(actions).forEach((action) => action?.fadeOut(0.5))
actions[next]?.reset().fadeIn(0.5).play()
```

### Speed-Based Blend Trees

Keep several locomotion clips playing simultaneously and drive their weights per frame — no discrete transitions, just continuous blending:

```jsx
import * as THREE from 'three'

function Locomotion({ speedRef }) {
  const { scene, animations } = useGLTF('/models/character.glb')
  const { ref, actions } = useAnimations(animations)

  useEffect(() => {
    for (const name of ['Idle', 'Walk', 'Run']) actions[name]?.play()
  }, [actions])

  useFrame(() => {
    const speed = speedRef.current
    const walk = THREE.MathUtils.clamp(speed / 4, 0, 1)
    const run = THREE.MathUtils.clamp((speed - 4) / 4, 0, 1)
    actions.Idle?.setEffectiveWeight(1 - walk)
    actions.Walk?.setEffectiveWeight(walk - run)
    actions.Run?.setEffectiveWeight(run)
  })

  return <primitive ref={ref} object={scene} />
}
```

Matching walk/run cycle phases (same stride timing in the DCC export) makes the blend read as one motion.

### Mixer Events

The mixer emits `finished` (after `LoopOnce` completes; `e.action`, `e.direction`) and `loop` (each repeat; `e.action`, `e.loopDelta`). Always remove listeners in cleanup:

```jsx
useEffect(() => {
  const onFinished = (e) => {
    if (e.action === actions.Death) onDeathComplete()
  }
  mixer.addEventListener('finished', onFinished)
  return () => mixer.removeEventListener('finished', onFinished)
}, [mixer, actions, onDeathComplete])
```

Calling `setState` here is fine — mixer events fire from discrete transitions, not per frame.

## Morph Targets

Morph (blend-shape) meshes expose `morphTargetDictionary` (name → index) and `morphTargetInfluences` (parallel array of 0–1 weights) on the mesh itself — usually a child in `nodes`, never the scene root:

```jsx
function Face() {
  const { nodes } = useGLTF('/models/face.glb')
  const face = nodes.Face

  useFrame(({ clock }) => {
    const smile = face.morphTargetDictionary['smile']
    face.morphTargetInfluences[smile] = (Math.sin(clock.elapsedTime) + 1) / 2
  })

  return <primitive object={face} />
}
```

Driving influences from external data (audio amplitude, sliders, ARKit blendshape streams) is the same pattern — write into `morphTargetInfluences[index]` inside `useFrame`. GLTF files whose animation clips key morph weights need no manual work: `useAnimations` plays them like any other clip.

## Skeletal Animation

Bones are `Object3D`s — find them with `scene.getObjectByName('BoneName')` or `skinnedMesh.skeleton.bones.find((b) => b.name === 'BoneName')`, then mutate per frame.

**Ordering gotcha:** drei's `useAnimations` advances the mixer in its own internal `useFrame`, and same-priority callbacks run in subscription order. If a clip animates the bone you're editing, register your `useFrame` **after** the `useAnimations` call in the same component so your write lands after the mixer's — otherwise the mixer silently overwrites it every frame:

```jsx
import { useMemo } from 'react'

function HeadTracker() {
  const { scene, animations } = useGLTF('/models/character.glb')
  const { ref, actions } = useAnimations(animations)
  const head = useMemo(() => scene.getObjectByName('mixamorigHead'), [scene])

  useEffect(() => {
    actions.Idle?.play()
  }, [actions])

  // Called after useAnimations, so this runs after mixer.update each frame
  useFrame(({ pointer }) => {
    head.rotation.y = pointer.x * 0.6
    head.rotation.x = -pointer.y * 0.4
  })

  return <primitive ref={ref} object={scene} />
}
```

Attach props (weapons, hats) to a bone imperatively, with cleanup so unmounting the prop doesn't leave a dangling child on the skeleton:

```jsx
function Sword({ bone }) {
  const swordRef = useRef(null)

  useEffect(() => {
    const sword = swordRef.current
    bone.add(sword)
    return () => bone.remove(sword)
  }, [bone])

  return (
    <mesh ref={swordRef} position={[0, 0.1, 0]}>
      <boxGeometry args={[0.05, 0.05, 1]} />
      <meshStandardMaterial color="silver" metalness={1} roughness={0.3} />
    </mesh>
  )
}
```

The prop inherits the bone's animated transform automatically; its own `position`/`rotation` become offsets in bone space.

## React Spring

`@react-spring/three` animates values with spring physics **outside the React render loop** — no re-render per frame. Wrap elements with `animated.*` (alias `a.*`) and feed them spring values:

```jsx
import { useSpring, animated, config } from '@react-spring/three'
import { useState } from 'react'

function Toggle() {
  const [active, setActive] = useState(false)
  const { scale, color } = useSpring({
    scale: active ? 1.5 : 1,
    color: active ? '#ff6b6b' : '#4ecdc4',
    config: config.wobbly,
  })

  return (
    <animated.mesh scale={scale} onClick={() => setActive(!active)}>
      <boxGeometry />
      <animated.meshStandardMaterial color={color} />
    </animated.mesh>
  )
}
```

A plain `<mesh scale={scale}>` receives the spring object, not its animated value — the `animated.` wrapper is what subscribes to updates.

### Presets and Custom Config

Presets: `config.default`, `config.gentle`, `config.wobbly`, `config.stiff`, `config.slow`, `config.molasses`. Or tune directly:

```jsx
const spring = useSpring({
  position: [0, 2, 0],
  config: { mass: 1, tension: 170, friction: 26, clamp: false, precision: 0.01 },
})
```

Higher `tension` = snappier; higher `friction` = more damped; `clamp: true` stops at the target without overshoot.

### Lists with useSprings

```jsx
import { useSprings, animated } from '@react-spring/three'

function Boxes({ count = 5 }) {
  const [springs, api] = useSprings(count, (i) => ({
    position: [i * 2 - count + 1, 0, 0],
    scale: 1,
  }))

  return springs.map((spring, i) => (
    <animated.mesh
      key={i}
      position={spring.position}
      scale={spring.scale}
      onClick={() => api.start((j) => ({ scale: j === i ? 1.5 : 1 }))}
    >
      <boxGeometry />
      <meshStandardMaterial color="orange" />
    </animated.mesh>
  ))
}
```

`api.start` retargets any subset imperatively — the springs interrupt and redirect mid-flight without snapping.

### Sequencing with useChain

```jsx
import { useSpring, animated, useChain, useSpringRef } from '@react-spring/three'

function Entrance() {
  const scaleRef = useSpringRef()
  const spinRef = useSpringRef()

  const { scale } = useSpring({ ref: scaleRef, from: { scale: 0 }, to: { scale: 1 } })
  const { rotation } = useSpring({
    ref: spinRef,
    from: { rotation: [0, 0, 0] },
    to: { rotation: [0, Math.PI * 2, 0] },
  })

  useChain([scaleRef, spinRef], [0, 0.5]) // scale first, spin starts at 50%

  return (
    <animated.mesh scale={scale} rotation={rotation}>
      <boxGeometry />
      <meshStandardMaterial color="cyan" />
    </animated.mesh>
  )
}
```

### Springs vs Frame-Loop Damping

| Use `@react-spring/three` when | Use `useFrame` + damp/lerp when |
|---|---|
| Discrete, event-driven transitions (click → scale up, open → slide in) | The target changes continuously (cursor followers, camera rigs, chase logic) |
| You want physical overshoot/bounce and interruptible retargeting | The target derives from other per-frame values (another object's position) |
| Sequencing/orchestration across elements (`useChain`, trails) | You're already in a `useFrame` for other reasons — one damp line is cheaper than a spring |

Both avoid per-frame React renders; the split is about where the target comes from, not performance.

## Drei Float and Trail

`Float` adds gentle idle hover/tumble to its children — the zero-effort "make it feel alive" wrapper:

```jsx
import { Float } from '@react-three/drei'

<Float
  speed={1}                    // animation speed multiplier
  rotationIntensity={1}        // tumble amount
  floatIntensity={1}           // bob amount
  floatingRange={[-0.1, 0.1]}  // y-range of the bob
>
  <mesh>
    <icosahedronGeometry />
    <meshStandardMaterial color="gold" />
  </mesh>
</Float>
```

`Trail` draws a fading ribbon behind a moving child (or behind `target`, a ref to any object elsewhere in the scene):

```jsx
import { Trail } from '@react-three/drei'

<Trail width={2} length={8} color="hotpink" decay={1} attenuation={(t) => t * t}>
  <mesh ref={orbiterRef}>
    <sphereGeometry args={[0.2]} />
    <meshStandardMaterial color="white" />
  </mesh>
</Trail>
```

Animated materials (`MeshWobbleMaterial`, `MeshDistortMaterial`) and the broader helper catalog live in [staging-and-drei.md](./staging-and-drei.md).

## Throttling Expensive Work

Cheap mutations run every frame; expensive periodic work (raycasts, pathfinding, LOD decisions, network sync) accumulates `delta` and fires on an interval:

```jsx
function Agent() {
  const meshRef = useRef(null)
  const acc = useRef(0)

  useFrame((state, delta) => {
    meshRef.current.rotation.y += delta // cheap: every frame

    acc.current += delta
    if (acc.current < 0.1) return // expensive path: ~10× per second
    acc.current = 0
    recomputePath(meshRef.current.position)
  })
}
```

Subtract the interval (`acc.current -= 0.1`) instead of zeroing when the periodic work must average an exact rate; zeroing is fine for "at most every N ms" semantics.

## Other Animation Libraries

`framer-motion-3d` (declarative `motion.mesh` variants/gestures) exists but was built against R3F v8 / React 18, and its upstream has deprecated the React Three Fiber integration — verify current compatibility before adopting it. For new R3F v9 work, `@react-spring/three` and maath damping cover the same ground and are maintained within the pmndrs ecosystem.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Animation stutters whenever unrelated UI state updates | `setState` in `useFrame`, or the animated mesh shares a component with reactive state. Mutate refs only; isolate the animated component; read stores via `getState()` ([performance.md](./performance.md)) |
| Motion runs twice as fast on a 120 Hz monitor | Fixed per-frame increments (`+= 0.01`). Scale everything by `delta` |
| Periodic GC hitches; sawtooth memory in the profiler | `new THREE.Vector3()` (or Color/Quaternion) allocated inside `useFrame`. Hoist one temp outside the callback and `.set()` it |
| Smooth-follow feels different across machines | Constant-alpha `lerp(v, 0.1)`. Use `THREE.MathUtils.damp`, `maath easing.damp*`, or `1 - Math.exp(-lambda * delta)` as the alpha |
| `actions['Walk']` is `undefined` | Clip name mismatch — log `names` from `useAnimations`; confirm the root passed to `useAnimations` contains the skinned mesh the clips target |
| Crossfade snaps in a frozen pose instead of blending | Fading in a finished action without rewinding. Always `action.reset().fadeIn(0.5).play()` |
| `LoopOnce` clip pops back to the first frame when done | Set `action.clampWhenFinished = true` before playing |
| `timeScale = -1` plays nothing | Starting reverse playback from time 0 finishes instantly. Set `action.time = action.getClip().duration` first |
| Bone rotation written in `useFrame` has no visible effect | The mixer overwrites clip-driven bones. Register your `useFrame` after the `useAnimations` call so it runs post-mixer |
| Spring values don't animate; mesh jumps instantly | Spring passed to a plain `<mesh>`. Use `<animated.mesh>` / `<a.mesh>` (and `<animated.meshStandardMaterial>` for material props) |
| Everything freezes under `frameloop="demand"` | `useFrame` mutations don't schedule frames on demand. Call `invalidate()` after changes, or use `frameloop="always"` ([performance.md](./performance.md)) |
| Morph slider does nothing | `morphTargetDictionary`/`morphTargetInfluences` live on the child mesh (find it in `nodes`), not the GLTF scene root |

## See Also

- [hooks.md](./hooks.md) — `useFrame` priorities and render takeover, `useThree` selectors, the full state object
- [performance.md](./performance.md) — never-setState doctrine, on-demand rendering, transient store subscriptions, instancing
- [loading-assets.md](./loading-assets.md) — `useGLTF`, gltfjsx output, Suspense boundaries for animated models
- [staging-and-drei.md](./staging-and-drei.md) — `MeshWobbleMaterial`/`MeshDistortMaterial` and the wider drei helper catalog
- [../SKILL.md](../SKILL.md) — version pairing and project setup
- [three.js AnimationAction docs](https://threejs.org/docs/#api/en/animation/AnimationAction) — full action/mixer API
- [react-spring docs](https://www.react-spring.dev/) — complete spring API (`@react-spring/three` shares it)
- [maath repository](https://github.com/pmndrs/maath) — `easing.damp*` sources and demos
