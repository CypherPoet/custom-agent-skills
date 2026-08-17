# Shaders

Two paths for custom shading in modern Three.js:

- **TSL (Three.js Shading Language) — primary.** A node-based shader system imported from `three/tsl`. Composes in JavaScript, compiles to GLSL or WGSL depending on the renderer. Works under `WebGPURenderer` natively and under `WebGLRenderer` via the TSL backend. Use this for new code.
- **`ShaderMaterial` / `RawShaderMaterial` (GLSL) — legacy.** The classic raw-GLSL path, now in its own reference: **[shaders-glsl.md](./shaders-glsl.md)**. Use when porting older code, targeting WebGL exclusively, or pulling in third-party shader chunks.

Pick one per surface; you can mix in the same scene but the mental model is cleaner if you don't.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

## Table of Contents

| Section | Covers |
|---|---|
| [TSL (Modern)](#tsl-modern) | Imports, minimum materials, uniforms, varyings and attributes, function nodes, swizzling and math, and conditional flow |
| [TSL Recipes](#tsl-recipes) | Texture sampling, vertex displacement, Fresnel, rim lighting, gradients, dissolve effects, instanced TSL, extending built-in node materials, and output-node overrides |
| [Recent TSL Additions (r184–r185)](#recent-tsl-additions-r184r185) | Render-pipeline, storage, batching, texture, and shader-node APIs added in r184 and r185 |
| [WGSL Interop](#wgsl-interop) | When you need hand-written WGSL under `WebGPURenderer` — porting an existing shader |
| [GLSL (Legacy)](#glsl-legacy) | Raw-GLSL `ShaderMaterial` / `RawShaderMaterial` — the compatibility path for WebGL-only targets |
| [Debugging](#debugging) | Inspect the Compiled Shader and Visualize Intermediate Values |
| [Performance Tips](#performance-tips) | Uniform counts, branching, precision, loop bounds, and recompilation |
| [Common Mistakes](#common-mistakes) | Legacy raw-GLSL pitfalls live in shaders-glsl.md |
| [See Also](#see-also) | Related references and supporting guidance |

## TSL (Modern)

### Imports

Almost everything ships from `three/tsl`:

```javascript
import * as THREE from "three/webgpu";   // or via importmap aliasing
import {
  // Constants and constructors
  color, vec2, vec3, vec4, float,

  // Inputs
  uniform, attribute, varying,

  // Geometry / surface state
  positionLocal, positionWorld, positionView,
  normalLocal,   normalWorld,   normalView,
  uv, cameraPosition,

  // Math
  sin, cos, tan, pow, exp, log, sqrt,
  abs, sign, floor, ceil, fract, mod,
  min, max, clamp, mix, step, smoothstep,
  length, distance, dot, cross, normalize, reflect, refract,

  // Sampling
  texture, cubeTexture,

  // Time
  time, deltaTime,

  // Flow / functions
  Fn, If, Discard,
} from "three/tsl";
```

API specifics evolve across releases — when an example below doesn't compile against your version, check the current docs for the symbol's new name. The shapes (uniform/attribute/varying/`Fn`/output assignment) have been stable.

### Minimum Viable TSL Material

```javascript
import * as THREE from "three/webgpu";
import { color, positionLocal, sin, time, uniform } from "three/tsl";

const material = new THREE.MeshStandardNodeMaterial({
  roughness: 0.4,
  metalness: 0.0,
});

// Hue-ish tint over time
material.colorNode = color(0xff0066).mul(sin(time).mul(0.5).add(0.5));

// Wobble vertices
material.positionNode = positionLocal.add(
  sin(time.add(positionLocal.y.mul(3))).mul(0.1)
);

// Use exactly like any other material
scene.add(new THREE.Mesh(new THREE.SphereGeometry(1, 64, 32), material));
```

### Uniforms

```javascript
import { uniform } from "three/tsl";

const tint = uniform(new THREE.Color(0x66ccff));
material.colorNode = tint;

// Update from JS — the live `.value` is what the shader sees
tint.value.setHSL((performance.now() / 5000) % 1, 0.6, 0.5);
```

Bind once, mutate the `.value` each frame.

### Varyings and Attributes

```javascript
import { attribute, varying, positionLocal, normalWorld, uv } from "three/tsl";

// Custom per-vertex attribute (set via geometry.setAttribute("offset", ...))
const offset = attribute("offset", "vec3");
material.positionNode = positionLocal.add(offset);

// Varying — defined in vertex stage, read in fragment stage
const vNormal = varying(normalWorld);
material.colorNode = vNormal.mul(0.5).add(0.5);
```

### Function Nodes (`Fn`)

Compose reusable shader logic:

```javascript
import { Fn, If, Discard, uv, vec4 } from "three/tsl";

const stripes = Fn(() => {
  If(uv().x.lessThan(0.5), () => Discard());
  return vec4(1, 0, 0, 1);
});

material.colorNode = stripes();
```

### Swizzling and Math

Vector components and operators map to `.x`/`.y`/`.r`/etc, and operators are method calls (`.add()`, `.mul()`, `.sub()`, `.div()`):

```javascript
import { uv, vec3 } from "three/tsl";

const flippedUv = uv().yx;                     // Swap x/y
const fade = uv().y.mul(2).sub(1).abs();       // |2y - 1|
const rgb = vec3(uv().x, uv().y, 0);
```

### Conditional Flow

```javascript
import { Fn, If, uv, vec4 } from "three/tsl";

material.colorNode = Fn(() => {
  const c = vec4(0, 0, 0, 1).toVar();
  If(uv().x.greaterThan(0.5), () => {
    c.assign(vec4(1, 0, 0, 1));
  }).Else(() => {
    c.assign(vec4(0, 0, 1, 1));
  });
  return c;
})();
```

Prefer `mix` / `step` for simple cases — they parallelize better than branches.

## TSL Recipes

### Texture Sampling

```javascript
import { texture, uv, color } from "three/tsl";

material.colorNode = texture(albedoTexture, uv()).mul(color(0xffeedd));
```

### Vertex Displacement

```javascript
import { positionLocal, sin, time } from "three/tsl";

material.positionNode = positionLocal.add(
  sin(positionLocal.x.mul(5).add(time)).mul(0.1)
);
```

> **Skinned / morph meshes (r185):** the example above is correct for static geometry. When you assign `positionNode` on a `SkinnedMesh` or morph-target mesh, `positionLocal` no longer carries the internal skinning/morph transforms — base the displacement on `positionGeometry` (the pre-transform geometry vertices) instead. See the [Migration Guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide) and [animation.md](./animation.md).

### Fresnel

```javascript
import {
  Fn, positionWorld, normalWorld, cameraPosition, vec4, mix, pow
} from "three/tsl";

const fresnelShade = Fn(() => {
  const viewDir = cameraPosition.sub(positionWorld).normalize();
  const f = pow(viewDir.dot(normalWorld).oneMinus(), 3);
  return mix(vec4(0, 0, 0.5, 1), vec4(0.5, 0.8, 1, 1), f);
});

material.colorNode = fresnelShade();
```

### Rim Lighting

```javascript
import { Fn, normalView, vec4, pow } from "three/tsl";

const rim = Fn(() => {
  const r = pow(normalView.z.abs().oneMinus(), 4);
  return vec4(0.2, 0.2, 0.8, 1).add(vec4(1, 0.5, 0, 0).mul(r));
});

material.colorNode = rim();
```

### Gradients

```javascript
import { color, uv, mix, smoothstep, distance, vec2 } from "three/tsl";

const linear = mix(color(0xff6644), color(0x66ccff), uv().y);

const radial = mix(
  color(0xffffff),
  color(0x000000),
  distance(uv(), vec2(0.5, 0.5)).mul(2)
);

const smooth = mix(
  color(0xff0000),
  color(0x0000ff),
  smoothstep(0, 1, uv().y)
);

material.colorNode = smooth;
```

### Dissolve

```javascript
import {
  Fn, If, Discard, texture, uv, uniform, smoothstep, vec4, mix, color
} from "three/tsl";

const progress = uniform(0);
const noiseTex = /* DataTexture or noise image */;

const dissolve = Fn(() => {
  const n = texture(noiseTex, uv()).r;
  If(n.lessThan(progress), () => Discard());
  const edge = smoothstep(progress, progress.add(0.1), n);
  return mix(vec4(1, 0.5, 0, 1), vec4(0.5, 0.5, 0.5, 1), edge);
});

material.colorNode = dissolve();

// Drive `progress.value` each frame from 0 → 1
```

### Instanced TSL

Per-instance attributes work the same as the GLSL path; read with the `attribute` node:

```javascript
geometry.setAttribute(
  "offset",
  new THREE.InstancedBufferAttribute(offsets, 3)
);

import { attribute, positionLocal } from "three/tsl";

material.positionNode = positionLocal.add(attribute("offset", "vec3"));
```

### Extending Built-in Node Materials

Every standard material has a node variant (`MeshStandardNodeMaterial`, `MeshPhysicalNodeMaterial`, etc.). Assign to the slots you want to override; lighting and the rest stay intact.

```javascript
import { texture, uv, color, mix, uniform } from "three/tsl";

const material = new THREE.MeshStandardNodeMaterial({
  roughness: 0.4,
  metalness: 0.1,
});

const dirt = uniform(0.5);

material.colorNode = mix(
  texture(albedoTexture, uv()),
  color(0x222222),
  dirt
);
material.roughnessNode = mix(0.3, 0.95, dirt);
```

### Output Node (Bypass Lighting)

`colorNode` participates in lighting. `outputNode` writes directly to the framebuffer — useful for unlit overlays / debug visualizations:

```javascript
import { vec4 } from "three/tsl";

material.outputNode = vec4(1, 0, 1, 1);
```

## Recent TSL Additions (r184–r185)

The node API grows each release. Two recent ones worth knowing:

- **Per-frame logic in a node graph** — `OnFrameUpdate(callback)` / `OnBeforeFrameUpdate(callback)` (from `three/tsl`, r184) run a callback every frame; declare them inside an `Fn()`.
- **Texture gather** — `texture(map, uv()).gather(channel)` (r185) returns, as a `vec4`, the four texels bilinear filtering would sample for the given channel (`0`–`3`). Add `.compare(ref)` on a depth texture for the hardware compare variant.

When an example here references a node your version doesn't have, check the [release notes](https://github.com/mrdoob/three.js/releases) — the TSL surface moves fast.

## WGSL Interop

When you need hand-written WGSL under `WebGPURenderer` — porting an existing shader, or reaching for something TSL doesn't expose — wrap it in a `wgslFn` node (from `three/tsl`). There is no `wgsl` tagged-template; the API is `wgslFn(code, includes?)`, and WGSL runs only under `WebGPURenderer`.

```javascript
import { wgslFn, texture } from "three/tsl";

const desaturate = wgslFn(`
  fn desaturate( color: vec3<f32> ) -> vec3<f32> {
    let lum = vec3<f32>( 0.299, 0.587, 0.114 );
    return vec3<f32>( dot( lum, color ) );
  }
`);

// Call the node with a named-params object.
material.colorNode = desaturate({ color: texture(map) });
```

Parameter and return types use WGSL spelling; they map onto TSL types one-to-one:

| TSL | WGSL |
|-----|------|
| `float` | `f32` |
| `int` / `uint` | `i32` / `u32` |
| `vec2` / `vec3` / `vec4` | `vec2<f32>` / `vec3<f32>` / `vec4<f32>` (short forms `vec2f`/`vec3f`/`vec4f`) |
| `mat3` / `mat4` | `mat3x3<f32>` / `mat4x4<f32>` |

To reuse one WGSL function inside another, pass it in the second `includes` argument — `wgslFn(codeThatCallsHelper, [helperFn])` — so the helper's source is emitted alongside the caller.

## GLSL (Legacy)

Raw-GLSL `ShaderMaterial` / `RawShaderMaterial` — the compatibility path for WebGL-only targets, third-party shader chunks, and ports from older code. The full reference (minimum-viable setup, built-in uniforms, `RawShaderMaterial`, GLSL recipes, `onBeforeCompile`, the GLSL function reference, `ShaderChunk`) lives in **[shaders-glsl.md](./shaders-glsl.md)**.

> For raw WebGL pipeline mechanics and deep GLSL technique *beneath* Three.js — custom `WebGLRenderingContext` work, advanced shader patterns, framework-limit drop-downs — see the sibling **`webgl-mastery`** skill (`webgl-kit` dependency).

## Debugging

### Inspect the Compiled Shader

```javascript
material.onBeforeCompile = (shader) => {
  console.log("vertex:",   shader.vertexShader);
  console.log("fragment:", shader.fragmentShader);
};

// Show compile/link errors loudly
renderer.debug.checkShaderErrors = true;
```

### Visualize Intermediate Values

```glsl
// UV check
gl_FragColor = vec4(vUv, 0.0, 1.0);

// Normal check
gl_FragColor = vec4(vNormal * 0.5 + 0.5, 1.0);

// World-position check
gl_FragColor = vec4(vWorldPosition * 0.1 + 0.5, 1.0);
```

For TSL, swap in the equivalent node:

```javascript
import { uv, normalWorld, positionWorld, vec4 } from "three/tsl";

material.outputNode = vec4(uv(), 0, 1);
material.outputNode = vec4(normalWorld.mul(0.5).add(0.5), 1);
```

## Performance Tips

- **Minimize uniforms.** Each is a CPU→GPU sync. Pack related scalars into a `vec3`/`vec4`.
- **Avoid divergent branches.** Use `mix`/`step`/`smoothstep` where possible; reserve `if` for fragment kills (`discard`) or rare paths.
- **Move constants out of the shader.** Anything you can compute once on the CPU is free vs computing it per-pixel.
- **Trade compute for textures.** Lookup tables (gradients, falloffs, noise) often beat repeated math.
- **Watch overdraw.** Transparent surfaces re-shade pixels behind them.

```glsl
// instead of
if (value > 0.5) color = colorA; else color = colorB;

// prefer
color = mix(colorB, colorA, step(0.5, value));
```

## Common Mistakes

Legacy raw-GLSL pitfalls live in [shaders-glsl.md](./shaders-glsl.md#common-mistakes).

| Mistake | Fix |
|---------|-----|
| TSL node graph mutates but the material doesn't redraw | Assign a new node to `material.colorNode`/`positionNode`/`outputNode` and set `material.needsUpdate = true`. Don't mutate the node in place. |
| `positionLocal` reads correctly but `material.positionNode = positionLocal.x = ...` errors | TSL nodes are immutable. Build a new expression: `positionLocal.add(...)`, not assignment to a swizzle. |
| Vertex displacement via `positionNode` ignores skinning/morphing on a `SkinnedMesh` (r185+) | Inside `positionNode`, `positionLocal` doesn't carry internal vertex transforms. Base the displacement on `positionGeometry` for the pre-transform geometry vertices. |
| `MeshStandardNodeMaterial` lighting looks darker than `MeshStandardMaterial` | Different defaults for environment intensity and tonemapping interaction. Set `material.envMapIntensity` explicitly and confirm `renderer.toneMapping` matches both pipelines. |
| `attribute` data isn't reaching the shader | For instancing, use `InstancedBufferAttribute` and `attribute("name", "vec3")` (TSL) / `attribute vec3 name;` (GLSL). For per-vertex non-instance, regular `BufferAttribute` is fine. |

## See Also

- [shaders-glsl.md](./shaders-glsl.md) — the legacy raw-GLSL `ShaderMaterial` path.
- [materials.md](./materials.md) — `MeshStandardNodeMaterial`, `ShaderMaterial`, `onBeforeCompile` in context.
- [postprocessing.md](./postprocessing.md) — TSL passes and custom screen-space effects.
- [textures.md](./textures.md) — sampling, color space, render targets.
- [geometry.md](./geometry.md) — per-instance attributes for instanced shaders.
