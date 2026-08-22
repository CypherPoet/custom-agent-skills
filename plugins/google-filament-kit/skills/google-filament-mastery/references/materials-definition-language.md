# Material Definition Language (.mat)

> Source: Filament Materials — "Material definitions" + "Sampler usage" (Materials.md), Filament v1.75.0
> Last synced: 2026-08-14

A `.mat` material definition is a text file describing everything a material needs: name, user parameters, material model, required attributes, interpolants (called _variables_), raster state (blending mode, etc.), and shader code (fragment shader, optionally vertex shader). It is compiled into a `.filamat` package by the `matc` command-line tool.

## Table of Contents

| Section | Covers |
|---|---|
| [File structure (the three blocks)](#file-structure-the-three-blocks) | Mandatory material and fragment blocks, optional vertex code, ESSL stage entry points, and nonshader versus shader responsibilities |
| [JSONish format rules](#jsonish-format-rules) | Optional and space-required quoting, raw shader blocks, line comments, case-sensitive keys, and case-insensitive values |
| [Material block keys](#material-block-keys) | Models and feature levels, parameters and constants, attributes and varyings, domains, blending and refraction, raster state, lighting, shadows, anti-aliasing, and custom shading |
| [Parameter types](#parameter-types) | Scalar, vector, matrix and sampler declarations, precision, sampler format and filtering, fixed arrays, and external-texture transforms |
| [Constant types](#constant-types) | Signed integer, floating-point, and Boolean specialization constants with optional runtime fallbacks |
| [Vertex block](#vertex-block) | Required entry point, vertex inputs and precision-shifted world position, UV flipping, custom attributes, variables, and bufferless procedural rendering |
| [Fragment block](#fragment-block) | Required material preparation order, per-model inputs, normal-map timing, refraction fields, and lit-only per-light custom surface shading |
| [Shader public APIs](#shader-public-apis) | Type aliases and math, coordinate matrices, viewport, camera, time and exposure constants, material globals, vertex attributes and indices, and fragment geometry, UV, color, tone, and render-target helpers |
| [Sampler usage by feature level](#sampler-usage-by-feature-level) | The number of usable sampler parameters depends on material properties, shading model, feature level, and variant filter |
| [Complete example: textured lit material](#complete-example-textured-lit-material) | Lit PBR declarations, required UV and tangent attributes, normal unpacking before preparation, tiled base-color sampling, and scalar metallic and roughness parameters |

---

## File structure (the three blocks)

A material definition is composed of up to 3 top-level blocks using JSON object notation:

```glsl
material {
    // material properties
}

vertex {
    // vertex shader, optional
}

fragment {
    // fragment shader
}
```

- A minimum viable material **must** contain a `material` preamble and a `fragment` block.
- The `vertex` block is **optional**.
- The `material` block holds non-shader data (key/value pairs).
- The `vertex` and `fragment` blocks contain GLSL-like shader code (ESSL 3.0). They map to the vertex and fragment shader stages: `vertex` runs per-vertex (`materialVertex` function), `fragment` runs per-fragment (`material` function).

## JSONish format rules

The format is loosely based on JSON, called _JSONish_:

- A pair is `key : value`. Quotes around string values are **optional** in JSONish (`key : value` is valid), but **mandatory when the string contains spaces** (`name : "Wet pavement"`).
- The `vertex` and `fragment` blocks contain unescaped, unquoted GLSL code (not valid JSON).
- Single-line C++-style comments (`//`) are allowed.
- The **key** of a pair is **case-sensitive**.
- The **value** of a pair is **not case-sensitive**.

---

## Material block keys

The `material` block is mandatory and contains a list of property pairs describing all non-shader data. Below, each key lists its type, allowed values (verbatim), and default.

### General

| Key | Type | Allowed values / default |
|-----|------|--------------------------|
| `name` | string | Any string. Double quotes required if it contains spaces. Retained at runtime for debugging. |
| `featureLevel` | number | `1`, `2`, or `3`. Defaults to `1`. (See feature-level table below.) |
| `shadingModel` | string | `lit`, `subsurface`, `cloth`, `unlit`, `specularGlossiness`. Defaults to `lit`. |
| `parameters` | array of objects | Each object has `name` + `type` (see [Parameter types](#parameter-types)), optional `precision`. |
| `constants` | array of objects | Each object has `name` + `type` (`int`/`float`/`bool`), optional `default`. |
| `variantFilter` | array of string | Each entry: `dynamicLighting`, `directionalLighting`, `shadowReceiver`, `skinning`, `ssr`, `stereo`. |
| `flipUV` | boolean | `true` or `false`. Defaults to `true`. Flips Y of UV attributes (`y = 1.0 - y`). |
| `linearFog` | boolean | `true` or `false`. Defaults to `false`. Simplified fog equation. |
| `shadowFarAttenuation` | boolean | `true` or `false`. Defaults to `true`. |
| `quality` | string | `low`, `normal`, `high`, `default`. Defaults to `default`. |
| `instanced` | boolean | `true` or `false`. Defaults to `false`. Enables `getInstanceIndex()`. |
| `vertexDomainDeviceJittered` | boolean | `true` or `false`. Defaults to `false`. Only meaningful for `vertexDomain:device`. |
| `useDefaultDepthVariant` | boolean | `true` or `false`. Defaults to `false`. Only meaningful with a vertex block; do not set `true` if the vertex block modifies `worldPosition`. |

**featureLevel guaranteed features:**

| Feature Level | Guaranteed features |
|:--------------|:--------------------|
| 1 | 9 textures per material |
| 2 | 9 textures per material, cubemap arrays, ESSL 3.10 |
| 3 | 12 textures per material, cubemap arrays, ESSL 3.10 |

A given feature level supports all features of lower levels. `matc` does **not** verify a material stays within its selected feature level (known bug).

**variantFilter** — lists shader variants the app guarantees will never be needed; they are skipped during code generation to shrink the material. Variant meanings:
- `directionalLighting` — a directional light is present in the scene
- `dynamicLighting` — a non-directional light (point, spot, etc.) is present
- `shadowReceiver` — an object can receive shadows
- `skinning` — an object is animated using GPU skinning
- `fog` — global fog is applied to the scene
- `vsm` — VSM shadows are enabled and the object is a shadow receiver
- `ssr` — screen-space reflections are enabled in the View
- `stereo` — stereoscopic rendering is enabled in the View

Lighting variants are automatically filtered out when compiling an `unlit` material. Filtering a variant required at runtime may crash.

```glsl
material {
    name : "Invisible shadow plane",
    shadingModel : unlit,
    shadowMultiplier : true,
    blending : transparent,
    variantFilter : [ skinning ]
}
```

**parameters** access in shaders:
- **Sampler types**: parameter name prefixed with `materialParams_` (e.g. `materialParams_myTexture`).
- **Other types**: a field of the `materialParams` struct (e.g. `materialParams.myColor`).

**constants** access in shaders: prefix the name with `materialConstants_` (e.g. `materialConstants_myConstant`). Constants are specialized at material-load time and cannot change afterward; they let the compiler generate more efficient code. If not set at runtime, the `default` is used.

```glsl
material {
    constants : [
        {
           name : overrideAlpha,
           type : bool
        },
        {
           name : customAlpha,
           type : float,
           default : 0.5
        }
    ],
    shadingModel : lit,
    blending : transparent,
}
```

### Vertex and attributes

| Key | Type | Allowed values / default |
|-----|------|--------------------------|
| `requires` | array of string | Each entry: `uv0`, `uv1`, `color`, `position`, `tangents`, `custom0` … `custom7`. |
| `variables` | array of string | Up to **5** strings, each a valid GLSL identifier (custom interpolants/varyings). |
| `vertexDomain` | string | `object`, `world`, `view`, `device`. Defaults to `object`. |
| `interpolation` | string | `smooth`, `flat`. Defaults to `smooth`. |

**requires** — `position` is always required and need not be listed. `tangents` is automatically required for any non-`unlit` shading model. Custom attributes `custom0`…`custom7` must be declared here before use.

**variables** — defines custom interpolants output by the vertex shader. Each interpolant is `float4` (`vec4`). Access: in the fragment shader use the `variable_` prefix (`variable_eyeDirection`); in the vertex shader use the `MaterialVertexInputs` member (`material.eyeDirection`). Default precision is `highp` in both stages. An alternate object syntax sets name + precision:

```glsl
variables : [
     eyeDirection,
     {
        name : eyeColor,
        precision : medium
     }
]
```

> **Interaction with `color`:** If `color` is in `requires`, only **four** variables are available instead of five.

**vertexDomain** — coordinate space of the rendered mesh, influencing vertex transform:
- **object** — object/model space; vertices transformed by the object's transform matrix.
- **world** — world space; not transformed by the object's transform.
- **view** — view/eye/camera space; not transformed by the object's transform.
- **device** — normalized device (clip) space; not transformed by the object's transform.

**interpolation** — `smooth` does perspective-correct interpolation per interpolant; `flat` does none (all fragments in a triangle shaded identically).

### Blending and transparency

| Key | Type | Allowed values / default |
|-----|------|--------------------------|
| `blending` | string | `opaque`, `transparent`, `fade`, `add`, `masked`, `multiply`, `screen`, `custom`. Defaults to `opaque`. |
| `blendFunction` | object | Fields `srcRGB`, `srcA`, `dstRGB`, `dstA` (used when `blending : custom`). |
| `postLightingBlending` | string | `opaque`, `transparent`, `add`. Defaults to `transparent`. |
| `transparency` | string | `default`, `twoPassesOneSide`, `twoPassesTwoSides`. Defaults to `default`. |
| `maskThreshold` | number | `0.0`–`1.0`. Defaults to `0.4`. (Only for `blending : masked`.) |
| `refractionMode` | string | `none`, `cubemap`, `screenspace`. Defaults to `none`. |
| `refractionType` | string | `solid`, `thin`. Defaults to `solid`. |

**blending** modes:
- **opaque** — blending disabled; the alpha channel is ignored.
- **transparent** — alpha-composited over the render target (Porter-Duff `source over`); assumes pre-multiplied alpha. Alpha applies to diffuse lighting only.
- **fade** — like `transparent`, but transparency also applies to specular lighting (useful to fade lit objects in/out).
- **add** — output added to the render target.
- **multiply** — output multiplied with the render target (darkens).
- **screen** — opposite of `multiply` (brightens).
- **masked** — blending disabled; enables alpha masking. The output alpha decides whether a fragment is discarded (see `maskThreshold`). `ALPHA_TO_COVERAGE` is enabled for non-translucent views (override with `alphaToCoverage : false`).
- **custom** — blending enabled with a user-specified function (see `blendFunction`).

**blendFunction** field values (each of `srcRGB`/`srcA`/`dstRGB`/`dstA`): `zero`, `one`, `srcColor`, `oneMinusSrcColor`, `dstColor`, `oneMinusDstColor`, `srcAlpha`, `oneMinusSrcAlpha`, `dstAlpha`, `oneMinusDstAlpha`, `srcAlphaSaturate`.

```glsl
material {
    blending : custom,
    blendFunction :
    {
        srcRGB: one,
        srcA: one,
        dstRGB: oneMinusSrcColor,
        dstA: oneMinusSrcAlpha
    }
}
```

**postLightingBlending** — how `postLightingColor` blends with lighting results. Modes: `opaque` (outputs `postLightingColor` directly), `transparent` (alpha-composited over `postLightingColor`, pre-multiplied alpha), `add`. (The source also describes `multiply` and `screen` behaviors, but the enum value list is `opaque`, `transparent`, `add`.)

**transparency** — only valid when `blending` is not `opaque` and `refractionMode` is `none`:
- `default` — rendered normally, honoring `culling`.
- `twoPassesOneSide` — depth pass then color pass, honoring `culling` (renders only one set of faces).
- `twoPassesTwoSides` — rendered twice in color (back faces, then front faces); reduces sorting issues. Combine with `doubleSided` for best effect.

**refractionMode** — `none` (off), `cubemap` (IBL cubemap only; efficient, no scene-object refraction), `screenspace` (advanced; refracts opaque scene objects). Defaults to `none`: a material is opted *into* refraction here. This is distinct from the View-level screen-space refraction pass, which is *enabled by default* (`View::setScreenSpaceRefractionEnabled(true)`) — so for glass you set `refractionMode` on the material; you do **not** need to "turn on" refraction at the View (it's already on). Don't conflate the material default (`none`) with the View default (enabled).

**refractionType** — `solid` (thick objects: crystal ball, ice cube — modeled as a sphere of radius `thickness`), `thin` (thin objects: window, soap bubble — modeled as flat of thickness `thickness`). Only meaningful when `refractionMode` is not `none`.

### Rasterization

| Key | Type | Allowed values / default |
|-----|------|--------------------------|
| `culling` | string | `none`, `front`, `back`, `frontAndBack`. Defaults to `back`. |
| `colorWrite` | boolean | `true` or `false`. Defaults to `true`. |
| `depthWrite` | boolean | `true` or `false`. Defaults to `true` for opaque, `false` for transparent. |
| `depthCulling` | boolean | `true` or `false`. Defaults to `true`. (Depth testing.) |
| `doubleSided` | boolean | `true` or `false`. Defaults to `false`. |
| `alphaToCoverage` | boolean | `true` or `false`. Defaults to `false`. Only meaningful with MSAA. |

**doubleSided** — when `true`, `culling` is automatically set to `none` and back-facing normals are flipped to front-facing. Explicit `false` lets double-sidedness be toggled at runtime.

**alphaToCoverage** — coverage derived from alpha. `blending : masked` auto-enables it; set `alphaToCoverage : false` to override.

### Lighting

| Key | Type | Allowed values / default |
|-----|------|--------------------------|
| `reflections` | string | `default`, `screenspace`. Defaults to `default`. |
| `shadowMultiplier` | boolean | `true` or `false`. Defaults to `false`. **`unlit` only.** |
| `transparentShadow` | boolean | `true` or `false`. Defaults to `false`. |
| `coloredPenumbra` | boolean | `true` or `false`. Defaults to `false`. |
| `clearCoatIorChange` | boolean | `true` or `false`. Defaults to `true`. |
| `multiBounceAmbientOcclusion` | boolean | `true` or `false`. Defaults to `false` on mobile, `true` on desktop. |
| `specularAmbientOcclusion` | string | `none`, `simple`, `bentNormals`. Defaults to `none` on mobile, `simple` on desktop. (`true`/`false` also accepted, mapping to `simple`/`none`.) |

- **reflections** — `default` uses image-based lights only; `screenspace` adds screen-space color-buffer reflections.
- **shadowMultiplier** — `unlit` only; multiplies final color by the shadowing factor (e.g. invisible AR ground plane). Directional-light shadows only.
- **transparentShadow** — emulates transparent shadows via dithering; works best with VSM + blur. Shadow opacity comes from `baseColor` alpha. Can be enabled on opaque objects.
- **coloredPenumbra** — tints the shadow penumbra. Color source by `shadingModel`: `lit`/`specularGlossiness` → saturated diffuse from `baseColor`; `subsurface`/`cloth` → `subsurfaceColor`; `unlit` → N/A. Always enabled for `subsurface` materials.
- **specularAmbientOcclusion** — `simple` is a cheap approximation; `bentNormals` is more accurate but more expensive.

### Anti-aliasing

| Key | Type | Allowed values / default |
|-----|------|--------------------------|
| `specularAntiAliasing` | boolean | `true` or `false`. Defaults to `false`. |
| `specularAntiAliasingVariance` | float | `0`–`1`. Defaults to `0.15`. |
| `specularAntiAliasingThreshold` | float | `0`–`1`. Defaults to `0.2`. (Set `0` to disable.) |

### Shading

| Key | Type | Allowed values / default |
|-----|------|--------------------------|
| `customSurfaceShading` | bool | `true` or `false`. Defaults to `false`. Requires a `surfaceShading` function in the fragment block. `lit` only. |

---

## Parameter types

Each `parameters` entry is an object with `name` (valid GLSL identifier) and `type`. Optional `precision`: one of `default` (best for platform — typically `high` desktop, `medium` mobile), `low`, `medium`, `high`.

| Type | Description |
|:-----|:------------|
| `bool` | Single boolean |
| `bool2` | Vector of 2 booleans |
| `bool3` | Vector of 3 booleans |
| `bool4` | Vector of 4 booleans |
| `float` | Single float |
| `float2` | Vector of 2 floats |
| `float3` | Vector of 3 floats |
| `float4` | Vector of 4 floats |
| `int` | Single integer |
| `int2` | Vector of 2 integers |
| `int3` | Vector of 3 integers |
| `int4` | Vector of 4 integers |
| `uint` | Single unsigned integer |
| `uint2` | Vector of 2 unsigned integers |
| `uint3` | Vector of 3 unsigned integers |
| `uint4` | Vector of 4 unsigned integers |
| `float3x3` | Matrix of 3x3 floats |
| `float4x4` | Matrix of 4x4 floats |
| `sampler2d` | 2D texture |
| `sampler2dArray` | Array of 2D textures |
| `samplerExternal` | External texture (platform-specific) |
| `samplerCubemap` | Cubemap texture |

**Sampler fields** (on sampler-type entries):
- `format` — `int` or `float` (defaults to `float`).
- `multisample` — boolean, whether the sampler is for multisampling (defaults to `false`).
- `filterable` — boolean. When `format` is `int`, assumed `false` and cannot be set. When `format` is `float`, defaults to `true`; set `false` explicitly for unfiltered sampling.

**Arrays** — append `[size]` to a non-sampler type for an array (e.g. `float[9]` is nine floats). Samplers cannot be arrayed this way (arrays are separate types). For Android external textures, an optional `transformName` parameter names the material parameter exposing the transform matrix (always identity on iOS/Vulkan).

## Constant types

Each `constants` entry has `name` (valid GLSL identifier) and `type`, with an optional `default`:

| Type | Description | Default |
|:-----|:------------|:--------|
| `int` | A signed, 32-bit GLSL int | `0` |
| `float` | A single-precision GLSL float | `0.0` |
| `bool` | A GLSL bool | `false` |

---

## Vertex block

Optional; controls the vertex shading stage. Must contain valid ESSL 3.0 code and **must** declare the `materialVertex` function:

```glsl
vertex {
    void materialVertex(inout MaterialVertexInputs material) {
        // vertex shading code
    }
}
```

Invoked automatically at runtime. Read/modify material properties via the `MaterialVertexInputs` struct — compute custom variables/interpolants or modify attribute values. All [Shader public APIs](#shader-public-apis) (and the [vertex-only APIs](#vertex-only-apis)) are available here.

```glsl
material {
    requires : [uv0, color]
}
vertex {
    void materialVertex(inout MaterialVertexInputs material) {
        material.color *= sin(getUserTime().x);
        material.uv0 *= sin(getUserTime().x);
    }
}
```

### MaterialVertexInputs struct

```glsl
struct MaterialVertexInputs {
    float4 color;              // if the color attribute is required
    float2 uv0;                // if the uv0 attribute is required
    float2 uv1;                // if the uv1 attribute is required
    float3 worldNormal;        // only if the shading model is not unlit
    float4 worldPosition;      // always available (see note below about world-space)

    mat4   clipSpaceTransform; // default: identity, transforms the clip-space position, only available for `vertexDomain:device`

    // variable* names are replaced with actual names
    float4 variable0;          // if 1 or more variables is defined
    float4 variable1;          // if 2 or more variables is defined
    float4 variable2;          // if 3 or more variables is defined
    float4 variable3;          // if 4 or more variables is defined
};
```

- `worldPosition` in the vertex shader is shifted by the camera position for precision. Use `getUserWorldPosition()` for true world-space (may not fit a `float` / reduced precision).
- By default the vertex shader flips UV Y: `material.uv0 = vec2(mesh_uv0.x, 1.0 - mesh_uv0.y)`. Disable via `flipUV : false`.

### Custom vertex attributes

Up to **8** custom vertex attributes, all `float4`, accessed via `getCustom0()`…`getCustom7()`. They must be declared in `requires`:

```glsl
material {
    requires : [
        custom0,
        custom1,
        custom2
    ]
}
```

### Procedural / attribute-less rendering

Render geometry generated entirely in the vertex shader (no vertex/index buffers):
1. Call `getVertexIndex()` in the vertex block (maps to `gl_VertexID` / `gl_VertexIndex` / `[[vertex_id]]`).
2. Omit `requires` attributes; pass fragment data via `variables`.
3. C++: build a `VertexBuffer` with `bufferCount(0)` and non-zero `vertexCount(...)`.
4. C++: use the non-indexed `geometry()` overload (omit the `IndexBuffer`).

Requires `featureLevel : 1` or higher; incompatible with skinning and morphing.

```glsl
material {
    name : ProceduralQuad,
    shadingModel : unlit,
    culling : none,
    parameters : [
        {
            type : sampler2d,
            name : albedo
        }
    ],
    variables : [
        quadUV
    ],
}

vertex {
    void materialVertex(inout MaterialVertexInputs material) {
        const vec2 positions[6] = vec2[6](
            vec2(-0.5, -0.5), vec2( 0.5, -0.5), vec2(-0.5,  0.5),
            vec2( 0.5, -0.5), vec2( 0.5,  0.5), vec2(-0.5,  0.5)
        );
        const vec2 uvs[6] = vec2[6](
            vec2(0.0, 0.0), vec2(1.0, 0.0), vec2(0.0, 1.0),
            vec2(1.0, 0.0), vec2(1.0, 1.0), vec2(0.0, 1.0)
        );

        int vid = getVertexIndex();
        material.worldPosition = vec4(positions[vid], 0.0, 1.0);
        material.quadUV        = vec4(uvs[vid], 0.0, 0.0);
    }
}

fragment {
    void material(inout MaterialInputs material) {
        prepareMaterial(material);
        material.baseColor = texture(materialParams_albedo, variable_quadUV.xy);
    }
}
```

---

## Fragment block

Mandatory; controls the fragment shading stage. Must contain valid ESSL 3.0 code and **must** declare the `material` function:

```glsl
fragment {
    void material(inout MaterialInputs material) {
        prepareMaterial(material);
        // fragment shading code
    }
}
```

The goal of `material()` is to compute the properties for the selected shading model. Example — glossy red metal (standard `lit`):

```glsl
fragment {
    void material(inout MaterialInputs material) {
        prepareMaterial(material);
        material.baseColor.rgb = vec3(1.0, 0.0, 0.0);
        material.metallic = 1.0;
        material.roughness = 0.0;
    }
}
```

### prepareMaterial requirement

You **must** call `prepareMaterial(material)` before exiting `material()`. It sets up the material model's internal state.

- APIs like `shading_normal` / `getWorldNormalVector()` can only be accessed **after** `prepareMaterial()`.
- The `normal` property only has effect when modified **before** `prepareMaterial()`. Example with bump mapping:

```glsl
fragment {
    void material(inout MaterialInputs material) {
        // fetch the normal in tangent space (before prepareMaterial)
        vec3 normal = texture(materialParams_normalMap, getUV0()).xyz;
        material.normal = normal * 2.0 - 1.0;

        prepareMaterial(material);

        // from now on, shading_normal, etc. can be accessed
        material.baseColor.rgb = vec3(1.0, 0.0, 0.0);
        material.metallic = 0.0;
        material.roughness = 1.0;
    }
}
```

### MaterialInputs struct (fields per shading model)

```glsl
struct MaterialInputs {
    float4 baseColor;           // default: float4(1.0)
    float4 emissive;            // default: float4(0.0, 0.0, 0.0, 1.0)
    float4 postLightingColor;   // default: float4(0.0)

    // no other field is available with the unlit shading model
    float  roughness;           // default: 1.0
    float  metallic;            // default: 0.0, not available with cloth or specularGlossiness
    float  reflectance;         // default: 0.5, not available with cloth or specularGlossiness
    float  ambientOcclusion;    // default: 0.0

    // not available when the shading model is subsurface or cloth
    float3 sheenColor;          // default: float3(0.0)
    float  sheenRoughness;      // default: 0.0
    float  clearCoat;           // default: 1.0
    float  clearCoatRoughness;  // default: 0.0
    float3 clearCoatNormal;     // default: float3(0.0, 0.0, 1.0)
    float  anisotropy;          // default: 0.0
    float3 anisotropyDirection; // default: float3(1.0, 0.0, 0.0)

    // only available when the shading model is subsurface or refraction is enabled
    float  thickness;           // default: 0.5

    // only available when the shading model is subsurface
    float  subsurfacePower;     // default: 12.234
    float3 subsurfaceColor;     // default: float3(1.0)

    // only available when the shading model is cloth
    float3 sheenColor;          // default: sqrt(baseColor)
    float3 subsurfaceColor;     // default: float3(0.0)

    // only available when the shading model is specularGlossiness
    float3 specularColor;       // default: float3(0.0)
    float  glossiness;          // default: 0.0

    // not available when the shading model is unlit
    // must be set before calling prepareMaterial()
    float3 normal;              // default: float3(0.0, 0.0, 1.0)

    // only available when refraction is enabled
    float transmission;         // default: 1.0
    float3 absorption;          // default float3(0.0, 0.0, 0.0)
    float ior;                  // default: 1.5
    float microThickness;       // default: 0.0, not available with refractionType "solid"
    float dispersion;           // default: 0.0, not available with refractionType "thin"
}
```

### Custom surface shading

When `customSurfaceShading : true` (in the `material` block), the fragment block **must** also declare `surfaceShading`. **`lit` only** — any other model is an error.

```glsl
fragment {
    void material(inout MaterialInputs material) {
        prepareMaterial(material);
        // prepare material inputs
    }

    vec3 surfaceShading(
        const MaterialInputs materialInputs,
        const ShadingData shadingData,
        const LightData lightData
    ) {
        return vec3(1.0); // output of custom lighting (linear sRGB RGB)
    }
}
```

`surfaceShading` is invoked for every light that may influence the fragment (including fully shadowed ones, where `lightData.NdotL <= 0.0` or `lightData.visibility <= 0.0`). Alpha blending/masking are handled outside it.

```glsl
struct ShadingData {
    vec3  diffuseColor;        // diffuse color from baseColor + metallic, pre-multiplied alpha, linear sRGB
    vec3  f0;                  // specular color from baseColor + metallic, pre-multiplied alpha, linear sRGB
    float perceptualRoughness; // roughness from MaterialInputs, clamped/filtered; 0.0–1.0
    float roughness;           // square of perceptualRoughness; 0.0–1.0
};

struct LightData {
    vec4  colorIntensity; // .rgb color (linear sRGB), .w pre-exposed intensity
    vec3  l;              // normalized light vector in world space (fragment -> light)
    float NdotL;          // saturate(dot(getWorldSpaceNormal(), l)); 0.0–1.0
    vec3  worldPosition;  // light position in world space
    float attenuation;    // distance attenuation; 0.0–1.0 (always 1.0 for directional)
    float visibility;     // shadow/occlusion factor; 0.0–1.0
};
```

---

## Shader public APIs

Available in vertex and/or fragment blocks. Use the type aliases over raw GLSL types.

### Type aliases

| Name | GLSL type | Description |
|:-----|:----------|:------------|
| `bool2` | bvec2 | Vector of 2 booleans |
| `bool3` | bvec3 | Vector of 3 booleans |
| `bool4` | bvec4 | Vector of 4 booleans |
| `int2` | ivec2 | Vector of 2 integers |
| `int3` | ivec3 | Vector of 3 integers |
| `int4` | ivec4 | Vector of 4 integers |
| `uint2` | uvec2 | Vector of 2 unsigned integers |
| `uint3` | uvec3 | Vector of 3 unsigned integers |
| `uint4` | uvec4 | Vector of 4 unsigned integers |
| `float2` | vec2 | Vector of 2 floats |
| `float3` | vec3 | Vector of 3 floats |
| `float4` | vec4 | Vector of 4 floats |
| `float4x4` | mat4 | A 4x4 float matrix |
| `float3x3` | mat3 | A 3x3 float matrix |

### Math

| Name | Type | Description |
|:-----|:-----|:------------|
| `PI` | float | The constant π |
| `HALF_PI` | float | The constant π/2 |
| `saturate(float x)` | float | Clamps the value between 0.0 and 1.0 |
| `pow5(float x)` | float | Computes x⁵ |
| `sq(float x)` | float | Computes x² |
| `max3(float3 v)` | float | Maximum component of the `float3` |
| `mulMat4x4Float3(float4x4 m, float3 v)` | float4 | Returns m * v |
| `mulMat3x3Float3(float4x4 m, float3 v)` | float4 | Returns m * v |

### Matrices

| Name | Type | Description |
|:-----|:-----|:------------|
| `getViewFromWorldMatrix()` | float4x4 | World space → view/eye space |
| `getWorldFromViewMatrix()` | float4x4 | View/eye space → world space |
| `getClipFromViewMatrix()` | float4x4 | View/eye space → clip (NDC) space |
| `getViewFromClipMatrix()` | float4x4 | Clip (NDC) space → view/eye space |
| `getEyeFromViewMatrix()` | float4x4 | View space → eye space |
| `getEyeFromViewMatrix(int eyeIndex)` | float4x4 | View → eye space for the given eye |
| `getClipFromWorldMatrix()` | float4x4 | World → clip (NDC) space |
| `getClipFromWorldMatrix(int eyeIndex)` | float4x4 | World → clip (NDC) space for the given eye |
| `getWorldFromClipMatrix()` | float4x4 | Clip (NDC) space → world space |

### Frame constants

| Name | Type | Description |
|:-----|:-----|:------------|
| `getResolution()` | float4 | Physical viewport dims: `width`, `height`, `1/width`, `1/height` (may differ from `View::getViewport()` due to guard-bands) |
| `getWorldCameraPosition()` | float3 | Camera/eye position in world space |
| `getWorldOffset()` | float3 | [deprecated] Shift to API-level world space; use `getUserWorldPosition()` |
| `getUserWorldFromWorldMatrix()` | float4x4 | World space → API-level (user) world space |
| `getTime()` | float | Current time as a remainder of 1 second (0–1) |
| `getUserTime()` | float4 | Current time as a float-float pair: `(float)time`, `time - (float)time`, `0`, `0` |
| `getUserTimeMod(float m)` | float | Current time modulo m, in seconds |
| `getExposure()` | float | Photometric exposure of the camera |
| `getEV100()` | float | Exposure value at ISO 100 of the camera |

> Filament's "world space" does not necessarily match API-level world space (precision shift). For the API-level camera, transform `getWorldCameraPosition()` with `getUserWorldFromWorldMatrix()`.

`getUserTime()` splits a double-precision time value across its first two floats. Use both components with a float-float technique such as Dekker's algorithms when an animation needs more precision than `getUserTime().x` alone provides.

### Material globals

| Name | Type | Description |
|:-----|:-----|:------------|
| `getMaterialGlobal0()` | float4 | Set via `View::setMaterialGlobal(0, float4)`. Default `{0,0,0,1}`. |
| `getMaterialGlobal1()` | float4 | Set via `View::setMaterialGlobal(1, float4)`. Default `{0,0,0,1}`. |
| `getMaterialGlobal2()` | float4 | Set via `View::setMaterialGlobal(2, float4)`. Default `{0,0,0,1}`. |
| `getMaterialGlobal3()` | float4 | Set via `View::setMaterialGlobal(3, float4)`. Default `{0,0,0,1}`. |

### Vertex-only APIs

| Name | Type | Description |
|:-----|:-----|:------------|
| `getPosition()` | float4 | Vertex position in the material's domain (default object/model space) |
| `getCustom0()` … `getCustom7()` | float4 | Custom vertex attribute |
| `getWorldFromModelMatrix()` | float4x4 | Model (object) space → world space |
| `getWorldFromModelNormalMatrix()` | float3x3 | Normals: model (object) space → world space |
| `getVertexIndex()` | int | Index of the current vertex |
| `getEyeIndex()` | int | Index of the eye being rendered (starts at 0) |

### Fragment-only APIs

| Name | Type | Description |
|:-----|:-----|:------------|
| `getWorldTangentFrame()` | float3x3 | Columns: tangent (`frame[0]`), bi-tangent (`frame[1]`), normal (`frame[2]`) in world space. Only `normal` is valid unless a tangent-space normal / anisotropic shading is used. |
| `getWorldPosition()` | float3 | Fragment position in world space |
| `getUserWorldPosition()` | float3 | Fragment position in API-level (user) world space |
| `getWorldViewVector()` | float3 | Normalized world-space vector from fragment to eye |
| `getWorldNormalVector()` | float3 | Normalized world-space normal after bump mapping (after `prepareMaterial()`) |
| `getWorldGeometricNormalVector()` | float3 | Normalized world-space normal before bump mapping (usable before `prepareMaterial()`) |
| `getWorldReflectedVector()` | float3 | Reflection of view vector about the normal (after `prepareMaterial()`) |
| `getNormalizedViewportCoord()` | float3 | Normalized user viewport position (NDC normalized to [0,1] pos, [1,0] depth); usable before `prepareMaterial()` |
| `getNdotV()` | float | `dot(normal, view)`, strictly > 0 (after `prepareMaterial()`) |
| `getColor()` | float4 | Interpolated fragment color (if `color` attribute required) |
| `getUV0()` | float2 | First interpolated UV set (if `uv0` required) |
| `getUV1()` | float2 | Second interpolated UV set (if `uv1` required) |
| `getMaskThreshold()` | float | Mask threshold (only when `blending : masked`) |
| `inverseTonemap(float3)` | float3 | Inverse tone map of a linear sRGB color → linear sRGB |
| `inverseTonemapSRGB(float3)` | float3 | Inverse tone map of a non-linear sRGB color → linear sRGB |
| `luminance(float3)` | float | Luminance of a linear sRGB color |
| `ycbcrToRgb(float, float2)` | float3 | Luminance + CbCr → sRGB color |
| `uvToRenderTargetUV(float2)` | float2 | Transforms a UV to sample from a `RenderTarget` attachment (flips per backend) |

> When sampling a `filament::Texture` attached to a `filament::RenderTarget` (surface domain), pass UVs through `uvToRenderTargetUV`.

---

## Sampler usage by feature level

The number of usable sampler parameters depends on material properties, shading model, feature level, and variant filter.

### Feature level 1 and 2

- `unlit` materials: up to **12** samplers by default.
- `lit` materials: up to **9** samplers by default; reduced to **8** if `refractionMode` or `reflectionMode` is `screenspace`.
- If `variantFilter` contains the `fog` filter, an extra sampler is freed: `unlit` up to **13**, `lit` up to **10**.

### Feature level 3

- **16** samplers available.

> `external` samplers (`samplerExternal`) account for **2** regular samplers each.

---

## Complete example: textured lit material

A standard `lit` material sampling an sRGB base-color texture and a normal map, with scalar metallic/roughness parameters and UV tiling. Uses only documented syntax.

```glsl
material {
    name : "Textured PBR surface",
    shadingModel : lit,
    blending : opaque,
    requires : [
        uv0,
        tangents
    ],
    parameters : [
        {
            type : sampler2d,
            name : baseColorMap
        },
        {
            type      : sampler2d,
            name      : normalMap
        },
        {
            type : float,
            name : metallic
        },
        {
            type : float,
            name : roughness
        },
        {
            type : float2,
            name : uvScale
        }
    ]
}

fragment {
    void material(inout MaterialInputs material) {
        // sample and unpack the tangent-space normal BEFORE prepareMaterial()
        vec2 uv = getUV0() * materialParams.uvScale;
        vec3 normal = texture(materialParams_normalMap, uv).xyz;
        material.normal = normal * 2.0 - 1.0;

        prepareMaterial(material);

        material.baseColor = texture(materialParams_baseColorMap, uv);
        material.metallic  = materialParams.metallic;
        material.roughness = materialParams.roughness;
    }
}
```
