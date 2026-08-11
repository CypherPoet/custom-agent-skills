# Cross-Platform Matrix: C++ vs Web vs Android

> Source: Synthesized from the platform references (platform-cpp / platform-web / platform-android), Filament v1.72.0
> Last synced: 2026-06-19

Filament's **rendering model is identical across bindings** — the same `Engine` → `Renderer` → `View` (+ `Scene`, `Camera`) graph, the same physical light units, the same compiled asset formats (`.filamat`, `.ktx`/`.ktx2`, `.filamesh`, glTF). What differs is the bootstrap, the surface/window, the frame driver, and the asset-loading helpers. Use this table to translate a snippet from one binding to another; load the matching `platform-*.md` for full code.

| Concern | C++ (desktop/iOS) | Web (filament.js) | Android (Kotlin/Java) |
|---|---|---|---|
| Language | C++17 | JavaScript | Kotlin / Java |
| Get the SDK | Prebuilt release archive, or build from source (`build.sh`) | `filament.js` + `filament.wasm` (npm / release) | Maven: `com.google.android.filament:filament-android:1.72.0` (+ `gltfio-android`, `filament-utils-android`, `filamat-android`) |
| One-time init | none | `Filament.init([asset urls], onReady)` — fetches assets, then runs your callback | `Filament.init()` (loads the native lib) |
| Backend | `Engine::create(Backend::OPENGL\|VULKAN\|METAL)` | WebGL2 (or `Filament.initWebGPU`) | GLES/Vulkan, auto-selected |
| Create Engine | `Engine::create(backend)` | `Filament.Engine.create(canvas)` | `Engine.create()` |
| Surface / SwapChain | `engine->createSwapChain(nativeWindow)` — a platform `void*` (NSView/CAMetalLayer, HWND, X11 window) | implicit from the `<canvas>` passed to `Engine.create` | `UiHelper` + `SurfaceView`/`TextureView`; `engine.createSwapChain(surface)` in the `RendererCallback` |
| Frame driver | your app loop (SDL/GLFW/native) | `requestAnimationFrame` | `Choreographer.postFrameCallback` |
| Frame call | `renderer.beginFrame(swapChain)` → `render(view)` → `endFrame()` | `renderer.render(swapChain, view)` inside the RAF loop | `renderer.beginFrame(swapChain, frameTimeNanos)` → `render(view)` → `endFrame()` |
| Load material (`.filamat`) | `Material::Builder().package(data,size)` | `engine.createMaterial(filamatUrl)` | `Material.Builder().payload(buffer, size)` |
| Load texture (`.ktx`) | KtxReader / `image` libs | `engine.createTextureFromKtx1/2(...)` | `KTX1Loader.createTexture(engine, buffer, opts)` |
| Load IBL + skybox | `iblprefilter` / KtxReader | `Filament.createIblFromKtx1`, `createSkyFromKtx1` | `KTX1Loader.createIndirectLight(...)`, `createSkybox(...)` |
| Load mesh (`.filamesh`) | `filamesh::MeshReader` | `engine.loadFilamesh(url, mat)` | `filament-utils` mesh loader (sample-side `loadMesh`) |
| Load glTF/GLB | `gltfio` C++ (`AssetLoader`/`ResourceLoader`) — see [`assets-gltf.md`](assets-gltf.md) | gltfio JS binding (`loadGltf`) | `gltfio-android` (`AssetLoader`/`ResourceLoader`) |
| Cleanup | `engine->destroy(obj)` each; `Engine::destroy(&engine)` last | `engine.destroy*` (also helps free wasm memory) | `engine.destroy*` / `engine.destroyEntity` — **mandatory**; native objects aren't GC'd |

## Things that are the SAME everywhere

- **Physical light units.** A directional sun is set in **lux** (e.g. ~100,000+), point/spot lights in **lumens/candela** — never a 0–1 intensity — on every binding. See [`concepts-lighting-ibl.md`](concepts-lighting-ibl.md).
- **Exposure.** The camera uses photographic exposure (aperture / shutter / ISO, default ~f/16, 1/125s, ISO 100). If the scene is black, it's almost always too-dim lights for that exposure, not a binding bug. See [`concepts-imaging-pipeline.md`](concepts-imaging-pipeline.md).
- **Asset pipeline.** `matc` (materials), `cmgen` (IBL), `filamesh` (meshes), `mipgen` produce binaries consumed identically by all three bindings. See [`tooling.md`](tooling.md).
- **Material model & `.mat` language.** One `.mat` compiles to a `.filamat` that runs on all platforms (subject to the target feature level / API variants chosen at `matc` time). See [`materials-definition-language.md`](materials-definition-language.md).
- **Coordinate system.** Right-handed, +Y up, units in meters, camera looks down −Z.

## Binding-specific gotchas

- **Android:** every Filament object you create must be explicitly destroyed through the `Engine`; there is no finalizer safety net, and leaking the `Engine` leaks native memory. Bundle Filament assets **uncompressed** in the APK (`noCompress` for `filamat`/`ktx`/`filamesh`) so they can be `mmap`/`openFd`'d.
- **Web:** assets must be fetched before use — pass them to `Filament.init([...])` (or `Filament.fetch`) and only touch the engine in the `onReady` callback. Serve over HTTP (not `file://`) and respect CORS. Requires WebGL2.
- **C++ / iOS:** the SwapChain's native-window pointer is platform-specific (CAMetalLayer on iOS/Metal, NSView on macOS, HWND on Windows). iOS ships via CocoaPods (`pod 'Filament', '~> 1.72.0'`) and uses the Metal backend; the render code is typically Objective-C++.
