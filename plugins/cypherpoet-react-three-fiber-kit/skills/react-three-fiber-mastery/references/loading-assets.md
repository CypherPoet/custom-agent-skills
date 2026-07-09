# Loading Assets

Models, textures, video, and render targets at the React layer: `useLoader` and the drei loader hooks suspend while fetching, cache by URL, and integrate with the component tree. This file covers the loading pipeline and Suspense patterns — GLTF format internals, PBR theory, and asset-compression tooling belong to the sibling `threejs-mastery` skill.

> Canvas/project setup: see [canvas-and-project-setup.md](./canvas-and-project-setup.md); shared conventions: [../SKILL.md](../SKILL.md).

**Contents:** [Quick Start](#quick-start) · [useGLTF](#usegltf) · [The gltfjsx Workflow](#the-gltfjsx-workflow) · [useLoader](#useloader) · [Primitive and Clone](#primitive-and-clone) · [Other Model Formats](#other-model-formats) · [useTexture](#usetexture) · [Texture Configuration](#texture-configuration) · [Color Spaces](#color-spaces) · [Environment, Cube, and Video Textures](#environment-cube-and-video-textures) · [Render Targets and Procedural Textures](#render-targets-and-procedural-textures) · [Suspense and Loading UI](#suspense-and-loading-ui) · [Caching and Preloading](#caching-and-preloading) · [Common Mistakes](#common-mistakes)

## Quick Start

```jsx
import { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { useGLTF, OrbitControls } from '@react-three/drei'

function Robot(props) {
  const { scene } = useGLTF('/models/robot.glb')
  return <primitive object={scene} {...props} />
}

export default function App() {
  return (
    <Canvas shadows>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} castShadow />
      <Suspense fallback={null}>
        <Robot position={[0, -1, 0]} />
      </Suspense>
      <OrbitControls />
    </Canvas>
  )
}
```

Every loader hook in this file suspends — a `<Suspense>` boundary above the loading component is mandatory. See [Suspense and Loading UI](#suspense-and-loading-ui).

## useGLTF

The recommended way to load GLTF/GLB (drei). Returns the full GLTF result plus memoized `nodes`/`materials` lookup graphs (fiber's `useLoader` attaches these to any result with a `.scene`):

```jsx
import { useGLTF } from '@react-three/drei'

function Model() {
  const { scene, nodes, materials, animations } = useGLTF('/models/robot.glb')
  // scene:      THREE.Group — the root
  // nodes:      { [name]: THREE.Object3D } — every named node/mesh
  // materials:  { [name]: THREE.Material }
  // animations: THREE.AnimationClip[] — feed to useAnimations (see animation.md)
  return <primitive object={scene} />
}
```

Render selectively by rebuilding from `nodes`/`materials` instead of mounting the whole scene:

```jsx
function Body() {
  const { nodes, materials } = useGLTF('/models/robot.glb')
  return (
    <mesh geometry={nodes.Body.geometry} material={materials.Metal} castShadow receiveShadow />
  )
}
```

Compression and static methods:

- **Draco and Meshopt decode automatically.** Signature: `useGLTF(url, useDraco = true, useMeshopt = true, extendLoader?)`. The Draco decoder loads from a CDN by default; pass a path string as the second argument for a self-hosted decoder (`useGLTF('/m.glb', '/draco-gltf/')`), or set it globally:

```jsx
useGLTF.setDecoderPath('/draco-gltf/')      // global override for the Draco decoder
useGLTF.preload('/models/robot.glb')        // module scope — starts fetching before mount
useGLTF.preload(['/a.glb', '/b.glb'])
useGLTF.clear('/models/robot.glb')          // evict from the URL cache
```

- The fourth argument extends the underlying `GLTFLoader` (e.g. wiring a `KTX2Loader`) — same idea as the [useLoader](#useloader) extensions callback.

Post-process the loaded graph in an effect (e.g. enable shadows everywhere):

```jsx
import { useEffect } from 'react'

function Model() {
  const { scene } = useGLTF('/models/robot.glb')
  useEffect(() => {
    scene.traverse((child) => {
      if (child.isMesh) child.castShadow = child.receiveShadow = true
    })
  }, [scene])
  return <primitive object={scene} />
}
```

Mutations like this hit the cached instance — every consumer of the same URL sees them (see [Caching and Preloading](#caching-and-preloading)).

## The gltfjsx Workflow

[gltfjsx](https://github.com/pmndrs/gltfjsx) turns a GLTF/GLB into a typed React component — the preferred way to consume models you control:

```bash
npx gltfjsx model.glb --types        # emits Model.tsx
npx gltfjsx model.glb --types --transform  # also compresses/dedupes into model-transformed.glb
```

Or use the web UI at https://gltf.pmnd.rs (drag-and-drop, copy the output).

Generated component idioms (modernized for v9 — gltfjsx 6.x templates predate v9, so fix the props type):

```tsx
import * as THREE from 'three'
import { useGLTF } from '@react-three/drei'
import type { ThreeElements } from '@react-three/fiber'
import type { GLTF } from 'three-stdlib'

type GLTFResult = GLTF & {
  nodes: {
    Body: THREE.Mesh
    Head: THREE.Mesh
  }
  materials: {
    Metal: THREE.MeshStandardMaterial
    Plastic: THREE.MeshStandardMaterial
  }
}

export function Robot(props: ThreeElements['group']) {
  const { nodes, materials } = useGLTF('/robot.glb') as GLTFResult
  return (
    <group {...props} dispose={null}>
      <mesh geometry={nodes.Body.geometry} material={materials.Metal} castShadow receiveShadow />
      <mesh geometry={nodes.Head.geometry} material={materials.Plastic} castShadow receiveShadow />
    </group>
  )
}

useGLTF.preload('/robot.glb')
```

Why each idiom matters:

| Idiom | Purpose |
|---|---|
| Typed `GLTF & { nodes, materials }` via `three-stdlib` | Autocomplete + compile errors when the model changes |
| `dispose={null}` on the root group | Geometries/materials live in the URL cache; unmounting one copy must not dispose them for everyone |
| `castShadow receiveShadow` per mesh | Shadows opt-in per mesh, not inherited from the group |
| Rebuild from `nodes`, don't mount `scene` | Selective rendering, per-mesh props/events, and the component can be mounted many times (each mount creates fresh `Mesh` objects sharing cached geometry/material — unlike `<primitive>`) |
| `useGLTF.preload` at module scope | Fetch starts at import time, before first render |
| gltfjsx templates emit `JSX.IntrinsicElements['group']` (v8-era) | Replace with `ThreeElements['group']` — the global JSX namespace and named prop aliases were removed in v9 |

## useLoader

Fiber's core loading hook, for any three.js loader: `useLoader(LoaderClassOrInstance, urlOrUrls, extensions?, onProgress?)`.

```jsx
import { useLoader } from '@react-three/fiber'
import { TextureLoader } from 'three'

const texture = useLoader(TextureLoader, '/textures/color.jpg')

// Parallel loading — array in, array out
const [color, normal, rough] = useLoader(TextureLoader, [
  '/textures/color.jpg',
  '/textures/normal.jpg',
  '/textures/roughness.jpg',
])
```

Manual GLTF wiring with Draco + KTX2 + Meshopt via the extensions callback (only needed when you skip `useGLTF`):

```jsx
import { useLoader, useThree } from '@react-three/fiber'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'

function CompressedModel() {
  const gl = useThree((state) => state.gl)
  const gltf = useLoader(GLTFLoader, '/model.glb', (loader) => {
    const draco = new DRACOLoader()
    draco.setDecoderPath('/draco/')
    loader.setDRACOLoader(draco)
    loader.setKTX2Loader(new KTX2Loader().setTranscoderPath('/basis/').detectSupport(gl))
    loader.setMeshoptDecoder(MeshoptDecoder)
  })
  return <primitive object={gltf.scene} />
}
```

- Import loaders from `three/addons/...` (the `three/examples/jsm/...` paths are the legacy form).
- **v9:** the first argument may be a loader *instance* instead of the class — pool one preconfigured loader across call sites: `const loader = new GLTFLoader(); useLoader(loader, url)`.
- Fourth argument is an `onProgress` callback: `useLoader(GLTFLoader, url, undefined, (e) => console.log(e.loaded / e.total))`.
- Any result with a `.scene` gets a memoized `{ nodes, materials }` graph attached — the same lookup `useGLTF` exposes.
- Statics: `useLoader.preload(GLTFLoader, '/model.glb')` and `useLoader.clear(GLTFLoader, '/model.glb')`.

## Primitive and Clone

`<primitive object={...}>` mounts a pre-existing three.js object into the JSX tree; extra props are applied to it:

```jsx
<primitive object={gltf.scene} position={[0, -1, 0]} scale={0.5} />
```

**Never mount the same object twice.** A three.js object has one parent; a second `<primitive>` with the same `object` steals it from the first. For multiple copies of one loaded model use drei's `<Clone>`:

```jsx
import { useGLTF, Clone } from '@react-three/drei'

function Trees() {
  const { scene } = useGLTF('/models/tree.glb')
  return (
    <>
      <Clone object={scene} position={[0, 0, 0]} />
      <Clone object={scene} position={[5, 0, 0]} scale={1.5} />
      <Clone object={scene} position={[-5, 0, 0]} />
    </>
  )
}
```

`<Clone>` deep-clones the object graph while sharing geometries/materials, and accepts overrides (`castShadow`, `receiveShadow`, `inject`) applied to every node. For dozens-to-thousands of copies, switch to instancing — see [performance.md](./performance.md).

## Other Model Formats

| Format | API | Returns |
|---|---|---|
| GLTF / GLB | `useGLTF` (drei) or `useLoader(GLTFLoader, ...)` | `{ scene, nodes, materials, animations }` |
| FBX | `useFBX` (drei) | `THREE.Group` |
| OBJ (+ MTL) | `useLoader(OBJLoader)` + `useLoader(MTLLoader)` | `THREE.Group` |
| STL | `useLoader(STLLoader)` | `THREE.BufferGeometry` |

```jsx
import { useFBX } from '@react-three/drei'

function FBXModel() {
  const fbx = useFBX('/model.fbx')
  return <primitive object={fbx} scale={0.01} />
}
useFBX.preload('/model.fbx')
```

```jsx
import { useLoader } from '@react-three/fiber'
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js'
import { MTLLoader } from 'three/addons/loaders/MTLLoader.js'

function OBJModel() {
  const materials = useLoader(MTLLoader, '/model.mtl')
  const obj = useLoader(OBJLoader, '/model.obj', (loader) => {
    materials.preload()
    loader.setMaterials(materials)
  })
  return <primitive object={obj} />
}
```

```jsx
import { STLLoader } from 'three/addons/loaders/STLLoader.js'

function STLModel() {
  const geometry = useLoader(STLLoader, '/model.stl')
  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="gray" />
    </mesh>
  )
}
```

## useTexture

drei's texture hook (suspends, caches by URL, uploads to the GPU on load — call it inside `<Canvas>`). Three input shapes:

```jsx
import { useTexture } from '@react-three/drei'

// Single
const texture = useTexture('/textures/wood.jpg')

// Array — positional destructure
const [color, normal] = useTexture(['/color.jpg', '/normal.jpg'])

// Named object — keys are material prop names, so the result spreads straight onto a material
const textures = useTexture({
  map: '/color.jpg',
  normalMap: '/normal.jpg',
  roughnessMap: '/roughness.jpg',
  metalnessMap: '/metalness.jpg',
  aoMap: '/ao.jpg',
})
return (
  <mesh>
    <sphereGeometry args={[1, 64, 64]} />
    <meshStandardMaterial {...textures} />
  </mesh>
)
```

Configure after load with the second-argument callback (receives the same shape as the input — texture, array, or keyed object):

```jsx
import * as THREE from 'three'

const textures = useTexture(
  { map: '/color.jpg', normalMap: '/normal.jpg' },
  (loaded) => {
    Object.values(loaded).forEach((t) => {
      t.wrapS = t.wrapT = THREE.RepeatWrapping
      t.repeat.set(4, 4)
    })
  }
)

useTexture.preload('/textures/wood.jpg')   // module scope
```

The callback mutates the *cached* textures — every component using the same URLs sees the config. For per-instance settings, clone: `const local = useMemo(() => texture.clone(), [texture])`.

## Texture Configuration

Quick reference for the `THREE.Texture` properties you set in loader callbacks:

| Property | Values | Notes |
|---|---|---|
| `wrapS`, `wrapT` | `THREE.ClampToEdgeWrapping` (default) / `RepeatWrapping` / `MirroredRepeatWrapping` | A repeat wrap mode is required for `repeat` to tile |
| `repeat` | `Vector2` | `texture.repeat.set(4, 4)` tiles 4×4 |
| `offset` | `Vector2` | Shifts UVs |
| `rotation` | radians | Rotates around `center` |
| `center` | `Vector2` | `(0.5, 0.5)` = rotate about the middle |
| `minFilter` | `LinearMipmapLinearFilter` (default) / `NearestFilter` / `LinearFilter` | `Nearest*` = pixelated |
| `magFilter` | `LinearFilter` (default) / `NearestFilter` | `NearestFilter` for pixel art |
| `anisotropy` | 1–16 | `gl.capabilities.getMaxAnisotropy()`; sharpens textures at grazing angles |
| `generateMipmaps` | `true` (default) | Disable for render targets / data textures that don't need them |
| `flipY` | `true` (TextureLoader default), `false` (GLTF convention) | Hand-loaded texture upside down on a GLTF mesh → set `flipY = false` |
| `colorSpace` | see [Color Spaces](#color-spaces) | |

### Second UV Set (aoMap / lightMap)

`aoMap` and `lightMap` sample whichever UV set the texture's `channel` selects — `0` (the default) reads the base `uv`, `1` reads `uv1` (the attribute named `uv2` before three r151). `useGLTF` sets `channel = 1` for you when the AO is baked against `TEXCOORD_1`; a map that shares the base UVs needs nothing. For procedural geometry with a **separate** AO UV layout, author `uv1` and point the map at it:

```jsx
import { useEffect, useRef } from 'react'
import { BufferAttribute } from 'three'

// `aoUv` is the second UV layout the AO/lightmap was baked against.
function BakedPlane({ aoMap, aoUv }) {
  const meshRef = useRef(null)
  useEffect(() => {
    const mesh = meshRef.current
    mesh.geometry.setAttribute('uv1', new BufferAttribute(aoUv, 2)) // 'uv1' was 'uv2' before three r151
    mesh.material.aoMap.channel = 1 // 0 (default) = base `uv`; 1 = `uv1`
  }, [aoUv])
  return (
    <mesh ref={meshRef}>
      <planeGeometry args={[4, 4]} />
      <meshStandardMaterial aoMap={aoMap} aoMapIntensity={1} />
    </mesh>
  )
}
```

## Color Spaces

**v9 change:** R3F v8 automatically converted every texture prop to sRGB — which corrupted data textures (normal, displacement). v9 **removed** that conversion; textures now behave exactly as in vanilla three.js:

- **Built-in materials** handle color-texture decoding like vanilla three — GLTF-embedded textures arrive correctly annotated by `GLTFLoader`, nothing to do.
- **Hand-loaded color textures** (`TextureLoader` / `useTexture`) going into color slots: set `texture.colorSpace = THREE.SRGBColorSpace` explicitly.
- **Custom materials/shaders**: always annotate manually — imperatively, or declaratively with a pierced prop (`foo-bar` sets `.foo.bar`, e.g. `map-colorSpace={THREE.SRGBColorSpace}` on a material sets `material.map.colorSpace`).
- If you carried v8-era workarounds that force data textures back to linear, delete them — they're no-ops or bugs now.

| Texture slot | colorSpace |
|---|---|
| `map`, `emissiveMap` (color data) | `THREE.SRGBColorSpace` — set explicitly for hand-loaded textures |
| `normalMap`, `roughnessMap`, `metalnessMap`, `aoMap`, `displacementMap`, `bumpMap`, `alphaMap`, `lightMap` (data) | Leave at the linear default — never mark sRGB |
| Textures embedded in GLTF/GLB | Annotated automatically by `GLTFLoader` |
| Textures sampled in custom shaders | Annotate manually + decode consciously — see [shaders-and-custom-materials.md](./shaders-and-custom-materials.md) |

```jsx
const colorMap = useTexture('/color.jpg', (t) => {
  t.colorSpace = THREE.SRGBColorSpace
})
```

Symptom table: color map looks **washed out / desaturated** → missing sRGB annotation. Normal/roughness behaves **wrong or noisy** → a data texture was marked sRGB.

## Environment, Cube, and Video Textures

```jsx
import { useEnvironment, useCubeTexture, useVideoTexture } from '@react-three/drei'

// Equirectangular env map — preset (fetched from a CDN) or local file(s)
const envMap = useEnvironment({ preset: 'sunset' })
// presets: apartment, city, dawn, forest, lobby, night, park, studio, sunset, warehouse
const hdrMap = useEnvironment({ files: '/hdri/studio.hdr' })
const cubeEnv = useEnvironment({
  files: ['px.jpg', 'nx.jpg', 'py.jpg', 'ny.jpg', 'pz.jpg', 'nz.jpg'],
  path: '/cube/',
})

// Classic cube texture
const cubeMap = useCubeTexture(
  ['px.jpg', 'nx.jpg', 'py.jpg', 'ny.jpg', 'pz.jpg', 'nz.jpg'],
  { path: '/textures/cube/' }
)

<meshStandardMaterial envMap={envMap} metalness={1} roughness={0} />
```

For scene-wide environment lighting/background prefer the declarative `<Environment>` component — see [staging-and-drei.md](./staging-and-drei.md).

`useVideoTexture` suspends until the video can play and returns a `THREE.VideoTexture` (`texture.image` is the `HTMLVideoElement` — call `.play()`/`.pause()` on it):

```jsx
function VideoPlane() {
  const texture = useVideoTexture('/video.mp4', {
    start: true,
    loop: true,
    muted: true,           // browsers block un-muted autoplay
    crossOrigin: 'anonymous',
  })
  return (
    <mesh>
      <planeGeometry args={[(16 / 9) * 2, 2]} />
      <meshBasicMaterial map={texture} toneMapped={false} />
    </mesh>
  )
}
```

Display video (and any screen-accurate UI texture) with `toneMapped={false}` so ACES tone mapping doesn't dim it. `useVideoTexture` also accepts a `MediaStream` (webcam) instead of a URL.

## Render Targets and Procedural Textures

**useFBO** (drei) creates a `THREE.WebGLRenderTarget` (defaults to canvas size; accepts `useFBO(width, height, { samples, depth })`). Render into it inside `useFrame`, always restoring the default target:

```jsx
import { useMemo } from 'react'
import * as THREE from 'three'
import { useFrame, createPortal } from '@react-three/fiber'
import { useFBO } from '@react-three/drei'

function RenderToTexture() {
  const target = useFBO(512, 512)
  const virtualScene = useMemo(() => new THREE.Scene(), [])

  useFrame(({ gl, camera }) => {
    gl.setRenderTarget(target)
    gl.render(virtualScene, camera)
    gl.setRenderTarget(null)
  })

  return (
    <>
      {createPortal(
        <mesh>
          <sphereGeometry args={[1, 32, 32]} />
          <meshStandardMaterial color="red" />
        </mesh>,
        virtualScene
      )}
      <mesh>
        <planeGeometry args={[4, 4]} />
        <meshBasicMaterial map={target.texture} />
      </mesh>
    </>
  )
}
```

Declarative alternative: drei's `<RenderTexture attach="map">` renders its children into the parent material's texture slot (give it its own camera via `makeDefault` inside).

**CanvasTexture** — draw with 2D canvas, flag `needsUpdate` after each mutation:

```jsx
function ProceduralCanvas() {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = 256
    canvas.getContext('2d').fillRect(0, 0, 256, 256)
    return new THREE.CanvasTexture(canvas)
  }, [])

  useFrame(({ clock }) => {
    const ctx = texture.image.getContext('2d')
    ctx.fillStyle = `hsl(${(clock.elapsedTime * 50) % 360} 100% 50%)`
    ctx.fillRect(0, 0, 256, 256)
    texture.needsUpdate = true
  })

  return (
    <mesh>
      <planeGeometry args={[2, 2]} />
      <meshBasicMaterial map={texture} />
    </mesh>
  )
}
```

**DataTexture** — raw pixel buffers (defaults: `RGBAFormat`, `UnsignedByteType`, `NearestFilter`). `needsUpdate = true` is required even for the initial upload:

```jsx
const noise = useMemo(() => {
  const size = 64
  const data = new Uint8Array(size * size * 4)
  for (let i = 0; i < data.length; i += 4) {
    data[i] = data[i + 1] = data[i + 2] = Math.floor(Math.random() * 256)
    data[i + 3] = 255
  }
  const texture = new THREE.DataTexture(data, size, size)
  texture.needsUpdate = true
  return texture
}, [])
```

## Suspense and Loading UI

All loader hooks suspend. Rules:

- Put the `<Suspense>` boundary **inside** the Canvas, around the loading subtree. Fallbacks rendered there must be three.js elements (a mesh, or drei `<Html>` for DOM) — not plain divs.
- Error handling happens at the same level: wrap with a React error boundary; load failures propagate to it.
- **v9:** suspension no longer re-fires constructor/`attach` side effects repeatedly — objects initialize once, when the tree actually connects.

In-canvas mesh fallback:

```jsx
<Suspense
  fallback={
    <mesh>
      <boxGeometry />
      <meshBasicMaterial color="gray" wireframe />
    </mesh>
  }
>
  <Model />
</Suspense>
```

**Progressive loading** — nest boundaries so a low-res model shows while the high-res streams in:

```jsx
<Suspense fallback={null}>
  <Suspense fallback={<Model url="/model-low.glb" />}>
    <Model url="/model-high.glb" />
  </Suspense>
</Suspense>
```

**Progress UI** — drei `useProgress` reports global loading state; render it inside the boundary with `<Html>`:

```jsx
import { Html, useProgress } from '@react-three/drei'

function LoadingOverlay() {
  const { active, progress, errors, item, loaded, total } = useProgress()
  return <Html center>{progress.toFixed(0)} % loaded</Html>
}

// <Suspense fallback={<LoadingOverlay />}> ... </Suspense>
```

**Ready-made overlay** — drei `<Loader />` is a full-page DOM progress bar; it goes **outside** the Canvas:

```jsx
import { Loader } from '@react-three/drei'

<>
  <Canvas>
    <Suspense fallback={null}>
      <Scene />
    </Suspense>
  </Canvas>
  <Loader />
</>
```

**Load failures** — error boundary around the Suspense boundary:

```jsx
import { ErrorBoundary } from 'react-error-boundary'

<ErrorBoundary
  fallback={
    <mesh>
      <boxGeometry />
      <meshBasicMaterial color="red" wireframe />
    </mesh>
  }
>
  <Suspense fallback={null}>
    <Model />
  </Suspense>
</ErrorBoundary>
```

Failed loads are cached as rejections — remounting alone won't retry. Evict first: `useLoader.clear(GLTFLoader, url)` (or `useGLTF.clear(url)`).

## Caching and Preloading

`useLoader` (and every drei hook built on it) caches by loader + URL: **same URL → same instance**, across all components. Consequences:

- Mutating a loaded scene/texture (traverse, `repeat.set`, `colorSpace`) affects every consumer of that URL. Clone when you need per-instance state.
- Disposing a cached asset breaks all its users — this is why gltfjsx roots carry `dispose={null}`. Evict deliberately instead: `useGLTF.clear(url)` / `useLoader.clear(Loader, url)`.
- **Preload critical assets at module scope** so fetching starts at import time, not first render:

```jsx
useGLTF.preload('/models/hero.glb')
useTexture.preload('/textures/hero-color.jpg')
useLoader.preload(GLTFLoader, '/models/prop.glb')
```

- drei `<Preload all />` (inside Canvas) goes further: it pre-compiles shaders and uploads textures for everything already in the scene graph, preventing first-frame jank.
- **Lazy-load by conditional mounting**, not conditional URLs — hooks only run while mounted:

```jsx
{visible && <DetailModel />}          // correct
useGLTF(visible ? url : null)          // NOT an API — useGLTF has no null/conditional-URL form
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| App crashes or blank canvas with "suspended while rendering" — no fallback | Every loader hook suspends: wrap the loading subtree in `<Suspense>` inside the Canvas. |
| Second `<primitive object={scene}>` makes the first copy vanish | One three.js object, one parent. Use `<Clone object={scene}>` or a gltfjsx component (fresh meshes per mount, shared geometry). |
| Draco model fails under raw `useLoader(GLTFLoader)` ("No DRACOLoader instance provided") | Wire `DRACOLoader` in the extensions callback, or just use drei `useGLTF` (automatic). |
| Color texture looks washed out / desaturated | v9 no longer auto-converts: set `texture.colorSpace = THREE.SRGBColorSpace` on hand-loaded color maps (config callback or pierced prop). |
| Normal/roughness map renders wrong after marking textures sRGB | Data textures stay linear — only color maps (`map`, `emissiveMap`) get `SRGBColorSpace`. Delete v8-era colorSpace workarounds. |
| `aoMap`/`lightMap` has no visible effect | They default to channel 0 (the base `uv`); for a separate AO UV set, author `uv1` and set `material.aoMap.channel = 1` (`uv1` was `uv2` before three r151). `useGLTF` handles `TEXCOORD_1` automatically. |
| Hand-loaded texture appears upside down on a GLTF mesh | GLTF UV convention: set `texture.flipY = false` (`TextureLoader` defaults to `true`). |
| Setting `repeat`/`wrapS` on a `useTexture` result changes other components too | The cache shares one instance per URL. Clone for per-instance config: `useMemo(() => texture.clone(), [texture])`. |
| `useGLTF(visible ? url : null)` throws | Not an API. Conditionally mount the component instead: `{visible && <Model />}`. |
| Other copies go black / WebGL errors after one model unmounts | Unmount disposal hit a cached asset shared by URL. Keep `dispose={null}` on loaded-asset roots; evict explicitly with `useGLTF.clear(url)`. |
| Video texture renders black | Browsers block un-muted autoplay: pass `{ muted: true, start: true }`. Display with `toneMapped={false}`. |
| `CanvasTexture`/`DataTexture` never shows changes (or never shows at all) | Set `texture.needsUpdate = true` after every mutation — including the initial `DataTexture` fill. |
| `<Loader />` inside Canvas errors; `useProgress`+`<Html>` outside Canvas errors | `<Loader />` is DOM — render it outside Canvas. `useProgress` fallbacks with `<Html>` live inside, as the Suspense fallback. |
| Model reloads fresh but still shows the old error | Rejections are cached like results — `useLoader.clear(Loader, url)` before retrying. |
| gltfjsx output fails to type-check under v9 | Templates predate v9: replace `JSX.IntrinsicElements['group']` with `ThreeElements['group']` from `@react-three/fiber`. |

## See Also

- [staging-and-drei.md](./staging-and-drei.md) — `<Environment>` scene-wide lighting, `Stage`, shadow helpers.
- [animation.md](./animation.md) — `useAnimations` for clips loaded with the model.
- [performance.md](./performance.md) — instancing many copies, `frameloop="demand"`, disposal discipline.
- [migration-v8-to-v9.md](./migration-v8-to-v9.md) — the full v8→v9 delta, including the texture color-space change.
- [../SKILL.md](../SKILL.md) — skill overview; deep three.js internals (GLTF format, PBR theory) → sibling `threejs-mastery` skill.
- Official: [R3F loading-models tutorial](https://r3f.docs.pmnd.rs/tutorials/loading-models) · [gltfjsx](https://github.com/pmndrs/gltfjsx) ([web UI](https://gltf.pmnd.rs)) · [drei](https://github.com/pmndrs/drei).
