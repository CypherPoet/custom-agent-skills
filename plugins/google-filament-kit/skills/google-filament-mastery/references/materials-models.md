# Material Models

> Source: Filament Materials — "Material models" (Materials.md), Filament v1.75.0
> Last synced: 2026-08-14

## Table of Contents

| Section | Covers |
|---|---|
| [Core Concepts](#core-concepts) | Materials, shading models, source definitions, compiled packages and platform variants, parameterized instances, linear colors, premultiplied alpha, and tangent-space directions |
| [Choosing a Model](#choosing-a-model) | When to choose lit, subsurface, cloth, unlit, or legacy specular-glossiness shading |
| [Lit Model (Standard)](#lit-model-standard) | Base, metallic, roughness and reflectance roles, specular and sheen layers, costly coat and anisotropy switches, indirect shading, emissive exposure, refraction and absorption, dispersion, and shadows |
| [Subsurface Model](#subsurface-model) | Translucent-volume use cases, inherited lit inputs, thickness, scattering tint and power, and the source's missing type, range, and default details |
| [Cloth Model](#cloth-model) | Fabric scattering and fuzz, excluded metallic and reflectance inputs, sheen and subsurface tints, performance and shadow caveats, and cotton, denim, and velvet recipes |
| [Unlit Model](#unlit-model) | Lighting-free video, camera, UI, and debug use, direct base color, exposure-weighted emissive output, and post-lighting blending |
| [Specular Glossiness (Legacy)](#specular-glossiness-legacy) | Legacy glTF compatibility, nonphysical limitations, omitted metallic-roughness inputs, and replacement diffuse, specular-color, and glossiness controls |

---

## Core Concepts

**Material** — defines the visual appearance of a surface. A complete material provides: a material model, a set of user-controllable named parameters, raster state (blending mode, backface culling, etc.), vertex shader code, and fragment shader code.

**Material model** — also called the *shading model* or *lighting model*. It defines the intrinsic properties of a surface. These properties directly influence how lighting is computed and therefore how the surface appears. The model is selected in the material definition via the `shadingModel` property. The available models are: `lit` (or standard), `subsurface`, `cloth`, `unlit`, and `specularGlossiness` (legacy).

**Material definition** — a text file describing all the information required by a material. This is the file you author directly to create new materials.

**Material package** — at runtime, materials load from *material packages* compiled from material definitions using the `matc` tool. A package contains all the material's information plus shaders generated for the target runtime platforms (Android, macOS, Linux, etc.). Separate per-platform shaders are needed because different platforms use different graphics APIs or variants (e.g. OpenGL vs OpenGL ES). The compiled package file uses the `.filamat` extension.

**Material instance** — a reference to a material together with a set of values for that material's parameters. Instances are created and manipulated from code via Filament's APIs (not authored in the material definition). One material can back many instances, each with its own parameter values.

### Conventions That Apply To All Color Properties

- **Linear RGB** — properties that take RGB colors expect them in linear space, not sRGB. Supply colors already converted to linear space.
- **Pre-multiplied alpha** — `float4` color properties (e.g. `baseColor`, `postLightingColor`) expect pre-multiplied alpha.
- **Normals/direction vectors** — `normal`, `bentNormal`, `clearCoatNormal`, and `anisotropyDirection` are `float3` values in `[0..1]` that encode a direction vector in tangent space (`+Z` points out of the surface).

---

## Choosing a Model

- **`lit`** — the default. Use it for almost everything: dielectrics and metals, hard surfaces, car paint (via clear coat), brushed metal (via anisotropy), refractive/transparent glass, and even cloth (via the sheen layer) when you also need other lit features. It is the most capable and most interoperable model.
- **`subsurface`** — use for translucent objects where light scatters *inside* the volume and re-emerges (wax, skin, marble, foliage held to light). Choose it over `lit` when surface-only shading looks flat and "solid."
- **`cloth`** — use for fabric/cloth where threads scatter light, producing a soft specular lobe with a wide falloff and fuzz/rim lighting (denim, cotton, velvet). Choose it over `lit` when you only need a cloth look and want lower cost than the full lit model's sheen layer. Note: leather, silk, and satin are usually better with the standard or anisotropic lit model.
- **`unlit`** — use when you want *no* lighting computed at all: pre-lit cubemaps, video/camera streams, UI, and visualization/debugging overlays.
- **`specularGlossiness`** — legacy, non-physically-based parameterization. Only use it to load legacy glTF spec-gloss assets; prefer the metallic-roughness `lit` model for new work.

---

## Lit Model (Standard)

Filament's standard, physically-based shading model. Designed for good interoperability with common tools and engines (Unity 5, Unreal Engine 4, Substance Designer, Marmoset Toolbag). It can describe both non-metallic surfaces (*dielectrics*) and metallic surfaces (*conductors*).

This is the richest model — the properties below are its full prose-described input set. (The exhaustive type/range table lives in the separate `materials-properties-reference` file.)

### Base Color

`baseColor` (`float4`, `[0..1]`, pre-multiplied linear RGB) — the perceived color of the object (sometimes called *albedo*). Its meaning depends on `metallic`:

- **Non-metals (dielectrics):** the diffuse color of the surface. Real-world values fall in roughly `[0.04..0.94]` (or `[10..240]` if encoded 0–255).
- **Metals (conductors):** the specular color of the surface. Real-world values fall in roughly `[0.66..1.0]` (or `[170..255]` if encoded 0–255).

### Metallic

`metallic` (`float`, `[0..1]`, should be 0 or 1) — whether the surface is a conductor (1.0) or a dielectric (0.0). Treat it as binary; intermediate values are only useful for texture-driven transitions between surface types. It dramatically changes appearance: dielectrics have chromatic diffuse reflection and achromatic specular reflection; metals have no diffuse reflection and chromatic specular reflection (the reflection takes the color from `baseColor`).

### Roughness

`roughness` (`float`, `[0..1]`) — perceived smoothness (0.0, perfectly smooth/glossy, sharp reflections) to roughness (1.0, blurry reflections). This is the inverse of *glossiness* used by some other engines (`roughness = 1 - glossiness`). Roughness affects both metals and dielectrics, and — when refraction is enabled — also blurs refractions (useful for frosted glass).

### Reflectance

`reflectance` (`float`, `[0..1]`, prefer values > 0.35) — affects **non-metallic surfaces only**. Controls specular intensity and (equivalently) the index of refraction. The value is a *remapped percentage* of reflectance: the default 0.5 corresponds to 4% reflectance. Avoid values below 0.35 (2% reflectance) — no real-world material is that low. Setting `reflectance` deduces `ior` automatically (and vice-versa); see [Index Of Refraction](#index-of-refraction-ior).

### Specular Factor And Specular Color Factor

`specularFactor` (`float`, `[0..1]`, optional, defaults to 1.0) — scales the amount of specular reflection for non-metallic surfaces. It scales the Fresnel reflectance at normal incidence (F0, also computed from `reflectance`) and sets the Fresnel reflectance at grazing angles (F90).

`specularColorFactor` (`float3`, `[0..1]`, linear RGB, defaults to 1.0) — the color of the specular reflection for non-metallic surfaces. It scales F0.

Both are commonly used to implement the `KHR_materials_specular` glTF extension.

### Sheen Color And Sheen Roughness

`sheenColor` (`float3`, `[0..1]`, linear RGB) — controls the color and strength of an optional sheen layer on top of the base layer. The sheen layer sits below the clear coat layer (if present) and is used to represent cloth/fabric appearances within the lit model.

`sheenRoughness` (`float`, `[0..1]`) — like `roughness`, but applies only to the sheen layer.

If you need *only* a cloth-like look (and not the rest of the lit feature set), the dedicated [Cloth model](#cloth-model) is more efficient.

### Clear Coat, Clear Coat Roughness, Clear Coat Normal

For multi-layer materials with a thin translucent layer over a base layer (car paint, soda cans, lacquered wood, acrylic). The clear coat layer is always isotropic and dielectric, and sits on top of the sheen layer if one is present.

`clearCoat` (`float`, `[0..1]`, should be 0 or 1) — strength of the clear coat layer. Treat as binary; intermediate values handle transitions between coated and uncoated regions. **Cost:** the clear coat layer roughly doubles specular computation cost — do not assign any value (not even 0.0) unless you need the second layer.

`clearCoatRoughness` (`float`, `[0..1]`) — like `roughness`, but applies only to the clear coat layer.

`clearCoatNormal` (`float3`, `[0..1]`, tangent-space direction) — a detail normal that perturbs the clear coat layer via bump/normal mapping. Behaves like `normal` but applies to the coat layer. Using it increases material runtime cost.

### Anisotropy And Anisotropy Direction

For materials whose highlights stretch directionally, such as brushed metal. Switching from the default isotropic model to the anisotropic model is slightly more expensive — do not assign a value (even 0.0) to `anisotropy` unless you need it.

`anisotropy` (`float`, `[-1..1]`) — amount of anisotropy. Positive values orient anisotropy in the **tangent** direction; negative values in the **bitangent** direction.

`anisotropyDirection` (`float3`, `[0..1]`, linear RGB encoding a tangent-space direction) — the local surface direction at a point, controlling the shape/orientation of the specular highlights. Usually supplied from a texture; because the direction is in tangent space, the Z component should be 0.

### Ambient Occlusion

`ambientOcclusion` (`float`, `[0..1]`) — a per-pixel shadowing factor: how much ambient light reaches a surface point, from 0.0 (fully shadowed) to 1.0 (fully lit). It affects **only diffuse indirect lighting** (image-based lighting) — not direct lights (directional/point/spot) and not specular lighting.

### Normal And Bent Normal

`normal` (`float3`, `[0..1]`, tangent-space direction) — the surface normal at a point, usually from a normal-map texture, allowing per-pixel variation. Supplied in tangent space (`+Z` out of the surface). It affects the **base layer**, not the clear coat layer. Using a normal map increases material runtime cost.

`bentNormal` (`float3`, `[0..1]`, tangent-space direction) — the average *unoccluded* direction at a point. Improves the accuracy of indirect lighting and the quality of specular ambient occlusion (`specularAmbientOcclusion`). It noticeably improves fidelity in cavities and concave areas (ears, nostrils, eyes).

### Emissive

`emissive` (`float4`; `rgb=[0..n]`, `a=[0..1]`) — additional light emitted by the surface, to simulate emissive surfaces (neon, displays). The RGB carries intensity in **nits** (e.g. a display is ~200–1,000 nits), so an emissive surface can act like a light. The alpha is an **exposure weight**: 0 means the emissive intensity is unaffected by camera exposure (forces bloom); 1 means it is multiplied by camera exposure like any regular light. To work in EV/f-stops, multiply by `filament::Exposure::luminance(ev)`, or convert via `L = 2^(EV - 3)`. Most useful in an HDR pipeline with a bloom pass.

### Post-Lighting Color

`postLightingColor` (`float4`, `[0..1]`, pre-multiplied linear RGB) — a color blended with the result of lighting *after* lighting is computed. It has no physical meaning; it exists for specific effects and debugging. It is blended according to the `postLightingBlending` material option. Tip: it can act as a cheaper `emissive` by setting `postLightingBlending` to `add` and supplying an RGB color with alpha 0.0.

### Index Of Refraction (ior)

`ior` (`float`, `[1..n]`, optional — usually deduced from `reflectance`) — affects **non-metallic surfaces only**. A dimensionless number describing how fast light travels through the material and, more importantly, how much the light path bends when entering it (higher IOR bends further). Intended for refractive (transmissive) materials — enabled when `refractionMode` is `cubemap` or `screenspace` — but also usable on non-refractive objects as an alternative to `reflectance`. `ior` and `reflectance` represent the same physical attribute: set one and the other is computed automatically. Setting both keeps them as-is, which can produce physically impossible materials (sometimes desirable artistically). Common IORs: air 1.0, water 1.33, plastics/glass 1.5–1.58, gemstones 1.58–2.33.

### Transmission

`transmission` (`float`, `[0..1]`) — what ratio of **diffuse** light is transmitted through a refractive dielectric (i.e. how transparent it is). Affects only materials with `refractionMode` set to `cubemap` or `screenspace`. At 0, no light is transmitted and the diffuse component is fully visible; at 1, all light is transmitted and only the specular component remains. Useful for decals/paint on the surface of refractive materials.

### Absorption

`absorption` (`float3`, `[0..n]`) — the absorption coefficients of light transmitted through the material. Light attenuation is exponential with optical depth: transmitted color follows `color · e^(-absorption · distance)`, where `distance` is `thickness` or `microThickness`. If no thickness is provided, attenuation becomes `color · (1 - absorption)`. Because coefficients are unintuitive, prefer specifying a *transmittance color* at a given *distance* and converting: `absorption = -ln(transmittanceColor) / atDistance` (Filament provides `Color::absorptionAtDistance()` / `Color::absorptionAtDistance`); do this offline when possible.

### Thickness And Micro-Thickness

Both define the optical depth of a refracting object and are used (with `absorption`) to compute transmitted color.

`thickness` (`float`, `[0..n]`) — thickness of the **solid volume** in the direction of the normal; used when `refractionType` is `volume`. For good results, provide it per fragment (a texture) or at least per vertex. In solid volumes it also affects how light rays are refracted. Not used when `refractionType` is `thin`.

`microThickness` (`float`, `[0..n]`) — thickness of the **thin layer/shell**; used when `refractionType` is `thin`. Can generally be a constant. Example: a 1 mm-thin hollow sphere of radius 1 m has `thickness` of 1 and `microThickness` of 0.001.

### Dispersion

`dispersion` (`float`, `[0..n]`; realistic values `[0, 1]`, except Rutile at 2.04) — strength of the angular separation of colors transmitting through a relatively clear volume. Usable only when `refractionType` is `volume`. Specified as `20/Abbe number`; 0 means no dispersion. Examples: Diamond/Water 0.36, Crown Glass 0.33, Polycarbonate 0.625.

### Shadow Strength

`shadowStrength` (`float`, `[0..1]`) — a strength factor for all shadows received by this material.

---

## Subsurface Model

Selected with `shadingModel : subsurface`. Use for translucent objects where light scatters inside the volume and re-emerges (e.g. wax, skin, foliage). It builds on the standard lit parameters and adds subsurface-specific inputs.

Additional parameters for this model:

- **`thickness`** — thickness of the translucent volume; modulates how much light passes through.
- **`subsurfaceColor`** — tint applied to light scattered and re-emitted through the volume.
- **`subsurfacePower`** — controls the falloff/strength of the subsurface scattering term.

> **Unverified:** In this v1.75.0 source (`01-material-models.md`), the Subsurface model section contains only the headers `Thickness`, `Subsurface color`, and `Subsurface power` with no descriptive prose, no property type/range table, and no defaults. The property *names* above are taken verbatim from those headers; their per-property meanings, exact types, ranges, and defaults are not stated in this source and should be confirmed against the property-reference file or upstream Filament docs.

---

## Cloth Model

Selected with `shadingModel : cloth`. Use for fabrics made of loosely connected threads that absorb and scatter incident light. Compared to hard surfaces, cloth has a softer specular lobe with a large falloff plus fuzz lighting from forward/backward scattering; some fabrics (e.g. velvet) show two-tone specular colors. The standard model makes fabric look rigid and plastic-like, so the cloth model exists to capture this softness. (Leather, silk, and satin are still better served by the standard or anisotropic lit model.)

The cloth model includes all standard-model parameters **except `metallic` and `reflectance`**, plus two extra parameters:

- **`sheenColor`** (`float3`, `[0..1]`, linear RGB) — a specular tint used to create two-tone specular fabrics. Defaults to `√baseColor`. It directly modifies specular reflectance and gives finer control over cloth appearance. Tip: make `sheenColor` brighter than `baseColor` for a visible fuzz effect; setting it to the luminance of `baseColor` gives a natural result for common cloth.
- **`subsurfaceColor`** (`float3`, `[0..1]`, linear RGB) — a tint for the diffuse color after scattering and absorption through the material. Not physically based; simulates scattering, partial absorption, and re-emission for softer fabrics. **Cost:** the cloth model is more expensive to compute when `subsurfaceColor` is used; high values can also interfere with shadows, so it suits subtle transmission effects.

**Recipes:** for common fabrics (denim, cotton), put chromaticity in `baseColor` and use the default `sheenColor` (or set it to the base color's luminance). For velvet, set `baseColor` to black/dark and put the chromaticity in a bright/saturated `sheenColor`.

---

## Unlit Model

Selected with `shadingModel : unlit`. Turns off all lighting computations. Use for pre-lit elements: cubemaps, external content (video or camera streams), user interfaces, and visualization/debugging. It exposes only three properties:

- **`baseColor`** (`float4`, `[0..1]`, pre-multiplied linear RGB) — the surface diffuse color (shown directly, with no lighting applied).
- **`emissive`** (`float4`; `rgb=[0..n]`, `a=[0..1]`, linear RGB intensity in nits, alpha = exposure weight) — additional diffuse color to simulate emissive surfaces; most useful in an HDR pipeline with a bloom pass.
- **`postLightingColor`** (`float4`, `[0..1]`, pre-multiplied linear RGB) — blended with the sum of `emissive` and `baseColor` according to the `postLightingBlending` material option.

---

## Specular Glossiness (Legacy)

Selected with `shadingModel : specularGlossiness`. An alternative lighting model that exists only for compatibility with legacy standards (e.g. the glTF spec-gloss parameterization). It is **not** physically based — do not use it except when loading legacy assets; prefer the metallic-roughness `lit` model for new work.

This model includes the standard lit parameters **except `metallic`, `reflectance`, and `roughness`**, and replaces them with:

- **`baseColor`** (`float4`, `[0..1]`, pre-multiplied linear RGB) — surface diffuse color.
- **`specularColor`** (`float3`, `[0..1]`, linear RGB) — specular tint. Defaults to black.
- **`glossiness`** (`float`, `[0..1]`) — glossiness, the inverse of roughness. Defaults to 0.0.
