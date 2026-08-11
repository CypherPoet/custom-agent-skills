# Transforms

**Contents:** [Clip Space](#clip-space) · [The MVP Chain](#the-mvp-chain) · [Use a Matrix Library](#use-a-matrix-library) · [Perspective Projection](#perspective-projection) · [Orthographic Projection](#orthographic-projection) · [A Basic Camera](#a-basic-camera) · [Normals](#normals--the-subtle-matrix) · [2D Math Without 3D Overhead](#2d-math-without-3d-overhead) · [Common Mistakes](#common-mistakes)

## Clip Space

The vertex shader's job is to output a `vec4` in **clip space** — a coordinate system where `(x, y, z)` after perspective divide (`/w`) lands in `[-1, +1]` for what's visible. Anything outside gets clipped.

```
clip-space x: -1 (left)   → +1 (right)
clip-space y: -1 (bottom) → +1 (top)
clip-space z: -1 (near)   → +1 (far)
```

The fastest way to get something on screen is to put vertices already in clip space and write `gl_Position = vec4(a_position, 1.0)`. That's how the shader-sandbox fullscreen quad works.

For anything spatial — moving things around, rotating, perspective — you build a 4×4 matrix on the CPU, send it as a uniform, and multiply in the vertex shader.

## The MVP Chain

The classical chain is **Model × View × Projection** (read right-to-left when applied to a position):

```
gl_Position = projection * view * model * vec4(position, 1.0);
```

- **Model**: object-local → world space. Where this object is in the scene.
- **View**: world space → camera space. "Move the world so the camera is at the origin looking down -Z."
- **Projection**: camera space → clip space. Adds perspective foreshortening (or stays orthographic).

Most code combines view × projection on the CPU into a single matrix (the "viewProjection") since it's the same for every object in a frame, and only sends `model` and `viewProjection` to the shader. Or combines all three into a single `u_mvp` per object.

## Use a Matrix Library

Don't roll your own. The two standard choices for WebGL:

- **[`gl-matrix`](https://github.com/toji/gl-matrix)** — battle-tested, column-major (matches WebGL's convention), `Float32Array`-native (fast uniform uploads). Use this for new code.
- **[`wgpu-matrix`](https://github.com/greggman/wgpu-matrix)** — same author's newer library, friendlier API, works for WebGL2 fine.

```javascript
import { mat4, vec3 } from "gl-matrix";

const model = mat4.create();
mat4.translate(model, model, [0, 0, -5]);
mat4.rotateY(model, model, performance.now() * 0.001);

const view = mat4.create();
mat4.lookAt(view, [0, 2, 5], [0, 0, 0], [0, 1, 0]);

const projection = mat4.create();
mat4.perspective(projection, Math.PI / 4, canvas.width / canvas.height, 0.1, 100);

const mvp = mat4.create();
mat4.multiply(mvp, view, model);
mat4.multiply(mvp, projection, mvp);

gl.uniformMatrix4fv(u_mvp, false, mvp);
```

Two memory layout notes that matter:

- **WebGL matrices are column-major** in memory. `gl-matrix` and Three.js both produce column-major arrays — they work as-is.
- **`uniformMatrix4fv`'s transpose flag must be `false`** in WebGL. If you have a row-major matrix from another library, transpose it on the CPU first.

## Perspective Projection

```javascript
mat4.perspective(out, fovYRadians, aspectRatio, near, far);
```

- `fovYRadians` is the *vertical* field of view in radians. 45° (`Math.PI / 4`) is a comfortable default; 60–75° feels first-person.
- `aspectRatio` is `width / height`. Recompute on resize, or the image stretches.
- `near` and `far` are the clipping distances. **Don't make `near` too small.** A `near` of `0.001` wastes most of the depth buffer's precision on the first centimeter; geometry behind that struggles with z-fighting. Use the largest `near` that doesn't clip your scene's closest object — typically `0.1` for general scenes, `0.5` for terrain.

## Orthographic Projection

For 2D rendering, UI layers, or technical visualizations:

```javascript
mat4.ortho(out, left, right, bottom, top, near, far);
```

A common 2D setup: `ortho(out, 0, canvas.width, canvas.height, 0, -1, 1)` puts `(0, 0)` at the top-left like CSS, with pixels as units. Inverting `top` and `bottom` flips the Y axis.

## A Basic Camera

`lookAt` is the standard "where am I and what am I pointing at":

```javascript
mat4.lookAt(view, eye, target, up);
// eye:    [x, y, z] camera position in world space
// target: [x, y, z] world-space point to look at
// up:     usually [0, 1, 0]
```

For an orbit camera (spherical coords around a target):

```javascript
function orbitCamera(yawRadians, pitchRadians, distance, target) {
  const eye = [
    target[0] + distance * Math.cos(pitchRadians) * Math.sin(yawRadians),
    target[1] + distance * Math.sin(pitchRadians),
    target[2] + distance * Math.cos(pitchRadians) * Math.cos(yawRadians),
  ];
  return mat4.lookAt(mat4.create(), eye, target, [0, 1, 0]);
}
```

For first-person: track a position and a forward vector (or yaw/pitch); compute `target = position + forward` each frame and call `lookAt`.

## Normals — The Subtle Matrix

When you transform positions by a matrix, you can't transform normals by the same matrix if it includes non-uniform scale. The correct matrix for normals is the **transpose of the inverse of the upper-left 3×3** of the model matrix:

```javascript
const normalMatrix = mat3.create();
mat3.normalFromMat4(normalMatrix, model);
gl.uniformMatrix3fv(u_normal, false, normalMatrix);
```

```glsl
in vec3 a_normal;
uniform mat3 u_normal;
out vec3 v_normal;

void main() {
  v_normal = normalize(u_normal * a_normal);
  // ...
}
```

For uniform scale or rotation-only transforms, the upper 3×3 of the model matrix works as a shortcut. The normal-from-mat4 helper handles both cases correctly — just use it.

## 2D Math Without 3D Overhead

For pure 2D work (sprites, UI, charts) you can stick to `mat3` and `vec2`. The math is the same shape; you just lose the Z dimension. The savings on uniform uploads and shader math are real on mobile.

For Book-of-Shaders-style fullscreen-quad effects, you usually skip the matrix entirely — just use `gl_FragCoord.xy / u_resolution.xy` as your UV and forget about transforms. See [shader-techniques.md](./shader-techniques.md).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Scene renders mirrored or upside down | View matrix or projection matrix has a sign flipped, or you're applying `model × view × projection` instead of `projection × view × model`. The chain reads right-to-left. |
| Image stretches horizontally on window resize | Aspect ratio not recomputed. Update `projection` and re-upload on resize. |
| Far objects flicker / z-fight | `near` too small relative to `far`. Bump `near` to `0.1` or higher; lower `far` to the actual scene extent. |
| Normals look wrong after non-uniform scale | Use a proper normal matrix (`mat3.normalFromMat4`), not the upper 3×3 of the model matrix. |
| Object rotates around the wrong point | Translation order matters. Translate to the desired pivot, rotate, translate back, then apply the rest of the transform. |
| `uniformMatrix4fv` with `transpose: true` throws | Must be `false` in WebGL. Transpose on the CPU. |
| `mat4.perspective` with fov in degrees gives a fisheye | The argument is radians. Use `Math.PI / 4` or convert from degrees explicitly. |
| 2D-looking scene needs odd-feeling Z values to be visible | You're applying perspective division to clip-space coords near the `w = 0` plane. Use `ortho` for true 2D. |
