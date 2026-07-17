# Platform Setup: Android (Kotlin/Java)

> Source: Filament android samples (Kotlin) + repo README + Maven guide, Filament v1.72.0
> Last synced: 2026-06-19

**Contents:** [Dependencies](#dependencies) · [Initialize Filament (`Filament.init()`)](#initialize-filament-filamentinit) · [Canonical Render Setup](#canonical-render-setup) · [Field declarations](#field-declarations) · [`onCreate` wiring](#oncreate-wiring) · [`UiHelper` + `SurfaceView`](#uihelper--surfaceview) · [Engine / Renderer / View / Scene / Camera](#engine--renderer--view--scene--camera) · [Configuring the View](#configuring-the-view) · [The `UiHelper.RendererCallback` (swap chain lifecycle)](#the-uihelperrenderercallback-swap-chain-lifecycle) · [The Frame Loop (`Choreographer` + `Renderer`)](#the-frame-loop-choreographer--renderer) · [Loading Assets from the APK](#loading-assets-from-the-apk) · [Reading a raw asset into a `ByteBuffer`](#reading-a-raw-asset-into-a-bytebuffer) · [Materials (`.filamat`) and material instances](#materials-filamat-and-material-instances) · [Image-based lighting (IBL / KTX)](#image-based-lighting-ibl--ktx) · [Meshes (`.filamesh`)](#meshes-filamesh) · [JNI / Lifetime: explicit destruction](#jni--lifetime-explicit-destruction) · [Kotlin vs Java](#kotlin-vs-java)

---

## Dependencies

Android projects declare Filament libraries as Maven dependencies from Maven Central, group `com.google.android.filament`. Verbatim from the repo README:

```groovy
repositories {
    // ...
    mavenCentral()
}

dependencies {
    implementation 'com.google.android.filament:filament-android:1.72.0'
}
```

All artifacts in the `com.google.android.filament` group (verbatim descriptions from the README):

| Artifact | Coordinate (v1.72.0) | Description |
| --- | --- | --- |
| `filament-android` | `com.google.android.filament:filament-android:1.72.0` | The Filament rendering engine itself. |
| `filament-android-debug` | `com.google.android.filament:filament-android-debug:1.72.0` | Debug version of `filament-android`. |
| `gltfio-android` | `com.google.android.filament:gltfio-android:1.72.0` | A glTF 2.0 loader for Filament, depends on `filament-android`. |
| `filament-utils-android` | `com.google.android.filament:filament-utils-android:1.72.0` | KTX loading, Kotlin math, and camera utilities, depends on `gltfio-android`. |
| `filamat-android` | `com.google.android.filament:filamat-android:1.72.0` | A runtime material builder/compiler. This library is large but contains a full shader compiler/validator/optimizer and supports both OpenGL and Vulkan. |

Notes:
- The dependency chain is `filament-utils-android` → `gltfio-android` → `filament-android`. Pulling `filament-utils-android` transitively brings the loader and the engine.
- `filamat-android` (runtime material compiler) is only needed when you build/compile materials at runtime. The samples ship pre-compiled `.filamat` packages instead, so they do **not** require it.
- Always use host-side tools (e.g. `matc`, `cmgen`, `filamesh`) from the *same release* as the runtime library. The README calls this out specifically for `matc` (the material compiler).

The KTX/IBL loader (`KTX1Loader`) and the filamesh loader live in `filament-utils-android`; the glTF loader lives in `gltfio-android`.

---

## Initialize Filament (`Filament.init()`)

`Filament.init()` loads the JNI native library that backs almost every API call. Call it **once, before any other Filament API**. The samples do it in a `companion object` static initializer so it runs at class load:

```kotlin
class MainActivity : Activity() {
    // Make sure to initialize Filament first
    // This loads the JNI library needed by most API calls
    companion object {
        init {
            Filament.init()
        }
    }
    // ...
}
```

The README states the same rule plainly: "You must always first initialize Filament by calling `Filament.init()`."

---

## Canonical Render Setup

Grounded in `hellotriangle-MainActivity.kt` (minimal), `litcube-MainActivity.kt` (material instance + light), and `ibl-MainActivity.kt` (IBL + mesh). All three share the same skeleton.

### Field declarations

```kotlin
// The View we want to render into
private lateinit var surfaceView: SurfaceView
// UiHelper is provided by Filament to manage SurfaceView and SurfaceTexture
private lateinit var uiHelper: UiHelper
// DisplayHelper is provided by Filament to manage the display
private lateinit var displayHelper: DisplayHelper
// Choreographer is used to schedule new frames
private lateinit var choreographer: Choreographer

// Engine creates and destroys Filament resources
// Each engine must be accessed from a single thread of your choosing
// Resources cannot be shared across engines
private lateinit var engine: Engine
// A renderer instance is tied to a single surface (SurfaceView, TextureView, etc.)
private lateinit var renderer: Renderer
// A scene holds all the renderable, lights, etc. to be drawn
private lateinit var scene: Scene
// A view defines a viewport, a scene and a camera for rendering
private lateinit var view: View
private lateinit var camera: Camera

// Filament entity representing a renderable object
@Entity private var renderable = 0

// A swap chain is Filament's representation of a surface
private var swapChain: SwapChain? = null

// Performs the rendering and schedules new frames
private val frameScheduler = FrameCallback()
```

Imports used across the samples (package `com.google.android.filament`):

```kotlin
import android.view.Choreographer
import android.view.Surface
import android.view.SurfaceView
import com.google.android.filament.*
import com.google.android.filament.android.DisplayHelper
import com.google.android.filament.android.FilamentHelper
import com.google.android.filament.android.UiHelper
```

The Android-specific helpers (`UiHelper`, `DisplayHelper`, `FilamentHelper`) live in the `com.google.android.filament.android` package. Core types (`Engine`, `Renderer`, `View`, `Scene`, `Camera`, `Material`, `Skybox`, `LightManager`, `RenderableManager`, `SwapChain`, `EntityManager`, …) are in `com.google.android.filament`.

### `onCreate` wiring

```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)

    surfaceView = SurfaceView(this)
    setContentView(surfaceView)

    choreographer = Choreographer.getInstance()

    displayHelper = DisplayHelper(this)

    setupSurfaceView()
    setupFilament()
    setupView()
    setupScene()
}
```

### `UiHelper` + `SurfaceView`

`UiHelper` manages the `SurfaceView` (or `TextureView` / `SurfaceTexture`) lifecycle and hands you a native `Surface` through its render callback. Set the callback, then `attachTo`:

```kotlin
private fun setupSurfaceView() {
    uiHelper = UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK)
    uiHelper.renderCallback = SurfaceCallback()

    // NOTE: To choose a specific rendering resolution, add the following line:
    // uiHelper.setDesiredSize(1280, 720)
    uiHelper.attachTo(surfaceView)
}
```

- `UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK)` is the constructor the samples use.
- `uiHelper.renderCallback = ...` registers a `UiHelper.RendererCallback` (see below).
- `uiHelper.attachTo(surfaceView)` binds the helper to your view. `attachTo` also accepts a `TextureView` — the README notes `UiHelper` works with `SurfaceTexture`, `TextureView`, or `SurfaceView`.
- `uiHelper.setDesiredSize(width, height)` (commented out in the samples) decouples render resolution from the on-screen view size.
- Other members used elsewhere: `uiHelper.isReadyToRender` (frame guard), `uiHelper.swapChainFlags`, `uiHelper.detach()`.

### Engine / Renderer / View / Scene / Camera

The simple samples create the engine with `Engine.create()`:

```kotlin
private fun setupFilament() {
    engine = Engine.create()
    renderer = engine.createRenderer()
    scene = engine.createScene()
    view = engine.createView()
    camera = engine.createCamera(engine.entityManager.create())
}
```

`hellotriangle` uses the builder form to pin a feature level (it renders at `FEATURE_LEVEL_0`, which has no post-processing):

```kotlin
private fun setupFilament() {
    val config = Engine.Config()
    //config.forceGLES2Context = true

    engine = Engine.Builder()
        .config(config)
        .featureLevel(Engine.FeatureLevel.FEATURE_LEVEL_0)
        .build()
    renderer = engine.createRenderer()
    scene = engine.createScene()
    view = engine.createView()
    camera = engine.createCamera(engine.entityManager.create())
}
```

Key facts (from the samples' own comments):
- The `Engine` creates and destroys all Filament resources. Each engine must be accessed from a single thread; resources cannot be shared across engines.
- A `Renderer` is tied to a single surface.
- A `Camera` is created on an entity: `engine.createCamera(engine.entityManager.create())`.
- `engine.entityManager` and the static `EntityManager.get()` both reach the entity manager; the samples use `EntityManager.get().create()` for renderable/light entities.

### Configuring the View

Attach the camera and scene to the view; set up the skybox on the scene:

```kotlin
private fun setupView() {
    scene.skybox = Skybox.Builder().color(0.035f, 0.035f, 0.035f, 1.0f).build(engine)

    // Tell the view which camera we want to use
    view.camera = camera
    // Tell the view which scene we want to render
    view.scene = scene
}
```

Variations:
- `hellotriangle` disables post-processing at feature level 0:
  ```kotlin
  if (engine.activeFeatureLevel == Engine.FeatureLevel.FEATURE_LEVEL_0) {
      view.isPostProcessingEnabled = false
  }
  ```
- `ibl` enables ambient occlusion ("the cheapest effect that adds a lot of quality"):
  ```kotlin
  view.ambientOcclusionOptions = view.ambientOcclusionOptions.apply {
      enabled = true
  }
  ```
- In the IBL sample the skybox comes from the loaded environment instead of a solid color:
  ```kotlin
  scene.skybox = ibl.skybox
  scene.indirectLight = ibl.indirectLight
  ```

---

## The `UiHelper.RendererCallback` (swap chain lifecycle)

You implement `UiHelper.RendererCallback` and create/destroy the `SwapChain` in response. The README is explicit: "You are still responsible for creating the swap chain in the `onNativeWindowChanged()` callback." Three methods:

```kotlin
inner class SurfaceCallback : UiHelper.RendererCallback {
    override fun onNativeWindowChanged(surface: Surface) {
        swapChain?.let { engine.destroySwapChain(it) }
        swapChain = engine.createSwapChain(surface)
        displayHelper.attach(renderer, surfaceView.display)
    }

    override fun onDetachedFromSurface() {
        displayHelper.detach()
        swapChain?.let {
            engine.destroySwapChain(it)
            // Required to ensure we don't return before Filament is done executing the
            // destroySwapChain command, otherwise Android might destroy the Surface
            // too early
            engine.flushAndWait()
            swapChain = null
        }
    }

    override fun onResized(width: Int, height: Int) {
        val aspect = width.toDouble() / height.toDouble()
        camera.setProjection(45.0, aspect, 0.1, 20.0, Camera.Fov.VERTICAL)

        view.viewport = Viewport(0, 0, width, height)

        FilamentHelper.synchronizePendingFrames(engine)
    }
}
```

Per-method notes (verbatim names from the samples):

- **`onNativeWindowChanged(surface: Surface)`** — destroy any existing swap chain, then `engine.createSwapChain(surface)`, then `displayHelper.attach(renderer, surfaceView.display)`. The `litcube`/`ibl` samples use `engine.createSwapChain(surface)` with no flags.
- **`onDetachedFromSurface()`** — `displayHelper.detach()`, destroy the swap chain, then **`engine.flushAndWait()`** before nulling it. The comment explains why: it ensures Filament finishes the `destroySwapChain` command before returning, otherwise Android may destroy the `Surface` too early.
- **`onResized(width, height)`** — recompute the camera projection, set `view.viewport = Viewport(0, 0, width, height)`, then call **`FilamentHelper.synchronizePendingFrames(engine)`**.

Projection differs by sample:
- `litcube` and `ibl` use a perspective projection: `camera.setProjection(45.0, aspect, 0.1, 20.0, Camera.Fov.VERTICAL)`.
- `hellotriangle` uses an orthographic projection: `camera.setProjection(Camera.Projection.ORTHO, -aspect * zoom, aspect * zoom, -zoom, zoom, 0.0, 10.0)`.

The `hellotriangle` sample also shows the sRGB swap-chain path for feature level 0:

```kotlin
override fun onNativeWindowChanged(surface: Surface) {
    swapChain?.let { engine.destroySwapChain(it) }

    // at feature level 0, we don't have post-processing, so we need to set
    // the colorspace to sRGB (FIXME: it's not supported everywhere!)
    var flags = uiHelper.swapChainFlags
    if (engine.activeFeatureLevel == Engine.FeatureLevel.FEATURE_LEVEL_0) {
        if (SwapChain.isSRGBSwapChainSupported(engine)) {
            flags = flags or SwapChainFlags.CONFIG_SRGB_COLORSPACE
        }
    }

    swapChain = engine.createSwapChain(surface, flags)
    displayHelper.attach(renderer, surfaceView.display)
}
```

---

## The Frame Loop (`Choreographer` + `Renderer`)

A `Choreographer.FrameCallback` re-posts itself every frame and drives `renderer.beginFrame` / `render` / `endFrame`. Identical across all three samples:

```kotlin
inner class FrameCallback : Choreographer.FrameCallback {
    override fun doFrame(frameTimeNanos: Long) {
        // Schedule the next frame
        choreographer.postFrameCallback(this)

        // This check guarantees that we have a swap chain
        if (uiHelper.isReadyToRender) {
            // If beginFrame() returns false you should skip the frame
            // This means you are sending frames too quickly to the GPU
            if (renderer.beginFrame(swapChain!!, frameTimeNanos)) {
                renderer.render(view)
                renderer.endFrame()
            }
        }
    }
}
```

Drive it from the Activity lifecycle — post in `onResume`, remove in `onPause` (and again in `onDestroy`):

```kotlin
override fun onResume() {
    super.onResume()
    choreographer.postFrameCallback(frameScheduler)
    animator.start()
}

override fun onPause() {
    super.onPause()
    choreographer.removeFrameCallback(frameScheduler)
    animator.cancel()
}
```

Frame-loop rules from the samples' comments:
- Guard every frame with `uiHelper.isReadyToRender` — this guarantees a swap chain exists before you dereference `swapChain!!`.
- `renderer.beginFrame(swapChain, frameTimeNanos)` returns `false` when you're feeding the GPU too fast; **skip the frame** (don't call `render`/`endFrame`) when it does.
- Always re-post the callback (`choreographer.postFrameCallback(this)`) at the top of `doFrame` to keep the loop alive.

Animation in these samples is a plain `ValueAnimator` whose update listener mutates Filament state on the main thread — e.g. `engine.transformManager.setTransform(...)` (litcube/hellotriangle) or `camera.lookAt(...)` (ibl).

---

## Loading Assets from the APK

### Reading a raw asset into a `ByteBuffer`

All three samples use this helper to pull an uncompressed asset out of `assets/` into a native-friendly `ByteBuffer`:

```kotlin
private fun readUncompressedAsset(assetName: String): ByteBuffer {
    assets.openFd(assetName).use { fd ->
        val input = fd.createInputStream()
        val dst = ByteBuffer.allocate(fd.length.toInt())

        val src = Channels.newChannel(input)
        src.read(dst)
        src.close()

        return dst.apply { rewind() }
    }
}
```

This uses `AssetManager.openFd`, which requires the asset to be stored **uncompressed** in the APK. For Filament asset types (`.filamat`, `.ktx`, `.filamesh`, etc.) keep them uncompressed via `aaptOptions { noCompress "filamat", "ktx", "filamesh" }` (or `androidResources { noCompress += [...] }` on newer AGP). Compressed assets can't be opened with `openFd`.

### Materials (`.filamat`) and material instances

A material is a pre-compiled `.filamat` package (built by `matc`), loaded from assets and fed to `Material.Builder().payload(...)`:

```kotlin
private fun loadMaterial() {
    readUncompressedAsset("materials/lit.filamat").let {
        material = Material.Builder().payload(it, it.remaining()).build(engine)
    }
}
```

`hellotriangle` additionally pre-compiles the material variants off the render path and flushes:

```kotlin
private fun loadMaterial() {
    readUncompressedAsset("materials/baked_color.filamat").let {
        material = Material.Builder().payload(it, it.remaining()).build(engine)
        material.compile(
            Material.CompilerPriorityQueue.HIGH,
            Material.UserVariantFilterBit.ALL,
            Handler(Looper.getMainLooper())) {
                    android.util.Log.i("hellotriangle",
                        "Material " + material.name + " compiled.")
        }
        engine.flush()
    }
}
```

Create a `MaterialInstance` to set per-object parameters (`litcube`):

```kotlin
private fun setupMaterial() {
    // Create an instance of the material to set different parameters on it
    materialInstance = material.createInstance()
    // sRGB color → Filament converts to linear automatically
    materialInstance.setParameter("baseColor", Colors.RgbType.SRGB, 1.0f, 0.85f, 0.57f)
    materialInstance.setParameter("metallic", 0.0f)
    materialInstance.setParameter("roughness", 0.3f)
}
```

The material instance is then handed to the renderable: `.material(0, materialInstance)` in `RenderableManager.Builder`. (`hellotriangle`, which sets no parameters, uses `material.defaultInstance` directly.)

### Image-based lighting (IBL / KTX)

The `ibl` sample loads an environment with a `loadIbl(...)` helper and wires its skybox + indirect light into the scene:

```kotlin
private lateinit var ibl: Ibl

private fun loadImageBasedLight() {
    ibl = loadIbl(assets, "envs/flower_road_no_sun_2k", engine)
    ibl.indirectLight.intensity = 40_000.0f
}

// in setupScene():
scene.skybox = ibl.skybox
scene.indirectLight = ibl.indirectLight
```

The `Ibl` type and the `loadIbl` / `destroyIbl` helpers are sample-side utilities (in the IBL sample project, not core Filament API). Under the hood they consume KTX environment files (an IBL is a `_ibl.ktx` reflections map plus a spherical-harmonics file, both produced by `cmgen`). The README confirms environments "must be pre-processed using `cmgen` or using the `libiblprefilter` library."

**KTX1 loader (`com.google.android.filament.utils.KTX1Loader`):** `filament-utils-android` exposes a `KTX1Loader` object that turns a KTX1 `java.nio.Buffer` into Filament objects. This is what a non-sample app uses directly (the `ibl` sample's `loadIbl(...)` helper just wraps these calls):

```kotlin
// Options.srgb controls sRGB interpretation (default false)
val texture: Texture = KTX1Loader.createTexture(engine, byteBuffer, KTX1Loader.Options())

// IBL: returns IndirectLightBundle(indirectLight, cubemap); SH are read from the KTX
val iblBundle = KTX1Loader.createIndirectLight(engine, iblBuffer)
val indirectLight: IndirectLight? = iblBundle.indirectLight

// Skybox: returns SkyboxBundle(skybox, cubemap)
val skyBundle = KTX1Loader.createSkybox(engine, skyboxBuffer)
val skybox: Skybox? = skyBundle.skybox

// or pull just the 9*3 spherical-harmonics coefficients
val sh: FloatArray? = KTX1Loader.getSphericalHarmonics(iblBuffer)
```

An IBL environment is a `_ibl.ktx` reflections map (with embedded spherical harmonics); a skybox is a separate `_skybox.ktx`. Both must be produced by `cmgen` (or `libiblprefilter`) — see [`concepts-lighting-ibl.md`](concepts-lighting-ibl.md).

### Meshes (`.filamesh`)

The `ibl` sample loads a mesh in the **filamesh** format (produced by the `filamesh` host tool) with a `loadMesh(...)` helper:

```kotlin
private lateinit var mesh: Mesh

// This map can contain named materials that will map to the material names
// loaded from the filamesh file. The material called "DefaultMaterial" is
// applied when no named material can be found
val materials = mapOf("DefaultMaterial" to materialInstance)

// Load the mesh in the filamesh format (see filamesh tool)
mesh = loadMesh(assets, "models/shader_ball.filamesh", materials, engine)

scene.addEntity(mesh.renderable)
```

The `Mesh` type and `loadMesh` / `destroyMesh` are sample-side helpers (wrapping `filameshio`'s `MeshReader`). `mesh.renderable` is the entity you add to the scene and transform via the `TransformManager`:

```kotlin
engine.transformManager.setTransform(
    engine.transformManager.getInstance(mesh.renderable),
    floatArrayOf(   // Filament uses column-major matrices
        1.0f,  0.0f, 0.0f, 0.0f,
        0.0f,  1.0f, 0.0f, 0.0f,
        0.0f,  0.0f, 1.0f, 0.0f,
        0.0f, -1.2f, 0.0f, 1.0f
    ))
```

> Unverified: `Mesh`, `loadMesh`, `destroyMesh` are referenced but **not defined** in the provided files — they are sample helpers, not necessarily a public API surface. For glTF assets, use the `gltfio-android` loader (`AssetLoader` / `ResourceLoader`) instead; those classes are not exercised in the provided samples, so verify their signatures against `gltfio-android`.

Constructing geometry by hand (no asset) uses `VertexBuffer.Builder` / `IndexBuffer.Builder` with a `ByteBuffer` in `ByteOrder.nativeOrder()` — see `hellotriangle.createMesh()` (interleaved position+color) and `litcube.createMesh()` (position + packed tangent frame via `MathUtils.packTangentFrame`).

---

## JNI / Lifetime: explicit destruction

Every Filament object is backed by a native (C++) resource reached through JNI. The garbage collector does **not** free these — you must destroy them explicitly through the `Engine`, and you must do it in the right order. The samples concentrate this in `onDestroy()`.

Canonical teardown (from `litcube`, the most complete):

```kotlin
override fun onDestroy() {
    super.onDestroy()

    // Stop the animation and any pending frame
    choreographer.removeFrameCallback(frameScheduler)
    animator.cancel()

    // Always detach the surface before destroying the engine
    uiHelper.detach()

    // Cleanup all resources
    engine.destroyEntity(light)
    engine.destroyEntity(renderable)
    engine.destroyRenderer(renderer)
    engine.destroyVertexBuffer(vertexBuffer)
    engine.destroyIndexBuffer(indexBuffer)
    engine.destroyMaterialInstance(materialInstance)
    engine.destroyMaterial(material)
    engine.destroyView(view)
    engine.destroyScene(scene)
    engine.destroyCameraComponent(camera.entity)

    // Engine.destroyEntity() destroys Filament related resources only
    // (components), not the entity itself
    val entityManager = EntityManager.get()
    entityManager.destroy(light)
    entityManager.destroy(renderable)
    entityManager.destroy(camera.entity)

    // Destroying the engine will free up any resource you may have forgotten
    // to destroy, but it's recommended to do the cleanup properly
    engine.destroy()
}
```

Lifetime rules, straight from the sample comments:

1. **Detach the surface before destroying the engine** — `uiHelper.detach()` first.
2. **Entities vs components are two separate destructions.** `engine.destroyEntity(entity)` destroys only the *Filament components* attached to the entity (the renderable/light component), **not the entity itself**. You must *also* call `EntityManager.get().destroy(entity)` to release the entity handle. The samples do both, for every entity (renderables, lights, and the camera's entity).
3. **Camera teardown:** destroy the camera *component* with `engine.destroyCameraComponent(camera.entity)`, then destroy `camera.entity` via the `EntityManager`. (There is no `engine.destroyCamera` in this flow.)
4. **Match every create with a destroy through the engine:** `destroyRenderer`, `destroyView`, `destroyScene`, `destroyVertexBuffer`, `destroyIndexBuffer`, `destroyMaterial`, `destroyMaterialInstance`, `destroySwapChain`. The IBL sample mirrors this and adds `destroyMesh(engine, mesh)` / `destroyIbl(engine, ibl)` for its sample-loaded assets.
5. **`engine.destroy()` last.** It will free anything you forgot, but the comment is explicit: "it's recommended to do the cleanup properly" — don't rely on it as your only cleanup.
6. **Swap-chain teardown needs a flush.** When destroying a swap chain in response to surface detach, call `engine.flushAndWait()` afterward so Android doesn't tear down the `Surface` before Filament finishes (see `onDetachedFromSurface` above).

Why it matters: skipping these leaks native GPU/driver memory that the JVM heap profiler won't even show, and destroying out of order (e.g. engine before swap chain, or component before entity) can crash in native code or leave dangling handles.

The `@Entity` annotation marks `Int` fields that hold entity ids (entities are plain integers in the Java/Kotlin binding):

```kotlin
@Entity private var renderable = 0
@Entity private var light = 0
```

---

## Kotlin vs Java

The samples are Kotlin, but Filament's Android binding is a plain **Java/JNI API** (the README lists "Java/JNI API for Android" as a first-class API). Everything above maps one-to-one to Java; the only differences are language syntax:

- Kotlin property access (`view.camera = camera`, `scene.skybox = ...`) becomes Java setters (`view.setCamera(camera)`, `scene.setSkybox(...)`).
- Kotlin's `engine.entityManager` becomes `engine.getEntityManager()` in Java.
- Builders, `Engine`, `EntityManager.get()`, the `UiHelper.RendererCallback` / `Choreographer.FrameCallback` interfaces, and all `engine.destroy*` calls are identical method names from Java.
- `Filament.init()`, the JNI-lifetime rules, and the asset-loading patterns are language-agnostic — they apply identically to a Java `Activity`.

The `filament-utils-android` "Kotlin math" types are a Kotlin convenience; the core engine API is usable from either language.
