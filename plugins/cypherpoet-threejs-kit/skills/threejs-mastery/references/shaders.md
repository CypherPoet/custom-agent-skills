# Shaders

Two paths for custom shading in modern Three.js:

- **TSL (Three.js Shading Language) — primary.** A node-based shader system imported from `three/tsl`. Composes in JavaScript, compiles to GLSL or WGSL depending on the renderer. Works under `WebGPURenderer` natively and under `WebGLRenderer` via the TSL backend. Use this for new code.
- **`ShaderMaterial` / `RawShaderMaterial` (GLSL) — legacy.** The classic raw-GLSL path. Still supported and widely deployed. Use when porting older code, targeting WebGL exclusively, or pulling in third-party shader chunks.

Pick one per surface; you can mix in the same scene but the mental model is cleaner if you don't.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

**Contents:** [TSL](#tsl-modern) · [TSL Recipes](#tsl-recipes) · [Recent TSL Additions](#recent-tsl-additions-r184r185) · [GLSL ShaderMaterial](#glsl-shadermaterial-legacy) · [GLSL Function Reference](#glsl-built-in-function-reference) · [Common Material Options](#common-material-options-shadermaterial) · [Shader Chunks](#shader-chunks) · [Debugging](#debugging) · [Performance Tips](#performance-tips) · [Common Mistakes](#common-mistakes)

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
  time, timerLocal,

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

## GLSL ShaderMaterial (Legacy)

Use when you need raw GLSL — third-party shader chunks, WebGL-only target, ports from legacy code.

> For raw WebGL pipeline mechanics and deep GLSL technique *beneath* Three.js — custom `WebGLRenderingContext` work, advanced shader patterns, framework-limit drop-downs — see the sibling **`webgl-mastery`** skill (`cypherpoet-webgl-kit` dependency).

### Minimum Viable ShaderMaterial

```javascript
const material = new THREE.ShaderMaterial({
  uniforms: {
    time:  { value: 0 },
    color: { value: new THREE.Color(0xff0000) },
  },
  vertexShader: /* glsl */`
    void main() {
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */`
    uniform vec3 color;
    void main() {
      gl_FragColor = vec4(color, 1.0);
    }
  `,
});

// Drive uniforms each frame
material.uniforms.time.value = clock.getElapsedTime();
```

### Built-in Uniforms / Attributes

`ShaderMaterial` provides these for free (`RawShaderMaterial` does not):

```glsl
uniform mat4 modelMatrix;
uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat3 normalMatrix;
uniform vec3 cameraPosition;

