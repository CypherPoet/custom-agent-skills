# Staging & the Drei Toolbox

Scene staging at the React layer — light JSX, the shadow pipeline, drei environment/shadow/staging helpers — plus a routing map of the drei catalog (drei v10, which requires fiber 9 / React 19). This is a catalog: each helper gets its import, one canonical snippet or table row, not an exhaustive prop dump. Lighting/PBR theory and three.js internals live in the sibling `threejs-mastery` skill.

> Canvas setup and renderer defaults: see [canvas-and-project-setup.md](./canvas-and-project-setup.md). Shared conventions: [../SKILL.md](../SKILL.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Lights & Shadows](#lights--shadows) | All three.js lights are lowercase JSX: `<ambientLight>`, `<hemisphereLight>` |
| [Debug Helpers](#debug-helpers) | `useHelper` (drei) mounts any three.js helper class against a ref object |
| [Environment & Sky](#environment--sky) | `<Environment>` (drei) loads an HDR, PMREM-filters it, and sets `scene.environment` |
| [Drei Shadow Helpers](#drei-shadow-helpers) | When to use each Drei shadow helper and which properties control it |
| [Stage](#stage) | Product staging with environment lighting, shadows, and automatic camera fitting |
| [Geometry & Layout Helpers](#geometry--layout-helpers) | Instances and Merged, lines and edges, Center and Bounds camera fitting, Detailed LOD, Float, Trail, Sparkles, and Billboard |
| [Text & Html](#text--html) | `<Text>` (SDF, troika-based) — the default for any readable text: crisp at every zoom level |
| [Drei Specialty Materials](#drei-specialty-materials) | Drop-in `<mesh>` children, uppercase imports from `@react-three/drei` |
| [Adaptive Quality](#adaptive-quality) | FPS-based quality changes for resolution, effects, and expensive scene details |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## Lights & Shadows

All three.js lights are lowercase JSX: `<ambientLight>`, `<hemisphereLight>`, `<directionalLight>`, `<pointLight>`, `<spotLight>`, `<rectAreaLight>`. Shadows need **three switches** — miss any one and nothing renders:

1. `<Canvas shadows>` — turns on the renderer shadow map.
2. `castShadow` on the light.
3. `castShadow` / `receiveShadow` on the meshes.

```jsx
import { Canvas } from '@react-three/fiber'

function App() {
  return (
    <Canvas shadows>
      <ambientLight intensity={0.4} />
      <directionalLight
        castShadow
        position={[5, 8, 5]}
        intensity={2}
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
        shadow-camera-near={0.5}
        shadow-camera-far={50}
        shadow-bias={-0.0001}
        shadow-normalBias={0.02}
      />
      <mesh castShadow receiveShadow>
        <torusKnotGeometry args={[0.6, 0.25, 128, 32]} />
        <meshStandardMaterial color="tomato" />
      </mesh>
      <mesh receiveShadow rotation-x={-Math.PI / 2} position-y={-1}>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial color="#999" />
      </mesh>
    </Canvas>
  )
}
```

The `shadow-*` props are R3F piercing syntax (`shadow-mapSize` → `light.shadow.mapSize`, `shadow-camera-left` → `light.shadow.camera.left`). The `shadow-camera-*` box only applies to `directionalLight` (orthographic shadow camera); `spotLight`/`pointLight` use a perspective shadow camera (`shadow-camera-fov`, `-near`, `-far`).

Tuning rules:

- **Shadow acne** (stripes on lit surfaces): `shadow-bias={-0.0001}`; on curved geometry prefer `shadow-normalBias` 0.02–0.05.
- **Peter-panning** (shadow detached from object): bias magnitude too large — dial it back, lean on `normalBias`.
- **Clipped shadows**: the shadow-camera frustum is too small. Make the `left/right/top/bottom/far` box just barely contain the casters — tighter frustum = more resolution per texel.
- `shadow-mapSize={[1024, 1024]}` is often enough; 2048 for hero shadows.

### Canvas Shadows Variants

| Canvas prop | three shadow map type |
|---|---|
| `shadows` or `shadows="soft"` | `PCFSoftShadowMap` |
| `shadows="basic"` | `BasicShadowMap` (fastest, hard edges) |
| `shadows="percentage"` | `PCFShadowMap` |
| `shadows="variance"` | `VSMShadowMap` (blurrable via `shadow-radius`) |
| `shadows={{ type: THREE.VSMShadowMap }}` | object form — props spread into `gl.shadowMap` |

### Aiming Directional & Spot Lights

`directionalLight` and `spotLight` point at a `target` Object3D. Setting `target-position={[x, y, z]}` alone is **not enough** — the target must be mounted in the scene graph or its world matrix never updates and the light keeps pointing at the origin:

```jsx
import { useMemo } from 'react'
import * as THREE from 'three'

function AimedSpot() {
  const target = useMemo(() => new THREE.Object3D(), [])
  return (
    <>
      <spotLight castShadow position={[0, 6, 0]} angle={0.4} penumbra={0.6} target={target} />
      <primitive object={target} position={[2, 0, -3]} />
    </>
  )
}
```

### Light Cost Ordering

Cheapest → most expensive. Every light grows every lit material's shader; shadow-casting lights add whole render passes.

| Light | Cost | Shadows | Notes |
|---|---|---|---|
| `ambientLight` | trivial | no | flat fill, no direction |
| `hemisphereLight` | trivial | no | sky/ground gradient — better outdoor fill than ambient |
| `directionalLight` | low | yes — 1 orthographic map | sun; one shadow render per frame |
| `spotLight` | medium | yes — 1 perspective map | cone; `angle`, `penumbra`, `decay` |
| `pointLight` | medium | yes — **6 cube-face renders** | most expensive shadow caster by far |
| `rectAreaLight` | high | **no** | only affects `meshStandardMaterial` / `meshPhysicalMaterial`; requires `RectAreaLightUniformsLib.init()` once (`import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js'`) |

Prefer one shadow-casting directional + `<Environment>` for fill over stacks of point lights. For soft-light looks without `rectAreaLight`'s cost, use [`<Lightformer>`](#environment--sky) rigs (emissive env content, zero per-light shader cost).

## Debug Helpers

`useHelper` (drei) mounts any three.js helper class against a **ref object** — never pass a dereferenced `.current` (it is `null` during render, and the hook can't track it):

```jsx
import { useRef } from 'react'
import { useHelper } from '@react-three/drei'
import { DirectionalLightHelper, CameraHelper } from 'three'

function DebugLight({ debug = true }) {
  const light = useRef(null)
  const shadowCam = useRef(null)
  useHelper(debug && light, DirectionalLightHelper, 1, 'hotpink')
  useHelper(debug && shadowCam, CameraHelper)
  return (
    <directionalLight ref={light} castShadow position={[5, 8, 5]}>
      <orthographicCamera ref={shadowCam} attach="shadow-camera" args={[-10, 10, 10, -10, 0.5, 50]} />
    </directionalLight>
  )
}
```

Two things this pattern buys:

- **Shadow-frustum debugging**: declaring the shadow camera as a child with `attach="shadow-camera"` gives you a ref target for `CameraHelper` *and* declarative frustum config via `args` (left, right, top, bottom, near, far) — the visualized box is exactly what the shadow map covers.
- **Toggling**: a falsy first argument (`debug && light`) disables the helper.

Orientation gizmo and reference grid:

```jsx
import { GizmoHelper, GizmoViewport, Grid, OrbitControls } from '@react-three/drei'

<OrbitControls makeDefault />
<GizmoHelper alignment="bottom-right" margin={[80, 80]}>
  <GizmoViewport axisColors={['#ff4d6d', '#4dff88', '#4d88ff']} labelColor="white" />
</GizmoHelper>
<Grid args={[10, 10]} cellSize={0.5} cellColor="#6f6f6f" sectionSize={2.5} sectionColor="#9d4b4b" fadeDistance={30} infiniteGrid />
```

`GizmoHelper` needs default-registered controls (`makeDefault`) so dragging the gizmo rotates the view. `Grid` is a shader grid: `cellSize`/`sectionSize` in world units, `infiniteGrid` extends past `args`, `followCamera` keeps it under the camera.

## Environment & Sky

`<Environment>` (drei) loads an HDR, PMREM-filters it, and sets `scene.environment` — image-based lighting for every PBR material, no analytical lights required. The 10 preset names: `apartment`, `city`, `dawn`, `forest`, `lobby`, `night`, `park`, `studio`, `sunset`, `warehouse`.

```jsx
import { Environment } from '@react-three/drei'

<Environment preset="city" />
<Environment preset="sunset" background />
<Environment preset="studio" background backgroundBlurriness={0.6} environmentIntensity={0.8} />
<Environment files="/hdr/studio_2k.hdr" background />
<Environment preset="park" ground={{ height: 12, radius: 70, scale: 90 }} />
```

- `background` also sets `scene.background` from the same texture (`background="only"` sets background without lighting). `backgroundBlurriness` (0–1) blurs the backdrop while lighting stays sharp.
- `environmentIntensity` scales IBL strength without reloading.
- **Presets download HDRs from a public CDN at runtime** — fine for prototyping, a liability in production. Ship your own HDR via `files` (single equirect `.hdr`, or an array of 6 cube faces plus `path`).
- `ground={{ height, radius, scale }}` projects the environment onto a virtual ground plane so objects appear to stand *in* the scene instead of floating in a skybox.

### Lightformer Studio Rigs

Children of `<Environment>` are rendered **into** the environment map — declarative studio lighting. `<Lightformer form="rect" | "ring" | "circle">` is an emissive panel for exactly this:

```jsx
import { Environment, Lightformer } from '@react-three/drei'

<Environment resolution={256}>
  <Lightformer form="rect" intensity={4} position={[5, 4, -5]} scale={[8, 4, 1]} target={[0, 0, 0]} />
  <Lightformer form="rect" intensity={1.5} position={[-5, 3, 3]} scale={[6, 3, 1]} />
  <Lightformer form="ring" intensity={2} color="#fff5e6" position={[0, 4, -8]} scale={4} />
</Environment>
```

Key/fill/rim with zero real lights and zero per-light shader cost. `target` aims the panel. For animated rigs set `frames={Infinity}` on `<Environment>` (re-renders the env map every frame — budget accordingly; static rigs render once).

### Sky, Stars, Clouds

```jsx
import { Sky, Stars, Clouds, Cloud } from '@react-three/drei'
import * as THREE from 'three'

<Sky sunPosition={[100, 20, 100]} turbidity={8} rayleigh={2} />
<Stars radius={100} depth={50} count={5000} factor={4} fade speed={1} />
<Clouds material={THREE.MeshBasicMaterial}>
  <Cloud segments={40} bounds={[10, 2, 2]} volume={10} color="white" />
  <Cloud seed={1} scale={2} volume={5} color="#f0c8ff" fade={100} />
</Clouds>
```

`<Sky>` is a backdrop mesh — it does **not** light the scene. Pair it with a `directionalLight` positioned at the same `sunPosition`, or add an `<Environment>` for ambient fill. `<Clouds>` batches multiple `<Cloud>` instances into one instanced draw; each `<Cloud>` takes `seed`, `segments`, `bounds`, `volume`, `speed`, `growth`, `opacity`.

## Drei Shadow Helpers

| Helper | When | Key props |
|---|---|---|
| `<ContactShadows>` | fake blurry ground shadow — no lights, no `castShadow` needed | `frames`, `blur`, `opacity`, `scale`, `far`, `resolution` |
| `<AccumulativeShadows>` + `<RandomizedLight>` | soft area-light-look baked shadows for **static** scenes | `temporal`, `frames`, `color`, `opacity`; light: `amount`, `radius`, `ambient` |
| `<SoftShadows>` | PCSS look on real shadow maps (distance-based softening) | `size`, `samples`, `focus` |
| `<BakeShadows>` | freeze shadow maps after first render | — |

```jsx
import { ContactShadows, AccumulativeShadows, RandomizedLight, SoftShadows, BakeShadows } from '@react-three/drei'

<ContactShadows position={[0, -1, 0]} opacity={0.6} scale={12} blur={2} far={4} resolution={512} frames={1} />

<AccumulativeShadows temporal frames={100} scale={10} position={[0, -1, 0]} color="#9d4b4b" opacity={0.9}>
  <RandomizedLight amount={8} radius={4} ambient={0.5} intensity={Math.PI} position={[5, 5, -10]} bias={0.001} />
</AccumulativeShadows>

<SoftShadows size={25} samples={10} focus={0} />
<BakeShadows />
```

- `ContactShadows` renders top-down depth of everything above its plane — it works with zero lights and ignores the three-switch pipeline. Default `frames={Infinity}` re-renders **every frame**; set `frames={1}` for static scenes (huge win).
- `AccumulativeShadows` accumulates many jittered shadow passes from the `<RandomizedLight>` children into one soft bake. `temporal` spreads accumulation across frames instead of blocking on mount. Move the scene → shadows are stale; it's for stills/product shots.
- `SoftShadows` monkey-patches the shadow shader globally (PCSS) while mounted — `size` is the virtual light size (bigger = softer), mount/unmount triggers material recompiles.
- `BakeShadows` sets `gl.shadowMap.autoUpdate = false` after the first render — real shadow maps at zero per-frame cost for static lighting; unmount restores live updates.

## Stage

`<Stage>` is one-liner product staging: environment + key/fill/rim lighting preset + ground shadows + auto camera fit (via `Bounds` internally).

```jsx
import { Stage, OrbitControls } from '@react-three/drei'

<Canvas shadows camera={{ position: [4, 2, 6], fov: 40 }}>
  <Stage preset="rembrandt" intensity={1} environment="city" shadows="contact" adjustCamera={1.2}>
    <Model />
  </Stage>
  <OrbitControls makeDefault />
</Canvas>
```

- `preset`: `"rembrandt"` | `"portrait"` | `"upfront"` | `"soft"`.
- `shadows`: `false` | `true` | `"contact"` | `"accumulative"` (or a config object merged into the shadow component).
- `environment`: any `<Environment>` preset name, or `null` to opt out.
- `adjustCamera`: `true`/number (fit margin) frames the content automatically; set `false` when you manage the camera.

Start with `<Stage>`; eject to explicit `<Environment>` + shadow helpers when you outgrow it.

## Geometry & Layout Helpers

### Instances / Merged

`<Instances>`/`<Instance>` — declarative `InstancedMesh`: one draw call, per-instance transform/color, full event support per instance.

```jsx
import { Instances, Instance } from '@react-three/drei'

<Instances limit={1000} range={1000}>
  <boxGeometry args={[0.5, 0.5, 0.5]} />
  <meshStandardMaterial />
  {positions.map((p, i) => (
    <Instance key={i} position={p} scale={0.8} color="tomato" onClick={(e) => e.stopPropagation()} />
  ))}
</Instances>
```

`limit` sizes the buffer at mount (cannot grow later — set it to the max you'll ever need); `range` caps how many render. `<Merged meshes={nodes}>` does the same for **existing meshes** (e.g. a filtered `useGLTF` `nodes` dict) — the render prop hands back one instanced component per mesh. Raw `<instancedMesh>` and the draw-call math live in [performance.md](./performance.md).

### Lines

drei's `Line` family uses `Line2`, so `lineWidth` is screen-space pixels and actually works (WebGL ignores `lineBasicMaterial.linewidth > 1` on most platforms):

```jsx
import { Line, CatmullRomLine, QuadraticBezierLine, CubicBezierLine } from '@react-three/drei'

<Line points={[[0, 0, 0], [1, 1, 0], [2, 0, 0]]} color="crimson" lineWidth={2} dashed={false} />
<CatmullRomLine points={waypoints} lineWidth={2} segments={64} />
<QuadraticBezierLine start={[0, 0, 0]} mid={[1, 2, 0]} end={[2, 0, 0]} lineWidth={2} />
<CubicBezierLine start={[0, 0, 0]} midA={[1, 2, 0]} midB={[2, -1, 0]} end={[3, 0, 0]} lineWidth={2} />
```

### Edges

Hard-edge outlines from the parent's geometry — drop it inside the mesh:

```jsx
import { Edges } from '@react-three/drei'

<mesh>
  <boxGeometry />
  <meshStandardMaterial color="orange" />
  <Edges linewidth={2} threshold={15} color="black" />
</mesh>
```

`threshold` = minimum dihedral angle in degrees before an edge is drawn.

### Center, Bounds, Detailed

```jsx
import { Center, Bounds, useBounds, Detailed } from '@react-three/drei'

<Center top>
  <Model />
</Center>
```

`<Center>` recenters its children's bounding box on the origin; alignment flags (`top`, `bottom`, `left`, `right`, `front`, `back`) pin a face instead — `top` sits the model *on* y=0.

`<Bounds>` + `useBounds` = click-to-fit camera framing:

```jsx
function ZoomToClick({ children }) {
  const api = useBounds()
  return (
    <group
      onClick={(e) => (e.stopPropagation(), api.refresh(e.object).fit())}
      onPointerMissed={(e) => e.button === 0 && api.refresh().fit()}
    >
      {children}
    </group>
  )
}

<Bounds fit clip observe margin={1.2}>
  <ZoomToClick><Model /></ZoomToClick>
</Bounds>
```

`fit` frames the contents on mount, `clip` adjusts camera near/far, `observe` refits on resize. `useBounds()` must be called **inside** `<Bounds>`.

`<Detailed>` is declarative LOD — children ordered nearest-first, one per distance threshold:

```jsx
<Detailed distances={[0, 15, 40]}>
  <HighPolyModel />
  <MediumPolyModel />
  <mesh><boxGeometry /><meshBasicMaterial color="#888" /></mesh>
</Detailed>
```

### Float, Trail, Sparkles, Billboard

```jsx
import { Float, Trail, Sparkles, Billboard, Text } from '@react-three/drei'

<Float speed={1.5} rotationIntensity={0.6} floatIntensity={1} floatingRange={[-0.1, 0.1]}>
  <Model />
</Float>

<Trail width={1.2} length={6} color="#f8a0c0" decay={1} attenuation={(w) => w}>
  <mesh ref={movingRef}>
    <sphereGeometry args={[0.2]} />
    <meshBasicMaterial color="#f8a0c0" />
  </mesh>
</Trail>

<Sparkles count={80} scale={[4, 2, 4]} size={2} speed={0.4} opacity={0.7} color="#fff" />

<Billboard follow>
  <Text fontSize={0.3}>Always faces the camera</Text>
</Billboard>
```

`<Float>` idle hover/rotation without touching `useFrame`. `<Trail>` extrudes a fading ribbon behind its moving child. `<Billboard>` rotates children to face the camera each frame (`lockX/lockY/lockZ` pin axes).

## Text & Html

**`<Text>` (SDF, troika-based)** — the default for any readable text: crisp at every zoom level, one draw call, no geometry cost per glyph. `font` accepts a `.ttf`/`.otf`/`.woff` URL (not `.woff2`).

```jsx
import { Text } from '@react-three/drei'

<Text font="/fonts/Inter-Bold.woff" fontSize={0.5} color="#222" anchorX="center" anchorY="middle" maxWidth={4} textAlign="center">
  Signed-distance-field text
</Text>
```

**`<Text3D>` (extruded TextGeometry)** — only when you need real depth/bevels. Its origin is the baseline start corner, so wrap in `<Center>`:

```jsx
import { Text3D, Center } from '@react-three/drei'

<Center>
  <Text3D font="/fonts/helvetiker_regular.typeface.json" size={1} height={0.2} bevelEnabled bevelSize={0.02} bevelThickness={0.02}>
    Extruded
    <meshStandardMaterial color="gold" />
  </Text3D>
</Center>
```

**`<Html>`** — real DOM anchored to a 3D point (labels, tooltips, in-world screens):

```jsx
import { Html } from '@react-three/drei'

<Html position={[0, 1.2, 0]} center distanceFactor={8} occlude>
  <div className="label">Engine</div>
</Html>

<Html transform position={[0, 0, 0.51]} occlude="blending">
  <button onClick={handleClick}>In-world UI</button>
</Html>
```

- `center` centers the div on the anchor (default is top-left corner) — for the non-`transform` overlay mode.
- `distanceFactor` scales the DOM with camera distance (perspective sizing).
- `transform` renders the element as a CSS3D-transformed plane that rotates/scales with the scene.
- `occlude`: `true` raycasts the scene and hides the div behind geometry; an array of refs tests only those objects; `"blending"` uses real depth occlusion against the WebGL canvas (the usual pairing with `transform` mode).

`<Html>` contents live outside the Canvas React tree — R3F hooks don't work inside; pass state in via props.

## Drei Specialty Materials

Drop-in `<mesh>` children, uppercase imports from `@react-three/drei`:

| Material | Use | Signature props |
|---|---|---|
| `MeshReflectorMaterial` | reflective floors / blurry mirrors | `blur={[400, 100]}`, `resolution`, `mixBlur`, `mixStrength`, `mirror` (0 = diffuse, 1 = mirror) |
| `MeshTransmissionMaterial` | premium glass — refraction beyond `meshPhysicalMaterial` | `backside`, `samples`, `thickness`, `chromaticAberration`, `anisotropy`, `attenuationColor`, `attenuationDistance` |
| `MeshWobbleMaterial` | jelly wobble | `factor`, `speed` |
| `MeshDistortMaterial` | organic noise blobs | `distort`, `speed` |
| `MeshDiscardMaterial` | invisible mesh that still casts shadows and raycasts | — |

```jsx
import { MeshReflectorMaterial, MeshTransmissionMaterial } from '@react-three/drei'

<mesh rotation-x={-Math.PI / 2} position-y={-1}>
  <planeGeometry args={[20, 20]} />
  <MeshReflectorMaterial blur={[400, 100]} resolution={1024} mixBlur={1} mixStrength={0.6}
    mirror={0.75} color="#151515" metalness={0.6} roughness={1} />
</mesh>

<mesh castShadow>
  <sphereGeometry args={[1, 64, 64]} />
  <MeshTransmissionMaterial backside samples={8} thickness={0.4} chromaticAberration={0.05}
    anisotropy={0.2} attenuationColor="#c9ffa1" attenuationDistance={0.6} />
</mesh>
```

`MeshTransmissionMaterial` renders the scene into a buffer per frame — expensive; cap `samples`/`resolution` and count instances. `MeshDiscardMaterial` discards fragments in the color pass only, so the mesh stays a shadow caster and raycast target (shadow catcher / invisible hitbox).

### meshPhysicalMaterial Quick Recipes

When plain built-ins suffice (all on `<meshPhysicalMaterial>`; full property reference in the `threejs-mastery` sibling skill):

| Look | Recipe |
|---|---|
| Glass | `transmission={1} thickness={0.5} roughness={0} ior={1.5}` |
| Car paint | `metalness={0.9} roughness={0.4} clearcoat={1} clearcoatRoughness={0.1}` |
| Fabric / velvet | `roughness={0.9} sheen={1} sheenColor="#ff9dff"` |
| Soap bubble | `iridescence={1} iridescenceIOR={1.3} iridescenceThicknessRange={[100, 400]}` |

## Adaptive Quality

Staging pairs with adaptive degradation: `<PerformanceMonitor>` measures fps and fires `onIncline`/`onDecline` (drive Canvas `dpr` or swap effect quality); `<AdaptiveDpr pixelated>` drops resolution while `performance.regress()` is active (e.g. during camera moves). Both are covered with the full performance doctrine in [performance.md](./performance.md).

## Common Mistakes

| Mistake | Fix |
|---|---|
| No shadows anywhere | One of the three switches is missing: `<Canvas shadows>`, `castShadow` on the light, `castShadow`/`receiveShadow` on meshes. |
| Shadows cut off at the edges of a region | Directional shadow-camera frustum too small — widen `shadow-camera-left/right/top/bottom` (and `-far`) to contain the casters. |
| Stripey banding (acne) on lit surfaces | `shadow-bias={-0.0001}`; on curved geometry use `shadow-normalBias={0.02}`–`0.05` instead of cranking bias. |
| Shadow floats detached from the object | Bias magnitude too large (peter-panning) — reduce it, prefer `normalBias`. |
| `useHelper(ref.current, …)` or `useHelper(light.current?.shadow.camera, …)` renders nothing | Pass the **ref object**, never `.current`. For shadow cameras, declare `<orthographicCamera attach="shadow-camera" ref={shadowCam} />` inside the light and helper that ref. |
| `target-position` on a spot/directional light does nothing | The target Object3D isn't in the scene graph, so its matrix never updates — mount it: `<primitive object={target} position={…} />` and pass `target={target}`. |
| `rectAreaLight` has zero effect | It only lights `meshStandardMaterial`/`meshPhysicalMaterial`, casts no shadows, and needs `RectAreaLightUniformsLib.init()` called once. |
| `<Environment preset>` works locally, breaks in production/offline | Presets fetch HDRs from a third-party CDN at runtime — self-host and pass `files="/hdr/….hdr"`. |
| Frame rate tanks after adding `<ContactShadows>` | Default `frames={Infinity}` re-renders the shadow every frame — use `frames={1}` for static scenes. |
| `<AccumulativeShadows>` renders empty or jet black | It needs `<RandomizedLight>` children to accumulate from, and the scene must hold still; bump `frames`, add `temporal`. |
| `<Html>` label anchored at its top-left corner / drifts | Add `center` (overlay mode); for UI on a surface use `transform` + `occlude="blending"`. |
| Dragging `<GizmoViewport>` doesn't rotate the camera | Controls must be default-registered: `<OrbitControls makeDefault />`. |
| `<Text3D>` sits off-center no matter the position | TextGeometry's origin is the baseline start — wrap in `<Center>`. |
| `<Instances>` silently stops showing items past N | `limit` fixed the buffer size at mount — set `limit` to the maximum ever needed, drive the visible count with `range`. |
| `<line>` + `lineBasicMaterial linewidth={3}` stays 1px | WebGL ignores line widths > 1 on most platforms — use drei `<Line lineWidth={3}>` (Line2, screen-space). |

## See Also

- [performance.md](./performance.md) — instancing math, on-demand frameloop, `PerformanceMonitor`/`AdaptiveDpr`, draw-call budgets.
- [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md) — piercing (`shadow-camera-left`) and `attach` semantics used throughout this file.
- [loading-assets.md](./loading-assets.md) — `useGLTF`/gltfjsx models to drop into `<Stage>`; custom HDR/texture loading.
- [shaders-and-custom-materials.md](./shaders-and-custom-materials.md) — drei `shaderMaterial` when the specialty materials aren't enough.
- [../SKILL.md](../SKILL.md) — version pins and skill map.
- Official: [pmndrs/drei README](https://github.com/pmndrs/drei) (canonical helper catalog) · [R3F docs](https://r3f.docs.pmnd.rs).
