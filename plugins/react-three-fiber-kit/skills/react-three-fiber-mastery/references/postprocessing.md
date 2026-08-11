# Post-processing

Screen-space effects in R3F via `@react-three/postprocessing` (v3), the React wrapper around pmndrs' `postprocessing` library. Effects are declared as JSX children of `<EffectComposer>` and merged into as few fullscreen passes as possible. This file covers the React layer only — the imperative `three/addons` pipeline is a different system (see [Native three.js Post-Processing](#native-threejs-post-processing)).

> Scene/Canvas setup: see [../SKILL.md](../SKILL.md). Custom *materials* (shaders on objects, not on the screen): see [shaders-and-custom-materials.md](./shaders-and-custom-materials.md).

**Contents:** [Install and Versions](#install-and-versions) · [EffectComposer](#effectcomposer) · [Effect Ordering](#effect-ordering) · [Bloom and Emissive Glow](#bloom-and-emissive-glow) · [Selective Effects: Selection and Select](#selective-effects-selection-and-select) · [Depth of Field](#depth-of-field) · [Ambient Occlusion: N8AO and SSAO](#ambient-occlusion-n8ao-and-ssao) · [Outline](#outline) · [God Rays](#god-rays) · [Tone Mapping and Color Grading](#tone-mapping-and-color-grading) · [Anti-Aliasing](#anti-aliasing) · [Custom Effects](#custom-effects) · [Animating Effect Parameters](#animating-effect-parameters) · [Performance and Mobile Scaling](#performance-and-mobile-scaling) · [Native three.js Post-Processing](#native-threejs-post-processing) · [Common Mistakes](#common-mistakes) · [See Also](#see-also)

## Install and Versions

```bash
npm install @react-three/postprocessing postprocessing
```

| Package | Line | Requires |
| --- | --- | --- |
| `@react-three/postprocessing` | **3.x (current)** | fiber `^9.0.0`, react `^19.0`, three `>= 0.156.0` |
| `@react-three/postprocessing` | 2.x (legacy) | fiber 8 / React 18 — do not pair with R3F 9 |
| `postprocessing` | `^6.36.6` (resolved by 3.x) | — |

v3 declares `postprocessing` — plus `n8ao` and `maath` — as regular dependencies, so a bare `npm install @react-three/postprocessing` works. Still add `postprocessing` explicitly whenever you import from it directly (`BlendFunction`, `ToneMappingMode`, `Effect`, loaders): strict layouts (pnpm) reject undeclared imports.

## EffectComposer

Place `<EffectComposer>` inside `<Canvas>`, after scene content. Effects go inside it, nothing else renders the chain.

```jsx
import { Canvas } from '@react-three/fiber'
import { EffectComposer, Bloom, ToneMapping } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'

function App() {
  return (
    <Canvas>
      <ambientLight intensity={0.5} />
      <mesh>
        <sphereGeometry args={[1, 64, 64]} />
        <meshStandardMaterial emissive="hotpink" emissiveIntensity={3} toneMapped={false} />
      </mesh>
      <EffectComposer>
        <Bloom mipmapBlur intensity={1} luminanceThreshold={1} />
        <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
      </EffectComposer>
    </Canvas>
  )
}
```

| Prop | Default | Meaning |
| --- | --- | --- |
| `enabled` | `true` | Render the chain. `false` hands rendering back to R3F. Prefer toggling this over unmounting — buffers stay allocated. |
| `multisampling` | `8` | MSAA samples on the composer's framebuffer. Set `0` when using SMAA/FXAA or on weak GPUs. |
| `autoClear` | `true` | Clear before render. Set `false` for `Outline` + `Selection`. |
| `depthBuffer` | — | Force a depth buffer on the render target (depth-based effects request what they need). |
| `stencilBuffer` | `false` | Enable stencil buffer. |
| `enableNormalPass` | `false` | Adds a normal pass. **Required by `SSAO`** (the type comment says "only used for SSGI", but `SSAO` errors without it). `N8AO` does not need it. |
| `resolutionScale` | — | Scales the depth-downsampling pass paired with the normal pass — *not* a global resolution scale (use Canvas `dpr` for that). |
| `frameBufferType` | `HalfFloatType` | HDR buffers by default — this is why emissive values above 1.0 survive to Bloom. |
| `renderPriority` | `1` | The composer renders in a `useFrame(cb, priority)` takeover. Coordinate if you also render manually. |
| `camera` / `scene` | R3F defaults | Override what the composer renders. |

Behavior to know:

- **Tone mapping is hijacked.** While mounted, the composer sets `gl.toneMapping = NoToneMapping` (restored on unmount) so the chain runs in HDR. Canvas's default ACES look disappears — add a `<ToneMapping>` effect near the end of the chain to get a filmic response back.
- **Rendering happens in `useFrame` at priority 1** (a takeover), so `frameloop="demand"` works normally — `invalidate()` triggers a composed frame.
- **Children are merged into passes.** Consecutive non-convolution effects share one fullscreen `EffectPass`; effects carrying the convolution flag (`ChromaticAberration`, `SMAA` in current `postprocessing`) each need their own pass. Heavyweight effects (Bloom, DepthOfField, GodRays) blur in their own internal render passes but still merge. Order children so mergeable effects sit next to each other.
- Use **one** composer. Stacking composers multiplies fullscreen renders.

## Effect Ordering

Children order = pass order. Canonical chain:

1. Ambient occlusion (`N8AO` / `SSAO`) — operates on scene depth/normals, before anything smears the image.
2. Heavyweight effects (`Bloom`, `DepthOfField`, `GodRays`) — each runs its own internal blur passes.
3. Color grading (`ToneMapping`, `HueSaturation`, `BrightnessContrast`, `LUT`) — grade the composited HDR image.
4. Overlays (`Vignette`, `Noise`, `ChromaticAberration`).
5. **Anti-aliasing last** (`SMAA` / `FXAA`) — AA earlier gets re-jagged by later effects.

```jsx
<EffectComposer multisampling={0}>
  <N8AO quality="medium" />
  <Bloom mipmapBlur intensity={0.8} luminanceThreshold={1} />
  <ToneMapping mode={ToneMappingMode.AGX} />
  <HueSaturation saturation={0.1} />
  <Vignette offset={0.3} darkness={0.6} />
  <Noise premultiply opacity={0.4} />
  <SMAA />
</EffectComposer>
```

## Bloom and Emissive Glow

| Prop | Default | Notes |
| --- | --- | --- |
| `intensity` | `1.0` | Overall bloom strength. |
| `luminanceThreshold` | `1.0` | Pixels below this luminance are masked out. `1.0` = only HDR pixels bloom. |
| `luminanceSmoothing` | `0.03` | Softness of the threshold cutoff. |
| `mipmapBlur` | `true` | Modern wide, soft bloom. Leave on; the non-mipmap path is deprecated. |
| `radius` | `0.85` | Blur radius (mipmapBlur only). |
| `levels` | `8` | MIP levels (mipmapBlur only). Lower = tighter and cheaper. |
| `blendFunction` | `BlendFunction.ADD` | The `<Bloom>` wrapper's default — the raw `BloomEffect` defaults to `SCREEN`. |

(Defaults from `postprocessing` 6.39.x — set the ones you rely on explicitly.)

**The glow recipe.** Bloom picks up pixels whose luminance exceeds `luminanceThreshold`. With the default threshold of `1.0` that means HDR pixels only, so a material must output values **above 1.0**:

```jsx
// Lit material: emissive color × intensity > 1
<meshStandardMaterial
  color="black"
  emissive="#ff40a0"
  emissiveIntensity={4}
  toneMapped={false}
/>

// Unlit variant: HDR color array, same rule
<meshBasicMaterial color={[4, 1.5, 8]} toneMapped={false} />
```

Both halves are load-bearing: the emissive intensity (or HDR color components) must push output past 1.0, **and** `toneMapped={false}` stops three.js from compressing it back under 1.0 before Bloom samples it. Every other surface stays below the threshold, so the glow *looks* selective with a single cheap `<Bloom>` — no selection machinery needed. Reach for [`<SelectiveBloom>`](#selective-effects-selection-and-select) only when objects must bloom without HDR materials.

## Selective Effects: Selection and Select

`<Selection>` provides a context; every `<Select enabled>` subtree contributes its meshes to the current selection (multi-select is just multiple enabled `<Select>`s). **Only `SelectiveBloom` and `Outline` consume the selection context — plain `<Bloom>` ignores it entirely.**

```jsx
import { useRef } from 'react'
import { EffectComposer, SelectiveBloom, Selection, Select } from '@react-three/postprocessing'

function Scene() {
  const ambientRef = useRef(null)
  return (
    <Selection>
      <ambientLight ref={ambientRef} intensity={0.6} />
      <EffectComposer>
        <SelectiveBloom lights={[ambientRef]} intensity={2} luminanceThreshold={0} mipmapBlur />
      </EffectComposer>

      <Select enabled>
        <mesh>
          <torusKnotGeometry args={[0.6, 0.2, 128, 32]} />
          <meshStandardMaterial color="orange" />
        </mesh>
      </Select>

      {/* Not selected — never blooms, even below threshold 0 */}
      <mesh position={[2, 0, 0]}>
        <boxGeometry />
        <meshStandardMaterial color="royalblue" />
      </mesh>
    </Selection>
  )
}
```

- `<Selection>` must wrap **both** the composer and the selectable scene content.
- `SelectiveBloom` requires a `lights` prop (array of light refs or instances) — it warns and renders nothing useful without lights. Extra props: `inverted` (bloom everything *except* the selection), `ignoreBackground`.
- Both `SelectiveBloom` and `Outline` also accept a direct `selection={[refOrObject, ...]}` prop plus `selectionLayer` if you prefer skipping the context. Direct `selection` is ignored while a surrounding `<Selection>` context exists.

## Depth of Field

```jsx
import { EffectComposer, DepthOfField } from '@react-three/postprocessing'

<EffectComposer>
  <DepthOfField focusDistance={0.01} focalLength={0.05} bokehScale={3} />
</EffectComposer>
```

| Prop | Meaning |
| --- | --- |
| `focusDistance` | Normalized `[0, 1]` distance to the focal plane. |
| `focalLength` | Normalized focal length — smaller = shallower depth of field. |
| `focusRange` | Normalized in-focus band around the focal plane. |
| `worldFocusDistance` / `worldFocusRange` | Same, in world units — usually easier to reason about. |
| `bokehScale` | Size of the bokeh blur. |
| `target` | **World-space point** (`[x, y, z]` or `Vector3`) to focus on. |

`target` is a position, **not** an object ref — the v8-era `target={meshRef}` idiom does not exist in v3. To track a moving object or the pointer, use `<Autofocus>` (exported by the library): it wraps DepthOfField and drives focus via GPU depth-picking with damping:

```jsx
import { Autofocus } from '@react-three/postprocessing'

<EffectComposer>
  <Autofocus mouse smoothTime={0.3} bokehScale={4} />
  {/* or: <Autofocus target={[0, 0, -5]} /> — omit both to focus screen center */}
</EffectComposer>
```

## Ambient Occlusion: N8AO and SSAO

**Prefer `N8AO`.** It is exported directly from `@react-three/postprocessing` (backed by the bundled `n8ao` package's `N8AOPostPass`), computes its own normals, and looks better than SSAO at similar cost.

```jsx
import { EffectComposer, N8AO } from '@react-three/postprocessing'

<EffectComposer>
  <N8AO aoRadius={0.5} intensity={1} quality="medium" halfRes />
</EffectComposer>
```

| Prop | Notes |
| --- | --- |
| `quality` | `'performance' \| 'low' \| 'medium' \| 'high' \| 'ultra'` — presets for samples/denoise. |
| `halfRes` | Compute AO at half resolution — large win on mobile, minor quality loss. |
| `aoRadius` / `distanceFalloff` / `intensity` | Core look controls (world units / falloff / strength). |
| `aoSamples` / `denoiseSamples` / `denoiseRadius` | Manual overrides of what `quality` presets set. |
| `color` | AO tint (default black). |
| `screenSpaceRadius` | Treat `aoRadius` as screen-space pixels instead of world units. |

`SSAO` (the classic effect from `postprocessing`) additionally **requires the composer's normal pass** — without it the wrapper logs "Please enable the NormalPass in the EffectComposer" and renders nothing:

```jsx
<EffectComposer enableNormalPass>
  <SSAO samples={30} radius={0.1} intensity={25} luminanceInfluence={0.6} worldDistanceThreshold={24} worldDistanceFalloff={0} worldProximityThreshold={0.4} worldProximityFalloff={0.1} />
</EffectComposer>
```

## Outline

Outline consumes the same `<Selection>`/`<Select>` machinery. Pair it with `autoClear={false}` on the composer:

```jsx
import { useState } from 'react'
import { EffectComposer, Outline, Selection, Select } from '@react-three/postprocessing'

function Shape(props) {
  const [hovered, setHovered] = useState(false)
  return (
    <Select enabled={hovered}>
      <mesh
        {...props}
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true) }}
        onPointerOut={() => setHovered(false)}
      >
        <boxGeometry />
        <meshStandardMaterial color="orange" />
      </mesh>
    </Select>
  )
}

function Scene() {
  return (
    <Selection>
      <EffectComposer autoClear={false}>
        <Outline visibleEdgeColor={0xffffff} hiddenEdgeColor={0x22090a} edgeStrength={10} pulseSpeed={0} blur xRay />
      </EffectComposer>
      <Shape position={[-1.5, 0, 0]} />
      <Shape position={[1.5, 0, 0]} />
    </Selection>
  )
}
```

| Prop | Notes |
| --- | --- |
| `visibleEdgeColor` / `hiddenEdgeColor` | Hex numbers; hidden = occluded portions (with `xRay`). |
| `edgeStrength` | Edge brightness. |
| `pulseSpeed` | `> 0` animates a pulse. |
| `xRay` | Show outline through occluders. |
| `blur` / `kernelSize` | Soft outline. |
| `selection` / `selectionLayer` | Direct ref-array alternative to `<Selection>`. |

Each `<Select enabled>` toggles its subtree in and out of the selection independently — hover state per item gives multi-select outlining for free.

## God Rays

`<GodRays sun={...}>` accepts a `Mesh`/`Points` instance or a ref to one. The sun mesh must exist **before** the effect constructs, which creates the classic gotcha:

```jsx
// BROKEN — never mounts. Assigning to sunRef.current does not re-render,
// so the condition is still false after the mesh mounts.
function Broken() {
  const sunRef = useRef(null)
  return (
    <>
      <mesh ref={sunRef} position={[0, 10, -30]}>…</mesh>
      <EffectComposer>
        {sunRef.current && <GodRays sun={sunRef} />}
      </EffectComposer>
    </>
  )
}
```

Use a **ref callback into state** — the state update re-renders and mounts the effect:

```jsx
import { useState } from 'react'
import { EffectComposer, GodRays } from '@react-three/postprocessing'

function SunAndRays() {
  const [sun, setSun] = useState(null)
  return (
    <>
      <mesh ref={setSun} position={[0, 10, -30]}>
        <sphereGeometry args={[4, 32, 32]} />
        <meshBasicMaterial color="#ffddaa" toneMapped={false} />
      </mesh>
      {sun && (
        <EffectComposer>
          <GodRays sun={sun} samples={60} density={0.96} decay={0.9} weight={0.4} exposure={0.6} clampMax={1} blur />
        </EffectComposer>
      )}
    </>
  )
}
```

Make the sun unlit (`meshBasicMaterial`) and `toneMapped={false}` so it stays bright. `samples` is the main cost knob; `density`/`decay`/`weight`/`exposure` shape the shafts.

## Tone Mapping and Color Grading

The composer disables renderer tone mapping (see [EffectComposer](#effectcomposer)), so grade inside the chain — late, before AA:

```jsx
import { ToneMapping } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'

<ToneMapping mode={ToneMappingMode.AGX} />
```

`ToneMappingMode` (verified against `postprocessing` 6.39): `LINEAR`, `REINHARD`, `REINHARD2`, `REINHARD2_ADAPTIVE`, `UNCHARTED2`, `OPTIMIZED_CINEON`, `CINEON`, `ACES_FILMIC`, `AGX` (default), `NEUTRAL`. `AGX` and `NEUTRAL` need a recent `postprocessing` (any version satisfying v3's `^6.36.6` has both); `NEUTRAL` (Khronos PBR neutral) additionally requires three r162+. The Reinhard2 modes take extra props (`resolution`, `whitePoint`, `middleGrey`, `minLuminance`, `averageLuminance`, `adaptationRate`); other modes ignore them.

One-liners (all from `@react-three/postprocessing`; `BlendFunction` from `postprocessing`):

| Effect | Key props | Use |
| --- | --- | --- |
| `<Vignette />` | `offset` (size), `darkness`, `eskil` | Darkened corners. |
| `<Noise />` | `premultiply`, `opacity`, `blendFunction` | Film grain. |
| `<ChromaticAberration />` | `offset={[x, y]}`, `radialModulation`, `modulationOffset` | RGB fringe. |
| `<HueSaturation />` | `hue` (radians), `saturation` (−1…1) | Global hue/sat shift. |
| `<BrightnessContrast />` | `brightness`, `contrast` (−1…1) | Simple levels. |
| `<Sepia />` | `intensity` | Sepia tint. |
| `<Pixelation />` | `granularity` | Chunky pixels. |
| `<Glitch />` | `delay`, `duration`, `strength` (each `[min,max]`), `mode` (`GlitchMode`), `active` | Digital glitch bursts. |
| `<LUT />` | `lut` (load a `.cube` via `useLoader(LUTCubeLoader, url)` from `postprocessing`) | Film-stock color lookup. |

## Anti-Aliasing

Three options — pick **one**:

| Approach | How | Trade-off |
| --- | --- | --- |
| MSAA | `<EffectComposer multisampling={8}>` (default) | Best geometric edges; costs framebuffer memory/bandwidth. |
| SMAA | `<SMAA />` as the **last** effect, `multisampling={0}` | Good quality, cheaper than MSAA on many GPUs. |
| FXAA | `<FXAA />` last, `multisampling={0}` | Cheapest; slightly blurrier. |

```jsx
<EffectComposer multisampling={0}>
  <Bloom mipmapBlur luminanceThreshold={1} />
  <SMAA />
</EffectComposer>
```

The `multisampling={0}` rule: MSAA and SMAA/FXAA solve the same problem — running both wastes GPU for no visible gain.

## Custom Effects

Subclass `Effect` from `postprocessing`. The fragment shader implements the `mainImage` convention (and optionally `mainUv` for distortion); uniforms are a `Map`; per-frame work goes in `update()`:

```jsx
import { useMemo } from 'react'
import { Uniform } from 'three'
import { Effect, BlendFunction } from 'postprocessing'

const fragmentShader = /* glsl */ `
  uniform float uTime;
  uniform float uStrength;

  void mainUv(inout vec2 uv) {
    uv.x += sin(uv.y * 12.0 + uTime) * 0.005 * uStrength;
  }

  void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
    outputColor = vec4(inputColor.rgb * (1.0 - 0.1 * uStrength), inputColor.a);
  }
`

class WaveEffect extends Effect {
  constructor({ strength = 1 } = {}) {
    super('WaveEffect', fragmentShader, {
      blendFunction: BlendFunction.NORMAL,
      uniforms: new Map([
        ['uTime', new Uniform(0)],
        ['uStrength', new Uniform(strength)],
      ]),
    })
  }

  update(renderer, inputBuffer, deltaTime) {
    this.uniforms.get('uTime').value += deltaTime
  }
}
```

Mount it either way — no `forwardRef` needed (React 19 passes `ref` as a prop):

```jsx
// Option A: memoized instance via <primitive>
function WaveDistortion({ strength = 1 }) {
  const effect = useMemo(() => new WaveEffect({ strength }), [strength])
  return <primitive object={effect} dispose={null} />
}

// Option B: wrapEffect — props become constructor options (+ blendFunction/opacity)
import { wrapEffect } from '@react-three/postprocessing'
const Wave = wrapEffect(WaveEffect)
// <Wave strength={0.5} />
```

Notes:

- `mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor)` is the exact required signature; `postprocessing` prefixes your uniforms/functions internally to avoid collisions when merging effects into one pass.
- Prop changes on `wrapEffect` components (and `args` changes generally) **reconstruct the effect** — animate through refs, not props.
- Advanced integrations (custom `Pass` coordination) can read `EffectComposerContext` (exported by the library) for `{ composer, camera, scene, normalPass }`. Only `postprocessing` `Pass` instances work as composer children — three/addons passes are a different class.

## Animating Effect Parameters

Mutate the effect instance through a ref inside `useFrame` — never `setState` per frame, and never drive wrapped-effect props from state (each change rebuilds the effect):

```jsx
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { EffectComposer, Bloom, ChromaticAberration } from '@react-three/postprocessing'

function PulsingEffects() {
  const bloomRef = useRef(null)
  const caRef = useRef(null)

  useFrame(({ clock }) => {
    const t = clock.elapsedTime
    if (bloomRef.current) bloomRef.current.intensity = 1.2 + Math.sin(t * 2) * 0.4
    if (caRef.current) caRef.current.offset.set(Math.sin(t * 4) * 0.0015, 0)
  })

  return (
    <EffectComposer>
      <Bloom ref={bloomRef} mipmapBlur luminanceThreshold={1} />
      <ChromaticAberration ref={caRef} offset={[0.001, 0]} />
    </EffectComposer>
  )
}
```

Refs resolve to the underlying `postprocessing` effect instance, so the mutable surface is the effect's own API (`intensity`, `offset: Vector2`, `uniforms.get('name').value`, …).

## Performance and Mobile Scaling

- Every effect costs fill rate; Bloom, DoF, and GodRays cost the most (each runs internal blur passes). Budget 2–4 effects on mobile.
- Group non-convolution effects adjacently so they merge into one pass.
- Toggle the whole chain with `enabled` instead of unmounting.
- `frameloop="demand"` + `invalidate()` works unchanged — the composer renders inside the frameloop.

```jsx
import { useDetectGPU } from '@react-three/drei'
import { EffectComposer, N8AO, Bloom, ToneMapping, FXAA } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'

function AdaptiveEffects() {
  const gpu = useDetectGPU()
  const low = gpu.isMobile || gpu.tier < 2

  return (
    <EffectComposer multisampling={low ? 0 : 8}>
      {!low && <N8AO quality="medium" halfRes />}
      <Bloom
        mipmapBlur
        intensity={low ? 0.6 : 1}
        radius={low ? 0.6 : 0.85}
        levels={low ? 4 : 8}
        luminanceThreshold={1}
      />
      <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
      {low && <FXAA />}
    </EffectComposer>
  )
}
```

The low-end branch: `multisampling={0}` (+ cheap FXAA), drop ambient occlusion first, then shrink bloom (`levels`/`radius`). Global resolution scaling belongs on Canvas `dpr`, not the composer. More scene-side techniques: [performance.md](./performance.md).

## Native three.js Post-Processing

Three.js ships its own imperative pipeline (`EffectComposer` from `three/addons/postprocessing/EffectComposer.js`, `RenderPass`, `UnrealBloomPass`, …). It is a **different, non-React system**: you construct passes manually, call `composer.render()` per frame, and its `Pass` class is incompatible with `postprocessing`'s. Don't mix the two, and don't port `UnrealBloomPass` recipes into `<EffectComposer>` — in R3F, use `@react-three/postprocessing` and its equivalents. For the native pipeline itself, see the sibling `threejs-mastery` skill.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Nothing glows after adding `<Bloom>` | Default `luminanceThreshold` is `1.0` — only HDR pixels bloom. Give the material `emissive` + `emissiveIntensity` > 1 **and** `toneMapped={false}` (or lower the threshold and accept whole-scene bloom). |
| Wrapped meshes in `<Select>` but plain `<Bloom>` still blooms everything | Only `SelectiveBloom` and `Outline` read the `<Selection>` context; `<Bloom>` ignores it. Use `<SelectiveBloom lights={[...]}>` or the HDR-emissive recipe. |
| Scene looks flat/washed out the moment `<EffectComposer>` mounts | The composer sets `gl.toneMapping = NoToneMapping`. Add `<ToneMapping mode={ToneMappingMode.ACES_FILMIC} />` late in the chain. |
| `{sunRef.current && <GodRays sun={sunRef} />}` never appears | Ref assignment doesn't re-render, so the condition stays false forever. Use `const [sun, setSun] = useState(null)` with `ref={setSun}`, then `{sun && <GodRays sun={sun} />}`. |
| `SSAO` logs "Please enable the NormalPass" and does nothing | Add `enableNormalPass` to `<EffectComposer>` — or switch to `<N8AO>`, which needs no normal pass. |
| SMAA/FXAA added but GPU cost jumped with no visual gain | You're still paying for MSAA. Set `multisampling={0}` on the composer when using an AA effect. |
| Outline never shows, or flickers | Set `autoClear={false}` on the composer, and make sure `<Selection>` wraps both the composer and the `<Select enabled>` content. |
| Effect animation via state props stutters or resets the effect | Wrapped-effect props feed the constructor — every change reconstructs it. Mutate via ref in `useFrame` (`bloomRef.current.intensity = …`). |
| `setState` in `useFrame` to drive an effect parameter | Never setState in the loop. Refs into the effect instance. |
| `target={meshRef}` on `<DepthOfField>` does nothing | v3's `target` is a world-space point (`[x, y, z]`), not an object ref (that was a v8-era idiom). Use `<Autofocus>` to track objects or the pointer. |
| Custom `Effect` constructed in render without memoization | New instance every render = recompile churn. Build in `useMemo`, or define the component once with `wrapEffect(MyEffect)`. |
| `EffectComposer` imported from `three/addons` inside Canvas | That's the imperative three.js pipeline; its passes don't work here. Import from `@react-three/postprocessing`. |
| Multiple `<EffectComposer>`s used to "organize" effects | Each composer is a full render + chain. Use one composer and order its children. |

## See Also

- [shaders-and-custom-materials.md](./shaders-and-custom-materials.md) — object-level GLSL (`shaderMaterial`, `onBeforeCompile`) vs the screen-level effects here.
- [performance.md](./performance.md) — frameloop demand mode, dpr scaling, draw-call budgets that gate how many effects you can afford.
- [staging-and-drei.md](./staging-and-drei.md) — `Environment`, lights, and HDR sources that feed bloom and tone mapping.
- [canvas-and-project-setup.md](./canvas-and-project-setup.md) — Canvas `gl`, `flat`, and tone-mapping defaults the composer overrides.
- [../SKILL.md](../SKILL.md) — version matrix and shared setup.
- External: [react-postprocessing docs](https://react-postprocessing.docs.pmnd.rs/) · [postprocessing wiki](https://github.com/pmndrs/postprocessing/wiki) (custom effects, pass internals).