attribute vec3 position;
attribute vec3 normal;
attribute vec2 uv;
```

### Uniform Types

```javascript
new THREE.ShaderMaterial({
  uniforms: {
    floatValue: { value: 1.5 },
    intValue:   { value: 1 },

    vec2Value: { value: new THREE.Vector2(1, 2) },
    vec3Value: { value: new THREE.Vector3(1, 2, 3) },
    vec4Value: { value: new THREE.Vector4(1, 2, 3, 4) },

    colorValue: { value: new THREE.Color(0xff0000) },        // becomes vec3

    mat3Value: { value: new THREE.Matrix3() },
    mat4Value: { value: new THREE.Matrix4() },

    textureValue:     { value: texture },                     // sampler2D
    cubeTextureValue: { value: cubeTexture },                 // samplerCube

    floatArray: { value: [1.0, 2.0, 3.0] },                   // float[3]
    vec3Array:  { value: [new THREE.Vector3(1, 0, 0),
                          new THREE.Vector3(0, 1, 0)] },      // vec3[2]
  },
});
```

### RawShaderMaterial

No built-ins — provide every matrix and attribute yourself:

```javascript
new THREE.RawShaderMaterial({
  uniforms: {
    projectionMatrix: { value: camera.projectionMatrix },
    modelViewMatrix:  { value: new THREE.Matrix4() },
  },
  vertexShader: /* glsl */`
    precision highp float;
    attribute vec3 position;
    uniform mat4 projectionMatrix;
    uniform mat4 modelViewMatrix;
    void main() {
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */`
    precision highp float;
    void main() {
      gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
  `,
});
```

### Varyings

Pass interpolated values from vertex to fragment:

```javascript
new THREE.ShaderMaterial({
  vertexShader: /* glsl */`
    varying vec2 vUv;
    varying vec3 vNormal;
    void main() {
      vUv = uv;
      vNormal = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */`
    varying vec2 vUv;
    varying vec3 vNormal;
    void main() {
      gl_FragColor = vec4(vNormal * 0.5 + 0.5, 1.0);
    }
  `,
});
```

### Common GLSL Recipes

**Texture sampling**

```glsl
uniform sampler2D map;
varying vec2 vUv;
void main() {
  gl_FragColor = texture2D(map, vUv);
  // GLSL 3 (glslVersion: THREE.GLSL3): texture(map, vUv);
}
```

**Vertex displacement**

```glsl
uniform float time;
void main() {
  vec3 pos = position;
  pos.z += sin(pos.x * 5.0 + time) * 0.5;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
```

**Fresnel**

```glsl
varying vec3 vNormal;
varying vec3 vWorldPosition;
// vertex:
//   vNormal = normalize(normalMatrix * normal);
//   vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
void main() {
  vec3 viewDir = normalize(cameraPosition - vWorldPosition);
  float fresnel = pow(1.0 - dot(viewDir, vNormal), 3.0);
  gl_FragColor = vec4(mix(vec3(0.0, 0.0, 0.5), vec3(0.5, 0.8, 1.0), fresnel), 1.0);
}
```

**Rim lighting**

```glsl
varying vec3 vNormal;
varying vec3 vViewPosition;
void main() {
  vec3 viewDir = normalize(-vViewPosition);
  float rim = 1.0 - max(0.0, dot(viewDir, vNormal));
  rim = pow(rim, 4.0);
  gl_FragColor = vec4(vec3(0.2, 0.2, 0.8) + vec3(1.0, 0.5, 0.0) * rim, 1.0);
}
```

**Value noise (no texture)**

```glsl
float random(vec2 st) {
  return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453);
}
float noise(vec2 st) {
  vec2 i = floor(st);
  vec2 f = fract(st);
  float a = random(i);
  float b = random(i + vec2(1.0, 0.0));
  float c = random(i + vec2(0.0, 1.0));
  float d = random(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}
```

**Dissolve**

```glsl
uniform float progress;
uniform sampler2D noiseMap;
varying vec2 vUv;
void main() {
  float n = texture2D(noiseMap, vUv).r;
  if (n < progress) discard;

  float edge = smoothstep(progress, progress + 0.1, n);
  vec3 edgeColor = vec3(1.0, 0.5, 0.0);
  vec3 baseColor = vec3(0.5);
  gl_FragColor = vec4(mix(edgeColor, baseColor, edge), 1.0);
}
```

### Extending Built-ins (`onBeforeCompile`)

Modify the shader source Three.js generates for a standard material:

```javascript
const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 });

material.onBeforeCompile = (shader) => {
  shader.uniforms.time = { value: 0 };
  material.userData.shader = shader;

  shader.vertexShader = "uniform float time;\n" + shader.vertexShader;
  shader.vertexShader = shader.vertexShader.replace(
    "#include <begin_vertex>",
    `
      #include <begin_vertex>
      transformed.y += sin(position.x * 10.0 + time) * 0.1;
    `
  );
};

function tick() {
  if (material.userData.shader) {
    material.userData.shader.uniforms.time.value = clock.getElapsedTime();
  }
}
```

Common injection points:

| Stage | Chunk | When |
|-------|-------|------|
| Vertex | `#include <begin_vertex>` | Just after `transformed = position` |
| Vertex | `#include <project_vertex>` | Just after `gl_Position` |
| Vertex | `#include <beginnormal_vertex>` | Normal calc start |
| Fragment | `#include <color_fragment>` | After diffuse color |
| Fragment | `#include <output_fragment>` | Final output |
| Fragment | `#include <fog_fragment>` | After fog |

Prefer `MeshStandardNodeMaterial` + TSL `colorNode`/`outputNode` for new code — same idea, no string munging.

## GLSL Built-in Function Reference

### Math

```glsl
abs(x), sign(x), floor(x), ceil(x), fract(x)
mod(x, y), min(x, y), max(x, y), clamp(x, min, max)
mix(a, b, t), step(edge, x), smoothstep(edge0, edge1, x)

sin(x), cos(x), tan(x), asin(x), acos(x), atan(y, x)
radians(deg), degrees(rad)

pow(x, y), exp(x), log(x), exp2(x), log2(x)
sqrt(x), inversesqrt(x)
```

### Vector

```glsl
length(v), distance(p0, p1), dot(x, y), cross(x, y)
normalize(v), reflect(I, N), refract(I, N, eta)

// Component-wise comparisons (return bvec)
lessThan, lessThanEqual, greaterThan, greaterThanEqual, equal, notEqual
any(bvec), all(bvec)
```

### Texture

```glsl
// GLSL 1.0 (default)
texture2D(sampler2D, vec2 coord)
texture2D(sampler2D, vec2 coord, float bias)
textureCube(samplerCube, vec3 coord)

// GLSL 3.0 (glslVersion: THREE.GLSL3) — same function name regardless of sampler
texture(sampler, coord)
textureLod(sampler, coord, lod)
textureSize(sampler, lod)
```

When you set `glslVersion: THREE.GLSL3`, write `out vec4 fragColor;` and `fragColor = ...;` instead of `gl_FragColor = ...;`.

## Common Material Options (ShaderMaterial)

```javascript
new THREE.ShaderMaterial({
  uniforms: { /* ... */ },
  vertexShader:   "/* ... */",
  fragmentShader: "/* ... */",

  transparent: true,
  opacity: 1.0,
  side: THREE.DoubleSide,
  depthTest: true,
  depthWrite: true,

  blending: THREE.NormalBlending,     // AdditiveBlending, etc.

  wireframe: false,

  extensions: {
    derivatives: true,                 // fwidth, dFdx, dFdy
    fragDepth: true,                   // gl_FragDepth
    drawBuffers: true,                 // MRT
    shaderTextureLOD: true,            // texture2DLod
  },

  glslVersion: THREE.GLSL3,            // WebGL 2 features
});
```

## Shader Chunks

Three.js exposes its internal shader fragments through `ShaderChunk` — handy for depth math, packing, fog, lighting:

```javascript
import { ShaderChunk } from "three";

const fragmentShader = /* glsl */`
  ${ShaderChunk.common}
  ${ShaderChunk.packing}

  uniform sampler2D depthTexture;
  varying vec2 vUv;
  void main() {
    float depth = texture2D(depthTexture, vUv).r;
    float linearDepth = perspectiveDepthToViewZ(depth, 0.1, 1000.0);
    gl_FragColor = vec4(vec3(-linearDepth / 100.0), 1.0);
  }
`;
```

### External Shader Files

With Vite / webpack:

```javascript
import vertexShader   from "./shaders/vertex.glsl";
import fragmentShader from "./shaders/fragment.glsl";

new THREE.ShaderMaterial({ vertexShader, fragmentShader });
```

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

| Mistake | Fix |
|---------|-----|
| TSL node graph mutates but the material doesn't redraw | Assign a new node to `material.colorNode`/`positionNode`/`outputNode` and set `material.needsUpdate = true`. Don't mutate the node in place. |
| `positionLocal` reads correctly but `material.positionNode = positionLocal.x = ...` errors | TSL nodes are immutable. Build a new expression: `positionLocal.add(...)`, not assignment to a swizzle. |
| Vertex displacement via `positionNode` ignores skinning/morphing on a `SkinnedMesh` (r185+) | Inside `positionNode`, `positionLocal` doesn't carry internal vertex transforms. Base the displacement on `positionGeometry` for the pre-transform geometry vertices. |
| GLSL fragment compiles, but the value is always 0 | You forgot to declare and write the `varying` in the vertex stage. Both stages must declare it; the vertex must write it. |
| Mobile shows precision artifacts (bands, jitter) | Switch to `precision highp float;` at the top of the fragment shader; some mobile defaults to `mediump`. |
| `texture2D` is "not defined" on a GLSL 3 shader | `glslVersion: THREE.GLSL3` changes the API to `texture(sampler, uv)` and requires `out vec4 fragColor;`. Pick GLSL 1 or 3 and write to match. |
| `MeshStandardNodeMaterial` lighting looks darker than `MeshStandardMaterial` | Different defaults for environment intensity and tonemapping interaction. Set `material.envMapIntensity` explicitly and confirm `renderer.toneMapping` matches both pipelines. |
| `attribute` data isn't reaching the shader | For instancing, use `InstancedBufferAttribute` and `attribute("name", "vec3")` (TSL) / `attribute vec3 name;` (GLSL). For per-vertex non-instance, regular `BufferAttribute` is fine. |
| `onBeforeCompile` runs but the patch doesn't apply | The injection string must match Three.js's generated source verbatim. Set `material.needsUpdate = true` after assigning `onBeforeCompile`. Patches break across Three.js versions when chunks are renamed — prefer the TSL path. |

## See Also

- [materials.md](./materials.md) — `MeshStandardNodeMaterial`, `ShaderMaterial`, `onBeforeCompile` in context.
- [postprocessing.md](./postprocessing.md) — TSL passes and custom screen-space effects.
- [textures.md](./textures.md) — sampling, color space, render targets.
- [geometry.md](./geometry.md) — per-instance attributes for instanced shaders.
