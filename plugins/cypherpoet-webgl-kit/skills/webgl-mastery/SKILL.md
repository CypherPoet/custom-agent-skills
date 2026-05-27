---
name: webgl-mastery
description: >
  Use whenever the user is working with raw WebGL or GLSL — writing,
  debugging, optimizing, or asking about WebGL2 (or WebGL1) without a
  higher-level framework. Trigger on `WebGLRenderingContext`,
  `WebGL2RenderingContext`, `getContext('webgl'|'webgl2')`, vertex/fragment
  shaders, `gl_FragColor`, `gl_Position`, `vec2`/`vec3`/`vec4`, `uniform`,
  `attribute`, `varying`, `in`/`out` in shader code, `gl.createBuffer`,
  `gl.vertexAttribPointer`, VBOs/VAOs/UBOs, FBOs/framebuffers, `texImage2D`,
  `drawArrays`/`drawElements`, instancing, GLSL noise/SDF/smoothstep
  patterns, "black canvas" debugging, `getShaderInfoLog`, shader compile
  errors, or any mention of WebGL pipeline mechanics. Load this even when
  the user doesn't say "WebGL" explicitly — if the code or question is
  about shaders, GPU rasterization, or the browser graphics pipeline
  beneath a framework, this is the right skill. For app-level 3D
  (Three.js scene graph, loaders, post-processing), defer to
  `threejs-mastery` instead.
---

# WebGL Fundamentals

## Overview

A guide for working in raw WebGL2 (and WebGL1 where it differs) plus the GLSL technique that powers shaders. The body of this file is shared mental models, cross-cutting laws, a routing table, and the mistakes that bite across every topic. Topical depth lives in [reference/](./reference/) — one file per topic, each closing with its own Common Mistakes table.

**WebGL2 is the default path.** This skill teaches WebGL2 first. WebGL1 still ships in older browsers (and is the only option on a few legacy embedded WebViews); the differences are concentrated in [reference/webgl1-vs-webgl2.md](./reference/webgl1-vs-webgl2.md). When in doubt, ask `getContext('webgl2')` first and fall back to `getContext('webgl')`.

**Raw WebGL vs. framework.** If the user is building a real 3D app — scene graph, model loaders, cameras, lighting rigs, post-processing chains — point them at [threejs-mastery](../../../cypherpoet-threejs-kit/skills/threejs-mastery/SKILL.md). This skill is for the layer underneath: writing custom shaders, learning the pipeline, hitting a framework limit and dropping down, or wanting zero dependencies.

## When to Use

Trigger this skill when the user:

- Mentions WebGL, WebGL2, GLSL, vertex shader, fragment shader, or pixel shader.
- Names raw WebGL API calls (`gl.createShader`, `gl.bufferData`, `gl.vertexAttribPointer`, `gl.drawArrays`, `gl.uniformMatrix4fv`, etc.).
- Writes or pastes GLSL code (`#version 300 es`, `precision mediump float;`, `in vec3 a_position;`, `gl_FragColor = ...`, `uniform`, `varying`, `attribute`).
- Asks about VBOs, VAOs, UBOs, FBOs/framebuffers, render targets, instancing, or texture units.
- Describes a problem in pipeline terms even without naming WebGL — "my canvas is black", "the shader compiles but nothing draws", "why is my texture upside down", "I need a soft circle that follows the mouse", "draw 10k particles".
- Wants to learn the WebGL pipeline from scratch.
- Wants to write a fragment-shader effect (noise, SDF, pattern, fractal) without pulling in a framework.

## Setup

The minimum WebGL2 boot is a canvas, a context, a program (vertex + fragment shader linked together), some vertex data in a buffer, and a draw call. The smallest complete example lives in [assets/hello-triangle.html](./assets/hello-triangle.html) — copy-paste runnable in any modern browser.

