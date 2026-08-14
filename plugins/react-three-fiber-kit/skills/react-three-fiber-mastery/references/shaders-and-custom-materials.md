# Shaders & Custom Materials

Custom GLSL at the React-reconciler layer: drei's `shaderMaterial` factory, raw `THREE.ShaderMaterial`, patching built-in materials with `onBeforeCompile`, and per-instance attributes. GLSL language fundamentals, lighting theory, and renderer internals are out of scope — route those to the sibling `threejs-mastery` skill.

> Canvas/scene setup: see [canvas-and-project-setup.md](./canvas-and-project-setup.md) and [../SKILL.md](../SKILL.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Drei shaderMaterial Workflow](#drei-shadermaterial-workflow) | Defining, extending, and rendering reusable Drei shader materials |
| [Shader HMR](#shader-hmr) | `WaveMaterial.key` is a UUID generated each time `shaderMaterial(...)` executes |
| [v9.6 Uniform Semantics](#v96-uniform-semantics) | How React Three Fiber v9.6 applies uniform props without replacing stable objects |
| [TypeScript for Custom Elements](#typescript-for-custom-elements) | v9 types custom elements by augmenting `ThreeElements` on the `@react-three/fiber` module |
| [Raw THREE.ShaderMaterial](#raw-threeshadermaterial) | The escape hatch when you want vanilla three.js semantics |
| [Uniform Type Mapping](#uniform-type-mapping) | The GLSL declaration decides the upload path; the JS value must match its shape |
| [Varyings and Shader Built-Ins](#varyings-and-shader-built-ins) | Non-raw `ShaderMaterial` gets a prelude for free: attributes `position` |
| [Effect Cookbook](#effect-cookbook) | Vertex displacement is in the workflow example above |
| [Patching Built-In Materials](#patching-built-in-materials) | `onBeforeCompile` injects GLSL into a built-in material's shader while keeping its lighting, shadows, and fog |
| [Instanced Custom Attributes](#instanced-custom-attributes) | Feed per-instance data to a custom shader with `<instancedBufferAttribute>` |
| [External GLSL Files](#external-glsl-files) | Vite, zero-config — the `?raw` suffix imports any file as a string |
| [GLSL Performance Rules](#glsl-performance-rules) | Branch avoidance, uniform packing, loop bounds, precision, and shader recompilation costs |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## Drei shaderMaterial Workflow

The idiomatic path. Three steps: **define** (uniforms + vertex + fragment) → **extend** into the reconciler catalog → **use** as a lowercase JSX element.

```tsx
import * as THREE from 'three'
import { useRef } from 'react'
import { extend, useFrame } from '@react-three/fiber'
import { shaderMaterial } from '@react-three/drei'

// 1. Define
const WaveMaterial = shaderMaterial(
  { uTime: 0, uAmplitude: 0.25, uColor: new THREE.Color('#5599ff') },
  /* glsl */ `
    uniform float uTime;
    uniform float uAmplitude;
    varying vec2 vUv;
    void main() {
      vUv = uv;
      vec3 pos = position;
      pos.z += sin(pos.x * 3.0 + uTime) * uAmplitude;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `,
  /* glsl */ `
    uniform vec3 uColor;
    varying vec2 vUv;
    void main() {
      gl_FragColor = vec4(uColor * vUv.y, 1.0);
    }
  `
)

// 2. Register with the reconciler catalog
extend({ WaveMaterial })

// 3. Use — uniforms are FLAT JSX props, not a uniforms object
function WavePlane() {
  const material = useRef<THREE.ShaderMaterial & { uTime: number }>(null!)

  useFrame((state, delta) => {
    material.current.uTime += delta
    // or absolute time: material.current.uTime = state.clock.elapsedTime
  })

  return (
    <mesh rotation-x={-Math.PI / 2}>
      <planeGeometry args={[10, 10, 128, 128]} />
      <waveMaterial ref={material} key={WaveMaterial.key} uAmplitude={0.4} />
    </mesh>
  )
}
```

Load-bearing details:

- **Flat uniform props.** `shaderMaterial` generates a getter/setter per uniform on the class, mapping onto `this.uniforms.<name>.value`. Set them as JSX props (`uAmplitude={0.4}`) and mutate per frame via the ref (`material.current.uTime = x`) — never `ref.current.uniforms.uTime.value` on these classes (it works, but the flat accessor is the idiom and what all drei examples assume).
- **Drive time in `useFrame`**, from `state.clock.elapsedTime` (absolute) or by accumulating `delta` (pause-friendly, survives `frameloop="demand"` gaps better). Never `setState` per frame — see [hooks.md](./hooks.md).
- Regular `THREE.ShaderMaterial` properties (`transparent`, `side`, `depthWrite`, `blending`, `wireframe`) remain normal JSX props alongside the uniform props.
- Optional fourth argument: `shaderMaterial(uniforms, vert, frag, (material) => { ... })` runs once per instance for extra setup.

## Shader HMR

`WaveMaterial.key` is a UUID generated each time `shaderMaterial(...)` executes. Under Vite/webpack HMR, editing the shader source re-evaluates the module, producing a new class with a new `key` — so `key={WaveMaterial.key}` forces React to unmount the old material and mount a freshly compiled one:

```tsx
<waveMaterial key={WaveMaterial.key} ref={material} />
```

Without the `key`, React keeps the stale compiled material and you must hard-refresh to see GLSL edits. Costs nothing in production; leave it in.

## v9.6 Uniform Semantics

R3F **9.6.0 ("Sunset X", 2026-04-13)** changed how the reconciler applies a `uniforms` prop: the material's existing uniforms object now keeps a **stable reference** — an object you pass is **copied into** it (the same semantics as `position`/`rotation` copy) instead of replacing it wholesale.

```tsx
// v9.6+: safe. The compiled program's reference to material.uniforms never breaks.
<shaderMaterial
  uniforms={{ uTime: { value: 0 }, uColor: { value: new THREE.Color('red') } }}
  vertexShader={vertex}
  fragmentShader={fragment}
/>

// Pierced uniform props hit the same stable object:
<shaderMaterial uniforms-uTime-value={elapsed} vertexShader={vertex} fragmentShader={fragment} />
```

What this fixes:

- **HMR desync** — re-renders that rebuilt the `uniforms` object no longer orphan the object the compiled `WebGLProgram` closed over.
- **React Compiler auto-memoization** — the compiler may re-create inline objects; copy-into semantics make that harmless.
- **Inline/pierced uniform props** in JSX are now first-class instead of a footgun.

**Legacy note (v8 and v9.0–9.5):** passing a fresh `uniforms` object on re-render *replaced* `material.uniforms`, silently freezing all uniform updates. On those versions, memoize the uniforms object (`useMemo(() => ({ uTime: { value: 0 } }), [])`) and mutate only its `.value`s.

## TypeScript for Custom Elements

v9 types custom elements by augmenting `ThreeElements` on the `@react-three/fiber` module — **never** the old global `JSX.IntrinsicElements` namespace (removed; React 19 deprecated global JSX augmentation):

```tsx
import { extend, type ThreeElement } from '@react-three/fiber'

declare module '@react-three/fiber' {
  interface ThreeElements {
    waveMaterial: ThreeElement<typeof WaveMaterial>
  }
}

extend({ WaveMaterial })
```

If the inferred element type doesn't surface your uniform names as props, intersect them explicitly:

```tsx
declare module '@react-three/fiber' {
  interface ThreeElements {
    waveMaterial: ThreeElement<typeof WaveMaterial> & {
      uTime?: number
      uAmplitude?: number
      uColor?: THREE.Color | string
    }
  }
}
```

Alternative with zero augmentation — the **v9 factory form of `extend`** returns a typed component directly and avoids polluting the global catalog (recommended for libraries):

```tsx
const Wave = extend(WaveMaterial)
// <Wave key={WaveMaterial.key} ... />
```

**Legacy note (v8):** `declare global { namespace JSX { interface IntrinsicElements { waveMaterial: Object3DNode<...> } } }` with `Object3DNode`/`MaterialNode` types. Those types are removed in v9 — see [migration-v8-to-v9.md](./migration-v8-to-v9.md).

## Raw THREE.ShaderMaterial

The escape hatch when you want vanilla three.js semantics. Construct in `useMemo`, update via the classic `.uniforms.<name>.value` path:

```tsx
import * as THREE from 'three'
import { useMemo, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'

function RippleMesh() {
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: {
          uTime: { value: 0 },
          uResolution: { value: new THREE.Vector2(1, 1) },
        },
        vertexShader,
        fragmentShader,
        transparent: true,
      }),
    []
  )
  useEffect(() => () => material.dispose(), [material])

  useFrame((state) => {
    material.uniforms.uTime.value = state.clock.elapsedTime
  })

  return (
    <mesh material={material}>
      <planeGeometry args={[4, 4, 64, 64]} />
    </mesh>
  )
}
```

Contrast with the drei path:

| | drei `shaderMaterial` | raw `THREE.ShaderMaterial` |
|---|---|---|
| Uniform access | flat props / `ref.current.uTime` | `material.uniforms.uTime.value` |
| HMR | `key={Material.key}` remount | manual hard refresh |
| JSX element | `<waveMaterial>` after `extend` | `material={...}` prop, or catalog `<shaderMaterial>` |
| Disposal | automatic on unmount (JSX-owned) | dispose explicitly in effect cleanup |

The catalog element `<shaderMaterial vertexShader={...} fragmentShader={...} uniforms={...} />` also works without drei — with v9.6 uniform semantics (above) making inline `uniforms` objects safe.

## Uniform Type Mapping

The GLSL declaration decides the upload path; the JS value must match its shape.

| JS uniform value | GLSL declaration |
|---|---|
| `number` | `uniform float` (or `int`/`bool` if declared so) |
| `boolean` | `uniform bool` |
| `THREE.Vector2` | `uniform vec2` |
| `THREE.Vector3` | `uniform vec3` |
| `THREE.Vector4` | `uniform vec4` |
| `THREE.Color` | `uniform vec3` |
| `THREE.Matrix3` | `uniform mat3` |
| `THREE.Matrix4` | `uniform mat4` |
| `THREE.Texture` (use `null` as placeholder) | `uniform sampler2D` |
| `THREE.CubeTexture` | `uniform samplerCube` |
| `number[]` / `Float32Array` | `uniform float name[N]` |
| `THREE.Vector3[]` | `uniform vec3 name[N]` |

Texture caveat: v9 removed automatic sRGB annotation for textures fed to custom materials. Annotate color textures yourself — `texture.colorSpace = THREE.SRGBColorSpace` (or in JSX: `colorSpace={THREE.SRGBColorSpace}` on the texture element); leave data textures (normal, roughness, displacement) linear. See [loading-assets.md](./loading-assets.md).

## Varyings and Shader Built-Ins

Non-raw `ShaderMaterial` gets a prelude for free: attributes `position`, `normal`, `uv`; vertex-stage uniforms `modelMatrix`, `modelViewMatrix`, `projectionMatrix`, `viewMatrix`, `normalMatrix`, `cameraPosition` — the fragment stage only gets `viewMatrix` and `cameraPosition`. `RawShaderMaterial` gets none — declare everything.

Standard varyings block:

```glsl
// Vertex
varying vec2 vUv;
varying vec3 vNormal;          // view-space
varying vec3 vWorldPosition;

void main() {
  vUv = uv;
  vNormal = normalize(normalMatrix * normal);              // view-space normal
  vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
```

Keep coordinate spaces consistent: `normalMatrix * normal` is **view**-space; math against `cameraPosition` (world-space) needs a **world**-space normal instead — `normalize(mat3(modelMatrix) * normal)` (correct for uniform scale; for non-uniform scale compute a proper normal matrix on the CPU and pass it as a uniform).

Output note: built-in materials end with tone mapping and output color-space conversion; a raw `gl_FragColor` skips both, so custom shaders often look darker or more saturated next to built-ins. Match them by ending `main()` with:

```glsl
#include <tonemapping_fragment>
#include <colorspace_fragment>
```

(Both resolve inside non-raw `ShaderMaterial`; `colorspace_fragment` was named `encodings_fragment` before three r154.)

## Effect Cookbook

Vertex displacement is in the [workflow example](#drei-shadermaterial-workflow) above. Three more staples:

**Fresnel rim** — world-space throughout, using the `cameraPosition` built-in:

```glsl
// Vertex
varying vec3 vWorldNormal;
varying vec3 vWorldPosition;
void main() {
  vWorldNormal = normalize(mat3(modelMatrix) * normal);
  vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}

// Fragment
uniform vec3 uBaseColor;
uniform vec3 uRimColor;
varying vec3 vWorldNormal;
varying vec3 vWorldPosition;
void main() {
  vec3 viewDir = normalize(cameraPosition - vWorldPosition);
  float rim = pow(1.0 - clamp(dot(viewDir, normalize(vWorldNormal)), 0.0, 1.0), 3.0);
  gl_FragColor = vec4(mix(uBaseColor, uRimColor, rim), 1.0);
}
```

**Value noise + fbm skeleton** (one skeleton is enough — extend as needed):

```glsl
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }

float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i),                 hash(i + vec2(1.0, 0.0)), u.x),
             mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.0; a *= 0.5; }
  return v;
}
```

**Dissolve** — noise threshold + `discard`, glowing edge via `smoothstep`:

```glsl
uniform float uProgress;   // animate 0 → 1
uniform vec3 uEdgeColor;
varying vec2 vUv;
// ...hash/noise from above

void main() {
  float n = noise(vUv * 12.0);
  if (n < uProgress) discard;
  float edge = 1.0 - smoothstep(uProgress, uProgress + 0.08, n);
  vec3 base = vec3(0.2, 0.2, 0.25);
  gl_FragColor = vec4(mix(base, uEdgeColor, edge), 1.0);
}
```

Pair with `side={THREE.DoubleSide}` so the hollowed interior stays visible. `discard` disables early-depth optimizations — keep dissolve materials off large overdraw-heavy surfaces.

## Patching Built-In Materials

`onBeforeCompile` injects GLSL into a built-in material's shader while keeping its lighting, shadows, and fog. Assign it (and a stable uniform container) via props:

```tsx
import * as THREE from 'three'
import { useCallback, useRef } from 'react'
import { useFrame, type ThreeElements } from '@react-three/fiber'

function WavyStandardMaterial(props: ThreeElements['meshStandardMaterial']) {
  const uTime = useRef({ value: 0 })

  const onBeforeCompile = useCallback((shader: THREE.WebGLProgramParametersWithUniforms) => {
    shader.uniforms.uTime = uTime.current
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uTime;')
      .replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
         transformed.y += sin(transformed.x * 4.0 + uTime) * 0.1;`
      )
  }, [])

  useFrame((state) => {
    uTime.current.value = state.clock.elapsedTime
  })

  return (
    <meshStandardMaterial
      {...props}
      onBeforeCompile={onBeforeCompile}
      customProgramCacheKey={() => 'wavy-standard-v1'}
    />
  )
}
```

Injection points (patch by replacing the `#include` with itself plus your code):

| Chunk | Stage | In scope | Typical patch |
|---|---|---|---|
| `#include <common>` | both | prelude | declare uniforms / helper functions |
| `#include <begin_vertex>` | vertex | `vec3 transformed` (local-space position) | displace vertices |
| `#include <beginnormal_vertex>` | vertex | `vec3 objectNormal` | bend normals to match displacement |
| `#include <project_vertex>` | vertex | `mvPosition`, writes `gl_Position` | post-projection tweaks |
| `#include <color_fragment>` | fragment | `vec4 diffuseColor` | tint/pattern albedo before lighting |
| `#include <opaque_fragment>` | fragment | writes `gl_FragColor` from the lit result | override final color — **renamed from `output_fragment` in three r154**; old snippets no-op silently |
| `#include <fog_fragment>` | fragment | after fog is mixed | last word after fog |

`customProgramCacheKey` caveats:

- Three caches compiled programs keyed by `material.customProgramCacheKey()`, which **defaults to `onBeforeCompile.toString()`**. Two instances whose callbacks stringify identically share one program — even if closured values differ. If the injected GLSL varies per instance, return a distinct key per variant; if it's identical, share the key (program reuse is the goal).
- Assigning a new `onBeforeCompile` to an already-compiled material does nothing until `material.needsUpdate = true`.
- Update uniforms through the shared container you captured (`uTime.current.value`), never by re-running the patch.

For anything beyond a couple of chunk replacements, use **three-custom-shader-material** (`three-custom-shader-material` on npm): it extends built-ins declaratively — `<CustomShaderMaterial baseMaterial={THREE.MeshPhysicalMaterial} vertexShader={...} fragmentShader={...} uniforms={...} />` with `csm_*` output variables — and keeps the base material's full lighting pipeline without string surgery. Mentioned here as the community-standard escalation path; see its docs for the API.

## Instanced Custom Attributes

Feed per-instance data to a custom shader with `<instancedBufferAttribute>`. **v9 uses the constructor-`args` form** — the v8 `count`/`array`/`itemSize` props are gone:

```tsx
import { useMemo } from 'react'

// ConfettiMaterial: a drei shaderMaterial defined + extended as in the workflow section
function Confetti({ count = 1000 }: { count?: number }) {
  const offsets = useMemo(() => {
    const a = new Float32Array(count * 3)
    for (let i = 0; i < a.length; i++) a[i] = (Math.random() - 0.5) * 20
    return a
  }, [count])

  return (
    <instancedMesh args={[undefined, undefined, count]}>
      <planeGeometry args={[0.2, 0.2]}>
        <instancedBufferAttribute attach="attributes-aOffset" args={[offsets, 3]} />
      </planeGeometry>
      <confettiMaterial key={ConfettiMaterial.key} />
    </instancedMesh>
  )
}
```

```glsl
// Vertex shader: declare the attribute yourself
attribute vec3 aOffset;
varying vec2 vUv;

void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position + aOffset, 1.0);
}
```

- The first two `args` of `<instancedMesh>` stay empty — geometry and material come from JSX children.
- To also honor matrices set via `setMatrixAt`, multiply `instanceMatrix` into the position (`... * modelViewMatrix * instanceMatrix * vec4(...)`); three declares that attribute automatically for non-raw `ShaderMaterial` when the object is an `InstancedMesh`.
- Changing `args` reconstructs the attribute — resize by changing `count`-derived arrays, not by mutating in place past the buffer length.
- Instancing strategy and draw-call budgeting live in [performance.md](./performance.md).

## External GLSL Files

Vite, zero-config — the `?raw` suffix imports any file as a string:

```ts
import vertexShader from './wave.vert.glsl?raw'
import fragmentShader from './wave.frag.glsl?raw'
```

Or `vite-plugin-glsl` for `#include` resolution across shader files plus minification:

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import glsl from 'vite-plugin-glsl'

export default defineConfig({ plugins: [glsl()] })
```

```ts
// src/glsl.d.ts — type shim for bare .glsl imports
declare module '*.glsl' {
  const src: string
  export default src
}
```

Tag inline strings with `/* glsl */` template comments to get editor syntax highlighting (e.g. the `glsl-literal` class of extensions) without any build change.

## GLSL Performance Rules

- Prefer `mix`/`step`/`smoothstep` over `if/else` — divergent branches serialize GPU warps; a select is nearly free.
- Pack related scalars into `vec2`/`vec4` uniforms instead of many floats — fewer uniform slots and uploads.
- Precompute anything constant per frame on the CPU (once in `useFrame`), not per fragment (millions of times).
- Move math to the vertex stage whenever linear interpolation of the result is acceptable — fragments outnumber vertices by orders of magnitude.
- Replace expensive functions with texture lookups (gradient ramps, precomputed noise).
- Minimize varyings; each one costs interpolation bandwidth.
- `discard` and `transparent` both defeat depth optimizations — use `alphaTest`-style thresholds and opaque materials where the look allows.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Editing GLSL under HMR changes nothing until a hard refresh | Add `key={WaveMaterial.key}` to the JSX element — the key regenerates when the module re-evaluates, forcing a remount + recompile. |
| `material.uTime = x` on a raw `THREE.ShaderMaterial` silently does nothing | Flat uniform accessors exist only on drei `shaderMaterial` classes. For raw materials use `material.uniforms.uTime.value = x`. |
| Uniform animation freezes after a re-render (R3F ≤ 9.5 / v8) | A fresh `uniforms` object replaced `material.uniforms` while the compiled program kept the old reference. Upgrade to 9.6+ (copy-into semantics), or memoize the uniforms object with `useMemo`. |
| `declare global { namespace JSX ... }` augmentation errors or doesn't type `<waveMaterial>` | v8 idiom. v9: `declare module '@react-three/fiber' { interface ThreeElements { waveMaterial: ThreeElement<typeof WaveMaterial> } }` — or skip augmentation with factory `extend(WaveMaterial)`. |
| `.replace('#include <output_fragment>', ...)` has no visible effect on three ≥ r154 | The chunk was renamed `opaque_fragment`; `String.replace` with a missing needle is a silent no-op. |
| `onBeforeCompile` assigned after the material already rendered doesn't apply | Set `material.needsUpdate = true` to trigger a recompile. |
| Two patched material instances render the same variant despite different closured constants | Default program cache key is `onBeforeCompile.toString()` — identical source, identical key. Override `customProgramCacheKey` per variant. |
| Custom-shader mesh ignores scene lights | `ShaderMaterial` implements no lighting. Patch a built-in via `onBeforeCompile` or use `three-custom-shader-material` to keep the PBR pipeline. |
| Custom shader looks darker/more saturated than built-in materials next to it | Built-ins end with tone mapping + output color-space conversion. Append `#include <tonemapping_fragment>` and `#include <colorspace_fragment>` at the end of `main()`. |
| Color texture sampled in a custom shader looks washed out | v9 removed automatic sRGB annotation for custom materials — set `texture.colorSpace = THREE.SRGBColorSpace` yourself; keep data textures linear. |
| `<instancedBufferAttribute count={n} array={a} itemSize={3} />` renders nothing / TS error | v8 form. v9 takes constructor args: `args={[array, itemSize]}`. |
| `setState` in `useFrame` to push a uniform value into a prop | Never setState in the frame loop — mutate the material ref directly (`ref.current.uTime = ...`). See [hooks.md](./hooks.md). |
| Fresnel/rim math looks wrong as the camera orbits | Coordinate-space mismatch: `normalMatrix * normal` is view-space but `cameraPosition` is world-space. Use `mat3(modelMatrix) * normal` for world-space math. |

## See Also

- [objects-jsx-and-typescript.md](./objects-jsx-and-typescript.md) — `extend`, `attach`, `args`, and `ThreeElements` typing in depth.
- [hooks.md](./hooks.md) — the `useFrame`/`useThree` contract that drives uniform updates.
- [performance.md](./performance.md) — instancing, `frameloop="demand"`, and re-render discipline.
- [postprocessing.md](./postprocessing.md) — full-screen shader effects, as opposed to per-material shaders.
- [../SKILL.md](../SKILL.md) — skill overview and shared setup.
- External: [drei shaderMaterial docs](https://drei.docs.pmnd.rs/shaders/shader-material) · [THREE.ShaderMaterial reference](https://threejs.org/docs/#api/en/materials/ShaderMaterial) · [The Book of Shaders](https://thebookofshaders.com/)
