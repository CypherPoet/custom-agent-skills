# Compiling Materials (matc) & Color Handling

> Source: Filament Materials — "Compiling materials" + "Handling colors" (Materials.md) + filamat lib, Filament v1.75.0
> Last synced: 2026-08-14

`matc` is the command-line tool that compiles a material definition (`.mat`) into a
material package (`.filamat`). `filamat` is the library that does the same thing at
runtime / on-device. This file covers both, plus how colors must be fed to materials.

**Contents:** [The `matc` CLI](#the-matc-cli) · [Material Packages, Variants & Platforms](#material-packages-variants--platforms) · [Runtime Compilation — the `filamat` Library](#runtime-compilation--the-filamat-library) · [Handling Colors](#handling-colors)

## The `matc` CLI

Simplest invocation — give it an input `.mat` and an output `.filamat`:

```shell
matc -o ./materials/bin/car_paint.filamat ./materials/src/car_paint.mat
```

`matc` has **no standalone README**; its documentation is the "Compiling materials"
section reproduced here.

### Shader validation

`matc` validates shaders when compiling a package. Reported line numbers refer to the
**source material definition file**. Example error for a typo (`metalic` instead of
`metallic`) in the fragment shader:

```text
ERROR: 0:13: 'metalic' : no such field in structure
ERROR: 0:13: '' : compilation terminated
ERROR: 2 compilation errors.  No code generated.

Could not compile material metal.mat
```

### Flags

These are the flags relevant to application development (verbatim from the source
`matcFlags` table). `matc` offers a few other flags that are irrelevant to application
developers and for internal use only.

| Flag | Value | Usage |
|---|---|---|
| `-o`, `--output` | `[path]` | Specify the output file path |
| `-p`, `--platform` | `desktop`/`mobile`/`all` | Select the target platform(s) |
| `-a`, `--api` | `opengl`/`vulkan`/`all` | Specify the target graphics API |
| `-S`, `--optimize-size` | N/A | Optimize compiled material for size instead of just performance |
| `-r`, `--reflect` | `parameters` | Outputs the specified metadata as JSON |
| `-v`, `--variant-filter` | `[variant]` | Filters out the specified, comma-separated variants |

> Note on `-a`/`--api`: the source table lists `opengl`/`vulkan`/`all`. The PRIMARY
> doc's API table does not enumerate `metal` as an accepted value for the `matc` CLI,
> so it is not listed here. (The `metal` target API does appear in the `filamat`
> `TargetApi` enum below.)

#### `-p` / `--platform`

By default `matc` generates packages containing shaders for **all** supported
platforms. To reduce package size, select only the target platform. Android-only
example:

```shell
matc -p mobile -o ./materials/bin/car_paint.filamat ./materials/src/car_paint.mat
```

#### `-a` / `--api`

By default `matc` generates packages containing shaders for the **OpenGL** API. You can
add Vulkan shaders alongside OpenGL. If targeting only Vulkan-capable devices, generate
just the Vulkan shaders to reduce size:

```shell
matc -a vulkan -o ./materials/bin/car_paint.filamat ./materials/src/car_paint.mat
```

#### `-S` / `--optimize-size`

Applies **fewer** optimization techniques to keep the final material as small as
possible. If the default-compiled material is deemed too large, this flag is a good
compromise between runtime performance and size.

#### `-r` / `--reflect`

Designed to help build tooling around `matc`. Prints specific metadata in JSON. Example
— printing the parameters of Filament's standard skybox material (two parameters,
`showSun` and `skybox`, a boolean and a cubemap texture):

```shell
matc --reflect parameters filament/src/materials/skybox.mat
```

```json
{
  "parameters": [
    {
      "name": "showSun",
      "type": "bool",
      "size": "1"
    },
    {
      "name": "skybox",
      "type": "samplerCubemap",
      "format": "float",
      "precision": "default"
    }
  ]
}
```

#### `-v` / `--variant-filter`

Further reduces package size by naming shader variants the application **guarantees will
never be needed**. Skipped during code generation. Specify as a comma-separated list:

```shell
--variant-filter=skinning,shadowReceiver
```

