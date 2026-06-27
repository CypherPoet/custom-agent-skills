# Materials

PBR, classic phong/lambert/basic, toon, point/line, and how to customize materials with TSL nodes (the modern path) or GLSL `ShaderMaterial` (the WebGL-era fallback). Most materials work on both renderers; the node-based variants (`MeshStandardNodeMaterial` etc.) are designed for `WebGPURenderer` and also compile to WebGL via the TSL backend.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

## Material Types

| Material                  | Use case                                  | Lighting           | Renderer note |
| ------------------------- | ----------------------------------------- | ------------------ | ------------- |
| MeshBasicMaterial         | Unlit, flat colors, wireframes            | No                 | Both |
| MeshLambertMaterial       | Matte surfaces, performance               | Diffuse only       | Both |
| MeshPhongMaterial         | Shiny plastic, specular highlights        | Yes                | Both |
| **MeshStandardMaterial**  | PBR, realistic — the default choice       | PBR                | Both |
| MeshPhysicalMaterial      | Advanced PBR: clearcoat, transmission, …  | PBR+               | Both |
| MeshToonMaterial          | Cel-shading / cartoon look                | Toon               | Both |
| MeshNormalMaterial        | Debug: visualize surface normals          | No                 | Both |
| MeshDepthMaterial         | Depth visualization, custom shadow output | No                 | Both |
| **MeshStandardNodeMaterial** | PBR + TSL customization (modern)        | PBR                | WebGPU primary |
| MeshBasicNodeMaterial / MeshPhysicalNodeMaterial / MeshToonNodeMaterial | TSL variants of the above | as above | WebGPU primary |
| ShaderMaterial            | Custom GLSL — legacy customization path   | Custom             | WebGL primary |
| RawShaderMaterial         | Full GLSL control, no built-ins           | Custom             | WebGL primary |

If you don't know which to pick, start with `MeshStandardMaterial` (or `MeshStandardNodeMaterial` if you plan to customize).

## MeshBasicMaterial

Unlit. Always visible regardless of lighting.

```javascript
new THREE.MeshBasicMaterial({
  color: 0xff0000,
  transparent: true,
  opacity: 0.5,
  side: THREE.DoubleSide,   // FrontSide | BackSide | DoubleSide
  wireframe: false,
  map: texture,             // Color texture
  alphaMap: alphaTexture,
  envMap: envTexture,
  reflectivity: 1,
  fog: true,
});
```

## MeshLambertMaterial

Diffuse lighting only. Fast — use when you don't need specular highlights.

```javascript
new THREE.MeshLambertMaterial({
  color: 0x00ff00,
  emissive: 0x111111,
  emissiveIntensity: 1,
  map: texture,
  emissiveMap: emissiveTexture,
  envMap: envTexture,
  reflectivity: 0.5,
});
```

## MeshPhongMaterial

Specular highlights. Useful for shiny plastic-style surfaces. PBR (`MeshStandardMaterial`) is usually a better choice for realism.

```javascript
new THREE.MeshPhongMaterial({
  color: 0x0000ff,
  specular: 0xffffff,
  shininess: 100,            // 0–1000
  emissive: 0x000000,
  flatShading: false,
  map: texture,
  specularMap: specTexture,
  normalMap: normalTexture,
  normalScale: new THREE.Vector2(1, 1),
  bumpMap: bumpTexture,
  bumpScale: 1,
  displacementMap: dispTexture,
  displacementScale: 1,
});
```

## MeshStandardMaterial (PBR)

The recommended default. Drives realistic results via roughness/metalness and an environment map.

```javascript
new THREE.MeshStandardMaterial({
  color: 0xffffff,
  roughness: 0.5,            // 0 = mirror, 1 = diffuse
  metalness: 0.0,            // 0 = dielectric, 1 = metal

  map: colorTexture,         // Albedo (set colorSpace = SRGBColorSpace!)
  roughnessMap: roughTexture,
  metalnessMap: metalTexture,
  normalMap: normalTexture,
  normalScale: new THREE.Vector2(1, 1),
  aoMap: aoTexture,          // Uses uv2 — assign geometry.attributes.uv2
  aoMapIntensity: 1,
  displacementMap: dispTexture,
  displacementScale: 0.1,
  displacementBias: 0,

  emissive: 0x000000,
  emissiveIntensity: 1,
  emissiveMap: emissiveTexture,

  envMap: envTexture,
  envMapIntensity: 1,

  flatShading: false,
  wireframe: false,
  fog: true,
});

// aoMap requires a second UV channel
geometry.setAttribute("uv2", geometry.attributes.uv);
```

