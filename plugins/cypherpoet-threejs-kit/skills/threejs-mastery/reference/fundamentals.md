# Fundamentals

Cameras, Object3D, the scene graph, math utilities, and the building blocks every Three.js project leans on. Scene/renderer bootstrapping is covered once in [../SKILL.md#setup](../SKILL.md#setup); this file goes deeper on the parts the setup glosses over.

**Contents:** [Scene](#scene) · [Cameras](#cameras) · [Renderer Configuration](#renderer-configuration) · [Object3D](#object3d) · [Group](#group) · [Mesh](#mesh) · [Coordinate System](#coordinate-system) · [Math Utilities](#math-utilities) · [LoadingManager](#loadingmanager) · [LOD](#lod-level-of-detail) · [Merging Static Geometry](#merging-static-geometry) · [Common Mistakes](#common-mistakes)

## Scene

Top-level container for objects, lights, and cameras. Properties worth knowing:

```javascript
const scene = new THREE.Scene();

scene.background = new THREE.Color(0x000000);   // Solid color
scene.background = texture;                      // 2D texture (equirect)
scene.background = cubeTexture;                  // Cube map
scene.backgroundBlurriness = 0;                  // 0–1
scene.backgroundIntensity = 1;

scene.environment = envMap;                      // Drives PBR materials

scene.fog = new THREE.Fog(0xffffff, 1, 100);     // Linear fog
scene.fog = new THREE.FogExp2(0xffffff, 0.02);   // Exponential fog
```

## Cameras

### PerspectiveCamera

Most common. `fov` is vertical and in degrees. After mutating `fov`/`aspect`/`near`/`far`, call `updateProjectionMatrix()`.

```javascript
const camera = new THREE.PerspectiveCamera(
  75,                                            // fov (deg)
  window.innerWidth / window.innerHeight,        // aspect
  0.1,                                           // near
  1000                                           // far
);
camera.position.set(0, 5, 10);
camera.lookAt(0, 0, 0);
```

### OrthographicCamera

No perspective distortion — useful for 2D, isometric, or technical visualizations.

```javascript
const aspect = window.innerWidth / window.innerHeight;
const frustumSize = 10;
const camera = new THREE.OrthographicCamera(
  (frustumSize * aspect) / -2,
  (frustumSize * aspect) /  2,
   frustumSize / 2,
   frustumSize / -2,
   0.1,
   1000
);
```

### ArrayCamera

Renders multiple sub-cameras in one draw call. Good for split-screen or VR.

```javascript
const cameras = [];
for (let i = 0; i < 4; i++) {
  const sub = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  sub.viewport = new THREE.Vector4(
    (i % 2) * 0.5,
    Math.floor(i / 2) * 0.5,
    0.5,
    0.5
  );
  cameras.push(sub);
}
const arrayCamera = new THREE.ArrayCamera(cameras);
```

### CubeCamera

Renders the scene into a cube render target — useful for dynamic reflections. Updating it is expensive.

```javascript
const target = new THREE.WebGLCubeRenderTarget(256);
const cubeCamera = new THREE.CubeCamera(0.1, 1000, target);
scene.add(cubeCamera);

material.envMap = target.texture;

cubeCamera.position.copy(reflectiveMesh.position);
cubeCamera.update(renderer, scene);
```

## Renderer Configuration

`WebGPURenderer` (modern) and `WebGLRenderer` (compatibility) share most configuration. Differences are noted inline.

```javascript
const renderer = new THREE.WebGPURenderer({  // or WebGLRenderer
  canvas: document.querySelector("#canvas"),
  antialias: true,
  alpha: true,
  powerPreference: "high-performance",
  preserveDrawingBuffer: true,                   // For screenshots
});

renderer.setSize(width, height);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;

renderer.outputColorSpace = THREE.SRGBColorSpace;

renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

renderer.setClearColor(0x000000, 1);

await renderer.init();                           // WebGPURenderer only
renderer.render(scene, camera);
```

## Object3D

Base class of every node in the scene graph. `Mesh`, `Group`, `Light`, `Camera`, and `Bone` all extend it.

### Transforms

```javascript
obj.position.set(x, y, z);
obj.rotation.set(x, y, z);          // Euler angles, radians
obj.quaternion.set(x, y, z, w);
obj.scale.set(x, y, z);
```

`rotation` and `quaternion` stay in sync — setting one updates the other.

### Local vs World

`position`/`rotation`/`scale` are local (relative to parent). To get world values:

```javascript
obj.getWorldPosition(new THREE.Vector3());
obj.getWorldQuaternion(new THREE.Quaternion());
obj.getWorldDirection(new THREE.Vector3());
```

### Hierarchy

```javascript
parent.add(child);
parent.remove(child);

obj.parent;
obj.children;

obj.traverse((child) => {
  if (child.isMesh) child.material.color.set(0xff0000);
});
```

### Visibility and Layers

```javascript
obj.visible = false;

obj.layers.set(1);                  // Object is on layer 1 only
obj.layers.enable(2);
obj.layers.disable(0);
```

Cameras and raycasters honor their own layer masks — see [interaction.md](./interaction.md).

### Matrix Updates

Matrices auto-update each frame by default. For performance, you can opt out:

```javascript
obj.matrixAutoUpdate = false;

// Then update explicitly when transforms change
obj.updateMatrix();
obj.updateMatrixWorld(true);        // Recursive
```

## Group

Empty container for organizing objects. Transforming the group transforms its children.

```javascript
const group = new THREE.Group();
group.add(mesh1);
group.add(mesh2);
scene.add(group);

group.position.x = 5;
group.rotation.y = Math.PI / 4;
```

## Mesh

Pairs a geometry with a material (or array of materials, one per geometry group).

```javascript
const mesh = new THREE.Mesh(geometry, material);

mesh.castShadow = true;
mesh.receiveShadow = true;
mesh.frustumCulled = true;          // Default — skip if outside camera view
mesh.renderOrder = 10;              // Higher = drawn later (e.g., for transparency)
```

## Coordinate System

Right-handed: **+X** right, **+Y** up, **+Z** toward viewer.

```javascript
const axesHelper = new THREE.AxesHelper(5);
scene.add(axesHelper);              // Red=X, Green=Y, Blue=Z
```

## Math Utilities

### Vector3

```javascript
const v = new THREE.Vector3(x, y, z);
v.set(x, y, z);
v.copy(other);
v.clone();

// In-place ops
v.add(v2); v.sub(v2);
v.multiply(v2); v.multiplyScalar(2);
v.divideScalar(2);
v.normalize();
v.negate();
v.clamp(min, max);
v.lerp(target, alpha);

// Calculations
v.length(); v.lengthSq();           // lengthSq is faster
v.distanceTo(v2);
v.dot(v2);
v.cross(v2);                        // In-place
v.angleTo(v2);

// Transform
v.applyMatrix4(matrix);
v.applyQuaternion(q);
v.project(camera);                  // World → NDC
v.unproject(camera);                // NDC → world
```

### Matrix4

```javascript
const m = new THREE.Matrix4();
m.identity();
m.copy(other);

m.makeTranslation(x, y, z);
m.makeRotationX(theta);
m.makeRotationFromQuaternion(q);
m.makeScale(x, y, z);

m.compose(position, quaternion, scale);
m.decompose(position, quaternion, scale);

m.multiply(m2);                     // m = m * m2
m.premultiply(m2);                  // m = m2 * m
m.invert();
m.transpose();

m.makePerspective(left, right, top, bottom, near, far);
m.makeOrthographic(left, right, top, bottom, near, far);
m.lookAt(eye, target, up);
```

### Quaternion

```javascript
const q = new THREE.Quaternion();
q.setFromEuler(euler);
q.setFromAxisAngle(axis, angle);
q.setFromRotationMatrix(matrix);

q.multiply(q2);
q.slerp(target, t);                 // Spherical interpolation — use for rotation lerps
q.normalize();
q.invert();
```

### Euler

```javascript
const euler = new THREE.Euler(x, y, z, "XYZ");   // Order matters
euler.setFromQuaternion(q);
euler.setFromRotationMatrix(m);
// Valid orders: 'XYZ', 'YXZ', 'ZXY', 'XZY', 'YZX', 'ZYX'
```

### Color

```javascript
const color = new THREE.Color(0xff0000);
const color = new THREE.Color("red");
const color = new THREE.Color("#ff0000");

color.setHex(0x00ff00);
color.setRGB(r, g, b);              // 0–1
color.setHSL(h, s, l);

color.lerp(other, alpha);
color.multiplyScalar(2);
```

### MathUtils

```javascript
THREE.MathUtils.clamp(value, min, max);
THREE.MathUtils.lerp(start, end, alpha);
THREE.MathUtils.mapLinear(value, inMin, inMax, outMin, outMax);
THREE.MathUtils.degToRad(deg);
THREE.MathUtils.radToDeg(rad);
THREE.MathUtils.randFloat(min, max);
THREE.MathUtils.randInt(min, max);
THREE.MathUtils.smoothstep(x, min, max);
THREE.MathUtils.smootherstep(x, min, max);
```

## LoadingManager

Track or coordinate progress across multiple loaders.

```javascript
const manager = new THREE.LoadingManager();
manager.onStart    = (url, loaded, total) => console.log("started", url);
manager.onLoad     = () =>                   console.log("all loaded");
manager.onProgress = (url, loaded, total) => console.log(`${loaded}/${total}`);
manager.onError    = (url) =>                console.error("error", url);

const textureLoader = new THREE.TextureLoader(manager);
const gltfLoader    = new GLTFLoader(manager);
```

## LOD (Level of Detail)

Switch meshes by camera distance:

```javascript
const lod = new THREE.LOD();
lod.addLevel(highDetailMesh,   0);
lod.addLevel(medDetailMesh,   50);
lod.addLevel(lowDetailMesh,  100);
scene.add(lod);
```

## Merging Static Geometry

Combine multiple geometries into one to reduce draw calls. Only for static objects with the same material.

```javascript
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";

const merged = mergeGeometries([geo1, geo2, geo3]);
const mergedMesh = new THREE.Mesh(merged, material);
```

For lots of identical movable objects, prefer `InstancedMesh` ([geometry.md](./geometry.md#instancing)).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Camera changes (`fov`, `aspect`, `near`, `far`) don't take effect | Call `camera.updateProjectionMatrix()` after mutation. |
| Resize works visually but rendering is fuzzy | Also call `renderer.setSize(width, height)` and re-apply `setPixelRatio(window.devicePixelRatio)`. |
| `THREE.Geometry is not a constructor` | `Geometry` was removed years ago. Use `BufferGeometry` (see [geometry.md](./geometry.md)). |
| Stale world transforms when reading `getWorldPosition` immediately after setting `position` | Either call `obj.updateMatrixWorld(true)` first, or read on the next frame after the auto-update runs. |
| Setting `obj.matrixAutoUpdate = false` and forgetting `updateMatrix()` | Whenever you toggle off auto-update, every transform change must be followed by `obj.updateMatrix()` (and `updateMatrixWorld()` if anything reads world values). |
| Lerping rotations with `Euler.lerp`/`Vector3.lerp` and getting weird flips | Use `Quaternion.slerp` instead. Euler interpolation isn't well-defined. |
| Forgetting to add `light.target` to the scene for spot/directional lights | The target is its own `Object3D`; without `scene.add(light.target)` the light won't aim at it correctly when the target moves. |

## See Also

- [geometry.md](./geometry.md) — shapes, BufferGeometry, instancing.
- [materials.md](./materials.md) — PBR materials, TSL node materials.
- [lighting.md](./lighting.md) — light types, shadows, IBL.
- [interaction.md](./interaction.md) — raycasting and camera controls; uses `Object3D.layers`.
