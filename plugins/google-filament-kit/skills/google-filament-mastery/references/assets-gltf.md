# Loading Assets: glTF / GLB (gltfio)

> Source: Filament gltfio library (public headers) + web suzanne tutorial + C++ sample, Filament v1.75.0
> Last synced: 2026-08-14

## Table of Contents

| Section | Covers |
|---|---|
| [The short version](#the-short-version) | How `gltfio` turns glTF and GLB assets into Filament entities and resources |
| [gltfio is a separate library, not core Filament](#gltfio-is-a-separate-library-not-core-filament) | Why `gltfio` is separate from core Filament and which assets its loader returns |
| [The gltfio object model](#the-gltfio-object-model) | `AssetLoader`, `ResourceLoader`, `MaterialProvider`, and `TextureProvider` roles, ownership, implementations, and threading constraints |
| [The canonical end-to-end C++ load flow](#the-canonical-end-to-end-c-load-flow) | This is the worked example from the `AssetLoader.h` docstring (quoted) |
| [The ubershader archive (.uberz) toolchain](#the-ubershader-archive-uberz-toolchain) | Building and loading precompiled `.uberz` shader archives |
| [Texture compression & mesh compression](#texture-compression--mesh-compression) | First-class KTX2 and Basis texture-provider support and sample encodings; Draco and meshopt geometry support remains unverified |
| [IMPORTANT: filamesh is NOT glTF](#important-filamesh-is-not-gltf) | This is the single most important accuracy point in this corpus |
| [What the Filament v1.75.0 samples actually load](#what-the-filament-v1750-samples-actually-load) | C++ sample (samples/suzanne.cpp) — filamesh + KTX2 and Web tutorial (web/suzanne) — filamesh + KTX2 |
| [What is verified vs not in this file](#what-is-verified-vs-not-in-this-file) | Verified — quoted from the v1.75.0 gltfio public headers and corpus files |

---

## The short version

- **`gltfio`** is the library that consumes `.gltf` / `.glb` content and produces Filament objects. It is a **separate dependency**, not part of core `filament`.
- It plugs together: an **`AssetLoader`** (parses glTF 2.0, builds Filament entities + a `MaterialInstance` per primitive), a **`ResourceLoader`** (fetches external buffers and creates/uploads vertex buffers + `Texture` objects), a **`MaterialProvider`** (supplies the Filament materials the glTF needs — prebuilt ubershaders or JIT-compiled), and a **`TextureProvider`** (decodes image data into Filament `Texture` objects).
- The whole API lives in namespace **`filament::gltfio`**. The canonical call sequence is `create providers → AssetLoader::create → createAsset(bytes) → ResourceLoader::loadResources → scene->addEntities(asset->getEntities(), …) → asset->releaseSourceData() → Animator per frame → destroyAsset / destroy loaders`. See [The canonical end-to-end C++ load flow](#the-canonical-end-to-end-c-load-flow).
- **Neither the C++ Suzanne sample nor the web Suzanne tutorial in this corpus uses gltfio.** Both load Filament's own **`filamesh`** binary mesh format instead. See [IMPORTANT: filamesh is NOT glTF](#important-filamesh-is-not-gltf).

---

## gltfio is a separate library, not core Filament

Direct from the gltfio README:

> `gltfio` is a loader library that consumes `gltf` or `glb` content and produces Filament objects. For usage details, see the docstring for `AssetLoader`.

Implications:

- Core `filament` has **no asset-loading system** for scene graphs. The web tutorial states this plainly about the engine itself:

  > Filament does not have an asset loading system, but it does provide a binary mesh format called `filamesh` for simple use cases.

- To load real glTF / GLB models (multiple meshes, a node hierarchy, PBR materials, textures, skinning, animation), you link and use **gltfio** on top of the engine. You do not get it for free with `<filament/Engine.h>`.

---

## The gltfio object model

All types below are in namespace `filament::gltfio`. Signatures are quoted verbatim from the v1.75.0 public headers (`gltfio/AssetLoader.h`, `ResourceLoader.h`, `FilamentAsset.h`, `FilamentInstance.h`, `Animator.h`, `MaterialProvider.h`, `TextureProvider.h`).

The two **plug-in interfaces** are `TextureProvider` and `MaterialProvider`. Each ships with ready-to-go implementations that you obtain through free factory functions — you do **not** instantiate the provider classes directly:

- `MaterialProvider` — created via `createUbershaderProvider(...)` (pre-built materials) or `createJitShaderProvider(...)` (built at run time using `filamat`).
- `TextureProvider` — created via `createStbProvider(...)` (PNG/JPEG), `createKtx2Provider(...)` (KTX2), or `createWebpProvider(...)` (WebP, if enabled at build time).

### AssetLoader

`AssetLoader` is the entry point. From its docstring: it "consumes a blob of glTF 2.0 content (either JSON or GLB) and produces a FilamentAsset object, which is a bundle of Filament textures, vertex buffers, index buffers, etc." It does **not** fetch external buffer data or create textures on its own — that is `ResourceLoader`'s job. Clients must use `AssetLoader` to create and destroy `FilamentAsset` objects.

Construction parameters (`struct AssetConfiguration`):

```cpp
struct AssetConfiguration {
    class filament::Engine* engine;                          // required
    MaterialProvider* materials;                             // required; client owns it
    utils::NameComponentManager* names = nullptr;            // optional: name → entity
    utils::EntityManager* entities = nullptr;                // optional entity factory
    char* defaultNodeName = nullptr;                         // optional name for anon nodes
    AssetConfigurationExtended* ext = nullptr;               // optional mikktspace tangents
};
```

(`AssetConfigurationExtended` enables mikktspace tangent-space computation; its docstring notes "Android, iOS, Web are not supported. And only disk-local glTF resources are supported," and `AssetConfigurationExtended::isSupported()` reports platform support.)

Public methods (verbatim):

```cpp
static AssetLoader* create(const AssetConfiguration& config);
static void destroy(AssetLoader** loader);

// Single-instance asset (one instance), or null on failure.
FilamentAsset* createAsset(const uint8_t* bytes, uint32_t nbytes);

// Primary asset that owns one-or-more instances; instances share textures,
// materials, and vertex buffers but each has its own entities, transforms,
// material instances, and renderables. Light components belong only to the
// primary asset.
FilamentAsset* createInstancedAsset(const uint8_t* bytes, uint32_t numBytes,
        FilamentInstance** instances, size_t numInstances);

// Adds one more instance later; cannot be called after releaseSourceData().
// NOTE: there is no destroyInstance() — gltfio favors flat arrays.
FilamentInstance* createInstance(FilamentAsset* asset);

void enableDiagnostics(bool enable = true);

// Destroys the asset, all its Filament objects, and all its instances.
void destroyAsset(const FilamentAsset* asset);

// Sweep unused entries from the loader's internal component managers.
void gc() noexcept;

const filament::Material* const* getMaterials() const noexcept;
size_t getMaterialsCount() const noexcept;
MaterialProvider& getMaterialProvider() noexcept;
```

`destroy()` does **not** free the material cache nor the entities of created assets — destroy assets explicitly via `destroyAsset()`.

### ResourceLoader

`ResourceLoader` "prepares and uploads vertex buffers and textures to the GPU." It obtains the URI list from the asset, fetches/decodes the external resources, and "finalizes" the asset (transforming vertex data, decoding images, supplying tangents).

Important threading constraint from the header: it "must be destroyed on the same thread that calls `filament::Renderer::render()`" because it listens to buffer-descriptor callbacks to know when to free CPU-side blobs.

Construction parameters (`struct ResourceConfiguration`):

```cpp
struct ResourceConfiguration {
    class filament::Engine* engine;        // required
    const char* gltfPath;                  // deprecated optional base path/URI for relative resources
    bool normalizeSkinningWeights;          // adjust skin weights to sum to 1
};
```

Public methods (verbatim):

```cpp
explicit ResourceLoader(const ResourceConfiguration& config);
~ResourceLoader();
void setConfiguration(const ResourceConfiguration& config);

// Register a texture decoder for a MIME type ("image/png", "image/jpeg",
// "image/ktx2", "image/webp"). Destroy the provider AFTER the ResourceLoader.
void addTextureProvider(const char* mimeType, TextureProvider* provider);

// Push externally-referenced resource bytes into the loader's URI cache.
// Call before loadResources / asyncBeginLoad. GLB clients usually don't need this.
void addResourceData(const char* uri, BufferDescriptor&& buffer);
bool hasResourceData(const char* uri) const;

// Free the URI cache populated via addResourceData (only after load completes
// or is cancelled).
void evictResourceData();

// SYNCHRONOUS: blocks until all textures decode. Returns false if already
// loaded or a resource failed.
bool loadResources(FilamentAsset* asset);

// ASYNCHRONOUS alternative: requires periodic asyncUpdateLoad() calls.
bool asyncBeginLoad(FilamentAsset* asset);
float asyncGetLoadProgress() const;       // [0,1]
void asyncUpdateLoad();                    // call until progress hits 100%
void asyncCancelLoad();
```

`BufferDescriptor` is `using BufferDescriptor = filament::backend::BufferDescriptor;`.

### FilamentAsset

The product of `AssetLoader`. From its docstring: it "owns a bundle of Filament objects" — a hierarchy of entities (every entity has a `TransformManager` component; some also have `Name`, `Renderable`, `Light`, `Camera`, or `Node` components), plus strong ownership of `VertexBuffer`, `IndexBuffer`, `Texture`, and an optional `Animator`. (Note its `\todo`: "Only the default glTF scene is loaded, other glTF scenes are ignored.")

Key accessors (verbatim):

```cpp
// All node entities (each has a Transform; some have Renderable and/or Light).
const Entity* getEntities() const noexcept;
size_t getEntityCount() const noexcept;

// Only entities with a Renderable component.
const utils::Entity* getRenderableEntities() const noexcept;
size_t getRenderableEntityCount() const noexcept;

// Only entities with a Light component.
const Entity* getLightEntities() const noexcept;
size_t getLightEntityCount() const noexcept;

// Only entities with a Camera component.
const Entity* getCameraEntities() const noexcept;
size_t getCameraEntityCount() const noexcept;

// Transform "super root" with no matching glTF node; transform the whole asset.
Entity getRoot() const noexcept;

// AABB from the glTF accessor min/max (load-time, not over all instances).
filament::Aabb getBoundingBox() const noexcept;

// Convenience: first instance (or null). Use this to reach the Animator, etc.
FilamentInstance* getInstance() noexcept;

// Resource URIs for externally-referenced buffers (used to drive ResourceLoader).
const char* const* getResourceUris() const noexcept;
size_t getResourceUriCount() const noexcept;

// Reclaim CPU-side memory (URI strings, bindings, raw animation data).
// Only call AFTER ResourceLoader::loadResources(). For instanced assets this
// prevents creating new instances.
void releaseSourceData() noexcept;
```

For progressive (async) reveal there is `Entity popRenderable() noexcept;` / `size_t popRenderables(Entity*, size_t) noexcept;` — pop ready renderables off the queue and add them to the scene as textures finish decoding (`while (Entity e = popRenderable()) { scene.addEntity(e); }`). There are also name lookups (`getName`, `getFirstEntityByName`, `getEntitiesByName`, `getEntitiesByPrefix`), morph-target accessors, `getWireframe()`, `getEngine()`, and a helper `addEntitiesToScene(scene, entities, count, sceneFilter)`.

### FilamentInstance

From its docstring: "Provides access to a hierarchy of entities that have been instanced from a glTF asset." Obtained from `FilamentAsset::getInstance()` or from the `instances` array filled by `createInstancedAsset()`.

Key methods (verbatim):

```cpp
FilamentAsset const* getAsset() const noexcept;

// This instance's entities (one per glTF node) and its transform root.
const utils::Entity* getEntities() const noexcept;
size_t getEntityCount() const noexcept;
utils::Entity getRoot() const noexcept;

// The instance's animation engine (owned by the asset; do NOT delete).
Animator* getAnimator() noexcept;

// Material variants (KHR_materials_variants).
void applyMaterialVariant(size_t variantIndex) noexcept;  // ignored if out of bounds
size_t getMaterialVariantCount() const noexcept;
const char* getMaterialVariantName(size_t variantIndex) const noexcept;

// Material instances (already bound to renderables).
MaterialInstance* const* getMaterialInstances() noexcept;
size_t getMaterialInstanceCount() const noexcept;
```

It also exposes skinning (`getSkinCount`, `getSkinNameAt`, `getJointCountAt`, `getJointsAt`, `attachSkin`, `detachSkin`, `getInverseBindMatricesAt`), per-instance bounding boxes (`getBoundingBox`, `recomputeBoundingBoxes`), and `detachMaterialInstances()`.

Animator note from the header: an animator obtained from the **primary asset's** instance shares the animation frame across all instances; obtain it from each individual `FilamentInstance` if you want per-instance control.

### Animator

From its docstring: "Updates matrices according to glTF `animation` and `skin` definitions" — drives `TransformManager` components for animations and `RenderableManager` bone matrices for skins. Obtain it from `FilamentInstance::getAnimator()` (never construct or delete it directly; the constructor/destructor are private).

Public methods (verbatim):

```cpp
// Apply animation #animationIndex at the given time (seconds). Uses TransformManager.
void applyAnimation(size_t animationIndex, float time) const;

// Push bone matrices into RenderableManager::setBones. Independent of animation.
void updateBoneMatrices();

// Cross-fade between a previous and current animation (alpha in [0,1]).
// Typical order: applyAnimation, applyCrossFade, updateBoneMatrices.
void applyCrossFade(size_t previousAnimIndex, float previousAnimTime, float alpha);

// Reset all bones to identity (T-pose). Independent of animation.
void resetBoneMatrices();

size_t getAnimationCount() const;
float getAnimationDuration(size_t animationIndex) const;     // seconds
const char* getAnimationName(size_t animationIndex) const;   // weak ref; "" if unnamed
```

### MaterialProvider (ubershader vs JIT)

A `MaterialProvider` hands gltfio the Filament `Material` objects (and `MaterialInstance`s) needed for the glTF's feature set. You obtain one through a **free factory function** (the `UbershaderProvider` / `JitShaderProvider` classes themselves are internal):

```cpp
// Builds materials on the fly via GLSL composed at run time. Requires libfilamat
// (NOT available in libgltfio_core). Streamlined shaders, slower construction.
MaterialProvider* createJitShaderProvider(Engine* engine, bool optimizeShaders = false,
        utils::FixedCapacityVector<char const*> const& variantFilters = {});

// Loads a small set of pre-built materials from an ubershader archive. No run-time
// work, no filamat. Larger/more-complex shaders.
MaterialProvider* createUbershaderProvider(Engine* engine, const void* archive,
        size_t archiveByteCount);
```

Note the asymmetry: `createUbershaderProvider` takes the `.uberz` `archive` bytes; `createJitShaderProvider` does not (it compiles per asset).

| Factory                       | How it gets materials                          | Use when                                                  |
|-------------------------------|------------------------------------------------|-----------------------------------------------------------|
| `createUbershaderProvider`    | Loads **pre-built** materials from a `.uberz` archive | You need **fast startup**; no runtime shader compilation, but shaders are larger/complex |
| `createJitShaderProvider`     | **Builds materials at run time** via `filamat`  | You can afford runtime compilation for leaner shaders (must link `libfilamat`) |

Both implementations cache materials that must be freed explicitly with `destroyMaterials()` — the cache is **not** freed when the `MaterialProvider` is destroyed (so clients can take ownership). Deleting the provider itself is the client's responsibility.

The interface also exposes `createMaterialInstance(MaterialKey* config, UvMap* uvmap, label, extras)`, `getMaterial(...)`, `getMaterials()`, `getMaterialsCount()`, and `needsDummyData(VertexAttribute)`. A `MaterialKey` is a 20-byte POD describing a glTF material's requirements (e.g. `doubleSided`, `unlit`, `hasBaseColorTexture`, `alphaMode`, clear-coat / sheen / transmission / volume / specular flags); `enum class AlphaMode : uint8_t { OPAQUE, MASK, BLEND };`.

### TextureProvider (PNG/JPEG vs KTX2 vs WebP)

A `TextureProvider` decodes the image bytes referenced by the glTF into Filament `Texture` objects. It "constructs Filament Texture objects synchronously, but populates their miplevels asynchronously." In practice the only client is gltfio's `ResourceLoader` — you create a provider and register it with the loader via `addTextureProvider(mimeType, provider)`. Free factory functions:

```cpp
// stb_image-based; handles "image/png" and "image/jpeg". Requires STB in the build.
TextureProvider* createStbProvider(filament::Engine* engine);

// Handles "image/ktx2" per KHR_texture_basisu (Basis Universal / BasisU).
TextureProvider* createKtx2Provider(filament::Engine* engine);

// Handles "image/webp" (lossless + lossy) IF webp support was enabled at build
// time; otherwise returns nullptr. Check with isWebpSupported().
TextureProvider* createWebpProvider(filament::Engine* engine);
bool isWebpSupported();
```

Pick (or register multiple of) these based on which texture encodings your glTF assets reference. The interface exposes `pushTexture(...)`, `popTexture()`, `updateQueue()`, `getPushMessage()` / `getPopMessage()`, `waitForCompletion()`, `cancelDecoding()`, and queue counters — but for normal glTF loading you let `ResourceLoader` drive all of that. `enum class TextureFlags : uint64_t { NONE = 0, sRGB = 1 << 0 };`.

---

## The canonical end-to-end C++ load flow

This is the worked example from the `AssetLoader.h` docstring (quoted), which is the authoritative usage reference for the whole library:

```cpp
auto engine = Engine::create();
auto materials = createJitShaderProvider(engine);
auto decoder = createStbProvider(engine);
auto loader = AssetLoader::create({engine, materials});

// Parse the glTF content and create Filament entities.
std::vector<uint8_t> content(...);
FilamentAsset* asset = loader->createAsset(content.data(), content.size());
content.clear();

// Load buffers and textures from disk.
ResourceLoader resourceLoader({engine, ".", true});
resourceLoader.addTextureProvider("image/png", decoder);
resourceLoader.addTextureProvider("image/jpeg", decoder);
resourceLoader.loadResources(asset);

// Free the glTF hierarchy as it is no longer needed.
asset->releaseSourceData();

// Add renderables to the scene.
scene->addEntities(asset->getEntities(), asset->getEntityCount());

// Extract the animator interface from the FilamentInstance.
auto animator = asset->getInstance()->getAnimator();

// Execute the render loop and play the first animation.
do {
     animator->applyAnimation(0, time);
     animator->updateBoneMatrices();
     if (renderer->beginFrame(swapChain)) {
         renderer->render(view);
         renderer->endFrame();
     }
} while (!quit);

scene->removeEntities(asset->getEntities(), asset->getEntityCount());
loader->destroyAsset(asset);
materials->destroyMaterials();
delete materials;
delete decoder;
AssetLoader::destroy(&loader);
Engine::destroy(&engine);
```

The shape of that flow, mapped to the sections above:

1. **Create providers.** `createJitShaderProvider(engine)` (or `createUbershaderProvider(engine, archive, size)`) for materials; `createStbProvider(engine)` (and/or `createKtx2Provider` / `createWebpProvider`) for textures. The client owns these and destroys them last.
2. **Create the loader.** `AssetLoader::create({engine, materials})` — `AssetConfiguration` with engine + material provider (other fields optional).
3. **Parse bytes → asset.** `loader->createAsset(bytes, nbytes)` for one instance, or `createInstancedAsset(bytes, nbytes, instances, n)` for many.
4. **Load resources.** Build a `ResourceLoader({engine, basePath, normalizeWeights})`, register texture providers per MIME type, then `loadResources(asset)` (synchronous) — or `asyncBeginLoad(asset)` plus periodic `asyncUpdateLoad()` while `asyncGetLoadProgress()` climbs to 1.0. For JSON glTF with external buffers you may `addResourceData(uri, buffer)` first (GLB usually needs none).
5. **Add to scene.** `scene->addEntities(asset->getEntities(), asset->getEntityCount())` (or `getRenderableEntities()` for just the drawables). For async reveal, drain `popRenderable()` per frame instead.
6. **Release source data.** `asset->releaseSourceData()` once `loadResources()` has run, to reclaim CPU-side memory (blocks adding new instances afterward).
7. **Animate per frame.** `auto animator = asset->getInstance()->getAnimator();` then `animator->applyAnimation(i, time)` and `animator->updateBoneMatrices()` each frame (add `applyCrossFade(...)` between them when blending).
8. **Tear down.** `scene->removeEntities(...)`, `loader->destroyAsset(asset)`, `materials->destroyMaterials()`, `delete materials; delete decoder;`, `AssetLoader::destroy(&loader)`, `Engine::destroy(&engine)`. The provider material cache must be freed explicitly — it does not go away with the provider.

---

## The ubershader archive (.uberz) toolchain

When using `createUbershaderProvider`, you feed it a precompiled `.uberz` archive (passed as the `archive` / `archiveByteCount` arguments). The README describes how that archive is built:

> The `uberz` command line tool consumes a list of `.spec` and `.filamat` files and produces a single `.uberz` file. For details on these two file formats, see the README in `libs/uberz`.

So the pipeline is:

```
.spec files + .filamat files  ──uberz──▶  one .uberz archive  ──▶  createUbershaderProvider (at load time)
```

- `.filamat` = compiled Filament material (the same archive format `matc` emits).
- `.spec` = formal description of which glTF features each material supports.
- The `.spec` / `.filamat` file formats are documented in `libs/uberz/README` (not in this corpus).

---

## Texture compression & mesh compression

What the **provided sources** actually state:

- **KTX2 texture support is real and first-class.** gltfio's `createKtx2Provider` "Creates a decoder that can handle certain types of `image/ktx2` content as specified in the KHR_texture_basisu specification" (i.e. Basis Universal supercompressed textures). Plain PNG/JPEG go through `createStbProvider`; WebP through `createWebpProvider` when built with WebP support.
- **KTX (KTX1) and KTX2 appear throughout the samples** for skyboxes, IBL, and material textures (see the sample sections below). The web tutorial generates KTX2 with `mipgen --compression=uastc` (UASTC) and `--compression=uastc_normals` for normal maps.

What the provided sources do **not** state (do not claim these from this file):

- **Draco** geometry compression — not mentioned in any of the source files or the 7 gltfio headers.
- **meshopt / EXT_meshopt_compression** — not mentioned in any of the source files or the 7 gltfio headers.

If you need to assert Draco or meshopt support for gltfio v1.75.0, verify against the actual gltfio sources / Filament release notes first. They are not confirmed here.

---

## IMPORTANT: filamesh is NOT glTF

This is the single most important accuracy point in this corpus, because the two "Suzanne" samples look like asset-loading examples but **do not use gltfio at all**.

- **`filamesh`** is Filament's own simple binary mesh format, produced by the `filamesh` command-line tool. The web tutorial:

  > Filament does not have an asset loading system, but it does provide a binary mesh format called `filamesh` for simple use cases.

  ```bash
  filamesh --compress monkey.obj suzanne.filamesh
  ```

- **gltfio** is what handles `.gltf` / `.glb`. filamesh and gltfio are different code paths:
  - filamesh: C++ `filamesh::MeshReader` (`<filameshio/MeshReader.h>`); JS `engine.loadFilamesh(...)`. One mesh, you supply the `MaterialInstance` yourself.
  - gltfio: `AssetLoader` + `ResourceLoader` + `MaterialProvider` + `TextureProvider` → a full `FilamentAsset` with its own entities and materials.

Do not present the Suzanne samples as glTF examples. They demonstrate filamesh loading plus compressed-texture (KTX2) handling.

---

## What the Filament v1.75.0 samples actually load

### C++ sample (samples/suzanne.cpp) — filamesh + KTX2

`samples/suzanne.cpp` renders the Suzanne monkey from a **filamesh** buffer with **KTX2** material textures. It does **not** include any gltfio header. Relevant includes:

```cpp
#include <filameshio/MeshReader.h>   // filamesh loader (NOT gltfio)
#include <ktxreader/Ktx2Reader.h>    // KTX2 texture decode
#include <stb_image.h>               // PNG/JPEG decode (for the normal map)
```

**KTX2 textures via `Ktx2Reader`.** You register acceptable internal formats in priority order (compressed first, uncompressed as fallback), then `load(...)` each texture, tagging its transfer function (sRGB vs linear):

```cpp
Ktx2Reader reader(*engine);

reader.requestFormat(Texture::InternalFormat::DXT3_SRGBA);
reader.requestFormat(Texture::InternalFormat::DXT3_RGBA);
// Uncompressed formats are lower priority, so they get added last.
reader.requestFormat(Texture::InternalFormat::SRGB8_A8);
reader.requestFormat(Texture::InternalFormat::RGBA8);

constexpr auto sRGB   = Ktx2Reader::TransferFunction::sRGB;
constexpr auto LINEAR = Ktx2Reader::TransferFunction::LINEAR;

app.albedo    = reader.load(MONKEY_ALBEDO_DATA,    MONKEY_ALBEDO_SIZE,    sRGB);
app.ao        = reader.load(MONKEY_AO_DATA,        MONKEY_AO_SIZE,        LINEAR);
app.metallic  = reader.load(MONKEY_METALLIC_DATA,  MONKEY_METALLIC_SIZE,  LINEAR);
app.roughness = reader.load(MONKEY_ROUGHNESS_DATA, MONKEY_ROUGHNESS_SIZE, LINEAR);
```

The image bytes (`MONKEY_*_DATA`/`_SIZE`) are baked into the binary via generated resource headers (`generated/resources/monkey.h`), so there is no async disk/network fetch in this sample.

**Normal map via STB** (not KTX2 here), building mips at load:

```cpp
static Texture* loadNormalMap(Engine* engine, const uint8_t* normals, size_t nbytes) {
    int w, h, n;
    unsigned char* data = stbi_load_from_memory(normals, nbytes, &w, &h, &n, 3);
    Texture* normalMap = Texture::Builder()
            .width(uint32_t(w))
            .height(uint32_t(h))
            .levels(0xff)
            .format(Texture::InternalFormat::RGB8)
            .usage(Texture::Usage::DEFAULT | Texture::Usage::GEN_MIPMAPPABLE)
            .build(*engine);
    Texture::PixelBufferDescriptor buffer(data, size_t(w * h * 3),
            Texture::Format::RGB, Texture::Type::UBYTE,
            (Texture::PixelBufferDescriptor::Callback) &stbi_image_free);
    normalMap->setImage(*engine, 0, std::move(buffer));
    normalMap->generateMipmaps(*engine);
    return normalMap;
}
```

**Material instance** is built from a compiled `.filamat` package (`RESOURCES_TEXTUREDLIT_*`) and each texture is bound by name with a sampler:

```cpp
TextureSampler sampler(TextureSampler::MinFilter::LINEAR_MIPMAP_LINEAR,
                       TextureSampler::MagFilter::LINEAR);

app.material = Material::Builder()
        .package(RESOURCES_TEXTUREDLIT_DATA, RESOURCES_TEXTUREDLIT_SIZE).build(*engine);
app.materialInstance = app.material->createInstance();
app.materialInstance->setParameter("albedo",    app.albedo,    sampler);
app.materialInstance->setParameter("ao",        app.ao,        sampler);
app.materialInstance->setParameter("metallic",  app.metallic,  sampler);
app.materialInstance->setParameter("normal",    app.normal,    sampler);
app.materialInstance->setParameter("roughness", app.roughness, sampler);
```

**Mesh load (the filamesh step) + scene insertion.** `MeshReader::loadMeshFromBuffer` returns a `filamesh::MeshReader::Mesh` whose `renderable` is an entity you add to the scene:

```cpp
app.mesh = filamesh::MeshReader::loadMeshFromBuffer(
        engine, MONKEY_SUZANNE_DATA, MONKEY_SUZANNE_SIZE,
        nullptr, nullptr, app.materialInstance);

auto ti = tcm.getInstance(app.mesh.renderable);
app.transform = mat4f{ mat3f(1), float3(0, 0, -4) } * tcm.getWorldTransform(ti);
rcm.setCastShadows(rcm.getInstance(app.mesh.renderable), false);
scene->addEntity(app.mesh.renderable);
tcm.setTransform(ti, app.transform);
```

**Cleanup** destroys the renderable, material, material instance, and every texture:

```cpp
engine->destroy(app.mesh.renderable);
engine->destroy(app.materialInstance);
engine->destroy(app.material);
engine->destroy(app.albedo);
engine->destroy(app.normal);
engine->destroy(app.roughness);
engine->destroy(app.metallic);
engine->destroy(app.ao);
```

> Mapping to a real gltfio C++ flow: the gltfio equivalent would replace `MeshReader::loadMeshFromBuffer` with `AssetLoader::createAsset(bytes, size)` to get a `FilamentAsset`, drive a `ResourceLoader` to populate buffers/textures, then `scene->addEntities(asset->getEntities(), asset->getEntityCount())` (or `getRenderableEntities()`). Those gltfio calls are **not present in this sample** — see [The canonical end-to-end C++ load flow](#the-canonical-end-to-end-c-load-flow) for the header-grounded sequence.

### Web tutorial (web/suzanne) — filamesh + KTX2

The web/JS "suzanne" tutorial likewise loads a **filamesh** mesh and **KTX/KTX2** textures via Filament's JS helpers. It introduces "compressed textures, mipmap generation, asynchronous texture loading, and trackball rotation" — **not** glTF.

**Asset URLs** — note `suzanne.filamesh` (a filamesh, not a glb), KTX1 for sky/IBL, KTX2 for material maps, and a compiled `.filamat`:

```js
const ibl_url        = 'venetian_crossroads_2k/venetian_crossroads_2k_ibl.ktx';
const sky_small_url  = 'venetian_crossroads_2k/venetian_crossroads_2k_skybox_tiny.ktx';
const sky_large_url  = 'venetian_crossroads_2k/venetian_crossroads_2k_skybox.ktx';
const albedo_url     = `albedo.ktx2`;
const ao_url         = `ao.ktx2`;
const metallic_url   = `metallic.ktx2`;
const normal_url     = `normal.ktx2`;
const roughness_url  = `roughness.ktx2`;
const filamat_url    = 'textured.filamat';
const filamesh_url   = 'suzanne.filamesh';
```

**`Filament.init([...], callback)`** preloads a small required subset before constructing the app; remaining assets stream in later for faster perceived load:

```js
const initFilament = (backend) => () => {
    Filament.init([ filamat_url, filamesh_url, sky_small_url, ibl_url ], () => {
        let options = {};
        if (backend == 'webgpu') {
            options = {backend: Filament.Backend.WEBGPU};
        }
        window.app = new App(document.getElementsByTagName('canvas')[0], options);
    });
};

if (location.search === '?backend=webgpu') {
    Filament.initWebGPU().then(initFilament("webgpu"));
} else {
    initFilament()();
}
```

**Loading the mesh (filamesh) and its material** inside the `App` constructor. `engine.loadFilamesh(url, materialInstance)` returns an object whose `.renderable` is the entity:

```js
const material = this.engine.createMaterial(filamat_url);
this.matinstance = material.createInstance();

const filamesh = this.engine.loadFilamesh(filamesh_url, this.matinstance);
this.suzanne = filamesh.renderable;
```

**Asynchronous texture streaming with `Filament.fetch([...], callback)`.** The tutorial: "It takes a list of asset URLs and a callback function that triggers when the assets have finished downloading." KTX2 textures are created from the fetched bytes, bound to the material instance, the skybox is upgraded to high-res, and only then is the renderable added to the scene:

```js
Filament.fetch([sky_large_url, albedo_url, roughness_url, metallic_url, normal_url, ao_url], () => {
    const albedo    = this.engine.createTextureFromKtx2(albedo_url, {srgb: true});
    const roughness = this.engine.createTextureFromKtx2(roughness_url);
    const metallic  = this.engine.createTextureFromKtx2(metallic_url);
    const normal    = this.engine.createTextureFromKtx2(normal_url);
    const ao        = this.engine.createTextureFromKtx2(ao_url);

    const sampler = new Filament.TextureSampler(
        Filament.MinFilter.LINEAR_MIPMAP_LINEAR,
        Filament.MagFilter.LINEAR,
        Filament.WrapMode.CLAMP_TO_EDGE);

    this.matinstance.setTextureParameter('albedo',    albedo,    sampler);
    this.matinstance.setTextureParameter('roughness', roughness, sampler);
    this.matinstance.setTextureParameter('metallic',  metallic,  sampler);
    this.matinstance.setTextureParameter('normal',    normal,    sampler);
    this.matinstance.setTextureParameter('ao',        ao,        sampler);

    // Replace low-res skybox with high-res skybox.
    this.engine.destroySkybox(this.skybox);
    this.skybox = this.engine.createSkyFromKtx1(sky_large_url);
    this.scene.setSkybox(this.skybox);

    this.scene.addEntity(this.suzanne);   // unhide the renderable once textures are ready
});
```

**Progressive-loading pattern to copy:** construct with the minimum (`Filament.init`), show a low-res skybox/IBL immediately, then `Filament.fetch` the heavy textures and high-res skybox, and only `scene.addEntity(...)` the model once its textures are bound. The tutorial frames this as reducing *perceived* load time.

**Picking the right compressed-texture variant per client** with `Filament.getSupportedFormatSuffix(...)`:

> This takes a space-separated list of desired format types (`etc`, `s3tc`, or `astc`) ... performs an intersection of the *desired* set with the *supported* set, then returns an appropriate string -- which might be empty.

```js
const albedo_suffix  = Filament.getSupportedFormatSuffix('astc s3tc_srgb');
const texture_suffix = Filament.getSupportedFormatSuffix('etc');
```

The empty-string (uncompressed) variant is always available as a last resort, so you append the suffix to a base URL to fetch only the format the client supports.

**KTX1 skybox / IBL helpers** used in the same constructor (KTX1, not KTX2):

```js
this.skybox = this.engine.createSkyFromKtx1(sky_small_url);
this.scene.setSkybox(this.skybox);
this.indirectLight = this.engine.createIblFromKtx1(ibl_url);
this.indirectLight.setIntensity(100000);
this.scene.setIndirectLight(this.indirectLight);
```

> Mapping to a real gltfio web flow: Filament's JS bindings expose a glTF path (commonly `engine.loadGltf` / a `loadGltf`-style helper that returns a `FilamentAsset`-like object) distinct from `loadFilamesh`. **The provided tutorial only demonstrates `loadFilamesh`**, and the JS gltfio binding was not in this corpus, so this file does not give a `loadGltf` snippet — see the verification note before writing one. (The verbatim signatures above are the C++ gltfio API; do not assume the JS names match.)

---

## What is verified vs not in this file

**Verified — quoted from the v1.75.0 gltfio public headers and corpus files:**

- The full `filament::gltfio` C++ object model and signatures: `AssetLoader` (`create`/`createAsset`/`createInstancedAsset`/`createInstance`/`destroyAsset`/`destroy`, `AssetConfiguration`), `ResourceLoader` (`ResourceConfiguration`, `addResourceData`, `addTextureProvider`, `loadResources`, `asyncBeginLoad`/`asyncGetLoadProgress`/`asyncUpdateLoad`/`asyncCancelLoad`, `evictResourceData`), `FilamentAsset` (`getEntities`/`getRenderableEntities`/`getLightEntities`/`getCameraEntities`/`getRoot`/`getBoundingBox`/`getInstance`/`getResourceUris`/`releaseSourceData`/`popRenderable`), `FilamentInstance` (`getEntities`/`getRoot`/`getAnimator`/`applyMaterialVariant`/`getMaterialInstances`), `Animator` (`applyAnimation`/`updateBoneMatrices`/`applyCrossFade`/`resetBoneMatrices`/`getAnimationCount`/`getAnimationDuration`/`getAnimationName`). (gltfio headers)
- The provider factories: `createUbershaderProvider` vs `createJitShaderProvider` (and the `MaterialKey` / `AlphaMode` types), `createStbProvider` / `createKtx2Provider` / `createWebpProvider` + `isWebpSupported`. These are **free functions**; the concrete provider classes are internal. (`MaterialProvider.h`, `TextureProvider.h`)
- The canonical end-to-end load flow, quoted verbatim from the `AssetLoader.h` docstring. (gltfio header)
- gltfio is a separate loader library for `.gltf` / `.glb`; core Filament has no scene-asset loader. (gltfio README; web tutorial)
- Ubershader trade-off (fast startup, large shaders; no runtime compile) and the `uberz` → `.uberz` archive toolchain from `.spec` + `.filamat`. (gltfio README + `MaterialProvider.h`)
- KTX2 support via BasisU; the C++ `Ktx2Reader` and JS `createTextureFromKtx2` usage; KTX1 sky/IBL helpers; `getSupportedFormatSuffix`; `Filament.init` / `Filament.fetch` async loading. (samples + tutorial, quoted)
- That **both** Suzanne samples load **filamesh**, not glTF. (samples + tutorial, quoted)

**Unverified — NOT confirmed by the headers or corpus; verify against real sources before stating as fact:**

- A JS `loadGltf` helper signature — the web tutorial only shows `loadFilamesh`, and the JS gltfio binding was not in this corpus. Do not assume the JS names mirror the C++ API.
- **Draco** and **meshopt / EXT_meshopt_compression** support — not mentioned in any corpus file or in the 7 gltfio headers.
