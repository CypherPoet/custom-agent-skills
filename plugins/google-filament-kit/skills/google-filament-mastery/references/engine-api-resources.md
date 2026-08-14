# Engine API: GPU Resources & Material Instances

> Source: Filament C++ headers (VertexBuffer/IndexBuffer/BufferObject/Texture/TextureSampler/Material/MaterialInstance/Skybox/IndirectLight), Filament v1.75.0
> Last synced: 2026-08-14

## Table of Contents

| Section | Covers |
|---|---|
| [Mental Model & Lifetime](#mental-model--lifetime) | Every GPU resource on this page follows the same pattern |
| [VertexBuffer](#vertexbuffer) | Holds a set of buffers defining a Renderable's geometry (position, color, normals/tangents, UVs, etc.) |
| [IndexBuffer](#indexbuffer) | Vertex indices into a `VertexBuffer` |
| [BufferObject](#bufferobject) | A generic GPU buffer. Optional — for simple use you don't need it |
| [Texture](#texture) | Supports 2D, 3D, cube maps, 2D arrays, and mip mapping |
| [TextureSampler](#texturesampler) | A non-engine-owned value type that controls texture filtering, wrapping, and comparison |
| [Material](#material) | A `Material` is built from a compiled `.filamat` package (binary blob produced by `matc` or `libfilamat`) |
| [MaterialInstance](#materialinstance) | Holds the concrete parameter values for a `Material`, plus per-instance render-state overrides |
| [Skybox](#skybox) | Fills untouched pixels of a Scene |
| [IndirectLight](#indirectlight) | Environment lighting (global illumination): an irradiance component + a reflections (specular) component |
| [BufferDescriptor & PixelBufferDescriptor (the upload+free contract)](#bufferdescriptor--pixelbufferdescriptor-the-uploadfree-contract) | Upload methods take ownership of a descriptor by rvalue (`&&` + `std::move`) |
| [End-to-End Resource Flow](#end-to-end-resource-flow) | Putting the pieces together (composed from `hellotriangle.cpp` and `suzanne.cpp`) |

---

## Mental Model & Lifetime

Every GPU resource on this page follows the same pattern:

1. **Build** with a `Builder` (`SomeType::Builder().…​.build(engine)` → returns a heap pointer owned by the `Engine`).
2. **Upload** data separately (`setBufferAt` / `setBuffer` / `setImage`), because the GPU buffers are allocated empty.
3. **Destroy** with `engine->destroy(ptr)`. Never `delete` these — destructors are protected (`~VertexBuffer() = default;` etc.) to prevent heap allocation/deletion outside the engine.

Buffers are GPU resources; mutating their data can be slow. Keep constant data and dynamic data in separate buffers. A single `VertexBuffer`/`IndexBuffer`/`Texture` can be shared across several renderables.

**Free-after-upload contract:** upload calls take a `BufferDescriptor` / `PixelBufferDescriptor` by rvalue (`&&`). You pass a pointer to your CPU data plus an optional **callback** that Filament invokes once it has finished consuming the data. After the callback fires (or after upload if you copied the data yourself), the source memory is safe to free. See [BufferDescriptor & PixelBufferDescriptor](#bufferdescriptor--pixelbufferdescriptor-the-uploadfree-contract).

---

## VertexBuffer

Holds a set of buffers defining a Renderable's geometry (position, color, normals/tangents, UVs, etc.). Attributes need not map 1:1 to buffers — several attributes can be **interleaved** in one buffer via `byteOffset`/`byteStride`.

### VertexBuffer Builder method set (verbatim)

```cpp
VertexBuffer::Builder& bufferCount(uint8_t bufferCount) noexcept;   // mandatory, default 0, max 8
VertexBuffer::Builder& vertexCount(uint32_t vertexCount) noexcept;  // vertices per buffer in the set
VertexBuffer::Builder& enableBufferObjects(bool enabled = true) noexcept; // use setBufferObjectAt instead of setBufferAt

VertexBuffer::Builder& attribute(VertexAttribute attribute, uint8_t bufferIndex,
        AttributeType attributeType,
        uint32_t byteOffset = 0, uint8_t byteStride = 0) noexcept;
//   byteStride == 0 → attribute size (from attributeType) is used.

VertexBuffer::Builder& normalized(VertexAttribute attribute, bool normalized = true) noexcept;
//   integer types only; maps the value to [0,1] in the shader.

VertexBuffer::Builder& advancedSkinning(bool enabled) noexcept;
VertexBuffer::Builder& name(utils::StaticString const& name) noexcept;
VertexBuffer::Builder& async(backend::CallbackHandler* handler,
        AsyncCompletionCallback callback = nullptr, void* user = nullptr) noexcept;

VertexBuffer* build(Engine& engine) const;
```

Notes:
- `using AttributeType = backend::ElementType;`
- `using BufferDescriptor = backend::BufferDescriptor;`
- `TANGENTS` must be specified as a quaternion — that is also how normals are supplied.
- Not all backends support non-float 3-component attributes; use `geometry::Transcoder` for conversion.
- `attribute()` is a no-op if the attribute enum is invalid or `bufferIndex` is out of bounds.

### VertexAttribute enum (verbatim)

`VertexAttribute` is a plain `enum` (defined in `filament/MaterialEnums.h`), passed unqualified (e.g. `VertexAttribute::POSITION`):

```cpp
enum VertexAttribute : uint8_t {
    POSITION        = 0,  //!< XYZ position (float3)
    TANGENTS        = 1,  //!< tangent, bitangent and normal, encoded as a quaternion (float4)
    COLOR           = 2,  //!< vertex color (float4)
    UV0             = 3,  //!< texture coordinates (float2)
    UV1             = 4,  //!< texture coordinates (float2)
    BONE_INDICES    = 5,  //!< indices of 4 bones, as unsigned integers (uvec4)
    BONE_WEIGHTS    = 6,  //!< weights of the 4 bones (normalized float4)
    // slot 7 is unused
    CUSTOM0         = 8,
    CUSTOM1         = 9,
    CUSTOM2         = 10,
    CUSTOM3         = 11,
    CUSTOM4         = 12,
    CUSTOM5         = 13,
    CUSTOM6         = 14,
    CUSTOM7         = 15,
    // Aliases for legacy vertex morphing (== CUSTOM0..CUSTOM7):
    MORPH_POSITION_0 = CUSTOM0, MORPH_POSITION_1 = CUSTOM1,
    MORPH_POSITION_2 = CUSTOM2, MORPH_POSITION_3 = CUSTOM3,
    MORPH_TANGENTS_0 = CUSTOM4, MORPH_TANGENTS_1 = CUSTOM5,
    MORPH_TANGENTS_2 = CUSTOM6, MORPH_TANGENTS_3 = CUSTOM7,
};
// MAX_CUSTOM_ATTRIBUTES = 8
```

### AttributeType / ElementType enum (verbatim)

`VertexBuffer::AttributeType` is an alias of `backend::ElementType`. Reference it as `VertexBuffer::AttributeType::FLOAT3` (as samples do):

```cpp
enum class ElementType : uint8_t {
    BYTE,   BYTE2,   BYTE3,   BYTE4,
    UBYTE,  UBYTE2,  UBYTE3,  UBYTE4,
    SHORT,  SHORT2,  SHORT3,  SHORT4,
    USHORT, USHORT2, USHORT3, USHORT4,
    INT,    UINT,
    FLOAT,  FLOAT2,  FLOAT3,  FLOAT4,
    HALF,   HALF2,   HALF3,   HALF4,
};
```

### VertexBuffer Uploading data (setBufferAt + BufferDescriptor)

```cpp
void setBufferAt(Engine& engine, uint8_t bufferIndex, BufferDescriptor&& buffer,
        uint32_t byteOffset = 0);   // byteOffset must be a multiple of 4. Do NOT use if enableBufferObjects() was set.

void setBufferObjectAt(Engine& engine, uint8_t bufferIndex,
        BufferObject const* bufferObject);   // requires enableBufferObjects() on the Builder.

size_t getVertexCount() const noexcept;
bool   isCreationComplete() const noexcept;  // true unless created via async()
```

Async variants exist (`setBufferAtAsync`, `setBufferObjectAtAsync`) and require the engine to be configured for async operation; they return an `AsyncCallId` you can pass to `Engine::cancelAsyncCall()`.

**Worked example (from `hellotriangle.cpp`):**

```cpp
app.vb = VertexBuffer::Builder()
        .vertexCount(3)
        .bufferCount(1)
        .attribute(VertexAttribute::POSITION, 0, VertexBuffer::AttributeType::FLOAT2, 0, 12)
        .attribute(VertexAttribute::COLOR,    0, VertexBuffer::AttributeType::UBYTE4, 8, 12)
        .normalized(VertexAttribute::COLOR)
        .build(*engine);
app.vb->setBufferAt(*engine, 0,
        VertexBuffer::BufferDescriptor(TRIANGLE_VERTICES, 36, nullptr));
```

Interleaved attributes (position at offset 0, color at offset 8) share buffer 0 with a 12-byte stride. From `lightbulb.cpp`, tangents go in a separate buffer and use a normalized `SHORT4`:

```cpp
.attribute(VertexAttribute::POSITION, 0, VertexBuffer::AttributeType::FLOAT3)
.attribute(VertexAttribute::TANGENTS, 1, VertexBuffer::AttributeType::SHORT4)
.normalized(VertexAttribute::TANGENTS)
```

---

## IndexBuffer

Vertex indices into a `VertexBuffer`. 16- or 32-bit. Usually constant; can be shared across renderables.

```cpp
enum class IndexBuffer::IndexType : uint8_t {
    USHORT = uint8_t(backend::ElementType::USHORT),  //!< 16-bit indices
    UINT   = uint8_t(backend::ElementType::UINT),    //!< 32-bit indices
};

// Builder (verbatim):
IndexBuffer::Builder& indexCount(uint32_t indexCount) noexcept;     // size in elements
IndexBuffer::Builder& bufferType(IndexType indexType) noexcept;     // USHORT or UINT
IndexBuffer::Builder& name(utils::StaticString const& name) noexcept;
IndexBuffer::Builder& async(backend::CallbackHandler*, AsyncCompletionCallback = nullptr, void* = nullptr) noexcept;
IndexBuffer* build(Engine& engine);                                 // buffer is uninitialized; call setBuffer()

// Upload (verbatim):
void setBuffer(Engine& engine, BufferDescriptor&& buffer, uint32_t byteOffset = 0); // byteOffset multiple of 4
size_t getIndexCount() const noexcept;
bool   isCreationComplete() const noexcept;
```

The raw bytes are interpreted as 16- or 32-bit indices based on the buffer's `IndexType`. Async variant: `setBufferAsync(...)`.

**Worked example (`hellotriangle.cpp`):**

```cpp
app.ib = IndexBuffer::Builder()
        .indexCount(3)
        .bufferType(IndexBuffer::IndexType::USHORT)
        .build(*engine);
app.ib->setBuffer(*engine, IndexBuffer::BufferDescriptor(TRIANGLE_INDICES, 6, nullptr));
```

---

## BufferObject

A generic GPU buffer. **Optional** — for simple use you don't need it. Use it when you want to **share data between multiple `VertexBuffer` instances** or efficiently **swap out** the buffers backing a `VertexBuffer`. Currently used only for vertex data.

To use one, call `enableBufferObjects()` on the `VertexBuffer::Builder`, then `vb->setBufferObjectAt(engine, idx, bufferObject)` instead of `setBufferAt`.

```cpp
using BindingType = backend::BufferObjectBinding;

// Builder (verbatim):
BufferObject::Builder& size(uint32_t byteCount) noexcept;            // capacity in bytes
BufferObject::Builder& bindingType(BindingType bindingType) noexcept; // defaults to VERTEX; must be VERTEX for now
BufferObject::Builder& name(utils::StaticString const& name) noexcept;
BufferObject* build(Engine& engine);                                 // uninitialized; call setBuffer()

// Upload (verbatim):
void setBuffer(Engine& engine, BufferDescriptor&& buffer, uint32_t byteOffset = 0); // byteOffset multiple of 4
size_t getByteCount() const noexcept;
```

```cpp
enum class BufferObjectBinding : uint8_t { VERTEX, UNIFORM, SHADER_STORAGE };
```

---

## Texture

Supports 2D, 3D, cube maps, 2D arrays, and mip mapping. Built with `Texture::Builder`; destroyed with `engine->destroy(texture)`.

### Texture Builder method set (verbatim)

```cpp
Texture::Builder& width(uint32_t width) noexcept;    // default 1, need not be power-of-two
Texture::Builder& height(uint32_t height) noexcept;  // default 1
Texture::Builder& depth(uint32_t depth) noexcept;    // default 1; >1 needs SAMPLER_3D or SAMPLER_2D_ARRAY (layers)
Texture::Builder& levels(uint8_t levels) noexcept;   // mip levels; pass a large value (e.g. 0xff) to mean "all"
Texture::Builder& samples(uint8_t samples) noexcept; // MSAA; implies render-target use, conflicts with setImage
Texture::Builder& sampler(Sampler target) noexcept;  // SAMPLER_2D, SAMPLER_CUBEMAP, ...
Texture::Builder& format(InternalFormat format) noexcept;   // internal texel storage format
Texture::Builder& usage(Usage usage) noexcept;       // bitmask; default Usage::DEFAULT
Texture::Builder& swizzle(Swizzle r, Swizzle g, Swizzle b, Swizzle a) noexcept; // if isTextureSwizzleSupported()
Texture::Builder& name(utils::StaticString const& name) noexcept;
Texture::Builder& external() noexcept;               // external image; fill via setExternalImage()
Texture::Builder& async(backend::CallbackHandler*, AsyncCompletionCallback = nullptr, void* = nullptr) noexcept;
Texture::Builder& import(intptr_t id) noexcept;      // last resort: wrap a native GL/Metal texture
Texture* build(Engine& engine);
```

Type aliases on `Texture`:
- `using Sampler = backend::SamplerType;`
- `using InternalFormat = backend::TextureFormat;`
- `using Format = backend::PixelDataFormat;` (pixel color format of the source data)
- `using Type = backend::PixelDataType;` (pixel data type of the source data)
- `using Usage = backend::TextureUsage;`
- `using PixelBufferDescriptor = backend::PixelBufferDescriptor;`
- `using CubemapFace = backend::TextureCubemapFace;`
- `using Swizzle = backend::TextureSwizzle;`

Static capability queries (call before choosing a format):
`isTextureFormatSupported(engine, fmt)`, `isTextureFormatMipmappable(engine, fmt)`, `isTextureFormatCompressed(fmt)`, `isTextureSwizzleSupported(engine)`, `getMaxTextureSize(engine, samplerType)`, `getMaxArrayTextureLayers(engine)`, `validatePixelFormatAndType(internalFmt, fmt, type)`.

### Sampler / SamplerType enum (verbatim)

```cpp
enum class SamplerType : uint8_t {
    SAMPLER_2D,             //!< 2D texture
    SAMPLER_2D_ARRAY,       //!< 2D array texture
    SAMPLER_CUBEMAP,        //!< Cube map texture
    SAMPLER_EXTERNAL,       //!< External texture
    SAMPLER_3D,             //!< 3D texture
    SAMPLER_CUBEMAP_ARRAY,  //!< Cube map array texture (feature level 2)
};
```

### InternalFormat / TextureFormat enum (representative, verbatim)

`backend::TextureFormat : uint16_t` is large (uncompressed + many compressed families). The commonly used uncompressed values, reproduced verbatim:

```cpp
// 8-bit / element
R8, R8_SNORM, R8UI, R8I, STENCIL8,
// 16-bit / element
R16F, R16UI, R16I, RG8, RG8_SNORM, RG8UI, RG8I, RGB565, RGB9_E5, RGB5_A1, RGBA4, DEPTH16,
// 24-bit / element
RGB8, SRGB8, RGB8_SNORM, RGB8UI, RGB8I, DEPTH24,
// 32-bit / element
R32F, R32UI, R32I, RG16F, RG16UI, RG16I, R11F_G11F_B10F,
RGBA8, SRGB8_A8, RGBA8_SNORM, RGB10_A2, RGBA8UI, RGBA8I,
DEPTH32F, DEPTH24_STENCIL8, DEPTH32F_STENCIL8,
// 48 / 64 / 96 / 128-bit / element
RGB16F, RGB16UI, RGB16I, RG32F, RG32UI, RG32I, RGBA16F, RGBA16UI, RGBA16I,
RGB32F, RGB32UI, RGB32I, RGBA32F, RGBA32UI, RGBA32I,
```

Compressed families (names only — see header `DriverEnums.h` for the full set):
- ETC2 / EAC: `EAC_R11`, `ETC2_RGB8`, `ETC2_SRGB8`, `ETC2_RGB8_A1`, `ETC2_EAC_RGBA8`, `ETC2_EAC_SRGBA8`, …
- S3TC/DXT (desktop): `DXT1_RGB`, `DXT1_RGBA`, `DXT3_RGBA`, `DXT5_RGBA`, `DXT1_SRGB`, `DXT3_SRGBA`, `DXT5_SRGBA`, …
- ASTC: `RGBA_ASTC_4x4` … `RGBA_ASTC_12x12`, plus `SRGB8_ALPHA8_ASTC_4x4` … `_12x12`.
- RGTC (BC4/BC5): `RED_RGTC1`, `SIGNED_RED_RGTC1`, `RED_GREEN_RGTC2`, `SIGNED_RED_GREEN_RGTC2`.
- BPTC (BC6H/BC7): `RGB_BPTC_SIGNED_FLOAT`, `RGB_BPTC_UNSIGNED_FLOAT`, `RGBA_BPTC_UNORM`, `SRGB_ALPHA_BPTC_UNORM`.

Common picks: `RGBA8` (linear color), `SRGB8_A8` (sRGB color), `RGB8`/`SRGB8` (no alpha), `R8` (single-channel masks), `R11F_G11F_B10F` / `RGBA16F` (HDR).

### Usage / TextureUsage enum (verbatim)

A `uint16_t` bitmask — combine with `|`:

```cpp
enum class TextureUsage : uint16_t {
    NONE                = 0x0000,
    COLOR_ATTACHMENT    = 0x0001,  //!< usable as a color attachment
    DEPTH_ATTACHMENT    = 0x0002,  //!< usable as a depth attachment
    STENCIL_ATTACHMENT  = 0x0004,  //!< usable as a stencil attachment
    UPLOADABLE          = 0x0008,  //!< data can be uploaded into it (default)
    SAMPLEABLE          = 0x0010,  //!< sampleable (default)
    SUBPASS_INPUT       = 0x0020,
    BLIT_SRC            = 0x0040,
    BLIT_DST            = 0x0080,
    PROTECTED           = 0x0100,
    GEN_MIPMAPPABLE     = 0x0200,  //!< usable with generateMipmaps()
    DEFAULT             = UPLOADABLE | SAMPLEABLE,
    ALL_ATTACHMENTS     = COLOR_ATTACHMENT | DEPTH_ATTACHMENT | STENCIL_ATTACHMENT | SUBPASS_INPUT,
};
```

### Format / PixelDataFormat & Type / PixelDataType (verbatim)

These describe the *source* pixel data handed to `setImage`, independent of the texture's internal format.

```cpp
enum class PixelDataFormat : uint8_t {
    R, R_INTEGER, RG, RG_INTEGER, RGB, RGB_INTEGER, RGBA, RGBA_INTEGER,
    UNUSED, DEPTH_COMPONENT, DEPTH_STENCIL, ALPHA
};

enum class PixelDataType : uint8_t {
    UBYTE, BYTE, USHORT, SHORT, UINT, INT, HALF, FLOAT,
    COMPRESSED,            //!< see CompressedPixelDataType
    UINT_10F_11F_11F_REV, USHORT_565, UINT_2_10_10_10_REV,
};
```

### Texture Uploading texels (setImage + PixelBufferDescriptor)

```cpp
// Full sub-image form (3D / 2D-array / cubemap-as-6-layers):
void setImage(Engine& engine, size_t level,
        uint32_t xoffset, uint32_t yoffset, uint32_t zoffset,
        uint32_t width, uint32_t height, uint32_t depth,
        PixelBufferDescriptor&& buffer) const;

// Inline 2D helpers (cover the whole level / a sub-rect):
void setImage(Engine& engine, size_t level, PixelBufferDescriptor&& buffer) const;
void setImage(Engine& engine, size_t level,
        uint32_t xoffset, uint32_t yoffset, uint32_t width, uint32_t height,
        PixelBufferDescriptor&& buffer) const;
```

Constraints: `level < getLevels()`; the buffer's `Texture::Format` must match `getFormat()`'s expectations; the full/3D form requires `SAMPLER_3D`, `SAMPLER_2D_ARRAY`, or `SAMPLER_CUBEMAP`. Async variant: `setImageAsync(...)` (returns `AsyncCallId`).

**Worked example (`suzanne.cpp`, normal map — note the free-after-upload callback):**

```cpp
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
        (Texture::PixelBufferDescriptor::Callback) &stbi_image_free); // frees `data` after upload
normalMap->setImage(*engine, 0, std::move(buffer));
normalMap->generateMipmaps(*engine);
```

### Mipmaps & cubemaps

```cpp
void generateMipmaps(Engine& engine) const;
```
Requires a color-renderable format and `usage` with `BLIT_SRC | BLIT_DST` (set automatically if unspecified). No effect on `SAMPLER_3D`. To get all levels generated, build with a large `levels()` value (samples use `0xff`).

Cubemap faces are laid out as a 2D array of six layers, addressed by `zoffset`/`depth` in the full `setImage`. Face order convention (matching OpenGL): +x, -x, +y, -y, +z, -z.

```cpp
enum class TextureCubemapFace : uint8_t {
    POSITIVE_X = 0, NEGATIVE_X = 1, POSITIVE_Y = 2,
    NEGATIVE_Y = 3, POSITIVE_Z = 4, NEGATIVE_Z = 5,
};
```

---

## TextureSampler

`TextureSampler` is a small value type (not engine-owned, no `destroy`) that defines how a texture is read. You construct one and pass it to `MaterialInstance::setParameter(name, texture, sampler)`.

Defaults: `filterMag = NEAREST`, `filterMin = NEAREST`, `wrapS/T/R = CLAMP_TO_EDGE`, `compareMode = NONE`, `compareFunc = LE`, anisotropy 1.

Construction / mutation (verbatim signatures):

```cpp
TextureSampler() noexcept;                                            // all defaults
explicit TextureSampler(MagFilter minMag, WrapMode str = WrapMode::CLAMP_TO_EDGE) noexcept;
TextureSampler(MinFilter min, MagFilter mag, WrapMode str = WrapMode::CLAMP_TO_EDGE) noexcept;
TextureSampler(MinFilter min, MagFilter mag, WrapMode s, WrapMode t, WrapMode r) noexcept;
explicit TextureSampler(CompareMode mode, CompareFunc func = CompareFunc::LE) noexcept;

void setMinFilter(MinFilter v) noexcept;
void setMagFilter(MagFilter v) noexcept;
void setWrapModeS(WrapMode v) noexcept;   // setWrapModeT, setWrapModeR
void setAnisotropy(float anisotropy) noexcept;   // power-of-two, max 128
void setCompareMode(CompareMode mode, CompareFunc func = CompareFunc::LE) noexcept;
```

**Worked example (`suzanne.cpp`):**

```cpp
TextureSampler sampler(TextureSampler::MinFilter::LINEAR_MIPMAP_LINEAR,
                       TextureSampler::MagFilter::LINEAR);
materialInstance->setParameter("albedo", albedoTexture, sampler);
```

### Filter / Wrap / Compare enums (verbatim)

```cpp
enum class SamplerWrapMode : uint8_t {   // TextureSampler::WrapMode
    CLAMP_TO_EDGE, REPEAT, MIRRORED_REPEAT,
};

enum class SamplerMinFilter : uint8_t {  // TextureSampler::MinFilter
    NEAREST = 0, LINEAR = 1,
    NEAREST_MIPMAP_NEAREST = 2, LINEAR_MIPMAP_NEAREST = 3,
    NEAREST_MIPMAP_LINEAR  = 4, LINEAR_MIPMAP_LINEAR  = 5,
};

enum class SamplerMagFilter : uint8_t {  // TextureSampler::MagFilter
    NEAREST = 0, LINEAR = 1,
};

enum class SamplerCompareMode : uint8_t { NONE = 0, COMPARE_TO_TEXTURE = 1 };

enum class SamplerCompareFunc : uint8_t { // TextureSampler::CompareFunc (also reused as DepthFunc/StencilCompareFunc)
    LE = 0, // Less or equal
    GE,     // Greater or equal
    L,      // Strictly less than
    G,      // Strictly greater than
    E,      // Equal
    NE,     // Not equal
    A,      // Always (test deactivated)
    N,      // Never (test always fails)
};
```

Depth textures can't be sampled with a linear filter unless `compareMode` is `COMPARE_TO_TEXTURE`.

---

## Material

A `Material` is built from a **compiled `.filamat` package** (binary blob produced by `matc` or `libfilamat`). It is a template; you spawn `MaterialInstance` objects from it.

```cpp
// Build from a package:
Material::Builder& package(const void* payload, size_t size);   // payload must stay valid until build()
template<typename T> Material::Builder& constant(const char* name, T value);  // specialize a constant (int32_t/float/bool)
Material::Builder& sphericalHarmonicsBandCount(size_t shBandCount) noexcept;  // 1, 2, or 3 (default)
Material::Builder& shadowSamplingQuality(ShadowSamplingQuality quality) noexcept; // HARD (2x2 PCF) / LOW (3x3 gaussian)
Material::Builder& uboBatching(UboBatchingMode mode) noexcept;  // DEFAULT / DISABLED
Material* build(Engine& engine) const;   // returns nullptr on error if exceptions disabled

// Instances:
MaterialInstance* createInstance(const char* name = nullptr) const noexcept;  // free with engine->destroy(...)
MaterialInstance*       getDefaultInstance() noexcept;
MaterialInstance const* getDefaultInstance() const noexcept;
```

Introspection: `getName()`, `hasParameter(name)` (with `const char*` and `std::string_view` overloads), `isSampler(name)`, `getParameterCount()`, `getParameters(out, count)`, `getRequiredAttributes()`, `getShading()`, `getBlendingMode()`, `getMaterialDomain()`, `getFeatureLevel()`, etc. Convenience setters `setDefaultParameter(...)` write through to `getDefaultInstance()`. Async shader compilation: `compile(priority, variants, handler, callback)`.

**Worked example (`hellotriangle.cpp` / `suzanne.cpp`):**

```cpp
app.mat = Material::Builder()
        .package(RESOURCES_BAKEDCOLOR_DATA, RESOURCES_BAKEDCOLOR_SIZE)
        .build(*engine);
// either use the shared default instance:
renderableBuilder.material(0, app.mat->getDefaultInstance());
// or create dedicated instances:
MaterialInstance* mi = app.material->createInstance();
```

---

## MaterialInstance

Holds the concrete parameter values for a `Material`, plus per-instance render-state overrides. Free with `engine->destroy(materialInstance)`; duplicate with the static `MaterialInstance::duplicate(other, name)`.

### setParameter overloads

Scalars / vectors / matrices (template; the type must be one of the supported set):

```cpp
template<typename T> void setParameter(const char* name, T const& value);          // single value
template<typename T> void setParameter(const char* name, const T* values, size_t count); // array
```
Supported `T`: `float`, `int32_t`, `uint32_t`, `int2/3/4`, `uint2/3/4`, `float2/3/4`, `mat4f`, plus the slower (layout-converted) `bool`, `bool2/3/4`, `mat3f`.

Textures (texture + sampler):

```cpp
void setParameter(const char* name, Texture const* texture, TextureSampler const& sampler);
```

Colors (with color-space tag):

```cpp
void setParameter(const char* name, RgbType  type, math::float3 color);  // RGB
void setParameter(const char* name, RgbaType type, math::float4 color);  // RGBA
```

```cpp
enum class RgbType  : uint8_t { sRGB, LINEAR };
enum class RgbaType : uint8_t { sRGB, LINEAR, PREMULTIPLIED_sRGB, PREMULTIPLIED_LINEAR };
```

Specialization constants (overridden per-instance; `T` ∈ {`int32_t`, `float`, `bool`}):

```cpp
template<typename T> void setConstant(const char* name, T value);
```

Each `setParameter`/`setConstant` has overloads taking a `(name, nameLength)` pair, a string literal, or a null-terminated C string. `setParameter` throws `PreConditionPanic` if `name` doesn't exist (or is a no-op when exceptions are disabled) — guard with `Material::hasParameter`. `getParameter<T>(name)` reads non-texture values back.

**Worked example (`suzanne.cpp` / `hellopbr.cpp`):**

```cpp
mi->setParameter("baseColor", RgbType::LINEAR, float3{0.8});
mi->setParameter("albedo",  albedoTex,  sampler);   // texture + sampler
mi->setParameter("metallic", metallicTex, sampler);
```

### Render-state overrides

Per-instance overrides of the parent material's defaults (verbatim signatures):

```cpp
void setScissor(uint32_t left, uint32_t bottom, uint32_t width, uint32_t height) noexcept;
void unsetScissor() noexcept;
void setPolygonOffset(float scale, float constant) noexcept;   // costly: disables early-Z; avoid unless needed
void setMaskThreshold(float threshold) noexcept;               // MASKED blend cutoff (default 0.4)
void setSpecularAntiAliasingVariance(float variance) noexcept; // default 0.15
void setSpecularAntiAliasingThreshold(float threshold) noexcept; // default 0.2
void setDoubleSided(bool doubleSided) noexcept;                // also disables backface culling when on
void setTransparencyMode(TransparencyMode mode) noexcept;
void setCullingMode(CullingMode culling) noexcept;
void setCullingMode(CullingMode colorPassCulling, CullingMode shadowPassCulling) noexcept;
void setColorWrite(bool enable) noexcept;
void setDepthWrite(bool enable) noexcept;
void setDepthCulling(bool enable) noexcept;                    // i.e. depth testing
void setDepthFunc(DepthFunc depthFunc) noexcept;              // DepthFunc == SamplerCompareFunc
// Stencil:
void setStencilWrite(bool enable) noexcept;
void setStencilCompareFunction(StencilCompareFunc func, StencilFace face = StencilFace::FRONT_AND_BACK) noexcept;
void setStencilOpStencilFail(StencilOperation op, StencilFace face = StencilFace::FRONT_AND_BACK) noexcept;
void setStencilOpDepthFail(StencilOperation op,   StencilFace face = StencilFace::FRONT_AND_BACK) noexcept;
void setStencilOpDepthStencilPass(StencilOperation op, StencilFace face = StencilFace::FRONT_AND_BACK) noexcept;
void setStencilReferenceValue(uint8_t value, StencilFace face = StencilFace::FRONT_AND_BACK) noexcept;
void setStencilReadMask(uint8_t readMask,   StencilFace face = StencilFace::FRONT_AND_BACK) noexcept;
void setStencilWriteMask(uint8_t writeMask, StencilFace face = StencilFace::FRONT_AND_BACK) noexcept;
// PostProcess/compute-domain instances must be committed manually (no-op for surface domain):
void commit(Engine& engine) const;
```

Getters mirror the booleans/values (`isDoubleSided()`, `getCullingMode()`, `getDepthFunc()`, `isDepthCullingEnabled()`, `getMaskThreshold()`, etc.).

### Enums for render state (verbatim)

```cpp
enum class CullingMode : uint8_t {  // MaterialInstance::CullingMode
    NONE,           //!< front and back faces visible
    FRONT,          //!< cull front faces (only back visible)
    BACK,           //!< cull back faces (only front visible)
    FRONT_AND_BACK, //!< geometry not visible
};

enum class TransparencyMode : uint8_t {  // MaterialInstance::TransparencyMode
    DEFAULT,
    TWO_PASSES_ONE_SIDE,
    TWO_PASSES_TWO_SIDES,
};

enum class StencilFace : uint8_t {
    FRONT = 0x1, BACK = 0x2, FRONT_AND_BACK = FRONT | BACK,
};

enum class StencilOperation : uint8_t {
    KEEP, ZERO, REPLACE, INCR, INCR_WRAP, DECR, DECR_WRAP, INVERT,
};
// DepthFunc / StencilCompareFunc == backend::SamplerCompareFunc (LE, GE, L, G, E, NE, A, N) — see above.
```

---

## Skybox

Fills untouched pixels of a Scene. Currently texture-based (a cubemap) or a constant color. Built with `Skybox::Builder`; destroyed with `engine->destroy(skybox)`.

```cpp
Skybox::Builder& environment(Texture* cubemap) noexcept;  // must be a cube map
Skybox::Builder& showSun(bool show) noexcept;             // needs a SUN light in the scene; default false
Skybox::Builder& intensity(float envIntensity) noexcept;  // lux; ignored when an IndirectLight is set; default 30000
Skybox::Builder& color(math::float4 color) noexcept;      // constant color; ignored if environment is set; default opaque black
Skybox::Builder& priority(uint8_t priority) noexcept;     // [0..7], default 7 (lowest, rendered last)
Skybox* build(Engine& engine);

void setColor(math::float4 color) noexcept;
void setLayerMask(uint8_t select, uint8_t values) noexcept;  // default 0x1
Texture const* getTexture() const noexcept;
```

Constant-color skybox (`hellotriangle.cpp`):

```cpp
app.skybox = Skybox::Builder().color({0.1, 0.125, 0.25, 1.0}).build(*engine);
scene->setSkybox(app.skybox);
```

The environment cubemap (and IBL data) is typically generated by the **cmgen** tool. For the full image-based-lighting concept, see `concepts-lighting-ibl.md`.

---

## IndirectLight

Environment lighting (global illumination): an irradiance component + a reflections (specular) component. Only one `IndirectLight` per Scene. Built with `IndirectLight::Builder`; destroyed with `engine->destroy(...)`. The resource-creation surface only:

```cpp
IndirectLight::Builder& reflections(Texture const* cubemap) noexcept;          // mip-mapped cubemap from cmgen
IndirectLight::Builder& irradiance(uint8_t bands, math::float3 const* sh) noexcept; // SH coefficients (bands 1/2/3 → 1/4/9 floats)
IndirectLight::Builder& radiance(uint8_t bands, math::float3 const* sh) noexcept;   // radiance as SH
IndirectLight::Builder& irradiance(Texture const* cubemap) noexcept;           // irradiance as a cubemap (alternative to SH)
IndirectLight::Builder& intensity(float envIntensity) noexcept;                // lux, default 30000
IndirectLight::Builder& rotation(math::mat3f const& rotation) noexcept;        // rigid-body transform of the IBL
IndirectLight* build(Engine& engine);

void setIntensity(float intensity) noexcept;
void setRotation(math::mat3f const& rotation) noexcept;
Texture const* getReflectionsTexture() const noexcept;
Texture const* getIrradianceTexture() const noexcept;
```

Irradiance is normally derived automatically from the reflections cubemap; supply SH or an irradiance cubemap only to override. Helper estimators `getDirectionEstimate(sh)` / `getColorEstimate(sh, dir)` derive a dominant directional-light direction/color from 3-band SH. Reflections/irradiance/SH data come from the **cmgen** tool. Full IBL workflow: see `concepts-lighting-ibl.md`.

---

## BufferDescriptor & PixelBufferDescriptor (the upload+free contract)

Upload methods take ownership of a descriptor by rvalue (`&&` + `std::move`). A descriptor wraps:
- a pointer to your CPU data and its size in bytes,
- (for `PixelBufferDescriptor`) the source `Format` + `Type`,
- an optional **completion callback** that fires once Filament has consumed the data.

`BufferDescriptor` is `VertexBuffer::BufferDescriptor` / `IndexBuffer::BufferDescriptor` / `BufferObject::BufferDescriptor` (all `= backend::BufferDescriptor`). `PixelBufferDescriptor` is `Texture::PixelBufferDescriptor` (`= backend::PixelBufferDescriptor`).

Patterns:
- Pass `nullptr` as the callback when the source data outlives the upload (e.g. a `static const` array, as in `hellotriangle.cpp`).
- Pass a `Callback` (and optional user pointer) when the data must be freed after upload — Filament invokes it on the appropriate thread once the data is consumed. The `suzanne.cpp` normal map uses `&stbi_image_free` so the decoded image is released automatically.

```cpp
// outlives upload — no callback:
VertexBuffer::BufferDescriptor(TRIANGLE_VERTICES, 36, nullptr);

// free after upload — callback releases `data`:
Texture::PixelBufferDescriptor(data, byteCount,
        Texture::Format::RGB, Texture::Type::UBYTE,
        (Texture::PixelBufferDescriptor::Callback) &stbi_image_free);
```

---

## End-to-End Resource Flow

Putting the pieces together (composed from `hellotriangle.cpp` and `suzanne.cpp`):

```cpp
// 1) Geometry
VertexBuffer* vb = VertexBuffer::Builder()
        .vertexCount(n).bufferCount(1)
        .attribute(VertexAttribute::POSITION, 0, VertexBuffer::AttributeType::FLOAT3)
        .attribute(VertexAttribute::UV0,      0, VertexBuffer::AttributeType::FLOAT2, 12, 20)
        .build(*engine);
vb->setBufferAt(*engine, 0, VertexBuffer::BufferDescriptor(verts, vertsBytes, nullptr));

IndexBuffer* ib = IndexBuffer::Builder()
        .indexCount(m).bufferType(IndexBuffer::IndexType::UINT)
        .build(*engine);
ib->setBuffer(*engine, IndexBuffer::BufferDescriptor(indices, indicesBytes, nullptr));

// 2) Texture
Texture* tex = Texture::Builder()
        .width(w).height(h).levels(0xff)
        .format(Texture::InternalFormat::SRGB8_A8)
        .usage(Texture::Usage::DEFAULT | Texture::Usage::GEN_MIPMAPPABLE)
        .sampler(Texture::Sampler::SAMPLER_2D)
        .build(*engine);
tex->setImage(*engine, 0, Texture::PixelBufferDescriptor(pixels, pixelBytes,
        Texture::Format::RGBA, Texture::Type::UBYTE, freeCallback));
tex->generateMipmaps(*engine);
TextureSampler sampler(TextureSampler::MinFilter::LINEAR_MIPMAP_LINEAR,
                       TextureSampler::MagFilter::LINEAR);

// 3) Material + instance
Material* mat = Material::Builder().package(matData, matSize).build(*engine);
MaterialInstance* mi = mat->createInstance();
mi->setParameter("baseColor", tex, sampler);
mi->setParameter("metallic", 0.0f);

// ... attach vb/ib/mi to a renderable via RenderableManager (see engine-api-entities-components.md) ...

// 4) Teardown — destroy everything through the engine:
engine->destroy(mi);
engine->destroy(mat);
engine->destroy(tex);
engine->destroy(vb);
engine->destroy(ib);
```

For wiring these resources into a drawable entity (RenderableManager geometry/material binding), see `engine-api-entities-components.md`.