## MeshPhysicalMaterial

Extends `MeshStandardMaterial` with clearcoat, transmission, sheen, iridescence, anisotropy, and explicit specular controls. Use only when you need them — they cost more.

```javascript
new THREE.MeshPhysicalMaterial({
  // ...all MeshStandardMaterial properties, plus:

  // Clearcoat (car paint, lacquer)
  clearcoat: 1.0,
  clearcoatRoughness: 0.1,
  clearcoatMap: ccTexture,
  clearcoatRoughnessMap: ccrTexture,
  clearcoatNormalMap: ccnTexture,
  clearcoatNormalScale: new THREE.Vector2(1, 1),

  // Transmission (glass, water)
  transmission: 1.0,
  transmissionMap: transTexture,
  thickness: 0.5,
  thicknessMap: thickTexture,
  attenuationDistance: 1,
  attenuationColor: new THREE.Color(0xffffff),
  ior: 1.5,                  // 1–2.333

  // Sheen (fabric, velvet)
  sheen: 1.0,
  sheenRoughness: 0.5,
  sheenColor: new THREE.Color(0xffffff),
  sheenColorMap: sheenTexture,
  sheenRoughnessMap: sheenRoughTexture,

  // Iridescence (soap bubbles, oil)
  iridescence: 1.0,
  iridescenceIOR: 1.3,
  iridescenceThicknessRange: [100, 400],
  iridescenceMap: iridTexture,
  iridescenceThicknessMap: iridThickTexture,

  // Anisotropy (brushed metal)
  anisotropy: 1.0,
  anisotropyRotation: 0,
  anisotropyMap: anisoTexture,

  // Specular controls
  specularIntensity: 1,
  specularColor: new THREE.Color(0xffffff),
  specularIntensityMap: specIntTexture,
  specularColorMap: specColorTexture,
});
```

### Glass

```javascript
new THREE.MeshPhysicalMaterial({
  color: 0xffffff,
  metalness: 0,
  roughness: 0,
  transmission: 1,
  thickness: 0.5,
  ior: 1.5,
  envMapIntensity: 1,
});
```

### Car Paint

```javascript
new THREE.MeshPhysicalMaterial({
  color: 0xff0000,
  metalness: 0.9,
  roughness: 0.5,
  clearcoat: 1,
  clearcoatRoughness: 0.1,
});
```

## MeshToonMaterial

Cel-shading. Provide a tiny stepped gradient texture for the toon ramp:

```javascript
const colors = new Uint8Array([0, 128, 255]);
const gradientMap = new THREE.DataTexture(colors, 3, 1, THREE.RedFormat);
gradientMap.minFilter = THREE.NearestFilter;
gradientMap.magFilter = THREE.NearestFilter;
gradientMap.needsUpdate = true;

new THREE.MeshToonMaterial({ color: 0x00ff00, gradientMap });
```

## Debug Materials

```javascript
new THREE.MeshNormalMaterial({ flatShading: false, wireframe: false });
new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
```

## PointsMaterial / LineBasicMaterial / LineDashedMaterial

```javascript
new THREE.PointsMaterial({
  color: 0xffffff,
  size: 0.1,
  sizeAttenuation: true,
  map: pointTexture,
  alphaMap: alphaTexture,
  transparent: true,
  alphaTest: 0.5,
  vertexColors: true,
});

new THREE.LineBasicMaterial({
  color: 0xffffff,
  linewidth: 1,              // >1 only honored on some platforms
  linecap: "round",
  linejoin: "round",
});

new THREE.LineDashedMaterial({
  color: 0xffffff,
  dashSize: 0.5,
  gapSize: 0.25,
  scale: 1,
});

const line = new THREE.Line(geometry, lineDashedMaterial);
line.computeLineDistances();   // Required for dashed lines
```

## Node Materials (TSL — Modern Customization)

When you need behavior the standard properties don't cover (custom color logic, animated displacement, procedural patterns), prefer **node materials** with TSL. They work on `WebGPURenderer` natively and compile to WebGL via the TSL backend. They replace most uses of `ShaderMaterial` for new code.

Every standard material has a node-material variant: `MeshStandardNodeMaterial`, `MeshPhysicalNodeMaterial`, `MeshBasicNodeMaterial`, `MeshLambertNodeMaterial`, `MeshPhongNodeMaterial`, `MeshToonNodeMaterial`.

### Customize the color output

