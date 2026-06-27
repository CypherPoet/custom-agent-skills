# Geometry

Built-in shapes, custom `BufferGeometry`, instancing, and the math you need to build or modify meshes. Geometry is renderer-agnostic — the same code runs under `WebGPURenderer` and `WebGLRenderer`.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

**Contents:** [Built-in Geometries](#built-in-geometries) · [BufferGeometry](#buffergeometry) · [Edges & Wireframe](#edgesgeometry-and-wireframegeometry) · [Points](#points) · [Lines](#lines) · [Instancing](#instancing) · [Geometry Utilities](#geometry-utilities) · [Common Manipulations](#common-manipulations) · [Performance Tips](#performance-tips) · [Common Mistakes](#common-mistakes)

## Built-in Geometries

### Basic Shapes

```javascript
new THREE.BoxGeometry(1, 1, 1, 1, 1, 1);     // w, h, d + per-axis segments
new THREE.SphereGeometry(1, 32, 32);          // radius, widthSegs, heightSegs
new THREE.PlaneGeometry(10, 10, 1, 1);
new THREE.CircleGeometry(1, 32);
new THREE.CylinderGeometry(1, 1, 2, 32, 1, false);  // radiusTop, radiusBottom, height, ...
new THREE.CylinderGeometry(0, 1, 2, 32);            // Cone (top radius 0)
new THREE.ConeGeometry(1, 2, 32, 1, false);
new THREE.TorusGeometry(1, 0.4, 16, 100);
new THREE.TorusKnotGeometry(1, 0.4, 100, 16, 2, 3);
new THREE.RingGeometry(0.5, 1, 32, 1);

// Partial sphere via phi/theta start+length
new THREE.SphereGeometry(1, 32, 32, 0, Math.PI);    // Hemisphere
```

### Polyhedra and Capsule

```javascript
new THREE.CapsuleGeometry(0.5, 1, 4, 8);
new THREE.DodecahedronGeometry(1, 0);
new THREE.IcosahedronGeometry(1, 0);       // detail > 0 subdivides for smoother sphere
new THREE.OctahedronGeometry(1, 0);
new THREE.TetrahedronGeometry(1, 0);

new THREE.PolyhedronGeometry(vertices, indices, radius, detail);
```

### Path-Based Shapes

```javascript
// Lathe — rotate a 2D profile around the Y axis
const profile = [
  new THREE.Vector2(0, 0),
  new THREE.Vector2(0.5, 0),
  new THREE.Vector2(0.5, 1),
  new THREE.Vector2(0, 1),
];
new THREE.LatheGeometry(profile, 32);

// Extrude — extrude a 2D Shape into 3D
const shape = new THREE.Shape();
shape.moveTo(0, 0);
shape.lineTo(1, 0);
shape.lineTo(1, 1);
shape.lineTo(0, 1);
shape.lineTo(0, 0);

new THREE.ExtrudeGeometry(shape, {
  steps: 2,
  depth: 1,
  bevelEnabled: true,
  bevelThickness: 0.1,
  bevelSize: 0.1,
  bevelSegments: 3,
});

// Tube — sweep a circle along a 3D curve
const curve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(-1, 0, 0),
  new THREE.Vector3( 0, 1, 0),
  new THREE.Vector3( 1, 0, 0),
]);
new THREE.TubeGeometry(curve, 64, 0.2, 8, false);
```

### Text Geometry

`TextGeometry` and `FontLoader` live in addons:

```javascript
import { FontLoader }   from "three/addons/loaders/FontLoader.js";
import { TextGeometry } from "three/addons/geometries/TextGeometry.js";

new FontLoader().load("fonts/helvetiker_regular.typeface.json", (font) => {
  const geometry = new TextGeometry("Hello", {
    font,
    size: 1,
    depth: 0.2,             // 'height' in pre-r163 versions
    curveSegments: 12,
    bevelEnabled: true,
    bevelThickness: 0.03,
    bevelSize: 0.02,
    bevelSegments: 5,
  });

  geometry.computeBoundingBox();
  geometry.center();

  scene.add(new THREE.Mesh(geometry, material));
});
```

## BufferGeometry

The base class for every geometry. Stores attributes as typed arrays for GPU upload.

### Building From Scratch

```javascript
const geometry = new THREE.BufferGeometry();

// Positions — 3 floats per vertex
const vertices = new Float32Array([
  -1, -1, 0,    // v0
   1, -1, 0,    // v1
   1,  1, 0,    // v2
  -1,  1, 0,    // v3
]);
geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));

// Indices — reuse vertices to define triangles
const indices = new Uint16Array([
  0, 1, 2,
  0, 2, 3,
]);
geometry.setIndex(new THREE.BufferAttribute(indices, 1));

// Normals — required for lighting
const normals = new Float32Array([
  0, 0, 1,
  0, 0, 1,
  0, 0, 1,
  0, 0, 1,
]);
geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));

// UVs — for texturing
const uvs = new Float32Array([
  0, 0,
  1, 0,
  1, 1,
  0, 1,
]);
geometry.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));

// Per-vertex colors (set material.vertexColors = true)
const colors = new Float32Array([
  1, 0, 0,
  0, 1, 0,
  0, 0, 1,
  1, 1, 0,
]);
geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
```

### Attribute Reference

```javascript
new THREE.BufferAttribute(array, itemSize);

// Typed arrays
new Float32Array(count * itemSize);   // Positions, normals, UVs
new Uint16Array(count);               // Indices, up to 65,535 vertices
new Uint32Array(count);               // Indices, larger meshes
new Uint8Array(count * itemSize);     // Colors (0–255)

// Common itemSize values
// position: 3 (x, y, z)
// normal:   3
// uv:       2
// color:    3 (rgb) or 4 (rgba)
// index:    1
```

### Modifying Attributes

```javascript
const positions = geometry.attributes.position;

positions.setXYZ(index, x, y, z);
const x = positions.getX(index);

positions.needsUpdate = true;          // Flag for GPU re-upload

geometry.computeVertexNormals();       // Recompute normals after position changes
geometry.computeBoundingBox();
geometry.computeBoundingSphere();
```

### Interleaved Buffers

A denser memory layout for large meshes — all per-vertex attributes share one buffer:

```javascript
const interleavedBuffer = new THREE.InterleavedBuffer(
  new Float32Array([
    // pos.x pos.y pos.z uv.u uv.v   (5 floats per vertex)
    -1, -1, 0, 0, 0,
     1, -1, 0, 1, 0,
     1,  1, 0, 1, 1,
    -1,  1, 0, 0, 1,
  ]),
  5
);

geometry.setAttribute(
  "position",
  new THREE.InterleavedBufferAttribute(interleavedBuffer, 3, 0)
);
geometry.setAttribute(
  "uv",
  new THREE.InterleavedBufferAttribute(interleavedBuffer, 2, 3)
);
```

## EdgesGeometry and WireframeGeometry

```javascript
// Only edges that meet at angles above the threshold (degrees)
const edges = new THREE.EdgesGeometry(boxGeometry, 15);
const edgeMesh = new THREE.LineSegments(
  edges,
  new THREE.LineBasicMaterial({ color: 0xffffff })
);

// All triangle edges
const wireframe = new THREE.WireframeGeometry(boxGeometry);
const wireMesh = new THREE.LineSegments(
  wireframe,
  new THREE.LineBasicMaterial({ color: 0xffffff })
);
```

## Points

```javascript
const geometry = new THREE.BufferGeometry();
const positions = new Float32Array(1000 * 3);
for (let i = 0; i < 1000; i++) {
  positions[i * 3]     = (Math.random() - 0.5) * 10;
  positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
  positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
}
geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

const points = new THREE.Points(
  geometry,
  new THREE.PointsMaterial({ size: 0.1, sizeAttenuation: true, color: 0xffffff })
);
scene.add(points);
```

## Lines

```javascript
// Line — connected segments
const pts = [
  new THREE.Vector3(-1, 0, 0),
  new THREE.Vector3( 0, 1, 0),
  new THREE.Vector3( 1, 0, 0),
];
const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
const line = new THREE.Line(
  lineGeo,
  new THREE.LineBasicMaterial({ color: 0xff0000 })
);

// LineLoop — closes back to the first point
const loop = new THREE.LineLoop(lineGeo, material);

// LineSegments — pairs of vertices form individual segments
```

## Instancing

### InstancedMesh

The standard way to render many copies of the same geometry/material in one draw call.

```javascript
const count = 1000;
const instancedMesh = new THREE.InstancedMesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshStandardMaterial({ color: 0x00ff00 }),
  count
);

const dummy = new THREE.Object3D();
for (let i = 0; i < count; i++) {
  dummy.position.set(
    (Math.random() - 0.5) * 20,
    (Math.random() - 0.5) * 20,
    (Math.random() - 0.5) * 20
  );
  dummy.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
  dummy.scale.setScalar(0.5 + Math.random());
  dummy.updateMatrix();
  instancedMesh.setMatrixAt(i, dummy.matrix);
}
instancedMesh.instanceMatrix.needsUpdate = true;

// Optional per-instance color
instancedMesh.instanceColor = new THREE.InstancedBufferAttribute(
  new Float32Array(count * 3),
  3
);
for (let i = 0; i < count; i++) {
  instancedMesh.setColorAt(i, new THREE.Color(Math.random(), Math.random(), Math.random()));
}
instancedMesh.instanceColor.needsUpdate = true;

scene.add(instancedMesh);
```

### Updating an Instance

```javascript
const m = new THREE.Matrix4();
instancedMesh.getMatrixAt(index, m);
// mutate m...
instancedMesh.setMatrixAt(index, m);
instancedMesh.instanceMatrix.needsUpdate = true;
```

### Picking Instances

`Raycaster` reports `instanceId` on the intersection:

```javascript
const hits = raycaster.intersectObject(instancedMesh);
if (hits.length) {
  const id = hits[0].instanceId;
}
```

### InstancedBufferGeometry

For custom per-instance attributes beyond transform and color. Useful with custom shaders or TSL materials.

```javascript
const geometry = new THREE.InstancedBufferGeometry();
geometry.copy(new THREE.BoxGeometry(1, 1, 1));

const offsets = new Float32Array(count * 3);
for (let i = 0; i < count; i++) {
  offsets[i * 3]     = Math.random() * 10;
  offsets[i * 3 + 1] = Math.random() * 10;
  offsets[i * 3 + 2] = Math.random() * 10;
}
geometry.setAttribute(
  "offset",
  new THREE.InstancedBufferAttribute(offsets, 3)
);

// Read it in a shader / TSL node
// GLSL:   attribute vec3 offset;  vec3 p = position + offset;
// TSL:    attribute("offset")
```

## Geometry Utilities

```javascript
import * as BufferGeometryUtils from "three/addons/utils/BufferGeometryUtils.js";

// Merge geometries (same attribute set)
const merged = BufferGeometryUtils.mergeGeometries([geo1, geo2, geo3]);

// Merge with groups for multi-material rendering
const mergedGrouped = BufferGeometryUtils.mergeGeometries([geo1, geo2], true);

// Tangents — required for normal-mapped materials
BufferGeometryUtils.computeTangents(geometry);

// Combine attributes into one interleaved buffer
const interleaved = BufferGeometryUtils.interleaveAttributes([
  geometry.attributes.position,
  geometry.attributes.normal,
  geometry.attributes.uv,
]);
```

## Common Manipulations

```javascript
// Center on origin
geometry.computeBoundingBox();
geometry.center();

// Normalize to a unit bounding box
geometry.computeBoundingBox();
const size = new THREE.Vector3();
geometry.boundingBox.getSize(size);
const maxDim = Math.max(size.x, size.y, size.z);
geometry.scale(1 / maxDim, 1 / maxDim, 1 / maxDim);

// Clone and transform
const clone = geometry.clone();
clone.rotateX(Math.PI / 2);
clone.translate(0, 1, 0);
clone.scale(2, 2, 2);
```

### Morph Targets

```javascript
const geometry = new THREE.BoxGeometry(1, 1, 1, 4, 4, 4);

// Build a deformed copy of the base positions
const morphed = geometry.attributes.position.array.slice();
for (let i = 0; i < morphed.length; i += 3) {
  morphed[i]     *= 2;       // Stretch X
  morphed[i + 1] *= 0.5;     // Squash Y
}

geometry.morphAttributes.position = [
  new THREE.BufferAttribute(new Float32Array(morphed), 3),
];

const mesh = new THREE.Mesh(geometry, material);
mesh.morphTargetInfluences[0] = 0.5;
```

## Performance Tips

- **Pick segment counts intentionally.** `SphereGeometry(1, 16, 16)` is fine for far/small objects; reserve 32+ for hero objects, 64+ only for close-ups.
- **Index your geometry.** Indexed geometry reuses vertices, cutting both memory and shader work.
- **Merge static meshes** with `mergeGeometries` — cuts draw calls.
- **Instance for repetition.** Hundreds of identical objects → `InstancedMesh`. Thousands → `InstancedMesh` is essential.
- **Dispose when retiring geometry**: `geometry.dispose()`. Failing to do so leaks GPU memory.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Mutating `attributes.position.array` and the mesh doesn't change | Set `geometry.attributes.position.needsUpdate = true`. |
| Lighting looks wrong after editing vertices | Call `geometry.computeVertexNormals()`; raycasting and frustum culling may also need `computeBoundingBox()`/`computeBoundingSphere()`. |
| 1000+ identical objects tank framerate | Switch to `InstancedMesh`. One draw call instead of one per object. |
| Rendering with `Uint16Array` indices fails silently above 65,535 vertices | Use `Uint32Array` indices for large meshes. |
| Memory grows over time when swapping geometry | Call `oldGeometry.dispose()` before throwing away the reference. |
| Normal maps look wrong | Run `BufferGeometryUtils.computeTangents(geometry)` so the material has tangent data. |
| `TextGeometry`/`FontLoader` import fails | They live under `three/addons/geometries/` and `three/addons/loaders/`, not the top-level package. |
| `InstancedMesh` instances don't move after `setMatrixAt` | Set `instancedMesh.instanceMatrix.needsUpdate = true`. Same for `instanceColor`. |

## See Also

- [fundamentals.md](./fundamentals.md) — Object3D, transforms, math utilities.
- [materials.md](./materials.md) — material types and what attributes they expect.
- [shaders.md](./shaders.md) — using attributes and instancing in TSL or GLSL shaders.
