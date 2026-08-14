# Lighting & Image-Based Lighting

> Source: Filament Core Concepts — "Lighting" (Filament.md) + cmgen/iblprefilter docs, Filament v1.75.0
> Last synced: 2026-08-14

## Table of Contents

| Section | Covers |
|---|---|
| [Physical light units (the trap)](#physical-light-units-the-trap) | Filament uses physical light units so lighting is correct by default and lighting rigs are reusable |
| [Direct lighting](#direct-lighting) | All light evaluation computes the outgoing luminance (radiance) `L_out = f(v,l) · E` |
| [Image-based lighting (IBL)](#image-based-lighting-ibl) | What an IBL is, Diffuse: spherical harmonics (irradiance), Specular: prefiltered roughness mip chain, and related topics |
| [Occlusion](#occlusion) | Contact, ambient, and screen-space darkening at different spatial scales |
| [Normal mapping](#normal-mapping) | Two use cases: replacing high-poly with low-poly meshes (base map) and adding surface detail (detail map) |
| [Runtime API reference (verbatim signatures)](#runtime-api-reference-verbatim-signatures) | LightManager::Builder (from LightManager.h), IndirectLight::Builder (from IndirectLight.h), and Skybox::Builder (from Skybox.h) |

---

## Physical light units (the trap)

Filament uses **physical light units** so lighting is correct by default and lighting rigs are reusable. The single most common mistake is feeding the wrong unit to a light's intensity. Each light type expects a specific photometric unit:

| Light type                | Unit                                   |
|---------------------------|----------------------------------------|
| Directional light         | Illuminance — **lux (lx)** or lm/m²    |
| Point light               | Luminous power — **lumen (lm)**        |
| Spot light                | Luminous power — **lumen (lm)**        |
| Photometric light         | Luminous intensity — **candela (cd)**  |
| Masked photometric light  | Luminous power — **lumen (lm)**        |
| Area light                | Luminous power — **lumen (lm)**        |
| Image based light         | Luminance — **cd/m²**                  |

Photometric terms and their symbols/units (verbatim from the doc):

| Photometric term    | Notation | Unit                          |
|---------------------|----------|-------------------------------|
| Luminous power      | Φ        | Lumen (lm)                    |
| Luminous intensity  | I        | Candela (cd) or lm/sr         |
| Illuminance         | E        | Lux (lx) or lm/m²             |
| Luminance           | L        | Nit (nt) or cd/m²             |
| Radiant power       | Φₑ       | Watt (W)                      |
| Luminous efficacy   | η        | Lumens per watt (lm/W)        |
| Luminous efficiency | V        | Percentage (%)                |

Real-world magnitudes the doc cites (use these as sanity checks):

- Household light bulb ≈ **800 lm**.
- Daylight sky + sun illumination ≈ **120,000 lx**.
- A **full moon has an illuminance of 1 lx**.
- The header `LightManager::Builder::intensity()` states: *"the sun's illuminance is about 100,000 lux."*

Sun & sky illuminance reference (lx), measured on a clear day in March, in California:

| Light                      | 10am    | 12pm    | 5:30pm  |
|----------------------------|---------|---------|---------|
| Sky⊥ + Sun⊥                | 120,000 | 130,000 | 90,000  |
| Sky⊥                       | 20,000  | 25,000  | 9,000   |
| Sun⊥                       | 100,000 | 105,000 | 81,000  |

A midday-sun directional light in the doc's example uses an **illuminance set to 110,000 lx**.

### Watts → lumens (artist convenience)

Watts measure energy consumed, not brightness. Filament still lets you specify intensity in watts plus an efficiency: `Φ = Φₑ · η`, and since the maximum possible luminous efficacy is **683 lm/W**, `Φ = Φₑ · 683 · V`. The header's `intensity(float watts, float efficiency)` is exactly equivalent to `intensity(efficiency * 683 * watts)`.

Efficacy / efficiency reference (from the lighting doc):

| Light type   | Efficacy η | Efficiency V |
|--------------|------------|--------------|
| Incandescent | 14-35      | 2-5%         |
| LED          | 28-100     | 4-15%        |
| Fluorescent  | 60-100     | 9-15%        |

`LightManager` ships these efficiency constants (verbatim):

```cpp
static constexpr float EFFICIENCY_INCANDESCENT = 0.0220f;  // 2.2%
static constexpr float EFFICIENCY_HALOGEN      = 0.0707f;  // 7.0%
static constexpr float EFFICIENCY_FLUORESCENT  = 0.0878f;  // 8.7%
static constexpr float EFFICIENCY_LED          = 0.1171f;  // 11.7%
```

> Note: internally all luminous powers are converted to luminous intensities (cd) before being sent to the shader. The conversion is light-type dependent (see Point / Spot below). The luminance/radiance output of all direct lighting equations is in cd/m².

---

## Direct lighting

All light evaluation computes the outgoing luminance (radiance) `L_out = f(v,l) · E`, where `f(v,l)` is the BSDF and `E` is the illuminance reaching the surface. Each light type differs only in how `E` is computed.

`LightManager::Type` enum (verbatim):

```cpp
enum class Type : uint8_t {
    SUN,            //!< Directional light that also draws a sun's disk in the sky.
    DIRECTIONAL,    //!< Directional light, emits light in a given direction.
    POINT,          //!< Point light, emits light from a position, in all directions.
    FOCUSED_SPOT,   //!< Physically correct spot light.
    SPOT,           //!< Spot light with coupling of outer cone and illumination disabled.
};
```

A light component is created with `LightManager::Builder(Type)` and committed with `.build(engine, entity)`; it is destroyed with `LightManager::destroy(entity)`. **At least one light must be added to a scene to see anything** (unless `Material.Shading.UNLIT` is used). Currently a max of **2048 lights** per Engine.

### Directional lights (sun)

Simulates the sun/moon: all rays parallel, no position, intensity in **lux**. Use `Type::DIRECTIONAL` for a plain directional light, or `Type::SUN` to additionally draw a sun disc in the sky and its reflection on glossy objects. **Only a single directional light is supported**; if several are added, the dominant one is used. Directional and spot lights can cast shadows.

`E⊥` is the illuminance for a surface perpendicular to the light. Runtime evaluation is cheap:

```glsl
vec3 l = normalize(-lightDirection);
float NoL = clamp(dot(n, l), 0.0, 1.0);

// lightIntensity is the illuminance
// at perpendicular incidence in lux
float illuminance = lightIntensity * NoL;
vec3 luminance = BSDF(v, l) * illuminance;
```

**Sun disc params** (only meaningful for `Type::SUN`):

- `sunAngularRadius(float angularRadiusDeg)` — sun radius in degrees, clamped to **0.25°–20.0°**. Default **0.545°**. (The real sun seen from Earth is 0.526°–0.545°.)
- `sunHaloSize(float haloSize)` — halo radius as a multiplier of the sun angular radius. Must be ≥ 1.0. Default **10.0**.
- `sunHaloFalloff(float haloFalloff)` — dimensionless halo falloff exponent. Must be ≥ 1.0. Default **80.0**.

### Point lights

Defined only by a position. Intensity is **luminous power (lm)**, emitted in all directions. Intensity diminishes with the inverse square of distance. `falloff()` controls the distance beyond which the light has no influence. A scene can have many point lights.

Luminous intensity is derived from luminous power: `I = Φ / (4π)`, so:

`L_out = f(v,l) · Φ / (4π·d²) · <NoL>`

### Spot lights

Like a point light but constrained to a cone defined by `spotLightCone(inner, outer)` plus the light's direction. Position + direction + inner & outer cones. The light's influence is limited to inside the **outer** cone; the **inner** cone defines the falloff attenuation.

Two spot types exist because a physically correct spot couples the outer-cone aperture to illumination level (shrinking the cone makes it brighter):

- **`Type::FOCUSED_SPOT`** — physically correct: `I = Φ / (2π(1 − cos(θ_outer/2)))`.
- **`Type::SPOT`** — coupling disabled (the "light absorber" formulation): `I = Φ / π`, so changing the cone aperture keeps illumination roughly constant.

> For `Type::FOCUSED_SPOT`, `getIntensity()` returns a value that depends on the `outer` cone angle.

Spot angle attenuation `λ(l) = (l·spotDir − cos θ_outer) / (cos θ_inner − cos θ_outer)`. GLSL:

```glsl
float getSpotAngleAttenuation(vec3 l, vec3 lightDir,
        float innerAngle, float outerAngle) {
    // the scale and offset computations can be done CPU-side
    float cosOuter = cos(outerAngle);
    float spotScale = 1.0 / max(cos(innerAngle) - cosOuter, 1e-4)
    float spotOffset = -cosOuter * spotScale

    float cd = dot(normalize(-lightDir), l);
    float attenuation = clamp(cd * spotScale + spotOffset, 0.0, 1.0);
    return attenuation * attenuation;
}
```

### Falloff / influence radius

Two practical fixes to the raw inverse-square law:

1. **Divide-by-zero / singularity** when a surface touches a light: treat punctual lights as small spheres of radius 1 cm — `E = I / max(d², 0.01²)`.
2. **Infinite influence** (`I/d²` is asymptotic): introduce a per-light **influence/falloff radius `r`** and window the function so light smoothly reaches zero at `r`:
   `E = I / max(d², 0.01²) · <1 − d⁴/r⁴>²`.

`Builder::falloff(float radius)` defines this **sphere of influence** for point & spot lights (default **1 meter**, ignored for directional/sun). Larger falloffs hurt performance — overlapping spheres of influence are the expensive case. Performance tips from the header: prefer spot to point lights, use the smallest outer cone and smallest falloff possible, and avoid overlap.

```glsl
float getSquareFalloffAttenuation(vec3 posToLight, float lightInvRadius) {
    float distanceSquare = dot(posToLight, posToLight);
    float factor = distanceSquare * lightInvRadius * lightInvRadius;
    float smoothFactor = max(1.0 - factor * factor, 0.0);
    return (smoothFactor * smoothFactor) / max(distanceSquare, 1e-4);
}
```

> The light intensity used in the GLSL punctual-light code is the luminous intensity `I` in cd, converted from luminous power CPU-side.

### Photometric (IES) lights

Photometric lights use an **IES** (Illuminating Engineering Society) profile to describe the light's intensity distribution (EULUMDAT exists too; Filament focuses on IES). An IES profile stores **luminous intensities in candela** at various angles around the source (vertical 0–180°, horizontal 0–360°). IES profiles can be applied to any punctual light, point or spot.

The profile is pre-processed into a **1D texture** (each texel = a vertical angle, averaged over horizontal angles — most lights are horizontally symmetric), with values **normalized by the inverse maximum intensity**. Stored normalized, the profile can act as a **mask**:

- **As a mask** (`Masked photometric light`, unit lm): the artist sets luminous power; the engine divides the artist's intensity by the profile's integrated intensity. The integrated intensity comes from a Monte-Carlo integration over the unit sphere around the luminaire (the IES file's stated intensity is for a bare bulb, not the fixture). *Example: the XArrow profile declares 1,750 lm but Monte-Carlo integration yields only 350 lm.*
- **Not as a mask** (`Photometric light`, unit cd): intensity comes from the profile itself — sampled values × max intensity × a convenience multiplier (default 1.0).

`L_out = f(v,l) · I/d² · <NoL> · Ψ(l)`, where `Ψ(l)` is the profile attenuation:

```glsl
float getPhotometricAttenuation(vec3 posToLight, vec3 lightDir) {
    float cosTheta = dot(-posToLight, lightDir);
    float angle = acos(cosTheta) * (1.0 / PI);
    return texture2DLodEXT(lightProfileMap, vec2(angle, 0.0), 0.0).r;
}
```

> Photometric point lights need a direction vector (spot lights already have one).

### Area lights

The lighting doc marks area lights as **[TODO]** — there is no detailed treatment in the v1.75.0 chapter. What the doc does state: area lights use **luminous power (lm)**; they take a **Length** (linear/tubular lights) and a **Radius** (spherical/tubular lights) parameter; and treating punctual lights as 1 cm spheres is the area-light approximation used to avoid the inverse-square singularity. There is no public area-light `Type` enum value in `LightManager.h` (the enum is SUN, DIRECTIONAL, POINT, FOCUSED_SPOT, SPOT).

### Light color & color temperature

Color (hue) is separated from intensity. Color is a **linear sRGB** RGB value (default white {1,1,1}); tools may accept sRGB or a **color temperature in Kelvin** (meaningful range **1,000 K–12,500 K**). Filament converts a temperature to RGB via the Planckian locus (Krystek's CIE 1960 UCS approximation, then xyY → XYZ → linear sRGB, normalized, with the sRGB OECF for display). Useful reference temperatures: candle flame ≈ 1,850–1,930 K; household tungsten bulb ≈ 2,500–2,900 K; sun at noon ≈ 5,000–5,400 K; daylight (sun + sky) ≈ 5,500–6,500 K; overcast sky ≈ 6,000–7,500 K.

### Pre-exposed lights

Physical light units produce a huge value range that overflows half-floats (mediump). The fix is to **pre-expose the lights** (multiply intensity by camera exposure) so the whole shading pipeline can run in half precision:

```glsl
fragColor = luminance * camera.exposure;          // pre-expose the lighting-pass output
```

In practice Filament pre-exposes: **punctual lights (point/spot) on the GPU; the directional light on the CPU; IBLs on the CPU; material emissive on the GPU.**

---

## Image-based lighting (IBL)

### What an IBL is

In real life light arrives from every direction — directly from sources and indirectly after bouncing off the environment. The whole environment can be treated as a light source, encoded in an image (typically a cubemap). This is **Image-Based Lighting (IBL)** / indirect lighting. Filament's `IndirectLight` simulates this as a form of global illumination.

The environment's contribution to a surface point is the **irradiance (E)**; the light bouncing off is the **radiance (L_out)**. Incident lighting is applied consistently to **both the diffuse and specular** parts of the BRDF. IBL intensity unit is **luminance (cd/m²)** — the same as direct-lighting output.

`IndirectLight` has two components: **(1) irradiance** and **(2) reflections (specular)**. Currently it is intended for **distant probes** (environment at infinity, e.g. sky/distant mountains) and **only a single IndirectLight can be used in a Scene**.

IBL types the doc names: distant light probes, local light probes, planar reflections, screen-space reflections. Filament's docs focus on **distant probes**.

### Diffuse: spherical harmonics (irradiance)

The diffuse (irradiance) response integrates the environment over the hemisphere weighted by the Lambertian BRDF. Instead of storing an irradiance cubemap, Filament approximates the irradiance with **spherical harmonics (SH)** — extremely cheap to evaluate at runtime and frees a texture unit. Only **2 or 3 bands (4 or 9 coefficients)** are needed for `cos θ`. Coefficients are pre-convolved with `cos θ` and pre-scaled by the basis factors `K_l^m`, so reconstruction is trivial; `sphericalHarmonics[0]` is directly the average irradiance.

```glsl
vec3 irradianceSH(vec3 n) {
    // uniform vec3 sphericalHarmonics[9]
    // We can use only the first 2 bands for better performance
    return
          sphericalHarmonics[0]
        + sphericalHarmonics[1] * (n.y)
        + sphericalHarmonics[2] * (n.z)
        + sphericalHarmonics[3] * (n.x)
        + sphericalHarmonics[4] * (n.y * n.x)
        + sphericalHarmonics[5] * (n.y * n.z)
        + sphericalHarmonics[6] * (3.0 * n.z * n.z - 1.0)
        + sphericalHarmonics[7] * (n.z * n.x)
        + sphericalHarmonics[8] * (n.x * n.x - n.y * n.y);
}
```

### Specular: prefiltered roughness mip chain

The specular response is a convolution of the environment by the BRDF — higher roughness → blurrier reflections. Filament uses the **split-sum approximation**: a prefiltered environment term `LD` plus a `DFG` lookup. `LD` is stored in a **mip-mapped cubemap where increasing LODs hold the environment pre-filtered with increasing roughness** (the convolution is a low-pass filter, hence mips). Roughness is remapped so each mip is used well: `α = perceptualRoughness²`, `lod_α = perceptualRoughness`.

The `DFG` term (a 2D LUT indexed by `(NoV, α)`, or an analytic approximation) carries the Fresnel/visibility integral. Combined IBL evaluation:

```glsl
vec3 evaluateIBL(vec3 n, vec3 v, vec3 diffuseColor, vec3 f0, vec3 f90, float perceptualRoughness) {
    float NoV = max(dot(n, v), 0.0);
    vec3 r = reflect(-v, n);

    // Specular indirect (sample the prefiltered roughness mip chain)
    vec3 indirectSpecular = evaluateSpecularIBL(r, perceptualRoughness);
    vec2 env = prefilteredDFG_LUT(perceptualRoughness, NoV);
    vec3 specularColor = f0 * env.x + f90 * env.y;

    // Diffuse indirect (from SH)
    vec3 indirectDiffuse = max(irradianceSH(n), 0.0) * Fd_Lambert();

    return diffuseColor * indirectDiffuse + indirectSpecular * specularColor;
}
```

Key approximations to be aware of: the prefilter assumes `v = n` (loses view-dependent "stretchy reflections"); roughness is quantized across LODs; the mips can't double as minification mips (possible aliasing/moiré at low roughness).

### Why you cannot use a raw HDR directly

> **You cannot feed a raw equirectangular / HDR environment to `IndirectLight` directly.** The radiance of an IBL is an integral over the hemisphere — far too expensive per-pixel at runtime. The environment must first be **pre-processed** into the two runtime-friendly forms above: SH coefficients for diffuse irradiance, and a prefiltered roughness mip chain (cubemap) for specular reflections. That preprocessing is done **offline by the `cmgen` CLI** or **at runtime on the GPU by the `iblprefilter` library**. Either way, `IndirectLight::Builder::reflections()` expects an already-prefiltered, mip-mapped cubemap — not a raw HDR. (From `IndirectLight.h`: *"Environments are usually captured as high-resolution HDR equirectangular images and processed by the cmgen tool to generate the data needed by IndirectLight."*)

HDR caveat: cameras don't record absolute luminance, so artists must supply a multiplier to recover the original luminance (color calibration with a gray card / ColorChecker, recorded aperture/shutter/ISO, and spot-meter luminance samples).

### Processing with cmgen (CLI)

`cmgen` generates SH and mipmap levels from an env map. Cubemap and equirectangular inputs are auto-detected by aspect ratio. It produces a mipmapped IBL, a blurry skybox, or both.

- **Input formats:** PNG (8/16-bit), Radiance `.hdr`, Photoshop `.psd` (16/32-bit), OpenEXR `.exr`.
- **Key options:** `--type=[cubemap|equirect|octahedron|ktx]` / `-t`; `--format=[exr|hdr|psd|rgbm|rgb32f|png|dds|ktx]` / `-f` (ktx implies `-type=ktx`; KTX is always KTX1, encoded as 3-channel RGB_10_11_11_REV); `--size=power-of-two` / `-s` (base cubemap size, default 256); `--deploy=dir` / `-x dir` (generate everything needed for deployment); `--ibl-samples=N` (default 1024); `--ibl-ld=dir` (roughness pre-filter); `--sh-shader` (generate irradiance SH for shader code); `--extract-blur=roughness` (blur the cubemap before extracting faces).

Generate an IBL (KTX + SH) into a directory — verbatim from the Filament docs:

```shell
# Filament BUILDING.md: produces the prefiltered IBL + skybox + SH text file
cmgen -f ktx -x ./ibls/ my_ibl.exr
```

`cmgen` creates a sub-directory named after the source map (above → `./ibls/my_ibl/`) containing the **pre-filtered environment map** (one file per cubemap face per mip level), the **skybox** environment texture, and a **text file with the SH coefficients** for indirect diffuse lighting. For a blurred background skybox add `--extract-blur=0.1` (the value is roughness in [0,1]). Example from the web tutorial:

```shell
# Filament web tutorial (suzanne): IBL + blurred skybox as KTX
cmgen -x . --format=ktx --size=256 --extract-blur=0.1 venetian_crossroads_2k.hdr
```

Sample apps expect a directory containing either the `.rgb32f` files (PNGs holding `R11F_G11F_B10F` data) or two `.ktx` files (one for the IBL, one for the skybox).

### Processing with iblprefilter (runtime GPU)

`iblprefilter` (`libfilament-iblprefilter.a`, headers in `<filament-iblprefilter/*.h>`) generates the `reflections` texture for `IndirectLight` entirely **on the GPU** — significantly faster than `cmgen`, though `cmgen` has more features. Expect **~100ms–300ms** for a 5-level 256×256 cubemap at 1024 samples. It is a pure client of Filament's public API.

```c++
#include <filament/Engine.h>
#include <filament-iblprefilter/IBLPrefilterContext.h>

using namespace filament;
Engine* engine = Engine::create();

// keep the context around if several cubemaps will be processed
IBLPrefilterContext context(engine);

// the specular (reflections) filter generates the kernel; reuse it across cubemaps
IBLPrefilterContext::SpecularFilter filter(context);

// run the heavy GPU computation
Texture* texture = filter(environment_cubemap);

IndirectLight* indirectLight = IndirectLight::Builder()
    .reflections(texture)
    .build(engine);
```

### Skybox

A `Skybox` fills all untouched pixels of a `Scene`. Only texture-based skyboxes are currently supported; the cubemap appears mirrored (OpenGL convention). The reflection maps `cmgen` generates by default are ideal as skyboxes. A skybox can also be set to a constant color. `showSun(true)` renders the sun, but only if a `Type::SUN` light is in the scene. Skybox `intensity` (default **30000**, in lux / lumen/m²) is only used when **no** `IndirectLight` is set; otherwise the IndirectLight's intensity wins.

---

## Occlusion

Occlusion darkens to recreate shadowing at three scales:

- **Small scale (micro)** — creases, cracks, cavities. Filament **ignores** micro-occlusion; it can simply be baked into the base color map (note: specular won't be affected).
- **Medium scale (macro)** — occlusion from an object's own geometry or normal-map-baked detail; pre-baked into **ambient occlusion maps**, exposed as a material parameter.
- **Large scale** — contact between objects / own geometry; computed at runtime with **SSAO** (screen-space ambient occlusion), **HBAO** (horizon-based), etc.

To avoid over-darkening when combining medium + large occlusion, Filament uses `min(AO_medium, AO_large)`.

**Diffuse occlusion:** the AO term is `AO = 1 − (1/π)∫ V(l)<NoL> dl`. Baked AO is a grayscale texture, and is applied **only to indirect lighting**:

```glsl
vec3 indirectDiffuse = max(irradianceSH(n), 0.0) * Fd_Lambert();
indirectDiffuse *= texture2D(aoMap, outUV).r;   // AO applies to indirect only
```

**Specular ambient occlusion:** lack of accessibility info causes specular light leaks. Two derived terms:

- **Specular micro-occlusion** from `f0` (no real material reflects below 2%): `f90 = clamp(50.0 * f0.g, 0.0, 1.0)` smoothly extinguishes the Fresnel term.
- **Lagarde's specular AO** (empirical; returns diffuse AO unchanged for rough surfaces, reduces it at normal incidence / increases at grazing for smooth surfaces):

```glsl
float computeSpecularAO(float NoV, float ao, float roughness) {
    return clamp(pow(NoV + ao, exp2(-16.0 * roughness - 1.0)) - 1.0 + ao, 0.0, 1.0);
}
```

- **Horizon specular occlusion** — kills reflections pointing back into the surface (another leak source): `horizon = min(1.0 + dot(r, n), 1.0); indirectSpecular *= horizon * horizon;`.

All occlusion factors are applied **only to indirect lighting**.

---

## Normal mapping

Two use cases: replacing high-poly with low-poly meshes (base map) and adding surface detail (detail map). Naive blending of two normal maps (linear/overlay) is wrong because XYZ are stored in tangent space. Filament uses:

- **Reoriented Normal Mapping (RNM)** — mathematically correct; rotates the detail map's basis onto the base normal via the shortest-arc quaternion. Used mostly **offline** (slightly more expensive); Filament ships an offline tool to combine two normal maps.
- **UDN blending** — cheaper, runtime-friendly variant of partial-derivative blending; visually close to RNM but less correct (loses detail over flat areas).

RNM assumes uncompressed normals in [0..1]. The normalization step can be skipped at runtime.

---

## Runtime API reference (verbatim signatures)

### LightManager::Builder (from `LightManager.h`)

```cpp
explicit Builder(Type type) noexcept;

Builder& lightChannel(unsigned int channel, bool enable = true) noexcept;
Builder& castShadows(bool enable) noexcept;
Builder& shadowOptions(const ShadowOptions& options) noexcept;
Builder& castLight(bool enable) noexcept;
Builder& position(const math::float3& position) noexcept;     // ignored for DIRECTIONAL/SUN
Builder& direction(const math::float3& direction) noexcept;   // default {0,-1,0}; ignored for POINT
Builder& color(const LinearColor& color) noexcept;            // linear sRGB, default white {1,1,1}
Builder& intensity(float intensity) noexcept;                 // directional: lux; point/spot: lumen
Builder& intensityCandela(float intensity) noexcept;          // luminous intensity in candela
Builder& intensity(float watts, float efficiency) noexcept;   // == intensity(efficiency * 683 * watts)
Builder& falloff(float radius) noexcept;                      // world units, default 1m; ignored for DIRECTIONAL/SUN
Builder& spotLightCone(float inner, float outer) noexcept;    // radians; clamped to >= 0.00873 (0.5 deg), outer <= pi/2
Builder& sunAngularRadius(float angularRadiusDeg) noexcept;   // 0.25 deg .. 20.0 deg, default 0.545
Builder& sunHaloSize(float haloSize) noexcept;                // multiplier >= 1.0, default 10.0
Builder& sunHaloFalloff(float haloFalloff) noexcept;          // exponent >= 1.0, default 80.0
Result build(Engine& engine, utils::Entity entity);
```

Helper queries: `getType`, `isDirectional`, `isPointLight`, `isSpotLight`. Dynamic setters mirror the builder: `setPosition`, `setDirection`, `setColor`, `setIntensity` (also `setIntensity(i, watts, efficiency)` = `setIntensity(i, watts * 683.0f * efficiency)`), `setIntensityCandela`, `setFalloff`, `setSpotLightCone`, `setSunAngularRadius`, `setSunHaloSize`, `setSunHaloFalloff`, plus getters and `setShadowCaster` / `isShadowCaster` / `getShadowOptions` / `setShadowOptions`. `getIntensity` returns luminous intensity in candela (for `FOCUSED_SPOT`, depends on the outer cone).

### IndirectLight::Builder (from `IndirectLight.h`)

```cpp
Builder() noexcept;

Builder& reflections(Texture const* cubemap) noexcept;             // mip-mapped cubemap from cmgen / iblprefilter
Builder& irradiance(uint8_t bands, math::float3 const* sh) noexcept; // bands 1/2/3 -> 1/4/9 SH coeffs (pre-convolved + pre-scaled)
Builder& radiance(uint8_t bands, math::float3 const* sh) noexcept;   // bands 1/2/3; raw radiance SH L_l^m
Builder& irradiance(Texture const* cubemap) noexcept;             // irradiance as a cubemap instead of SH
Builder& intensity(float envIntensity) noexcept;                 // scale to lux / lumen/m^2, default 30000
Builder& rotation(math::mat3f const& rotation) noexcept;          // rigid-body 3x3 rotation
IndirectLight* build(Engine& engine);
```

Runtime: `setIntensity` / `getIntensity` (lux, default 30000), `setRotation` / `getRotation`, `getReflectionsTexture`, `getIrradianceTexture`. SH helpers: `getDirectionEstimate(const float3 sh[9])` and `getColorEstimate(const float3 sh[9], float3 direction)` (and instance overloads) estimate the dominant light direction/color from 3-band SH — useful to drive a matching directional light (`color()` returns linear color; the 4th component of the color estimate is the dominant light's intensity, which you multiply by the IBL intensity).

> Irradiance is normally derived automatically from `reflections()` and need not be supplied. Provide it explicitly only to override. `sh[0]` is the environment's average irradiance.

### Skybox::Builder (from `Skybox.h`)

```cpp
Builder() noexcept;

Builder& environment(Texture* cubemap) noexcept;   // must be a cube map (cmgen reflection maps are ideal)
Builder& showSun(bool show) noexcept;              // default false; needs a Type::SUN light in the scene
Builder& intensity(float envIntensity) noexcept;   // lux/lumen-m^2, default 30000; ignored if an IndirectLight is set
Builder& color(math::float4 color) noexcept;       // constant color, default opaque black; ignored if environment set
Builder& priority(uint8_t priority) noexcept;      // [0..7], default 7 (lowest, rendered last)
Skybox* build(Engine& engine);
```

Runtime: `setColor`, `setLayerMask(select, values)` (default 0x1), `getLayerMask`, `getIntensity` (lux), `getTexture`.
