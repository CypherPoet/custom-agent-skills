# Engine API: Entities & Component Managers

> Source: Filament C++ headers (RenderableManager/LightManager/TransformManager/Box), Filament v1.75.0
> Last synced: 2026-08-14

## Table of Contents

| Section | Covers |
|---|---|
| [Mental Model: Entity-Component](#mental-model-entity-component) | Opaque entity identities, renderable, light, transform, and optional name components, engine-owned managers, and component attachment and removal |
| [Entities: utils::Entity & utils::EntityManager](#entities-utilsentity--utilsentitymanager) | Singleton allocation and batch creation, component-first teardown, engine-wide component destruction, and storing entities rather than transient instances |
| [Common Manager Surface (Instance pattern)](#common-manager-surface-instance-pattern) | Component presence, transient instance lookup and validation, counts, entity enumeration, reverse lookup, and component removal |
| [RenderableManager](#renderablemanager) | Primitive and material bundles, indexed and nonindexed geometry, bounds and visibility, shadows and fog, skinning and morphing, instancing, live mutation, and computed AABBs |
| [LightManager](#lightmanager) | Sun, directional, point, and spot semantics, engine limits, builder and runtime controls, photometric units, cone and falloff limits, efficiencies, and shadow configuration |
| [TransformManager](#transformmanager) | Local and world transforms, parent hierarchy and orphaning, child traversal, accurate translations, cycle prevention, and batched hierarchy updates |
| [Box & Aabb (bounding boxes)](#box--aabb-bounding-boxes) | Center-and-half-extent `Box` semantics, min/max construction and conversion, computed bounds, transforms, unions, spheres, and the distinct min/max `Aabb` type |
| [End-to-End Flow (grounded in hellopbr.cpp)](#end-to-end-flow-grounded-in-hellopbrcpp) | Material and geometry setup, renderable transforms and mutation, physical sun creation, scene insertion, per-frame animation, and entity cleanup |

---

## Mental Model: Entity-Component

A Filament **entity** (`utils::Entity`) is just an opaque id. It has no behavior on its own. Behavior comes from **components** attached to it through **managers** owned by the `Engine`:

- `RenderableManager` — makes an entity drawable (geometry + material + culling/shadow state).
- `LightManager` — makes an entity a light source.
- `TransformManager` — gives an entity a position/orientation and a place in the scene hierarchy.
- (`utils::NameComponentManager` — human-readable labels; not covered here.)

One entity can carry several components at once (e.g. a renderable that also has a transform). Each manager is obtained from the engine:

```cpp
auto& rcm = engine->getRenderableManager();
auto& lcm = engine->getLightManager();
auto& tcm = engine->getTransformManager();
auto& em  = utils::EntityManager::get();
```

Components are added with a `Builder` (renderable, light) or with `create()` (transform), and removed with `destroy(entity)`.

---

## Entities: utils::Entity & utils::EntityManager

Entities are created and destroyed through the singleton `utils::EntityManager` (not the engine):

```cpp
#include <utils/EntityManager.h>

utils::Entity e = utils::EntityManager::get().create();   // allocate a fresh entity id
// ... attach components to e ...
utils::EntityManager::get().destroy(e);                   // release the id
```

- `utils::EntityManager::get()` returns the process-wide manager (singleton).
- `create()` returns a new `utils::Entity`; there is also a batch `create(n, Entity*)` form.
- Destroying an entity through `EntityManager` does **not** automatically tear down its Filament components. Destroy components first via each manager's `destroy(entity)` (or `engine->destroy(entity)`, which removes the entity's components across managers), then destroy the entity id. In `hellopbr.cpp` cleanup calls `engine->destroy(app.light)` / `engine->destroy(app.mesh.renderable)`.

An entity is a value type — store **entities**, not instances (see below).

---

## Common Manager Surface (Instance pattern)

All three managers expose the same lookup pattern. An `Instance` is an ephemeral handle into a manager's component storage; use it to read/write component state after `build`/`create`. **Do not store instances** — store entities and re-resolve.

Shared methods (identical signatures across RenderableManager, LightManager, TransformManager):

```cpp
using Instance = utils::EntityInstance<ThisManager>;

bool          hasComponent(utils::Entity e) const noexcept;
Instance      getInstance(utils::Entity e) const noexcept;   // 0/invalid if no component
size_t        getComponentCount() const noexcept;
bool          empty() const noexcept;
utils::Entity getEntity(Instance i) const noexcept;
utils::Entity const* getEntities() const noexcept;           // all entities, unordered
void          destroy(utils::Entity e) noexcept;             // remove this component from e
```

Check validity with `instance.isValid()` (LightManager/TransformManager note this; a RenderableManager `getInstance` returns 0 when absent).

---

## RenderableManager

A renderable is a bundle of **primitives**; each primitive has its own geometry and material. All primitives in one renderable share rendering attributes (shadows, skinning, culling, etc.). The `Builder(count)` constructor fixes the primitive count.

```cpp
using PrimitiveType = backend::PrimitiveType;
using Instance      = utils::EntityInstance<RenderableManager>;
```

Canonical usage (from the header docs):

```cpp
auto renderable = utils::EntityManager::get().create();

RenderableManager::Builder(1)
        .boundingBox({{ -1, -1, -1 }, { 1, 1, 1 }})
        .material(0, matInstance)
        .geometry(0, RenderableManager::PrimitiveType::TRIANGLES, vertBuffer, indBuffer, 0, 3)
        .receiveShadows(false)
        .build(engine, renderable);

scene->addEntity(renderable);
```

### PrimitiveType enum

`PrimitiveType` is `backend::PrimitiveType` (from `backend/DriverEnums.h`; not in these four headers). Referenced verbatim in the headers as `RenderableManager::PrimitiveType::TRIANGLES`. The standard Filament backend members are `POINTS`, `LINES`, `LINE_STRIP`, `TRIANGLES`, `TRIANGLE_STRIP`. **`TRIANGLES` is the value quoted and used in every header/sample example here**; the others are not shown in these files — confirm against `backend/DriverEnums.h` before relying on them.

### Builder constructor & nested enums

```cpp
explicit Builder(size_t count) noexcept;   // count = number of primitives

enum Result { Error = -1, Success = 0 };

static constexpr uint8_t DEFAULT_CHANNEL = 2u;

enum class GeometryType : uint8_t {
    DYNAMIC,        //!< dynamic geometry has no restriction
    STATIC_BOUNDS,  //!< bounds and world space transform are immutable
    STATIC          //!< skinning/morphing not allowed and Vertex/IndexBuffer immutable
};

enum class MorphType : uint8_t {
    NONE     = 0,
    POSITION = 1,
    TANGENT  = 2,
    CUSTOM   = 4
};

struct Bone {
    math::quatf unitQuaternion = { 1.f, 0.f, 0.f, 0.f };
    math::float3 translation   = { 0.f, 0.f, 0.f };
    float reserved = 0;
};
```

### RenderableManager Builder method set (verbatim)

Signatures copied from the header. `UTILS_NONNULL` annotations omitted for brevity; pointer params are non-null unless noted.

```cpp
// --- geometry (see overloads section for all five) ---
Builder& geometry(size_t index, PrimitiveType type,
        VertexBuffer* vertices, IndexBuffer* indices,
        size_t offset, size_t minIndex, size_t maxIndex, size_t count) noexcept;
Builder& geometry(size_t index, PrimitiveType type,
        VertexBuffer* vertices, IndexBuffer* indices,
        size_t offset, size_t count) noexcept;
Builder& geometry(size_t index, PrimitiveType type,
        VertexBuffer* vertices, IndexBuffer* indices) noexcept;
Builder& geometry(size_t index, PrimitiveType type,
        VertexBuffer* vertices, size_t offset, size_t count) noexcept;   // non-indexed
Builder& geometry(size_t index, PrimitiveType type,
        VertexBuffer* vertices) noexcept;                                // non-indexed

Builder& geometryType(GeometryType type) noexcept;                       // default DYNAMIC

Builder& material(size_t index, MaterialInstance const* materialInstance) noexcept;

Builder& boundingBox(const Box& axisAlignedBoundingBox) noexcept;        // object-space AABB

Builder& layerMask(uint8_t select, uint8_t values) noexcept;             // default mask 0x1
Builder& priority(uint8_t priority) noexcept;                            // [0..7], default 4 (7 = drawn last)
Builder& channel(uint8_t channel) noexcept;                             // [0..7], default 2
Builder& culling(bool enable) noexcept;                                  // frustum culling, default true
Builder& lightChannel(unsigned int channel, bool enable = true) noexcept; // channel 0 on by default

Builder& castShadows(bool enable) noexcept;                              // default FALSE
Builder& receiveShadows(bool enable) noexcept;                          // default true
Builder& screenSpaceContactShadows(bool enable) noexcept;              // default false
Builder& fog(bool enabled = true) noexcept;                            // large-scale fog, default true

Builder& enableSkinningBuffers(bool enabled = true) noexcept;          // default false
Builder& skinning(SkinningBuffer* skinningBuffer, size_t count, size_t offset) noexcept;
Builder& skinning(size_t boneCount, math::mat4f const* transforms) noexcept;
Builder& skinning(size_t boneCount, Bone const* bones) noexcept;
Builder& skinning(size_t boneCount) noexcept;
Builder& boneIndicesAndWeights(size_t primitiveIndex,
        math::float2 const* indicesAndWeights, size_t count, size_t bonesPerVertex) noexcept;
Builder& boneIndicesAndWeights(size_t primitiveIndex,
        utils::FixedCapacityVector<utils::FixedCapacityVector<math::float2>> indicesAndWeightsVector) noexcept;

Builder& morphing(size_t targetCount) noexcept;                        // legacy morphing, default 0
Builder& morphing(MorphTargetBuffer* morphTargetBuffer) noexcept;      // standard morphing
Builder& morphing(uint8_t level, size_t primitiveIndex, size_t offset) noexcept;

Builder& blendOrder(size_t primitiveIndex, uint16_t blendOrder) noexcept; // default 0, low 15 bits
Builder& globalBlendOrderEnabled(size_t primitiveIndex, bool enabled) noexcept; // default local

Builder& instances(size_t instanceCount) noexcept;                     // default 1, max 32767
Builder& instances(size_t instanceCount, InstanceBuffer* instanceBuffer) noexcept;

Result build(Engine& engine, utils::Entity entity) const;
```

**Mandatory-ish:** `boundingBox` is required unless culling is disabled. `material` is optional (Filament falls back to a basic default material). At least one `geometry` call per primitive is expected.

### Geometry overloads

`index` is the zero-based primitive slot (`< count` from the Builder constructor). `type` is a `PrimitiveType`. The five overloads:

| Form | Buffers | Range params meaning |
| --- | --- | --- |
| `geometry(index, type, vb, ib, offset, minIndex, maxIndex, count)` | indexed | `offset`+`count` = indices read; `minIndex`/`maxIndex` = index bounds |
| `geometry(index, type, vb, ib, offset, count)` | indexed | `offset`+`count` expressed in indices |
| `geometry(index, type, vb, ib)` | indexed | full buffers |
| `geometry(index, type, vb, offset, count)` | **non-indexed** | `offset`+`count` = vertex offset/count |
| `geometry(index, type, vb)` | **non-indexed** | full vertex buffer |

Notes: for `TRIANGLES`, `count` should be a multiple of 3. Non-indexed and attribute-less rendering (procedural, `bufferCount == 0`) require `FEATURE_LEVEL_1`+.

### RenderableManager post-build mutators

Resolve an `Instance` via `getInstance(entity)`, then mutate live state:

```cpp
void  setAxisAlignedBoundingBox(Instance, const Box& aabb);       // not allowed if STATIC bounds
const Box& getAxisAlignedBoundingBox(Instance) const noexcept;
void  setLayerMask(Instance, uint8_t select, uint8_t values) noexcept;
uint8_t getLayerMask(Instance) const noexcept;
void  setPriority(Instance, uint8_t priority) noexcept;
void  setChannel(Instance, uint8_t channel) noexcept;
void  setCulling(Instance, bool enable) noexcept;
bool  isCullingEnabled(Instance) const noexcept;
void  setFogEnabled(Instance, bool enable) noexcept;
void  setLightChannel(Instance, unsigned int channel, bool enable) noexcept;
void  setCastShadows(Instance, bool enable) noexcept;            // used in hellopbr.cpp
void  setReceiveShadows(Instance, bool enable) noexcept;
void  setScreenSpaceContactShadows(Instance, bool enable) noexcept;
bool  isShadowCaster(Instance) const noexcept;
bool  isShadowReceiver(Instance) const noexcept;
void  setBones(Instance, Bone const* transforms, size_t boneCount = 1, size_t offset = 0);
void  setBones(Instance, math::mat4f const* transforms, size_t boneCount = 1, size_t offset = 0);
void  setSkinningBuffer(Instance, SkinningBuffer*, size_t count, size_t offset);
void  setMorphWeights(Instance, float const* weights, size_t count, size_t offset = 0);
void  setMaterialInstanceAt(Instance, size_t primitiveIndex, MaterialInstance const*);
void  clearMaterialInstanceAt(Instance, size_t primitiveIndex);
MaterialInstance* getMaterialInstanceAt(Instance, size_t primitiveIndex) const noexcept;
void  setGeometryAt(Instance, size_t primitiveIndex, PrimitiveType, VertexBuffer*, IndexBuffer*, size_t offset, size_t count) noexcept;
void  setGeometryAt(Instance, size_t primitiveIndex, PrimitiveType, VertexBuffer*, size_t offset, size_t count) noexcept;
void  setBlendOrderAt(Instance, size_t primitiveIndex, uint16_t order) noexcept;
size_t getPrimitiveCount(Instance) const noexcept;
size_t getInstanceCount(Instance) const noexcept;
```

**`computeAABB` helper** — static utility to build a `Box` from vertex/index data:

```cpp
template<typename VECTOR, typename INDEX>
static Box computeAABB(VECTOR const* vertices, INDEX const* indices,
                       size_t count, size_t stride = sizeof(VECTOR)) noexcept;
// VECTOR must be float4 / half4 / float3 / half3 ; INDEX must be uint16_t / uint32_t.
```

---

## LightManager

A light is a component on an entity; build it with `LightManager::Builder(Type)`. Header example:

```cpp
utils::Entity sun = utils::EntityManager::get().create();

LightManager::Builder(LightManager::Type::SUN)
        .castShadows(true)
        .build(*engine, sun);

engine->getLightManager().destroy(sun);
```

Limits: only **one directional/sun light** is effective (dominant one wins if several); at most **2048 lights** per Engine.

### LightManager Type enum (verbatim)

```cpp
enum class Type : uint8_t {
    SUN,            //!< Directional light that also draws a sun's disk in the sky.
    DIRECTIONAL,    //!< Directional light, emits light in a given direction.
    POINT,          //!< Point light, emits light from a position, in all directions.
    FOCUSED_SPOT,   //!< Physically correct spot light.
    SPOT,           //!< Spot light with coupling of outer cone and illumination disabled.
};
```

Type semantics:
- `SUN` / `DIRECTIONAL` — parallel rays, no position; `SUN` additionally renders a sun disk + glossy reflection. Can cast shadows. Position/falloff ignored.
- `POINT` — has a position, emits in all directions; intensity falls off by inverse-square, bounded by `falloff()`. Direction ignored.
- `FOCUSED_SPOT` — physically correct cone light (changing outer cone changes illumination).
- `SPOT` — like `FOCUSED_SPOT` but decouples outer cone from illumination (artist-friendly).

Type helpers on the manager: `getType(i)`, `isDirectional(i)` (SUN or DIRECTIONAL), `isPointLight(i)` (POINT), `isSpotLight(i)` (SPOT or FOCUSED_SPOT).

### LightManager Builder method set (verbatim)

```cpp
explicit Builder(Type type) noexcept;

Builder& lightChannel(unsigned int channel, bool enable = true) noexcept; // channel 0 on by default
Builder& castShadows(bool enable) noexcept;                              // default FALSE (disabled)
Builder& shadowOptions(const ShadowOptions& options) noexcept;
Builder& castLight(bool enable) noexcept;                               // emits light, default true
Builder& position(const math::float3& position) noexcept;              // default origin; ignored for directional/sun
Builder& direction(const math::float3& direction) noexcept;            // unit vector, default {0,-1,0}; ignored for POINT
Builder& color(const LinearColor& color) noexcept;                     // linear sRGB, default white {1,1,1}
Builder& intensity(float intensity) noexcept;                         // lux (directional) OR lumen (point/spot)
Builder& intensityCandela(float intensity) noexcept;                  // candela (spot/point)
Builder& intensity(float watts, float efficiency) noexcept;          // == intensity(efficiency * 683 * watts)
Builder& falloff(float radius) noexcept;                              // world units, default 1 m; ignored for directional/sun
Builder& spotLightCone(float inner, float outer) noexcept;           // radians; half-angles; ignored for non-spot
Builder& sunAngularRadius(float angularRadiusDeg) noexcept;          // degrees, [0.25, 20.0], default 0.545
Builder& sunHaloSize(float haloSize) noexcept;                       // multiplier of angular radius, >= 1.0, default 10.0
Builder& sunHaloFalloff(float haloFalloff) noexcept;                // dimensionless exponent, >= 1.0, default 80.0

enum Result { Error = -1, Success = 0 };
Result build(Engine& engine, utils::Entity entity);
```

`spotLightCone`: both `inner` and `outer` are silently clamped to a minimum of 0.5° (~0.00873 rad); `inner` in `[0.00873, outer]`, `outer` in `[inner, pi/2]`. Cones are half-angles from the center axis.

Efficiency constants (for `intensity(watts, efficiency)`):

```cpp
static constexpr float EFFICIENCY_INCANDESCENT = 0.0220f;  // 2.2%
static constexpr float EFFICIENCY_HALOGEN      = 0.0707f;  // 7.0%
static constexpr float EFFICIENCY_FLUORESCENT  = 0.0878f;  // 8.7%
static constexpr float EFFICIENCY_LED          = 0.1171f;  // 11.7%
```

### Physical units

Filament lights use **physical photometric units** — pick the right setter for the light type:

| Light type | `intensity(float)` unit | candela setter | notes |
| --- | --- | --- | --- |
| `SUN` / `DIRECTIONAL` | **lux** (lumen/m²) — illuminance | `intensityCandela` ≡ `intensity` for directional | sun ≈ 100,000 lux; hellopbr uses 110000 |
| `POINT` / `SPOT` / `FOCUSED_SPOT` | **lumen** — luminous power | `intensityCandela` sets candela (luminous intensity) | |

- `intensity(float)` and `intensityCandela(float)` **override each other** (last call wins).
- `intensity(watts, efficiency)` is sugar for `intensity(efficiency * 683 * watts)` (683 lm/W is the luminous efficacy at 555 nm).
- `getIntensity(i)` always returns **candela**; for `FOCUSED_SPOT` the returned value depends on the outer cone angle.
- Color is **linear sRGB**. Convert from sRGB with `Color::toLinear<ACCURATE>(sRGBColor(...))` (see hellopbr).

### LightManager post-build mutators

```cpp
void  setLightChannel(Instance, unsigned int channel, bool enable = true) noexcept;
bool  getLightChannel(Instance, unsigned int channel) const noexcept;
void  setPosition(Instance, const math::float3&) noexcept;
const math::float3& getPosition(Instance) const noexcept;
void  setDirection(Instance, const math::float3&) noexcept;
const math::float3& getDirection(Instance) const noexcept;
void  setColor(Instance, const LinearColor&) noexcept;
const math::float3& getColor(Instance) const noexcept;
void  setIntensity(Instance, float intensity) noexcept;                 // can be negative
void  setIntensity(Instance, float watts, float efficiency) noexcept;   // == watts * 683 * efficiency
void  setIntensityCandela(Instance, float intensity) noexcept;
float getIntensity(Instance) const noexcept;                           // returns candela
void  setFalloff(Instance, float radius) noexcept;
float getFalloff(Instance) const noexcept;
void  setSpotLightCone(Instance, float inner, float outer) noexcept;
float getSpotLightOuterCone(Instance) const noexcept;
float getSpotLightInnerCone(Instance) const noexcept;
void  setSunAngularRadius(Instance, float angularRadius) noexcept;     // degrees
float getSunAngularRadius(Instance) const noexcept;
void  setSunHaloSize(Instance, float haloSize) noexcept;
float getSunHaloSize(Instance) const noexcept;
void  setSunHaloFalloff(Instance, float haloFalloff) noexcept;
float getSunHaloFalloff(Instance) const noexcept;
ShadowOptions const& getShadowOptions(Instance) const noexcept;
void  setShadowOptions(Instance, ShadowOptions const&) noexcept;
void  setShadowCaster(Instance, bool shadowCaster) noexcept;          // only DIRECTIONAL/SUN/SPOT/FOCUSED_SPOT can cast
bool  isShadowCaster(Instance) const noexcept;
```

`ShadowOptions` (selected defaults): `mapSize = 1024`, `shadowCascades = 1` (1–4; CSM > 1, SUN/DIRECTIONAL only), `cascadeSplitPositions = {0.125, 0.25, 0.50}`, `constantBias = 0.001`, `normalBias = 1.0`, `shadowFar = 0.0` (0 = camera far), `shadowNearHint = 1.0`, `shadowFarHint = 100.0`, `stable = false`, `lispsm = true`, `screenSpaceContactShadows = false`, `stepCount = 8`, `maxShadowDistance = 0.3`, and `shadowBulbRadius = -1.0` (select the light-type default). PCSS adds per-light `penumbraScale = 1.0`, `penumbraRatioScale = 1.0`, `maxPenumbraRatio = 0.0`, and `maxSearchRadius = 0.0`; nonpositive maximums use the corresponding global defaults. The `Vsm` sub-struct retains `elvsm = false` and `blurWidth = 0.0`. Split-position helpers live in `LightManager::ShadowCascades::computeUniformSplits / computeLogSplits / computePracticalSplits`.

---

## TransformManager

Gives an entity a position/orientation relative to its **parent** transform, and computes the world transform (relative to the root). Components are created with `create()` (no Builder).

```cpp
auto& tcm = engine->getTransformManager();
utils::Entity object = utils::EntityManager::get().create();

tcm.create(object);                                   // identity local transform, no parent
auto i = tcm.getInstance(object);
tcm.setTransform(i, mat4f::translation({ 0, 0, -1 }));
tcm.destroy(object);
```

`create` overloads and core API:

```cpp
void create(utils::Entity entity, Instance parent, const math::mat4f& localTransform);
void create(utils::Entity entity, Instance parent, const math::mat4& localTransform);   // double precision
void create(utils::Entity entity, Instance parent = {});                                 // identity local transform

void destroy(utils::Entity e) noexcept;        // children are ORPHANED (their local becomes world)

void setParent(Instance i, Instance newParent) noexcept;   // re-parent; error to parent under a descendant
utils::Entity getParent(Instance i) const noexcept;
size_t getChildCount(Instance i) const noexcept;
size_t getChildren(Instance i, utils::Entity* children, size_t count) const noexcept;
children_iterator getChildrenBegin(Instance parent) const noexcept;
children_iterator getChildrenEnd(Instance parent) const noexcept;
children_range getChildrenRange(Instance parent) const noexcept;   // range-based for

void setTransform(Instance ci, const math::mat4f& localTransform) noexcept;
void setTransform(Instance ci, const math::mat4& localTransform) noexcept;       // double translation
const math::mat4f& getTransform(Instance ci) const noexcept;                    // local (relative to parent)
math::mat4  getTransformAccurate(Instance ci) const noexcept;
const math::mat4f& getWorldTransform(Instance ci) const noexcept;               // relative to root
math::mat4  getWorldTransformAccurate(Instance ci) const noexcept;

void setAccurateTranslationsEnabled(bool enable) noexcept;   // double-precision translation mode, off by default
bool isAccurateTranslationsEnabled() const noexcept;

void openLocalTransformTransaction() noexcept;     // batch many setTransform() cheaply for deep hierarchies
void commitLocalTransformTransaction() noexcept;   // MUST be called to finalize; never auto-closed
```

Key points:
- `Instance parent = Instance{}` means "no parent" (root).
- `setTransform` takes a **local** matrix (relative to the parent); `getWorldTransform` returns the composed root-relative matrix.
- `setTransform` can be slow for deep hierarchies — wrap bulk updates in `openLocalTransformTransaction()` / `commitLocalTransformTransaction()`. Forgetting to commit leaves world transforms invalid.
- Transform matrices are `filament::math::mat4f`; helpers like `mat4f::translation(...)` and `mat4f::rotation(angle, axis)` are used in samples.

---

## Box & Aabb (bounding boxes)

`filament::Box` is the AABB type a renderable's `boundingBox()` expects. **It is stored as center + half-extent**, not min/max:

```cpp
class Box {
    math::float3 center     = {};   // box center
    math::float3 halfExtent = {};   // half extent from center on each axis

    constexpr float3 getMin() const noexcept;        // center - halfExtent
    constexpr float3 getMax() const noexcept;        // center + halfExtent
    Box& set(const float3& min, const float3& max) noexcept;   // build from min/max corners
    constexpr bool isEmpty() const noexcept;
    Box& unionSelf(const Box& box) noexcept;
    constexpr Box translateTo(const float3& tr) const noexcept;
    float4 getBoundingSphere() const noexcept;       // xyz = center, w = radius
    static Box transform(const mat3f& m, float3 const& t, const Box& box) noexcept;
    friend Box rigidTransform(Box const& box, const mat4f& m) noexcept;
};
```

Three ways to specify a renderable's bounds:

```cpp
// 1. brace-init {center, halfExtent}  — what boundingBox() literally takes
builder.boundingBox({ {0,0,0}, {1,1,1} });   // center (0,0,0), half-extent 1 → unit cube of side 2

// 2. from min/max corners
Box b; b.set({-1,-1,-1}, {1,1,1});
builder.boundingBox(b);

// 3. computed from geometry
Box b = RenderableManager::computeAABB(vertices, indices, count);
builder.boundingBox(b);
```

> Gotcha: the header's canonical example `.boundingBox({{ -1, -1, -1 }, { 1, 1, 1 }})` brace-initializes `{center, halfExtent}` — so that is center `(-1,-1,-1)` with half-extent `(1,1,1)`, **not** min/max corners. To express min/max corners use `Box::set()` (form 2).

`filament::Aabb` is a separate **min/max**-based struct (used internally / for utilities), with `center()`, `extent()`, `isEmpty()`, `getCorners()` (8 vertices), `contains(point)`, and `transform(...)` helpers. Defaults to an inverted/empty box (`min = FLT_MAX`, `max = -FLT_MAX`). It is not the type `boundingBox()` accepts — convert via `Box().set(aabb.min, aabb.max)` when needed.

---

## End-to-End Flow (grounded in hellopbr.cpp)

The complete create-entity → attach-component → add-to-scene flow. `hellopbr.cpp` uses `MeshReader` to load geometry (which builds the renderable + transform internally), then attaches a light explicitly.

```cpp
// Inside the setup callback: (Engine* engine, View* view, Scene* scene)
auto& tcm = engine->getTransformManager();
auto& rcm = engine->getRenderableManager();
auto& em  = utils::EntityManager::get();

// 1. Material + instance (the renderable will bind this)
app.material = Material::Builder()
        .package(RESOURCES_AIDEFAULTMAT_DATA, RESOURCES_AIDEFAULTMAT_SIZE).build(*engine);
auto mi = app.materialInstance = app.material->createInstance();
mi->setParameter("baseColor", RgbType::LINEAR, float3{0.8});
mi->setParameter("metallic", 1.0f);
mi->setParameter("roughness", 0.4f);
mi->setParameter("reflectance", 0.5f);

// 2. Geometry → renderable entity (MeshReader builds the RenderableManager component for us)
app.mesh = MeshReader::loadMeshFromBuffer(engine, MONKEY_SUZANNE_DATA, MONKEY_SUZANNE_SIZE,
                                          nullptr, nullptr, mi);

// 3. Transform: read the mesh's world transform, offset it back along -Z
auto ti = tcm.getInstance(app.mesh.renderable);
app.transform = mat4f{ mat3f(1), float3(0, 0, -4) } * tcm.getWorldTransform(ti);

// 4. Tweak renderable state via its Instance
rcm.setCastShadows(rcm.getInstance(app.mesh.renderable), false);

// 5. Add renderable to the scene
scene->addEntity(app.mesh.renderable);

// 6. Light: create entity, attach light component via Builder, add to scene
app.light = em.create();
LightManager::Builder(LightManager::Type::SUN)
        .color(Color::toLinear<ACCURATE>(sRGBColor(0.98f, 0.92f, 0.89f)))  // linear sRGB
        .intensity(110000)                                                  // lux (directional/sun)
        .direction({ 0.7, -1, -0.8 })
        .sunAngularRadius(1.9f)
        .castShadows(false)
        .build(*engine, app.light);
scene->addEntity(app.light);
```

Per-frame animation (drives the transform component live):

```cpp
auto animate = [&app](Engine* engine, View* view, double now) {
    auto& tcm = engine->getTransformManager();
    auto ti = tcm.getInstance(app.mesh.renderable);
    tcm.setTransform(ti, app.transform * mat4f::rotation(now, float3{ 0, 1, 0 }));
};

// Supply `animate` to FilamentApp2::Builder().animation(animate).
```

Cleanup — destroy components/entities through the engine:

```cpp
auto cleanup = [&app](Engine* engine, View*, Scene*) {
    engine->destroy(app.light);
    engine->destroy(app.mesh.renderable);
    engine->destroy(app.materialInstance);
    engine->destroy(app.material);
};
```

**The pattern in one line:** `EntityManager::create()` → attach a component (`RenderableManager::Builder`/`LightManager::Builder`/`TransformManager::create`) → `scene->addEntity(entity)` to render it → mutate live via `manager.getInstance(entity)` → `engine->destroy(entity)` to tear down.
