# Tooling: CLI Tools, Debuggers & Performance

> Source: Filament tool READMEs + library notes (cmgen/filamesh/mipgen/matinfo/specgen/matdbg/viewer/framegraph/debugging), Filament v1.72.0
> Last synced: 2026-06-19

**Contents:** [Asset & Material CLI Tools](#asset--material-cli-tools) · [matc — material compiler (cross-ref)](#matc--material-compiler-cross-ref) · [cmgen — IBL / cubemap & SH generation](#cmgen--ibl--cubemap--sh-generation) · [filamesh — mesh → .filamesh binary](#filamesh--mesh--filamesh-binary) · [mipgen — mipmap chains](#mipgen--mipmap-chains) · [matinfo — inspect a compiled .filamat](#matinfo--inspect-a-compiled-filamat) · [specgen — spectral integration matrices (dispersion)](#specgen--spectral-integration-matrices-dispersion) · [normal_blending — combine two normal maps](#normal_blending--combine-two-normal-maps) · [roughness_prefilter — prefilter a roughness map](#roughness_prefilter--prefilter-a-roughness-map) · [Inspect & Debug Libraries](#inspect--debug-libraries) · [matdbg — in-app material debugger web UI](#matdbg--in-app-material-debugger-web-ui) · [viewer — model viewer / gltf_viewer](#viewer--model-viewer--gltf_viewer) · [filamat — runtime material compilation (cross-ref)](#filamat--runtime-material-compilation-cross-ref) · [Performance & Backend Debugging](#performance--backend-debugging) · [FrameGraph](#framegraph) · [Performance analysis (Android / AGI)](#performance-analysis-android--agi) · [Metal debugging](#metal-debugging) · [Vulkan debugging](#vulkan-debugging)

---

## Asset & Material CLI Tools

### matc — material compiler (cross-ref)

Compiles `.mat` material definitions into `.filamat` packages. Full flags, variants, and
build-time vs runtime tradeoffs are documented in
[`materials-compiling-matc.md`](./materials-compiling-matc.md).

### cmgen — IBL / cubemap & SH generation

Generate spherical harmonics (SH) and mipmap levels from an environment map. Consumes HDR
environment maps in latlong (equirectangular), "cross" cubemap (vertical/horizontal), and
row/column cubemap formats — auto-detected by aspect ratio. Produces a mipmapped IBL (Image
Based Lighting), a blurry skybox, or both.

Input formats: PNG (8/16-bit), Radiance (`.hdr`), Photoshop (`.psd`, 16/32-bit), OpenEXR (`.exr`).

```shell
cmgen [options] <input-file>
cmgen [options] <uv[N]>
```

Key options (verbatim):

```
--help, -h
    Print this message
--license
    Print copyright and license information
--quiet, -q
    Quiet mode. Suppress all non-error output
--type=[cubemap|equirect|octahedron|ktx], -t [cubemap|equirect|octahedron|ktx]
    Specify output type (default: cubemap)
--format=[exr|hdr|psd|rgbm|rgb32f|png|dds|ktx], -f [format]
    Specify output file format. ktx implies -type=ktx.
    KTX files are always KTX1 files, not KTX2.
    They are encoded with 3-channel RGB_10_11_11_REV data
--compression=COMPRESSION, -c COMPRESSION
    Format specific compression:
        KTX: ignored
        PNG: Ignored
        PNG RGBM: Ignored
        Radiance: Ignored
        Photoshop: 16 (default), 32
        OpenEXR: RAW, RLE, ZIPS, ZIP, PIZ (default)
        DDS: 8, 16 (default), 32
--size=power-of-two, -s power-of-two
    Size of the output cubemaps (base level), 256 by default
    Also applies to DFG LUT
--deploy=dir, -x dir
    Generate everything needed for deployment into <dir>
--extract=dir
    Extract faces of the cubemap into <dir>
--extract-blur=roughness
    Blurs the cubemap before saving the faces using the roughness blur
--clamp
    Clamp environment before processing
--no-mirror
    Skip mirroring of generated cubemaps (for assets with mirroring already backed in)
--ibl-samples=numSamples
    Number of samples to use for IBL integrations (default 1024)
--ibl-ld=dir
    Roughness pre-filter into <dir>
--sh-shader
    Generate irradiance SH for shader code
```

Canonical command — generate everything needed for deployment into a directory:

```shell
cmgen --deploy=<output_dir> <environment.hdr>
```

### filamesh — mesh → .filamesh binary

Converts any `assimp`-supported mesh into Filament's custom binary `.filamesh` format for fast,
easy loading in test apps. The source mesh must have at least one set of UV coordinates. Output
contains vertex positions, one UV set, and per-vertex tangents/bitangents/normals as a single
vertex buffer + single index buffer; mesh parts are offset/count ranges with per-part materials.

```shell
filamesh source_mesh destination_mesh
```

Format notes: header magic is `FILAMESH`. Flags bits — Bit 0: interleaved vertex attributes;
Bit 1: UVs are 16-bit ints normalized to [-1,+1] (vs half-floats); Bit 2: vertex/index data
compressed with zeux/meshoptimizer. UV1 cannot be used in interleaved mode. (A Hex Fiend
template for inspecting `.filamesh` files lives in `ide/hexfiend/Templates`.)

### mipgen — mipmap chains

Generates mipmaps for an image down to the 1x1 level.

```shell
mipgen [options] <input_file> <output_pattern>
```

Run `mipgen --help` for available options. (The README does not enumerate them.)

### matinfo — inspect a compiled .filamat

Lists the contents of a compiled material as output by `matc` (variants, shaders, etc.).
Debug-purpose only.

```shell
matinfo [options] <material file>
```

### specgen — spectral integration matrices (dispersion)

Pre-calculates a set of matrices `K_n` for real-time spectral dispersion (wavelength-dependent
refraction) in an RGB pipeline. Each `K_n` is the contribution of one sample wavelength to the
final image, folding in the sRGB↔XYZ conversions and that sample's spectral weight; weights are
normalized for energy conservation so that a white input stays white when there's no dispersion.

It also precomputes per-wavelength IOR `Offset(λ)` from a Cauchy dispersion model parameterized
by the Abbe number, so the shader can compute each sample's index of refraction cheaply:

```glsl
float ior_n = baseIOR + dispersionFactor * offsets[n];
```

The source doc is theoretical background only — it does not document a command line or flags.

### normal_blending — combine two normal maps

Combines two normal maps into a single texture using _Reoriented Normal Mapping_, which gives
mathematically correct results (unlike linear or overlay blending). The README documents purpose
only — no command line / flags.

### roughness_prefilter — prefilter a roughness map

Generates a pre-filtered roughness map from a normal map; input roughness may be a constant or a
roughness map. The output reduces shading aliasing. The README documents purpose only — no command
line / flags.

---

## Inspect & Debug Libraries

### matdbg — in-app material debugger web UI

A library + web app for debugging and live-editing Filament shaders. Supports: OpenGL (edit GLSL),
Metal (edit MSL), Vulkan (edit transpiled GLSL, view disassembled SPIR-V), WebGPU (edit WGSL).
A material built with multiple backends can have any of its backends inspected, regardless of
which backend the running app uses.

**Desktop setup** — build with matdbg enabled (the `-d` build flag turns on the
`FILAMENT_ENABLE_MATDBG` CMake option; `f` forces a CMake re-run), set the port env var, then point
a browser at it:

```shell
./build.sh -fd debug gltf_viewer
export FILAMENT_MATDBG_PORT=8080   # Windows: use `set` instead of `export`
# launch an app linked against a debug Filament, then open:
# http://localhost:8080
```

**Android setup** — rebuild Filament with `FILAMENT_ENABLE_MATDBG` ON (pragmatically, force it ON
in `CMakeLists.txt` and `filament-android/CMakeLists.txt`), add the INTERNET permission to the
manifest, then forward the device's hardcoded port **8081** to the host:

```shell
adb forward tcp:8081 tcp:8081
# then open http://localhost:8081 in Chrome on the host
```

Android release builds optimize shaders into something unreadable; pass `-g` to `matc` even in
release to keep them readable.

**Usage**: select a material (upper-left), then an active (boldface) shader variant (lower-left) to
view GLSL/MSL/SPIR-V. Edit GLSL/MSL (inputs/uniforms must stay intact) and click `[rebuild]` —
edits are lost when the page closes. Active status refreshes every second; the material database is
cleared only on a manual page refresh.

Keyboard shortcuts: **Cmd+S** (Ctrl+S on Linux/Windows) to save/rebuild; with editor focus,
**Shift+Ctrl + ↑/↓** navigates materials and **Shift+Ctrl + ←/→** navigates variants.

Architecture: a C++ `DebugServer` (civetweb-based HTTP + WebSocket) plus a JavaScript client
(lit-html + monaco). HTTP GET API returns JSON keyed by an 8-digit hex `{id}` (a hash of the
material package):

```
/api/matids                                              # array of known material ids
/api/materials                                           # all info (no shader source) for all materials
/api/material?matid={id}                                 # same, one material
/api/active                                              # map of matid -> active variant(s)
/api/shader?matid={id}&type=[glsl|spirv|msl]&[glindex|vkindex|metalindex]={index}   # returns shader text
```

`type` selects the shading language (e.g. SPIR-V vs decompiled GLSL for Vulkan), not the backend;
the original GLSL behind the SPIR-V is not recoverable.

### viewer — model viewer / gltf_viewer

`libs/viewer` is a high-level abstraction for configuring and rendering Filament scenes; it backs
tools like `gltf_viewer` (load assets, manage settings, drive the render loop). Features: a
`Settings` struct (View/Camera/Lights/Materials), JSON load/save, an `AutomationEngine` for batch
scripting via JSON test cases, and imgui GUI binding via `ViewerGui`.

JSON settings (used by `gltf_viewer --settings` and automation specs) — root keys: `view`,
`camera`, `lighting`, `viewer`, `animation`, `material`. Highlights:

- `camera` — explicit camera control; `enabled: true` required to override the default orbit
  camera. Keys include `projection` ("PERSPECTIVE"/"ORTHO"), `center`, `lookAt`, `up`, `near`,
  `far`, `focalLength` (mm), `fov` (deg, overrides focalLength if >0), `aperture`, `shutterSpeed`,
  `sensitivity` (ISO), `focusDistance`.
- `lighting` — `iblIntensity`, `iblRotation` (deg), `enableSunlight`, `enableShadows`, a nested
  `sunlight` object (intensity/color/direction/halo/`shadowOptions`), and a `lights[]` array
  (`type`: POINT/SPOT/FOCUSED_SPOT/DIRECTIONAL/SUN).
- `view` — `postProcessingEnabled`, `antiAliasing` ("NONE"/"FXAA"), `msaa`, `ssao`, `bloom`,
  `dof`, `vignette`, `colorGrading` (`toneMapping`: LINEAR/ACES/FILMIC/PBR_NEUTRAL/ACES_LEGACY/…).
- `viewer` — `skyboxEnabled`, `backgroundColor`, `autoScaleEnabled`, `groundPlaneEnabled`.
- `animation` — `enabled`, `speed`, `time` (if ≥0, forces that time in seconds).

### filamat — runtime material compilation (cross-ref)

`filamat` builds materials programmatically on-device (vs `matc` on the host), at the cost of a
larger app binary. `filamat_lite` is a smaller drop-in: OpenGL-only, no shader optimization, no
GLSL correctness checking, and the `MaterialInputs` variable must always be named `material`.
Core usage — `MaterialBuilder::init()`, configure a `MaterialBuilder`, `build()` a `Package`, then
`MaterialBuilder::shutdown()`. Distributed as static libs (`filamat`, `filabridge`, `shaders`,
`utils`, `smol-v`); Java via `filamat-java.jar` + `filamat-jni`. See also
[`materials-compiling-matc.md`](./materials-compiling-matc.md).

---

## Performance & Backend Debugging

### FrameGraph

A framework inside Filament for computing the resources needed to render a frame and declaring
dependencies between them (e.g. the color pass depends on the shadow-map texture written by an
earlier pass). It is a directed acyclic graph of two node types:

- **Resource** — a generic resource, ~90% of the time a texture.
- **Pass** — a computation/rendering process that reads a set of resources and writes a set.

Edges: Resource→Pass = read, Pass→Resource = write, Resource→Resource = subresource relationship
(e.g. a mip layer). Because the graph is acyclic, passes can be ordered by topological sort; the
framework also detects cycles and culls unreachable nodes.

What it does: manages resource lifetimes (allocate/use/free), computes texture usage bits (e.g.
sampled vs blitted), and computes render-target load/store bits (keep vs discard). Build passes
with `fg.addPass<Data>(name, setup, execute)` — the setup lambda runs immediately/synchronously to
declare resources; the execute lambda runs later when the completed graph is traversed.
(Resource import/export supports cross-frame techniques like TAA.)

A graphical FrameGraph debugger ("fgviewer", in the spirit of matdbg) is listed as future work in
the source notes, not a shipped tool.

### Performance analysis (Android / AGI)

Profile with **Android GPU Inspector (AGI)** — https://developer.android.com/agi. Key guidance:

- **Lock the GPU frequency** before profiling for consistent results (requires an OEM-unlocked,
  rooted/`-userdebug`/`-eng` device). The GPU sysfs path varies per device (e.g.
  `/sys/class/kgsl/kgsl-3d0`, or a `*.mali` path); read `available_governors` /
  `available_frequencies`, then pin via the device's knobs (e.g. `gpu_governor`,
  `gpu_min_freq`/`gpu_max_freq`, or `hint_min_freq`/`hint_max_freq`). Re-apply just before the
  trace and verify with `cur_freq` before and after; settings revert on reboot.
