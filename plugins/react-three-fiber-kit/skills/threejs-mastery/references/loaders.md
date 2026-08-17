# Loaders

Loading models (GLTF/GLB primary, plus OBJ/FBX/STL/PLY), textures (`TextureLoader`, `CubeTextureLoader`, `KTX2Loader`), and HDR environments (`RGBELoader`, `EXRLoader`). Loaders are renderer-agnostic.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

## Table of Contents

| Section | Covers |
|---|---|
| [LoadingManager — Coordinate Progress](#loadingmanager--coordinate-progress) | Coordinating progress and ready state across multiple asset loaders |
| [TextureLoader](#textureloader) | Texture configuration (wrap, repeat, filtering, anisotropy) is covered in textures.md |
| [CubeTextureLoader](#cubetextureloader) | Loading six-face cube textures for backgrounds, environments, and material maps |
| [HDR / EXR Environments](#hdr--exr-environments) | PMREMGenerator — Prefilter for PBR |
| [GLTFLoader (Primary 3D Format)](#gltfloader-primary-3d-format) | Loading GLB/GLTF scenes and animations, enabling shadows, finding meshes, tuning materials, centering and normalizing models, and configuring Draco, Meshopt, and KTX2 decoders |
| [Other Model Formats](#other-model-formats) | OBJ and MTL, FBX, STL, and PLY loaders and their returned scene data |
| [Async / Promise Patterns](#async--promise-patterns) | Promisify Any Loader and Parallel Loads with Promise.all |
| [Cache](#cache) | Three.js has a global request cache shared across loaders that go through the file loader (most do) |
| [Asset Manager Pattern](#asset-manager-pattern) | For larger apps, a small cache layer pays off |
| [Loading From Other Sources](#loading-from-other-sources) | Data URL / Base64, Blob URL, ArrayBuffer / parse, and Base Paths and URL Rewriting |
| [Error Handling](#error-handling) | Fallback and retry patterns for asynchronous asset loading |
| [Performance Tips](#performance-tips) | Geometry and texture compression, caching, concurrency, and disposal |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## LoadingManager — Coordinate Progress

A single `LoadingManager` collects callbacks across multiple loaders so you can show progress and gate "ready" until everything is in.

```javascript
const manager = new THREE.LoadingManager();

manager.onStart = (url, loaded, total) => {
  console.log(`Started: ${url}`);
};
manager.onProgress = (url, loaded, total) => {
  updateProgressBar((loaded / total) * 100);
};
manager.onLoad = () => {
  startGame();
};
manager.onError = (url) => {
  console.error(`Error: ${url}`);
};

// Hand the manager to each loader you build
const textureLoader = new THREE.TextureLoader(manager);
const gltfLoader    = new GLTFLoader(manager);
```

## TextureLoader

```javascript
const loader = new THREE.TextureLoader();

// Callback style
loader.load(
  "texture.jpg",
  (texture) => {
    texture.colorSpace = THREE.SRGBColorSpace;     // For color/albedo maps
    material.map = texture;
    material.needsUpdate = true;
  },
  undefined,                                        // onProgress is not fired for images
  (error) => console.error(error)
);

// Implicit async — returns immediately, fills in once loaded
const texture = loader.load("texture.jpg");
material.map = texture;
```

Texture configuration (wrap, repeat, filtering, anisotropy) is covered in [textures.md](./textures.md).

## CubeTextureLoader

```javascript
const cubeTexture = new THREE.CubeTextureLoader().load([
  "px.jpg", "nx.jpg",
  "py.jpg", "ny.jpg",
  "pz.jpg", "nz.jpg",
]);

scene.background  = cubeTexture;
scene.environment = cubeTexture;
material.envMap   = cubeTexture;
```

## HDR / EXR Environments

```javascript
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
import { EXRLoader }  from "three/addons/loaders/EXRLoader.js";

new RGBELoader().load("environment.hdr", (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;
  scene.background  = texture;
});

new EXRLoader().load("environment.exr", (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;
});
```

### PMREMGenerator — Prefilter for PBR

Raw HDR equirects produce noisy reflections. `PMREMGenerator` builds a mipmap-prefiltered cube map:

```javascript
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";

const pmremGenerator = new THREE.PMREMGenerator(renderer);
pmremGenerator.compileEquirectangularShader();

new RGBELoader().load("environment.hdr", (texture) => {
  const envMap = pmremGenerator.fromEquirectangular(texture).texture;

  scene.environment = envMap;
  scene.background  = envMap;

  texture.dispose();
  pmremGenerator.dispose();
});
```

## GLTFLoader (Primary 3D Format)

GLB/GLTF is the recommended format for web 3D. The loader exposes the parsed scene, animations, cameras, and `userData`.

```javascript
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const loader = new GLTFLoader();

loader.load("model.glb", (gltf) => {
  const model = gltf.scene;
  scene.add(model);

  // Animations
  if (gltf.animations.length) {
    const mixer = new THREE.AnimationMixer(model);
    gltf.animations.forEach((clip) => mixer.clipAction(clip).play());
  }

  // Cameras authored in the scene (Blender, etc.)
  const cameras = gltf.cameras;

  // Provenance and custom data
  console.log(gltf.asset);       // version, generator, copyright, etc.
  console.log(gltf.userData);    // extras / custom properties
});
```

### Enable Shadows on a Loaded Model

GLTF doesn't carry shadow flags. Walk the scene and set them yourself:

```javascript
loader.load("model.glb", (gltf) => {
  gltf.scene.traverse((child) => {
    if (child.isMesh) {
      child.castShadow = true;
      child.receiveShadow = true;
    }
  });
  scene.add(gltf.scene);
});
```

### Find Specific Meshes

```javascript
const head = gltf.scene.getObjectByName("Head");

gltf.scene.traverse((child) => {
  if (child.isMesh && child.name.startsWith("Glass_")) {
    child.material.transmission = 1;
    child.material.thickness = 0.5;
  }
});
```

### Tune Environment Intensity / Material Tweaks

```javascript
gltf.scene.traverse((child) => {
  if (child.isMesh && child.material) {
    child.material.envMapIntensity = 0.5;
  }
});
```

### Center and Normalize Scale

```javascript
const box = new THREE.Box3().setFromObject(model);
const center = box.getCenter(new THREE.Vector3());
const size = box.getSize(new THREE.Vector3());

model.position.sub(center);
const maxDim = Math.max(size.x, size.y, size.z);
model.scale.setScalar(1 / maxDim);
```

### GLTF with Draco Compression

Draco compresses geometry. Decoder is loaded from a CDN or local copy:

```javascript
import { GLTFLoader }  from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://www.gstatic.com/draco/versioned/decoders/1.5.6/");
dracoLoader.preload();

const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);

gltfLoader.load("compressed-model.glb", (gltf) => {
  scene.add(gltf.scene);
});
```

### GLTF with Meshopt Compression

Meshopt is a more recent alternative to Draco that also compresses morph targets and animation data:

```javascript
import { GLTFLoader }    from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";

const loader = new GLTFLoader();
loader.setMeshoptDecoder(MeshoptDecoder);

loader.load("meshopt-model.glb", (gltf) => scene.add(gltf.scene));
```

### GLTF with KTX2 Textures

Use compressed textures inside the GLB:

```javascript
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { KTX2Loader } from "three/addons/loaders/KTX2Loader.js";

const ktx2Loader = new KTX2Loader();
ktx2Loader.setTranscoderPath(
  "https://cdn.jsdelivr.net/npm/three@0.185.1/examples/jsm/libs/basis/"
);
ktx2Loader.detectSupport(renderer);

const gltfLoader = new GLTFLoader();
gltfLoader.setKTX2Loader(ktx2Loader);

gltfLoader.load("model-with-ktx2.glb", (gltf) => scene.add(gltf.scene));
```

## Other Model Formats

### OBJ + MTL

```javascript
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { MTLLoader } from "three/addons/loaders/MTLLoader.js";

new MTLLoader().load("model.mtl", (materials) => {
  materials.preload();
  const objLoader = new OBJLoader();
  objLoader.setMaterials(materials);
  objLoader.load("model.obj", (object) => scene.add(object));
});
```

### FBX

Since r184, `FBXLoader` auto-converts +Z-up models to +Y-up — any manual axis rotation you applied on load can be removed. Scale often still needs correcting:

```javascript
import { FBXLoader } from "three/addons/loaders/FBXLoader.js";

new FBXLoader().load("model.fbx", (object) => {
  // FBX files often arrive at centimeter scale
  object.scale.setScalar(0.01);

  if (object.animations.length) {
    const mixer = new THREE.AnimationMixer(object);
    object.animations.forEach((clip) => mixer.clipAction(clip).play());
  }
  scene.add(object);
});
```

### STL

```javascript
import { STLLoader } from "three/addons/loaders/STLLoader.js";

new STLLoader().load("model.stl", (geometry) => {
  const mesh = new THREE.Mesh(
    geometry,
    new THREE.MeshStandardMaterial({ color: 0x888888 })
  );
  scene.add(mesh);
});
```

### PLY

```javascript
import { PLYLoader } from "three/addons/loaders/PLYLoader.js";

new PLYLoader().load("model.ply", (geometry) => {
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(
    geometry,
    new THREE.MeshStandardMaterial({ vertexColors: true })
  );
  scene.add(mesh);
});
```

## Async / Promise Patterns

### Promisify Any Loader

```javascript
function promisifyLoader(loader, url) {
  return new Promise((resolve, reject) => {
    loader.load(url, resolve, undefined, reject);
  });
}

const gltf = await promisifyLoader(new GLTFLoader(), "model.glb");
scene.add(gltf.scene);
```

### Parallel Loads with `Promise.all`

```javascript
async function loadAssets() {
  const [model, env, color] = await Promise.all([
    promisifyLoader(new GLTFLoader(), "model.glb"),
    new Promise((resolve, reject) =>
      new RGBELoader().load("environment.hdr", (t) => {
        t.mapping = THREE.EquirectangularReflectionMapping;
        resolve(t);
      }, undefined, reject)
    ),
    promisifyLoader(new THREE.TextureLoader(), "color.jpg"),
  ]);

  scene.add(model.scene);
  scene.environment = env;
  material.map = color;
}
```

## Cache

Three.js has a global request cache shared across loaders that go through the file loader (most do):

```javascript
THREE.Cache.enabled = true;            // Default false

THREE.Cache.clear();
THREE.Cache.add("key", data);
THREE.Cache.get("key");
THREE.Cache.remove("key");
```

## Asset Manager Pattern

For larger apps, a small cache layer pays off:

```javascript
class AssetManager {
  constructor() {
    this.textures = new Map();
    this.models = new Map();
    this.gltfLoader = new GLTFLoader();
    this.textureLoader = new THREE.TextureLoader();
  }

  async loadTexture(key, url) {
    if (this.textures.has(key)) return this.textures.get(key);
    const texture = await new Promise((res, rej) =>
      this.textureLoader.load(url, res, undefined, rej));
    this.textures.set(key, texture);
    return texture;
  }

  async loadModel(key, url) {
    if (this.models.has(key)) return this.models.get(key).clone();
    const gltf = await new Promise((res, rej) =>
      this.gltfLoader.load(url, res, undefined, rej));
    this.models.set(key, gltf.scene);
    return gltf.scene.clone();
  }

  dispose() {
    this.textures.forEach((t) => t.dispose());
    this.textures.clear();
    this.models.clear();
  }
}
```

## Loading From Other Sources

### Data URL / Base64

```javascript
const texture = new THREE.TextureLoader().load("data:image/png;base64,iVBORw...");
```

### Blob URL

```javascript
async function loadFromBlob(blob) {
  const url = URL.createObjectURL(blob);
  const texture = await promisifyLoader(new THREE.TextureLoader(), url);
  URL.revokeObjectURL(url);
  return texture;
}
```

### ArrayBuffer / `parse`

```javascript
const buffer = await (await fetch("model.glb")).arrayBuffer();
new GLTFLoader().parse(buffer, "", (gltf) => scene.add(gltf.scene));
```

### Base Paths and URL Rewriting

```javascript
loader.setPath("assets/models/");                 // model.glb → assets/models/model.glb
loader.setResourcePath("assets/textures/");       // For textures referenced inside

manager.setURLModifier((url) => `https://cdn.example.com/${url}`);
```

## Error Handling

```javascript
async function loadWithFallback(primary, fallback) {
  try {
    return await promisifyLoader(new GLTFLoader(), primary);
  } catch (err) {
    console.warn("primary failed, trying fallback", err);
    return promisifyLoader(new GLTFLoader(), fallback);
  }
}

async function loadWithRetry(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try { return await promisifyLoader(new GLTFLoader(), url); }
    catch (err) {
      if (i === maxRetries - 1) throw err;
      await new Promise((r) => setTimeout(r, 1000 * (i + 1)));
    }
  }
}
```

## Performance Tips

- **Compress what you ship.** Draco (or Meshopt) for geometry; KTX2/Basis for textures. Both are byte-on-disk wins *and* GPU wins (KTX2 stays compressed in VRAM).
- **Lazy-load.** Don't fetch what isn't on screen yet.
- **Use a CDN** for decoder paths and assets.
- **Enable `THREE.Cache.enabled = true`** before kicking off loads, especially if loading the same texture from multiple places.
- **Show a placeholder** while large assets load; swap in when ready.

```javascript
const placeholder = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshBasicMaterial({ wireframe: true })
);
scene.add(placeholder);

promisifyLoader(new GLTFLoader(), "model.glb").then((gltf) => {
  scene.remove(placeholder);
  scene.add(gltf.scene);
});
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Loaded GLTF model is unlit / casts no shadows | GLTF doesn't carry shadow flags. After loading, `traverse(child => { if (child.isMesh) { child.castShadow = true; child.receiveShadow = true; } })`. |
| `DRACOLoader` throws "decoder not loaded" or hangs | You forgot `dracoLoader.setDecoderPath(...)` and/or `preload()`. The path must match the Draco version on your CDN. |
| Large GLBs are slow to load | Add Draco or Meshopt compression on export; pair with KTX2/Basis textures. |
| Colors in a loaded GLTF still look washed out | `GLTFLoader` sets `colorSpace = SRGBColorSpace` on color maps automatically. If you swap in a `TextureLoader`-loaded image afterwards, you must set it manually. |
| Model centered but appears way off-camera | The pivot is at the origin of the original asset, not its bounding box. Use the center-and-normalize pattern above before adding to the scene. |
| Loaded animations don't play | You created a mixer but never call `mixer.update(delta)` each frame. See [animation.md](./animation.md). |
| FBX is "huge" or tiny | FBX often arrives at centimeter scale. `object.scale.setScalar(0.01)` is a common correction. |
| Same texture loads multiple times across the scene | Set `THREE.Cache.enabled = true` early, or use an `AssetManager` to dedupe. |

## See Also

- [textures.md](./textures.md) — texture configuration after loading.
- [animation.md](./animation.md) — playing GLTF animations.
- [materials.md](./materials.md) — adjusting materials on a loaded model.
- [lighting.md](./lighting.md) — using loaded HDR environments for IBL.
