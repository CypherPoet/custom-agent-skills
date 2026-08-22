# Performance

WebGL bottlenecks fall into three families: too many draw calls, too much GPU state churn, and CPU↔GPU sync stalls. Frame budget is ~16ms at 60fps; on mobile, often half that. Measure with the browser's performance profiler before you optimize — guesses are usually wrong.

## Table of Contents

| Section | Covers |
|---|---|
| [Instancing — One Draw, Many Copies](#instancing--one-draw-many-copies) | Per-instance attributes and matrices, divisor setup, native WebGL2 calls, and the WebGL1 extension equivalents |
| [Uniform Buffer Objects (UBOs)](#uniform-buffer-objects-ubos) | Shared cross-program uploads, binding points, partial updates, strict `std140` padding, and when reuse pays off |
| [Draw Call Batching](#draw-call-batching) | Static geometry merging and draw sorting by program, vertex state, and texture to reduce fixed CPU overhead |
| [State Change Minimization](#state-change-minimization) | JavaScript-side caching of programs and capabilities to skip redundant driver calls |
| [Avoid CPU↔GPU Sync Points](#avoid-cpugpu-sync-points) | Readback and query stalls, diagnostic-only finishing, and delayed pixel-buffer reads for continuous GPU results |
| [Buffer Update Strategies](#buffer-update-strategies) | Full versus sliced uploads, streaming hints, and allocation orphaning to avoid update stalls |
| [Texture Atlasing](#texture-atlasing) | Shared UV atlases and same-sized texture arrays that reduce sampler switches and atlas bleeding |
| [Mobile-Specific Pitfalls](#mobile-specific-pitfalls) | Tile flushes, upload timing, discard and early-Z, real mediump limits, and sustainable frame-rate targets |
| [Measuring](#measuring) | CPU profiling, GPU timer queries, captured draw state, and phase-level render-loop instrumentation |
| [Common Mistakes](#common-mistakes) | Excess draw calls, missing divisors, mobile FBO churn, synchronous readback, uncached programs, misaligned UBOs, guesswork, and thermal throttling |

## Instancing — One Draw, Many Copies

When you draw the same mesh N times with only per-instance variation (position, color, scale), use **instancing**: one draw call, N copies.

```javascript
// Per-instance attribute: a vec3 offset per instance.
const offsets = new Float32Array(numInstances * 3);
// ...fill offsets...

const offsetBuffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, offsetBuffer);
gl.bufferData(gl.ARRAY_BUFFER, offsets, gl.STATIC_DRAW);

gl.bindVertexArray(vao);
const aOffset = gl.getAttribLocation(program, "a_offset");
gl.enableVertexAttribArray(aOffset);
gl.vertexAttribPointer(aOffset, 3, gl.FLOAT, false, 0, 0);
gl.vertexAttribDivisor(aOffset, 1);     // 1 = "advance once per instance"

gl.drawArraysInstanced(gl.TRIANGLES, 0, vertexCount, numInstances);
```

```glsl
in vec3 a_position;
in vec3 a_offset;       // per-instance

void main() {
  gl_Position = u_viewProjection * vec4(a_position + a_offset, 1.0);
}
```

For per-instance matrices (full transforms, not just offsets), use 4 separate `vec4` attribute slots — `mat4` attributes are not directly supported as a single attribute. Pass each row as a `vec4`, then reassemble in the shader.

WebGL2 supports this natively. WebGL1 needs `ANGLE_instanced_arrays` and the methods are named `drawArraysInstancedANGLE` / `vertexAttribDivisorANGLE`.

Order of magnitude: 10,000 cubes via instancing is one fast draw call; 10,000 cubes via a loop with separate `drawArrays` calls will saturate the CPU.

## Uniform Buffer Objects (UBOs)

For uniforms shared across many programs — camera matrices, scene lighting — UBOs let you upload once and bind to multiple programs without re-uploading per program. WebGL2 only.

```javascript
const blockIndex = gl.getUniformBlockIndex(program, "Scene");
gl.uniformBlockBinding(program, blockIndex, 0);   // bind point 0

const ubo = gl.createBuffer();
gl.bindBuffer(gl.UNIFORM_BUFFER, ubo);
gl.bufferData(gl.UNIFORM_BUFFER, 256, gl.DYNAMIC_DRAW);  // size in bytes
gl.bindBufferBase(gl.UNIFORM_BUFFER, 0, ubo);

// To update:
gl.bindBuffer(gl.UNIFORM_BUFFER, ubo);
gl.bufferSubData(gl.UNIFORM_BUFFER, 0, new Float32Array([...]));
```

```glsl
layout(std140) uniform Scene {
  mat4 u_view;
  mat4 u_projection;
  vec3 u_cameraPos;
};
```

The `std140` layout has strict alignment rules — `vec3` is padded to `vec4` boundaries, `mat3` columns are padded to `vec4`. Get the layout wrong and the GPU reads garbage. Easiest mitigations: only use `mat4`, `vec4`, and `float` arrays in UBOs, padding by hand when needed.

UBOs pay off when many shaders share the same uniforms or when you're swapping uniforms frequently within a frame.

## Draw Call Batching

Each draw call has fixed CPU overhead (validation, state checks). Two ways to cut total calls:

1. **Combine geometry**: merge static meshes into a single VBO + IBO, draw the whole thing in one call. Particularly worth it for UI elements, tile maps, particles.
2. **Sort by state**: group draws by program, then by VAO, then by texture. Each state change (especially `useProgram` and `bindFramebuffer`) is expensive.

If your render loop looks like "for each object, useProgram, bindVAO, draw" — that's the fast path *if* you've sorted the objects to minimize program/VAO swaps.

## State Change Minimization

Track JS-side what's currently bound and skip redundant calls:

```javascript
let currentProgram = null;
function useProgramOnce(p) {
  if (currentProgram !== p) {
    gl.useProgram(p);
    currentProgram = p;
  }
}
```

WebGL drivers do some of this internally, but not all of them, not consistently. Cheap CPU-side caching is a real win on hot paths.

`gl.enable` / `gl.disable` for capabilities (depth test, blend, cull) are surprisingly slow on some drivers. Cache and skip.

## Avoid CPU↔GPU Sync Points

These functions stall the entire pipeline because the CPU has to wait for the GPU to finish:

- `gl.readPixels` — the big one. Forces a sync to read the rendered framebuffer.
- `gl.getError` — depending on driver, can force a sync.
- `gl.finish` — explicit sync. Never call this except for diagnostics.
- `gl.getParameter` of dynamic state — usually OK but avoid in hot loops.

If you need GPU output back on the CPU continuously (e.g., GPU physics → CPU readback), use WebGL2 pixel buffer objects with `getBufferSubData` and stagger reads across 2–3 frames so the GPU has time to finish naturally.

## Buffer Update Strategies

Updating a buffer every frame is fine — the driver double-buffers internally. But:

- **`bufferData(target, newData)`** replaces the entire allocation. Cheap if the size matches the previous call.
- **`bufferSubData(target, offset, data)`** updates a slice. Use for partial updates.
- **Orphaning trick**: `bufferData(target, null, gl.STREAM_DRAW)` followed by `bufferSubData` tells the driver "the old data is gone, allocate fresh" — can avoid a stall on some drivers.

For data that changes every frame (particles, dynamic meshes), `STREAM_DRAW` is the right hint.

## Texture Atlasing

Switching textures is a state change. For small textures (sprites, icons, glyphs), pack them into one large atlas and switch UV ranges instead of textures. Same idea as combining meshes — fewer state changes per frame.

WebGL2's `sampler2DArray` is the modern alternative: an array of same-sized textures bound to one sampler, indexed by a layer integer. Cleaner than atlases for tiling, doesn't suffer from bleeding at atlas edges.

## Mobile-Specific Pitfalls

- **Mobile GPUs are tile-based.** Switching framebuffers (especially mid-frame for ping-pong) flushes tiles to memory and is much more expensive than on desktop. Minimize FBO switches.
- **Texture uploads are slow.** Upload all textures during init when possible; avoid streaming during gameplay.
- **`discard` disables early-Z** on most mobile GPUs — costly. Use it only when truly needed (alpha-tested foliage), and render those passes last.
- **`mediump float` is genuinely 16-bit on some mobile GPUs.** Banding, precision artifacts in normalized coords. Stick to `highp` for anything spatial.
- **Aim for 30fps**, not 60. The thermal budget on phones is hard to sustain at 60fps for more than a few minutes.

## Measuring

Browser DevTools' performance tab shows the CPU work per frame — useful for catching JS-side bottlenecks. For GPU work, Chrome's `chrome://tracing` or the `EXT_disjoint_timer_query_webgl2` extension lets you time individual draw calls on the GPU.

[Spector.js](https://spector.babylonjs.com/) captures a frame and shows the state at every draw — useful for spotting redundant state changes, even if not strictly perf measurement.

The cheapest diagnostic: instrument the render loop with `performance.now()` around each phase (update, draw, post). If your frame time is 16ms and update takes 14ms, the GPU isn't your problem.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| "I'm only drawing 1,000 things and it's slow" | Almost certainly draw-call overhead. Move to instancing. |
| Instancing draws garbage | `vertexAttribDivisor` wasn't set on the per-instance attribute, or it's set on the wrong VAO. |
| FBO bounces tank mobile framerate | Tile-based GPUs flush on every framebuffer switch. Reduce passes or combine post-processing into one shader. |
| `readPixels` once per frame for "GPU physics" | Pure sync stall. Use PBOs + delayed readback, or do the physics CPU-side. |
| `useProgram` called in inner loop | State cache it. Sort draws by program. |
| UBO data reads as garbage | `std140` layout mismatch. Pad `vec3` to `vec4`, align `mat3` columns. Use `mat4` and `vec4` when in doubt. |
| Optimized "just in case" without measuring | Profile first. WebGL perf intuition is wrong as often as it's right. |
| Mobile build looks fine in dev, drops to 10fps in production | Thermal throttle. Lower target framerate, drop pixel ratio (`canvas.width = clientWidth`), or simplify shaders. |