```javascript
import * as THREE from "three";
import { color, texture, uv, mix, sin, time } from "three/tsl";

const material = new THREE.MeshStandardNodeMaterial({
  roughness: 0.4,
  metalness: 0.0,
});

// Hue-shift the albedo over time
material.colorNode = mix(
  color(0xff0066),
  color(0x66ccff),
  sin(time).mul(0.5).add(0.5)
);
```

### Customize vertex position

```javascript
import { positionLocal, sin, time } from "three/tsl";

material.positionNode = positionLocal.add(
  sin(time.add(positionLocal.y.mul(3))).mul(0.1)
);
```

> For a `SkinnedMesh` or morph-target mesh, base the offset on `positionGeometry` instead — under r185 `positionLocal` doesn't carry skinning/morph transforms inside `positionNode`. See [shaders.md](./shaders.md#vertex-displacement).

### Bind a uniform

```javascript
import { uniform } from "three/tsl";

const tint = uniform(new THREE.Color(0x66ccff));

material.colorNode = tint;       // Reads the live uniform value

// Update from JS each frame
tint.value.setHSL((performance.now() / 5000) % 1, 0.6, 0.5);
```

### Sample a texture in a node graph

```javascript
import { texture, uv } from "three/tsl";

material.colorNode = texture(albedoTexture, uv()).mul(color(0xffeedd));
```

### Output node (full pixel control)

`colorNode` integrates with the material's lighting model. To bypass lighting entirely and write directly to the output, use `outputNode`. Useful for emissive / unlit overlays.

```javascript
import { vec4, color } from "three/tsl";

material.outputNode = vec4(color(0xff00ff), 1.0);
```

### Function nodes

`Fn` lets you compose reusable node logic with locals and conditional flow:

```javascript
import { Fn, If, Discard, uv, vec4 } from "three/tsl";

const stripes = Fn(() => {
  If(uv().x.lessThan(0.5), () => Discard());
  return vec4(1, 0, 0, 1);
});

material.colorNode = stripes();
```

See [shaders.md](./shaders.md) for the full TSL surface — flow control, varying nodes, attribute nodes, geometry transforms, screen-space patterns.

## ShaderMaterial (GLSL — Legacy / WebGL)

`ShaderMaterial` is still supported and useful when you're targeting `WebGLRenderer` exclusively or porting older code. For new code, prefer TSL node materials above.

```javascript
const material = new THREE.ShaderMaterial({
  uniforms: {
    time:    { value: 0 },
    color:   { value: new THREE.Color(0xff0000) },
    map:     { value: texture },
  },
  vertexShader: `
    varying vec2 vUv;
    uniform float time;
    void main() {
      vUv = uv;
      vec3 pos = position;
      pos.z += sin(pos.x * 10.0 + time) * 0.1;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `,
  fragmentShader: `
    varying vec2 vUv;
    uniform vec3 color;
    uniform sampler2D map;
    void main() {
      vec4 tex = texture2D(map, vUv);  // texture() if glslVersion: THREE.GLSL3
      gl_FragColor = vec4(color * tex.rgb, 1.0);
    }
  `,
  transparent: true,
  side: THREE.DoubleSide,
});

// Drive a uniform from the render loop
material.uniforms.time.value = clock.getElapsedTime();
```

### Built-in GLSL Uniforms / Attributes

```glsl
// Provided automatically in ShaderMaterial (not RawShaderMaterial)
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

### RawShaderMaterial

Full control, no built-ins — you provide every matrix and attribute yourself:

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
    void main() { gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); }
  `,
});
```

## Patching Built-in Shaders (`onBeforeCompile`)

Pre-TSL, the way to inject custom GLSL into a standard material was `onBeforeCompile`. It still works on `WebGLRenderer`; prefer the equivalent node-material override on TSL.

```javascript
material.onBeforeCompile = (shader) => {
  shader.uniforms.time = { value: 0 };
  shader.vertexShader = shader.vertexShader.replace(
    "#include <begin_vertex>",
    `
      #include <begin_vertex>
      transformed.y += sin(time + position.x * 5.0) * 0.1;
    `
  );
  material.userData.shader = shader;
};

// In the render loop
if (material.userData.shader) {
  material.userData.shader.uniforms.time.value = clock.getElapsedTime();
}
```

## Common Material Properties

```javascript
// Visibility
material.visible = true;
material.transparent = false;
material.opacity = 1.0;
material.alphaTest = 0;            // Discard pixels with alpha below threshold

// Rendering
material.side = THREE.FrontSide;    // FrontSide | BackSide | DoubleSide
material.depthTest = true;
material.depthWrite = true;
material.colorWrite = true;

