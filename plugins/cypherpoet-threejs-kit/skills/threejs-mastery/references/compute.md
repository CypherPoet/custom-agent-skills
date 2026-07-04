# Compute Shaders

GPU compute in Three.js runs through TSL: you allocate storage buffers, write a compute function with `Fn()`, and dispatch it with the renderer. It's the tool for simulation and data-parallel work — particles, boids, cloth, physics, image processing — where the same code runs across thousands of elements on the GPU.

**Compute is `WebGPURenderer`-only.** WebGL has no compute path; feature-detect and branch (or skip the effect) when you fall back to `WebGLRenderer`.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

**Contents:** [Storage Buffers](#storage-buffers) · [Writing and Dispatching a Compute Node](#writing-and-dispatching-a-compute-node) · [Mutating Values Inside a Compute Node](#mutating-values-inside-a-compute-node) · [Worked Example: GPU Particles](#worked-example-gpu-particles) · [Common Mistakes](#common-mistakes)

## Storage Buffers

Compute reads and writes **storage buffers** — GPU-resident arrays the shader can mutate in place. Two constructors from `three/tsl` create them, both `(count, type = "float")`:

```javascript
import { instancedArray, attributeArray } from "three/tsl";

const positions = instancedArray(count, "vec3");   // per-instance storage
const scratch = attributeArray(count, "vec4");     // plain storage
```

- **`instancedArray`** backs the buffer with a `StorageInstancedBufferAttribute` — use it for per-instance data you also render (particles, instanced transforms).
- **`attributeArray`** backs it with a `StorageBufferAttribute` — a general scratch/working buffer.
- The `type` is the *element* type (`"float"`, `"vec2"`, `"vec3"`, `"vec4"`, a `Struct`), not the buffer's byte size. Get the element for the current invocation with `.element(index)`.

## Writing and Dispatching a Compute Node

A compute pass is an `Fn()` with no return value, turned into a compute node with `.compute(count)` and handed to the renderer:

```javascript
import { Fn, instanceIndex, vec3 } from "three/tsl";

const init = Fn(() => {
  positions.element(instanceIndex).assign(vec3(0));
})().compute(count);   // note the () — call the Fn, then .compute(count)

await renderer.init();              // the backend must exist before compute
await renderer.computeAsync(init);  // dispatch
```

- **`instanceIndex`** (from `three/tsl`) is the current invocation index — the compute equivalent of a loop counter. Use it to address `.element(instanceIndex)`.
- **`.compute(count)`** sets how many invocations to dispatch (optionally `.compute(count, workgroupSize)`; the default workgroup size is `[64]`).
- **`renderer.computeAsync(node)`** initializes the backend if needed and resolves when the dispatch is queued — use it for one-off passes. **`renderer.compute(node)`** is the synchronous form; it only works *after* `await renderer.init()` and is the right call inside the animation loop (no per-frame promise). Calling `compute()` before init warns and does nothing.

## Mutating Values Inside a Compute Node

The one rule that trips everyone: **mutation must flow through a shader node.** Inside `Fn()`/`If()`, reassigning a plain JavaScript `const`/`let` to a new node just rebinds the JS name — the shader graph never sees it. To mutate a value, wrap it with `.toVar()` and write through `.assign()` (or set a component directly):

```javascript
import { Fn, If, float } from "three/tsl";

const clampUp = Fn(() => {
  const v = someInput.toVar();     // a shader variable — assignable
  If(v.lessThan(0), () => {
    v.assign(0);                   // writes through the node
  });
  return v;
});
```

For a value-returning choice, use `select(condition, ifValue, elseValue)` — the TSL ternary. Unlike `If()`, it returns a value and works outside `Fn()`:

```javascript
import { select } from "three/tsl";

const limited = select(input.greaterThan(1), float(1), input);  // input > 1 ? 1 : input
```

## Worked Example: GPU Particles

Two passes: a one-time seed, then a per-frame update that integrates gravity. Everything mutable lives in storage buffers; the CPU only feeds the frame delta.

```javascript
import * as THREE from "three/webgpu";
import { Fn, instancedArray, instanceIndex, vec3, uniform } from "three/tsl";

const count = 100_000;
const positions = instancedArray(count, "vec3");
const velocities = instancedArray(count, "vec3");

// Seed: all at the origin, moving up. In practice, vary these per instanceIndex.
const seed = Fn(() => {
  positions.element(instanceIndex).assign(vec3(0));
  velocities.element(instanceIndex).assign(vec3(0, 10, 0));
})().compute(count);

await renderer.init();
await renderer.computeAsync(seed);

// Per-frame integration.
const uDelta = uniform(0);
const gravity = vec3(0, -9.8, 0);

const update = Fn(() => {
  const pos = positions.element(instanceIndex);
  const vel = velocities.element(instanceIndex);
  vel.assign(vel.add(gravity.mul(uDelta)));
  pos.assign(pos.add(vel.mul(uDelta)));
})().compute(count);

const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  uDelta.value = clock.getDelta();
  renderer.compute(update);   // sync dispatch, cheap per frame once initialized
  renderer.render(scene, camera);
});
```

To draw the result, bind the position buffer to a node material's `positionNode` — e.g. a `Points` whose geometry has `count` vertices, with `material.positionNode = positions.element(instanceIndex)`. The vertex stage then reads each particle's computed position straight from GPU memory, with no CPU round-trip.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `renderer.compute()` warns or does nothing | The backend isn't initialized. `await renderer.init()` first, or use `renderer.computeAsync()` (it initializes for you). |
| Reassigning a JS `const`/`let` inside `Fn()` has no effect | The shader graph only tracks node mutations. Wrap the value in `.toVar()` and write via `.assign()` (or set a component like `pos.y = 0`); rebinding the JS name just points it at a new node. |
| Compute silently missing under `WebGLRenderer` | There is no WebGL compute path — compute requires `WebGPURenderer`. Feature-detect and branch. |
| Buffer element type mismatch | Pass the element type to `instancedArray(count, "vec3")`; `.element(i)` returns that type. A wrong type corrupts strides silently. |
| Large particle counts fail to allocate | Big buffers can exceed `maxStorageBufferBindingSize` (default 128 MiB). Request a higher limit — see [webgpu-runtime.md](./webgpu-runtime.md). |

## See Also

- [shaders.md](./shaders.md) — TSL fundamentals (`Fn`, nodes, `select`, `toVar`) the compute API builds on.
- [webgpu-runtime.md](./webgpu-runtime.md) — raising the device limits that large compute buffers need.
- [geometry.md](./geometry.md) — instancing (`InstancedMesh`) for rendering compute-driven transforms.
