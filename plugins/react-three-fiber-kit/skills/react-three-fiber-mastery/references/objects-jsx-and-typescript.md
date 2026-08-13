# Objects, JSX Semantics & TypeScript

How the @react-three/fiber reconciler turns JSX into live three.js objects: constructor `args`, prop shorthands and piercing, `attach`, `<primitive>`, `extend`, automatic disposal, and the v9 TypeScript surface. Current stack: R3F 9.7.x + React 19 + three 0.185.x — v8 idioms appear only in explicitly labeled legacy notes.

> Canvas/project setup: see [../SKILL.md](../SKILL.md) and [canvas-and-project-setup.md](./canvas-and-project-setup.md).

**Contents:** [How the Reconciler Maps JSX to three.js](#how-the-reconciler-maps-jsx-to-threejs) · [Constructor Arguments: args](#constructor-arguments-args) · [Prop Shorthands and Piercing](#prop-shorthands-and-piercing) · [The attach Prop](#the-attach-prop) · [primitive: Mounting Existing Objects](#primitive-mounting-existing-objects) · [extend: Registering Custom Elements](#extend-registering-custom-elements) · [Disposal and dispose=null](#disposal-and-disposenull) · [The onUpdate Prop](#the-onupdate-prop) · [TypeScript](#typescript) · [Common Mistakes](#common-mistakes)

## How the Reconciler Maps JSX to three.js

Every three.js class is available as a camelCase intrinsic element: `<mesh>` ≡ `new THREE.Mesh()`, `<boxGeometry args={[2, 2, 2]} />` ≡ `new THREE.BoxGeometry(2, 2, 2)`. Nothing is imported per element — the reconciler resolves tag names against the `THREE` namespace; classes outside it need [`extend`](#extend-registering-custom-elements).

Core semantics:

- **Declare, don't construct.** The reconciler creates each instance once on mount and *mutates* it when props change. Only [`args`](#constructor-arguments-args) changes reconstruct.
- `Object3D` children are inserted via `parent.add(child)`. Non-`Object3D` children (geometries, materials, buffer attributes, fog) are wired to a parent property via [`attach`](#the-attach-prop).
- Props flow through React — right for slow or reactive state (visibility toggles, color themes, staged content). Per-frame values must bypass React entirely: mutate through refs inside `useFrame`, never `setState` in a loop. See [hooks.md](./hooks.md) and [performance.md](./performance.md).

```tsx
import * as THREE from 'three'

// Imperative three.js — avoid inside components (re-runs every render)
const mesh = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial())

// Declarative R3F — constructed once, diffed thereafter
function Box() {
  return (
    <mesh visible userData={{ hello: 'world' }} position={[1, 2, 3]} rotation={[Math.PI / 2, 0, 0]}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="hotpink" transparent opacity={0.6} />
    </mesh>
  )
}
```

For one-off imperative updates (e.g. walking a loaded scene), the exported `applyProps(object, props)` applies the exact same conversion rules — shorthands, piercing, all of it — outside JSX:

```tsx
import { applyProps } from '@react-three/fiber'

applyProps(mesh, { 'rotation-x': Math.PI / 2, 'material-color': 'hotpink' })
```

## Constructor Arguments: `args`

`args` is an array matching the class constructor signature. Omit it for the default constructor.

```tsx
<sphereGeometry args={[1, 32, 32]} />        // new THREE.SphereGeometry(1, 32, 32)
<cylinderGeometry args={[1, 1, 2, 32]} />    // new THREE.CylinderGeometry(1, 1, 2, 32)
<fog attach="fog" args={['#0b1026', 5, 25]} /> // new THREE.Fog('#0b1026', 5, 25)
```

**Changing `args` destroys the instance and constructs a new one.** Buffers re-upload, materials recompile, GPU state resets. Consequences:

- Keep `args` referentially meaningful, not per-frame: derive them from stable props/`useMemo`, never from animation state.
- Reconstruction is sometimes the point — a segment-count control *should* rebuild the geometry:

```tsx
function Ring({ segments = 64 }: { segments?: number }) {
  return (
    <mesh>
      <torusGeometry args={[1, 0.2, 16, segments]} />
      <meshStandardMaterial color="royalblue" />
    </mesh>
  )
}
```

- Anything settable after construction (color, roughness, position) belongs in regular props, not `args` — props mutate cheaply; `args` rebuilds.

## Prop Shorthands and Piercing

### `.set()` and `setScalar` Shorthands

Any underlying property with a `.set()` method accepts set's arguments directly as the prop value:

```tsx
<mesh position={[1, 2, 3]} />            // mesh.position.set(1, 2, 3)
<meshStandardMaterial color="hotpink" /> // material.color.set('hotpink') — any THREE.Color input
<mesh scale={1} />                       // setScalar shorthand: scale.set(1, 1, 1)
```

Passing an instance of the matching class (e.g. a `THREE.Vector3` to `position`) *copies* it into the existing object — the target keeps a stable reference and is never swapped out. Since v9.6, `uniforms` objects on shader materials get the same copy-into semantics: the uniforms reference is stable, which fixes HMR desync and React Compiler auto-memoization and makes inline/pierced uniform props safe. See [shaders-and-custom-materials.md](./shaders-and-custom-materials.md).

### Piercing (Dash Props)

Each dash descends one property level; shorthands still apply at the leaf. This reaches nested objects without extra JSX elements or refs:

| JSX prop | Applies |
|---|---|
| `rotation-x={Math.PI / 2}` | `obj.rotation.x = Math.PI / 2` |
| `position-y={2}` | `obj.position.y = 2` |
| `material-color="hotpink"` | `mesh.material.color.set('hotpink')` |
| `material-uniforms-resolution-value={[512, 512]}` | `mesh.material.uniforms.resolution.value` |
| `shadow-camera-left={-10}` | `light.shadow.camera.left = -10` |
| `shadow-mapSize={[2048, 2048]}` | `light.shadow.mapSize.set(2048, 2048)` |
| `texture-colorSpace={THREE.SRGBColorSpace}` | any nested `.texture` — v9 no longer auto-converts texture color spaces |

The canonical shadow-camera use:

```tsx
<directionalLight
  castShadow
  position={[5, 8, 5]}
  shadow-mapSize={[2048, 2048]}
  shadow-camera-left={-10}
  shadow-camera-right={10}
  shadow-camera-top={10}
  shadow-camera-bottom={-10}
/>
```

## The `attach` Prop

`attach` binds a non-`Object3D` child to a named property of its parent instead of `parent.add()`.

**Automatic:** elements whose class name ends in `Geometry` receive `attach="geometry"`; names ending in `Material` receive `attach="material"`. That is why `<boxGeometry />` and `<meshStandardMaterial />` need no attach.

**Explicit:** anything else names its target property:

```tsx
<mesh>
  <meshBasicMaterial attach="material" /> {/* explicit form of the automatic rule */}
</mesh>

<fog attach="fog" args={['white', 1, 10]} /> {/* scene.fog */}
```

**Nested paths** use dashes, exactly like pierced props. The workhorse is buffer attributes — **in v9 the constructor `args={[array, itemSize]}` form is required**:

```tsx
import { useMemo } from 'react'

function PointCloud({ count = 5000 }: { count?: number }) {
  const positions = useMemo(() => {
    const array = new Float32Array(count * 3)
    for (let i = 0; i < array.length; i++) array[i] = (Math.random() - 0.5) * 10
    return array
  }, [count])

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.03} sizeAttenuation color="white" />
    </points>
  )
}
```

> **Legacy (v8):** `<bufferAttribute count={n} array={arr} itemSize={3} />` — the prop-trio form. It no longer initializes the attribute correctly in v9; convert to `args={[arr, 3]}`. Indexed geometry attaches the same way: `<bufferAttribute attach="index" args={[indices, 1]} />`.

**Array-index attach** targets array slots. For multi-material meshes, `material-0` through `material-5` follow BoxGeometry's group order — +X (right), −X (left), +Y (top), −Y (bottom), +Z (front), −Z (back):

```tsx
<mesh>
  <boxGeometry />
  {['#e63946', '#f1a208', '#2a9d8f', '#264653', '#7209b7', '#f72585'].map((color, index) => (
    <meshStandardMaterial key={index} attach={`material-${index}`} color={color} />
  ))}
</mesh>
```

**Functional attach** receives `(parent, self)` and returns a cleanup function — the escape hatch when binding isn't a simple property assignment:

```tsx
<bar
  attach={(parent, self) => {
    parent.add(self)
    return () => parent.remove(self)
  }}
/>
```

## `<primitive>`: Mounting Existing Objects

`<primitive object={...}>` places a pre-existing three.js object into the JSX graph. Extra props (including pierced ones) are applied on top, and R3F events work on it:

```tsx
import { useGLTF } from '@react-three/drei'
import type { ThreeElements } from '@react-three/fiber'

function Model(props: ThreeElements['group']) {
  const { scene } = useGLTF('/robot.glb')
  return <primitive object={scene} {...props} />
}
```

Rules:

- **Never mount the same object twice.** A three.js object has exactly one parent — a second `<primitive object={sameObject}>` re-parents it, so the first mount silently loses it.
- **Clone for reuse.** `useMemo(() => scene.clone(), [scene])` for a second instance; drei's `<Clone object={scene} />` packages this (see [staging-and-drei.md](./staging-and-drei.md)). Skinned meshes need `SkeletonUtils.clone` from `three/addons/utils/SkeletonUtils.js` — plain `.clone()` breaks bone bindings. Model workflows: [loading-assets.md](./loading-assets.md).
- The object came from outside React, so React neither creates nor recreates it; swapping the `object` prop swaps what is mounted.
- Loader-cached objects (`useLoader`/`useGLTF` results) are shared per URL — mount them under `dispose={null}` (next section) or unmounting one consumer disposes the asset for all.

## `extend`: Registering Custom Elements

Classes outside the `THREE` namespace (addons, your own subclasses) must be registered before use as JSX.

**Catalog form** — registers a global lowercase intrinsic element:

```tsx
import { extend, useThree } from '@react-three/fiber'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

extend({ OrbitControls }) // module level, once

function Controls() {
  const camera = useThree((state) => state.camera)
  const gl = useThree((state) => state.gl)
  return <orbitControls args={[camera, gl.domElement]} />
}
```

**Factory form (v9, recommended for libraries)** — `extend(Class)` returns a component directly. No global catalog entry, no JSX namespace collisions between libraries, and TypeScript infers the props with zero augmentation:

```tsx
import { extend, useThree } from '@react-three/fiber'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

const Controls = extend(OrbitControls)

function CameraRig() {
  const camera = useThree((state) => state.camera)
  const gl = useThree((state) => state.gl)
  return <Controls args={[camera, gl.domElement]} enableDamping />
}
```

Notes:

- Import addons from `three/addons/...`, not the legacy `three/examples/jsm/...` path.
- In apps, prefer drei's wrapped `<OrbitControls makeDefault />` over hand-extending — [staging-and-drei.md](./staging-and-drei.md).
- Custom roots that skip `<Canvas>` can register the whole namespace with `extend(THREE)` (or a hand-picked subset for tree-shaking) — [canvas-and-project-setup.md](./canvas-and-project-setup.md).

## Disposal and `dispose={null}`

When a JSX subtree unmounts, R3F automatically calls `.dispose()` on the objects beneath it — geometries, materials, textures. You rarely free GPU resources by hand.

Opt out with `dispose={null}` on a parent — it applies to that object *and its entire subtree*:

```tsx
<group dispose={null}>
  <primitive object={cachedGltf.scene} />
</group>
```

Use it whenever the mounted asset outlives the component:

- **Loader caches.** `useLoader`/`useGLTF` cache by URL and hand every consumer the same objects; disposing on unmount corrupts the cache for everyone. gltfjsx-generated components put `dispose={null}` on the root group for exactly this reason.
- **Module-level shared geometry/material** mounted as JSX in several places.
- Assets you created yourself (`useMemo`, module scope) and pass by prop are yours to manage — dispose them in an effect cleanup when genuinely done.

Mount/unmount is expensive beyond disposal (buffer re-upload, shader recompile) — prefer `visible={false}` over conditional unmount for toggled content; see [performance.md](./performance.md).

## The `onUpdate` Prop

`onUpdate` is a callback — not a pointer event — invoked with the instance after fresh props are applied to it. Use it for follow-up work a plain prop can't express:

```tsx
<perspectiveCamera
  fov={zoomed ? 20 : 60}
  onUpdate={(self) => self.updateProjectionMatrix()}
/>
```

Camera projection props (`fov`, `near`, `far`, `zoom`) don't take effect until `updateProjectionMatrix()` — this is the standard fix. (For app cameras, drei's `<PerspectiveCamera makeDefault>` handles it.)

## TypeScript

### Refs

Type refs with the three.js instance type and the non-null assertion — the element is assumed to exist by the time handlers and frames run:

```tsx
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import type { Mesh } from 'three'

function Spinner() {
  const meshRef = useRef<Mesh>(null!)
  useFrame((_, delta) => {
    meshRef.current.rotation.y += delta
  })
  return (
    <mesh ref={meshRef}>
      <boxGeometry />
      <meshStandardMaterial color="orange" />
    </mesh>
  )
}
```

### Component Props: `ThreeElements['mesh']`

Derive component prop types from the `ThreeElements` interface. **`MeshProps` and friends are removed in v9** — `ThreeElements['mesh']` is the replacement:

```tsx
import type { ThreeElements } from '@react-three/fiber'

type BoxProps = ThreeElements['mesh'] & { size?: number }

function Box({ size = 1, ...props }: BoxProps) {
  return (
    <mesh {...props}>
      <boxGeometry args={[size, size, size]} />
      <meshStandardMaterial color="hotpink" />
    </mesh>
  )
}

// React 19: ref is a regular prop — no forwardRef; it rides along in the spread
// <Box ref={meshRef} position={[0, 1, 0]} />
```

### Typing `extend`: Module Augmentation with `ThreeElement`

Catalog-form `extend` needs a `ThreeElements` augmentation so TypeScript knows the new tag:

```tsx
import { extend, type ThreeElement } from '@react-three/fiber'
import { GridHelper } from 'three'

class CustomElement extends GridHelper {}

extend({ CustomElement })

declare module '@react-three/fiber' {
  interface ThreeElements {
    customElement: ThreeElement<typeof CustomElement>
  }
}
```

Or skip augmentation entirely with the factory form — `const Element = extend(CustomElement)` infers props and avoids namespace bleeding. For WebGPU custom roots, `ThreeToJSXElements<typeof THREE>` maps a whole namespace at once (see [migration-v8-to-v9.md](./migration-v8-to-v9.md)).

### Exported Types

| Type | What it is |
|---|---|
| `ThreeElements` | Interface mapping every JSX tag to its prop type; index it (`ThreeElements['mesh']`) for component props |
| `ThreeElement<typeof X>` | Element props for a constructor — replaces removed `Node`/`Object3DNode`/`BufferGeometryNode`/`MaterialNode`/`LightNode` |
| `CanvasProps` | `<Canvas>` props (renamed from `Props` in v9) |
| `RootState` | The full state object returned by `useThree()` |
| `RenderCallback` | `useFrame` callback signature |
| `ThreeEvent<E>` | Pointer/interaction event, e.g. `ThreeEvent<PointerEvent>` — see [events-and-interaction.md](./events-and-interaction.md) |
| `Intersection` | Raycast hit entry (`event.intersections`) |
| `Camera` | `PerspectiveCamera \| OrthographicCamera` union used by the root state |
| `Size`, `Viewport`, `Dpr` | Shapes of `state.size`, `state.viewport`, and the Canvas `dpr` prop |
| `Performance` | Shape of `state.performance` (adaptive regression) |
| `Events`, `EventManager` | Event-system typing for custom event managers |

```tsx
import type { ThreeEvent } from '@react-three/fiber'

function handleClick(event: ThreeEvent<MouseEvent>) {
  event.stopPropagation()
  event.object.scale.setScalar(1.2)
}
```

### Legacy v8 Typing (Recognize, Never Write)

```tsx
// v8 — REMOVED in v9. If you see this, the code predates React 19.
declare global {
  namespace JSX {
    interface IntrinsicElements {
      orbitControls: ReactThreeFiber.Object3DNode<OrbitControls, typeof OrbitControls>
    }
  }
}
```

React 19 deprecated the global `JSX` namespace, and v9 removed `Object3DNode` and its siblings with it. Migrate to the `declare module '@react-three/fiber'` + `ThreeElement<T>` pattern above. Full breaking list: [migration-v8-to-v9.md](./migration-v8-to-v9.md).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Geometry flickers, recompiles, or resets state every render — `args` receives a fresh array derived from changing values | Changing `args` reconstructs the object. Keep `args` stable (constants or `useMemo`); animate via ref mutation, never through `args`. |
| `<bufferAttribute count={n} array={arr} itemSize={3} />` renders nothing or garbage on v9 | v8 prop-trio form no longer initializes attributes. Use constructor args: `<bufferAttribute attach="attributes-position" args={[arr, 3]} />`. |
| Second `<primitive>` of the same object makes the first vanish | A three.js object has one parent; mounting it twice re-parents it. Clone (`scene.clone()`, drei `<Clone>`, `SkeletonUtils.clone` for skinned meshes). |
| GLTF model goes black/invisible after another component using the same URL unmounts | Auto-disposal destroyed the shared loader-cache asset. Mount cached scenes under `dispose={null}` (gltfjsx does this on the root group). |
| TS error: `Property 'orbitControls' does not exist on type 'JSX.IntrinsicElements'` after `extend` | Augment `ThreeElements` via `declare module '@react-three/fiber'` with `ThreeElement<typeof OrbitControls>`, or switch to factory `const Controls = extend(OrbitControls)`. |
| Imports of `MeshProps`, `Object3DNode`, or `Props` fail after upgrading to v9 | Removed. Use `ThreeElements['mesh']`, `ThreeElement<typeof X>`, and `CanvasProps`. |
| Pierced camera prop (`fov`, `near`) changes but the view doesn't | Projection matrix isn't rebuilt automatically: `onUpdate={(self) => self.updateProjectionMatrix()}`. |
| Custom-shader texture looks washed out or too dark after moving to v9 | v9 removed automatic sRGB conversion of texture props. Annotate color maps manually — `texture.colorSpace = THREE.SRGBColorSpace` — and leave data maps (normal/roughness) linear. |
| Multi-material box paints the wrong faces | `material-0..5` follow BoxGeometry group order: +X, −X, +Y, −Y, +Z, −Z. |
| A non-`Object3D` child (fog, attribute, render target) silently does nothing | It can't be `add()`ed — give it an explicit `attach` path, e.g. `<fog attach="fog" />`. |
| `position={new THREE.Vector3(x, y, z)}` allocated every render "for correctness" | Unnecessary — values are copied into the existing vector either way (stable reference). Use the array form; and never allocate per frame (see [performance.md](./performance.md)). |

## See Also

- [../SKILL.md](../SKILL.md) — skill overview and shared setup.
- [hooks.md](./hooks.md) — `useThree`, `useFrame`, `useLoader`; the ref-mutation side of "declare, don't construct".
- [loading-assets.md](./loading-assets.md) — `useGLTF`, gltfjsx, `<primitive>` model workflows, loader caching.
- [shaders-and-custom-materials.md](./shaders-and-custom-materials.md) — drei `shaderMaterial`, uniforms-as-props, v9.6 stable uniforms.
- [migration-v8-to-v9.md](./migration-v8-to-v9.md) — the complete v8 → v9 breaking-change list.
- Official docs: [Objects, properties and constructor arguments](https://r3f.docs.pmnd.rs/api/objects) · [TypeScript](https://r3f.docs.pmnd.rs/api/typescript)
