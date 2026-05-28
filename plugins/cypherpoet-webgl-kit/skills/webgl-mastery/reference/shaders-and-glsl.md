# Shaders and GLSL

## The Compile + Link Lifecycle

A WebGL program is a vertex shader and a fragment shader compiled separately, then linked together. Both stages are required — there's no "fragment-only" program.

```javascript
function compileShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(shader);
    gl.deleteShader(shader);
    throw new Error(`Shader compile error:\n${log}\n--- source ---\n${source}`);
  }
  return shader;
}

function makeProgram(gl, vsSource, fsSource) {
  const vs = compileShader(gl, gl.VERTEX_SHADER, vsSource);
  const fs = compileShader(gl, gl.FRAGMENT_SHADER, fsSource);
  const program = gl.createProgram();
  gl.attachShader(program, vs);
  gl.attachShader(program, fs);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const log = gl.getProgramInfoLog(program);
    gl.deleteProgram(program);
    throw new Error(`Program link error:\n${log}`);
  }
  // Safe to detach + delete after a successful link.
  gl.detachShader(program, vs);
  gl.detachShader(program, fs);
  gl.deleteShader(vs);
  gl.deleteShader(fs);
  return program;
}
```

Two failure modes, both extremely common:

- **Compile fails.** `getShaderInfoLog` will name the line and column. Most errors are typos in built-in names, missing semicolons, or implicit type conversions (GLSL won't auto-promote `int` to `float`).
- **Link fails.** Vertex `out` and fragment `in` names/types must match exactly. Same for `uniform`s declared in both stages (they share a namespace). The link log says which name is mismatched.

## GLSL ES 3.00 (WebGL2)

A WebGL2 shader **must** start with `#version 300 es` on the *first* line — no leading whitespace, no comments before it. Fragment shaders also need a precision qualifier:

```glsl
#version 300 es
precision highp float;

in vec3 v_color;
out vec4 outColor;

void main() {
  outColor = vec4(v_color, 1.0);
}
```

Vertex shader equivalent:

```glsl
#version 300 es

in vec3 a_position;
in vec3 a_color;
out vec3 v_color;

uniform mat4 u_mvp;

void main() {
  v_color = a_color;
  gl_Position = u_mvp * vec4(a_position, 1.0);
}
```

Key GLSL ES 3.00 changes from GLSL ES 1.00 (WebGL1):

- `attribute` → `in` (vertex shader inputs).
- `varying` → `out` in vertex, `in` in fragment.
- `gl_FragColor` is gone — declare your own `out vec4 outColor;` and write to it.
- `texture2D` / `textureCube` → `texture` (overloaded by sampler type).
- New types: `uint`, `uvec*`, `mat2x3`, etc. Integer texture samplers (`isampler2D`, `usampler2D`).

## Types You'll Actually Use

| Type | What |
|------|------|
| `float`, `int`, `uint`, `bool` | Scalars. |
| `vec2`, `vec3`, `vec4` | Floating-point vectors. |
| `ivec2/3/4`, `uvec2/3/4`, `bvec2/3/4` | Integer/unsigned/bool vectors. |
| `mat2`, `mat3`, `mat4` | Square matrices, column-major. `mat3x4` etc. for non-square. |
| `sampler2D`, `samplerCube`, `sampler3D`, `sampler2DArray` | Texture handles. |
| `isampler2D`, `usampler2D` | Integer texture samplers. |

GLSL is strict about types. `float x = 1;` is a compile error — write `1.0`. `vec3(1)` is fine (broadcasts), `vec3(1.0, 2.0, 3.0)` is fine, `vec3(some_vec2, 1.0)` is fine (constructor concatenates).

## Swizzling

Vector components have multiple names that all map to the same slots: `.xyzw`, `.rgba`, `.stpq`. Swizzling reorders or selects them:

```glsl
vec4 c = vec4(1.0, 2.0, 3.0, 4.0);
c.xyz;      // vec3(1, 2, 3)
c.rgb;      // same thing
c.bgr;      // vec3(3, 2, 1) — channel swap
c.xxxx;     // vec4(1, 1, 1, 1)
c.x = 9.0;  // assignment works for non-repeating swizzles
```

Mixing component families (`c.xrg`) is a compile error. Pick one set per expression.

## Qualifiers

| Qualifier | Where | Meaning |
|-----------|-------|---------|
| `in` | Vertex shader globals | Per-vertex attribute pulled from a buffer. |
| `in` | Fragment shader globals | Interpolated varying from the vertex shader. |
| `out` | Vertex shader globals | Varying that gets interpolated for the fragment shader. |
| `out` | Fragment shader globals | Fragment color output (or MRT attachment). |
| `uniform` | Both | Same value across the entire draw call. Set from JS. |
| `flat` | varyings | Don't interpolate — use the provoking vertex's value. |
| `centroid` | varyings | Sample at the covered area's centroid (MSAA hint). |
| `const` | Anywhere | Compile-time constant. |

## Built-In Variables

In the vertex shader, you write to `gl_Position` (a `vec4` in clip space) and optionally `gl_PointSize`. You can read `gl_VertexID` (which vertex this invocation is, useful for procedural geometry) and `gl_InstanceID` (which instance, when using instanced drawing).

In the fragment shader, you can read `gl_FragCoord` (window-space pixel coordinates, `.xy` are pixel center coords, `.z` is depth, `.w` is `1/w`), `gl_FrontFacing` (bool, for two-sided shading), and `gl_PointCoord` (`vec2` 0..1 across a rasterized point). Write to your declared `out`s; optionally write `gl_FragDepth` to override the interpolated depth (usually a bad idea — disables early-Z).

## Uniforms from JS

```javascript
const u_mvp = gl.getUniformLocation(program, "u_mvp");
const u_color = gl.getUniformLocation(program, "u_color");
const u_texture = gl.getUniformLocation(program, "u_texture");

gl.useProgram(program);                            // REQUIRED before uniform writes.
gl.uniformMatrix4fv(u_mvp, false, mvpMatrix);      // 16-float column-major.
gl.uniform3fv(u_color, [1, 0.5, 0.2]);
gl.uniform1i(u_texture, 0);                        // Texture *unit* index, not the texture object.
```

A few rules that confuse newcomers:

- **Sampler uniforms take a texture unit index, not a texture object.** `gl.uniform1i(u_texture, 0)` says "this sampler reads from texture unit 0". You bind the actual texture with `gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex)`.
- **`gl.getUniformLocation` returns `null` for unused uniforms.** If you declare `uniform vec3 u_unused;` but never read it in main, the compiler optimizes it out and the location is `null`. Setting `null` is a no-op, not an error.
- **Locations are stable for a program.** Cache them after link; don't re-query per frame.
- **`mat4` upload is `uniformMatrix4fv(loc, false, array)`.** The second arg (`transpose`) **must be `false`** in WebGL — non-`false` is a spec error. Pass column-major data (the standard for `glMatrix`, gl-matrix, glm, and Three.js).

## Precision

In WebGL1, vertex shaders defaulted to `highp` for `float` and fragment shaders had no default — you needed `precision mediump float;` (or `highp`). In WebGL2 with `#version 300 es`, fragment shaders still need it; `highp float` is required to be supported. Use `highp` unless you have a measured perf reason; `mediump` can cause banding/precision artifacts on mobile GPUs.

For sampler precision, follow the rule of thumb: `highp` samplers + `highp` lookups for normal/data textures, `mediump` for plain albedo. Most code doesn't bother — `highp` works everywhere on modern hardware.

## Control Flow Caveats

Old WebGL1 advice was "no `for` loops, no early `return`, no `if`" — this is mostly obsolete on modern GPUs. Modern caveats:

- **`for` loop counters need a constant upper bound** in WebGL1 GLSL ES 1.00. WebGL2 GLSL ES 3.00 allows dynamic loops, but compile times for huge unrolls still suffer.
- **Branching has a cost on GPUs**, but predictable branches across a warp (all threads take the same path) are free. Pixel-dependent branches in a tight inner loop can hurt — try `mix()` or `step()` for branchless equivalents.
- **`discard` in fragment shaders disables early-Z** on many GPUs. Only use it when you genuinely need transparency culling.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `Error: Shader compile error: ERROR: 0:1` on line 1 | Almost always `#version 300 es` not on the first line, with leading whitespace or a comment before it. |
| Fragment shader compiles in WebGL1 but not WebGL2 | Add `out vec4 outColor;` and replace `gl_FragColor =` with `outColor =`. Also `attribute`/`varying` → `in`/`out`, and `texture2D` → `texture`. |
| `gl.uniformMatrix4fv(loc, true, m)` throws | The transpose flag must be `false` in WebGL. Transpose on the CPU side if needed. |
| Uniform location is `null` but the uniform is declared | The compiler optimized it out because it's unused. Use it (even `if (false) read it`) or just accept that setting it is a no-op. |
| Sampler bound but shader reads black | You bound the texture but didn't tell the sampler which unit. `gl.uniform1i(samplerLoc, unitIndex)` after `useProgram`. |
| `1.0 / 0.0` or `normalize(vec3(0))` poisons the output | NaN propagates. Guard divisions and normalize calls in shader code. |
| `int x = 1.0;` compile error | GLSL doesn't auto-convert. Use `int(1.0)` or just `1`. |
| Link fails: "out varying 'v_uv' has no matching declaration" | Vertex `out vec2 v_uv;` must have an identically named/typed `in vec2 v_uv;` in the fragment shader. |
