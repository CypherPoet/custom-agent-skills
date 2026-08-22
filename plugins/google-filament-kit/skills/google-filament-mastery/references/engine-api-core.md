# Engine API: Core Objects & Render Loop

> Source: Filament C++ headers (Engine/SwapChain/Renderer/View/Scene/Camera) + repo README, Filament v1.75.0
> Last synced: 2026-08-14

> Build, linking, SDK install, and native-window creation (SDL2 / NSView / HWND / ANativeWindow) live in the platform reference, not here. Exposure / tone-mapping / post-processing depth lives in `concepts-imaging-pipeline.md`.

## Table of Contents

| Section | Covers |
|---|---|
| [Mental Model & Ownership](#mental-model--ownership) | Engine factories, surfaces, renderers, views, flat scenes, entity cameras, explicit destruction, and non-reference-counted associations |
| [Minimal Setup + Render Loop](#minimal-setup--render-loop) | Core object creation, scene and camera binding, renderable setup, projection updates, guarded frame sequencing, and ordered component cleanup |
| [Engine](#engine) | Engine creation and configuration, factory methods, explicit resource destruction and tracking, feature levels, threading constraints, and frame pumping |
| [SwapChain](#swapchain) | Platform-specific native windows, headless surfaces, transparency, readback, color, stencil, protection and MSAA flags, capability checks, frame-rate requests, and callbacks |
| [Renderer](#renderer) | Frame admission and pacing, ordered shadow, depth, color, and post passes, multi-view rendering, timing, copies and readback, standalone views, and telemetry |
| [View](#view) | Scene, camera, viewport, and render-target bindings, effect and quality options, visibility layers, picking, culling and froxel debug, and temporal-history resets |
| [Scene](#scene) | Flat renderable and light membership, one skybox and indirect light, bulk insertion and removal, counts, iteration limits, and transform ownership elsewhere |
| [Camera](#camera) | Entity-component lifecycle, right-handed pose, perspective, orthographic, lens and custom projections, infinite render far plane, transform vectors, exposure, and focus |
| [Common Pitfalls](#common-pitfalls) | Frame guards, swap-chain lifecycle, resource destruction, and engine-thread mistakes |

---

## Mental Model & Ownership

`Engine` is Filament's main entry point and the **factory + owner of every other object**. The canonical object graph:

- **Engine** — hardware context (one OpenGL/Vulkan/Metal context); spawns the render thread and worker threads.
- **SwapChain** — wraps a native OS renderable surface (window/view) or an offscreen buffer.
- **Renderer** — maps to one window; drives the per-frame loop.
- **View** — a render pass: binds a Scene + Camera + Viewport + quality/AO/bloom/AA options.
- **Scene** — flat container of renderable + light *entities*, plus skybox + IBL. Not a scene-graph.
- **Camera** — a *component* on an entity; holds projection + transform + exposure.

**Ownership rule (critical):** every Filament object is created via an `engine->createX(...)` factory and **must** be destroyed via `engine->destroy(...)`. `Engine::destroy(&engine)` is called **last**, after all other resources. Leaked resources are freed when the Engine is destroyed, but a warning is logged. The Engine does not reference-count: `View`/`Scene`/`Camera`/`ColorGrading` associations are plain references — dissociate (or destroy in the right order) before destroying the referenced object.

---

## Minimal Setup + Render Loop

The Engine header's own doc-comment gives the canonical full lifecycle (this is verbatim from `Engine.h`):

```cpp
#include <filament/Engine.h>
#include <filament/Renderer.h>
#include <filament/Scene.h>
#include <filament/View.h>
using namespace filament;

Engine* engine       = Engine::create();
SwapChain* swapChain = engine->createSwapChain(nativeWindow);
Renderer* renderer   = engine->createRenderer();
Scene* scene         = engine->createScene();
View* view           = engine->createView();

view->setScene(scene);

do {
    // typically we wait for VSYNC and user input events
    if (renderer->beginFrame(swapChain)) {
        renderer->render(view);
        renderer->endFrame();
    }
} while (!quit);

engine->destroy(view);
engine->destroy(scene);
engine->destroy(renderer);
engine->destroy(swapChain);
Engine::destroy(&engine); // clears engine*
```

A complete real app additionally needs a **Camera** (a component on an entity) and at least one renderable in the Scene. Adapted from `samples/hellotriangle.cpp` (which uses the `filamentapp` SDL2 skeleton, so it supplies `engine`/`view`/`scene` via callbacks rather than constructing them inline):

```cpp
// --- setup ---
app.skybox = Skybox::Builder().color({0.1, 0.125, 0.25, 1.0}).build(*engine);
scene->setSkybox(app.skybox);
view->setPostProcessingEnabled(false);

// ... build VertexBuffer / IndexBuffer / Material (see materials + geometry refs) ...

app.renderable = EntityManager::get().create();
RenderableManager::Builder(1)
        .boundingBox({{ -1, -1, -1 }, { 1, 1, 1 }})
        .material(0, app.mat->getDefaultInstance())
        .geometry(0, RenderableManager::PrimitiveType::TRIANGLES, app.vb, app.ib, 0, 3)
        .culling(false)
        .receiveShadows(false)
        .castShadows(false)
        .build(*engine, app.renderable);
scene->addEntity(app.renderable);

app.camera = utils::EntityManager::get().create();
app.cam = engine->createCamera(app.camera);   // Camera is a component on an entity
view->setCamera(app.cam);

// --- per-frame (animate callback) ---
const uint32_t w = view->getViewport().width;
const uint32_t h = view->getViewport().height;
const float aspect = (float) w / h;
app.cam->setProjection(Camera::Projection::ORTHO,
    -aspect * ZOOM, aspect * ZOOM, -ZOOM, ZOOM, 0, 1);

// --- cleanup ---
engine->destroy(app.skybox);
engine->destroy(app.renderable);
engine->destroy(app.mat);
engine->destroy(app.vb);
engine->destroy(app.ib);
engine->destroyCameraComponent(app.camera);          // destroys the Camera component
utils::EntityManager::get().destroy(app.camera);     // then destroy the entity itself
```

Ordering invariants enforced by the headers:

1. `render()` must be called **after** `beginFrame()` and **before** `endFrame()`.
2. If `beginFrame()` returns `true`, you **must** render and call `endFrame()`.
3. If `beginFrame()` returns `false`, skip the frame and do **not** call `endFrame()` (or ignore the return and proceed as if `true`).
4. A `View` with no Camera set makes `Renderer::render()` a no-op.

---

## Engine

### Creating an Engine

`Engine::create` is a backward-compatibility helper that wraps `Engine::Builder`. Backend selection happens here:

```cpp
static inline Engine* create(Backend backend = Backend::DEFAULT,
        Platform* platform = nullptr,
        void* sharedContext = nullptr,
        const Config* config = nullptr);
```

`Backend::DEFAULT` lets Filament pick the platform-appropriate driver (OpenGL/OpenGL ES, Vulkan, Metal, WebGPU/WebGL). `Backend` is `backend::Backend`; other values let you force a specific driver. Returns `nullptr` if the GPU driver couldn't be initialized (e.g. the right OpenGL/GLES version isn't supported). May throw `utils::PostConditionPanic` if there isn't enough memory for the command buffer (fatal abort if exceptions are disabled).

The fluent `Builder` form, equivalent and more expressive:

```cpp
Engine* engine = Engine::Builder()
        .backend(Engine::Backend::VULKAN)   // or DEFAULT / OPENGL / METAL ...
        .config(&config)                     // optional Engine::Config*
        .featureLevel(Engine::FeatureLevel::FEATURE_LEVEL_1)
        .platform(myPlatform)                // optional custom Platform*
        .sharedContext(sharedGlContext)      // optional
        .build();                            // returns nullptr on failure
```

Other Builder methods: `.paused(bool)` (experimental — start the render thread paused), `.feature(name, value)` / `.features({...})` (set feature flags; constant flags can only be set here), `.colorGrading(ColorGrading::Builder const&)`.

**Asynchronous creation** (only when `UTILS_HAS_THREADING`): `Engine::createAsync(callback, user, ...)` or `Builder::build(callback)`, then `Engine::getEngine(token)` from the same thread to retrieve the pointer.

### Engine::Config

Passed to `Builder::config()` / `create(..., config)`. Controls memory footprint. Defaults shown verbatim:

```cpp
struct Config {
    static constexpr uint32_t SINGLE_THREADED = std::numeric_limits<uint32_t>::max();
    uint32_t commandBufferSizeMB        = 3;   // = minCommandBufferSizeMB * 3 (3 frames batched)
    uint32_t perRenderPassArenaSizeMB   = 3;   // main per-frame allocation arena (froxels, hi-level cmds)
    uint32_t driverHandleArenaSizeMB    = 0;   // 0 => platform default
    uint32_t minCommandBufferSizeMB     = 1;
    uint32_t perFrameCommandsSizeMB     = 2;   // ~ number of draw calls per frame
    uint32_t jobSystemThreadCount       = 0;   // 0 => heuristic; SINGLE_THREADED => caller thread
    size_t   metalUploadBufferSizeBytes = 512 * 1024;  // Metal only; 0 disables shared staging buffer
    bool     metalDisablePanicOnDrawableFailure = false;
    bool     disableParallelShaderCompile = false;     // deprecated -> feature flag
    StereoscopicType stereoscopicType   = StereoscopicType::NONE;
    uint8_t  stereoscopicEyeCount       = 2;   // 1..Engine::getMaxStereoscopicEyes()
    uint32_t resourceAllocatorCacheSizeMB = 64;        // deprecated: no longer used
    uint32_t resourceAllocatorCacheMaxAge = 1;
    bool     disableHandleUseAfterFreeCheck = false;   // deprecated -> feature flag
    ShaderLanguage preferredShaderLanguage = ShaderLanguage::DEFAULT; // Metal: DEFAULT/MSL/METAL_LIBRARY
    bool     forceGLES2Context          = false;       // GLES backend only
    bool     assertNativeWindowIsValid  = false;       // deprecated -> feature flag (EGL/Android)
    GpuContextPriority gpuContextPriority = GpuContextPriority::DEFAULT;
    uint32_t sharedUboInitialSizeInBytes = 256 * 64;
    AsynchronousMode asynchronousMode   = AsynchronousMode::NONE;
    uint32_t materialCacheCapacity      = 0;   // LRU cache for material definitions; 0 = immediate destroy
    uint32_t programCacheCapacity       = 0;   // LRU cache for shader programs; 0 = immediate destroy
};
```

Retrieve the active config with `engine->getConfig()`.

### Factory Methods

All return non-null on success (objects are engine-owned):

```cpp
SwapChain* createSwapChain(void* nativeWindow, uint64_t flags = 0) noexcept;  // window-backed
SwapChain* createSwapChain(uint32_t width, uint32_t height, uint64_t flags = 0) noexcept; // headless
Renderer*  createRenderer() noexcept;
View*      createView() noexcept;
Scene*     createScene() noexcept;
Camera*    createCamera(utils::Entity entity) noexcept;      // attaches a Camera component to entity
Camera*    getCameraComponent(utils::Entity entity) noexcept;// nullptr if none
void       destroyCameraComponent(utils::Entity entity) noexcept;
Fence*     createFence() noexcept;
Sync*      createSync() noexcept;
```

Accessors for the shared component managers (not destroyed by you):
`getEntityManager()`, `getRenderableManager()`, `getLightManager()`, `getTransformManager()`, `getJobSystem()`, `getDebugRegistry()`. Also `getDefaultMaterial()` (80% white, LIT shading singleton), `getBackend()` (resolved backend), `getPlatform()`.

### Destruction & Resource Tracking

Two static destroy overloads (both thread-safe):

```cpp
static void destroy(Engine** engine);  // clears *engine to nullptr
static void destroy(Engine* engine);
```

Per-object destroy is overloaded by type and returns `bool` (false if the object wasn't valid). Examples: `engine->destroy(view)`, `engine->destroy(scene)`, `engine->destroy(renderer)`, `engine->destroy(swapChain)`, `engine->destroy(material)`, `engine->destroy(materialInstance)`, `engine->destroy(skybox)`, `engine->destroy(indirectLight)`, plus buffers, textures, render targets, etc. There is also `engine->destroy(utils::Entity e)` which destroys all Filament-known components on that entity.

Order matters: **all `MaterialInstance`s of a `Material` must be destroyed before the `Material`** (otherwise `utils::PreConditionPanic`). And `Engine::destroy(&engine)` runs last of all.

Validity checks: `engine->isValid(ptr)` (per-type), `isValidExpensive(materialInstance)` when the owning Material is unknown. Debug resource counts: `getViewCount()`, `getSceneCount()`, `getSwapChainCount()`, `getMaterialCount()`, `getTextureCount()`, etc.

### Feature Levels

`FeatureLevel` gates which features are available. Default is `FEATURE_LEVEL_0` on devices without GLES 3.0, otherwise `FEATURE_LEVEL_1`. The active level can be raised (never lowered) up to `getSupportedFeatureLevel()`, and cannot change at all if the Engine was initialized at level 0.

```cpp
FeatureLevel getSupportedFeatureLevel() const noexcept;
FeatureLevel setActiveFeatureLevel(FeatureLevel);   // throws/aborts if above supported, or if init at FL0
FeatureLevel getActiveFeatureLevel() const noexcept;
```

Note: post-processing (including MSAA) is disabled at `FEATURE_LEVEL_0` — values passed to `View::setSampleCount`/MSAA options are ignored there.

### Threading & Frame Pumping

- An `Engine` instance is **not thread-safe**. The implementation does not synchronize calls; if you call into it from multiple threads, you must synchronize externally.
- On creation, the Engine starts a render thread plus multiple worker threads at elevated priority. Worker count is chosen automatically; on big.LITTLE it makes educated core-affinity guesses (e.g. keeps the GLES thread on a big core).
- Set `Engine::Config::jobSystemThreadCount` to `Engine::Config::SINGLE_THREADED` to run jobs on the calling thread without a worker pool in CPU-constrained environments.
- `render()` must run on the Engine's main thread (or be externally synchronized); calls to `render()` on different `Renderer`s must be synchronized.
- `flushAndWait()` / `flushAndWait(timeout_ns)` — kick the hardware thread and block until all commands so far are executed (typically used right after destroying a SwapChain). `flush()` — kick without waiting.
- `pumpMessageQueues()` — drain & run pending user callbacks immediately; call once per frame after vsync.
- `execute()` — runs one render-loop iteration; **single-threaded platforms only** (call each time the windowing system needs to paint).
- `hasUnrecoverableFailure()` — poll for a fatal backend error instead of relying on exceptions.
- `setPaused(bool)` / `isPaused()` — experimental; while paused, commands keep queuing and the program aborts when the buffer limit is hit, and buffer callbacks never fire.

---

## SwapChain

A `SwapChain` represents an OS *native* renderable surface. It's created from a native object handed to Filament as a `void*`, so the pointer must be the correct type for the platform. When `Engine::create()` is used with no custom `Platform`, the expected `nativeWindow` types are:

| Platform        | nativeWindow type |
|-----------------|-------------------|
| Android         | `ANativeWindow*`  |
| macOS - OpenGL  | `NSView*`         |
| macOS - Metal   | `CAMetalLayer*`   |
| iOS - OpenGL    | `CAEAGLLayer*`    |
| iOS - Metal     | `CAMetalLayer*`   |
| X11             | `Window`          |
| Windows         | `HWND`            |

Created via the Engine (not a Builder):

```cpp
SwapChain* swapChain = engine->createSwapChain(nativeWindow);          // window-backed
SwapChain* offscreen = engine->createSwapChain(width, height, flags);  // headless / offscreen
```

The **headless** overload takes `width`/`height` in pixels instead of a native window — use it for offscreen rendering with no OS surface. `getNativeWindow()` returns the stored pointer (nullptr for headless).

**Config flags** (`uint64_t`, OR them together for the `flags` arg). All are `static constexpr uint64_t`:

```cpp
SwapChain::CONFIG_TRANSPARENT          // request an alpha channel
SwapChain::CONFIG_READABLE             // allow read-back (source for Renderer::copyFrame)
SwapChain::CONFIG_ENABLE_XCB           // native X11 window is XCB rather than XLIB (Linux only)
SwapChain::CONFIG_APPLE_CVPIXELBUFFER  // native window is a CVPixelBufferRef (Metal only)
SwapChain::CONFIG_SRGB_COLORSPACE      // auto linear->sRGB encoding (needs isSRGBSwapChainSupported)
SwapChain::CONFIG_HAS_STENCIL_BUFFER   // allocate a stencil buffer (needed for View::setStencilBufferEnabled w/o post-proc)
SwapChain::CONFIG_PROTECTED_CONTENT    // protected content (needs isProtectedContentSupported)
SwapChain::CONFIG_MSAA_4_SAMPLES       // 4x MSAA swap chain (needs isMSAASwapChainSupported(4); EGL/Metal)
```

Capability checks (static, take `Engine&`): `isProtectedContentSupported(engine)`, `isSRGBSwapChainSupported(engine)`, `isMSAASwapChainSupported(engine, samples)` — all default to `false`.

Frame-rate control is instance-specific: `isFrameRateChangeSupported()` returns a `utils::tribool` because a newly connected surface can be indeterminate, and `setFrameRate(frameRate, compatibility, strategy)` requests an intended rate. A rate of `0.0f` clears the request.

Frame callbacks (Metal-centric): `setFrameScheduledCallback(handler, callback, flags)` (latched at `endFrame()`; lets the app schedule presentation via the supplied `PresentCallable` — on non-Metal backends the callable is a no-op), and `setFrameCompletedCallback(handler, callback)` (fires when GPU rendering of a frame completes — **only Metal**; other backends ignore it).

---

## Renderer

A `Renderer` represents one OS window and generates the drawing commands. Created with `engine->createRenderer()`, destroyed with `engine->destroy(renderer)`. The per-frame loop is its core responsibility.

```cpp
bool beginFrame(SwapChain* swapChain, uint64_t vsyncSteadyClockTimeNano = 0u);
void render(View const* view);
void endFrame();
```

**`beginFrame(swapChain, vsyncTime)`** sets up the frame and does frame-pacing. It returns whether the frame should be drawn:

- `true` — the frame **must** be rendered and `endFrame()` **must** be called.
- `false` — the GPU is falling behind; the caller should skip the frame and **not** call `endFrame()` (latency-keeping). The caller may instead ignore the return and proceed as if `true`.

`vsyncSteadyClockTimeNano` is the timestamp of the last hardware vsync in the `std::chrono::steady_clock` base (0 if unknown; on Android use the Choreographer frame time). `shouldRenderFrame()` returns the same value as `beginFrame()` without starting a frame. Once a backend exception has been delivered to the main thread, `beginFrame()` returns `false`.

**`render(view)`** is the main CPU-side work; it generates commands for: (1) shadow map passes, (2) depth pre-pass, (3) color pass, (4) post-processing. Must be called *after* `beginFrame()` and *before* `endFrame()`. Cannot be multi-threaded across Renderers (internally it is heavily multi-threaded). Pass multiple Views by calling `render()` once per View within the same begin/end block.

**`endFrame()`** schedules the frame for display. Only call it if `beginFrame()` returned `true` (or if you deliberately ignored a `false`).

Canonical loop (verbatim from `Renderer.h`):

```cpp
void renderLoop(Renderer* renderer, SwapChain* swapChain) {
    do {
        // typically we wait for VSYNC and user input events
        if (renderer->beginFrame(swapChain)) {
            renderer->render(mView);
            renderer->endFrame();
        }
    } while (!quit());
}
```

Use the **same** `swapChain` for every `beginFrame()` call — switching it can lose all or part of the `FrameInfo` history.

Other Renderer surface:
- `setClearOptions(ClearOptions)` — `{ math::double4 clearColor{}; uint8_t clearStencil=0; bool clear=false; bool discard=true; }`. Clears/retains the SwapChain at frame start (does not apply to a View's custom render target). `getClearOptions()`.
- `setDisplayInfo(DisplayInfo)` — `{ float refreshRate=60.0f; ... }` (set refreshRate to 0 for offscreen / to disable frame-pacing) — needed for dynamic resolution + frame-pacing.
- `setFrameRateOptions(FrameRateOptions)` — `{ float headRoomRatio=0; float scaleRate=1/8; uint8_t history=15; uint8_t interval=1; }`.
- `skipFrame(vsyncTime)` / `skipNextFrames(n)` / `getFrameToSkipCount()` — skip frames when the scene is static.
- `setVsyncTime(ns)`, `setPresentationTime(...)`, `setDesiredPresentationTime(...)`, and `setRenderingDeadline(...)` configure frame timing before `endFrame()`; each presentation/deadline API accepts raw steady-clock nanoseconds or a `std::chrono::steady_clock::time_point`.
- `copyFrame(dstSwapChain, dstViewport, srcViewport, flags)` — flags `COMMIT` / `SET_PRESENTATION_TIME` / `CLEAR`; call after `render()` before `endFrame()`.
- `readPixels(...)` (SwapChain or a RenderTarget) — debug/testing; significant perf impact; within a frame.
- `renderStandaloneView(view)` — renders a View into its associated RenderTarget *outside* begin/end (lower overhead; a poor-man's compute).
- `getFrameInfoHistory(n)` / `getMaxFrameHistorySize()` — frame timing telemetry.
- `getMaterialTime()` / `setMaterialTimeEpoch(...)` — the material clock and its steady-clock epoch. The deprecated `getUserTime()` / `resetUserTime()` C++ methods remain compatibility helpers; materials still read the encoded clock through the shader function `getUserTime()`.
- `hasGpuFallenBehind()`, `setFrameScheduleTime(...)`, and `pauseRenderThread(duration_ns)` support manual pacing and latency testing.

---

## View

A `View` is everything needed to render a Scene — effectively one render pass. Views are heavy (they cache a lot of render state), so use few of them (e.g. one for the 3D scene, one for the UI). Created with `engine->createView()`, destroyed with `engine->destroy(view)`.

Core bindings (no reference-counting — the View only holds references):

```cpp
void   setScene(Scene* scene);              // nullptr to dissociate
Scene* getScene() noexcept;
void   setCamera(Camera* camera) noexcept;  // nullptr => render() is a no-op
bool   hasCamera() const noexcept;
Camera& getCamera() noexcept;               // UB if !hasCamera()
void   setViewport(Viewport const& viewport) noexcept;   // where the scene is drawn (value type, copied)
Viewport const& getViewport() const noexcept;
void   setRenderTarget(RenderTarget* rt) noexcept;       // nullptr => the engine's SwapChain (default)
void   setName(const char* name) noexcept;               // debugging only
```

Quality / post-processing / effects (most are off by default unless noted; setters mirror getters):

```cpp
void setPostProcessingEnabled(bool enabled) noexcept;        // ON by default; off forgoes color correctness
void setBlendMode(BlendMode) noexcept;                       // OPAQUE | TRANSLUCENT
void setAntiAliasing(AntiAliasing type) noexcept;            // FXAA (default) | NONE  (post-process AA)
void setMultiSampleAntiAliasingOptions(MultiSampleAntiAliasingOptions) noexcept;  // MSAA, off by default
void setTemporalAntiAliasingOptions(TemporalAntiAliasingOptions) noexcept;        // TAA, off by default
void setAmbientOcclusionOptions(AmbientOcclusionOptions const&) noexcept;         // SSAO
void setBloomOptions(BloomOptions) noexcept;                 // off by default
void setFogOptions(FogOptions) noexcept;                     // off by default
void setDepthOfFieldOptions(DepthOfFieldOptions) noexcept;   // off by default
void setVignetteOptions(VignetteOptions) noexcept;          // off by default
void setDithering(Dithering) noexcept;                       // ON by default
void setScreenSpaceReflectionsOptions(ScreenSpaceReflectionsOptions) noexcept;    // off by default
void setColorGrading(ColorGrading* colorGrading) noexcept;   // nullptr => default grading
void setRenderQuality(RenderQuality const&) noexcept;
void setDynamicResolutionOptions(DynamicResolutionOptions const&) noexcept;
void setShadowingEnabled(bool) noexcept;                     // ON by default
void setShadowType(ShadowType) noexcept;                     // PCF, VSM, or PCSS; DPCF is deprecated and falls back to PCSS
void setStencilBufferEnabled(bool) noexcept;                 // needs CONFIG_HAS_STENCIL_BUFFER if no post-proc
void setStereoscopicOptions(StereoscopicOptions const&) noexcept;
```

Note: `setSampleCount(uint8_t)` / `getSampleCount()` are **deprecated** — use the MSAA options instead. The detailed semantics of bloom/DoF/vignette/color-grading and exposure are in `concepts-imaging-pipeline.md`.

Visibility & misc: `setVisibleLayers(select, values)` / `setLayerEnabled(layer, enabled)` (8 layers; only layer 0 visible by default), `setFrontFaceWindingInverted(bool)`, `setDynamicLightingOptions(zLightNear, zLightFar)` (defaults 5m / 100m), and `getVisibleRenderableCount()` (returns the most recent rendered count, or `-1` before a valid render). Picking: the templated `pick(x, y, ...)` family enqueues a query resolved during the next `render()` (results arrive a couple frames later). Debug: `setFrustumCullingEnabled(bool)`, `setDebugCamera(Camera*)`, `setFroxelVizEnabled(bool)`. Temporal history: `clearFrameHistory(engine)` when switching Renderer or on a hard scene cut (avoids TAA/SSR ghosting).

---

## Scene

A `Scene` is a **flat container** of renderable and light entities — not a scene-graph (hierarchy/transforms live in `TransformManager`). A renderable must be added to a Scene to be drawn, and that Scene must be bound to a View. Created with `engine->createScene()`, destroyed with `engine->destroy(scene)`.

```cpp
void setSkybox(Skybox* skybox) noexcept;           // drawn last, fills untouched pixels; nullptr to unset
Skybox* getSkybox() const noexcept;
void setIndirectLight(IndirectLight* ibl) noexcept;// one IBL per scene; replaces current; nullptr to unset
IndirectLight* getIndirectLight() const noexcept;

void addEntity(utils::Entity entity);              // ignored at render time if no Renderable/Light component
void addEntities(const utils::Entity* entities, size_t count);
void remove(utils::Entity entity);                 // ignored if not present
void removeEntities(const utils::Entity* entities, size_t count);
void removeAllEntities() noexcept;

size_t getEntityCount() const noexcept;            // all entities, alive or not
size_t getRenderableCount() const noexcept;        // alive renderables
size_t getLightCount() const noexcept;             // alive lights
bool   hasEntity(utils::Entity entity) const noexcept;
void   forEach(utils::Invocable<void(utils::Entity)>&& functor) const noexcept; // no add/remove inside
```

An entity is only meaningful to the Scene if it carries a Renderable or Light component; a given entity can be added only once. Entities can be added/removed at any time. (IBL setup details live in the lighting reference.)

---

## Camera

A `Camera` is a **component on an entity**, not a free object. Create it with `engine->createCamera(entity)` and destroy it with `engine->destroyCameraComponent(entity)` — then destroy the entity itself via the `EntityManager`. It holds position/orientation (its transform component), the projection, and exposure. The camera looks down its **-z axis**, with +y up and +x right (right-handed view space).

```cpp
filament::Engine* engine = filament::Engine::create();
utils::Entity cameraEntity = utils::EntityManager::get().create();
filament::Camera* camera = engine->createCamera(cameraEntity);
camera->setProjection(45, 16.0/9.0, 0.1, 1.0);   // fov, aspect, near, far
camera->lookAt({0, 1.60, 1}, {0, 0, 0});         // eye, center
// ...
engine->destroyCameraComponent(cameraEntity);
```

**Projection.** Two enums drive it: `Projection { PERSPECTIVE, ORTHO }` and `Fov { VERTICAL, HORIZONTAL }`.

```cpp
// FOV-based perspective/ortho convenience:
void setProjection(double fovInDegrees, double aspect, double near, double far,
                   Fov direction = Fov::VERTICAL);    // 0 < fov < 180, aspect > 0, near > 0, far > near

// Six-plane frustum form (used by hellotriangle for ORTHO):
void setProjection(Projection projection,
                   double left, double right,
                   double bottom, double top,
                   double near, double far);

// Lens / focal-length form:
void setLensProjection(double focalLengthInMillimeters, double aspect, double near, double far);

// Fully custom matrices (NDC must be OpenGL convention, all axes [-1, 1]):
void setCustomProjection(math::mat4 const& projection, double near, double far);
void setCustomProjection(math::mat4 const& projection, math::mat4 const& projectionForCulling,
                         double near, double far);
void setCustomEyeProjection(math::mat4 const* projection, size_t count,
                            math::mat4 const& projectionForCulling, double near, double far); // stereo
```

The **far plane is always internally infinity for rendering** (for depth precision); the finite `far` you pass is used only for culling/shadows. `getProjectionMatrix(eyeId=0)` returns the render matrix (infinite far); `getCullingProjectionMatrix()` returns the finite one. Pick the **largest near** distance you can — depth precision drops sharply as near shrinks (much less so on Vulkan/Metal/clip-control GL). Keep a near:far ratio roughly between 1:100 and 1:100000. `setScaling(double2)` / `setShift(double2)` adjust the projection after the fact (e.g. aspect correction).

**Transform / pose.**

```cpp
void lookAt(math::double3 const& eye, math::double3 const& center,
            math::double3 const& up = {0, 1, 0}) noexcept;
void setModelMatrix(const math::mat4& modelMatrix) noexcept;   // rigid transform; equivalent to setting
void setModelMatrix(const math::mat4f& modelMatrix) noexcept;  // the entity's TransformManager transform
math::mat4 getModelMatrix() const noexcept;
math::mat4 getViewMatrix() const noexcept;                     // inverse of model matrix
math::double3 getPosition() const noexcept;
math::float3 getForwardVector() const noexcept;  // also getLeftVector/getUpVector
utils::Entity getEntity() const noexcept;
```

**Exposure** (the Camera sets the scene's brightness, like a real camera — full treatment in `concepts-imaging-pipeline.md`):

```cpp
// Default exposure is f/16, 1/125s, 100 ISO (sunny outdoor at zenith).
void setExposure(float aperture, float shutterSpeed, float sensitivity) noexcept;
//   aperture: f-stops, clamped 0.5..64 (lower = brighter); realistic 0.95..32
//   shutterSpeed: seconds, clamped 1/25000..60 (lower = brighter); realistic 1/8000..30
//   sensitivity: ISO, clamped 10..204800 (higher = brighter); realistic 50..25600
void setExposure(float exposure) noexcept;   // direct: sets aperture=1.0, shutter=1.2, ISO from exposure
float getAperture() const noexcept;          // also getShutterSpeed(), getSensitivity()
```

With default exposure the scene needs at least one sun-like light (e.g. a ~100,000 lux directional light) to be visible. Depth-of-field focus: `setFocusDistance(float)` / `getFocusDistance()`. Statics: `Camera::projection(...)`, `Camera::inverseProjection(...)`, `Camera::computeEffectiveFocalLength(...)`, `Camera::computeEffectiveFov(...)`.

---

## Common Pitfalls

- **Forgetting the per-frame `beginFrame()` guard.** Calling `render()`/`endFrame()` unconditionally breaks frame-pacing and is undefined after `beginFrame()` returns `false`.
- **Destroy ordering.** Destroy every created object via `engine->destroy(...)`, then `Engine::destroy(&engine)` last. Destroy all `MaterialInstance`s before their `Material`. Destroy the Camera component *and* its entity.
- **No Camera on the View.** `Renderer::render()` silently no-ops if the View has no Camera.
- **Cross-thread Engine calls.** The Engine is not thread-safe; `render()` runs on the main thread, and concurrent Renderers must be synchronized externally.
- **Wrong `nativeWindow` type.** The `void*` must match the platform/backend (e.g. `CAMetalLayer*` for macOS Metal, `NSView*` for macOS OpenGL).
- **Switching SwapChains mid-loop.** Use one SwapChain per `beginFrame()`; switching loses FrameInfo history.
- **Too-small near plane.** Crushes depth precision on OpenGL; prefer the largest near you can afford and a sane near:far ratio.
- **Forgetting post-processing is off at FL0.** MSAA and other post-process options are ignored at `FEATURE_LEVEL_0`.
