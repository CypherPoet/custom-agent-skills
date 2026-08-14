# Platform Setup: Web (filament.js / WebAssembly)

> Source: Filament web tutorials (triangle/redball/suzanne), Filament v1.75.0
> Last synced: 2026-08-14

Filament runs in the browser as a WebAssembly module (`filament.js`) targeting **WebGL 2.0**. The
JS API is a thin binding over the C++ API: same objects (`Engine`, `Scene`, `View`, `Renderer`,
`Camera`), same Builder pattern, same Entity-Component System (entities + `TransformManager` /
`RenderableManager` / `LightManager` components). Method names differ only where JS conventions
demand it (e.g. `createIblFromKtx1`, `setColor3Parameter`). All API names below are copied verbatim
from the tutorials — do not substitute guessed names.

## Table of Contents

| Section | Covers |
|---|---|
| [Page Skeleton (HTML)](#page-skeleton-html) | A minimal, mobile-friendly page with a full-screen canvas |
| [Bootstrapping: `Filament.init` and Engine Creation](#bootstrapping-filamentinit-and-engine-creation) | `Filament.init()` takes two arguments: a list of asset URLs and a callback |
| [WebGL2 / WebGPU Backend](#webgl2--webgpu-backend) | Default backend is WebGL 2.0 — no `options` needed |
| [Serving Over HTTP (CORS / MIME)](#serving-over-http-cors--mime) | Because of CORS restrictions, the app cannot fetch material packages / textures from the local filesystem (`file://`) |
| [Core Object Graph](#core-object-graph) | The standard wiring, lifted from the constructors |
| [Entities, Components, Managers](#entities-components-managers) | Filament uses an Entity-Component System |
| [The Builder Pattern in JS](#the-builder-pattern-in-js) | Builders mirror the C++ API: chain configuration calls, end with `.build(engine[, entity])` |
| [Vertex & Index Buffers](#vertex--index-buffers) | Enums are nested types exposed with a `$` separator (`Filament.VertexBuffer$AttributeType`, `Filament.IndexBuffer$IndexType`) |
| [Materials & Material Instances](#materials--material-instances) | A material package (`.filamat`) is a binary blob (shaders + metadata) produced by `matc` |
| [Lighting (Directional / Sun / IBL)](#lighting-directional--sun--ibl) | Lights are entities with a `LightManager` component |
| [Skybox & IBL from KTX](#skybox--ibl-from-ktx) | The high-level helpers are the easy path; the low-level path is shown for completeness |
| [Textures (KTX2, Compressed, Async)](#textures-ktx2-compressed-async) | `.ktx2` textures are loaded with `engine.createTextureFromKtx2(url, options)` |
| [Meshes: filamesh](#meshes-filamesh) | Filament has no general asset-loading system, but ships a simple binary mesh format, `.filamesh` (produced by the `filamesh` CLI) |
| [The Render & Resize Loop](#the-render--resize-loop) | Drive frames with `requestAnimationFrame` |
| [Resize / DPR Handling](#resize--dpr-handling) | The resize handler scales the drawing buffer by `window.devicePixelRatio` for high-DPI displays |
| [Asset-Production Toolchain (matc / cmgen / filamesh / mipgen)](#asset-production-toolchain-matc--cmgen--filamesh--mipgen) | The CLI tools live in the Filament release for your development machine (not the web archive) |
| [Asset Type Reference](#asset-type-reference) | Asset types that must be initialized before creating matching Filament resources |
| [Gotchas](#gotchas) | `Filament.IndexBuffer$IndexType`, `Filament.RenderableManager$PrimitiveType` |

---

## Page Skeleton (HTML)

A minimal, mobile-friendly page with a full-screen canvas. `filament.js` must load before your app
script.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Filament Tutorial</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,user-scalable=no,initial-scale=1">
    <style>
        body { margin: 0; overflow: hidden; }
        canvas { touch-action: none; width: 100%; height: 100%; }
    </style>
</head>
<body>
    <canvas></canvas>
    <script src="filament.js"></script>
    <script src="//unpkg.com/gl-matrix@2.8.1"></script>
    <script src="triangle.js"></script>
</body>
</html>
```

The page loads three scripts:

- **`filament.js`** — downloads assets and compiles the Filament WASM module; also contains
  high-level utilities (e.g. simplified KTX texture loading).
- **`gl-matrix-min.js`** (`gl-matrix@2.8.1`) — small vector/matrix math library used for
  transforms and camera math (`mat4.fromRotation`, `vec3.rotateY`, etc.).
- **your app script** (`triangle.js`, `redball.js`, `suzanne.js`) — your code.

The suzanne demo adds one more script for trackball drag rotation:

```html
<script src="//unpkg.com/gltumble"></script>
```

> The published Filament module is distributed on npm as `filament` — match the version in your
> `unpkg.com/filament@x.x.x` script URL to the CLI tools (`matc`, `cmgen`, etc.) you download from
> the Filament release, so the material-package format versions agree.

---

## Bootstrapping: `Filament.init` and Engine Creation

`Filament.init()` takes two arguments: **a list of asset URLs** and **a callback**. The callback
fires only after all listed assets finish downloading *and* the WASM module is ready. Assets are
fetched up front so that synchronous engine calls (e.g. `engine.createMaterial(url)`,
`engine.createIblFromKtx1(url)`) can read them out of the in-memory cache without further I/O.

```js
Filament.init(['triangle.filamat'], () => { window.app = new App() });
```

Typical structure — list the assets the constructor needs immediately, build the app inside the
callback:

```js
const initFilament = (backend) => () => {
  Filament.init([ filamat_url, ibl_url, sky_url ], () => {
    // Create some global aliases to enums for convenience.
    window.VertexAttribute = Filament.VertexAttribute;
    window.AttributeType = Filament.VertexBuffer$AttributeType;
    window.PrimitiveType = Filament.RenderableManager$PrimitiveType;
    window.IndexType = Filament.IndexBuffer$IndexType;
    window.Fov = Filament.Camera$Fov;
    window.LightType = Filament.LightManager$Type;

    const canvas = document.getElementsByTagName('canvas')[0];
    window.app = new App(canvas, {});
  });
};
initFilament()();
```

Create the engine by handing it the canvas DOM object. The engine needs the canvas to create its
WebGL 2.0 context in the constructor:

```js
this.canvas = document.getElementsByTagName('canvas')[0];
const engine = this.engine = Filament.Engine.create(this.canvas);
```

`Filament.Engine.create(canvas, options)` accepts an optional `options` object (used to select a
backend — see below).

After init, downloaded asset bytes are also reachable directly via `Filament.assets[url]` (used in
the low-level KTX path, wrapped with `Filament.Buffer(...)`).

---

## WebGL2 / WebGPU Backend

Default backend is **WebGL 2.0** — no `options` needed. The tutorials show an optional WebGPU path
gated on a query string. WebGPU requires an extra async init (`Filament.initWebGPU()`) before
`Filament.init`:

```js
if (location.search === '?backend=webgpu') {
    Filament.initWebGPU().then(() => {
        Filament.init(['triangle.filamat'], () => {
            window.app = new App({backend: Filament.Backend ? Filament.Backend.WEBGPU : 4});
        });
    });
} else {
    Filament.init(['triangle.filamat'], () => { window.app = new App() });
}
```

Pass the backend through the engine options object: `{backend: Filament.Backend.WEBGPU}`. With no
options, you get WebGL2.

---

## Serving Over HTTP (CORS / MIME)

Because of CORS restrictions, the app cannot fetch material packages / textures from the local
filesystem (`file://`). Serve over HTTP:

```bash
python3 -m http.server     # Python 3
python -m SimpleHTTPServer # Python 2.7
npx http-server -p 8000    # nodejs
```

Then open `http://localhost:8000`. **Do not use Python's simple server in production** — it does
not serve WebAssembly files with the correct MIME type. (`npx http-server` and proper production
servers set `application/wasm`.)

---

## Core Object Graph

The standard wiring, lifted from the constructors. Same shape across all three tutorials:

```js
this.swapChain = engine.createSwapChain();
this.renderer  = engine.createRenderer();
this.camera    = engine.createCamera(Filament.EntityManager.get().create());
this.view      = engine.createView();
this.view.setCamera(this.camera);
this.view.setScene(this.scene);
```

- `engine.createScene()` — flat container of entities.
- `engine.createSwapChain()` — render target tied to the canvas.
- `engine.createRenderer()` — drives a frame onto a (swapChain, view) pair.
- `engine.createCamera(entity)` — camera is attached to an **entity** (note the `EntityManager`
  call inside).
- `engine.createView()` — couples a camera + scene + viewport; the unit the renderer draws.

Clear color is set on the renderer:

```js
this.renderer.setClearOptions({clearColor: [0.0, 0.1, 0.2, 1.0], clear: true});
```

---

## Entities, Components, Managers

Filament uses an Entity-Component System. Create a bare entity, then attach components (renderable,
light, transform) via the corresponding manager's `Builder`:

```js
this.triangle = Filament.EntityManager.get().create();
this.scene.addEntity(this.triangle);
```

A fresh entity has no components — it becomes a *renderable* once `RenderableManager.Builder(...)
.build(engine, entity)` runs against it. The three managers seen in the tutorials:

- `Filament.EntityManager.get().create()` — mints entities.
- `engine.getTransformManager()` — per-entity transforms (read/write each frame).
- `Filament.RenderableManager.Builder(n)` — attaches draw-call geometry to an entity.
- `Filament.LightManager.Builder(type)` — attaches a light component to an entity.

Transform access per frame (note `inst.delete()` to free the temporary instance handle):

```js
const tcm  = this.engine.getTransformManager();
const inst = tcm.getInstance(this.triangle);
tcm.setTransform(inst, transform);   // transform is a 4x4 (gl-matrix mat4 / array)
inst.delete();
```

---

## The Builder Pattern in JS

Builders mirror the C++ API: chain configuration calls, end with `.build(engine[, entity])`. Used
in lieu of long argument lists; the daisy-chain reads as self-documenting. Examples appear under
each subsystem below. The general shape:

```js
Filament.SomeObject.Builder()
    .someProperty(value)
    .anotherProperty(value)
    .build(engine);            // some builders also take a target entity: .build(engine, entity)
```

---

## Vertex & Index Buffers

Enums are nested types exposed with a `$` separator (`Filament.VertexBuffer$AttributeType`,
`Filament.IndexBuffer$IndexType`). Buffer slots are filled after the build with `setBufferAt` /
`setBuffer`.

```js
const VertexAttribute = Filament.VertexAttribute;
const AttributeType   = Filament.VertexBuffer$AttributeType;

this.vb = Filament.VertexBuffer.Builder()
    .vertexCount(3)
    .bufferCount(2)
    .attribute(VertexAttribute.POSITION, 0, AttributeType.FLOAT2, 0, 8)
    .attribute(VertexAttribute.COLOR,    1, AttributeType.UBYTE4, 0, 4)
    .normalized(VertexAttribute.COLOR)
    .build(engine);

this.vb.setBufferAt(engine, 0, TRIANGLE_POSITIONS);   // a Float32Array
this.vb.setBufferAt(engine, 1, TRIANGLE_COLORS);      // a Uint32Array

this.ib = Filament.IndexBuffer.Builder()
    .indexCount(3)
    .bufferType(Filament.IndexBuffer$IndexType.USHORT)   // only USHORT or UINT
    .build(engine);

this.ib.setBuffer(engine, new Uint16Array([0, 1, 2]));
```

Data is passed as JS typed arrays (`Float32Array`, `Uint32Array`, `Uint16Array`). A vertex buffer
can use multiple slots (one attribute each, as above) or interleave/concatenate into one slot.

**`Filament.IcoSphere`** is a built-in geometry helper (constructor takes a LOD/subdivision level).
It exposes three typed arrays you feed straight into buffers:

```js
const icosphere = new Filament.IcoSphere(5);
// icosphere.vertices  -> Float32Array of XYZ
// icosphere.tangents  -> Uint16Array (half-floats), surface orientation as quaternions
// icosphere.triangles -> Uint16Array of indices

const vb = Filament.VertexBuffer.Builder()
  .vertexCount(icosphere.vertices.length / 3)
  .bufferCount(2)
  .attribute(VertexAttribute.POSITION, 0, AttributeType.FLOAT3, 0, 0)
  .attribute(VertexAttribute.TANGENTS, 1, AttributeType.SHORT4, 0, 0)
  .normalized(VertexAttribute.TANGENTS)
  .build(engine);
vb.setBufferAt(engine, 0, icosphere.vertices);
vb.setBufferAt(engine, 1, icosphere.tangents);
ib.setBuffer(engine, icosphere.triangles);
```

---

## Materials & Material Instances

A **material package** (`.filamat`) is a binary blob (shaders + metadata) produced by `matc`. Load
it into a `Material` object, then get/create a `MaterialInstance` (instances hold concrete parameter
values and bind to renderables).

```js
const mat     = engine.createMaterial('triangle.filamat');
const matinst = mat.getDefaultInstance();   // shared default instance
```

Or create your own instance and set parameters on it:

```js
const material    = engine.createMaterial(filamat_url);
const matinstance = material.createInstance();

matinstance.setColor3Parameter('baseColor', Filament.RgbType.sRGB, [0.8, 0.0, 0.0]);
matinstance.setFloatParameter('roughness', 0.5);
matinstance.setFloatParameter('clearCoat', 1.0);
matinstance.setFloatParameter('clearCoatRoughness', 0.3);
```

Parameter setters seen in the tutorials:

- `matinstance.setColor3Parameter(name, Filament.RgbType.sRGB, [r,g,b])`
- `matinstance.setFloatParameter(name, value)`
- `matinstance.setTextureParameter(name, texture, sampler)`  (see Textures)

Bind a material instance to a renderable via the `RenderableManager.Builder`:

```js
Filament.RenderableManager.Builder(1)
    .boundingBox({ center: [-1, -1, -1], halfExtent: [1, 1, 1] })
    .material(0, matinst)
    .geometry(0, Filament.RenderableManager$PrimitiveType.TRIANGLES, this.vb, this.ib)
    .build(engine, this.triangle);
```

`PrimitiveType` is `Filament.RenderableManager$PrimitiveType` (`.TRIANGLES`).

---

## Lighting (Directional / Sun / IBL)

Lights are entities with a `LightManager` component. Light type enum is
`Filament.LightManager$Type` (`.SUN`, `.DIRECTIONAL`). The `SUN` type is like `DIRECTIONAL` but
Filament also draws a sun disk into the skybox, hence the extra sun parameters.

```js
const sunlight = Filament.EntityManager.get().create();
scene.addEntity(sunlight);
Filament.LightManager.Builder(LightType.SUN)
  .color([0.98, 0.92, 0.89])
  .intensity(110000.0)
  .direction([0.6, -1.0, -0.8])
  .sunAngularRadius(1.9)
  .sunHaloSize(10.0)
  .sunHaloFalloff(80.0)
  .build(engine, sunlight);

const backlight = Filament.EntityManager.get().create();
scene.addEntity(backlight);
Filament.LightManager.Builder(LightType.DIRECTIONAL)
  .direction([-1, 0, 1])
  .intensity(50000.0)
  .build(engine, backlight);
```

---

## Skybox & IBL from KTX

The high-level helpers are the easy path; the low-level path is shown for completeness.

**High-level (preferred):**

```js
const indirectLight = engine.createIblFromKtx1(ibl_url);   // image-based light from *_ibl.ktx
indirectLight.setIntensity(50000);
scene.setIndirectLight(indirectLight);

const skybox = engine.createSkyFromKtx1(sky_url);          // skybox from *_skybox.ktx
scene.setSkybox(skybox);
```

`cmgen` produces these two cubemap KTX files from an HDR latlong map: a mipmapped IBL and a blurry
skybox. The IBL KTX carries spherical-harmonics coefficients in its metadata (the standalone `sh`
text file from `cmgen` can be discarded).

**Low-level (what the helpers wrap)** — builds the IBL by hand from raw KTX bytes; useful when you
need direct texture control. Names verbatim:

```js
const format   = Filament.PixelDataFormat.RGB;
const datatype = Filament.PixelDataType.UINT_10F_11F_11F_REV;

const ibl_package = Filament.Buffer(Filament.assets[ibl_url]);
const iblktx      = new Filament.Ktx1Bundle(ibl_package);

const ibltex = Filament.Texture.Builder()
  .width(iblktx.info().pixelWidth)
  .height(iblktx.info().pixelHeight)
  .levels(iblktx.getNumMipLevels())
  .sampler(Filament.Texture$Sampler.SAMPLER_CUBEMAP)
  .format(Filament.Texture$InternalFormat.RGBA8)
  .build(engine);

for (let level = 0; level < iblktx.getNumMipLevels(); ++level) {
  const uint8array  = iblktx.getCubeBlob(level).getBytes();
  const pixelbuffer = Filament.PixelBuffer(uint8array, format, datatype);
  ibltex.setImageCube(engine, level, pixelbuffer);
}

const shstring = iblktx.getMetadata('sh');                       // spherical harmonics
const shfloats = shstring.split(/\s/, 9 * 3).map(parseFloat);

const indirectLight = Filament.IndirectLight.Builder()
  .reflections(ibltex)
  .irradianceSh(3, shfloats)
  .intensity(50000.0)
  .build(engine);
scene.setIndirectLight(indirectLight);
```

Low-level names worth keeping: `Filament.Buffer`, `Filament.assets[url]`, `Filament.Ktx1Bundle`,
`.info().pixelWidth/.pixelHeight`, `getNumMipLevels()`, `getCubeBlob(level).getBytes()`,
`Filament.PixelBuffer`, `Filament.PixelDataFormat.RGB`,
`Filament.PixelDataType.UINT_10F_11F_11F_REV`, `Filament.Texture$Sampler.SAMPLER_CUBEMAP`,
`Filament.Texture$InternalFormat.RGBA8`, `ibltex.setImageCube(...)`.

Destroy a skybox before replacing it: `engine.destroySkybox(this.skybox)`.

---

## Textures (KTX2, Compressed, Async)

`.ktx2` textures are loaded with **`engine.createTextureFromKtx2(url, options)`**. Pass
`{srgb: true}` for color (albedo) textures; omit it for linear data maps (roughness/metallic/
normal/ao).

```js
const albedo    = this.engine.createTextureFromKtx2(albedo_url, {srgb: true});
const roughness = this.engine.createTextureFromKtx2(roughness_url);
const metallic  = this.engine.createTextureFromKtx2(metallic_url);
const normal    = this.engine.createTextureFromKtx2(normal_url);
const ao        = this.engine.createTextureFromKtx2(ao_url);
```

Build a sampler and bind each texture as a material parameter:

```js
const sampler = new Filament.TextureSampler(
    Filament.MinFilter.LINEAR_MIPMAP_LINEAR,
    Filament.MagFilter.LINEAR,
    Filament.WrapMode.CLAMP_TO_EDGE);

this.matinstance.setTextureParameter('albedo', albedo, sampler);
this.matinstance.setTextureParameter('roughness', roughness, sampler);
this.matinstance.setTextureParameter('metallic', metallic, sampler);
this.matinstance.setTextureParameter('normal', normal, sampler);
this.matinstance.setTextureParameter('ao', ao, sampler);
```

> Note: the `createTextureFromKtx2` name takes a `2`; there is no `*Ktx2` suffix on the
> IBL/skybox helpers — those are `createIblFromKtx1` / `createSkyFromKtx1`. Copy exactly.

**Picking compressed variants per client** — GPUs differ in supported compression. Use
`Filament.getSupportedFormatSuffix(desired)` where `desired` is a space-separated list of formats
the *server* has (`etc`, `s3tc` / `s3tc_srgb`, `astc`). It intersects desired with supported and
returns a suffix string (possibly empty — uncompressed is always the fallback). You append the
returned suffix to your texture URLs.

```js
const albedo_suffix  = Filament.getSupportedFormatSuffix('astc s3tc_srgb');
const texture_suffix = Filament.getSupportedFormatSuffix('etc');
```

**Asynchronous loading with `Filament.fetch`** — same signature as `Filament.init` (asset URL list
+ callback), but used *after* the app is constructed for progressive loading. Load a minimal asset
set in `Filament.init`, render a low-res skybox immediately, then `Filament.fetch` the heavy
textures and hi-res skybox and swap them in when ready (and unhide the renderable):

```js
Filament.fetch([sky_large_url, albedo_url, roughness_url, metallic_url, normal_url, ao_url], () => {
    const albedo = this.engine.createTextureFromKtx2(albedo_url, {srgb: true});
    // ... create remaining textures + sampler, then setTextureParameter for each ...

    // Replace low-res skybox with high-res skybox.
    this.engine.destroySkybox(this.skybox);
    this.skybox = this.engine.createSkyFromKtx1(sky_large_url);
    this.scene.setSkybox(this.skybox);

    this.scene.addEntity(this.suzanne);   // reveal the renderable now its textures exist
});
```

---

## Meshes: filamesh

Filament has no general asset-loading system, but ships a simple binary mesh format, **`.filamesh`**
(produced by the `filamesh` CLI). Load it with **`engine.loadFilamesh(url, materialInstance)`**,
which returns an object whose `.renderable` is the entity:

```js
const filamesh = this.engine.loadFilamesh(filamesh_url, this.matinstance);
this.suzanne   = filamesh.renderable;   // an entity; add to scene with scene.addEntity(...)
```

For richer scenes use glTF/glb via the gltfio-based loaders (the larger web samples — `helmet`,
`animation`, `morphing`, `skinning`, `parquet`, `cube_fl0`, `sky` — demonstrate these), but the
three core tutorials use `filamesh` only.

---

## The Render & Resize Loop

Drive frames with `requestAnimationFrame`. The render method updates transforms/camera, then issues
the one mandatory call:

```js
this.renderer.render(this.swapChain, this.view);
```

That is the verbatim render call — `renderer.render(swapChain, view)`. Full render method from the
triangle tutorial (rotate via the transform manager, then render):

```js
render() {
    // Rotate the triangle.
    const radians = Date.now() / 1000;
    const transform = mat4.fromRotation(mat4.create(), radians, [0, 0, 1]);
    const tcm = this.engine.getTransformManager();
    const inst = tcm.getInstance(this.triangle);
    tcm.setTransform(inst, transform);
    inst.delete();

    // Render the frame.
    this.renderer.render(this.swapChain, this.view);
    window.requestAnimationFrame(this.render);
}
```

Camera animation (redball — orbit the eye, then `lookAt`):

```js
render() {
    const eye = [0, 0, 4], center = [0, 0, 0], up = [0, 1, 0];
    const radians = Date.now() / 10000;
    vec3.rotateY(eye, eye, center, radians);
    this.camera.lookAt(eye, center, up);
    this.renderer.render(this.swapChain, this.view);
    window.requestAnimationFrame(this.render);
}
```

Trackball-driven transform (suzanne — `gltumble`'s `Trackball`):

```js
this.trackball = new Trackball(canvas, {startSpin: 0.035});
// ...in render():
const tcm = this.engine.getTransformManager();
const inst = tcm.getInstance(this.suzanne);
tcm.setTransform(inst, this.trackball.getMatrix());
inst.delete();
```

Bind callbacks and start the loop in the constructor:

```js
this.render = this.render.bind(this);
this.resize = this.resize.bind(this);
window.addEventListener('resize', this.resize);
window.requestAnimationFrame(this.render);
```

---

## Resize / DPR Handling

The resize handler scales the drawing buffer by `window.devicePixelRatio` for high-DPI displays,
updates the view's viewport, and adjusts the camera projection. This is shown in every tutorial.

**Orthographic (triangle):**

```js
resize() {
    const dpr = window.devicePixelRatio;
    const width  = this.canvas.width  = this.canvas.clientWidth  * dpr;
    const height = this.canvas.height = this.canvas.clientHeight * dpr;
    this.view.setViewport([0, 0, width, height]);

    const aspect = width / height;
    const Projection = Filament.Camera$Projection;
    this.camera.setProjection(Projection.ORTHO, -aspect, aspect, -1, 1, 0, 1);
}
```

**Perspective FOV (redball):**

```js
resize() {
    const dpr = window.devicePixelRatio;
    const width  = this.canvas.width  = this.canvas.clientWidth  * dpr;
    const height = this.canvas.height = this.canvas.clientHeight * dpr;
    this.view.setViewport([0, 0, width, height]);
    this.camera.setProjectionFov(45, width / height, 1.0, 10.0, Fov.VERTICAL);
}
```

**Perspective FOV picking axis by aspect (suzanne):**

```js
resize() {
    const dpr = window.devicePixelRatio;
    const width  = this.canvas.width  = this.canvas.clientWidth  * dpr;
    const height = this.canvas.height = this.canvas.clientHeight * dpr;
    this.view.setViewport([0, 0, width, height]);

    const aspect = width / height;
    const Fov = Filament.Camera$Fov, fov = aspect < 1 ? Fov.HORIZONTAL : Fov.VERTICAL;
    this.camera.setProjectionFov(45, aspect, 1.0, 10.0, fov);
}
```

Camera projection methods/enums seen: `camera.setProjection(Filament.Camera$Projection.ORTHO,
left, right, bottom, top, near, far)`, `camera.setProjectionFov(fovDegrees, aspect, near, far,
Filament.Camera$Fov.VERTICAL|HORIZONTAL)`, `camera.lookAt(eye, center, up)`.

Call `this.resize()` once at the end of the constructor to set the initial viewport before the
first frame.

---

## Asset-Production Toolchain (matc / cmgen / filamesh / mipgen)

The CLI tools live in the Filament release for your **development** machine (not the web archive).
Match the release version to the `unpkg.com/filament@x.x.x` in your HTML.

**`matc`** — compile a `.mat` text material into a `.filamat` package (shaders + metadata):

```bash
matc -a opengl -p mobile -o plastic.filamat plastic.mat
matc -a opengl -p mobile -o textured.filamat textured.mat
```

`-a opengl` selects the GL/WebGL backend shaders; `-p mobile` the mobile profile. A `.mat` file
declares `name`, `shadingModel`, `parameters`, optional `requires` (e.g. `[ uv0 ]` for textured
materials), and a `fragment` block. Textured materials reference samplers as
`materialParams_<name>` and read UVs with `getUV0()`.

**`cmgen`** — bake an HDR latlong environment into IBL + skybox cubemap KTX files:

```bash
cmgen -x pillars_2k --format=ktx --size=256 --extract-blur=0.1 pillars_2k.hdr
```

Output folder contains `*_ibl.ktx` (mipmapped, with SH metadata) and `*_skybox.ktx`. For a tiny
fast-loading skybox, bake a small size and rename, e.g.:

```bash
cmgen -x . --format=ktx --size=64 --extract-blur=0.1 venetian_crossroads_2k.hdr
mv venetian*_ibl.ktx venetian_crossroads_2k_skybox_tiny.ktx
```

**`filamesh`** — convert an OBJ to the binary `.filamesh` format (`--compress` for compression):

```bash
filamesh --compress monkey.obj suzanne.filamesh
```

**`mipgen`** — generate mipmapped KTX (`.ktx`) and KTX2 (`.ktx2`) textures, with optional GPU
compression. Make both compressed and uncompressed variants since clients differ:

```bash
# base color
mipgen albedo.png albedo.ktx2
mipgen --compression=uastc albedo.png albedo.ktx2

# normal map (+ compressed)
mipgen --strip-alpha --kernel=NORMALS --linear normal.png normal.ktx
mipgen --strip-alpha --kernel=NORMALS --linear --compression=uastc_normals normal.png normal.ktx2

# single-channel maps (roughness / metallic / ao)
mipgen --grayscale roughness.png roughness.ktx
mipgen --grayscale --compression=uastc roughness.png roughness.ktx2
```

Run `mipgen --help` for full flags. In production, drive all of the above from a build script.

---

## Asset Type Reference

| Asset | Extension | Produced by | Loaded in JS by |
|-------|-----------|-------------|------------------|
| Material package | `.filamat` | `matc` | `engine.createMaterial(url)` |
| IBL cubemap | `*_ibl.ktx` | `cmgen` | `engine.createIblFromKtx1(url)` |
| Skybox cubemap | `*_skybox.ktx` | `cmgen` | `engine.createSkyFromKtx1(url)` |
| Texture | `.ktx2` | `mipgen` | `engine.createTextureFromKtx2(url[, {srgb}])` |
| Mesh | `.filamesh` | `filamesh` | `engine.loadFilamesh(url, matinstance)` |

All of these must be listed in `Filament.init([...])` (or `Filament.fetch([...])`) before the
matching `engine.create*` / `loadFilamesh` call runs — the helpers read from the pre-fetched cache.

---

## Gotchas

- **Enums use `$`**: nested C++ enums are flattened with a `$` in JS — `Filament.VertexBuffer$AttributeType`,
  `Filament.IndexBuffer$IndexType`, `Filament.RenderableManager$PrimitiveType`, `Filament.Camera$Fov`,
  `Filament.Camera$Projection`, `Filament.LightManager$Type`, `Filament.Texture$Sampler`,
  `Filament.Texture$InternalFormat`. Aliasing them to locals/globals keeps call sites readable.
- **`inst.delete()`**: transform/component *instance* handles from `tcm.getInstance(entity)` are
  temporary native handles — call `inst.delete()` after use each frame to avoid leaks.
- **Pre-fetch before use**: synchronous `engine.create*FromKtx*` / `createMaterial` / `loadFilamesh`
  only work for URLs already downloaded via `Filament.init` or `Filament.fetch`.
- **sRGB flag**: pass `{srgb: true}` to `createTextureFromKtx2` for color maps; leave it off for
  linear data maps (roughness, metallic, normal, ao).
- **Cameras are entities**: `engine.createCamera(Filament.EntityManager.get().create())` — you must
  mint the entity yourself.
- **Helper version mismatch**: KTX1 (IBL/skybox) helpers are `...FromKtx1`; the KTX2 texture helper
  is `...FromKtx2`. They are not interchangeable.
- **No general asset loader for meshes in core tutorials**: only `filamesh` is covered; glTF/glb is
  in the larger samples (helmet, animation, etc.).
- **Don't ship Python's `http.server`**: wrong WASM MIME type in production.
```