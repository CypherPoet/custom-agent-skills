# Lighting

Light types, shadows, and image-based environment lighting. The light classes themselves are renderer-agnostic — the code here works under both `WebGPURenderer` and `WebGLRenderer`.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

**Contents:** [Light Types](#light-types) · [Shadows](#shadows) · [Light Helpers](#light-helpers) · [Environment Lighting](#environment-lighting-ibl) · [Common Setups](#common-setups) · [Many Dynamic Lights](#many-dynamic-lights-webgpu) · [Performance Tips](#performance-tips) · [Common Mistakes](#common-mistakes)

## Light Types

| Light            | Description            | Shadow Support | Cost     |
| ---------------- | ---------------------- | -------------- | -------- |
| AmbientLight     | Uniform everywhere     | No             | Very Low |
| HemisphereLight  | Sky/ground gradient    | No             | Very Low |
| DirectionalLight | Parallel rays (sun)    | Yes            | Low      |
| PointLight       | Omnidirectional (bulb) | Yes            | Medium   |
| SpotLight        | Cone-shaped            | Yes            | Medium   |
| RectAreaLight    | Area light (window)    | No\*           | High     |

\*RectAreaLight shadows require custom solutions.

### AmbientLight

Illuminates all objects equally. No direction, no shadows.

```javascript
// AmbientLight(color, intensity)
const ambient = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambient);
```

### HemisphereLight

Gradient from sky to ground color. Good for outdoor scenes.

```javascript
// HemisphereLight(skyColor, groundColor, intensity)
const hemi = new THREE.HemisphereLight(0x87ceeb, 0x8b4513, 0.6);
hemi.position.set(0, 50, 0);
scene.add(hemi);
```

### DirectionalLight

Parallel rays. Simulates a distant source like the sun. Light points toward `light.target` (default origin).

```javascript
const dirLight = new THREE.DirectionalLight(0xffffff, 1);
dirLight.position.set(5, 10, 5);
dirLight.target.position.set(0, 0, 0);
scene.add(dirLight.target);
scene.add(dirLight);
```

### PointLight

Emits in all directions from a point. `distance = 0` is infinite range; physically-correct `decay` is 2.

```javascript
// PointLight(color, intensity, distance, decay)
const pointLight = new THREE.PointLight(0xffffff, 1, 100, 2);
pointLight.position.set(0, 5, 0);
scene.add(pointLight);
```

### SpotLight

Cone-shaped light. `angle` is in radians (max `Math.PI/2`); `penumbra` softens the edge (0–1).

```javascript
// SpotLight(color, intensity, distance, angle, penumbra, decay)
const spotLight = new THREE.SpotLight(0xffffff, 1, 100, Math.PI / 6, 0.5, 2);
spotLight.position.set(0, 10, 0);
spotLight.target.position.set(0, 0, 0);
scene.add(spotLight.target);
scene.add(spotLight);
```

### RectAreaLight

Rectangular area light — soft, realistic illumination. Only works with `MeshStandardMaterial` and `MeshPhysicalMaterial`, and only after initializing its uniforms.

```javascript
import { RectAreaLightHelper } from "three/addons/helpers/RectAreaLightHelper.js";
import { RectAreaLightUniformsLib } from "three/addons/lights/RectAreaLightUniformsLib.js";

RectAreaLightUniformsLib.init();

// RectAreaLight(color, intensity, width, height)
const rectLight = new THREE.RectAreaLight(0xffffff, 5, 4, 2);
rectLight.position.set(0, 5, 0);
rectLight.lookAt(0, 0, 0);
scene.add(rectLight);

const helper = new RectAreaLightHelper(rectLight);
rectLight.add(helper);
```

## Shadows

### Enabling Shadows

Three places to wire up:

```javascript
// 1. Renderer
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
// Other types: BasicShadowMap (fast/low), PCFShadowMap (default),
// PCFSoftShadowMap (soft edges), VSMShadowMap (variance)

// 2. Light
light.castShadow = true;

// 3. Each object that participates
mesh.castShadow = true;
mesh.receiveShadow = true;

// Floors typically receive but don't cast
floor.receiveShadow = true;
floor.castShadow = false;
```

### Tuning DirectionalLight Shadows

The shadow camera is orthographic — its frustum needs to tightly cover the area you actually want shadowed:

```javascript
dirLight.castShadow = true;

dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;

const d = 10;
dirLight.shadow.camera.left = -d;
dirLight.shadow.camera.right = d;
dirLight.shadow.camera.top = d;
dirLight.shadow.camera.bottom = -d;
dirLight.shadow.camera.near = 0.5;
dirLight.shadow.camera.far = 30;

dirLight.shadow.radius = 4;          // Blur radius (PCFSoftShadowMap only)
dirLight.shadow.bias = -0.0001;      // Fixes shadow acne
dirLight.shadow.normalBias = 0.02;   // Bias along surface normal

const helper = new THREE.CameraHelper(dirLight.shadow.camera);
scene.add(helper);
```

> **WebGPURenderer (r183+):** shadow quality improved, so these bias values can over-bias and cause peter-panning. Under WebGPU, start with `bias = 0` (and a small `normalBias`), then add bias only if acne actually appears.

### PointLight / SpotLight Shadows

`PointLight` uses six perspective shadow maps (cube). `SpotLight` uses one perspective camera with `fov` and `focus`.

```javascript
pointLight.castShadow = true;
pointLight.shadow.mapSize.width = 1024;
pointLight.shadow.mapSize.height = 1024;
pointLight.shadow.camera.near = 0.5;
pointLight.shadow.camera.far = 50;
pointLight.shadow.bias = -0.005;

spotLight.castShadow = true;
spotLight.shadow.mapSize.width = 1024;
spotLight.shadow.mapSize.height = 1024;
spotLight.shadow.camera.near = 0.5;
spotLight.shadow.camera.far = 50;
spotLight.shadow.camera.fov = 30;
spotLight.shadow.bias = -0.0001;
spotLight.shadow.focus = 1;
```

### Shadow Map Sizing

| Size | Use |
| ---- | --- |
| 512  | Low — distant or out-of-focus shadows |
| 1024 | Medium — most spotlights / pointlights |
| 2048 | High — main directional / sun |
| 4096 | Very high — expensive, rarely justified |

### Contact Shadows

Fast fake shadows for grounded objects. **Three.js core ships no `ContactShadows`
add-on** — that class belongs to drei (react-three-fiber). On plain Three.js, roll
your own: render the casters from directly overhead into a render target with an
overriding dark material, blur it, and map it onto a ground plane; or bake the blob
offline and use a `CanvasTexture`/image on a transparent plane. For the React stack,
use drei's `<ContactShadows>` via the sibling `react-three-fiber-mastery` skill.

## Light Helpers

```javascript
import { RectAreaLightHelper } from "three/addons/helpers/RectAreaLightHelper.js";

scene.add(new THREE.DirectionalLightHelper(dirLight, 5));
scene.add(new THREE.PointLightHelper(pointLight, 1));
scene.add(new THREE.SpotLightHelper(spotLight));
scene.add(new THREE.HemisphereLightHelper(hemiLight, 5));
rectLight.add(new RectAreaLightHelper(rectLight));

// When you move a light, call helper.update() to keep the gizmo in sync.
```

## Environment Lighting (IBL)

Image-Based Lighting uses an HDR environment map to drive PBR materials.

```javascript
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";

const rgbeLoader = new RGBELoader();
rgbeLoader.load("environment.hdr", (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;

  scene.environment = texture;       // PBR materials read this
  scene.background = texture;        // Optional: also as backdrop
  scene.backgroundBlurriness = 0;    // 0–1
  scene.backgroundIntensity = 1;
});
```

### PMREM for Sharp Reflections

Pre-filter the env map with `PMREMGenerator` for higher-quality reflections:

```javascript
const pmremGenerator = new THREE.PMREMGenerator(renderer);
pmremGenerator.compileEquirectangularShader();

rgbeLoader.load("environment.hdr", (texture) => {
  const envMap = pmremGenerator.fromEquirectangular(texture).texture;
  scene.environment = envMap;
  texture.dispose();
  pmremGenerator.dispose();
});
```

### Cube Texture Environments

```javascript
const cubeLoader = new THREE.CubeTextureLoader();
const envMap = cubeLoader.load([
  "px.jpg", "nx.jpg",
  "py.jpg", "ny.jpg",
  "pz.jpg", "nz.jpg",
]);

scene.environment = envMap;
scene.background = envMap;
```

### Light Probes

Capture lighting from a point in space:

```javascript
import { LightProbeGenerator } from "three/addons/lights/LightProbeGenerator.js";

const lightProbe = new THREE.LightProbe();
scene.add(lightProbe);
lightProbe.copy(LightProbeGenerator.fromCubeTexture(cubeTexture));
```

## Common Setups

### Three-Point Lighting

```javascript
const keyLight = new THREE.DirectionalLight(0xffffff, 1);
keyLight.position.set(5, 5, 5);

const fillLight = new THREE.DirectionalLight(0xffffff, 0.5);
fillLight.position.set(-5, 3, 5);

const backLight = new THREE.DirectionalLight(0xffffff, 0.3);
backLight.position.set(0, 5, -5);

const ambient = new THREE.AmbientLight(0x404040, 0.3);
scene.add(keyLight, fillLight, backLight, ambient);
```

### Outdoor Daylight

```javascript
const sun = new THREE.DirectionalLight(0xffffcc, 1.5);
sun.position.set(50, 100, 50);
sun.castShadow = true;

const hemi = new THREE.HemisphereLight(0x87ceeb, 0x8b4513, 0.6);

scene.add(sun, hemi);
```

### Indoor Studio

```javascript
RectAreaLightUniformsLib.init();

const light1 = new THREE.RectAreaLight(0xffffff, 5, 2, 2);
light1.position.set(3, 3, 3);
light1.lookAt(0, 0, 0);

const light2 = new THREE.RectAreaLight(0xffffff, 3, 2, 2);
light2.position.set(-3, 3, 3);
light2.lookAt(0, 0, 0);

scene.add(light1, light2, new THREE.AmbientLight(0x404040, 0.2));
```

## Many Dynamic Lights (WebGPU)

`WebGPURenderer` can pack lights into uniform arrays so adding or removing lights doesn't recompile affected materials — useful when the active light set changes at runtime. Opt in with `DynamicLighting` (r184):

```javascript
import { DynamicLighting } from "three/addons/lighting/DynamicLighting.js";

renderer.lighting = new DynamicLighting();
```

Without it, each change to the light set can trigger a shader recompile.

## Performance Tips

- **Limit light count.** Each light adds shader complexity. PBR materials with many lights re-evaluate per fragment.
- **Bake lighting** for static scenes (use lightmaps via the `lightMap` material slot).
- **Modest shadow map sizes.** 512–1024 is enough for most lights; reserve 2048+ for the primary sun/key light.
- **Tight shadow frustums.** Only cover the area that needs shadows. Loose frustums waste resolution and produce soft, low-contrast edges.
- **Disable shadows where unneeded.** Decor objects rarely need to cast.
- **Light layers** let you scope which meshes a light affects:

```javascript
light.layers.set(1);
mesh.layers.enable(1);
otherMesh.layers.disable(1);
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Per-light `castShadow = true` but no visible shadows | Set `renderer.shadowMap.enabled = true` once on the renderer; verify both casting meshes (`castShadow`) and receiving surfaces (`receiveShadow`). |
| Shadows look low-resolution or jagged | Shrink the shadow camera frustum so it tightly bounds shadow casters; bump `mapSize` only if that's not enough. |
| Shadow acne (stripes on lit surfaces) | Tune `shadow.bias` (small negative, e.g. `-0.0001`) and `shadow.normalBias` (~`0.02`). Under `WebGPURenderer` (r183+) shadows improved — try `bias = 0` first; the old values can over-bias. |
| Peter-panning (objects look detached from their shadows) | Reduce `normalBias`. The two biases trade off; tune both. |
| RectAreaLight has no effect | Call `RectAreaLightUniformsLib.init()` once at startup, and only use it with `MeshStandardMaterial`/`MeshPhysicalMaterial`. |
| HDR environment loaded but reflections look noisy | Run the HDR through `PMREMGenerator.fromEquirectangular()` before assigning to `scene.environment`. |
| Tonemapping looks wrong with HDR IBL | Set `renderer.toneMapping = THREE.ACESFilmicToneMapping` and `renderer.toneMappingExposure` to taste. |
| Moving a light but its helper stays put | Call `helper.update()` after moving the light. |

## See Also

- [materials.md](./materials.md) — how PBR materials respond to lights and environment.
- [textures.md](./textures.md) — lightmaps, environment maps, and HDR encoding.
- [postprocessing.md](./postprocessing.md) — bloom and other lighting-driven effects.
