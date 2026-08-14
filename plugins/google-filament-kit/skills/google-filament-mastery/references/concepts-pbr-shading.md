# PBR Shading Model

> Source: Filament Core Concepts — "Material system" (Filament.md), Filament v1.75.0
> Last synced: 2026-08-14

## Table of Contents

| Section | Covers |
|---|---|
| [Notation](#notation) | Perceptual roughness notation and the BRDF value derived from it |
| [The standard surface model](#the-standard-surface-model) | A material is described by a BSDF (Bidirectional Scattering Distribution Function) = BRDF (reflectance) + BTDF (transmittance) |
| [Microfacet theory](#microfacet-theory) | Real surfaces aren't flat at the micro level — they're a large number of randomly aligned planar fragments (microfacets) |
| [Dielectrics vs conductors](#dielectrics-vs-conductors) | How dielectric and conductor surfaces divide specular and diffuse reflection |
| [Energy conservation](#energy-conservation) | A good PBR BRDF is energy conservative: total reflected (specular + diffuse) energy is ≤ incident energy |
| [Specular BRDF (Cook-Torrance)](#specular-brdf-cook-torrance) | The specular term is the Cook-Torrance approximation of the microfacet integral |
| [Diffuse BRDF (Lambert vs Disney)](#diffuse-brdf-lambert-vs-disney) | Filament uses a simple Lambertian diffuse BRDF (uniform diffuse response over the microfacet hemisphere) |
| [Energy compensation (multiscattering)](#energy-compensation-multiscattering) | The single-bounce Cook-Torrance model loses energy at high roughness |
| [Parameterization & remapping](#parameterization--remapping) | Disney's full model has too many parameters for real-time |
| [Extended models](#extended-models) | In Filament's implementation the standard, clear-coat, and anisotropic models combine into one flexible model |

## Notation

| Symbol | Meaning |
|---|---|
| `n` | surface normal unit vector |
| `v` | view unit vector |
| `l` | incident light unit vector |
| `h` | half unit vector between `l` and `v` |
| `NoL`, `NoV`, `NoH`, `VoH`, `LoH` | clamped dot products (e.g. `n·l`), in `[0..1]` |
| `α` (`roughness`) | roughness, remapped from input `perceptualRoughness` |
| `σ` | diffuse reflectance |
| `f0` | reflectance at normal incidence (perpendicular view) |
| `f90` | reflectance at grazing angle |
| `n_ior` | index of refraction (IOR) of an interface |

The user-facing roughness input is `perceptualRoughness`; the value used inside the BRDF math is `roughness` = `perceptualRoughness²` (see [remapping](#perceptualroughness--roughness)). Code throughout uses `roughness` to mean the already-remapped `α`.

## The standard surface model

A material is described by a BSDF (Bidirectional Scattering Distribution Function) = BRDF (reflectance) + BTDF (transmittance). Filament's standard model focuses on the BRDF and ignores/approximates the BTDF — it correctly mimics reflective, isotropic, dielectric or conductive surfaces with short mean free paths.

The BRDF is the sum of two terms — a diffuse component `fd` and a specular component `fr`:

```glsl
f(v,l) = fd(v,l) + fr(v,l)
```

This is the response for light from a single direction; the full rendering equation integrates `l` over the hemisphere.

**Standard model summary:**
- **Specular**: Cook-Torrance microfacet model = GGX normal distribution (D) × Smith-GGX height-correlated visibility (V) × Schlick Fresnel (F).
- **Diffuse**: Lambertian.

## Microfacet theory

Real surfaces aren't flat at the micro level — they're a large number of randomly aligned planar fragments (microfacets). Only microfacets whose normal is oriented halfway between `l` and `v` (i.e. aligned with `h`) reflect visible light; masking and shadowing then cut down which of those actually contribute.

Roughness drives this: smoother surface → more aligned facets → sharper, more pronounced specular highlight; rougher surface → fewer facets aimed at the camera → light scattered away → blurry highlights.

General microfacet integral (x = specular or diffuse component):

```glsl
fx(v,l) = (1 / (|NoV| |NoL|)) * ∫_Ω D(m,α) G(v,l,m) fm(v,l,m) (v·m) (l·m) dm
```

- `D` — distribution of microfacet normals (the NDF). Dominant driver of surface appearance.
- `G` — visibility / occlusion / shadow-masking of microfacets.
- `fm` — the per-microfacet BRDF; what differs between specular and diffuse.

The hemisphere integration happens at the *micro* level; at the *macro* level the shaded fragment is treated as a flat point. Computing the full integral per fragment is impractical, so D, G, F are approximated (below).

## Dielectrics vs conductors

When light hits a surface it splits into specular reflectance (off the interface) and diffuse reflectance (light that penetrates, scatters inside, and re-exits). The key distinction:

- **Conductors (metals):** no subsurface scattering → **no diffuse component**. All reflectance is specular, and the specular color is **chromatic** (tinted by the metal).
- **Dielectrics (non-metals):** scattering occurs → **both** specular and diffuse. Specular reflectance at normal incidence is **achromatic** (a single grey f0).

This is why `metallic` controls whether `baseColor` is used as diffuse albedo (dielectric) or specular color (conductor) — see [baseColor remapping](#basecolor--diffuse--f0).

## Energy conservation

A good PBR BRDF is energy conservative: total reflected (specular + diffuse) energy is ≤ incident energy. This means artists never have to hand-balance reflected light against incident light to avoid surfaces that look brighter than their illumination. The standard single-bounce model still loses energy at high roughness — addressed by [energy compensation](#energy-compensation-multiscattering).

## Specular BRDF (Cook-Torrance)

The specular term is the Cook-Torrance approximation of the microfacet integral:

```glsl
fr(v,l) = D(h,α) G(v,l,α) F(v,h,f0) / (4 (NoV) (NoL))
```

The `4 (NoV)(NoL)` denominator folds into G to give a visibility function `V`, so Filament evaluates:

```glsl
fr(v,l) = D(h,α) * V(v,l,α) * F(v,h,f0)
where V(v,l,α) = G(v,l,α) / (4 (NoV)(NoL))
```

### D — Normal distribution (GGX)

Long-tailed NDFs fit real surfaces well (Burley). Filament uses the **GGX** distribution (equivalent to Trowbridge-Reitz) — long-tailed falloff, short highlight peak:

```glsl
D_GGX(h,α) = α² / (π ((NoH)² (α² - 1) + 1)²)
```

Reference GLSL:

```glsl
float D_GGX(float NoH, float roughness) {
    float a = NoH * roughness;
    float k = roughness / (1.0 - NoH * NoH + a * a);
    return k * k * (1.0 / PI);
}
```

fp16-safe variant (uses Lagrange's identity `|n×h|² = 1 - (NoH)²` to avoid floating-point cancellation near `NoH ≈ 1`):

```glsl
#define MEDIUMP_FLT_MAX    65504.0
#define saturateMediump(x) min(x, MEDIUMP_FLT_MAX)

float D_GGX(float roughness, float NoH, const vec3 n, const vec3 h) {
    vec3 NxH = cross(n, h);
    float a = NoH * roughness;
    float k = roughness / (dot(NxH, NxH) + a * a);
    float d = k * k * (1.0 / PI);
    return saturateMediump(d);
}
```

### G / V — Geometric shadowing (Smith-GGX)

The Smith function is the correct G term (Heitz): `G(v,l,α) = G1(l,α) · G1(v,α)`. Filament uses the **height-correlated Smith-GGX visibility** function (correlating masking and shadowing via microfacet height is more accurate):

```glsl
V(v,l,α) = 0.5 / ( NoL·√((NoV)²(1-α²)+α²) + NoV·√((NoL)²(1-α²)+α²) )
```

Reference GLSL (note: parameter `roughness` here is `α`, already remapped):

```glsl
float V_SmithGGXCorrelated(float NoV, float NoL, float roughness) {
    float a2 = roughness * roughness;
    float GGXV = NoL * sqrt(NoV * NoV * (1.0 - a2) + a2);
    float GGXL = NoV * sqrt(NoL * NoL * (1.0 - a2) + a2);
    return 0.5 / (GGXV + GGXL);
}
```

Fast approximation (drops the two `sqrt`s — mathematically wrong but good enough for mobile; can also be written as a single `lerp`):

```glsl
float V_SmithGGXCorrelatedFast(float NoV, float NoL, float roughness) {
    float a = roughness;
    float GGXV = NoL * (NoV * (1.0 - a) + a);
    float GGXL = NoV * (NoL * (1.0 - a) + a);
    return 0.5 / (GGXV + GGXL);
}
// equivalent: V = 0.5 / lerp(2·NoL·NoV, NoL + NoV, α)
```

### F — Fresnel (Schlick)

The Fresnel effect: how much light reflects depends on viewing angle (and the material's IOR). At normal incidence reflectance is `f0`; at grazing angle it approaches 100% (`f90`). `f0` is **achromatic for dielectrics, chromatic for metals**.

Schlick approximation:

```glsl
F_Schlick(v,h,f0,f90) = f0 + (f90 - f0)(1 - VoH)⁵
```

```glsl
vec3 F_Schlick(float u, vec3 f0, float f90) {
    return f0 + (vec3(f90) - f0) * pow(1.0 - u, 5.0);
}
```

Both dielectrics and conductors show achromatic specular reflectance at grazing angles and Fresnel = 1.0 at 90°, so Filament sets **`f90 = 1.0`**. That lets the scalar form drop `f90`:

```glsl
vec3 F_Schlick(float u, vec3 f0) {
    float f = pow(1.0 - u, 5.0);
    return f + f0 * (1.0 - f);
}
```

## Diffuse BRDF (Lambert vs Disney)

Filament uses a simple **Lambertian** diffuse BRDF (uniform diffuse response over the microfacet hemisphere). Extremely efficient, results close enough to fancier models:

```glsl
fd(v,l) = σ / π

float Fd_Lambert() { return 1.0 / PI; }
vec3 Fd = diffuseColor * Fd_Lambert();
```

The diffuse reflectance `σ` (`diffuseColor`) is multiplied in afterward.

The alternative **Disney diffuse BRDF** (Burley) takes roughness into account and adds retro-reflection at grazing angles, but costs more and complicates IBL / spherical-harmonics — Filament judged the quality gain not worth it. For completeness:

```glsl
fd(v,l) = (σ/π) · F_Schlick(n,l,1,f90) · F_Schlick(n,v,1,f90)
where f90 = 0.5 + 2·α·cos²(θd)

float Fd_Burley(float NoV, float NoL, float LoH, float roughness) {
    float f90 = 0.5 + 2.0 * roughness * LoH * LoH;
    float lightScatter = F_Schlick(NoL, 1.0, f90);
    float viewScatter  = F_Schlick(NoV, 1.0, f90);
    return lightScatter * viewScatter * (1.0 / PI);
}
```

Note: the Disney diffuse BRDF as expressed here is **not** energy conserving.

Full standard-model evaluation (note the `perceptualRoughness² → roughness` remap inline):

```glsl
void BRDF(...) {
    vec3 h = normalize(v + l);

    float NoV = abs(dot(n, v)) + 1e-5;
    float NoL = clamp(dot(n, l), 0.0, 1.0);
    float NoH = clamp(dot(n, h), 0.0, 1.0);
    float LoH = clamp(dot(l, h), 0.0, 1.0);

    // perceptually linear roughness to roughness
    float roughness = perceptualRoughness * perceptualRoughness;

    float D = D_GGX(NoH, roughness);
    vec3  F = F_Schlick(LoH, f0);
    float V = V_SmithGGXCorrelated(NoV, NoL, roughness);

    vec3 Fr = (D * V) * F;          // specular
    vec3 Fd = diffuseColor * Fd_Lambert();  // diffuse
    // apply lighting...
}
```

## Energy compensation (multiscattering)

The single-bounce Cook-Torrance model loses energy at high roughness — rays masked after one bounce are discarded, so rough surfaces darken. Metals are hit hardest (all-specular). A white-furnace test (uniform pure-white env, fully reflective metal `f0 = 1`) reveals it: such a surface should vanish into the background at any roughness, but single-scattering darkens it as roughness rises.

Filament compensates by scaling the specular lobe (Lagarde/Golubev; Kulla/Conty). The key simplification: the average Fresnel reduces to `f0`, and the compensation reuses `r`, the specular DFG term precomputed in the IBL DFG lookup table:

```glsl
fr(l,v) = fss(l,v) + f0·(1/r - 1)·fss(l,v)
where r = ∫_Ω D(l,v) V(l,v) <NoL> dl   (stored as dfg.y)

vec3 energyCompensation = 1.0 + f0 * (1.0 / dfg.y - 1.0);
Fr *= pixel.energyCompensation;  // scale specular lobe for multiscattering
```

(Cost is negligible since `r` is already in the DFG LUT used for image-based lighting.)

## Parameterization & remapping

Disney's full model has too many parameters for real-time. Filament reduces to a small, intuitive set; any combination should yield a physically plausible result.

### Standard parameters and ranges

| Parameter | Physical meaning | Type / range |
|---|---|---|
| **baseColor** | Diffuse albedo for non-metals; specular color for metals | Linear RGB `[0..1]` |
| **metallic** | Dielectric (0.0) vs conductor (1.0). Effectively binary | Scalar `[0..1]` |
| **roughness** | Perceived smoothness (0.0) → roughness (1.0). Smooth = sharp reflections | Scalar `[0..1]` |
| **reflectance** | Fresnel reflectance at normal incidence for dielectrics — replaces an explicit IOR | Scalar `[0..1]` |
| **emissive** | Extra diffuse albedo for self-emitting surfaces (neons etc.); most useful in HDR + bloom | Linear RGB `[0..1]` + exposure compensation |
| **ambientOcclusion** | Per-pixel fraction of ambient light reaching a point | Scalar `[0..1]` |

(Tools/UI may expose these in friendlier units — e.g. baseColor in sRGB, metallic/roughness/reflectance as 0–255 grey — and convert before the shader.)

### baseColor → diffuse / f0

`baseColor` plays two roles depending on `metallic`. Dielectrics keep baseColor as diffuse and have achromatic specular; conductors use baseColor as the specular color and have no diffuse. So the shader works with `diffuseColor` and `f0`, not baseColor directly:

```glsl
vec3 diffuseColor = (1.0 - metallic) * baseColor.rgb;
```

Conductor f0 is chromatic, taken straight from baseColor: `f0 = baseColor · metallic`. Combined f0 for both cases:

```glsl
vec3 f0 = 0.16 * reflectance * reflectance * (1.0 - metallic) + baseColor * metallic;
```

### reflectance → f0 (dielectrics)

Dielectric `f0` is achromatic and derived from the user's `reflectance` parameter (Lagarde 2014 remapping):

```glsl
f0 = 0.16 · reflectance²
```

This maps the `[0..1]` input onto the Fresnel range covering common dielectrics (4%) up to gemstones (8–16%). It is tuned so `reflectance = 0.5` (128 on a linear grey scale) yields the canonical **4%** Fresnel reflectance — the default.

If the IOR is known instead, f0 follows from it (and inverts back):

```glsl
f0(n_ior) = (n_ior - 1)² / (n_ior + 1)²
n_ior     = 2 / (1 - √f0) - 1
```

`f90` (grazing) is set to **1.0** for all materials.

Common dielectric reference values (no real material is under 2%):

| Material | Reflectance | IOR | Linear value |
|---|---|---|---|
| Water | 2% | 1.33 | 0.35 |
| Fabric | 4%–5.6% | 1.5–1.62 | 0.5–0.59 |
| Common liquids | 2%–4% | 1.33–1.5 | 0.35–0.5 |
| Common gemstones | 5%–16% | 1.58–2.33 | 0.56–1.0 |
| Plastics, glass | 4%–5% | 1.5–1.58 | 0.5–0.56 |
| Other dielectrics | 2%–5% | 1.33–1.58 | 0.35–0.56 |
| Eyes | 2.5% | 1.38 | 0.39 |
| Skin | 2.8% | 1.4 | 0.42 |
| Hair | 4.6% | 1.55 | 0.54 |
| Teeth | 5.8% | 1.63 | 0.6 |
| **Default** | **4%** | **1.5** | **0.5** |

For metals, `f0` is the measured sRGB reflectance used as baseColor — e.g. Gold `0.97`/`0.74`/`0.62`... (silver, aluminum, iron, copper, etc. each have characteristic chromatic f0). `reflectance` is ignored for metals.

### perceptualRoughness → roughness

The user sets `perceptualRoughness`; the BRDF uses `roughness` (`α`). The remapping is a simple square (perceptually linear — Burley reached the same conclusion; cubic/quadratic were tried and rejected):

```glsl
roughness (α) = perceptualRoughness²
```

Without it, shiny metals would be crammed into a tiny `[0.0, 0.05]` band.

**Clamping:** roughness is used in computations like `1/roughness⁴` that underflow in fp16 (smallest half-float `2⁻¹⁴ ≈ 6.1×10⁻⁵`). To avoid div-by-zero on devices without denormals, `perceptualRoughness` is clamped to a minimum of **0.089** (gives `1/roughness⁴ ≈ 6.274×10⁻⁵`). Roughness can never be 0 (div-by-zero, plus near-invisible highlights); clamping also reduces specular aliasing. (Frostbite clamps analytic-light roughness to 0.045 when using fp32.)

### Authoring cheat sheet

- **All materials** — baseColor should carry no baked lighting (except micro-occlusion). Treat `metallic` as near-binary (0 or 1); intermediate values are only for transitions (metal→rust).
- **Non-metals** — baseColor sRGB in 50–240 (strict) or 30–240 (tolerant); metallic = 0; reflectance = 127 sRGB (0.5 linear, 4%) if unsure, never below 90 sRGB (0.35 linear, 2%).
- **Metals** — baseColor is both specular color and reflectance, luminosity 67–100% (170–255 sRGB); metallic = 1; reflectance is ignored. Dirty/oxidized metals use lower luminosity.
- **Blending/layering** materials is just interpolating these parameters; intermediate blends look plausible even if not strictly physical.

## Extended models

In Filament's implementation the standard, clear-coat, and anisotropic models combine into one flexible model. Each extended model below adds parameters on top of the standard set.

### Clear coat

**When:** multi-layer materials with a thin translucent layer over a base — car paint, soda cans, lacquered wood, acrylic.

Adds a second specular lobe (a second Cook-Torrance BRDF). The coat is **always isotropic and dielectric**; the base layer can be anything the standard model allows. Energy lost traversing the coat is accounted for (no inter-reflection/refraction simulated).

The coat BRDF reuses GGX (D) and Schlick (F) but swaps in the cheaper **Kelemen visibility** (the coat is low-roughness, so accuracy loss is invisible):

```glsl
V_Kelemen(LoH) = 1 / (4 (LoH)²)

float V_Kelemen(float LoH) { return 0.25 / (LoH * LoH); }
```

Coat Fresnel assumes a polyurethane coat, IOR 1.5 → `f0 = (1.5-1)²/(1.5+1)² = 0.04` (the usual 4% dielectric value).

Surface response with the coat (`Fc` = coat Fresnel, `fc` = coat BRDF):

```glsl
f(v,l) = fd(v,l)(1 - Fc) + fr(v,l)(1 - Fc) + fc(v,l)
```

Extra parameters:

| Parameter | Meaning | Range |
|---|---|---|
| **clearCoat** | Strength of the clear coat layer | `[0..1]` |
| **clearCoatRoughness** | Perceived roughness of the coat | `[0..1]` |

`clearCoatRoughness` is remapped/clamped like standard roughness (square it; clamp to `[0.089, 1.0]`).

```glsl
clearCoatPerceptualRoughness = clamp(clearCoatPerceptualRoughness, 0.089, 1.0);
clearCoatRoughness = clearCoatPerceptualRoughness * clearCoatPerceptualRoughness;

float  Dc = D_GGX(clearCoatRoughness, NoH);
float  Vc = V_Kelemen(clearCoatRoughness, LoH);
float  Fc = F_Schlick(0.04, LoH) * clearCoat;  // coat strength
float Frc = (Dc * Vc) * Fc;
// account for energy loss in the base layer:
return color * ((Fd + Fr) * (1.0 - Fc) + Frc);
```

**Base-layer f0 modification:** the base f0 normally assumes an air-material interface, but under a coat it's a coat-material interface. Recompute via the base IOR then a new f0 against the coat's IOR (1.5):

```glsl
IOR_base = (1 + √f0) / (1 - √f0)
f0_base  = ((IOR_base - 1.5) / (IOR_base + 1.5))²
// combined (coat IOR fixed at 1.5):
f0_base  = (1 - 5√f0)² / (5 - √f0)²
```

(Filament leaves the corresponding base-roughness adjustment out for now.)

### Anisotropic

**When:** surfaces whose reflection differs by direction — brushed metal, etc. (isotropic models can't reproduce these).

Uses an anisotropic GGX NDF with two roughness terms — `αt` (tangent) and `αb` (bitangent) — derived from `α` and an `anisotropy` parameter. Filament uses the Kulla relationship (allows sharper highlights):

```glsl
αt = α · (1 + anisotropy)
αb = α · (1 - anisotropy)

// implementation guards against zero:
float at = max(roughness * (1.0 + anisotropy), 0.001);
float ab = max(roughness * (1.0 - anisotropy), 0.001);
```

Requires tangent and bitangent directions (already available from normal mapping). Uses an anisotropic Smith-GGX visibility (`V_SmithGGXCorrelated_Anisotropic`) to match.

Extra parameter:

| Parameter | Meaning | Range |
|---|---|---|
| **anisotropy** | Amount of anisotropy | `[-1..1]` |

No remapping needed. **Negative values align the anisotropy with the bitangent** direction instead of the tangent.

### Subsurface

The standard-doc section is a `[TODO]` placeholder in this source — no equations or parameters are specified here. (A separate `subsurfaceColor` mechanism does appear in the cloth model below.)

### Cloth (sheen)

**When:** loosely-woven fabrics — denim, cotton, velvet — that absorb and scatter light, giving a soft specular lobe with large falloff plus fuzz/rim lighting from forward/backward scattering. (Leather, silk, and satin are still better done with the standard or anisotropic models.)

Standard microfacet BRDFs assume mirror-like grooves and render cloth as rigid/plastic-looking, so cloth uses a modified BRDF:

- **Specular NDF** — an inverted-Gaussian "velvet" distribution (Ashikhmin) that produces fuzz lighting plus a front-facing specular offset; the masking/shadowing term is dropped. Filament also offers the "Charlie" sheen NDF (Estevez/Kulla) — softer, more intuitive, simpler:

```glsl
// velvet (Ashikhmin/Neubelt), normalized
float D_Ashikhmin(float roughness, float NoH) {
    float a2 = roughness * roughness;
    float cos2h = NoH * NoH;
    float sin2h = max(1.0 - cos2h, 0.0078125);
    float sin4h = sin2h * sin2h;
    float cot2 = -cos2h / (a2 * sin2h);
    return 1.0 / (PI * (4.0 * a2 + 1.0) * sin4h) * (4.0 * exp(cot2) + sin4h);
}

// "Charlie" sheen (Estevez/Kulla)
float D_Charlie(float roughness, float NoH) {
    float invAlpha = 1.0 / roughness;
    float cos2h = NoH * NoH;
    float sin2h = max(1.0 - cos2h, 0.0078125);
    return (2.0 + invAlpha) * pow(sin2h, invAlpha * 0.5) / (2.0 * PI);
}
```

- **Visibility** — a smoother Neubelt denominator: `V = 1 / (4(NoL + NoV - NoL·NoV))`. The Fresnel term is removed from the cloth specular BRDF.
- **Diffuse** — Lambertian, made energy conservative (like clear coat), with an optional non-physical subsurface scattering term using wrapped diffuse (`w = 0.5` fixed) — simulates scatter/absorption/re-emission in fabrics.

Extra parameters (cloth drops `metallic` and `reflectance`):

| Parameter | Meaning | Default |
|---|---|---|
| **sheenColor** | Specular tint for two-tone fabrics (e.g. velvet) | 0.04 (matches standard reflectance) |
| **subsurfaceColor** | Tint of diffuse color after scatter/absorption | — |

Authoring: for **velvet**, set baseColor black/dark and put the chromaticity on `sheenColor`. For **denim/cotton**, put chromaticity in baseColor and leave sheenColor at default (or set it to baseColor's luminance).
