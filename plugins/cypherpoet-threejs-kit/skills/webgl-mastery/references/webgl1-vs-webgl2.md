# WebGL1 vs WebGL2

A concise diff for the cases where you need to support both: legacy code, fallback paths, or running on an embedded WebView stuck on WebGL1.

WebGL2 ships in every modern browser (including Safari since 15). WebGL1 is still useful for very old browsers and some embedded contexts. New code should default to WebGL2 with a WebGL1 fallback only if you have a concrete reason to support it.

**Contents:** [Context Detection](#context-detection) · [Shader Source](#shader-source) · [Vertex Array Objects](#vertex-array-objects) · [Instancing](#instancing) · [NPOT Textures](#npot-textures) · [Features That Are WebGL2-Only](#features-that-are-webgl2-only) · [Recommended Strategy](#recommended-strategy) · [Common Mistakes](#common-mistakes)

## Context Detection

```javascript
const gl =
  canvas.getContext("webgl2") ||
  canvas.getContext("webgl") ||
  canvas.getContext("experimental-webgl");
const isWebGL2 = gl instanceof WebGL2RenderingContext;
```

Branch on `isWebGL2` for shader version selection, VAO API selection, and instancing path.

## Shader Source

| Concept | WebGL1 (GLSL ES 1.00) | WebGL2 (GLSL ES 3.00) |
|---------|-----------------------|------------------------|
| Version directive | implicit (no directive) | `#version 300 es` on line 1 |
| Vertex input | `attribute vec3 a_pos;` | `in vec3 a_pos;` |
| Varying (vert out) | `varying vec2 v_uv;` | `out vec2 v_uv;` |
| Varying (frag in) | `varying vec2 v_uv;` | `in vec2 v_uv;` |
| Fragment output | `gl_FragColor = …;` | declare `out vec4 outColor;` then assign |
| Texture sample | `texture2D(samp, uv)` | `texture(samp, uv)` |
| Cube sample | `textureCube(samp, dir)` | `texture(samp, dir)` |
| Integer types | not supported | `int`, `uint`, `ivec*`, `uvec*` |
| Integer texture samplers | not supported | `isampler2D`, `usampler2D` |
| Dynamic loops | restricted (constant bounds) | unrestricted |

A pattern for dual-version shaders: ship one source as a string, prepend `#version 300 es` and a polyfill block at upload time if WebGL2:

```javascript
const PREFIX_300 = `#version 300 es
#define attribute in
#define varying out          // only valid in vertex shader
out vec4 outColor;
#define gl_FragColor outColor
#define texture2D texture
`;

const source = isWebGL2 ? PREFIX_300 + originalGLSL1Source : originalGLSL1Source;
```

(Different prefix per shader stage, since `varying` becomes `out` in vertex and `in` in fragment.) This works for the simple cases. For real codebases with both versions, maintain separate shader files — the macro tricks get fragile fast.

## Vertex Array Objects

```javascript
let createVAO, bindVAO;
if (isWebGL2) {
  createVAO = () => gl.createVertexArray();
  bindVAO = (vao) => gl.bindVertexArray(vao);
} else {
  const ext = gl.getExtension("OES_vertex_array_object");
  if (!ext) throw new Error("VAOs not available");
  createVAO = () => ext.createVertexArrayOES();
  bindVAO = (vao) => ext.bindVertexArrayOES(vao);
}
```

`OES_vertex_array_object` is universally available on WebGL1 in practice — assume it's there, but check.

## Instancing

```javascript
let drawInstanced, attribDivisor;
if (isWebGL2) {
  drawInstanced = (mode, first, count, instances) =>
    gl.drawArraysInstanced(mode, first, count, instances);
  attribDivisor = (loc, divisor) => gl.vertexAttribDivisor(loc, divisor);
} else {
  const ext = gl.getExtension("ANGLE_instanced_arrays");
  if (!ext) throw new Error("Instancing not available");
  drawInstanced = (mode, first, count, instances) =>
    ext.drawArraysInstancedANGLE(mode, first, count, instances);
  attribDivisor = (loc, divisor) => ext.vertexAttribDivisorANGLE(loc, divisor);
}
```

## NPOT Textures

WebGL1 imposes restrictions on non-power-of-two textures: only `CLAMP_TO_EDGE` wrap, only non-mipmap filters, no `generateMipmap`. Hit any of those rules with an NPOT texture and it silently samples black.

WebGL2 has no such restrictions — NPOT textures work everywhere.

If you must support WebGL1 with NPOT sources, either:

- Resize to a power of two at upload time (`Math.pow(2, Math.ceil(Math.log2(size)))`), or
- Constrain to `CLAMP_TO_EDGE` + `LINEAR` / `NEAREST` and skip mipmaps.

## Features That Are WebGL2-Only

These have no WebGL1 equivalent (or only painful extension paths):

- **3D textures** (`TEXTURE_3D`).
- **Texture arrays** (`sampler2DArray`).
- **Multiple render targets (MRT)** without an extension.
- **Uniform buffer objects (UBOs)**.
- **Transform feedback** (capture vertex shader output back into a buffer).
- **Integer attributes and samplers**.
- **sRGB framebuffers**.
- **`textureLod` in fragment shader** (WebGL1 has it in vertex only).

If your code needs any of these, drop WebGL1 support — emulating them is more work than it's worth.

## Recommended Strategy

For a new project:

```javascript
const gl = canvas.getContext("webgl2");
if (!gl) {
  showFallbackUI("This page requires WebGL2 (any browser from 2020 or newer).");
  return;
}
```

WebGL2 has been the global baseline for years. The set of users on WebGL1-only browsers is small enough that a graceful "please update" message is the right call for almost every consumer-facing project.

For libraries or tools that need maximum reach, dual-pathing is the cost of admission — accept the complexity and structure your code so the differences are isolated in a small abstraction layer (a `gfx` module that exposes `createVAO`, `drawInstanced`, etc.).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| WebGL2 shader fails with "ERROR: 0:1: '#version' : invalid" | Whitespace or a comment before `#version 300 es`. The directive must be the very first thing. |
| Dual-version codebase: WebGL1 shader runs, WebGL2 same shader doesn't | You didn't add a `#version 300 es` and the `attribute`/`varying` keywords don't exist there. Use separate sources or a prefix macro pack. |
| WebGL1 NPOT texture samples solid black | NPOT restrictions. Set wrap to `CLAMP_TO_EDGE` and filter to `LINEAR`, or resize to POT. |
| `ext.drawArraysInstancedANGLE is not a function` | `getExtension` returned null. The extension exists almost everywhere, but always check and fail loudly. |
| Cube map sample missing in WebGL2 | Use `texture(samp, dir)` — the overloaded `texture()` handles all sampler types in GLSL ES 3.00. |
| Need MRT, project is on WebGL1 | `WEBGL_draw_buffers` extension exists but the support and ergonomics are weak. Upgrade to WebGL2. |
