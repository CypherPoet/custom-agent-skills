# Animation

Three.js animation has three building blocks: `AnimationClip` (keyframe data), `AnimationMixer` (plays clips on a root object), and `AnimationAction` (a clip's playback state). Everything else — GLTF playback, blending, additive layers — composes on top of those. Animation is renderer-agnostic; the same code runs under `WebGPURenderer` and `WebGLRenderer`.

> Render loop and `delta`: see [../SKILL.md#setup](../SKILL.md#setup).

## Building an AnimationClip

```javascript
const times  = [0, 1, 2];               // Seconds
const values = [0, 1, 0];

const track = new THREE.NumberKeyframeTrack(".position[y]", times, values);
const clip  = new THREE.AnimationClip("bounce", 2, [track]);
```

### KeyframeTrack Types

```javascript
// NumberKeyframeTrack — single scalar (opacity, morph influence, etc.)
new THREE.NumberKeyframeTrack(".material.opacity", times, [1, 0]);

// VectorKeyframeTrack — 3-component (position, scale)
new THREE.VectorKeyframeTrack(".position", times, [
  0, 0, 0,
  1, 2, 0,
  0, 0, 0,
]);

// QuaternionKeyframeTrack — rotation
const q1 = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0));
const q2 = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI, 0));
new THREE.QuaternionKeyframeTrack(".quaternion", [0, 1], [
  q1.x, q1.y, q1.z, q1.w,
  q2.x, q2.y, q2.z, q2.w,
]);

// ColorKeyframeTrack
new THREE.ColorKeyframeTrack(".material.color", times, [
  1, 0, 0,
  0, 1, 0,
  0, 0, 1,
]);

// BooleanKeyframeTrack
new THREE.BooleanKeyframeTrack(".visible", [0, 0.5, 1], [true, false, true]);

// StringKeyframeTrack — primarily for morph targets
new THREE.StringKeyframeTrack(".morphTargetInfluences[smile]", [0, 1], ["0", "1"]);
```

### Interpolation Modes

```javascript
track.setInterpolation(THREE.InterpolateLinear);    // Default
track.setInterpolation(THREE.InterpolateSmooth);    // Cubic spline
track.setInterpolation(THREE.InterpolateDiscrete);  // Step
```

## AnimationMixer

A mixer plays animations on an `Object3D` and everything below it.

```javascript
const mixer = new THREE.AnimationMixer(model);
const action = mixer.clipAction(clip);
action.play();

// Drive the mixer every frame with the time delta — NOT wall-clock time
function animate() {
  const delta = clock.getDelta();
  mixer.update(delta);
  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);
```

### Mixer Events

```javascript
mixer.addEventListener("finished", (e) => {
  console.log("Animation finished:", e.action.getClip().name);
});

mixer.addEventListener("loop", (e) => {
  console.log("Animation looped:", e.action.getClip().name);
});
```

## AnimationAction

Controls how a clip plays through a mixer.

```javascript
const action = mixer.clipAction(clip);

// Playback control
action.play();
action.stop();
action.reset();
action.halt(fadeOutDuration);

// State
action.isRunning();
action.isScheduled();

// Time
action.time = 0.5;
action.timeScale = 1;                   // Negative = reverse
action.paused = false;

// Weight (for blending)
action.weight = 1;
action.setEffectiveWeight(1);

// Loop modes
action.loop = THREE.LoopRepeat;         // Default
action.loop = THREE.LoopOnce;
action.loop = THREE.LoopPingPong;
action.repetitions = 3;                 // Infinity by default
action.clampWhenFinished = true;        // Hold the last frame

// Blend mode
action.blendMode = THREE.NormalAnimationBlendMode;   // Default
action.blendMode = THREE.AdditiveAnimationBlendMode;
```

### Fade and Crossfade

```javascript
action.reset().fadeIn(0.5).play();
action.fadeOut(0.5);

// Crossfade between two actions (both must be playing)
action1.play();
action1.crossFadeTo(action2, 0.5, true);
action2.play();
```

## Loading GLTF Animations

GLTF/GLB is the most common source of skeletal animation.

```javascript
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const loader = new GLTFLoader();
loader.load("model.glb", (gltf) => {
  const model = gltf.scene;
  scene.add(model);

  const mixer = new THREE.AnimationMixer(model);
  const clips = gltf.animations;
  console.log("Available animations:", clips.map((c) => c.name));

  // Play first clip
  if (clips.length) mixer.clipAction(clips[0]).play();

  // Play a clip by name
  const walk = THREE.AnimationClip.findByName(clips, "Walk");
  if (walk) mixer.clipAction(walk).play();

  // Stash for the render loop
  window.mixer = mixer;
});

function animate() {
  const delta = clock.getDelta();
  window.mixer?.update(delta);
  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);
```

## Skeletal Animation

### Skeleton and Bones

```javascript
const skinnedMesh = model.getObjectByProperty("type", "SkinnedMesh");
const skeleton = skinnedMesh.skeleton;

skeleton.bones.forEach((bone) => {
  console.log(bone.name, bone.position, bone.rotation);
});

const head = skeleton.bones.find((b) => b.name === "Head");
if (head) head.rotation.y = Math.PI / 4;

scene.add(new THREE.SkeletonHelper(model));
```

### Programmatic Bone Animation

```javascript
function animate() {
  const time = clock.getElapsedTime();
  const head = skeleton.bones.find((b) => b.name === "Head");
  if (head) head.rotation.y = Math.sin(time) * 0.3;

  mixer.update(clock.getDelta());
}
```

### Attaching Objects to Bones

```javascript
const weapon = new THREE.Mesh(weaponGeometry, weaponMaterial);
const hand = skeleton.bones.find((b) => b.name === "RightHand");
hand?.add(weapon);

weapon.position.set(0, 0, 0.5);
weapon.rotation.set(0, Math.PI / 2, 0);
```

## Morph Targets

Morph targets blend between mesh shapes. They live on geometry (`geometry.morphAttributes`) and weights live on the mesh (`mesh.morphTargetInfluences`).

```javascript
console.log("Morph attributes:", Object.keys(mesh.geometry.morphAttributes));

mesh.morphTargetInfluences;        // Array of weights
mesh.morphTargetDictionary;        // Name → index

// Set by index
mesh.morphTargetInfluences[0] = 0.5;

// Set by name
const smile = mesh.morphTargetDictionary["smile"];
mesh.morphTargetInfluences[smile] = 1;
```

### Animating Morph Targets

```javascript
// Procedural
function animate() {
  const t = clock.getElapsedTime();
  mesh.morphTargetInfluences[0] = (Math.sin(t) + 1) / 2;
}

// Via clip
const track = new THREE.NumberKeyframeTrack(
  ".morphTargetInfluences[smile]",
  [0, 0.5, 1],
  [0, 1, 0]
);
mixer.clipAction(new THREE.AnimationClip("smile", 1, [track])).play();
```

## Animation Blending

Blend several clips by weight (e.g., idle ↔ walk ↔ run on a speed continuum):

```javascript
const idleAction = mixer.clipAction(idleClip);
const walkAction = mixer.clipAction(walkClip);
const runAction  = mixer.clipAction(runClip);

idleAction.play();
walkAction.play();
runAction.play();

idleAction.setEffectiveWeight(1);
walkAction.setEffectiveWeight(0);
runAction.setEffectiveWeight(0);

function updateAnimations(speed) {
  if (speed < 0.1) {
    idleAction.setEffectiveWeight(1);
    walkAction.setEffectiveWeight(0);
    runAction.setEffectiveWeight(0);
  } else if (speed < 5) {
    const t = speed / 5;
    idleAction.setEffectiveWeight(1 - t);
    walkAction.setEffectiveWeight(t);
    runAction.setEffectiveWeight(0);
  } else {
    const t = Math.min((speed - 5) / 5, 1);
    idleAction.setEffectiveWeight(0);
    walkAction.setEffectiveWeight(1 - t);
    runAction.setEffectiveWeight(t);
  }
}
```

### Additive Blending

Layer an extra motion (breathing, recoil) on top of a base pose:

```javascript
const baseAction = mixer.clipAction(baseClip);
baseAction.play();

const additive = mixer.clipAction(additiveClip);
additive.blendMode = THREE.AdditiveAnimationBlendMode;
additive.play();

// Convert a clip in-place to additive (relative to clip's first frame)
THREE.AnimationUtils.makeClipAdditive(additiveClip);
// Or relative to a different reference pose
THREE.AnimationUtils.makeClipAdditive(additiveClip, 0, referenceClip);
```

## Animation Utilities

```javascript
// Lookup
THREE.AnimationClip.findByName(clips, "Walk");

// Subclip
THREE.AnimationUtils.subclip(clip, "subclip", 0, 30, 30);

// Make additive
THREE.AnimationUtils.makeClipAdditive(clip);

// Clip operations
const clone = clip.clone();
clip.duration;
clip.optimize();                    // Remove redundant keyframes
clip.resetDuration();
```

## Procedural Patterns

When you don't need (or don't have) keyframe data, drive transforms in the loop directly.

### Smooth Damping

```javascript
const target = new THREE.Vector3();
const current = new THREE.Vector3();
const velocity = new THREE.Vector3();

function smoothDamp(current, target, velocity, smoothTime, deltaTime) {
  const omega = 2 / smoothTime;
  const x = omega * deltaTime;
  const exp = 1 / (1 + x + 0.48 * x * x + 0.235 * x * x * x);
  const change = current.clone().sub(target);
  const temp = velocity.clone()
    .add(change.clone().multiplyScalar(omega))
    .multiplyScalar(deltaTime);
  velocity.sub(temp.clone().multiplyScalar(omega)).multiplyScalar(exp);
  return target.clone().add(change.add(temp).multiplyScalar(exp));
}

function animate() {
  current.copy(smoothDamp(current, target, velocity, 0.3, delta));
  mesh.position.copy(current);
}
```

### Spring Physics

```javascript
class Spring {
  constructor(stiffness = 100, damping = 10) {
    this.stiffness = stiffness;
    this.damping = damping;
    this.position = 0;
    this.velocity = 0;
    this.target = 0;
  }

  update(dt) {
    const force = -this.stiffness * (this.position - this.target);
    const damp  = -this.damping   *  this.velocity;
    this.velocity += (force + damp) * dt;
    this.position += this.velocity * dt;
    return this.position;
  }
}

const spring = new Spring(100, 10);
spring.target = 1;
function animate() {
  mesh.position.y = spring.update(delta);
}
```

### Common Oscillations

```javascript
function animate() {
  const t = clock.getElapsedTime();

  mesh.position.y = Math.sin(t * 2) * 0.5;             // Sine
  mesh.position.y = Math.abs(Math.sin(t * 3)) * 2;     // Bouncing
  mesh.position.set(Math.cos(t) * 2, 0, Math.sin(t) * 2);  // Circle
  mesh.position.set(Math.sin(t) * 2, 0, Math.sin(t * 2));  // Figure 8
}
```

## Performance Tips

- **Share clips.** The same `AnimationClip` can be used by multiple mixers — clone is rarely needed.
- **`clip.optimize()`** removes redundant keyframes from imported clips.
- **Pause off-screen mixers.** A mixer behind the camera still costs CPU.
- **Use LOD for rigs.** Simpler skeletons for distant characters.
- **Cap active actions.** Every playing action with non-zero weight contributes to per-frame work.

```javascript
mesh.onBeforeRender = () => { action.paused = false; };
mesh.onAfterRender = () => {
  if (!isInFrustum(mesh)) action.paused = true;
};
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Animation doesn't play — model is stuck in T-pose | You forgot `mixer.update(delta)` in the render loop. Drive every mixer with the per-frame delta. |
| Animation speeds up/slows down with framerate | Passing wall-clock time (`elapsed`) instead of `delta` to `mixer.update()`. Use `clock.getDelta()`. |
| `crossFadeTo` does nothing | Both actions must be `play()`ing before the crossfade. The fade just retunes weights. |
| Imported animation drifts at the end | Set `action.clampWhenFinished = true` (and `action.loop = THREE.LoopOnce` for one-shot anims). |
| `LoopOnce` plays then snaps back to frame 0 | Same fix — `clampWhenFinished = true`. |
| Memory grows when swapping characters | Detach the mixer (`mixer.uncacheRoot(model)`), and dispose geometry/materials/textures via the model's `traverse`. |
| Programmatic bone rotations get overwritten | The mixer is also writing those bones. Apply procedural bone changes *after* `mixer.update()` in the same frame, or use additive clips for layered motion. |
| `findByName` returns `undefined` for a known-good clip | GLTF exporters sometimes rename clips (e.g., `Armature\|Walk`). Log `clips.map((c) => c.name)` to see the actual names. |

## See Also

- [loaders.md](./loaders.md) — loading GLTF/GLB and other animated formats.
- [fundamentals.md](./fundamentals.md) — `Clock` and the render loop.
- [shaders.md](./shaders.md) — vertex/material animation via TSL or GLSL.