```javascript
const canvas = document.querySelector("canvas");
const gl = canvas.getContext("webgl2");
if (!gl) throw new Error("WebGL2 not supported");

// Compile + link both shaders → a program object.
const program = makeProgram(gl, vertexSource, fragmentSource);
gl.useProgram(program);

// Upload vertex data once.
const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const buffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(program, "a_position");
gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

// Draw.
gl.viewport(0, 0, canvas.width, canvas.height);
gl.clearColor(0, 0, 0, 1);
gl.clear(gl.COLOR_BUFFER_BIT);
gl.drawArrays(gl.TRIANGLES, 0, 3);
```

For anything beyond a single static frame — animation, resize, repeated draws — start from [assets/webgl2-boilerplate.html](./assets/webgl2-boilerplate.html), which adds a `requestAnimationFrame` loop, a HiDPI-aware resize handler, and a `makeProgram` helper that surfaces shader errors clearly.

If the goal is "I just want to write a fragment shader" (no geometry, no transforms), use [assets/shader-sandbox.html](./assets/shader-sandbox.html) — a fullscreen-quad scaffold that gives the shader `u_resolution`, `u_time`, and `u_mouse` uniforms, Book-of-Shaders style.

## Shared Laws

These cross every topic. Internalize them once and most of WebGL's "weird" behavior stops being weird.

### WebGL Is a Big State Machine

There is one current program, one current VAO, one current buffer per binding target, one current texture per texture unit, one viewport, one set of enabled capabilities (depth test, blend, cull face). Every call either reads or mutates that global state. A function like `gl.bufferData` doesn't take "which buffer" — it operates on whatever is currently bound to `ARRAY_BUFFER`. This is the single biggest source of "I called the function and nothing happened" bugs.

The practical consequence: **bind before you call**. Bind the VAO before setting attribute pointers. Bind the buffer before uploading data. `useProgram` before setting uniforms. Bind the framebuffer before drawing to a texture. When in doubt, walk the chain of binds backwards.

### Shaders Must Compile *and* Link

Two separate gates. `compileShader` can succeed on each shader individually and `linkProgram` can still fail because vertex outs don't match fragment ins, or built-in versions disagree, or attribute locations collide. Always check both. The error text from `getShaderInfoLog` and `getProgramInfoLog` is the most useful thing in the entire API — read it before anything else.

### Uniforms Belong to a Program, Not to a Context

`gl.uniform4fv(loc, value)` writes to the *currently bound* program. Setting a uniform on the wrong program is a silent no-op. After `useProgram(p)`, all uniform writes go to `p`. When swapping programs, you re-set uniforms — they're not shared.

### Contexts Get Lost

On mobile, on GPU resets, when another tab steals the GPU, on driver crashes. The context fires a `webglcontextlost` event and every resource (buffers, textures, programs) becomes invalid. Add listeners that prevent the default on lost and recreate resources on `webglcontextrestored`. Skipping this works fine in dev and breaks in production on real devices.

### WebGL2 First, WebGL1 as Fallback

`#version 300 es` GLSL with `in`/`out` qualifiers is the modern shape. VAOs, instancing, UBOs, MRTs, NPOT textures, sRGB framebuffers all ship by default. WebGL1 needs extensions (`OES_vertex_array_object`, `ANGLE_instanced_arrays`) and uses `attribute`/`varying`/`gl_FragColor`. If the user pastes either dialect, follow their lead; if they're starting fresh, default to WebGL2.

### Y Is Up — and Flipped

Clip space `+Y` is up, but the canvas's CSS coordinate space (and mouse events) has `+Y` going down. Texture coordinates `+V` is up by default, but image pixels are stored top-down. Either flip on the JS side (`gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true)` for textures; `y = canvas.height - mouseY` for mouse uniforms) or flip in the shader — pick one and be consistent.

### Canvas Pixel Size Is Two Sizes

A canvas has a **CSS size** (`canvas.clientWidth`/`clientHeight` — what the user sees) and a **drawing-buffer size** (`canvas.width`/`canvas.height` — what the GPU writes into). They are not coupled. On a retina display where `devicePixelRatio = 2`, a 600 CSS-pixel canvas needs a 1200-pixel drawing buffer to look crisp:

