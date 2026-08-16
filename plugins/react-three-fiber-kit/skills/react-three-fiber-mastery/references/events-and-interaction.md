# Events & Interaction

R3F raycasts DOM pointer input against the scene and delivers React-style synthetic events — with bubbling, `stopPropagation`, and pointer capture — on any object that has a `raycast` method. This file covers the event system plus the drei interaction catalog: camera controls, transform/drag gizmos, keyboard input, and scroll rigs. Assumes R3F v9 + drei 10 + React 19.

> Canvas-level event props (`events`, `eventSource`, `eventPrefix`, `onPointerMissed`) and general setup: see [canvas-and-project-setup.md](./canvas-and-project-setup.md) and [../SKILL.md](../SKILL.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Event Catalog](#event-catalog) | Attach handlers directly to any object with a `raycast` method (mesh, line, points, sprite) |
| [Event Data](#event-data) | Every handler receives a `ThreeEvent`: the native DOM event spread together with the `THREE.Intersection` for this hit |
| [Occlusion and Propagation](#occlusion-and-propagation) | The raycaster returns all intersected objects sorted nearest-first |
| [Pointer Capture](#pointer-capture) | Standard DOM API, R3F-routed: capture on pointerdown, release on pointerup |
| [Raycast Tuning](#raycast-tuning) | Override hit-testing per object with the `raycast` prop |
| [Hover and Cursor](#hover-and-cursor) | Hover boundaries are discrete events — setState here is fine (unlike per-frame updates) |
| [Custom Event Manager and Event Source](#custom-event-manager-and-event-source) | Replace or extend the event system through the Canvas `events` prop — a factory `(state) => EventManager` |
| [Camera Controls](#camera-controls) | Orbit, Map, Trackball, Fly, PointerLock, and Transform controls from Drei |
| [Transform and Drag Controls](#transform-and-drag-controls) | TransformControls, PivotControls, and DragControls with controlled matrices, snapping, axis locks, and camera-control coordination |
| [Keyboard Controls](#keyboard-controls) | `KeyboardControls` wraps the app (outside `<Canvas>` is fine) with a key map; `useKeyboardControls` reads it two ways |
| [Scroll and Presentation Controls](#scroll-and-presentation-controls) | ScrollControls creates a scrollable HTML zone over the canvas and exposes progress to the scene — the scrollytelling primitive |
| [Screen and World Coordinates](#screen-and-world-coordinates) | Screen → world, the easy case: if the pointer hit a mesh, `e.point` already is the world-space position |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## Event Catalog

Attach handlers directly to any object with a `raycast` method (mesh, line, points, sprite). Groups receive events through bubbling from child hits. Mouse, touch, and pen are unified as pointer events.

```jsx
<mesh
  onClick={(e) => console.log('click')}
  onContextMenu={(e) => console.log('right-click / long-press')}
  onDoubleClick={(e) => console.log('double click')}
  onWheel={(e) => console.log('wheel', e.deltaY)}
  onPointerDown={(e) => console.log('down')}
  onPointerUp={(e) => console.log('up')}
  onPointerMove={(e) => console.log('move while over')}
  onPointerOver={(e) => console.log('over')}
  onPointerOut={(e) => console.log('out')}
  onPointerEnter={(e) => console.log('enter')} // caveat: behaves like over
  onPointerLeave={(e) => console.log('leave')} // caveat: behaves like out
  onPointerMissed={() => console.log('a click missed THIS object')}
/>
```

- `onPointerEnter`/`onPointerLeave` are **not fully implemented** — they behave exactly like `onPointerOver`/`onPointerOut` (they bubble). Do not rely on DOM enter/leave (non-bubbling) semantics.
- `onPointerMissed` exists at two levels: on an object it fires when a click lands somewhere that misses *that* object; on `<Canvas onPointerMissed={...}>` it fires when a click hits *nothing* — the standard deselect hook:

```jsx
<Canvas onPointerMissed={() => setSelected(null)}>
```

- `onUpdate` sits in the same prop namespace but is **not** a pointer event — it is a callback invoked with the object after its props update.

## Event Data

Every handler receives a `ThreeEvent`: the native DOM event spread together with the `THREE.Intersection` for this hit, plus R3F extras.

| Field | Type | Meaning |
|---|---|---|
| *(DOM spread)* | — | Native event props: `clientX/Y`, `shiftKey`, `timeStamp`, `deltaY` (wheel), … |
| *(Intersection spread)* | — | This hit's `point` (world coords), `distance`, `face`, `faceIndex`, `uv`, `normal`, `instanceId` |
| `intersections` | `Intersection[]` | First hit of *every* object the ray intersected, nearest-first |
| `object` | `Object3D` | The object the ray actually hit |
| `eventObject` | `Object3D` | The object the handler is registered on (changes as the event bubbles) |
| `unprojectedPoint` | `Vector3` | Pointer NDC unprojected into world space through the camera |
| `ray` | `THREE.Ray` | The ray used for this raycast |
| `camera` | `Camera` | The camera used for the raycast |
| `pointer` | `Vector2` | Normalized device coords of the pointer (−1..1) |
| `delta` | `number` | Screen-pixel distance between pointerdown and pointerup |
| `nativeEvent` / `sourceEvent` | DOM event | The underlying DOM event object |
| `stopPropagation()` | `() => void` | Stops bubbling AND delivery to occluded objects behind |

`object` vs `eventObject` matters on group handlers:

```jsx
<group onClick={(e) => {
  console.log(e.object.name)      // the child mesh the ray hit
  console.log(e.eventObject.name) // this group — the handler owner
}}>
  <mesh name="a">…</mesh>
  <mesh name="b">…</mesh>
</group>
```

**Click-vs-drag detection** — `delta` is the pixel distance the pointer travelled between down and up. With orbit controls active, every drag ends in a `click`; gate on `delta`:

```jsx
<mesh
  onClick={(e) => {
    if (e.delta > 2) return // pointer moved >2px: that was a camera drag
    e.stopPropagation()
    select(e.object)
  }}
/>
```

## Occlusion and Propagation

The raycaster returns all intersected objects sorted nearest-first. The event fires on the nearest hit, bubbles up that object's ancestors (with `eventObject` updated at each level), then — unlike the DOM — **continues to the next object behind it**, and so on through `intersections`.

`e.stopPropagation()` cuts both paths at once: no further ancestor bubbling, and no delivery to occluded objects behind. Objects behind that were in hover state receive an immediate `pointerout` when blocked during over/move.

**Occluder pattern** — a mesh only blocks events it actually handles. To make a mesh occlude events *without* doing anything itself, register handlers that only call `stopPropagation`:

```jsx
function Occluder() {
  return (
    <mesh
      onPointerOver={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
    >
      <planeGeometry args={[4, 4]} />
      <meshStandardMaterial />
    </mesh>
  )
}
```

Conversely, in a selection UI call `e.stopPropagation()` in the nearest object's handler so a click selects only the front object rather than everything along the ray.

## Pointer Capture

Standard DOM API, R3F-routed: capture on pointerdown, release on pointerup. While captured, the object keeps receiving move/up events even when the ray leaves it — essential for dragging.

```jsx
<mesh
  onPointerDown={(e) => {
    e.stopPropagation()
    e.target.setPointerCapture(e.pointerId)
  }}
  onPointerUp={(e) => e.target.releasePointerCapture(e.pointerId)}
  onPointerMove={(e) => {/* keeps firing while captured — see Screen and World Coordinates */}}
/>
```

R3F difference from the DOM: the capturing object is **added to** each raycast's hit results — it does not *replace* them, so other objects under the pointer still receive their events. Multiple simultaneously active pointers are not supported. Full drag idiom (capture + math-plane intersection): [Screen and World Coordinates](#screen-and-world-coordinates).

## Raycast Tuning

Override hit-testing per object with the `raycast` prop:

```jsx
import { meshBounds } from '@react-three/drei'

<mesh raycast={() => null} />                       // opt out: never hit-tested
<mesh raycast={meshBounds} onClick={handleClick} /> // cheap bounds test instead of per-triangle
```

`meshBounds` raycasts the bounding sphere and box only — near-free for high-poly meshes; imprecise silhouettes are usually acceptable for click targets, not for precision picking.

**Invisible proxy collider** — pair a complex visible mesh (raycast disabled) with a simple invisible hit mesh:

```jsx
<group>
  <mesh raycast={() => null}>
    <torusKnotGeometry args={[1, 0.4, 256, 64]} />
    <meshStandardMaterial color="purple" />
  </mesh>
  <mesh onClick={select} onPointerOver={hover}>
    <sphereGeometry args={[1.6]} />
    <meshBasicMaterial visible={false} />
  </mesh>
</group>
```

**Throttle `onPointerMove` work.** Move events fire at pointer frequency (often faster than the frame rate). Never setState in them; write into a ref and consume in `useFrame`, which naturally coalesces to one update per frame:

```jsx
import * as THREE from 'three'
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'

function Reticle() {
  const hit = useRef(new THREE.Vector3())
  const reticle = useRef(null)
  useFrame(() => reticle.current.position.copy(hit.current))
  return (
    <>
      <mesh onPointerMove={(e) => hit.current.copy(e.point)}>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial />
      </mesh>
      <mesh ref={reticle}>
        <sphereGeometry args={[0.1]} />
        <meshBasicMaterial color="red" />
      </mesh>
    </>
  )
}
```

For genuinely expensive work (server calls, heavy computation), add a time gate: `if (e.timeStamp - last.current < 50) return`.

## Hover and Cursor

Hover boundaries are discrete events — setState here is fine (unlike per-frame updates). drei's `useCursor` handles the pointer cursor with cleanup:

```jsx
import { useCursor } from '@react-three/drei'
import { useState } from 'react'

function HoverMesh() {
  const [hovered, setHovered] = useState(false)
  useCursor(hovered) // 'pointer' while true, 'auto' otherwise; cleans up on unmount
  return (
    <mesh
      onPointerOver={(e) => { e.stopPropagation(); setHovered(true) }}
      onPointerOut={() => setHovered(false)}
      scale={hovered ? 1.1 : 1}
    >
      <boxGeometry />
      <meshStandardMaterial color={hovered ? 'hotpink' : 'orange'} />
    </mesh>
  )
}
```

`stopPropagation` in `onPointerOver` keeps overlapping objects behind from hovering simultaneously. Manual equivalent: `document.body.style.cursor = 'pointer'` in over, reset in out — but remember unmount cleanup, which `useCursor` does for you.

## Custom Event Manager and Event Source

Replace or extend the event system through the Canvas `events` prop — a factory `(state) => EventManager`. Use it to filter which intersections deliver events or to customize how the pointer maps to a ray:

```jsx
import { Canvas, events } from '@react-three/fiber'

const eventManagerFactory = (state) => ({
  ...events(state),                   // start from the default manager
  filter: (hits) => hits.slice(0, 1), // deliver only the nearest hit
  compute: (event, state) => {
    state.pointer.set(
      (event.offsetX / state.size.width) * 2 - 1,
      -(event.offsetY / state.size.height) * 2 + 1,
    )
    state.raycaster.setFromCamera(state.pointer, state.camera)
  },
})

<Canvas events={eventManagerFactory}>…</Canvas>
```

**DOM overlays on top of the canvas** block pointer events from reaching it. Fix by subscribing events on a shared parent element and switching to client-space coordinates:

```jsx
<div id="app" style={{ position: 'relative' }}>
  <Canvas eventSource={document.getElementById('app')} eventPrefix="client" />
  <div className="overlay">…</div> {/* scene still receives pointer events through this */}
</div>
```

`eventPrefix` selects which DOM coordinate pair feeds the raycast (`'offset'` default, `'client'`, `'page'`, `'layer'`, `'screen'`). Use `'client'` whenever `eventSource` is not the canvas's direct parent. At runtime you can also rebind: `useThree((s) => s.events).connect(domElement)`.

**Camera moved under a still pointer** — events only recompute on pointer motion, so hover states go stale while orbiting. Force a raycast from the controls' change event:

```jsx
import { OrbitControls } from '@react-three/drei'
import { useThree } from '@react-three/fiber'

function Controls() {
  const events = useThree((state) => state.events)
  return <OrbitControls makeDefault onChange={() => events.update()} />
}
```

## Camera Controls

All from `@react-three/drei`. drei controls call `invalidate()` on change automatically, so they work with `frameloop="demand"`, and drive their own per-frame `update()` for damping.

| Control | Use case | Key props / methods |
|---|---|---|
| `OrbitControls` | Default orbit-around-target | `makeDefault`, `target`, `enableDamping` (on by default), `min/maxDistance`, `min/maxPolarAngle`, `min/maxAzimuthAngle`, `autoRotate` |
| `MapControls` | Top-down maps — left-drag pans | Same API as OrbitControls; `screenSpacePanning` |
| `CameraControls` | Animated camera transitions (camera-controls lib) | `setLookAt(px,py,pz, tx,ty,tz, transition)`, `fitToBox` |
| `PointerLockControls` | FPS mouse-look | `.lock()` / `.unlock()`; `selector` prop for click-to-lock |
| `FlyControls` | Free flight | `movementSpeed`, `rollSpeed`, `dragToLook` |
| `FirstPersonControls` | Walk-style look-around | `movementSpeed`, `lookSpeed` |
| `TrackballControls` | Unconstrained rotation, no fixed up-axis | `rotateSpeed`, `zoomSpeed`, `panSpeed` |
| `ArcballControls` | CAD-style arcball with gizmo | `enableAnimations`, `dampingFactor` |

```jsx
import { OrbitControls } from '@react-three/drei'

<OrbitControls
  makeDefault
  target={[0, 1, 0]}
  minDistance={2}
  maxDistance={30}
  minPolarAngle={0}
  maxPolarAngle={Math.PI / 2}   // don't go below the horizon
  minAzimuthAngle={-Math.PI / 4}
  maxAzimuthAngle={Math.PI / 4}
  enableDamping
  dampingFactor={0.05}
/>
```

**`makeDefault` matters**: it writes the instance into R3F state (`useThree((s) => s.controls)`), which is how other drei helpers (TransformControls, Bounds, gizmos) find and cooperate with your controls. Set it on your primary controls as a habit.

**CameraControls** for smooth focus transitions — `setLookAt` with the final `true` animates:

```jsx
import { CameraControls } from '@react-three/drei'
import { useRef } from 'react'

function FocusScene() {
  const controls = useRef(null)
  return (
    <>
      <CameraControls ref={controls} minDistance={2} maxDistance={20} />
      <mesh
        onClick={(e) => {
          e.stopPropagation()
          const { x, y, z } = e.object.position
          controls.current?.setLookAt(x + 3, y + 2, z + 3, x, y, z, true)
        }}
      >
        <boxGeometry />
        <meshStandardMaterial color="red" />
      </mesh>
    </>
  )
}
```

**PointerLockControls** — the browser requires a user gesture to lock:

```jsx
import { PointerLockControls } from '@react-three/drei'

<PointerLockControls selector="#play-button" /> // locks when that DOM element is clicked
// or imperatively: controlsRef.current?.lock() inside an onClick
```

## Transform and Drag Controls

**TransformControls** — translate/rotate/scale gizmo. The classic conflict: dragging the gizmo also orbits the camera. Fix: put `makeDefault` on OrbitControls — drei's TransformControls automatically disables the default controls while dragging. For non-default controls, toggle manually:

```jsx
import { OrbitControls, TransformControls } from '@react-three/drei'

function Editor() {
  return (
    <>
      <OrbitControls makeDefault />  {/* auto-disabled while the gizmo drags */}
      <TransformControls mode="translate" /* 'translate' | 'rotate' | 'scale' */>
        <mesh>
          <boxGeometry />
          <meshStandardMaterial color="orange" />
        </mesh>
      </TransformControls>
    </>
  )
}
```

Also accepts `object={meshRef}` instead of wrapping children, plus `space="local" | "world"`, `translationSnap`, `rotationSnap`, `scaleSnap`, `showX/Y/Z`, and `onMouseDown`/`onMouseUp`/`onObjectChange` callbacks (use the mouse callbacks to toggle `otherControls.enabled` when not using `makeDefault`).

**PivotControls** — combined translate/rotate gizmo with a configurable pivot:

```jsx
import { PivotControls } from '@react-three/drei'

<PivotControls
  anchor={[0, 1, 0]}   // pivot relative to the child's bounding box
  depthTest={false}    // draw the gizmo on top of everything
  fixed                 // constant screen-size gizmo…
  scale={75}            // …scale is then in pixels
  lineWidth={2}
>
  <mesh>
    <boxGeometry />
    <meshStandardMaterial color="orange" />
  </mesh>
</PivotControls>
```

By default it applies its matrix to the children (`autoTransform`); pass `autoTransform={false}` plus `onDrag={(matrix) => …}` for controlled use.

**DragControls (drei)** — drag children on a plane:

```jsx
import { DragControls } from '@react-three/drei'
import { useThree } from '@react-three/fiber'

function Draggables() {
  const controls = useThree((state) => state.controls) // the makeDefault'd controls
  return (
    <DragControls
      axisLock="y" // drag on the plane perpendicular to Y (the ground plane)
      onDragStart={() => controls && (controls.enabled = false)}
      onDragEnd={() => controls && (controls.enabled = true)}
    >
      <mesh>
        <boxGeometry />
        <meshStandardMaterial color="orange" />
      </mesh>
    </DragControls>
  )
}
```

**useDrag from @use-gesture/react + react-spring** — gesture-driven drag with physics. Convert pixel movement to world units via `viewport.factor` (`= size.width / viewport.width`, px per world unit at the camera's target distance); screen Y is inverted:

```jsx
import { useDrag } from '@use-gesture/react'
import { useSpring, animated } from '@react-spring/three'
import { useThree } from '@react-three/fiber'

function DraggableCard() {
  const factor = useThree((state) => state.viewport.factor)
  const [spring, api] = useSpring(() => ({
    position: [0, 0, 0],
    config: { mass: 1, tension: 280, friction: 60 },
  }))
  const bind = useDrag(({ offset: [x, y] }) =>
    api.start({ position: [x / factor, -y / factor, 0] }))
  return (
    <animated.mesh {...bind()} position={spring.position}>
      <boxGeometry />
      <meshStandardMaterial color="hotpink" />
    </animated.mesh>
  )
}
```

## Keyboard Controls

`KeyboardControls` wraps the app (outside `<Canvas>` is fine) with a key map; `useKeyboardControls` reads it two ways.

```jsx
import { KeyboardControls, useKeyboardControls } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useRef } from 'react'

const keyMap = [
  { name: 'forward', keys: ['ArrowUp', 'KeyW'] },
  { name: 'backward', keys: ['ArrowDown', 'KeyS'] },
  { name: 'left', keys: ['ArrowLeft', 'KeyA'] },
  { name: 'right', keys: ['ArrowRight', 'KeyD'] },
  { name: 'jump', keys: ['Space'] },
]

function Player() {
  const mesh = useRef(null)
  const [, getKeys] = useKeyboardControls() // polled reads — no re-renders
  useFrame((state, delta) => {
    const { forward, backward, left, right } = getKeys()
    const speed = 5
    if (forward) mesh.current.position.z -= speed * delta
    if (backward) mesh.current.position.z += speed * delta
    if (left) mesh.current.position.x -= speed * delta
    if (right) mesh.current.position.x += speed * delta
  })
  return (
    <mesh ref={mesh}>
      <boxGeometry />
      <meshStandardMaterial color="blue" />
    </mesh>
  )
}

// <KeyboardControls map={keyMap}><Canvas>…<Player /></Canvas></KeyboardControls>
```

Three read modes — pick by update frequency:

- **Polled** (`const [, getKeys] = useKeyboardControls()`, call `getKeys()` in `useFrame`) — for continuous movement. No re-renders; the performant default.
- **Reactive selector** (`const jump = useKeyboardControls((state) => state.jump)`) — re-renders on change; fine for discrete UI (showing a prompt), wasteful for WASD.
- **Transient subscription** — fire logic on the edge without re-rendering:

```jsx
import { useKeyboardControls } from '@react-three/drei'
import { useEffect } from 'react'

function JumpListener({ onJump }) {
  const [subscribe] = useKeyboardControls()
  useEffect(
    () => subscribe((state) => state.jump, (pressed) => pressed && onJump()),
    [subscribe, onJump],
  )
  return null
}
```

## Scroll and Presentation Controls

**ScrollControls** creates a scrollable HTML zone over the canvas and exposes progress to the scene — the scrollytelling primitive. Props: `pages` (scroll height in viewport-heights), `damping` (smoothing in seconds, default 0.25), `distance`, `horizontal`, `infinite`.

```jsx
import { ScrollControls, Scroll, useScroll } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useRef } from 'react'

function Story() {
  const group = useRef(null)
  const scroll = useScroll()
  useFrame(() => {
    const enter = scroll.range(0, 1 / 3)    // 0→1 across the first third
    const spin = scroll.curve(1 / 3, 1 / 3) // 0→1→0 across the middle third
    group.current.position.y = enter * 2
    group.current.rotation.y = spin * Math.PI
  })
  return (
    <group ref={group}>
      <mesh>
        <boxGeometry />
        <meshStandardMaterial color="orange" />
      </mesh>
    </group>
  )
}

export default function App() {
  return (
    <Canvas>
      <ScrollControls pages={3} damping={0.2}>
        <Story />
        <Scroll>{/* 3D children here translate with the scroll offset */}</Scroll>
        <Scroll html style={{ width: '100%' }}>
          <h1 style={{ position: 'absolute', top: '10vh' }}>Intro</h1>
          <h1 style={{ position: 'absolute', top: '130vh' }}>Middle</h1>
          <h1 style={{ position: 'absolute', top: '230vh' }}>End</h1>
        </Scroll>
      </ScrollControls>
    </Canvas>
  )
}
```

`useScroll()` returns `offset` (0–1 overall), `delta`, and window helpers `range(from, distance)`, `curve(from, distance)` (bell 0→1→0), `visible(from, distance)` (boolean). Read them in `useFrame` — scroll position is not React state. DOM content must live inside `<Scroll html>` with absolute positioning in `vh` units.

**PresentationControls** — product-showcase rotation. It rotates its *children*, not the camera, with spring physics; combine with a fixed camera and your staging:

```jsx
import { PresentationControls } from '@react-three/drei'

<PresentationControls
  global                                  // drag anywhere in the viewport
  snap                                    // spring back to rest on release
  polar={[-Math.PI / 6, Math.PI / 6]}     // vertical rotation limits
  azimuth={[-Math.PI / 4, Math.PI / 4]}   // horizontal rotation limits
  config={{ mass: 1, tension: 170, friction: 26 }}
>
  <mesh>
    <boxGeometry />
    <meshStandardMaterial color="gold" />
  </mesh>
</PresentationControls>
```

## Screen and World Coordinates

**Screen → world, the easy case**: if the pointer hit a mesh, `e.point` already *is* the world-space position:

```jsx
<mesh onClick={(e) => spawnMarkerAt(e.point)}>…</mesh>
```

**Screen → world on an infinite plane**: during captured drags the ray can leave every mesh, and click-to-place may have no ground mesh at all. Intersect the event's own ray with a math plane — no `setFromCamera` needed:

```jsx
import * as THREE from 'three'
import { useMemo, useRef } from 'react'

const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0) // y = 0

function DragOnGround() {
  const mesh = useRef(null)
  const dragging = useRef(false)
  const hit = useMemo(() => new THREE.Vector3(), [])
  return (
    <mesh
      ref={mesh}
      onPointerDown={(e) => {
        e.stopPropagation()
        e.target.setPointerCapture(e.pointerId)
        dragging.current = true
      }}
      onPointerUp={(e) => {
        e.target.releasePointerCapture(e.pointerId)
        dragging.current = false
      }}
      onPointerMove={(e) => {
        if (!dragging.current) return
        if (e.ray.intersectPlane(groundPlane, hit)) mesh.current.position.copy(hit)
      }}
    >
      <boxGeometry />
      <meshStandardMaterial color="teal" />
    </mesh>
  )
}
```

**World → screen**: drei `<Html>` does the projection automatically — DOM content tracks a 3D position:

```jsx
import { Html } from '@react-three/drei'

<mesh position={[2, 1, 0]}>
  <boxGeometry />
  <meshStandardMaterial />
  <Html center distanceFactor={8} occlude>
    <div className="label">Crate</div>
  </Html>
</mesh>
```

Manual projection when you need raw pixels: `v.copy(worldPos).project(camera)` gives NDC; then `x = (v.x * 0.5 + 0.5) * size.width`, `y = (1 - (v.y * 0.5 + 0.5)) * size.height` (with `size` from `useThree`).

## Common Mistakes

| Mistake | Fix |
|---|---|
| `onClick` fires after every orbit drag, selecting things mid-camera-move | Gate with `if (e.delta > 2) return` — `delta` is px travelled between pointerdown and pointerup |
| Clicks "pass through" a foreground mesh to objects behind it | R3F delivers to *all* hits along the ray. The front handler must call `e.stopPropagation()`; for a pure blocker use the occluder pattern (handler that only stops propagation) |
| Relying on `onPointerEnter`/`onPointerLeave` not bubbling (DOM semantics) | Not implemented that way — they behave like `over`/`out`. Use `e.stopPropagation()` or check `e.eventObject === e.object` |
| setState inside `onPointerMove` — frame rate collapses while hovering | Write to a ref and consume in `useFrame`, or time-gate the handler; move events fire faster than frames |
| Drag stops working the moment the pointer slips off the mesh | `e.target.setPointerCapture(e.pointerId)` on pointerdown, release on pointerup — captured objects stay in the hit results |
| Hover highlight goes stale while orbiting (camera moves, pointer doesn't) | Events only recompute on pointer motion — call `events.update()` from the controls' `onChange` |
| TransformControls gizmo drags also orbit the camera | `makeDefault` on OrbitControls (drei auto-disables it during gizmo drags); or toggle `controls.enabled` in `onMouseDown`/`onMouseUp` |
| A DOM overlay on top of the canvas swallows all scene pointer events | `eventSource={parentElement}` on Canvas plus `eventPrefix="client"` |
| `onPointerMove`/hover janky on a high-poly mesh | `raycast={meshBounds}` from drei, or invisible simple collider + `raycast={() => null}` on the visible mesh |
| WASD via the reactive `useKeyboardControls(selector)` re-renders every keypress | Poll instead: `const [, getKeys] = useKeyboardControls()` and read `getKeys()` inside `useFrame` |
| Expecting mesh-level `onPointerMissed` to mean "nothing was clicked" | Mesh-level fires when a click misses *that object*; only Canvas-level `onPointerMissed` means the click hit nothing |
| Scroll HTML renders but doesn't scroll, or sits at the wrong offset | DOM content must be inside `<Scroll html>` within `ScrollControls`, positioned `absolute` in `vh` units against `pages` |
| `state.mouse` in older examples (legacy v8-era name) | Deprecated — use `state.pointer` (same normalized Vector2) |

## See Also

- [canvas-and-project-setup.md](./canvas-and-project-setup.md) — Canvas props including `events`, `eventSource`, `eventPrefix`, `raycaster`, `onPointerMissed`
- [hooks.md](./hooks.md) — `useThree` (pointer, viewport, events), `useFrame` discipline behind the ref-write patterns here
- [staging-and-drei.md](./staging-and-drei.md) — `Html`, `Bounds`/`useBounds` click-to-fit, and the rest of the drei helper map
- [performance.md](./performance.md) — `frameloop="demand"` + `invalidate()`, event-driven rendering, `AdaptiveEvents`
- [../SKILL.md](../SKILL.md) — install, version pairing, skill map
- External: [R3F events docs](https://r3f.docs.pmnd.rs/api/events) · [drei README (controls, gizmos, ScrollControls)](https://github.com/pmndrs/drei) · [@use-gesture docs](https://use-gesture.netlify.app/)
