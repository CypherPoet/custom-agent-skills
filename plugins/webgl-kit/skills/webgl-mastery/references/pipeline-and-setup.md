# Pipeline and Setup

## Table of Contents

| Section | Covers |
|---|---|
| [The Mental Model](#the-mental-model) | Vertex processing, primitive assembly, rasterization, fragment shading and tests, plus the state mutations that precede a draw |
| [Creating the Context](#creating-the-context) | WebGL2 creation options, WebGL1 fallback detection, and capability routing for modern versus extension APIs |
| [HiDPI and Resize](#hidpi-and-resize) | CSS versus drawing-buffer dimensions, device-pixel-ratio scaling, synchronized viewport changes, and correct interpretation of requested canvas sizes |
| [State Machine Hygiene](#state-machine-hygiene) | Current program, VAO, buffers, texture units, framebuffer, viewport, and capability state with JavaScript-side caching over hot-loop queries |
| [Clearing](#clearing) | Color and depth initialization plus the limited cases where either clear can be omitted |
| [Context Loss](#context-loss) | Stopping work, preserving restoration, rebuilding every GPU resource, resuming animation, and testing forced loss |
| [Common Mistakes](#common-mistakes) | Blurry or partially rendered canvases, unnecessary preserved buffers, absent loss recovery, state-query stalls, and depth testing without an attachment |

## The Mental Model

WebGL is a **rasterization engine**, not a "3D engine." It runs two programs you write — a vertex shader and a fragment shader — and rasterizes triangles between them. Everything else is data plumbing.

A single draw call goes like this:

1. **Vertex shader** runs once per vertex. Input: per-vertex attributes (pulled from buffers via the currently bound VAO). Output: a clip-space position (`gl_Position`) plus any `out` varyings.
2. **Primitive assembly** groups the vertex outputs into points / lines / triangles.
3. **Rasterization** turns each triangle into a grid of candidate fragments. Per-vertex varyings get linearly interpolated across the triangle.
4. **Fragment shader** runs once per candidate fragment. Output: a color (and optionally depth) written to the bound framebuffer's color attachment.
5. **Per-fragment tests** (depth test, blend, stencil, scissor) decide whether the fragment actually lands.

Everything is configured by mutating the context's global state before the draw call. There is no immediate-mode equivalent of "draw this triangle right now" — you bind buffers and programs, then issue `gl.drawArrays` / `gl.drawElements`, and the pipeline runs.

## Creating the Context

```javascript
const canvas = document.querySelector("canvas");
const gl = canvas.getContext("webgl2", {
  antialias: true,
  alpha: true,            // false if you want an opaque canvas (slightly faster)
  premultipliedAlpha: true,
  preserveDrawingBuffer: false,  // true only if you need to `toDataURL()` later
  powerPreference: "high-performance",  // hints to use the discrete GPU on laptops
});
if (!gl) throw new Error("WebGL2 unavailable");
```

For a WebGL1 fallback chain:

```javascript
const gl =
  canvas.getContext("webgl2") ||
  canvas.getContext("webgl") ||
  canvas.getContext("experimental-webgl");
const isWebGL2 = gl instanceof WebGL2RenderingContext;
```

`isWebGL2` controls whether you can use VAOs, instancing, UBOs, and GLSL ES 3.00 directly versus needing extensions. See [webgl1-vs-webgl2.md](./webgl1-vs-webgl2.md).

## HiDPI and Resize

The canvas has two sizes: its **drawing buffer** (the pixel grid the GPU writes into — `canvas.width` / `canvas.height`) and its **CSS size** (`canvas.clientWidth` / `canvas.clientHeight`). They are not coupled. If you don't resize the drawing buffer to match the displayed size — and account for `devicePixelRatio` — the canvas looks blurry on retina screens.

```javascript
function resizeCanvasToDisplaySize(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const displayWidth  = Math.round(canvas.clientWidth  * dpr);
  const displayHeight = Math.round(canvas.clientHeight * dpr);
  const needResize = canvas.width !== displayWidth || canvas.height !== displayHeight;
  if (needResize) {
    canvas.width = displayWidth;
    canvas.height = displayHeight;
  }
  return needResize;
}

function render() {
  if (resizeCanvasToDisplaySize(gl.canvas)) {
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
  }
  // ...draw...
  requestAnimationFrame(render);
}
```

Three gotchas:

- **Viewport doesn't auto-track canvas size.** A resized canvas with a stale `gl.viewport` renders into a sub-rectangle of the new buffer (or off-screen entirely). Always update both together.
- **Don't put `gl.viewport` calls inside other state changes.** Issue once per resize, not per draw.
- **A "600x600 canvas" prompt is always the CSS size, not the drawing buffer.** When a user names a fixed pixel size, they're describing what they want to see on screen. Drive the *displayed* size with CSS (or matching HTML `width`/`height` attributes used as a CSS fallback), then let the resize helper above multiply by `devicePixelRatio` for the drawing buffer. Setting `canvas.width = 600` directly skips the DPR step and produces a blurry retina image — and it's a frequent misread of the prompt, because the named number looks like a drawing-buffer dimension. It isn't.

## State Machine Hygiene

WebGL has one current value for almost every kind of setting. Reading the state with `gl.getParameter(...)` is allowed but slow — never do it in a hot loop. Instead, track what you've bound on the JS side if state changes are a bottleneck (see [performance.md](./performance.md)).

The most-changed bindings:

| State | Set with | Notes |
|-------|----------|-------|
| Current program | `gl.useProgram(p)` | Uniforms write to *this* program. |
| Current VAO | `gl.bindVertexArray(vao)` | WebGL2 only. Captures all attribute pointer state. |
| Buffer per target | `gl.bindBuffer(target, b)` | `ARRAY_BUFFER`, `ELEMENT_ARRAY_BUFFER`, `UNIFORM_BUFFER`, etc. |
| Texture per unit | `gl.activeTexture(gl.TEXTURE0 + n); gl.bindTexture(target, t)` | Up to ~16+ units. |
| Current framebuffer | `gl.bindFramebuffer(target, fb)` | `null` means the default (canvas). |
| Viewport | `gl.viewport(x, y, w, h)` | In device pixels. |
| Capabilities | `gl.enable(cap)` / `gl.disable(cap)` | `DEPTH_TEST`, `BLEND`, `CULL_FACE`, `SCISSOR_TEST`. |

## Clearing

A frame typically starts with a clear:

```javascript
gl.clearColor(0, 0, 0, 1);
gl.clearDepth(1.0);
gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
```

Skip the depth clear if you have no depth buffer attached (and don't enable `DEPTH_TEST` without one). Skip the color clear if you're rendering a fullscreen pass that covers every pixel — pure micro-optimization, usually not worth it.

## Context Loss

The browser can drop your WebGL context at any time — GPU reset, tab backgrounded too long, driver crash, another tab grabbing the GPU. Real production code handles this:

```javascript
canvas.addEventListener("webglcontextlost", (e) => {
  e.preventDefault();          // Required, or `restored` will never fire.
  cancelAnimationFrame(rafId);
  // All gl resources (buffers, textures, programs) are now invalid.
  // Stop trying to use them.
});

canvas.addEventListener("webglcontextrestored", () => {
  // Recreate everything: programs, buffers, textures, framebuffers.
  initResources();
  rafId = requestAnimationFrame(render);
});
```

To test the code path without waiting for a crash, use the [`WEBGL_lose_context`](https://registry.khronos.org/webgl/extensions/WEBGL_lose_context/) extension: `gl.getExtension("WEBGL_lose_context").loseContext()`.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Canvas looks blurry on retina | `canvas.width = canvas.clientWidth * devicePixelRatio` in the resize handler, then update `gl.viewport`. |
| Drawing into a sub-rectangle after window resize | Viewport wasn't updated alongside `canvas.width/height`. Pair them. |
| Setting `preserveDrawingBuffer: true` "just in case" | It disables some browser optimizations. Only set when you actually call `canvas.toDataURL` / `toBlob` on the next frame. |
| Code works in dev, dies on mobile after the user backgrounds the tab | No context-loss handlers. Add `webglcontextlost` (with `preventDefault`) and `webglcontextrestored`. |
| `gl.getParameter` in the render loop | It stalls the pipeline. Cache state on the JS side; never query GL state per draw. |
| Enabled `DEPTH_TEST` with no depth buffer | The fallback canvas defaults to having a depth buffer; FBOs you create yourself don't unless you attach one. Symptom: depth test silently culls everything or nothing. |
