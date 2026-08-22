# Shaders — GLSL ShaderMaterial (Legacy)

The classic raw-GLSL path: `ShaderMaterial` and `RawShaderMaterial`. Still fully supported and widely deployed. Reach for it when porting older code, targeting WebGL exclusively, or pulling in third-party shader chunks — otherwise prefer the modern TSL path in **[shaders.md](./shaders.md)**, which composes in JavaScript, compiles to GLSL or WGSL, and works under both renderers.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

> For raw WebGL pipeline mechanics and deep GLSL technique *beneath* Three.js — custom `WebGLRenderingContext` work, advanced shader patterns, framework-limit drop-downs — see the sibling **`webgl-mastery`** skill (`webgl-kit` dependency).

## Table of Contents

| Section | Covers |
|---|---|
| [Minimum Viable ShaderMaterial](#minimum-viable-shadermaterial) | A complete `ShaderMaterial` with uniforms plus vertex and fragment shaders |
| [Built-in Uniforms and Attributes](#built-in-uniforms-and-attributes) | Automatically supplied transform and camera uniforms plus position, normal, and UV attributes |
| [Uniform Types](#uniform-types) | JavaScript mappings for scalar, vector, color, matrix, texture, cube texture, and array uniforms |
| [RawShaderMaterial](#rawshadermaterial) | Explicit precision, attributes, and transform uniforms without Three.js shader declarations |
| [Varyings](#varyings) | Declaring, writing, interpolating, and reading vertex-to-fragment values |
| [Common GLSL Recipes](#common-glsl-recipes) | Texture sampling, animated displacement, Fresnel, rim light, value noise, and edge-colored dissolve |
| [Extending Built-ins (`onBeforeCompile`)](#extending-built-ins-onbeforecompile) | Injected uniforms and source replacements at common vertex and fragment chunks, with node materials preferred for new work |
| [GLSL Built-in Function Reference](#glsl-built-in-function-reference) | Scalar math, vector operations, comparisons, and GLSL-version-specific texture access and fragment output |
| [Common Material Options (ShaderMaterial)](#common-material-options-shadermaterial) | Transparency, sidedness, depth, blending, extensions, wireframe, and GLSL version options |
| [Shader Chunks](#shader-chunks) | Reusing internal depth, packing, fog, and lighting fragments and importing external shader source files |
| [Common Mistakes](#common-mistakes) | Unwritten varyings, mobile precision artifacts, mixed GLSL-version syntax, and brittle source-patch matching |
| [See Also](#see-also) | Related references and supporting guidance |

## Minimum Viable ShaderMaterial

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
material.uniforms.time.value = timer.getElapsed();
```

## Built-in Uniforms and Attributes

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

## Uniform Types

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

## RawShaderMaterial

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

## Varyings

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

## Common GLSL Recipes

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

## Extending Built-ins (`onBeforeCompile`)

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
  timer.update();
  if (material.userData.shader) {
    material.userData.shader.uniforms.time.value = timer.getElapsed();
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

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| GLSL fragment compiles, but the value is always 0 | You forgot to declare and write the `varying` in the vertex stage. Both stages must declare it; the vertex must write it. |
| Mobile shows precision artifacts (bands, jitter) | Switch to `precision highp float;` at the top of the fragment shader; some mobile defaults to `mediump`. |
| `texture2D` is "not defined" on a GLSL 3 shader | `glslVersion: THREE.GLSL3` changes the API to `texture(sampler, uv)` and requires `out vec4 fragColor;`. Pick GLSL 1 or 3 and write to match. |
| `onBeforeCompile` runs but the patch doesn't apply | The injection string must match Three.js's generated source verbatim. Set `material.needsUpdate = true` after assigning `onBeforeCompile`. Patches break across Three.js versions when chunks are renamed — prefer the TSL path. |

## See Also

- [shaders.md](./shaders.md) — the modern TSL path (primary), plus shared shader debugging and performance tips.
- [materials.md](./materials.md) — `ShaderMaterial` and `onBeforeCompile` in material context.
- [textures.md](./textures.md) — sampling, color space, and render targets.