Available variants:

- `directionalLighting` — a directional light is present in the scene
- `dynamicLighting` — a non-directional light (point, spot, etc.) is present in the scene
- `shadowReceiver` — an object can receive shadows
- `skinning` — an object is animated using GPU skinning or vertex morphing
- `fog` — global fog is applied to the scene
- `vsm` — VSM shadows are enabled and the object is a shadow receiver
- `ssr` — screen-space reflections are enabled in the View

Behavior notes:

- Some variants are filtered automatically — e.g. all lighting-related variants
  (`directionalLighting`, etc.) are filtered out when compiling an `unlit` material.
- The flag's filters are **merged** with the variant filters specified in the material
  itself.
- **Use with caution** — filtering out a variant required at runtime may lead to
  **crashes**.

## Material Packages, Variants & Platforms

A `.filamat` material package contains compiled shaders for the requested
platforms/APIs plus a set of **shader variants** (see the variant list above). The
runtime selects the right variant based on scene/View state (lighting present, shadow
receiving, skinning, fog, VSM, SSR, etc.).

- **Platform variants** are controlled by `-p`/`--platform` (`desktop`/`mobile`/`all`).
- **API variants** are controlled by `-a`/`--api` (`opengl`/`vulkan`/`all`); default is
  OpenGL.
- Compiling for **all** platforms/APIs (the default for platform) produces the largest
  package; narrowing the targets and filtering variants are the two levers for shrinking
  it.

### Sampler limits per feature level

The number of usable sampler parameters depends on shading model, feature level, and
variant filter. (Full detail lives in the samplers reference; the feature-level-relevant
facts:)

- **Feature level 1 & 2:** `unlit` materials up to **12** samplers by default; `lit`
  materials up to **9** (reduced to **8** if `refractionMode` or `reflectionMode` is
  `screenspace`). If the `variantFilter` contains the `fog` filter, one extra sampler is
  freed: `unlit` → up to **13**, `lit` → up to **10**.
- **Feature level 3:** **16** samplers available.
- `external` samplers each count as **2** regular samplers.

## Runtime Compilation — the `filamat` Library

`filamat` generates materials **programmatically on the device** instead of via `matc`
on the host. Cost: a binary-size increase from the relatively large `filamat` library.
It is included in the GitHub release packages.

### `MaterialBuilder` usage

```cpp
#include <filamat/MaterialBuilder.h>

#include <iostream>

using namespace filamat;

int main(int argc, char** argv)
{
    // Must be called before any materials can be built.
    MaterialBuilder::init();

    MaterialBuilder builder;
    builder
        .name("My material")
        .material("void material (inout MaterialInputs material) {"
                  "  prepareMaterial(material);"
                  "  material.baseColor.rgb = float3(1.0, 0.0, 0.0);"
                  "}")
        .shading(MaterialBuilder::Shading::LIT)
        .targetApi(MaterialBuilder::TargetApi::ALL)
        .platform(MaterialBuilder::Platform::ALL);

    Package package = builder.build();
    if (package.isValid()) {
        std::cout << "Success!" << std::endl;
    }

    // Call when finished building all materials to release internal MaterialBuilder resources.
    MaterialBuilder::shutdown();
    return 0;
}
```

Enum values shown in the source:

- `MaterialBuilder::Shading::LIT`
- `MaterialBuilder::TargetApi::ALL` (the `metal` target API is part of this enum family)
- `MaterialBuilder::Platform::ALL`

### Handing the package to Filament

```cpp
Package package = builder.build();
filament::Material* myMaterial = Material::Builder()
    .package(package.getData(), package.getSize())
    .build(*engine);
```

This requires linking against Filament's libraries in addition to Filamat's.

### Linking against `filamat`

Distributed as static libraries to link against:

- `filamat` — Filamat main library
- `filabridge` — support library for Filament / Filamat
- `shaders` — shader text for material generation
- `utils` — support library for Filament / Filamat
- `smol-v` — SPIR-V compression library

From **Java**, use these two instead:

- `filamat-java.jar` — Filamat's Java classes
- `filamat-jni` — Filamat's JNI bindings