```javascript
const dpr = window.devicePixelRatio || 1;
canvas.width  = Math.round(canvas.clientWidth  * dpr);
canvas.height = Math.round(canvas.clientHeight * dpr);
gl.viewport(0, 0, canvas.width, canvas.height);
```

**A user saying "600x600 canvas" is always describing the CSS size** — what they want to see — never the drawing buffer. Set the displayed size via CSS (or the matching HTML `width`/`height` attribute as a CSS hint), then size the drawing buffer to `cssSize * devicePixelRatio`. Writing `canvas.width = 600` directly skips the DPR multiply and produces a blurry image on every retina display — the canonical "looks fine on my Linux desktop, looks like garbage on a MacBook" bug. Apply this even when the prompt names fixed pixel dimensions.

## Topics

| Topic | Reference | What it covers |
|-------|-----------|----------------|
| Pipeline and setup | [pipeline-and-setup.md](./reference/pipeline-and-setup.md) | Rasterization model, state machine, context creation, HiDPI/resize, context loss |
| Shaders and GLSL | [shaders-and-glsl.md](./reference/shaders-and-glsl.md) | Shader anatomy, compile/link lifecycle, GLSL ES 3.00 syntax, qualifiers, built-ins |
| Buffers and attributes | [buffers-and-attributes.md](./reference/buffers-and-attributes.md) | VBOs, IBOs, VAOs, attribute layout, interleaved vs separate, indexed draws |
| Transforms | [transforms.md](./reference/transforms.md) | 2D matrices, model-view-projection, orthographic vs perspective, basic camera |
| Textures and framebuffers | [textures-and-framebuffers.md](./reference/textures-and-framebuffers.md) | Texture creation/upload, filtering, mipmaps, FBOs, render-to-texture |
| Lighting | [lighting.md](./reference/lighting.md) | Directional/point/spot, normals, ambient + diffuse + specular |
| Shader techniques | [shader-techniques.md](./reference/shader-techniques.md) | `smoothstep`/`mix`, noise (value/Perlin/simplex), SDFs, polar coords, FBM |
| Performance | [performance.md](./reference/performance.md) | Instancing, UBOs, draw-call batching, state caching, CPU↔GPU sync stalls |
| Debugging | [debugging.md](./reference/debugging.md) | Reading info logs, `gl.getError`, Spector.js, the black-canvas checklist |
| WebGL1 vs WebGL2 | [webgl1-vs-webgl2.md](./reference/webgl1-vs-webgl2.md) | Concise diff for legacy code or fallback paths |

## Routing Rules

When the question fits one topic cleanly, load that reference and answer from it. Most non-trivial WebGL work spans two or three — load each in turn.

Quick routing cues:

- "Black canvas / nothing draws / shader compiles but no output" → **debugging** first, then whichever stage is the culprit.
- "Write a fragment shader that draws X" with no geometry talk → **shader-techniques** + the shader-sandbox asset.
- "How do I get this shape on screen" → **pipeline-and-setup** + **buffers-and-attributes**.
- "My texture looks wrong / upside down / blurry / pixelated" → **textures-and-framebuffers**.
- "Render thousands / millions of X" → **performance** (instancing).
- "Move/rotate/scale this in 3D", "perspective camera", "screen-to-world" → **transforms**.
- "Make this look lit / shiny / matte" → **lighting**.
- "Render to a texture", "post-process pass", "ping-pong buffers" → **textures-and-framebuffers** (the FBO half).
- "Why is `varying` not a keyword anymore" / "this WebGL1 sample doesn't work" → **webgl1-vs-webgl2**.
- App-level 3D (scene graph, GLTF loaders, OrbitControls, EffectComposer) → hand off to [`threejs-mastery`](../../../cypherpoet-threejs-kit/skills/threejs-mastery/SKILL.md).

