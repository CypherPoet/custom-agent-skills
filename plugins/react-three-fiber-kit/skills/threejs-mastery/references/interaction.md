# Interaction

Raycasting, camera controls, pointer/touch input, drag/transform gizmos, selection systems, keyboard input, and screen↔world conversion. All renderer-agnostic.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

## Table of Contents

| Section | Covers |
|---|---|
| [Raycaster](#raycaster) | Basic picking, Raycaster APIs, full-window and canvas coordinates, touch picking, and lower-cost raycasting strategies |
| [Camera Controls](#camera-controls) | Orbit, Fly, FirstPerson, PointerLock, Trackball, Map, Transform, and Drag controls |
| [Selection Patterns](#selection-patterns) | Click to Select with Highlight, Hover Effects, and Box (Marquee) Selection |
| [Keyboard Input](#keyboard-input) | Track held keys in a map; read each frame |
| [Screen ↔ World Conversion](#screen--world-conversion) | World → Screen, Screen → World (at a target Z), and Ray → Plane Intersection |
| [Interaction Manager Pattern](#interaction-manager-pattern) | For larger apps, encapsulate event wiring |
| [Performance Tips](#performance-tips) | Raycast throttling, target filtering, layer masks, object reuse, and event delegation |
| [Common Mistakes](#common-mistakes) | Frequent mistakes and the changes that correct them |
| [See Also](#see-also) | Related references and supporting guidance |

## Raycaster

### Basic Picking

```javascript
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onClick(event) {
  // NDC (normalized device coordinates): each axis from -1 to +1
  mouse.x =  (event.clientX / window.innerWidth)  * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(scene.children, true);

  if (hits.length) console.log("clicked", hits[0].object);
}

window.addEventListener("click", onClick);
```

### Raycaster API

```javascript
// From camera (most common)
raycaster.setFromCamera(mouseNDC, camera);

// From explicit origin + direction
raycaster.set(origin, normalizedDirection);

// Intersections
raycaster.intersectObject(object, recursive);
raycaster.intersectObjects(objects, recursive);

// Each hit:
// {
//   distance, point, face, faceIndex, object,
//   uv, uv1, normal, instanceId   // instanceId on InstancedMesh hits
// }

// Filtering
raycaster.near = 0;
raycaster.far  = 100;
raycaster.params.Line.threshold   = 0.1;
raycaster.params.Points.threshold = 0.1;
raycaster.layers.set(1);              // Only objects on layer 1
```

### Mouse Coordinates: Full Window vs Canvas

Window-wide canvas:

```javascript
mouse.x =  (event.clientX / window.innerWidth)  * 2 - 1;
mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
```

Canvas embedded in a page (preferred when the canvas isn't full-screen):

```javascript
function updateMouseCanvas(event, canvas) {
  const rect = canvas.getBoundingClientRect();
  mouse.x =  ((event.clientX - rect.left) / rect.width)  * 2 - 1;
  mouse.y = -((event.clientY - rect.top)  / rect.height) * 2 + 1;
}
```

### Touch Picking

```javascript
function onTouchStart(event) {
  event.preventDefault();
  if (event.touches.length !== 1) return;

  const t = event.touches[0];
  mouse.x =  (t.clientX / window.innerWidth)  * 2 - 1;
  mouse.y = -(t.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(clickableObjects);
  if (hits.length) handleSelection(hits[0]);
}

renderer.domElement.addEventListener("touchstart", onTouchStart);
```

### Cheap Raycasting

```javascript
// Pass a tight list, not all of scene.children
const clickables = [mesh1, mesh2, mesh3];
const hits = raycaster.intersectObjects(clickables, false);

// Or use layers
mesh1.layers.set(1);
raycaster.layers.set(1);

// Throttle hover raycasts (mousemove fires every pixel)
let lastRaycast = 0;
function onMouseMove(event) {
  const now = performance.now();
  if (now - lastRaycast < 50) return;     // ~20 Hz
  lastRaycast = now;
  // ...raycast here
}

// Use a simpler invisible collision mesh for complex models
const collisionMesh = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshBasicMaterial({ visible: false })
);
collisionMesh.userData.target = complexMesh;
clickables.push(collisionMesh);
```

## Camera Controls

### OrbitControls

The standard orbit-around-a-target camera controller.

```javascript
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const controls = new OrbitControls(camera, renderer.domElement);

controls.enableDamping = true;
controls.dampingFactor = 0.05;

controls.minPolarAngle   = 0;
controls.maxPolarAngle   = Math.PI / 2;
controls.minAzimuthAngle = -Math.PI / 4;
controls.maxAzimuthAngle =  Math.PI / 4;

controls.minDistance = 2;
controls.maxDistance = 50;

controls.enableRotate = true;
controls.enableZoom   = true;
controls.enablePan    = true;

controls.autoRotate = true;
controls.autoRotateSpeed = 2.0;

controls.target.set(0, 1, 0);

// MUST be called every frame when damping or autoRotate is on
renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});
```

### FlyControls

```javascript
import { FlyControls } from "three/addons/controls/FlyControls.js";

const controls = new FlyControls(camera, renderer.domElement);
controls.movementSpeed = 10;
controls.rollSpeed = Math.PI / 24;
controls.dragToLook = true;

// Drive with delta — FlyControls accumulates motion per frame
renderer.setAnimationLoop(() => {
  timer.update();
  controls.update(timer.getDelta());
  renderer.render(scene, camera);
});
```

### FirstPersonControls

Redesigned in r184 with smoothing (`dampingFactor`) and built-in touch/mobile support.

```javascript
import { FirstPersonControls } from "three/addons/controls/FirstPersonControls.js";

const controls = new FirstPersonControls(camera, renderer.domElement);
controls.movementSpeed = 10;
controls.lookSpeed = 0.1;
controls.lookVertical = true;
controls.constrainVertical = true;
controls.verticalMin = Math.PI / 4;
controls.verticalMax = (Math.PI * 3) / 4;
controls.dampingFactor = 0.1;        // r184+ — smooths look/movement

// Needs the per-frame delta, like FlyControls
renderer.setAnimationLoop(() => {
  timer.update();
  controls.update(timer.getDelta());
  renderer.render(scene, camera);
});
```

### PointerLockControls

For FPS-style games.

```javascript
import { PointerLockControls } from "three/addons/controls/PointerLockControls.js";

const controls = new PointerLockControls(camera, document.body);

document.addEventListener("click", () => controls.lock());

controls.addEventListener("lock",   () => console.log("locked"));
controls.addEventListener("unlock", () => console.log("unlocked"));

const velocity  = new THREE.Vector3();
const direction = new THREE.Vector3();
let moveForward = false, moveBackward = false;

document.addEventListener("keydown", (e) => {
  if (e.code === "KeyW") moveForward = true;
  if (e.code === "KeyS") moveBackward = true;
});
document.addEventListener("keyup", (e) => {
  if (e.code === "KeyW") moveForward = false;
  if (e.code === "KeyS") moveBackward = false;
});

function update() {
  if (!controls.isLocked) return;
  direction.z = Number(moveForward) - Number(moveBackward);
  direction.normalize();
  velocity.z -= direction.z * 0.1;
  velocity.z *= 0.9;
  controls.moveForward(-velocity.z);
}
```

### TrackballControls

```javascript
import { TrackballControls } from "three/addons/controls/TrackballControls.js";

const controls = new TrackballControls(camera, renderer.domElement);
controls.rotateSpeed  = 2.0;
controls.zoomSpeed    = 1.2;
controls.panSpeed     = 0.8;
controls.staticMoving = true;
```

### MapControls

Top-down "map style" panning (good for orthographic or top-down 3D scenes).

```javascript
import { MapControls } from "three/addons/controls/MapControls.js";

const controls = new MapControls(camera, renderer.domElement);
controls.enableDamping     = true;
controls.dampingFactor     = 0.05;
controls.screenSpacePanning = false;
controls.maxPolarAngle     = Math.PI / 2;
```

### TransformControls (Gizmo)

```javascript
import { TransformControls } from "three/addons/controls/TransformControls.js";

const gizmo = new TransformControls(camera, renderer.domElement);
scene.add(gizmo.getHelper());   // TransformControls is not an Object3D — add its helper
gizmo.attach(selectedMesh);

gizmo.setMode("translate");        // 'translate' | 'rotate' | 'scale'
gizmo.setSpace("local");           // 'local' | 'world'
gizmo.setSize(1);

// Disable orbit controls while dragging the gizmo
gizmo.addEventListener("dragging-changed", (e) => {
  orbitControls.enabled = !e.value;
});

window.addEventListener("keydown", (e) => {
  if (e.key === "g") gizmo.setMode("translate");
  if (e.key === "r") gizmo.setMode("rotate");
  if (e.key === "s") gizmo.setMode("scale");
  if (e.key === "Escape") gizmo.detach();
});
```

### DragControls

Drag meshes directly with the mouse.

```javascript
import { DragControls } from "three/addons/controls/DragControls.js";

const draggables = [mesh1, mesh2, mesh3];
const drag = new DragControls(draggables, camera, renderer.domElement);

drag.addEventListener("dragstart", (e) => {
  orbitControls.enabled = false;
  e.object.material.emissive.set(0xaaaaaa);
});

drag.addEventListener("drag", (e) => {
  // Constrain to ground plane
  e.object.position.y = 0;
});

drag.addEventListener("dragend", (e) => {
  orbitControls.enabled = true;
  e.object.material.emissive.set(0x000000);
});
```

## Selection Patterns

### Click to Select with Highlight

```javascript
let selected = null;

function onClick(event) {
  updateMouseCanvas(event, renderer.domElement);
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(selectable);

  if (selected) selected.material.emissive.set(0x000000);

  if (hits.length) {
    selected = hits[0].object;
    selected.material.emissive.set(0x444444);
  } else {
    selected = null;
  }
}
```

### Hover Effects

```javascript
let hovered = null;

function onMouseMove(event) {
  updateMouseCanvas(event, renderer.domElement);
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(hoverable);

  if (hovered) {
    hovered.material.color.set(hovered.userData.originalColor);
    document.body.style.cursor = "default";
  }

  if (hits.length) {
    hovered = hits[0].object;
    hovered.userData.originalColor ??= hovered.material.color.getHex();
    hovered.material.color.set(0xff6600);
    document.body.style.cursor = "pointer";
  } else {
    hovered = null;
  }
}
```

### Box (Marquee) Selection

```javascript
import { SelectionBox }    from "three/addons/interactive/SelectionBox.js";
import { SelectionHelper } from "three/addons/interactive/SelectionHelper.js";

const selectionBox    = new SelectionBox(camera, scene);
const selectionHelper = new SelectionHelper(renderer, "selectBox");  // CSS class

document.addEventListener("pointerdown", (e) => {
  selectionBox.startPoint.set(
    (e.clientX / window.innerWidth)  * 2 - 1,
   -(e.clientY / window.innerHeight) * 2 + 1,
    0.5
  );
});

document.addEventListener("pointermove", (e) => {
  if (!selectionHelper.isDown) return;
  selectionBox.endPoint.set(
    (e.clientX / window.innerWidth)  * 2 - 1,
   -(e.clientY / window.innerHeight) * 2 + 1,
    0.5
  );
});

document.addEventListener("pointerup", (e) => {
  selectionBox.endPoint.set(
    (e.clientX / window.innerWidth)  * 2 - 1,
   -(e.clientY / window.innerHeight) * 2 + 1,
    0.5
  );
  const selected = selectionBox.select();
});
```

## Keyboard Input

Track held keys in a map; read each frame:

```javascript
const keys = {};
document.addEventListener("keydown", (e) => { keys[e.code] = true; });
document.addEventListener("keyup",   (e) => { keys[e.code] = false; });

function update() {
  const speed = 0.1;
  if (keys["KeyW"])     player.position.z -= speed;
  if (keys["KeyS"])     player.position.z += speed;
  if (keys["KeyA"])     player.position.x -= speed;
  if (keys["KeyD"])     player.position.x += speed;
  if (keys["Space"])    player.position.y += speed;
  if (keys["ShiftLeft"]) player.position.y -= speed;
}
```

## Screen ↔ World Conversion

### World → Screen

Pin HTML elements over 3D objects:

```javascript
function worldToScreen(position, camera) {
  const v = position.clone().project(camera);
  return {
    x:  ((v.x + 1) / 2) * window.innerWidth,
    y: (-(v.y - 1) / 2) * window.innerHeight,
  };
}

const p = worldToScreen(mesh.position, camera);
labelEl.style.left = `${p.x}px`;
labelEl.style.top  = `${p.y}px`;
```

### Screen → World (at a target Z)

```javascript
function screenToWorld(screenX, screenY, camera, targetZ = 0) {
  const v = new THREE.Vector3(
    (screenX / window.innerWidth)  * 2 - 1,
   -(screenY / window.innerHeight) * 2 + 1,
    0.5
  ).unproject(camera);

  const dir = v.sub(camera.position).normalize();
  const distance = (targetZ - camera.position.z) / dir.z;

  return camera.position.clone().add(dir.multiplyScalar(distance));
}
```

### Ray → Plane Intersection

Useful for "drop a marker on the ground":

```javascript
const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

function rayPlane(mouseNDC, camera, plane) {
  const r = new THREE.Raycaster();
  r.setFromCamera(mouseNDC, camera);
  const hit = new THREE.Vector3();
  r.ray.intersectPlane(plane, hit);
  return hit;
}
```

## Interaction Manager Pattern

For larger apps, encapsulate event wiring:

```javascript
class InteractionManager {
  constructor(camera, renderer, scene) {
    this.camera = camera;
    this.renderer = renderer;
    this.scene = scene;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.clickables = [];
    this.#bindEvents();
  }

  #bindEvents() {
    const c = this.renderer.domElement;
    c.addEventListener("click",      (e) => this.onClick(e));
    c.addEventListener("mousemove",  (e) => this.onMouseMove(e));
    c.addEventListener("touchstart", (e) => this.onTouchStart(e));
  }

  #updateMouse(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x =  ((event.clientX - rect.left) / rect.width)  * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top)  / rect.height) * 2 + 1;
  }

  #intersects() {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    return this.raycaster.intersectObjects(this.clickables, true);
  }

  onClick(event) {
    this.#updateMouse(event);
    const hits = this.#intersects();
    if (hits.length) hits[0].object.userData.onClick?.(hits[0]);
  }

  addClickable(object, callback) {
    this.clickables.push(object);
    object.userData.onClick = callback;
  }
}

const interaction = new InteractionManager(camera, renderer, scene);
interaction.addClickable(mesh, (hit) => console.log("clicked at", hit.point));
```

## Performance Tips

- **Throttle `mousemove` raycasts.** Pixel-rate updates blow your budget; ~20 Hz is plenty for hover.
- **Use layers.** A `raycaster.layers.set(N)` mask is cheaper than iterating a custom array.
- **Invisible simpler collision meshes** beat raycasting against high-poly models.
- **Toggle controls when not needed.** `controls.enabled = false` for cinematic cutscenes; re-enable after.
- **Pass a `false` second arg to `intersectObjects`** when you don't need recursion — saves traversal cost.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `OrbitControls` work but feel laggy or skippy | `enableDamping = true` requires `controls.update()` every frame. Add it to the render loop. |
| Mouse picks the wrong objects when the canvas is not full-screen | Use `getBoundingClientRect()` for NDC conversion; window dimensions only work if the canvas fills the window. |
| Raycaster hits nothing on `InstancedMesh` | It does work — the hit's `instanceId` tells you which instance was hit. Recurse into `InstancedMesh` and read `hits[0].instanceId`. |
| Hovering causes severe FPS drop | Raycaster is firing on every `mousemove`. Throttle to ~20 Hz, or use layer masks to shrink the candidate set. |
| `TransformControls` gizmo and `OrbitControls` fight | Wire `dragging-changed` on the gizmo to toggle `orbitControls.enabled`. |
| `PointerLockControls.lock()` fails silently | Browsers require pointer lock to start inside a user gesture (click/keydown). Call `.lock()` from inside that handler. |
| `FlyControls`/`FirstPersonControls` ignore input | They require `controls.update(delta)` each frame with the *delta* (seconds since last frame). |
| Touch picks don't fire | `event.preventDefault()` and pass the touch event through your same NDC math; `touchstart` doesn't bubble through `click`. |

## See Also

- [fundamentals.md](./fundamentals.md) — `Object3D.layers` (used by raycaster and cameras).
- [animation.md](./animation.md) — animating selection/hover responses.
- [shaders.md](./shaders.md) — outline / highlight shaders.
