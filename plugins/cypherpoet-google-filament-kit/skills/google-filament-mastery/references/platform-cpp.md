# Platform Setup: C++ (Desktop & iOS)

> Source: Filament repo README + BUILDING.md + iOS tutorial + C++ sample, Filament v1.72.0
> Last synced: 2026-06-19

Install/link/native-window/build glue only. The `Engine`/`Renderer`/`View`/`Scene`/`Camera` API
itself is covered in `engine-api-core` — this file stops at getting an `Engine` and a `SwapChain`
created from a native window.

## Contents

- [Supported platforms & backends](#supported-platforms--backends)
- [Toolchain prerequisites](#toolchain-prerequisites)
- [Getting the SDK: prebuilt vs build from source](#getting-the-sdk-prebuilt-vs-build-from-source)
  - [Prebuilt release binaries](#prebuilt-release-binaries)
  - [Build from source: build.sh (macOS/Linux)](#build-from-source-buildsh-macoslinux)
  - [Build from source: raw cmake + ninja](#build-from-source-raw-cmake--ninja)
  - [Filament-specific CMake options](#filament-specific-cmake-options)
  - [Per-OS build notes](#per-os-build-notes)
- [What you link against (libraries & include dirs)](#what-you-link-against-libraries--include-dirs)
- [Engine + SwapChain from a native window (desktop)](#engine--swapchain-from-a-native-window-desktop)
  - [The hellotriangle include set](#the-hellotriangle-include-set)
  - [The filamentapp / SDL helper vs. a real app](#the-filamentapp--sdl-helper-vs-a-real-app)
- [iOS specifics](#ios-specifics)
  - [CocoaPods install](#cocoapods-install)
  - [Objective-C++ + headers](#objective-c--headers)
  - [Engine with the Metal backend](#engine-with-the-metal-backend)
  - [SwapChain from a CAMetalLayer](#swapchain-from-a-cametallayer)
- [Compiled assets at build time (matc / cmgen / filamesh / resgen)](#compiled-assets-at-build-time-matc--cmgen--filamesh--resgen)

## Supported platforms & backends

Filament is a real-time physically based rendering engine for **Android, iOS, Linux, macOS, Windows,
and WASM**.

APIs: "Native C++ API for Android, iOS, Linux, macOS and Windows" (plus Java/JNI for Android and a
JavaScript API).

Backends (from the README):

- OpenGL 4.1+ for Linux, macOS and Windows
- OpenGL ES 3.0+ for Android and iOS
- Metal for macOS and iOS
- Vulkan 1.0 for Android, Linux, macOS, and Windows
- WebGPU for Android, Linux, macOS, and Windows
- WebGL 2.0 for all browsers supporting it

iOS support floor: "Filament is supported on iOS 11.0 and above." On iOS, Metal is preferred
(OpenGL ES also supported).

## Toolchain prerequisites

From BUILDING.md, to build Filament you must first install:

- **CMake 3.22.1 (or more recent)**
- **clang 17.0 (or more recent)** — required for Linux and macOS; Windows uses MSVC (see per-OS notes)
- **[ninja 1.10](https://github.com/ninja-build/ninja/wiki/Pre-built-Ninja-packages) (or more recent)**

These are the host-build prerequisites. If you only consume prebuilt release binaries (or the
CocoaPods pod on iOS) you do not need this toolchain to build the engine itself — but you still need
a C++ toolchain for your own app, and the matc/cmgen host tools from a release to prepare assets.

Android-only extras (not needed for desktop/iOS): Android Studio Flamingo+, Android SDK,
Android NDK 25.1+, Java 17.

## Getting the SDK: prebuilt vs build from source

### Prebuilt release binaries

> [Download Filament releases](https://github.com/google/filament/releases) to access stable builds.
> Filament release archives contains host-side tools that are required to generate assets.

Critical version-pinning rule from the README:

> Make sure you always use tools from the same release as the runtime library. This is particularly
> important for `matc` (material compiler).

iOS has a published CocoaPods release (see [iOS specifics](#ios-specifics)). Desktop C++ has no
package-manager install in these docs — you either unpack a release archive or build from source.

### Build from source: build.sh (macOS/Linux)

`build.sh` lives at the repo root and produces artifacts in the `out/` directory inside the source
tree. It can be invoked from anywhere.

```shell
./build.sh debug              # incremental debug build
./build.sh release            # incremental release build
./build.sh debug release      # both
```

Key flags:

- `-c` — force a clean build (use if a failed build left `out/` broken)
- `-i` — install libraries and executables into `out/debug/` and `out/release/`
- `-h` — full help / more features
- `-p ios` — build for iOS (e.g. `./build.sh -p ios debug`)
- `-p android`, `-q <abi>`, `-k <sample>` — Android targets
- `-p webgl` — WebAssembly (requires `EMSDK` set)
- `-E` — disable C++ exceptions (space saving for pure-native Android)
- `-d` (matdbg), `-t` (fgviewer), `-b`/`-y` (ASAN/UBSAN) — specialized builds

### Build from source: raw cmake + ninja

If you prefer running `cmake` directly (Linux/macOS pattern):

```shell
mkdir out/cmake-release
cd out/cmake-release
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../release/filament ../..
ninja
```

`ninja` builds Filament, its tests and samples, and the host tools. On Linux, if your distro
defaults to `gcc`, force clang + libc++:

```shell
mkdir out/cmake-release
cd out/cmake-release
# Or use a specific version of clang, for instance /usr/bin/clang-17
CC=/usr/bin/clang CXX=/usr/bin/clang++ CXXFLAGS=-stdlib=libc++ \
  cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../release/filament ../..
```

IDE: the maintainers recommend CLion — open the root `CMakeLists.txt` to get a usable project.

### Filament-specific CMake options

Boolean options (toggle with `cmake . -DOPTION=ON` inside the build dir):

- `FILAMENT_ENABLE_LTO` — link-time optimizations if the compiler supports them
- `FILAMENT_BUILD_FILAMAT` — build filamat and JNI bindings
- `FILAMENT_SUPPORTS_OPENGL` — include the OpenGL backend
- `FILAMENT_SUPPORTS_METAL` — include the Metal backend
- `FILAMENT_SUPPORTS_VULKAN` — include the Vulkan backend
- `FILAMENT_INSTALL_BACKEND_TEST` — install the backend test library so it can be consumed on iOS
- `FILAMENT_USE_EXTERNAL_GLES3` — experimental: compile against OpenGL ES 3
- `FILAMENT_SKIP_SAMPLES` — don't build sample apps
- `FILAMENT_ENABLE_EXCEPTIONS` — enable C++ exceptions (default: ON, OFF for iOS). Required for JNI bindings.
- `FILAMENT_ENABLE_RTTI` — enable C++ RTTI (default: OFF).

### Per-OS build notes

**macOS** — needs the most recent Xcode; ensure command-line tools are set up:

```shell
xcode-select --install
```

Default backend is Metal. To run Vulkan instead, install the LunarG SDK, enable "System Global
Components", and reboot. Then the standard cmake + ninja flow above applies.

**iOS** — easiest path is `build.sh -p ios`:

```shell
./build.sh -p ios debug
```

See `ios/samples/README.md` in the repo for more.

**Linux** — install dependencies first:

```shell
sudo apt install clang-17 libglu1-mesa-dev libc++-17-dev libc++abi-17-dev ninja-build libxi-dev libxcomposite-dev libxxf86vm-dev -y
```

(Fedora equivalents: `libcxx-devel`/`libcxx-static`, `libcxxabi-static`, `libXcomposite-devel`,
`libXxf86vm-devel`.) Then prefer the easy build script.

**Windows** — Visual Studio 2019 or later (no MSYS2 support). Install VS 2019+, the Windows SDK,
Python 3.7, and CMake (BUILDING.md links CMake 3.14 here, but the global prerequisite is 3.22.1+).
Keep the filesystem case-insensitive. Generate and build via a Native Tools prompt:

```bat
mkdir out
cd out
cmake ..
```

Open the generated `TNT.sln` in Visual Studio, or build a target headlessly:

```bat
cmake --build . --target gltf_viewer --config Release
```

## What you link against (libraries & include dirs)

Filament is split into the core engine plus supporting libraries (from the repo directory
structure). The core:

- `filament` — Filament rendering engine (minimal dependencies)
  - `filament/backend` — rendering backends/drivers (Vulkan, Metal, OpenGL/ES)

Supporting libraries under `libs/`:

| Library | Role |
| --- | --- |
| `bluegl` | OpenGL bindings for macOS, Linux and Windows |
| `bluevk` | Vulkan bindings for macOS, Linux, Windows and Android |
| `camutils` | Camera manipulation utilities |
| `filabridge` | Library shared by the Filament engine and host tools |
| `filaflat` | Serialization/deserialization library used for materials |
| `filagui` | Helper library for Dear ImGui |
| `filamat` | Material generation library (runtime material compiler) |
| `filamentapp` | SDL2 skeleton to build sample apps |
| `filameshio` | Tiny filamesh parsing library (see also `tools/filamesh`) |
| `geometry` | Mesh-related utilities |
| `gltfio` | Loader for glTF 2.0 |
| `ibl` | IBL generation tools |
| `image` | Image filtering and simple transforms |
| `matdbg` | DebugServer for inspecting shaders at run-time (debug builds only) |
| `math` | Math library |
| `utils` | Utility library (threads, memory, data structures, etc.) |
| `viewer` | glTF viewer library (requires gltfio) |

Which of these you actually link is driven by what your app uses. A minimal renderer pulls
`filament` (which depends on `backend`, `filabridge`, `filaflat`, `geometry`, `utils`, and the
backend-binding libs `bluegl`/`bluevk` for the GL/Vulkan backends). Add `filamat` if you compile
materials at runtime, `gltfio`/`viewer` for glTF loading, `ibl` for image-based-lighting
generation, `filamentapp` only for the SDL2 sample skeleton.

**Include dirs.** After an install (e.g. `cmake --install` / `build.sh -i` with prefix
`out/release/filament`), public headers land under that prefix's `include/`. App code includes by
component namespace directory — e.g. `<filament/Engine.h>`, `<filament/SwapChain.h>`,
`<utils/Entity.h>`, `<filamat/MaterialBuilder.h>` — so the install's `include/` is the include root.
(These exact include paths are shown in the sample and iOS tutorial; the docs don't enumerate the
full set of `-I` flags or static-lib filenames, so confirm against your release archive's `lib/` and
`include/` directories.)

## Engine + SwapChain from a native window (desktop)

The platform-specific glue is: create an `Engine`, then create a `SwapChain` from a **native window
pointer** passed as a `void*`. From the README ("Native Linux, macOS and Windows"):

```c++
Engine* engine = Engine::create();
SwapChain* swapChain = engine->createSwapChain(nativeWindow);
Renderer* renderer = engine->createRenderer();
```

> The `SwapChain` is created from a native window pointer (an `NSView` on macOS or a `HWND` on
> Windows for instance).

So a real app passes:

- **macOS** — an `NSView*` (or the layer, depending on backend) cast to `void*`
- **Windows** — an `HWND` cast to `void*`
- **Linux** — the native window handle from your windowing layer (X11/Wayland via SDL etc.) as `void*`

The API is platform-agnostic by design: `createSwapChain` takes a `void*`, and you cast your
platform's window/layer handle to it.

### The hellotriangle include set

The desktop C++ sample (`samples/hellotriangle.cpp`) uses this include set:

```c++
#include "common/arguments.h"

#include <filament/Camera.h>
#include <filament/Engine.h>
#include <filament/IndexBuffer.h>
#include <filament/Material.h>
#include <filament/MaterialInstance.h>
#include <filament/RenderableManager.h>
#include <filament/Scene.h>
#include <filament/Skybox.h>
#include <filament/TransformManager.h>
#include <filament/VertexBuffer.h>
#include <filament/View.h>

#include <utils/EntityManager.h>

#include <filamentapp/Config.h>
#include <filamentapp/FilamentApp.h>

#include <utils/getopt.h>

#include <cmath>
#include <iostream>
#include <string>// for printing usage/help

#include "generated/resources/resources.h"

using namespace filament;
using utils::Entity;
using utils::EntityManager;
```

Two install/build-relevant notes here:

- `#include <filamentapp/...>` pulls in the SDL2 sample skeleton — that's the helper, not the engine.
- `#include "generated/resources/resources.h"` is a **build-time generated** header (baked material
  blob); see the assets section below.

### The filamentapp / SDL helper vs. a real app

The sample never calls `Engine::create()` / `createSwapChain()` itself — it hands a `setup` and
`cleanup` lambda to `FilamentApp`:

```c++
auto setup = [&app](Engine* engine, View* view, Scene* scene) {
    // ... build skybox, vertex/index buffers, material, renderable, camera ...
};

FilamentApp::get().run(app.config, setup, cleanup);
```

From the README: the samples "are all based on `libs/filamentapp/` which contains the code that
creates a native window with SDL2 and initializes the Filament engine, renderer and views."

So `filamentapp` (SDL2) owns the native window, the `Engine::create()` call, and the
`createSwapChain(nativeWindow)` step. **A real (non-sample) app does that glue itself:** create your
own window with whatever toolkit (Cocoa/Win32/SDL/Qt/...), pull its native handle as a `void*`, and
call `engine->createSwapChain(thatHandle)` per the README's three-line snippet. Don't ship
`filamentapp` in production — it's a sample harness.

The material in the sample comes from the generated resource header, not a file load:

```c++
app.mat = Material::Builder()
        .package(RESOURCES_BAKEDCOLOR_DATA, RESOURCES_BAKEDCOLOR_SIZE)
        .build(*engine);
```

`RESOURCES_BAKEDCOLOR_DATA` / `RESOURCES_BAKEDCOLOR_SIZE` come from `generated/resources/resources.h`
(see assets section).

## iOS specifics

Source: the "CocoaPods Hello Triangle" tutorial (`ios.md`). CocoaPods install has been available
"as of release 1.8.0."

### CocoaPods install

README form:

```shell
pod 'Filament', '~> 1.72.0'
```

Full Podfile from the tutorial:

```ruby
platform :ios, '11.0'

target 'HelloCocoaPods' do
    pod 'Filament'
end
```

Then:

```shell
pod install
```

Close the project and re-open the generated `.xcworkspace` (not the `.xcodeproj`).

### Objective-C++ + headers

Filament exposes a C++ API, so any file including Filament headers must compile as a C++ variant —
the tutorial uses **Objective-C++** (`.mm`, file type "Objective-C++ Source"). Minimal header +
namespace:

```obj-c
#include <filament/Engine.h>

using namespace filament;
```

### Engine with the Metal backend

Select Metal explicitly at engine creation (Metal is strongly recommended over OpenGL ES on iOS):

```obj-c
_engine = Engine::create(Engine::Backend::METAL);
```

Expected log on a successful run:

```
FEngine (64 bits) created at 0x10ab94000 (threading is enabled)
FEngine resolved backend: Metal
```

Destroy in reverse order; the `Engine` is always destroyed last:

```obj-c
_engine->destroy(&_engine);
```

### SwapChain from a CAMetalLayer

On iOS+Metal the native window is a `CAMetalLayer`. The tutorial uses an `MTKView` (already backed
by a `CAMetalLayer`) and passes its `.layer` to `createSwapChain`, cast to `void*`:

```obj-c
#include <filament/SwapChain.h>
#import <MetalKit/MTKView.h>

// ...
MTKView* mtkView = (MTKView*) self.view;
mtkView.delegate = self;
_swapChain = _engine->createSwapChain((__bridge void*) mtkView.layer);
```

Note the `(__bridge void*)` cast — Filament's API is platform-agnostic, so the layer is handed over
as an opaque `void*`. (The README confirms the iOS contract: "A `CAEAGLLayer` or `CAMetalLayer` is
passed to the `createSwapChain` method.") Destroy the swap chain before the engine:

```obj-c
_engine->destroy(_swapChain);
_engine->destroy(&_engine);
```

You do not link Filament libraries by hand on iOS — the `Filament` pod provides the prebuilt
framework and headers; the include paths above resolve through the pod.

## Compiled assets at build time (matc / cmgen / filamesh / resgen)

Filament consumes pre-compiled binary assets, not raw source assets, at runtime. The relevant host
tools (under `tools/`) ship in every release archive:

- `matc` — material compiler (turns `.mat` → binary material package). **Version-match `matc` to
  your runtime release.** The README and iOS tutorial both recommend compiling materials offline
  with `matc` for production rather than at runtime.
- `cmgen` — image-based lighting / environment-map asset generator
- `filamesh` — mesh converter (FBX/OBJ → `.filamesh`)
- `resgen` — "Aggregates binary blobs into embeddable resources" (the source of generated
  `resources.h`-style headers)
- supporting: `mipgen`, `matinfo`, `matedit`, `glslminifier`, `normal-blending`,
  `roughness-prefilter`, `specular-color`

**Generated resource headers.** The desktop sample includes
`#include "generated/resources/resources.h"` and references `RESOURCES_BAKEDCOLOR_DATA` /
`RESOURCES_BAKEDCOLOR_SIZE`. These are produced at build time by `resgen` aggregating compiled
material blobs into a C header you `#include` and pass to `Material::Builder().package(...)`. That is
how compiled material/IBL/mesh data reaches the binary in the sample build.

**Runtime material compile (iOS tutorial, for reference).** The tutorial compiles a material at
runtime with the `filamat` library instead of `matc`, then loads it:

```obj-c
#include <filamat/MaterialBuilder.h>

filamat::MaterialBuilder::init();
filamat::Package pkg = filamat::MaterialBuilder()
    .name("Triangle material")
    .shading(filamat::MaterialBuilder::Shading::UNLIT)
    .require(VertexAttribute::COLOR)
    .material("void material (inout MaterialInputs material) {"
              "  prepareMaterial(material);"
              "  material.baseColor = getColor();"
              "}")
    .targetApi(filamat::MaterialBuilder::TargetApi::METAL)
    .platform(filamat::MaterialBuilder::Platform::MOBILE)
    .build();
assert(pkg.isValid());
filamat::MaterialBuilder::shutdown();

_material = Material::Builder()
    .package(pkg.getData(), pkg.getSize())
    .build(*_engine);
```

The tutorial explicitly notes this is for simplicity and recommends `matc` offline compilation for
production.

**Asset prep commands** (BUILDING.md, "Running the native samples") — run the tools from your build
dir:

```shell
filamesh ./assets/models/monkey/monkey.obj monkey.filamesh
cmgen -f ktx -x ./ibls/ my_ibl.exr
```

Starter assets ship in `third_party/textures` and `third_party/environments` (CC0). Environments
must be pre-processed with `cmgen` or the `libiblprefilter` library before use.
