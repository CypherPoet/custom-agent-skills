# How Do I…? Task Index & Gotchas

> Source: Synthesized task index over the other references, Filament v1.75.0
> Last synced: 2026-08-14

A goal-oriented map: find the task, jump to the reference(s), and heed the gotcha that bites people first. "Engine API" tasks are binding-agnostic in shape — translate the calls with [`cross-platform-matrix.md`](cross-platform-matrix.md).

## Get something on screen

| Goal | Read | Gotcha |
|---|---|---|
| Render my first triangle | [`platform-*`](platform-cpp.md) for setup + [`engine-api-core.md`](engine-api-core.md) | The frame loop order is `beginFrame` → `render(view)` → `endFrame`; skip rendering when `beginFrame` returns false. |
| Set up Engine/Renderer/View/Scene/Camera | [`engine-api-core.md`](engine-api-core.md) | The `Engine` owns and must `destroy(...)` every object; destroy the Engine last. |
| Draw a mesh with vertices/indices | [`engine-api-resources.md`](engine-api-resources.md) + [`engine-api-entities-components.md`](engine-api-entities-components.md) | A renderable needs a correct **bounding box** or frustum culling drops it; `boundingBox({center, halfExtent})`, not min/max corners. |
| Load a 3D model | glTF/GLB → [`assets-gltf.md`](assets-gltf.md); `.filamesh` → [`tooling.md`](tooling.md) (filamesh) | `gltfio` is a separate library/dependency. Convert OBJ/etc. to `.filamesh` with the `filamesh` tool, or load glTF via `gltfio`. |

## Materials & looks

| Goal | Read | Gotcha |
|---|---|---|
| Author a custom material | [`materials-definition-language.md`](materials-definition-language.md) → compile with [`materials-compiling-matc.md`](materials-compiling-matc.md) | A `.mat` is compiled to a `.filamat` by `matc` **before** runtime; the engine loads the `.filamat`, not the `.mat`. |
| Choose a shading model (lit/unlit/cloth/…) | [`materials-models.md`](materials-models.md) | Use `unlit` only when you truly want no lighting; most surfaces are `lit`. |
| Make metal vs. plastic vs. dielectric | [`concepts-pbr-shading.md`](concepts-pbr-shading.md) | `metallic` is effectively binary (0 or 1); for non-metals tune `reflectance` (default ~0.5 ≈ 4% F0), not `metallic`. |
| Make glass / transparent / refractive | [`materials-models.md`](materials-models.md) (refraction) + [`materials-definition-language.md`](materials-definition-language.md) (`blending`, `refractionMode`, `refractionType`, `ior`, `transmission`) | Refraction needs `refractionMode` set in the `.mat`; alpha `blending` alone is not refraction. |
| Exact property name / range / default | [`materials-properties-reference.md`](materials-properties-reference.md) | Property names are case-sensitive camelCase; ranges are 0..1 unless the table says otherwise. |
| Texture a material | [`engine-api-resources.md`](engine-api-resources.md) (Texture + TextureSampler) + [`materials-definition-language.md`](materials-definition-language.md) (sampler params) | sRGB color textures must use an sRGB internal format; data textures (normal/roughness) must be linear. |

## Lighting

| Goal | Read | Gotcha |
|---|---|---|
| Light a scene with a sun/directional light | [`concepts-lighting-ibl.md`](concepts-lighting-ibl.md) + [`engine-api-entities-components.md`](engine-api-entities-components.md) | Sun intensity is in **lux** (e.g. ~100,000), not 0–1. A value of `1.0` is essentially black under default exposure. |
| Add point/spot lights | [`concepts-lighting-ibl.md`](concepts-lighting-ibl.md) | Point/spot intensity is in **lumens** (or candela) — a household bulb is ~800 lm. |
| Add image-based / environment lighting | [`concepts-lighting-ibl.md`](concepts-lighting-ibl.md) + [`tooling.md`](tooling.md) (cmgen) | You **cannot** feed a raw `.hdr`/`.exr` to `IndirectLight`. Pre-process it with `cmgen` (or `iblprefilter`) into a prefiltered KTX + spherical harmonics first. |
| Show the environment as a background | [`concepts-lighting-ibl.md`](concepts-lighting-ibl.md) (Skybox) | The skybox cubemap is a separate `_skybox.ktx` from the `_ibl.ktx` reflections map. |

## Camera, exposure & color

| Goal | Read | Gotcha |
|---|---|---|
| Set up a camera / projection | [`engine-api-core.md`](engine-api-core.md) (Camera) | Right-handed, +Y up, meters, looks down −Z. |
| Control exposure / brightness | [`concepts-imaging-pipeline.md`](concepts-imaging-pipeline.md) | Exposure is photographic (aperture/shutter/ISO). Brightness is the interplay of light units **and** exposure — change one deliberately, not both. |
| Tone mapping / color grading / bloom | [`concepts-imaging-pipeline.md`](concepts-imaging-pipeline.md) | These are `View`/`ColorGrading`/`ToneMapper` options, not material settings. |

## Platform setup

| Goal | Read |
|---|---|
| Set up a C++ / iOS project | [`platform-cpp.md`](platform-cpp.md) |
| Set up a web / browser project | [`platform-web.md`](platform-web.md) |
| Set up an Android project | [`platform-android.md`](platform-android.md) |
| Translate a snippet between bindings | [`cross-platform-matrix.md`](cross-platform-matrix.md) |

## Debugging checklist

**"My scene is black / nothing renders"** — work down this list (most common first):

1. **Lights too dim for the exposure.** With physical units + the default camera exposure (~f/16, 1/125s, ISO 100), a sun needs ~100,000 lux and a bulb ~hundreds of lumens. An intensity of `1.0` renders black. → [`concepts-lighting-ibl.md`](concepts-lighting-ibl.md), [`concepts-imaging-pipeline.md`](concepts-imaging-pipeline.md)
2. **No light and no IBL** in the scene at all (a `lit` material with zero illumination is black). Add a light or an `IndirectLight`.
3. **Renderable culled** — missing/incorrect bounding box, or the camera isn't pointed at it / near-far clip excludes it. → [`engine-api-entities-components.md`](engine-api-entities-components.md)
4. **Entity never added to the scene**, or the `View` isn't bound to that `Scene` + `Camera`.
5. **Material/asset not actually loaded** — wrong path, or a `.filamat` built for the wrong feature level / API variant. → [`materials-compiling-matc.md`](materials-compiling-matc.md)
6. **You rendered when `beginFrame` returned false** (C++/Android), or touched the engine before `onReady`/`Filament.init` resolved (web). → [`cross-platform-matrix.md`](cross-platform-matrix.md)

**"Render is washed out / too dark / wrong colors"** — usually exposure vs. light-unit mismatch, or a linear-vs-sRGB texture/format mistake. → [`concepts-imaging-pipeline.md`](concepts-imaging-pipeline.md), [`materials-compiling-matc.md`](materials-compiling-matc.md) (color handling)

**"Performance / frame time"** — Filament is clustered-forward, so many lights are cheap; look at overdraw, texture sizes, shadow settings, and the profiling guidance in [`tooling.md`](tooling.md). Inspect compiled materials/variants with `matinfo`; debug live shaders with `matdbg`.