- Build a **release** build (debug builds are useless for this); WebGPU needs the explicit `-W`
  flag, e.g. `./build.sh -W -p android,desktop -i release`. Limit ABI with `-q arm64-v8a` to speed
  the build (then set `com.google.android.filament.abis` in `android/gradle.properties`).
- Select the backend at runtime via system property (numbers map to `enum class Backend` in
  `DriverEnums.h`):

```shell
adb shell setprop debug.filament.backend 2   # Vulkan
adb shell setprop debug.filament.backend 4   # WebGPU
adb shell getprop debug.filament.backend     # view current
```

- Use AGI's **"Capture System Profiler trace"** (Vulkan API config — WebGPU runs on Vulkan
  underneath); ~1s is enough. In advanced mode, restrict track_event categories to
  `filament/filament`, `filament/jobsystem`, `filament/gltfio`. Focus on the `FEngine::loop`
  thread: total time, overlap of activities, fewer queue submissions, and on the GPU timeline,
  overlapping shader invocations with uninterrupted fragment-shader runs. Navigate with
  `W`/`S`/`A`/`D` and the mouse wheel.

### Metal debugging

Enable the Metal validation layers via env var (look for "Metal API Validation Enabled" on
startup):

```shell
export METAL_DEVICE_WRAPPER_TYPE=1
```

Capture a Metal frame from `gltf_viewer`: create an `Info.plist` next to `gltf_viewer`
(`cmake/samples`) with `MetalCaptureEnabled` = `true`, run normally, and hit "Capture frame" under
the Debug menu. The capture is written to `filament.gputrace` in the CWD, openable in Xcode.

### Vulkan debugging

Install the LunarG Vulkan SDK and set these env vars (e.g. in `.bashrc`); with a **debug** build of
Filament, validation errors/perf warnings then print to the console:

```shell
export VULKAN_SDK='/path_to_home/VulkanSDK/1.3.216.0/x86_64'
export VK_LAYER_PATH="$VULKAN_SDK/etc/explicit_layer.d"
export PATH="$VULKAN_SDK/bin:$PATH"
```
