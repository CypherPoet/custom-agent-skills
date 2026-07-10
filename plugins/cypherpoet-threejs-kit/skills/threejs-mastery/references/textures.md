# Textures

Image, data, canvas, video, and HDR textures; color space; filtering; render targets; UV mapping; and the texture maps a PBR material expects. Textures are renderer-agnostic — the same code runs under `WebGPURenderer` and `WebGLRenderer`.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

**Contents:** [Loading](#loading) · [Color Space](#color-space--the-1-gotcha) · [Wrapping & Repeat](#wrapping-repeat-offset-rotation) · [Filtering & Mipmaps](#filtering-and-mipmaps) · [Texture Sources](#texture-sources) · [Cube & HDR Environments](#cube-textures-and-hdr-environments) · [Render Targets](#render-targets) · [CubeCamera](#cubecamera--dynamic-environment-maps) · [UV Mapping](#uv-mapping) · [Texture Atlases](#texture-atlases) · [PBR Texture Set](#pbr-texture-set) · [Procedural Textures](#procedural-textures) · [Memory Management](#memory-management) · [Performance Tips](#performance-tips) · [Common Mistakes](#common-mistakes)

## Loading

### TextureLoader

```javascript
const loader = new THREE.TextureLoader();

// Callbacks
loader.load(
  "texture.jpg",
  (texture) => { /* loaded */ },
  (progress) => { /* progress */ },
  (error)    => { /* error */ }
);

// Implicit async — `texture` is returned immediately, fills in once loaded
const texture = loader.load("texture.jpg");
material.map = texture;
```

### Promise Wrapper

```javascript
function loadTexture(url) {
  return new Promise((resolve, reject) => {
    new THREE.TextureLoader().load(url, resolve, undefined, reject);
  });
}

const [colorMap, normalMap, roughnessMap] = await Promise.all([
  loadTexture("color.jpg"),
  loadTexture("normal.jpg"),
  loadTexture("roughness.jpg"),
]);
```

## Color Space — the #1 Gotcha

Color/albedo textures must be tagged `SRGBColorSpace`. Data textures (normal, roughness, metalness, AO, displacement) stay in linear:

```javascript
// Color / albedo / emissive — sRGB
colorTexture.colorSpace = THREE.SRGBColorSpace;
emissiveTexture.colorSpace = THREE.SRGBColorSpace;

// Data — leave at the default (NoColorSpace / linear)
// normalTexture, roughnessTexture, metalnessTexture, aoTexture, displacementMap
```

`GLTFLoader` sets this correctly on its own outputs. `TextureLoader` does not — you set it yourself.

## Wrapping, Repeat, Offset, Rotation

```javascript
texture.wrapS = THREE.RepeatWrapping;
texture.wrapT = THREE.RepeatWrapping;
// ClampToEdgeWrapping (default), RepeatWrapping, MirroredRepeatWrapping

texture.repeat.set(4, 4);
texture.offset.set(0.5, 0.5);

texture.rotation = Math.PI / 4;
texture.center.set(0.5, 0.5);       // Rotation pivot
```

## Filtering and Mipmaps

```javascript
// Minification — texture larger than its screen footprint
texture.minFilter = THREE.LinearMipmapLinearFilter;   // Default — trilinear
texture.minFilter = THREE.LinearFilter;               // No mipmaps
texture.minFilter = THREE.NearestFilter;              // Pixelated

// Magnification — texture smaller than its screen footprint
texture.magFilter = THREE.LinearFilter;               // Smooth (default)
texture.magFilter = THREE.NearestFilter;              // Pixelated (retro)

// Anisotropic — sharpens textures at grazing angles
texture.anisotropy = renderer.capabilities.getMaxAnisotropy();

// Mipmap generation (default true; disable for non-power-of-2 and data textures)
texture.generateMipmaps = true;
```

## Texture Sources

### Image

```javascript
const texture = new THREE.Texture(image);
texture.needsUpdate = true;
```

### DataTexture

```javascript
const size = 256;
const data = new Uint8Array(size * size * 4);
for (let i = 0; i < size; i++) {
  for (let j = 0; j < size; j++) {
    const idx = (i * size + j) * 4;
    data[idx]     = i;
    data[idx + 1] = j;
    data[idx + 2] = 128;
    data[idx + 3] = 255;
  }
}
const texture = new THREE.DataTexture(data, size, size);
texture.needsUpdate = true;
```

### CanvasTexture

```javascript
const canvas = document.createElement("canvas");
canvas.width = canvas.height = 256;
const ctx = canvas.getContext("2d");
ctx.fillStyle = "red";  ctx.fillRect(0, 0, 256, 256);
ctx.fillStyle = "white"; ctx.font = "48px Arial";
ctx.fillText("Hello", 50, 150);

const texture = new THREE.CanvasTexture(canvas);
// On subsequent canvas redraws:
texture.needsUpdate = true;
```

### VideoTexture

```javascript
const video = document.createElement("video");
video.src = "video.mp4";
video.loop = true;
video.muted = true;
video.play();

const texture = new THREE.VideoTexture(video);
texture.colorSpace = THREE.SRGBColorSpace;
// No needsUpdate — VideoTexture auto-updates each frame
```

### Compressed Textures (KTX2 / Basis)

KTX2 with Basis transcoding is the recommended on-disk format for web — much smaller than PNG/JPG, and the GPU keeps the compressed form in memory:

```javascript
import { KTX2Loader } from "three/addons/loaders/KTX2Loader.js";

const ktx2Loader = new KTX2Loader();
ktx2Loader.setTranscoderPath("path/to/basis/");
ktx2Loader.detectSupport(renderer);

ktx2Loader.load("texture.ktx2", (texture) => {
  material.map = texture;
});
```

## Cube Textures and HDR Environments

### CubeTextureLoader

```javascript
const cubeTexture = new THREE.CubeTextureLoader().load([
  "px.jpg", "nx.jpg",   // +X, -X
  "py.jpg", "ny.jpg",   // +Y, -Y
  "pz.jpg", "nz.jpg",   // +Z, -Z
]);

scene.background  = cubeTexture;
scene.environment = cubeTexture;
material.envMap   = cubeTexture;
```

### Equirectangular HDR → Filtered Environment

```javascript
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";

const pmremGenerator = new THREE.PMREMGenerator(renderer);
pmremGenerator.compileEquirectangularShader();

new RGBELoader().load("environment.hdr", (texture) => {
  const envMap = pmremGenerator.fromEquirectangular(texture).texture;
  scene.environment = envMap;
  scene.background  = envMap;

  texture.dispose();
  pmremGenerator.dispose();
});
```

### RGBELoader (.hdr)

```javascript
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";

new RGBELoader().load("environment.hdr", (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;
  scene.background  = texture;
});
```

### EXRLoader (.exr)

```javascript
import { EXRLoader } from "three/addons/loaders/EXRLoader.js";

new EXRLoader().load("environment.exr", (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;
});
```

### Scene Background Tuning

```javascript
scene.background = texture;
scene.backgroundBlurriness = 0.5;       // 0–1
scene.backgroundIntensity  = 1.0;
scene.backgroundRotation.y = Math.PI;   // Spin the env around Y
```

## Render Targets

Render the scene (or a custom pass) into a texture. Use for reflections, dynamic shadows, screenshots, and post-processing.

```javascript
const renderTarget = new THREE.WebGLRenderTarget(512, 512, {
  minFilter: THREE.LinearFilter,
  magFilter: THREE.LinearFilter,
  format: THREE.RGBAFormat,
});

renderer.setRenderTarget(renderTarget);
renderer.render(scene, camera);
renderer.setRenderTarget(null);          // Back to the canvas

material.map = renderTarget.texture;
```

### Depth Texture

```javascript
const renderTarget = new THREE.WebGLRenderTarget(512, 512);
renderTarget.depthTexture = new THREE.DepthTexture(512, 512, THREE.UnsignedShortType);
const depth = renderTarget.depthTexture;
```

### Multisample (MSAA)

```javascript
new THREE.WebGLRenderTarget(512, 512, { samples: 4 });
```

> Under `WebGPURenderer`, the equivalent types are `WebGPURenderTarget` / `WebGPUStorageTexture`; APIs are similar but check current docs when you need them.

## CubeCamera — Dynamic Environment Maps

```javascript
const cubeRenderTarget = new THREE.WebGLCubeRenderTarget(256, {
  generateMipmaps: true,
  minFilter: THREE.LinearMipmapLinearFilter,
});

const cubeCamera = new THREE.CubeCamera(0.1, 1000, cubeRenderTarget);
scene.add(cubeCamera);

reflectiveMaterial.envMap = cubeRenderTarget.texture;

function animate() {
  reflectiveObject.visible = false;       // Avoid feedback
  cubeCamera.position.copy(reflectiveObject.position);
  cubeCamera.update(renderer, scene);
  reflectiveObject.visible = true;
}
```

Cube-camera updates are expensive — every frame is six camera renders. Throttle, render at a lower resolution, or update only on motion.

## UV Mapping

### Reading and Writing UVs

```javascript
const uvs = geometry.attributes.uv;

const u = uvs.getX(vertexIndex);
const v = uvs.getY(vertexIndex);

uvs.setXY(vertexIndex, newU, newV);
uvs.needsUpdate = true;
```

### Second UV Channel

`aoMap` and `lightMap` sample whichever UV set the texture's `channel` selects: `0`
(the default) reads the primary `uv`, `1` reads `uv1`. (Before r151 they were hardwired
to a second attribute named `uv2`, which is now `uv1`.)

```javascript
// Reuse the primary UVs: nothing to do — channel 0 (the default) already reads `uv`.

// Use a distinct second set: author `uv1`, then point the maps at it.
const uv1 = new Float32Array(vertexCount * 2);
// ...fill
geometry.setAttribute("uv1", new THREE.BufferAttribute(uv1, 2));
material.aoMap.channel = 1;
material.lightMap.channel = 1;
```

### UV Transform in a Shader

GLSL `ShaderMaterial`:

```javascript
new THREE.ShaderMaterial({
  uniforms: {
    map: { value: texture },
    uvOffset: { value: new THREE.Vector2(0, 0) },
    uvScale:  { value: new THREE.Vector2(1, 1) },
  },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    uniform vec2 uvOffset;
    uniform vec2 uvScale;
    void main() {
      vUv = uv * uvScale + uvOffset;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */`
    varying vec2 vUv;
    uniform sampler2D map;
    void main() { gl_FragColor = texture2D(map, vUv); }
  `,
});
```

TSL equivalent — see [shaders.md](./shaders.md):

```javascript
import { texture, uv, uniform } from "three/tsl";

const uvOffset = uniform(new THREE.Vector2(0, 0));
const uvScale  = uniform(new THREE.Vector2(1, 1));

material.colorNode = texture(map, uv().mul(uvScale).add(uvOffset));
```

## Texture Atlases

```javascript
const atlas = loader.load("atlas.png");
atlas.wrapS = atlas.wrapT = THREE.ClampToEdgeWrapping;

function selectSprite(row, col, gridSize = 2) {
  atlas.offset.set(col / gridSize, 1 - (row + 1) / gridSize);
  atlas.repeat.set(1 / gridSize, 1 / gridSize);
}

selectSprite(0, 0);
```

## PBR Texture Set

```javascript
const material = new THREE.MeshStandardMaterial({
  map: colorTexture,                   // sRGB
  normalMap: normalTexture,            // Linear
  normalScale: new THREE.Vector2(1, 1),

  roughnessMap: roughnessTexture,      // Linear
  roughness: 1,

  metalnessMap: metalnessTexture,      // Linear
  metalness: 1,

  aoMap: aoTexture,                    // Linear; samples uv (channel 0) by default
  aoMapIntensity: 1,

  emissiveMap: emissiveTexture,        // sRGB
  emissive: 0xffffff,
  emissiveIntensity: 1,

  displacementMap: displacementTexture, // Linear
  displacementScale: 0.1,
  displacementBias: 0,

  alphaMap: alphaTexture,              // Linear
  transparent: true,
});

// aoMap reads the primary `uv` by default. For a separate AO/lightmap UV layout,
// author a `uv1` attribute and set `material.aoMap.channel = 1` (`uv1` was `uv2` before r151).

// Albedo and emissive maps must be sRGB
colorTexture.colorSpace    = THREE.SRGBColorSpace;
emissiveTexture.colorSpace = THREE.SRGBColorSpace;
```

### Normal Map Types

```javascript
material.normalMapType = THREE.TangentSpaceNormalMap;   // OpenGL/default
material.normalMapType = THREE.ObjectSpaceNormalMap;
```

## Procedural Textures

### Noise

```javascript
function generateNoiseTexture(size = 256) {
  const data = new Uint8Array(size * size * 4);
  for (let i = 0; i < size * size; i++) {
    const v = Math.random() * 255;
    data[i * 4]     = v;
    data[i * 4 + 1] = v;
    data[i * 4 + 2] = v;
    data[i * 4 + 3] = 255;
  }
  const texture = new THREE.DataTexture(data, size, size);
  texture.needsUpdate = true;
  return texture;
}
```

### Gradient

```javascript
function generateGradientTexture(color1, color2, size = 256) {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = 1;
  const ctx = canvas.getContext("2d");

  const gradient = ctx.createLinearGradient(0, 0, size, 0);
  gradient.addColorStop(0, color1);
  gradient.addColorStop(1, color2);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, 1);

  return new THREE.CanvasTexture(canvas);
}
```

## Memory Management

```javascript
texture.dispose();

function disposeMaterial(material) {
  const maps = [
    "map", "normalMap", "roughnessMap", "metalnessMap", "aoMap",
    "emissiveMap", "displacementMap", "alphaMap", "envMap",
    "lightMap", "bumpMap", "specularMap",
  ];
  maps.forEach((m) => material[m]?.dispose());
  material.dispose();
}
```

### Texture Pool

```javascript
class TexturePool {
  constructor() {
    this.textures = new Map();
    this.loader = new THREE.TextureLoader();
  }
  async get(url) {
    if (this.textures.has(url)) return this.textures.get(url);
    const t = await new Promise((res, rej) =>
      this.loader.load(url, res, undefined, rej));
    this.textures.set(url, t);
    return t;
  }
  dispose(url) {
    this.textures.get(url)?.dispose();
    this.textures.delete(url);
  }
  disposeAll() {
    this.textures.forEach((t) => t.dispose());
    this.textures.clear();
  }
}
```

## Performance Tips

- **Power-of-two dimensions** (256/512/1024/2048) play nicely with mipmaps and old GPUs.
- **Compress with KTX2/Basis** for delivery — smaller download *and* smaller GPU footprint.
- **Atlas small textures** to reduce binds and improve batching.
- **Anisotropy is cheap but bounded** — `renderer.capabilities.getMaxAnisotropy()` returns the device limit.
- **Reuse textures.** Two meshes with the same `material.map` instance share GPU memory and batch better.
- **Watch memory**: `renderer.info.memory.textures` reports live count.

```javascript
const isMobile = /iPhone|iPad|Android/i.test(navigator.userAgent);
const targetSize = isMobile ? 1024 : 2048;
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| GLB looks washed out / overbright vs the reference | Albedo/`map` and `emissiveMap` need `colorSpace = THREE.SRGBColorSpace`. Data textures must NOT — leave them at default. |
| Normal map looks fine but lighting is off | Flip `normalMap.flipY` (`false` for KTX2/normal maps from many tools) and/or set `material.normalMapType = THREE.TangentSpaceNormalMap`. |
| `aoMap` has no visible effect | It samples channel 0 (the primary `uv`) by default. For a separate AO UV layout, author a `uv1` attribute and set `material.aoMap.channel = 1` (the second-UV attribute was `uv2` before r151). |
| Mipmaps look smeary on a data texture | Disable them: `generateMipmaps = false; minFilter = LinearFilter;` (and set `magFilter = LinearFilter`). |
| Canvas drawing doesn't update on the mesh | Set `texture.needsUpdate = true` after redrawing. |
| Memory grows when textures change | Call `oldTexture.dispose()` before assigning the new texture; same for render targets when resizing. |
| HDR/`RGBE`/`EXR` environment loaded but reflections are noisy | Run through `PMREMGenerator.fromEquirectangular(texture)` before assigning to `scene.environment`. |
| Anisotropy isn't doing anything | Reassign after change: some setups require `texture.anisotropy = N` *before* the first upload; for runtime change, set `needsUpdate = true`. |

## See Also

- [materials.md](./materials.md) — how each map slot is interpreted.
- [loaders.md](./loaders.md) — texture loaders, HDR, compressed formats, and how loaders set up color space for you.
- [shaders.md](./shaders.md) — sampling textures in TSL or GLSL.