Build (after a Makefile is in place): `make`, then run the executable; on Windows open a
Visual Studio Native Tools Command Prompt and run `nmake`.

```shell
make
./main
Success!
```

#### Linux Makefile

```make
FILAMENT_LIBS=-lfilamat -lfilabridge -lshaders -lutils -lsmol-v
CC=clang++

main: main.o
	$(CC) -Llib/x86_64/ -stdlib=libc++ main.o $(FILAMENT_LIBS) -lpthread -ldl -o main

main.o: main.cpp
	$(CC) -Iinclude/ -std=c++20 -stdlib=libc++ -pthread -c main.cpp

clean:
	rm -f main main.o

.PHONY: clean
```

#### macOS Makefile

```make
FILAMENT_LIBS=-lfilamat -lfilabridge -lshaders -lutils -lsmol-v
CC=clang++

main: main.o
	$(CC) -Llib/x86_64/ main.o $(FILAMENT_LIBS) -o main

main.o: main.cpp
	$(CC) -Iinclude/ -std=c++20 -c main.cpp

clean:
	rm -f main main.o

.PHONY: clean
```

#### Windows Makefile

Windows static libs ship variants `mt`/`md`/`mtd`/`mdd`, corresponding to the run-time
library flags `/MT`, `/MD`, `/MTd`, `/MDd`. The example uses `mt`. When building Filamat
from source, the `USE_STATIC_CRT` CMake option changes the run-time library version.

```make
FILAMENT_LIBS=lib/x86_64/mt/filamat.lib lib/x86_64/mt/filabridge.lib lib/x86_64/mt/shaders.lib \
              lib/x86_64/mt/utils.lib lib/x86_64/mt/smol-v.lib
CC=clang-cl.exe

main.exe: main.obj
	$(CC) main.obj $(FILAMENT_LIBS) gdi32.lib user32.lib opengl32.lib

main.obj: main.cpp
	$(CC) /MT /Iinclude/ /std:c++20 /c main.cpp

clean:
	del main.exe main.obj

.PHONY: clean
```

### `filamat_lite`

A smaller-sized alternative library, interchangeable with `filamat` but with caveats. It
has **no dependency on `glslang`**, but:

1. Material compilation is only supported for the **OpenGL** backend.
2. **No shader-level optimization** is performed.
3. **GLSL correctness is not checked.**

Additionally, `filamat_lite` does a **simple text match** to determine which
`MaterialInputs` properties are set, so the `material` input variable must **always be
referred to by the name `material`**:

```glsl
void anotherFunction(inout MaterialInputs m) {
    // Incorrect! The MaterialInputs is being referred to by the name "m".
    m.metallic = 0.0;
}

void aFunction(inout MaterialInputs material) {
    // Works, but only because the variable name "material" is used.
    material.reflectance = 0.5;
}

// The MaterialInputs variable must be named material.
void material(inout MaterialInputs material) {
    prepareMaterial(material);

    // Good.
    material.roughness = materialParams.roughness;
    material.baseColor.rgb = vec3(1.0, 0.0, 1.0);

    aFunction(material);
    anotherFunction(material);
}
```

## Handling Colors

Filament works in **linear** color space. Color inputs that arrive as sRGB must be
converted.

### Linear colors

- **From a texture:** use an **sRGB texture** so the hardware converts sRGB → linear
  automatically.
- **From a material parameter:** convert each color channel from sRGB to linear with the
  exact algorithm:

```glsl
float sRGB_to_linear(float color) {
	return color <= 0.04045 ? color / 12.92 : pow((color + 0.055) / 1.055, 2.4);
}
```

Cheaper, less accurate approximations:

```glsl
// Cheaper
linearColor = pow(color, 2.2);
// Cheapest
linearColor = color * color;
```

### Pre-multiplied alpha

A color uses pre-multiplied alpha when its RGB components are multiplied by the alpha
channel:

```glsl
// Compute pre-multiplied color
color.rgb *= color.a;
```

If the color is sampled from a texture, ensure the texture data is pre-multiplied ahead
of time. On Android, any texture uploaded from a `Bitmap` is pre-multiplied by default.
