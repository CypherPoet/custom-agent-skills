# Imaging Pipeline: Camera, Exposure, Post-Processing & Coordinates

> Source: Filament Core Concepts — "Imaging pipeline" + Annex (Filament.md), Filament v1.75.0
> Last synced: 2026-08-14

## Table of Contents

| Section | Covers |
|---|---|
| [The Imaging Pipeline](#the-imaging-pipeline) | Filament's lighting equations compute scene luminance in physically based photometric units |
| [Physically Based Camera & Exposure](#physically-based-camera--exposure) | The first step is using a physically based camera to properly expose the scene's outgoing luminance |
| [Post-Processing & `View` Options](#post-processing--view-options) | Post-processing is configured on the `View` (`View.h`) |
| [Color Management](#color-management) | Linear vs sRGB, Color Conversion API, and ColorSpace API |
| [Renderer Pipeline: Clustered Forward Rendering](#renderer-pipeline-clustered-forward-rendering) | Filament uses clustered forward rendering |
| [Coordinate Systems & Conventions](#coordinate-systems--conventions) | Quoting the doc's "Coordinates systems" section |
| [Validation & Debug](#validation--debug) | Reference rendering, debug views, and checks for the imaging pipeline |

---

## The Imaging Pipeline

Filament's lighting equations compute scene luminance in physically based photometric units. These HDR values must be transformed into displayable pixel values. The pipeline (from `03-imaging-pipeline.md`):

```
Scene luminance → Normalized luminance (HDR) → White balance
  → Color grading → Tone mapping → OETF → Pixel value (LDR)
```

The **OETF** step applies the opto-electronic transfer function of the target color space. Post-processing effects (vignette, bloom, etc.) are applied separately and are *not* shown in that core diagram — see the `ColorGrading` ordering and `View` options below for where each actually sits.

---

## Physically Based Camera & Exposure

The first step is using a physically based camera to properly expose the scene's outgoing luminance. Because Filament uses photometric units throughout, the light reaching the camera is luminance $L$ in $cd \cdot m^{-2}$. Incident light spans a huge range — from $10^{-5}\,cd.m^{-2}$ (starlight) to $10^{9}\,cd.m^{-2}$ (the sun) — so it must be remapped. The scene's light range is centered around "middle gray" (18%, halfway between black and white).

### The Exposure Triangle

Exposure is achieved (manually or automatically) by manipulating 3 settings:

| Setting | Symbol | Unit | Also controls |
|---|---|---|---|
| **Aperture** | $N$ | f-stops (ƒ) | Depth of field. High value (ƒ/16) = small aperture; small value (ƒ/1.4) = wide aperture. F-stop = ratio of focal length to entrance-pupil diameter. |
| **Shutter speed** | $t$ | seconds ($s$) | Motion blur. How long the aperture stays open. |
| **Sensitivity** (gain / "ISO") | $S$ | ISO | Amount of noise. How light reaching the sensor is quantized. |

The same exposure (same EV) can be hit by many combinations — the artistic trade-off is depth of field vs motion blur vs grain.

### Exposure Value (EV)

EV summarizes the triangle on a base-2 log scale. A difference of **1 EV = one "stop"**: +1 EV is a factor of two in luminance, −1 EV is a factor of half.

$$EV = log_2\left(\frac{N^2}{t}\right)$$

This is a function of aperture and shutter speed only — *not* sensitivity. By convention EV is defined at ISO 100 ($EV_{100}$):

$$EV_S = EV_{100} + log_2\left(\frac{S}{100}\right)$$

$$EV_{100} = EV_S - log_2\left(\frac{S}{100}\right) = log_2\left(\frac{N^2}{t}\right) - log_2\left(\frac{S}{100}\right)$$

**EV ↔ luminance** (calibration constant $K = 12.5$, the reflected-light meter constant used by Canon/Nikon/Sekonic; Pentax/Minolta use 14):

$$EV = log_2\left(\frac{L \times S}{K}\right) \quad\Rightarrow\quad EV = log_2\left(L \frac{100}{12.5}\right)$$

$$L = 2^{EV_{100}} \times \frac{12.5}{100} = 2^{EV_{100} - 3}$$

**EV ↔ illuminance** (incident-light meter constant $C$; flat sensor 250, hemispherical 320 Minolta / 340 Sekonic):

$$EV = log_2\left(\frac{E \times S}{C}\right) \quad\Rightarrow\quad EV = log_2\left(E \frac{100}{C}\right)$$

Flat sensor ($C=250$): $E = 2^{EV_{100}} \times 2.5$. Hemispherical ($C=340$): $E = 2^{EV_{100}} \times 3.4$.

**Exposure compensation** ($EC$, in f-stops) offsets EV. Note the negative sign — a higher EV produces a *darker* image:

$$EV_{100}' = EV_{100} - EC$$

### Photometric Exposure & Normalization

To convert scene luminance into normalized luminance, use the photometric (luminous) exposure $H$ in lux-seconds:

$$H = \frac{q \cdot t}{N^2} L$$

where $q$ is lens + vignetting attenuation, typically $q = 0.65$. Filament uses the **saturation-based speed** relation, giving the max exposure that doesn't clip:

$$H_{sat} = \frac{78}{S_{sat}}$$

The maximum luminance that saturates the sensor, and the normalization, are:

$$L_{max} = \frac{N^2}{q \cdot t}\frac{78}{S} \qquad L' = \frac{L}{L_{max}}$$

Simplified for $S=100$, $q=0.65$:

$$L_{max} = 2^{EV_{100}} \times 1.2$$

GLSL implementation (the exposure factor can be precomputed on the CPU to save shader instructions):

```glsl
// aperture in f-stops, shutterSpeed in seconds, sensitivity in ISO
float exposureSettings(float aperture, float shutterSpeed, float sensitivity) {
    return log2((aperture * aperture) / shutterSpeed * 100.0 / sensitivity);
}

// exposure normalization factor from the camera's EV100
float exposure(float ev100) {
    return 1.0 / (pow(2.0, ev100) * 1.2);
}

float ev100 = exposureSettings(aperture, shutterSpeed, sensitivity);
float exposure = exposure(ev100);

vec4 color = evaluateLighting();
color.rgb *= exposure;
```

### `Camera` Exposure API

From `Camera.h`. The Camera sets the scene's exposure just like a real camera; light intensity and Camera exposure interact to produce final brightness.

```cpp
/** Sets this camera's exposure (default is f/16, 1/125s, 100 ISO)
 *
 * @param aperture      Aperture in f-stops, clamped between 0.5 and 64.
 *                      A lower aperture value increases the exposure (brighter).
 *                      Realistic values are between 0.95 and 32.
 * @param shutterSpeed  Shutter speed in seconds, clamped between 1/25,000 and 60.
 *                      A lower shutter speed increases the exposure.
 *                      Realistic values are between 1/8000 and 30.
 * @param sensitivity   Sensitivity in ISO, clamped between 10 and 204,800.
 *                      A higher sensitivity increases the exposure.
 *                      Realistic values are between 50 and 25600.
 */
void setExposure(float aperture, float shutterSpeed, float sensitivity) noexcept;

/** Sets this camera's exposure directly. Sets aperture to 1.0, shutter speed
 * to 1.2, and computes sensitivity to match (for exposure 1.0, sensitivity = 100 ISO).
 * Useful to match other engines/tools that use unit-less light intensities. */
void setExposure(float exposure) noexcept {
    setExposure(1.0f, 1.2f, 100.0f * (1.0f / exposure));
}

float getAperture() const noexcept;       //!< aperture in f-stops
float getShutterSpeed() const noexcept;   //!< shutter speed in seconds
float getSensitivity() const noexcept;    //!< sensitivity in ISO
```

**Defaults**: `f/16, 1/125s, 100 ISO` — adequate exposure for a sunny outdoor scene with the sun at zenith. With the defaults, the scene needs at least one Light of sun-like intensity (e.g. a 100,000 lux directional light).

Why this matters: because everything is photometric, light intensities are set in real physical units (lux, candela, lumens) and the camera's f-number / shutter / ISO determine how those map to pixels — exactly as in photography. `setExposure(float)` is the escape hatch for matching engines that use arbitrary unit-less intensities.

Related `Camera` methods used by the imaging effects:

```cpp
/** Focus distance, used by the Depth-of-field PostProcessing effect.
 *  @param distance to the plane of focus in world units; must be > near plane. */
void setFocusDistance(float distance) noexcept;
float getFocusDistance() const noexcept;

/** Focal length in meters [m] for a 35mm camera (uses Eye 0's projection). */
double getFocalLength() const noexcept;
static double computeEffectiveFocalLength(double focalLength, double focusDistance) noexcept;
static double computeEffectiveFov(double fovInDegrees, double focusDistance) noexcept;
```

### `Exposure` Utility Namespace

From `Exposure.h` — free functions in `namespace filament::Exposure` for computing exposure, EV100, luminance, and illuminance with the physically based camera model. Each comes in 3 overloads: from a `Camera`, from raw `(aperture, shutterSpeed, sensitivity)`, and from a precomputed value.

```cpp
// All free functions in namespace filament::Exposure

float ev100(const Camera& camera) noexcept;
float ev100(float aperture, float shutterSpeed, float sensitivity) noexcept;
float ev100FromLuminance(float luminance) noexcept;   // luminance in cd/m^2
float ev100FromIlluminance(float illuminance) noexcept; // illuminance in lux

float exposure(const Camera& camera) noexcept;
float exposure(float aperture, float shutterSpeed, float sensitivity) noexcept;
float exposure(float ev100) noexcept;

float luminance(const Camera& camera) noexcept;        // camera as a spot meter, cd/m^2
float luminance(float aperture, float shutterSpeed, float sensitivity) noexcept;
float luminance(float ev100) noexcept;

float illuminance(const Camera& camera) noexcept;      // camera as incident light meter, lux
float illuminance(float aperture, float shutterSpeed, float sensitivity) noexcept;
float illuminance(float ev100) noexcept;
```

Note: `exposure(aperture, shutterSpeed, sensitivity)` is equivalent to `exposure(ev100(aperture, shutterSpeed, sensitivity))` but is slightly faster and higher precision (same pattern for the `luminance` / `illuminance` 3-arg overloads). EV100 is *not* itself a measure of luminance or illuminance — the conversion functions return the luminance/illuminance for which a camera would use that EV100 for nominally correct exposure.

### Automatic Exposure & Metering

Since EV can be derived from measured luminance, the camera can act as a spot meter for auto-exposure. Two common scene-luminance measurement techniques:

- **Luminance downsampling** — successively downsample the previous frame to a 1×1 log-luminance buffer read on the CPU (or via compute shader); gives average log luminance. Can be unstable; smooth over time.
- **Luminance histogram** — find average log luminance while ignoring extreme values; more stable.

Both measure luminance *after* albedo multiplication (not strictly correct, but the alternative is too expensive). Both implement *average* metering. Cameras also offer:

- **Spot metering** — only a small center circle (1–5% of image) contributes. Weight is 1 inside the spot radius, 0 outside.
- **Center-weighted metering** — more influence near the center, via a smoothing function (e.g. `smoothstep`).
- **Multi-zone / matrix metering** — manufacturer-specific; splits the image into a grid and classifies cells to prioritize important regions.

**Adaptation** smoothing (exponential feedback loop, Pattanaik et al.):

$$L_{avg} = L_{avg} + (L - L_{avg}) \times (1 - e^{-\Delta t \cdot \tau})$$

where $\Delta t$ is delta time and $\tau$ controls adaptation rate.

### EV as a Light Unit & Emissive Bloom

Because the EV scale is nearly perceptually linear, EV (via exposure compensation) can be used as a light unit — letting artists specify light/emissive intensity relative to exposure. **Avoid this when possible**, but it's useful to force (or cancel) a bloom around emissive surfaces independent of camera settings (e.g. a lightsaber that should always bloom).

$$EV_{bloom} = EV_{100} + EC \qquad L_{bloom} = c \times 2^{EV_{bloom} - 3}$$

```glsl
vec4 surfaceShading() {
    vec4 color = evaluateLights();
    // rgb = color, w = exposure compensation
    vec4 emissive = getEmissive();
    color.rgb += emissive.rgb * pow(2.0, ev100 + emissive.w - 3.0);
    color.rgb *= exposure;
    return color;
}
```

---

## Post-Processing & `View` Options

Post-processing is configured on the `View` (`View.h`). Master toggle:

```cpp
void setPostProcessingEnabled(bool enabled) noexcept;   // enabled by default
bool isPostProcessingEnabled() const noexcept;
```

`setPostProcessingEnabled` docs enumerate what post-processing includes (in roughly this order): Depth-of-field, Bloom, Vignetting, Temporal Anti-aliasing (TAA), Color grading & gamma encoding, Dithering, FXAA, Dynamic scaling. Disabling it forgoes color correctness and most anti-aliasing — use only for debugging, UI overlays, or custom render targets.

### Tone Mapping (`ToneMapper`)

From `ToneMapper.h`. A tone mapper compresses scene dynamic range to a display range. In Filament tone mapping is a **color grading step**: a `ToneMapper` instance is passed to `ColorGrading::Builder` to produce a 3D LUT used during post-processing.

The `operator()` maps open-domain ("scene referred") to display-domain ("display referred") color; **both input and output are linear Rec.2020** (no transfer function applied). There is an optional NEON 4-pixel overload on most operators.

`ToneMapper` base interface:

```cpp
struct ToneMapper {
    virtual math::float3 operator()(math::float3 c) const noexcept = 0;
    virtual bool isOneDimensional() const noexcept { return false; } // 1D LUT possible
    virtual bool isLDR() const noexcept { return false; }            // LUT need not be log-encoded
};
```

Three categories of provided operators:

**Configurable**

- `GenericToneMapper` — full control over the curve. Constructor (defaults approximate an ACES curve, hdrMax = 10.0):
  ```cpp
  explicit GenericToneMapper(
      float contrast   = 1.55f,   // > 0.0; 0.5..2.0 recommended
      float midGrayIn  = 0.18f,   // 0.0..1.0
      float midGrayOut = 0.215f,  // 0.0..1.0
      float hdrMax     = 10.0f    // >= 1.0; max input mapped to output white
  ) noexcept;
  // getters/setters: getContrast/setContrast, getMidGrayIn/setMidGrayIn,
  //                  getMidGrayOut/setMidGrayOut, getHdrMax/setHdrMax
  // isOneDimensional() -> true
  ```
- `AgxToneMapper` — `explicit AgxToneMapper(AgxLook look = AgxLook::NONE)`.
  `enum class AgxLook : uint8_t { NONE = 0, PUNCHY, GOLDEN }`.
  NONE = base contrast; PUNCHY = punchy/more chroma for sRGB; GOLDEN = golden, washed look for BT.1886. Public field `AgxLook look;`.

**Fixed-aesthetic**

- `ACESToneMapper` — ACES RRT + ODT for sRGB monitors (dim surround, 100 nits).
- `ACESLegacyToneMapper` — ACES modified to match `FilmicToneMapper` perceived brightness (~1.6× brightness multiplier to target brighter viewing environments). **This is Filament's default tone mapper.**
- `FilmicToneMapper` — approximates ACES RRT+ODT for Rec.709; Filament's historical default. Kept for backward compatibility, **not otherwise recommended**. `isOneDimensional() -> true`.
- `PBRNeutralToneMapper` — Khronos PBR Neutral; preserves material appearance across lighting, avoids HDR highlight artifacts.
- `GT7ToneMapper` — Gran Turismo 7; preserves material appearance, avoids HDR highlight artifacts. Targets an SDR paper-white of 250 nits, reference luminance 100 cd/m² (= 1.0 in the HDR framebuffer).

**Debug / validation**

- `LinearToneMapper` — returns input clamped to 0..1. `isOneDimensional() -> true`, `isLDR() -> true`.
- `DisplayRangeToneMapper` — maps HDR RGB into 16 debug colors representing exposure. Cyan = middle gray (18%); each stop above/below shifts color: −5EV black, −4 darkest blue, −3 darker blue, −2 dark blue, −1 blue, **0EV cyan**, +1 dark green, +2 green, +3 yellow, +4 yellow-orange, +5 orange, +6 bright red, +7 red, +8 magenta, +9 purple, +10EV white. Useful for validating/tweaking scene lighting.

### Color Grading (`ColorGrading::Builder`)

From `ColorGrading.h`. `ColorGrading` transforms the HDR buffer; transforms are applied **after lighting and after lens effects (e.g. bloom)** and **include tone mapping**. Created with the builder, set on a `View`, destroyed via `Engine::destroy(const ColorGrading*)`. Building may generate a LUT on the CPU and can be more expensive than other Filament objects.

```cpp
filament::ColorGrading* colorGrading = filament::ColorGrading::Builder()
        .toneMapping(filament::ColorGrading::ToneMapping::ACES)
        .build(*engine);
myView->setColorGrading(colorGrading);
engine->destroy(colorGrading);
```

**Ordering** (transforms are applied in this exact order):
Exposure → Night adaptation → White balance → Channel mixer → Shadows/mid-tones/highlights → Slope/offset/power (CDL) → Contrast → Vibrance → Saturation → Curves → Tone mapping → Luminance scaling → Gamut mapping.

**Defaults**: Exposure 0.0; Night adaptation 0.0; White balance temperature 0, tint 0; Channel mixer red {1,0,0} green {0,1,0} blue {0,0,1}; Shadows/mid-tones/highlights {1,1,1,0} each, ranges {0,0.333,0.550,1}; Slope 1.0 / Offset 0.0 / Power 1.0; Contrast 1.0; Vibrance 1.0; Saturation 1.0; Curves gamma {1,1,1} midPoint {1,1,1} scale {1,1,1}; Tone mapping **ACESLegacyToneMapper**; Luminance scaling false; Gamut mapping false; Output color space **Rec709-sRGB-D65**.

LUT control enums and builder methods:

```cpp
enum class QualityLevel : uint8_t { LOW, MEDIUM, HIGH, ULTRA };
enum class LutFormat   : uint8_t { INTEGER /*10 bpc*/, FLOAT /*16 bpc, 10-bit mantissa*/ };

// Deprecated — prefer toneMapper(ToneMapper*)
enum class ToneMapping : uint8_t {
    LINEAR = 0, ACES_LEGACY = 1, ACES = 2, FILMIC = 3, DISPLAY_RANGE = 4
};
```

`Builder` methods (all return `Builder&` for chaining unless noted):

```cpp
// LUT configuration
Builder& quality(QualityLevel);   // default MEDIUM. LOW=16^3 10bit, MEDIUM=32^3 10bit,
                                  //   HIGH=32^3 16bit, ULTRA=64^3 16bit. Overrides format/dimensions.
Builder& format(LutFormat);       // default INTEGER; overrides quality()
Builder& dimensions(uint8_t dim); // default 32; range 16..64; overrides quality()

// Tone mapping
Builder& toneMapper(ToneMapper const* toneMapper); // default ACESLegacyToneMapper
Builder& toneMapping(ToneMapping);                 // deprecated; default ACES_LEGACY

// EVILS / gamut
Builder& luminanceScaling(bool); // LICH from EVILS; high-chroma rolls off to white,
                                 //   avoids hue skews; tone maps on luminance not per-channel
Builder& gamutMapping(bool);     // bring out-of-gamut back in (preserve chroma/lightness) vs clip

// Grading adjustments
Builder& exposure(float);                          // in EV stops; applied AFTER all post-processing
Builder& nightAdaptation(float adaptation);        // 0 (none) .. 1 (full)
Builder& whiteBalance(float temperature, float tint); // each [-1..+1]; temp -1=50000K, +1=2000K
Builder& channelMixer(float3 outRed, float3 outGreen, float3 outBlue); // each component [-2..+2]
Builder& shadowsMidtonesHighlights(float4 shadows, float4 midtones,
                                   float4 highlights, float4 ranges); // .rgb color, .w weight; linear space
Builder& slopeOffsetPower(float3 slope, float3 offset, float3 power);  // ASC CDL; log space;
                                                                       //   slope/power strictly positive
Builder& contrast(float);    // [0.0..2.0]; 1.0 = no effect; log space
Builder& vibrance(float);    // [0.0..2.0]; 1.0 = no effect; linear space
Builder& saturation(float);  // [0.0..2.0]; 1.0 = no effect; linear space
Builder& curves(float3 shadowGamma, float3 midPoint, float3 highlightScale); // linear space

// Custom LUT & output
Builder& customLut(utils::FixedCapacityVector<math::float3> data, uint8_t dimension); // applied in LDR (sRGB)
Builder& outputColorSpace(const color::ColorSpace&); // must be Rec709-sRGB-D65 or Rec709-Linear-D65
                                                     //   (only the transfer function is used)
Builder& exportLut(ExportCallback callback, void* user = nullptr); // inspect/copy generated LUT
Builder& fastMath(bool);     // default true; false forces exact libm scalar math

ColorGrading* build(Engine& engine);
```

Note: `ColorGrading::Builder::exposure()` is in EV stops and applied *after* all post-processing (bloom, etc.), in contrast to `Camera::setExposure` which is the photographic exposure applied before post-processing. White balance: temperature/tint are blue-yellow and green-magenta axes respectively.

### Bloom, Lens Flare & Chromatic Aberration (`BloomOptions`)

From `Options.h`. Bloom simulates saturated photosites creating a glow in bright scene regions. Set via `View::setBloomOptions(BloomOptions)`. **Disabled by default.** Notably, screen-space **lens flare** and **chromatic aberration** are fields of `BloomOptions` (not a separate options struct).

```cpp
struct BloomOptions {
    enum class BlendMode : uint8_t {
        ADD,         // bloom modulated by strength, added to scene
        INTERPOLATE  // bloom interpolated with scene using strength
    };
    Texture* dirt = nullptr;            // dirt/scratch/smudge texture; requires threshold=true
    float dirtStrength = 0.2f;
    float strength = 0.10f;             // 0.0..1.0 — how much bloom is added
    uint32_t resolution = 384;          // resolution of vertical axis (2^levels to 2048)
    uint8_t levels = 6;                 // number of blur levels (1 to 11)
    BlendMode blendMode = BlendMode::ADD;
    bool threshold = true;              // threshold source at 1.0
    bool enabled = false;
    float highlight = 1000.0f;          // limit highlights to this before bloom [10, +inf]
    QualityLevel quality = QualityLevel::LOW; // LOW/MEDIUM/HIGH; HIGH improves anamorphic bloom

    // --- Screen-space lens flare ---
    bool lensFlare = false;             // enable screen-space lens flare
    bool starburst = true;              // starburst effect on lens flare
    float chromaticAberration = 0.005f; // amount of chromatic aberration
    uint8_t ghostCount = 4;             // number of flare "ghosts"
    float ghostSpacing = 0.6f;          // spacing of ghosts in screen units [0, 1[
    float ghostThreshold = 10.0f;       // hdr threshold for ghosts
    float haloThickness = 0.1f;         // halo thickness in vertical screen units, 0 = off
    float haloRadius = 0.4f;            // halo radius in vertical screen units [0, 0.5]
    float haloThreshold = 10.0f;        // hdr threshold for halo
};
```

(The doc-comment's `BlendMode` description says "additive (false)" vs "mixed (true)"; the actual enum is `ADD` / `INTERPOLATE`.) Filament's optics docs note that lens flares use an **image-based** approach rather than physically tracing rays through the lens assembly — cheaper, with free emitter occlusion and unlimited light-source support.

### Depth of Field (`DepthOfFieldOptions`)

From `Options.h`. Set via `View::setDepthOfFieldOptions`. **Disabled by default.** Uses the `Camera`'s focus distance (`Camera::setFocusDistance`). `cocScale` decouples blur from aperture artistically: `cocScale = cameraAperture / desiredDoFAperture`.

```cpp
struct DepthOfFieldOptions {
    enum class Filter : uint8_t { NONE, UNUSED, MEDIAN };
    float cocScale = 1.0f;              // circle-of-confusion scale (amount of blur)
    float cocAspectRatio = 1.0f;        // CoC w/h aspect (anamorphic lenses)
    float maxApertureDiameter = 0.01f;  // max aperture diameter in meters (0 disables rotation)
    bool enabled = false;
    Filter filter = Filter::MEDIAN;     // gap-filling filter
    bool nativeResolution = false;      // process DoF at native resolution
    uint8_t foregroundRingCount = 0;    // kernel rings, foreground tiles (0=default: 5 desktop, 3 mobile)
    uint8_t backgroundRingCount = 0;    // kernel rings, background tiles
    uint8_t fastGatherRingCount = 0;    // kernel rings, fast tiles
    uint16_t maxForegroundCOC = 0;      // max CoC px, foreground [0,32]; 0=default 32 desktop/24 mobile
    uint16_t maxBackgroundCOC = 0;      // max CoC px, background [0,32]; 0=default 32 desktop/24 mobile
};
```

Samples-per-pixel for a gather kernel = `(ringCount * 2 - 1)^2` (3 rings → 25, 4 → 49, 5 → 81, 17 → 1089). With a max CoC of 32, never more than 17 rings needed.

### Vignette (`VignetteOptions`)

From `Options.h`. Set via `View::setVignetteOptions`. **Disabled by default.**

```cpp
struct VignetteOptions {
    float midPoint = 0.5f;   // higher = vignette closer to corners, [0,1]
    float roundness = 0.5f;  // shape: rounded rect (0.0) → oval (0.5) → circle (1.0)
    float feather = 0.5f;    // softening amount, [0,1]
    LinearColorA color = {0.0f, 0.0f, 0.0f, 1.0f}; // alpha currently ignored
    bool enabled = false;
};
```

### Other `View` Post-Process Options

All from `Options.h` / `View.h`. Selected relevant structs:

- **`FogOptions`** (large-scale fog; `setFogOptions`, disabled by default): `distance`, `cutOffDistance = INFINITY`, `maximumOpacity = 1.0f`, `height = 0.0f`, `heightFalloff = 1.0f`, `color = {1,1,1}`, `density = 0.1f` (extinction in 1/m), `inScatteringStart`, `inScatteringSize = -1.0f`, `fogColorFromIbl = false`, `Texture* skyColor`, `enabled = false`.
- **`AntiAliasing`** enum (`setAntiAliasing`): `NONE`, `FXAA` (default FXAA is enabled). Plus `MultiSampleAntiAliasingOptions` (MSAA, `sampleCount = 4`) and `TemporalAntiAliasingOptions` (TAA, `feedback = 0.12f`, `jitterPattern = HALTON_23_X16`).
- **`Dithering`** enum (`setDithering`): `NONE`, `TEMPORAL` (default).
- **`RenderQuality`** (`setRenderQuality`): `hdrColorBuffer = QualityLevel::HIGH`. HIGH/ULTRA → RGB16F/RGBA16F (10-bit LDR precision); LOW/MEDIUM → R11G11B10F opaque or RGBA16F transparent.
- **`AmbientOcclusionOptions`** (`setAmbientOcclusionOptions`): `aoType` SAO or GTAO, `radius = 0.3f`, etc.
- **`ScreenSpaceReflectionsOptions`** (`setScreenSpaceReflectionsOptions`), **`GuardBandOptions`**, **`DynamicResolutionOptions`**, **`StereoscopicOptions`**.
- Color grading is attached separately via `View::setColorGrading(ColorGrading*)`.

---

## Color Management

### Linear vs sRGB

Lighting, post-processing on scene-referred data, and most internal math happen in **linear** space. The advice from the imaging docs: perform post-processing on scene-referred linear data (before tone mapping) as much as possible. The conversion to display (sRGB) happens at the **OETF** step at the very end of the pipeline (after tone mapping), as part of color grading & gamma encoding. The `ColorGrading` output color space (default `Rec709-sRGB-D65`) controls the transfer function applied to the final color.

Tone mapper input/output is **linear Rec.2020** (no transfer function), so the color-management chain converts scene-referred linear → tone-mapped → output color space transfer function → display pixel.

### `Color` Conversion API

From `Color.h`. Type aliases and conversion utilities:

```cpp
using LinearColor   = math::float3; //!< RGB color in linear space
using sRGBColor     = math::float3; //!< RGB color in sRGB space
using LinearColorA  = math::float4; //!< RGBA color in linear space, with alpha
using sRGBColorA    = math::float4; //!< RGBA color in sRGB space, with alpha

enum class RgbType : uint8_t {
    sRGB,   //!< color defined in Rec.709-sRGB-D65 (sRGB) space
    LINEAR, //!< color defined in Rec.709-Linear-D65 ("linear sRGB") space
};

enum class RgbaType : uint8_t {
    sRGB, LINEAR, PREMULTIPLIED_sRGB, PREMULTIPLIED_LINEAR  // not / are pre-multiplied by alpha
};

enum ColorConversion {
    ACCURATE,   //!< accurate conversion using the sRGB standard
    FAST        //!< fast conversion using a simple gamma 2.2 curve
};

class Color {
public:
    static LinearColor  toLinear(RgbType type, math::float3 color);
    static LinearColorA toLinear(RgbaType type, math::float4 color);
    template<ColorConversion = ACCURATE> static LinearColor  toLinear(sRGBColor const& color);
    template<ColorConversion = ACCURATE> static sRGBColor    toSRGB(LinearColor const& color);
    template<ColorConversion = ACCURATE> static LinearColorA toLinear(sRGBColorA const& color);
    template<ColorConversion = ACCURATE> static sRGBColorA   toSRGB(LinearColorA const& color);

    static LinearColor cct(float K);          // correlated color temp → linear RGB; K in [1000, 15000]
    static LinearColor illuminantD(float K);  // CIE illuminant D → linear RGB; K in [4000, 25000]
    static math::float3 absorptionAtDistance(LinearColor const& color, float distance); // Beer-Lambert
};
```

`FAST` conversions use `pow(color, 2.2)` (to linear) and `pow(color, 1/2.2)` (to sRGB); `ACCURATE` uses the sRGB standard curve.

### `ColorSpace` API

From `ColorSpace.h`, `namespace filament::color`. A color space is always RGB, defined by `Primaries` (xy chromaticities of R/G/B), a `WhitePoint` (xy), and a `TransferFunction` (ICC parametric curve). Constants and the builder ("-") syntax:

```cpp
struct Primaries { float2 r, g, b; };
using WhitePoint = float2;
struct TransferFunction { double a, b, c, d, e, f, g; /* ICC type 3/4 ctors */ };

//! Rec.709 color gamut, used in the sRGB and DisplayP3 color spaces.
constexpr Gamut Rec709 = {{0.640f,0.330f},{0.300f,0.600f},{0.150f,0.060f}};
constexpr TransferFunction Linear = { 1.0, 0.0, 0.0, 0.0, 1.0 };
constexpr TransferFunction sRGB   = { 1.0/1.055, 0.055/1.055, 1.0/12.92, 0.04045, 2.4 };
//! Standard CIE 1931 2° illuminant D65 — color temperature 6504K.
constexpr WhitePoint D65 = { 0.31271f, 0.32902f };

// Build with "-" syntax, e.g.:  ColorSpace cs = Rec709-Linear-D65;
```

---

## Renderer Pipeline: Clustered Forward Rendering

Filament uses **clustered forward rendering**. Goal constraints: low bandwidth, many dynamic lights per pixel; plus easy support for MSAA, transparency, and multiple material models.

Why not the alternatives:
- **Deferred** scales to hundreds/thousands of lights but is bandwidth-heavy — Filament's default PBR G-buffer would be 160–192 bits/pixel.
- **Classic forward** is historically bad at many lights (re-render per light, or a fixed max lights per object — impractical for large objects).
- **Tiled shading** (2D screen grid) reduces overdraw/shading but suffers from depth-discontinuity issues causing extraneous work.

**Clustered shading** extends tiling with a 3rd (depth) axis: the view-space frustum is split into a 3D grid. Each cluster is a **froxel** ("voxel in frustum space"). The "froxelization" pass voxelizes the frustum (e.g. a 1280×720 target with 80×80px tiles → 16×9 tiles, combined with depth slices).

**Light assignment**: before rendering, each light is assigned to every froxel it intersects (sphere/frustum test for point lights, cone/frustum for spot lights). The result is a per-froxel light list. During rendering, a fragment computes its froxel ID and only iterates that froxel's lights — **this is why many dynamic lights are cheap**: each fragment only shades the lights that can actually affect it, not all scene lights.

**Practical limits / numbers (from annex listings)**:
- Per-froxel max lights — the example listings use `#define MAX_LIGHT_COUNT 16` (fragment-side example) and `#define MAX_FROXEL_LIGHT_COUNT 32u` (compute assignment example). A sentinel `0x7fffffffu` separates point and spot lights and marks the end of a froxel's list.
- Depth slicing is **exponential, not linear** — more froxels near the near plane where more pixels are (example: near 0.1m, far 100m, 16 slices). A pure exponential wastes ~half the slices very close to the camera, so Filament manually tweaks the **first ("special") froxel** size (e.g. 0.1–5m occupies the first froxel; remaining 15 slices cover 5m–100m) to better distribute the rest.
- Assignment runs on **GPU** (compute shaders, requires OpenGL ES 3.1 + SSBOs; froxel generation runs once while the projection matrix is unchanged, assignment runs per frame) or **CPU** (rasterize each light into froxels; gives tighter culling and a packed light list on non-ES-3.1 devices).

**Tuning from the API** (`View.h`): `setDynamicLightingOptions(float zLightNear, float zLightFar)` — `zLightNear` (default **5m**) is where lights are expected to start shining, `zLightFar` (default **100m**) where they stop being visible; both clamped to the camera near/far. Choosing these well spreads the visible light influence and improves performance. Debug: `setFroxelVizEnabled(bool)` and `getFroxelConfigurationInfo()` (returns froxel `width`/`height`/`depth`, viewport dims, `froxelDimension`, `zLightFar`, `linearizer`, projection `p`, `clipTransform`).

**Depth ↔ froxel formulas** (from annex, for context when reading froxel debug data). Linear depth from `gl_FragCoord.z` (standard OpenGL projection):

$$linearZ(z) = \frac{n}{f + z(n-f)} = \frac{1}{z \cdot c0 + c1}, \quad c1 = \frac{f}{n},\; c0 = 1 - c1$$

Cluster index with the special-near fix $sn$:

$$zToCluster(z,n,sn,f,m) = floor\left(max\left(log_2(z)\frac{m-1}{-log_2(\frac{sn}{f})} + m,\ 0\right)\right)$$

---

## Coordinate Systems & Conventions

Quoting the doc's "Coordinates systems" section:

**World coordinate system** — Filament uses a **Y-up, right-handed** coordinate system. (Figure: red +X, green +Y, blue +Z.)

**Units** — world units are **meters** ([m]) throughout (near/far planes, fog distances, AO radius, focus distance, etc.).

**Camera coordinate system** — "Filament's Camera looks towards its local -Z axis. That is, when placing a camera in the world without any transform applied to it, the camera looks down the world's -Z axis." From `Camera.h`: the camera coordinate system defines *view space*; the camera points towards its **−z** axis, top in **+y**, right in **+x**.

**Near / far & clip space** (`Camera.h`):
- Near and far planes are defined by *distance* from the camera, so their view-space coordinates are −near and −far (the near plane is at view-space z = −near, far at z = −far).
- Six clipping planes (left, right, bottom, top, near, far) form a box (ORTHO) or frustum (PERSPECTIVE).
- For rendering, the **far plane is always assumed at infinity** (to maximize depth-buffer precision); it is still used during culling (objects entirely behind far are culled) and shadowing. `getProjectionMatrix()` returns the rendering matrix (far at infinity); `getCullingProjectionMatrix()` returns the finite-far matrix.
- **Pick the highest near distance possible** — depth-buffer precision drops rapidly with distance and is highly sensitive to near on OpenGL (much less so on Vulkan/Metal or GL with `EXT_clip_control`/`ARB_clip_control`). Keep a near:far ratio in **1:100 to 1:100000**.
- Custom projection matrices must use the **OpenGL NDC convention — all 3 axes mapped to [-1, 1]** (`setCustomProjection`).
- `Projection` enum: `PERSPECTIVE` (objects shrink with distance), `ORTHO` (preserves distances). `Fov` enum: `VERTICAL`, `HORIZONTAL`.

```cpp
enum class Projection : int { PERSPECTIVE, ORTHO };
enum class Fov : int { VERTICAL, HORIZONTAL };

void setProjection(double fovInDegrees, double aspect, double near, double far,
                   Fov direction = Fov::VERTICAL);   // 0 < fov < 180; aspect > 0; near > 0; far > near
void setLensProjection(double focalLengthInMillimeters, double aspect, double near, double far);
void setCustomProjection(math::mat4 const& projection, double near, double far); // NDC: all axes [-1,1]
void lookAt(math::double3 const& eye, math::double3 const& center,
            math::double3 const& up = math::double3{0, 1, 0}) noexcept;
```

**Front-face winding** (`View.h`) — front faces use a **counter-clockwise** winding order by default; `setFrontFaceWindingInverted(bool)` flips to clockwise (useful for mirrored reflections).

**Screen-space / picking** (`View.h`) — `View::pick(x, y, ...)`: x has origin on the **left**, y has origin at the **bottom**. `PickingQueryResult::fragCoords` are GL-convention screen-space; `depth` is 1 (near) to 0 (infinity). To reconstruct positions:
`clip = (fragCoords.xy / viewport.wh, fragCoords.z) * 2.0 - 1.0`; `view = inverse(projection) * clip`; `world = model * view`.

**Cubemaps** — follow the OpenGL face-alignment convention. IBL cubemaps are stored **mirrored on the X axis** (the default of the `cmgen` tool), so a cubemap used as environment background must be mirrored again at runtime (Filament does this by default via textured back faces). When specifying a skybox/IBL, the cubemap is oriented so its −Z face points towards the world's +Z (because Filament assumes mirrored cubemaps); pre-mirrored environments therefore have their −Z (back) face pointing towards the world's −Z, matching the camera's default look direction. Equirectangular → cross conversion positions the +Z face at the center of the source.

---

## Validation & Debug

- **Reference renderings** validated against **Mitsuba** (offline path tracer). The validation scene used Filament exposure **f/16, 1/125s, ISO 100**, directional light 120,000 lux, IBL multiplier 35,000 — and Mitsuba `exposure = -15.23` (computed from `log2(filamentExposure)`).
- **Scene-referred (luminance) visualization** — a custom debug tone-mapping operator color-codes stops around middle gray (18%): cyan = middle gray, blue 1 stop darker, green 1 stop brighter, etc. This is the same scheme exposed at runtime by `DisplayRangeToneMapper` (and `ToneMapping::DISPLAY_RANGE`). The 16-color debug array starts at black (−5EV) and runs to white (+10EV), with cyan as the 6th entry (0EV / middle gray).

```glsl
vec3 Tonemap_DisplayRange(const vec3 x) {
    // The 5th index (cyan) represents middle gray (18%); each stop shifts color.
    float v = log2(luminance(x) / 0.18);
    v = clamp(v + 5.0, 0.0, 15.0);
    int index = int(floor(v));
    return mix(debugColors[index], debugColors[min(15, index + 1)], fract(v));
}
```
