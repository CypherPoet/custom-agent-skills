# Lighting

## Table of Contents

| Section | Covers |
|---|---|
| [The Three Ingredients](#the-three-ingredients) | Ambient baseline, Lambertian diffuse response, Blinn-Phong specular highlights, and when raw shading should yield to framework PBR |
| [Per-Vertex vs Per-Fragment](#per-vertex-vs-per-fragment) | Gouraud cost savings versus density-dependent highlights and smoother per-pixel Phong shading |
| [Surface Normals](#surface-normals) | Normal attributes, inverse-transpose transforms, post-interpolation normalization, and complete world-space Blinn-Phong inputs |
| [Light Types](#light-types) | Infinite directional rays, distance-attenuated point sources, and smooth inner-to-outer spotlight cones |
| [Multiple Lights](#multiple-lights) | Small uniform-array loops versus culled, forward-plus, or deferred techniques for larger light sets |
| [Tone Mapping and Gamma](#tone-mapping-and-gamma) | Reinhard compression and approximate sRGB output, with framebuffer conversion as a WebGL2 alternative |
| [Common Mistakes](#common-mistakes) | Negative diffuse and attenuation, vertex-blocky specular, wrong normal transforms, bad half vectors, absent gamma, stale normal length, and hard spot edges |

## The Three Ingredients

Real-time shading boils down to three terms added together per fragment:

- **Ambient**: a constant baseline so shadowed faces don't go pitch-black.
- **Diffuse** (Lambertian): how much the surface is facing the light. `max(dot(normal, lightDir), 0)`.
- **Specular**: the shiny highlight. Depends on the angle between the reflection and the camera.

This is the Blinn-Phong model — old-school, but cheap, well-understood, and a great starting point for any custom shader. PBR (physically based rendering) is the modern standard for app-level engines; for raw-WebGL custom effects, Phong/Blinn-Phong is usually what you want. (For PBR in a framework, hand off to [`threejs-mastery` materials](https://github.com/CypherPoet/custom-agent-skills/blob/main/plugins/threejs-kit/skills/threejs-mastery/references/materials.md).)

## Per-Vertex vs Per-Fragment

You can compute lighting in the **vertex shader** (Gouraud shading — cheap, but specular highlights look blocky on low-poly meshes) or in the **fragment shader** (Phong shading — more expensive per pixel, but smooth highlights regardless of vertex density). Default to per-fragment unless you're optimizing for mobile.

## Surface Normals

Lighting math needs the surface normal. Three rules to keep them correct:

1. **Upload them as a vertex attribute**, normalized. Typically a `vec3` per vertex.
2. **Transform them with the normal matrix** (transpose of inverse of model's upper 3×3), not the model matrix. See [transforms.md](./transforms.md#normals--the-subtle-matrix).
3. **Re-normalize in the fragment shader** after interpolation — linear interpolation between two unit vectors doesn't yield a unit vector.

```glsl
// Vertex
in vec3 a_position;
in vec3 a_normal;
uniform mat4 u_model;
uniform mat4 u_viewProjection;
uniform mat3 u_normalMatrix;
out vec3 v_worldPos;
out vec3 v_normal;

void main() {
  vec4 worldPos = u_model * vec4(a_position, 1.0);
  v_worldPos = worldPos.xyz;
  v_normal = normalize(u_normalMatrix * a_normal);
  gl_Position = u_viewProjection * worldPos;
}
```

```glsl
// Fragment
in vec3 v_worldPos;
in vec3 v_normal;
uniform vec3 u_lightDir;        // world-space, pre-normalized
uniform vec3 u_lightColor;
uniform vec3 u_ambient;
uniform vec3 u_albedo;
uniform vec3 u_cameraPos;
out vec4 outColor;

void main() {
  vec3 N = normalize(v_normal);
  vec3 L = normalize(-u_lightDir);            // From surface to light.
  vec3 V = normalize(u_cameraPos - v_worldPos); // From surface to camera.
  vec3 H = normalize(L + V);                  // Half-vector for Blinn-Phong.

  float diff = max(dot(N, L), 0.0);
  float spec = pow(max(dot(N, H), 0.0), 32.0); // 32 = "shininess"; higher → tighter highlight

  vec3 color = u_albedo * (u_ambient + u_lightColor * diff)
             + u_lightColor * spec;
  outColor = vec4(color, 1.0);
}
```

## Light Types

### Directional

The sun. Light comes from infinity in one direction, so position doesn't matter — only the direction.

```glsl
vec3 L = normalize(-u_lightDir);   // u_lightDir points *away* from the light (toward the scene)
```

Cheap, no attenuation, perfect for outdoor scenes.

### Point

A bulb. Has a world-space position, emits in all directions, falls off with distance.

```glsl
vec3 toLight = u_lightPos - v_worldPos;
float distance = length(toLight);
vec3 L = toLight / distance;
float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.05 * distance * distance);
// diffuse, specular as before, multiplied by attenuation
```

The attenuation polynomial — `1 / (constant + linear * d + quadratic * d²)` — has no "right" values; pick by eye. Larger quadratic = faster falloff.

### Spot

A flashlight: like a point light, but only inside a cone.

```glsl
vec3 toLight = u_lightPos - v_worldPos;
vec3 L = normalize(toLight);
float theta = dot(L, normalize(-u_spotDir));
float intensity = smoothstep(u_outerCos, u_innerCos, theta);   // soft edge
// intensity = 0 outside the outer cone, 1 inside the inner cone, smooth between
```

`u_innerCos` and `u_outerCos` are precomputed cosines of the cone half-angles (smaller = wider; `cos(0) = 1` is the cone axis).

## Multiple Lights

Two strategies:

- **Loop in the fragment shader.** Pass lights as a uniform array. Easiest, but every fragment pays for every light even when far from it. Practical up to maybe 4–8 lights.
- **Light culling / forward+ / deferred.** More complex; outside the scope of a single shader. For more than a handful of lights in a custom WebGL renderer, look at deferred shading (render G-buffer to FBOs, then accumulate lights in screen-space passes).

For raw WebGL projects, almost always: one directional ("sun") + a handful of points. Past that, reach for a framework.

## Tone Mapping and Gamma

After computing lighting in linear space, output to an sRGB display:

```glsl
// At the end of main, before writing outColor:
vec3 mapped = color / (color + vec3(1.0));          // Reinhard tone mapping — simple, OK
mapped = pow(mapped, vec3(1.0 / 2.2));              // Approx sRGB gamma
outColor = vec4(mapped, 1.0);
```

Skip both at your peril — over-bright lights blow out without tone mapping, and shadows look milky without gamma correction. For a quick-and-dirty default, the two lines above work.

(In WebGL2 you can create an sRGB-format framebuffer that gamma-corrects automatically on write. Cleaner but a small step deeper into format territory.)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Lit surfaces are darker than expected | Forgot to clamp diffuse with `max(dot, 0.0)` — negative contributions subtract. |
| Specular highlight is square/blocky | You're doing per-vertex lighting on a low-poly mesh. Move the math to the fragment shader. |
| Normals look correct on the cube but wrong after scaling | Using model matrix to transform normals. Use a normal matrix (`mat3.normalFromMat4`). |
| Highlight stays bright at all view angles | View vector not normalized, or you used the unhalved view vector instead of the half-vector. For Blinn-Phong, `H = normalize(L + V)` and `pow(dot(N, H), shininess)`. |
| Adding a second light makes the scene black | The light's attenuation went negative — clamp or use `max(0, ...)` on each component. |
| Image looks "milky" or washed out | No gamma correction. Apply `pow(color, 1/2.2)` before writing the final color. |
| Lights flicker as objects move | Interpolated `v_normal` not re-normalized in the fragment shader. |
| Spotlight has a hard edge | Use `smoothstep(outerCos, innerCos, dot(L, spotAxis))` instead of `step`. |
