# Debugging

**Contents:** [The Black Canvas Checklist](#the-black-canvas-checklist) · [Reading Info Logs](#reading-info-logs) · [`gl.getError()`](#glgeterror) · [Spector.js](#spectorjs--the-tool-to-reach-for) · [Print-Debugging Inside Shaders](#print-debugging-inside-shaders) · [When the Shader Compiles Differently in Production](#when-the-shader-compiles-differently-in-production) · [Common Mistakes](#common-mistakes)

## The Black Canvas Checklist

By far the most common WebGL question: "my canvas is black, no errors logged, what's wrong?" Walk this checklist top to bottom. The first few catch ~80% of cases.

1. **Did compile or link fail?** Read `getShaderInfoLog` for both shaders and `getProgramInfoLog` for the program. Even if your wrapper "succeeded," double-check the logs — some apps swallow them.
2. **Was the program bound at draw time?** `gl.useProgram(program)` immediately before the draw call.
3. **Was the right VAO bound?** `gl.bindVertexArray(vao)` immediately before the draw.
4. **Is the viewport set to the actual canvas size?** After every resize, `gl.viewport(0, 0, canvas.width, canvas.height)`. A stale 1x1 viewport draws into a single pixel.
5. **Did you clear with non-zero alpha?** `gl.clearColor(0, 0, 0, 1)` — alpha of zero plus the canvas's default `alpha: true` can make the page background show through and look black.
6. **Are the vertices actually in clip space?** A vertex shader that outputs unscaled world-space coords will land far outside `[-1, 1]` and get clipped. Try outputting `gl_Position = vec4(a_position, 1.0)` with positions already in `[-1, 1]` to isolate the math.
7. **Is the depth test killing everything?** If `DEPTH_TEST` is enabled and you cleared without `DEPTH_BUFFER_BIT`, the existing depth buffer (all 1.0s) rejects nothing — but if your geometry is at `z = -1` after projection, it might be behind the near plane. Try `gl.disable(gl.DEPTH_TEST)` to see if geometry appears.
8. **Is back-face culling killing everything?** If `CULL_FACE` is enabled and you wound your triangles clockwise instead of counter-clockwise (or vice versa), every triangle is back-facing. Try `gl.disable(gl.CULL_FACE)`.
9. **Are the uniforms set to the program that's bound?** Setting a uniform before `useProgram` writes to the previous program (or to none). Always `useProgram` → set uniforms → draw.
10. **Are attributes actually enabled and pointing at the right buffer?** `enableVertexAttribArray` is required. Run `gl.getVertexAttrib(loc, gl.VERTEX_ATTRIB_ARRAY_ENABLED)` once in dev to confirm.
11. **Is the fragment shader actually writing to `outColor`?** In WebGL2, the declared `out` is the one that lands in color attachment 0. Misnaming it (e.g., declaring `fragColor` and `outFrag` both) confuses some drivers.
12. **Is `gl.getError()` returning something?** Call it once after init and once before the first draw. Any value other than `gl.NO_ERROR` (0) is real — look up the constant name.

## Reading Info Logs

```javascript
const log = gl.getShaderInfoLog(shader);
if (log) console.error(log);
```

Shader logs typically look like `ERROR: 0:5: 'foo' : undeclared identifier` — the `5` is the line number (1-based) within the shader source you uploaded. If the line number is off, you probably prepended `#version` or precision declarations dynamically — count from the actual top of what you passed to `shaderSource`.

Program link logs are usually shorter: "vertex shader output 'v_uv' has no matching declaration in fragment shader" tells you exactly what's wrong.

## `gl.getError()`

```javascript
const err = gl.getError();
switch (err) {
  case gl.NO_ERROR: break;
  case gl.INVALID_ENUM: console.error("Bad enum constant"); break;
  case gl.INVALID_VALUE: console.error("Bad numeric argument"); break;
  case gl.INVALID_OPERATION: console.error("Operation not allowed in current state"); break;
  case gl.INVALID_FRAMEBUFFER_OPERATION: console.error("Framebuffer incomplete"); break;
  case gl.OUT_OF_MEMORY: console.error("GPU OOM"); break;
  case gl.CONTEXT_LOST_WEBGL: console.error("Context lost"); break;
}
```

`getError` is **cumulative and slow**. Don't call it in a tight loop — it forces a CPU↔GPU sync. Use it sparingly: once after init, once after major state changes, perhaps once per frame in dev. In production, leave it out.

A pattern that works: wrap GL calls in dev only (e.g., via a Proxy) and assert `getError == NO_ERROR` after each. Strip the wrapper in production builds.

## Spector.js — The Tool to Reach For

[Spector.js](https://spector.babylonjs.com/) is a browser extension that captures every WebGL call in a frame and lets you click through them. It shows:

- The full state at each call (which program, VAO, framebuffer).
- Every uniform value and its current binding.
- A visual preview of every framebuffer at each draw.
- The shader source for the bound program.

When the checklist above doesn't catch the issue, fire up Spector, capture a frame, and walk the draws. Nine times in ten you'll see the bug — wrong texture bound, wrong uniform value, wrong viewport, draw count mismatch.

## Print-Debugging Inside Shaders

There's no `console.log` in GLSL. The closest equivalent is "render the value as color":

```glsl
// Debug a value by writing it to the output color.
outColor = vec4(some_value, 0.0, 0.0, 1.0);          // single float in red
outColor = vec4(uv, 0.0, 1.0);                       // visualize UVs
outColor = vec4(normal * 0.5 + 0.5, 1.0);            // visualize normals (remap -1..1 → 0..1)
outColor = vec4(vec3(depth), 1.0);                   // visualize depth
```

For "is this branch ever taken?" — paint the pixel a unique color in that branch:

```glsl
if (something_should_be_true) {
  outColor = vec4(1.0, 0.0, 1.0, 1.0);   // magenta = "I was here"
  return;
}
```

For numeric values, render a digit using a font texture, or sample known ranges with `step()` to convert numbers to color bands. Crude but effective.

## When the Shader Compiles Differently in Production

Driver bugs and shader compiler differences are real. Symptoms: works in Chrome dev, fails in Safari; works on Intel iGPU, fails on Apple Silicon; works on desktop, draws garbage on a specific Android device.

Mitigations:

- Always use `precision highp float;` in fragment shaders. `mediump` can be 16-bit float on mobile and cause banding/precision artifacts.
- Avoid unspecified-result patterns: `1.0 / 0.0`, `pow(negative, non_integer)`, `sqrt(negative)`. Guard them.
- Don't rely on `gl_FragCoord.w` having a specific meaning across drivers.
- When a `for` loop runs millions of times in a shader, some drivers refuse to compile. Cap it or split the work.
- Test on real mobile hardware before shipping. Browser DevTools' device-mode is a layout simulator, not a GPU simulator.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| "Shader compiles fine but I see nothing" | Compile success doesn't mean link success. Always check `getProgramInfoLog` too. |
| Logs look fine, still no output | Walk the [black canvas checklist](#the-black-canvas-checklist). Most often: viewport wrong, attribute not enabled, or wrong VAO bound. |
| `gl.getError()` everywhere in the render loop | Stalls the GPU. Use it during dev, strip from prod. |
| Print-debugging in shaders via comments | GLSL doesn't conditionally compile branches based on comments. Write the value to `outColor`. |
| "It works in Chrome on my Mac and breaks everywhere else" | Mobile GPUs are stricter. Test on real mobile and Safari before shipping. Add `precision highp float;` explicitly. |
| Error message line number doesn't match your file | You're prepending `#version` / precision lines at upload time. Count from the start of the string you pass to `shaderSource`. |
| Spector.js capture shows zero draw calls | Your render loop didn't fire during the capture (Spector captures one frame after you click). Make sure the page is actively rendering when you hit capture. |
