# WebGPU Runtime

Two `WebGPURenderer`-specific runtime concerns that don't exist (or work differently) under WebGL: the GPU **device can be lost** mid-session, and its **limits are conservative by default**. A robust WebGPU app handles both.

These are WebGPU concerns. WebGL surfaces device trouble as a `webglcontextlost` DOM event on the canvas instead; the recovery *shape* below still applies, but the APIs differ.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

**Contents:** [Accessing the GPUDevice](#accessing-the-gpudevice) · [Device Loss](#device-loss) · [Requesting Limits and Features](#requesting-limits-and-features) · [Common Mistakes](#common-mistakes)

## Accessing the GPUDevice

The underlying `GPUDevice` lives on the renderer's backend:

```javascript
await renderer.init();
const device = renderer.backend.device;   // the GPUDevice
```

There is **no** `renderer.getDevice()`. Read `renderer.backend.device` only *after* `await renderer.init()` — the backend initializes lazily, so it's `null` before that.

## Device Loss

A GPU device can vanish at runtime: a driver crash or update, the OS reclaiming the GPU under memory pressure, a hung shader, or a background tab being evicted. When it happens, every GPU resource is gone and the canvas freezes unless you recover.

Three.js gives you a high-level hook — assign `renderer.onDeviceLost`:

```javascript
renderer.onDeviceLost = (info) => {
  // info = { api: "WebGPU", message, reason, originalEvent }
  if (info.reason === "destroyed") return;   // deliberate teardown — don't recover
  console.error(`WebGPU device lost: ${info.message}`);
  recover();
};
```

Or listen on the device's `lost` promise directly (the primitive three.js builds on). It stays pending for the device's lifetime and resolves with a `GPUDeviceLostInfo` carrying `reason` and `message`:

```javascript
const device = renderer.backend.device;
device.lost.then((info) => {
  if (info.reason !== "destroyed") recover();
});
```

**Recovery tiers**, cheapest to most seamless:

1. **Reload the page** — crude but reliable; fine for non-interactive scenes.
2. **Rebuild GPU state** — construct a fresh `WebGPURenderer`, re-`init()`, and recreate the GPU-owned resources (geometries, materials, textures, render targets, storage buffers). The scene graph and CPU state survive; only GPU handles need rebuilding.
3. **Rebuild and restore app state** — tier 2 plus restoring camera pose, simulation state, and user settings you snapshot as you go, so the user barely notices.

Never try to recover from `reason === "destroyed"` — that's a device you tore down on purpose (you called `.destroy()`, or the page is unloading).

## Requesting Limits and Features

WebGPU's default limits are deliberately conservative — e.g. `maxBufferSize` defaults to 256 MiB and `maxStorageBufferBindingSize` to 128 MiB. Large compute buffers or big textures can exceed them. Ask for more by passing `requiredLimits` (and `requiredFeatures`) to the renderer; the values flow through to `adapter.requestDevice()`:

```javascript
const renderer = new THREE.WebGPURenderer({
  requiredLimits: { maxStorageBufferBindingSize: 1 << 30 },  // request 1 GiB
});
await renderer.init();
```

`requestDevice()` **fails if the adapter can't grant what you ask for**, so check support first and clamp your request to what's available:

```javascript
const adapter = await navigator.gpu.requestAdapter();
const cap = adapter.limits.maxStorageBufferBindingSize;   // adapter's real ceiling
const want = Math.min(1 << 30, cap);
```

The same pattern applies to optional features (via `requiredFeatures`): query `adapter.features` before requesting, and degrade gracefully when a feature is absent.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `renderer.backend.device` is `null` | The backend initializes lazily. Read the device after `await renderer.init()`. |
| App white-screens after a GPU hiccup | Unhandled device loss. Register `renderer.onDeviceLost` (or `device.lost.then(...)`) and rebuild the renderer + GPU resources on an unexpected loss. |
| Treating every loss as fatal | `reason === "destroyed"` is a deliberate teardown — don't recover from it. Only recover when `reason` is something else. |
| `requestDevice` fails after setting `requiredLimits` | You asked for more than the adapter supports. Read `adapter.limits` first and clamp the request. |
| Assuming big buffers work everywhere | Defaults are low (`maxBufferSize` 256 MiB, `maxStorageBufferBindingSize` 128 MiB). Request explicitly and handle adapters that can't grant it. |

## See Also

- [compute.md](./compute.md) — large storage buffers are the usual reason to raise device limits.
- [../SKILL.md#setup](../SKILL.md#setup) — the baseline `WebGPURenderer` boot.