## Cross-Cutting Common Mistakes

These bite across every topic. Topical mistakes live in each reference's own table.

| Mistake | Fix |
|---------|-----|
| Canvas is black, no errors logged | Walk the [debugging checklist](./reference/debugging.md). The top suspects: viewport not set after canvas resize, depth test rejecting everything, attribute not enabled, wrong VAO bound, uniform set before `useProgram`. |
| Shader compiles, draw does nothing | Linking probably failed silently — check `getProgramInfoLog`. Common cause: vertex `out` and fragment `in` names/types don't match. |
| `gl.bufferData` "applies to the wrong buffer" | You forgot to `bindBuffer` first, or a later call rebound the target. WebGL is a state machine — bind before every upload. |
| Attribute pointers reset themselves between draws | You're not using a VAO. WebGL2: always bind a VAO before setting attribute pointers; the VAO captures the pointer state. WebGL1: same thing via `OES_vertex_array_object`. |
| Uniforms set fine but the shader sees zero | Wrong program bound when the uniform was written. `useProgram` before every `uniform*` call when juggling multiple programs. |
| `NaN` propagating into the entire shader output | Division by zero somewhere — most often `normalize(vec3(0))`. Guard with `length(v) > 0 ? normalize(v) : vec3(0)`. |
| Texture renders as solid black or white | Filtering set to mipmapped without mipmaps generated, or texture not complete (NPOT in WebGL1, missing wrap modes, etc.). Either call `gl.generateMipmap` or set `MIN_FILTER` to `LINEAR`/`NEAREST`. |
| Image loads but uploads upside down | Set `gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true)` before `texImage2D`, or flip the V coordinate in the shader. |
| `gl.getError` returns errors only after every call breaks | `gl.getError` is *cumulative and slow*. Use sparingly — once per frame in dev, never in tight loops. Prefer reading the info logs and using a tool like Spector.js. |
| Canvas blurry on retina / HiDPI | Set `canvas.width = canvas.clientWidth * devicePixelRatio` (and height similarly) in the resize handler, then `gl.viewport(0, 0, canvas.width, canvas.height)`. |
| Shader silently ignores writes to `out` variables | The output isn't being routed to a draw buffer. Default framebuffer expects exactly one fragment out (location 0). MRT setups need explicit `layout(location = N) out` plus `drawBuffers`. |
| Mobile WebGL works in dev, dies in the wild | No `webglcontextlost` / `webglcontextrestored` handlers. Add them. |

## Handoff: When to Reach for a Framework

This skill stops being the right tool when the user needs:

- A scene graph with parented transforms, animated cameras, multiple models — use [`threejs-mastery`](../../../cypherpoet-threejs-kit/skills/threejs-mastery/SKILL.md).
- GLTF/GLB/HDR loaders, IBL, PBR materials, post-processing chains — same.
- WebGPU (compute shaders, modern API surface) — Three.js's `WebGPURenderer` path, also in `threejs-mastery`.
- A 2D rendering layer (sprites, batched UI) — consider PixiJS or Konva instead of rolling it raw.

Raw WebGL is the right tool for: writing one custom shader, prototyping a graphics technique, embedded demos, performance-critical custom pipelines, and learning the pipeline itself.

## See Also

- [WebGL2 Fundamentals](https://webgl2fundamentals.org/) — the canonical WebGL2 tutorial site. Deep, code-first, complete.
- [The Book of Shaders](https://thebookofshaders.com/) — the canonical GLSL fragment-shader tutorial. Procedural patterns, noise, SDFs, color.
- [Khronos WebGL2 spec](https://registry.khronos.org/webgl/specs/latest/2.0/) — the source of truth when behavior surprises you.
- [Shadertoy](https://www.shadertoy.com/) — a galaxy of fragment-shader examples (uses its own uniform conventions; adapt to your scaffold).
- [Spector.js](https://spector.babylonjs.com/) — capture-and-inspect every WebGL call in a frame; the single most useful debugging tool.
