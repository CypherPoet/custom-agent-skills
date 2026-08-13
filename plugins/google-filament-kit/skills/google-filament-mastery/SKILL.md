---
name: google-filament-mastery
description: >
  Use whenever the user is building or debugging anything in Google Filament —
  the real-time physically-based rendering engine — in C++, on the web
  (filament.js), or on Android. Covers the Engine/Scene/View/Renderer API,
  renderables and GPU resources, .mat/matc materials, PBR parameters and shading
  models, physically-correct lighting and IBL, tone mapping, glTF loading, and
  the CLI tools (cmgen, filamesh, matinfo). Trigger even when "Filament" isn't
  named but the user pastes Filament code or works with .filamat/.filamesh
  files. For raw WebGL use webgl-mastery; for Three.js, threejs-mastery.
---

# Google Filament Mastery

*Distilled from the official [Filament documentation](https://google.github.io/filament/) and the `google/filament` source at tag **v1.72.0** (released 2026-06-17).*

Working knowledge of [Google Filament](https://github.com/google/filament) — a real-time **physically-based** rendering engine for C++ (desktop/iOS), the web (WebAssembly over WebGL2), and Android. Use this to write correct, idiomatic Filament code, author and compile materials, light scenes with real photometric units, load assets, and explain the rendering model — grounded in the docs, not training-data guesses.

## Mental Model (read this first — it prevents most mistakes)

- **Everything is physical.** Lights are set in **lux** (directional/sun) or **lumens/candela** (point/spot) — *not* a 0–1 slider. The camera has a photographic **exposure** (aperture / shutter / ISO, default ≈ f/16, 1/125s, ISO 100). The single most common "it renders black" cause is a light intensity that's tiny for that exposure (a sun is ~100,000 lux, not `1.0`). Brightness is the *interplay* of light units and exposure — change one deliberately.
- **The `Engine` owns everything.** Every object is built with a `Builder` and created through the `Engine`; you must `destroy(...)` each one, and destroy the `Engine` last. There's no garbage collector for native resources (especially on Android).
- **The render graph is fixed:** `Engine` → `Renderer` → `View`, where a `View` binds a `Scene` (renderables + lights + skybox/IBL) + a `Camera` + a `Viewport`. The per-frame loop is `beginFrame` → `render(view)` → `endFrame`.
- **Materials and data are pre-compiled.** You author a `.mat` and compile it to a `.filamat` with **`matc`**; the engine loads the `.filamat`. Environments are pre-processed into IBL KTX + spherical harmonics by **`cmgen`** (you cannot feed a raw `.hdr`). Meshes are converted to `.filamesh` (or loaded as glTF via `gltfio`).
- **The model is identical across bindings;** only bootstrap, the window/surface, the frame driver, and the asset-loading helpers differ between C++, web, and Android.

## Identify the Platform First

Filament's concepts (PBR, lighting, materials, the render graph) are the same everywhere, but **setup, the surface/SwapChain, the frame driver, and asset loading are binding-specific.** Before writing setup or asset code, determine whether the target is **C++ (desktop/iOS)**, **Web (filament.js)**, or **Android (Kotlin/Java)** — if unspecified, ask, or state the assumption. Load the matching `platform-*.md`. For pure concept/material questions, the platform usually doesn't matter; use [`cross-platform-matrix.md`](references/cross-platform-matrix.md) to translate a snippet between bindings.

## Reference Files

Load only the rows the question touches — usually one or two files. Each reference is a dense, source-grounded cluster; signatures are quoted from the v1.72.0 headers/docs.

| Asking about… | Read |
|---|---|
| Where do I start? "How do I…?" task lookup, debugging a black/washed-out render, performance | [`references/how-do-i.md`](references/how-do-i.md) |
| Translating a snippet between C++ / Web / Android; what differs per binding | [`references/cross-platform-matrix.md`](references/cross-platform-matrix.md) |
| The PBR theory: BRDF, metallic/roughness/reflectance, clear coat, anisotropy, cloth, subsurface — and *why* | [`references/concepts-pbr-shading.md`](references/concepts-pbr-shading.md) |
| Lighting: physical units, directional/point/spot lights, IBL, skyboxes, occlusion, normal mapping | [`references/concepts-lighting-ibl.md`](references/concepts-lighting-ibl.md) |
| Camera & exposure, tone mapping, color grading, bloom, clustered-forward rendering, coordinate/color conventions | [`references/concepts-imaging-pipeline.md`](references/concepts-imaging-pipeline.md) |
| Choosing/understanding a shading model (lit, unlit, cloth, subsurface, specularGlossiness) | [`references/materials-models.md`](references/materials-models.md) |
| Writing a `.mat` file: material/vertex/fragment blocks, keys + allowed values, shader APIs, an example | [`references/materials-definition-language.md`](references/materials-definition-language.md) |
| Exact property name / type / range / default for a material parameter | [`references/materials-properties-reference.md`](references/materials-properties-reference.md) |
| Compiling materials with `matc` (flags, variants, feature levels), runtime `filamat`, color handling | [`references/materials-compiling-matc.md`](references/materials-compiling-matc.md) |
| Engine / SwapChain / Renderer / View / Scene / Camera lifecycle and the render loop | [`references/engine-api-core.md`](references/engine-api-core.md) |
| Entities & component managers: RenderableManager, LightManager, TransformManager, bounding boxes | [`references/engine-api-entities-components.md`](references/engine-api-entities-components.md) |
| GPU resources: VertexBuffer, IndexBuffer, Texture/TextureSampler, Material, MaterialInstance, Skybox, IndirectLight | [`references/engine-api-resources.md`](references/engine-api-resources.md) |
| Loading glTF / GLB with `gltfio` (AssetLoader, ResourceLoader, Animator); `.filamesh` vs glTF | [`references/assets-gltf.md`](references/assets-gltf.md) |
| Setting up a C++ / iOS project (SDK, linking, native-window SwapChain, CocoaPods/Metal) | [`references/platform-cpp.md`](references/platform-cpp.md) |
| Setting up a web project (filament.js init, canvas, JS API, loading KTX/IBL/mesh, RAF loop) | [`references/platform-web.md`](references/platform-web.md) |
| Setting up an Android project (Maven deps, UiHelper/SurfaceView, Choreographer, KTX1Loader) | [`references/platform-android.md`](references/platform-android.md) |
| Command-line tools (cmgen, filamesh, mipgen, matinfo, specgen) and debuggers (matdbg, FrameGraph) | [`references/tooling.md`](references/tooling.md) |

## Core Workflows

These are the common multi-step jobs. Each names the references to pull; don't load the whole corpus.

### Stand up a Filament app
1. Identify the platform → load the matching `platform-*.md` for SDK/deps, the surface/SwapChain, and the frame driver.
2. Load [`engine-api-core.md`](references/engine-api-core.md) for the `Engine → Renderer → View(Scene, Camera)` graph and the `beginFrame`/`render`/`endFrame` loop.
3. Add geometry + a light: [`engine-api-entities-components.md`](references/engine-api-entities-components.md) and [`engine-api-resources.md`](references/engine-api-resources.md).
4. **Set a real light intensity and confirm exposure** before assuming anything is wrong — see the Mental Model.

### Author and use a material
1. Write the `.mat` with [`materials-definition-language.md`](references/materials-definition-language.md); pick the model via [`materials-models.md`](references/materials-models.md) and exact params via [`materials-properties-reference.md`](references/materials-properties-reference.md).
2. Compile it to `.filamat` with `matc` — [`materials-compiling-matc.md`](references/materials-compiling-matc.md) (choose platform/API variants and feature level deliberately).
3. Load it at runtime as a `Material`, create a `MaterialInstance`, set parameters — [`engine-api-resources.md`](references/engine-api-resources.md).

### Light a scene (and add an environment)
1. Direct lights with **physical units** + the `LightManager.Builder` — [`concepts-lighting-ibl.md`](references/concepts-lighting-ibl.md), [`engine-api-entities-components.md`](references/engine-api-entities-components.md).
2. For image-based lighting, pre-process the `.hdr`/`.exr` with **`cmgen`** ([`tooling.md`](references/tooling.md)) into an IBL KTX + SH, then build an `IndirectLight` and (optionally) a `Skybox` — [`concepts-lighting-ibl.md`](references/concepts-lighting-ibl.md).

### Load a model
- glTF/GLB → `gltfio` (`AssetLoader` → `ResourceLoader` → add entities → drive `Animator`): [`assets-gltf.md`](references/assets-gltf.md).
- Other formats → convert to `.filamesh` with the `filamesh` tool ([`tooling.md`](references/tooling.md)), then load it.

### Debug a render
Start at the **debugging checklist** in [`how-do-i.md`](references/how-do-i.md) — black-screen and washed-out-color causes are ordered by likelihood (lights-too-dim-for-exposure is #1). Inspect compiled materials with `matinfo`; debug live shaders with `matdbg` ([`tooling.md`](references/tooling.md)).

## Accuracy Notes

A few things the upstream v1.72.0 docs leave incomplete — don't fill them with guesses:

- The **subsurface** material model and **area lights** are `[TODO]` placeholders in the official docs; their properties are named but not fully specified, and there is no area-light `LightManager::Type`. Say so rather than inventing an API.
- `matc`'s documented `--api` values are `opengl`, `vulkan`, `all` — the CLI docs don't list `metal` even though the engine renders with Metal (the `filamat` `TargetApi::ALL` covers it).
- Filament versions move fast; if exact current behavior matters, verify against the installed version's headers.
