# Textures and Framebuffers

## Loading a Texture from an Image

```javascript
function loadTexture(gl, url) {
  const texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, texture);

  // 1x1 placeholder so the texture is renderable before the image loads.
  gl.texImage2D(
    gl.TEXTURE_2D, 0, gl.RGBA,
    1, 1, 0,
    gl.RGBA, gl.UNSIGNED_BYTE,
    new Uint8Array([255, 0, 255, 255])   // magenta = "still loading"
  );

  const image = new Image();
  image.crossOrigin = "anonymous";       // Needed for textures from other origins.
  image.onload = () => {
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);   // Match shader UV convention.
    gl.texImage2D(
      gl.TEXTURE_2D, 0, gl.RGBA,
      gl.RGBA, gl.UNSIGNED_BYTE,
      image
    );
    gl.generateMipmap(gl.TEXTURE_2D);
  };
  image.src = url;
  return texture;
}
```

## Binding to a Sampler

```javascript
gl.activeTexture(gl.TEXTURE0);                  // Pick a texture unit.
gl.bindTexture(gl.TEXTURE_2D, texture);          // Bind the texture to that unit.

gl.uniform1i(u_textureSampler, 0);              // Tell the sampler uniform to read from unit 0.
```

The `uniform1i` takes the *unit index* (0, 1, 2…), not the texture object. Most code uses unit 0 for the main color texture and assigns others (1, 2…) for normal maps, masks, etc.

## Filtering and Wrap Modes

```javascript
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
```

| Setting | What it controls |
|---------|------------------|
| `MIN_FILTER` | How to sample when the texture is being *minified* (further away than 1:1). |
| `MAG_FILTER` | How to sample when *magnified* (closer than 1:1). Only `NEAREST` or `LINEAR`. |
| `WRAP_S/T` | What happens at UV `< 0` or `> 1`. `REPEAT`, `MIRRORED_REPEAT`, `CLAMP_TO_EDGE`. |

The most common mistake: setting `MIN_FILTER` to a `_MIPMAP_` variant without generating mipmaps. Either call `gl.generateMipmap(gl.TEXTURE_2D)` after upload, or set `MIN_FILTER` to plain `LINEAR` / `NEAREST` (no mipmap chain needed).

## NPOT (Non-Power-of-Two) Textures

In WebGL1, NPOT textures (e.g. 640×480) have severe restrictions: no `REPEAT` wrap mode, no mipmaps, only `LINEAR`/`NEAREST` filtering. Hit any of those and the texture silently samples black.

In WebGL2, **NPOT textures work normally** — full mipmap support, full wrap modes, full filtering. This is one of the bigger quality-of-life wins moving to WebGL2.

## Sampling in the Shader

```glsl
#version 300 es
precision highp float;

uniform sampler2D u_texture;
in vec2 v_uv;
out vec4 outColor;

void main() {
  outColor = texture(u_texture, v_uv);
}
```

GLSL ES 3.00 uses `texture(sampler, uv)` for all sampler types (it's overloaded). The WebGL1 names — `texture2D`, `textureCube` — are gone.

For LOD-explicit sampling: `textureLod(sampler, uv, mipLevel)`. For derivative-explicit (when you compute UVs procedurally in branchy code): `textureGrad`.

## Render-to-Texture: Framebuffer Objects

To render into a texture instead of the canvas, create a **framebuffer** with a texture attached:

```javascript
const fbTexture = gl.createTexture();
gl.bindTexture(gl.TEXTURE_2D, fbTexture);
gl.texImage2D(
  gl.TEXTURE_2D, 0, gl.RGBA,
  width, height, 0,
  gl.RGBA, gl.UNSIGNED_BYTE, null      // null = allocate, no upload
);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

const framebuffer = gl.createFramebuffer();
gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer);
gl.framebufferTexture2D(
  gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0,
  gl.TEXTURE_2D, fbTexture, 0
);

// Optional: attach a depth buffer if you need depth testing while rendering to texture.
const depth = gl.createRenderbuffer();
gl.bindRenderbuffer(gl.RENDERBUFFER, depth);
gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT16, width, height);
gl.framebufferRenderbuffer(
  gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT,
  gl.RENDERBUFFER, depth
);

// Always check completeness before drawing into it.
if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
  throw new Error("Framebuffer incomplete");
}

gl.bindFramebuffer(gl.FRAMEBUFFER, null);   // Unbind: subsequent draws go to canvas.
```

To render into it:

```javascript
gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer);
gl.viewport(0, 0, width, height);            // Match the FBO's dimensions, not the canvas.
gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
// ...draw...

gl.bindFramebuffer(gl.FRAMEBUFFER, null);
gl.viewport(0, 0, canvas.width, canvas.height);
// ...now draw something that samples `fbTexture`...
```

Two unforgettable gotchas:

- **Viewport doesn't track framebuffer size.** Set it explicitly after every `bindFramebuffer`.
- **A framebuffer can't read and write the same texture in one draw.** If you need to ping-pong (blur, simulation), allocate two FBOs and swap each pass.

## Ping-Pong for Multi-Pass Effects

```javascript
const passes = [createFBO(width, height), createFBO(width, height)];
let read = 0, write = 1;

for (let i = 0; i < numPasses; i++) {
  gl.bindFramebuffer(gl.FRAMEBUFFER, passes[write].fbo);
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, passes[read].texture);
  // ...draw the pass...
  [read, write] = [write, read];
}
// Final result is in passes[read].texture.
```

## Reading Pixels Back

```javascript
const pixels = new Uint8Array(width * height * 4);
gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
```

`readPixels` **stalls the entire pipeline** — the CPU waits for the GPU to finish everything queued. This is unavoidable; it's a fundamental sync point. If you call it every frame, your framerate craters. Use it for screenshots and one-off picking, not for continuous CPU↔GPU data flow.

For a faster (still slow) alternative in WebGL2, use pixel buffer objects (`PIXEL_PACK_BUFFER` + `getBufferSubData`) and stagger reads across frames.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Texture renders as solid black | `MIN_FILTER` is mipmapped but no mipmaps generated. Either `gl.generateMipmap` or set `MIN_FILTER` to `LINEAR`/`NEAREST`. |
| Texture renders as solid magenta (your placeholder) | Image hasn't loaded yet. `image.onload` runs async — bind/sample happens on first frame after load. |
| Image renders upside down | `gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true)` before `texImage2D`, or flip V in the shader. Pick one. |
| Image from another origin uploads as black | Set `image.crossOrigin = "anonymous"` *before* `image.src = ...`, and the server needs to send CORS headers. |
| FBO renders garbage / partial | Viewport wasn't reset to FBO dimensions after `bindFramebuffer`. |
| FBO renders solid color of the clear | Forgot to actually issue draw calls between `bindFramebuffer` and the next bind. Or the program/VAO got lost. |
| Sampler reads from wrong texture | `gl.uniform1i(samplerLoc, unitIndex)` was forgotten, or unit-0 had something else bound at draw time. |
| `readPixels` tanks framerate | It's a hard sync. Limit to user-triggered events. WebGL2 PBOs + `getBufferSubData` help in pipelines that need continuous readback. |
| WebGL1 texture from a 640×480 image silently black | NPOT restrictions: needs `CLAMP_TO_EDGE` wrap and non-mipmap filter, or upgrade to WebGL2. |