// Blending
material.blending = THREE.NormalBlending;
// NormalBlending, AdditiveBlending, SubtractiveBlending, MultiplyBlending, CustomBlending

// Polygon offset — relieve z-fighting between coplanar surfaces
material.polygonOffset = false;
material.polygonOffsetFactor = 0;
material.polygonOffsetUnits = 0;

// Misc
material.dithering = false;
material.toneMapped = true;         // Apply renderer's tonemapping?
```

## Multi-Material Meshes

Assign different materials to geometry groups:

```javascript
const geometry = new THREE.BoxGeometry(1, 1, 1);
const mesh = new THREE.Mesh(geometry, [
  new THREE.MeshBasicMaterial({ color: 0xff0000 }), // +X
  new THREE.MeshBasicMaterial({ color: 0x00ff00 }), // -X
  new THREE.MeshBasicMaterial({ color: 0x0000ff }), // +Y
  new THREE.MeshBasicMaterial({ color: 0xffff00 }), // -Y
  new THREE.MeshBasicMaterial({ color: 0xff00ff }), // +Z
  new THREE.MeshBasicMaterial({ color: 0x00ffff }), // -Z
]);

// Custom groups
geometry.clearGroups();
geometry.addGroup(0, 6, 0);         // (start, count, materialIndex)
geometry.addGroup(6, 6, 1);
```

## Environment Maps

Drive reflections / IBL on a per-material basis, or globally via `scene.environment`.

```javascript
// Cube texture
const envMap = new THREE.CubeTextureLoader().load([
  "px.jpg", "nx.jpg",
  "py.jpg", "ny.jpg",
  "pz.jpg", "nz.jpg",
]);
material.envMap = envMap;
material.envMapIntensity = 1;

// Equirectangular HDR
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
new RGBELoader().load("environment.hdr", (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;
  scene.background = texture;
});
```

For lighting-only HDR setups, see [lighting.md#environment-lighting-ibl](./lighting.md#environment-lighting-ibl).

## Cloning, Modifying, and Disposing

```javascript
const clone = material.clone();
clone.color.set(0x00ff00);

material.color.set(0xff0000);       // Most numeric mutations apply instantly

// Cases that require recompile
material.flatShading = true;
material.map = newTexture;
material.transparent = !material.transparent;
material.needsUpdate = true;        // Force shader recompile

// Always dispose when you discard a material
material.dispose();
```

## Performance Tips

- **Reuse materials across meshes.** Same material instance → engine can batch draw calls.
- **Avoid transparency when alphaTest is enough.** Transparent objects require depth sorting and disable certain optimizations.
- **Pick the cheapest material that meets the look.** Basic < Lambert < Phong < Standard < Physical.
- **Limit active lights.** Each light grows the lighting shader.
- **Pool materials** for procedurally-colored objects:

```javascript
const materialCache = new Map();
function getMaterial(color) {
  const key = color.toString(16);
  if (!materialCache.has(key)) {
    materialCache.set(key, new THREE.MeshStandardMaterial({ color }));
  }
  return materialCache.get(key);
}
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| PBR model looks washed out / overbright | Color/albedo textures need `colorSpace = THREE.SRGBColorSpace`. Normal/metalness/roughness textures stay in linear (`NoColorSpace`). See [textures.md](./textures.md). |
| Swapping `material.map` doesn't update | Set `material.needsUpdate = true` after the change. |
| `flatShading` change has no effect at runtime | Same — set `needsUpdate = true`; otherwise the compiled shader is reused. |
| `aoMap` has no effect | Provide a second UV channel: `geometry.setAttribute("uv2", geometry.attributes.uv)`. |
| Mixing `ShaderMaterial` (GLSL) with `MeshStandardNodeMaterial` (TSL) and expecting consistent behavior | They compile through different pipelines. Pick one per scene where possible; mixing is allowed but watch for tone-mapping / color-space mismatches. |
| Transmission/clearcoat have no effect on `MeshStandardMaterial` | Those properties belong to `MeshPhysicalMaterial`. |
| Memory grows over time when swapping materials | Call `oldMaterial.dispose()` before dropping the reference. |
| Custom GLSL color looks too dark or too bright vs the rest of the scene | `material.toneMapped = true` may be applying tonemapping you've already baked in (or vice versa). Toggle it explicitly. |

## See Also

- [textures.md](./textures.md) — color space and how to feed maps into materials correctly.
- [shaders.md](./shaders.md) — full TSL / GLSL reference for custom shaders.
- [lighting.md](./lighting.md) — how lights drive PBR materials; environment maps.
- [postprocessing.md](./postprocessing.md) — node-based screen-space effects.
