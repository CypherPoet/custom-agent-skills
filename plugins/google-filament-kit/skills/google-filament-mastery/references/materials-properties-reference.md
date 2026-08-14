# Material Properties Reference

> Source: Filament — "Material Properties" notes (material_properties.md) + Materials.md, Filament v1.75.0
> Last synced: 2026-08-14

Exhaustive lookup table for every Filament material parameter: property name, GLSL type, value range, default, applicable shading model(s), and a one-line meaning. Defaults are left blank where the source does not state one — do not infer.

The five material models are: **Lit** (standard), **Subsurface**, **Cloth**, **Unlit**, **Specular glossiness** (legacy). The Lit model is the baseline; Cloth, Unlit, and Specular glossiness are explicitly defined as subsets/variants of it (see each section's scope note).

## Table of Contents

| Section | Covers |
|---|---|
| [Standard (Lit) Model — Base & Common](#standard-lit-model--base--common) | Types, ranges, and notes are reproduced from Materials.md `[standardPropertiesTypes]` |
| [Standard (Lit) Model — Clear Coat](#standard-lit-model--clear-coat) | The clear coat layer is always isotropic and dielectric, with a fixed index of refraction of 1.5 |
| [Standard (Lit) Model — Anisotropy](#standard-lit-model--anisotropy) | Anisotropy amount and tangent-space direction properties |
| [Standard (Lit) Model — Sheen](#standard-lit-model--sheen) | Sheen color and roughness for cloth-like material response |
| [Standard (Lit) Model — Refraction / Transmission](#standard-lit-model--refraction--transmission) | Refractive properties apply when `refractionMode` is set to `cubemap` or `screenspace` |
| [Standard (Lit) Model — Other](#standard-lit-model--other) | Emissive and post-lighting color properties shared across material models |
| [Subsurface Model](#subsurface-model) | Subsurface thickness, color, and power properties and source-data limits |
| [Cloth Model](#cloth-model) | The cloth model encompasses all standard (Lit) model parameters except `metallic` and `reflectance` |
| [Unlit Model](#unlit-model) | Turns off all lighting computations |
| [Specular Glossiness Model (legacy)](#specular-glossiness-model-legacy) | Legacy, non-physically-based model |
| [Reference Value Tables](#reference-value-tables) | Concrete sample values for tuning common materials |

---

## Standard (Lit) Model — Base & Common

Types, ranges, and notes are reproduced from Materials.md `[standardPropertiesTypes]`. "Range" and "Note" columns are verbatim; the "Note" content is folded into Default/Meaning where applicable.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `baseColor` | float4 | [0..1] | | Lit, Subsurface, Cloth, Unlit, Specular glossiness | Diffuse albedo for non-metallic surfaces, and specular color for metallic surfaces. Pre-multiplied linear RGB. |
| `metallic` | float | [0..1] | | Lit, Subsurface | Whether a surface appears to be dielectric (0.0) or conductor (1.0). Should be 0 or 1. (Not in Cloth or Specular glossiness.) |
| `roughness` | float | [0..1] | | Lit, Subsurface, Cloth | Perceived smoothness (0.0) or roughness (1.0) of a surface. Smooth surfaces exhibit sharp reflections. (Not in Specular glossiness.) |
| `reflectance` | float | [0..1] | 0.5 (= 4% reflectance) | Lit, Subsurface | Fresnel reflectance at normal incidence for dielectric surfaces; controls the strength of the reflections. Prefer values > 0.35. (Not in Cloth or Specular glossiness.) |
| `specularFactor` | float | [0..1] | 1.0 | Lit, Subsurface | Scales the amount of specular reflection for non-metallic surfaces. Optional. |
| `specularColorFactor` | float3 | [0..1] | 1.0 | Lit, Subsurface | Color of the specular reflection for non-metallic surfaces. Linear RGB. |
| `ambientOcclusion` | float | [0..1] | | Lit, Subsurface, Cloth | How much ambient light is accessible to a surface point; per-pixel shadowing factor between 0.0 (fully shadowed) and 1.0 (fully lit). |
| `emissive` | float4 | rgb=[0..n], a=[0..1] | | Lit, Subsurface, Cloth, Unlit, Specular glossiness | Additional diffuse albedo to simulate emissive surfaces. Linear RGB intensity in nits; alpha encodes the exposure weight. |
| `normal` | float3 | [0..1] | | Lit, Subsurface, Cloth | A detail normal used to perturb the surface using bump/normal mapping. Linear RGB, encodes a direction vector in tangent space (+Z points outside the surface). |
| `bentNormal` | float3 | [0..1] | | Lit, Subsurface, Cloth | A normal pointing in the average unoccluded direction; improves indirect lighting quality. Linear RGB, encodes a direction vector in tangent space. |
| `postLightingColor` | float4 | [0..1] | | Lit, Subsurface, Cloth, Unlit, Specular glossiness | Additional color blended with the result of lighting computations (see `postLightingBlending`). Pre-multiplied linear RGB. |
| `shadowStrength` | float | | | Lit, Subsurface, Cloth | Strength factor between 0 and 1 for all shadows received by this material. (Range stated in `[standardProperties]` definition; not listed in `[standardPropertiesTypes]`.) |

## Standard (Lit) Model — Clear Coat

The clear coat layer is always isotropic and dielectric, with a fixed index of refraction of 1.5. It is added on top of the sheen layer if present.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `clearCoat` | float | [0..1] | | Lit, Subsurface, Cloth | Strength of the clear coat layer. Should be 0 or 1. |
| `clearCoatRoughness` | float | [0..1] | | Lit, Subsurface, Cloth | Perceived smoothness or roughness of the clear coat layer. |
| `clearCoatNormal` | float3 | [0..1] | | Lit, Subsurface, Cloth | A detail normal used to perturb the clear coat layer using bump/normal mapping. Linear RGB, encodes a direction vector in tangent space. |

## Standard (Lit) Model — Anisotropy

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `anisotropy` | float | [-1..1] | | Lit, Subsurface, Cloth | Amount of anisotropy in either the tangent or bitangent direction. Anisotropy is in the tangent direction when this value is positive (bitangent when negative). |
| `anisotropyDirection` | float3 | [0..1] | | Lit, Subsurface, Cloth | Local surface direction in tangent space. Linear RGB, encodes a direction vector in tangent space (Z component should be 0). |

## Standard (Lit) Model — Sheen

The sheen layer sits below the clear coat layer (if present) and is used to represent cloth and fabric materials within the standard model.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `sheenColor` | float3 | [0..1] | | Lit, Subsurface, Cloth | Strength of the sheen layer (specular tint). Linear RGB. In the Cloth model it creates two-tone specular fabrics and defaults to √baseColor. |
| `sheenRoughness` | float | [0..1] | | Lit, Subsurface, Cloth | Perceived smoothness or roughness of the sheen layer. |

## Standard (Lit) Model — Refraction / Transmission

Refractive properties apply when `refractionMode` is set to `cubemap` or `screenspace`. `ior` and `reflectance` represent the same physical attribute — specifying one auto-computes the other. `thickness` is used when `refractionType` is `solid`/`volume`; `microThickness` is used when `refractionType` is `thin`. `thickness` and `dispersion` are not used when `refractionType` is `thin`.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `ior` | float | [1..n] | | Lit, Subsurface | Index of refraction, for refractive objects or as an alternative to reflectance. Optional, usually deduced from the reflectance. |
| `transmission` | float | [0..1] | | Lit, Subsurface | How much of the diffuse light of a dielectric is transmitted through the object (how transparent it is). |
| `absorption` | float3 | [0..n] | | Lit, Subsurface | Absorption factor (coefficients) for refractive objects. |
| `microThickness` | float | [0..n] | | Lit, Subsurface | Thickness of the thin layer (shell) of refractive objects. Used when `refractionType` is `thin`. |
| `thickness` | float | [0..n] | | Lit, Subsurface | Thickness of the solid volume of refractive objects (in the direction of the normal). Used when `refractionType` is `solid`/`volume`. |
| `dispersion` | float | [0..n] | | Lit, Subsurface | Strength of the dispersion effect for refractive objects, specified as 20/Abbe number. Realistic values are between [0, 1], with the exception of Rutile (2.04). Only used when `refractionType` is `volume`. |

## Standard (Lit) Model — Other

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `emissive` | float4 | rgb=[0..n], a=[0..1] | | Lit, Subsurface, Cloth, Unlit, Specular glossiness | (See Base & Common.) Additional emitted light; RGB intensity in nits, alpha = exposure weight. |
| `postLightingColor` | float4 | [0..1] | | Lit, Subsurface, Cloth, Unlit, Specular glossiness | (See Base & Common.) Modifies surface color after lighting; pre-multiplied linear RGB. Can act as a simpler `emissive` with `postLightingBlending` = `add` and alpha 0.0. |

---

## Subsurface Model

Materials.md lists three Subsurface subsections (`Thickness`, `Subsurface color`, `Subsurface power`) but provides **no type/range/default table** for them in the synced corpus. The Subsurface model otherwise shares the standard (Lit) model properties. The rows below carry the property names from Materials.md headings; types/ranges/defaults are left blank because the source omits them — do not infer.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `thickness` | | | | Subsurface | Thickness parameter for the subsurface model. (No type/range/default in source.) |
| `subsurfaceColor` | | | | Subsurface | Subsurface color for the subsurface model. (No type/range/default in source.) |
| `subsurfacePower` | | | | Subsurface | Subsurface power for the subsurface model. (No type/range/default in source.) |

## Cloth Model

The cloth model encompasses all standard (Lit) model parameters **except `metallic` and `reflectance`**, plus the two extra parameters below. Types/ranges from Materials.md `[clothPropertiesTypes]`.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `sheenColor` | float3 | [0..1] | √baseColor | Cloth | Specular tint to create two-tone specular fabrics. Linear RGB. Defaults to √baseColor. |
| `subsurfaceColor` | float3 | [0..1] | | Cloth | Tint for the diffuse color after scattering and absorption through the material. Linear RGB. |

## Unlit Model

Turns off all lighting computations. Exposes only the three properties below. Types/ranges from Materials.md `[unlitPropertiesTypes]`.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `baseColor` | float4 | [0..1] | | Unlit | Surface diffuse color. Pre-multiplied linear RGB. |
| `emissive` | float4 | rgb=[0..n], a=[0..1] | | Unlit | Additional diffuse color to simulate emissive surfaces. Linear RGB intensity in nits, alpha encodes the exposure weight. |
| `postLightingColor` | float4 | [0..1] | | Unlit | Additional color to blend with base color and emissive (per `postLightingBlending`). Pre-multiplied linear RGB. |

## Specular Glossiness Model (legacy)

Legacy, non-physically-based model. Encompasses the standard (Lit) parameters **except `metallic`, `reflectance`, and `roughness`**, and adds `specularColor` and `glossiness`. Types/ranges from Materials.md `[glossinessPropertiesTypes]`.

| Property | Type | Range | Default | Models | Meaning |
|----------|------|-------|---------|--------|---------|
| `baseColor` | float4 | [0..1] | | Specular glossiness | Surface diffuse color. Pre-multiplied linear RGB. |
| `specularColor` | float3 | [0..1] | black | Specular glossiness | Specular tint. Linear RGB. Defaults to black. |
| `glossiness` | float | [0..1] | 0.0 | Specular glossiness | Glossiness (inverse of roughness). Defaults to 0.0. |

---

## Reference Value Tables

Concrete sample values for tuning common materials. Source: material_properties.md (sRGB / hex samples) and Materials.md (sRGB linear, hex, reflectance/IOR/dispersion tables).

### baseColor — Common Non-Metals (dielectrics)

Real-world dielectric base colors fall in [10..240] when encoded 0–255, or [0.04..0.94] between 0 and 1. (sRGB linear values and hex from Materials.md `[baseColorsDielectrics]`; the 0–255 sRGB triplets are from material_properties.md.)

| Material | sRGB (linear) | sRGB (0–255) | Hex |
|----------|---------------|--------------|-----|
| Coal | 0.19, 0.19, 0.19 | 50, 50, 50 | #323232 |
| Rubber | 0.21, 0.21, 0.21 | 53, 53, 53 | #353535 |
| Mud | 0.33, 0.24, 0.19 | 85, 61, 49 | #553d31 |
| Wood | 0.53, 0.36, 0.24 | 135, 92, 60 | #875c3c |
| Vegetation | 0.48, 0.51, 0.31 | 123, 130, 78 | #7b824e |
| Brick | 0.58, 0.49, 0.46 | 148, 125, 117 | #947d75 |
| Sand | 0.69, 0.66, 0.52 | 177, 168, 132 | #b1a884 |
| Concrete | 0.75, 0.75, 0.73 | 192, 191, 187 | #c0bfbb |

### baseColor — Common Metals (conductors)

Real-world conductor base colors fall in [170..255] when encoded 0–255, or [0.66..1.0] between 0 and 1. (sRGB linear values and hex from Materials.md `[baseColorsConductors]`; the 0–255 sRGB triplets and display hex are from material_properties.md.)

| Material | sRGB (linear) | sRGB (0–255) | Hex (Materials.md) | Display hex (notes) |
|----------|---------------|--------------|--------------------|---------------------|
| Silver | 0.97, 0.96, 0.91 | 250, 249, 245 | #f7f4e8 | #faf9f5 |
| Aluminum | 0.91, 0.92, 0.92 | 244, 245, 245 | #e8eaea | #faf5f5 |
| Platinum | 0.83, 0.81, 0.78 | 214, 209, 200 | #d3cec6 | #d6d1c8 |
| Iron | 0.77, 0.78, 0.78 | 192, 189, 186 | #c4c6c6 | #c0bdba |
| Titanium | 0.76, 0.73, 0.69 | 206, 200, 194 | #c1baaf | #cec8c2 |
| Copper | 0.97, 0.74, 0.62 | 251, 216, 184 | #f7bc9e | #fbd8b8 |
| Gold | 1.00, 0.85, 0.57 | 255, 220, 157 | #ffd891 | #fedc9d |
| Brass | 0.98, 0.90, 0.59 | 244, 228, 173 | #f9e596 | #f4e4ad |

### Reflectance / IOR of Common Materials

No real-world material has a reflectance value under 2%. Default `reflectance` is 0.5 (4% reflectance, IOR 1.5). Source: Materials.md `[commonMatReflectance]`.

| Material | Reflectance | IOR | Linear value |
|----------|-------------|-----|--------------|
| Water | 2% | 1.33 | 0.35 |
| Fabric | 4% to 5.6% | 1.5 to 1.62 | 0.5 to 0.59 |
| Common liquids | 2% to 4% | 1.33 to 1.5 | 0.35 to 0.5 |
| Common gemstones | 5% to 16% | 1.58 to 2.33 | 0.56 to 1.0 |
| Plastics, glass | 4% to 5% | 1.5 to 1.58 | 0.5 to 0.56 |
| Other dielectric materials | 2% to 5% | 1.33 to 1.58 | 0.35 to 0.56 |
| Eyes | 2.5% | 1.38 | 0.39 |
| Skin | 2.8% | 1.4 | 0.42 |
| Hair | 4.6% | 1.55 | 0.54 |
| Teeth | 5.8% | 1.63 | 0.6 |
| Default value | 4% | 1.5 | 0.5 |

Reflectance samples (from material_properties.md `[SAMPLES]`):

| Material | sRGB (0–255) | Reflectance |
|----------|--------------|-------------|
| Water | 90, 90, 90 | 2% |
| Glass | 119, 119, 119 | 3.5% |
| Liquids | | 2% to 4% |
| Defaults | 127, 127, 127 | 4% |
| Others | | 2% to 5% |
| Ruby | 180, 180, 180 | 8% |
| Diamond | 255, 255, 255 | 16% |
| Gemstones | | 5% to 16% |

### Index of Refraction of Common Materials

Source: Materials.md `[commonMatIOR]`.

| Material | IOR |
|----------|-----|
| Air | 1.0 |
| Water | 1.33 |
| Common liquids | 1.33 to 1.5 |
| Common gemstones | 1.58 to 2.33 |
| Plastics, glass | 1.5 to 1.58 |
| Other dielectric materials | 1.33 to 1.58 |

### Dispersion of Common Materials

Dispersion is specified as 20/Abbe number. Source: Materials.md `[commonMatDispersion]`.

| Material | Abbe Number (V) | Dispersion (20/V) |
|----------|-----------------|-------------------|
| Rutile | 9.8 | 2.04 |
| Polycarbonate | 32 | 0.625 |
| Diamond | 55 | 0.36 |
| Water | 55 | 0.36 |
| Crown Glass | 59 | 0.33 |
