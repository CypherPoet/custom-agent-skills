# Shader Techniques

The GLSL patterns that power procedural visuals — shaped curves, soft edges, noise, signed distance fields. These compose: a great-looking shader is usually two or three of these stacked. For deep dives on any of them, [The Book of Shaders](https://thebookofshaders.com/) is the canonical reference. The snippets here are the working subset that covers ~90% of fragment-shader requests.

**Contents:** [The Fullscreen Quad Setup](#the-fullscreen-quad-setup) · [`step` and `smoothstep`](#step-and-smoothstep--the-building-blocks) · [`mix`](#mix--linear-interpolation) · [Mouse-Following Soft Circle](#mouse-following-soft-circle) · [Hash and Value Noise](#hash-and-value-noise) · [Simplex / Perlin Noise](#simplex--perlin-noise) · [Fractal Brownian Motion (fBM)](#fractal-brownian-motion-fbm) · [Signed Distance Fields (SDFs)](#signed-distance-fields-sdfs) · [Polar Coordinates](#polar-coordinates) · [Color](#color) · [Composing](#composing--a-cheap-lava-lamp) · [Common Mistakes](#common-mistakes)

## The Fullscreen Quad Setup

Most of these techniques run in a fragment shader on a fullscreen quad. The vertex shader is trivial — just pass clip-space positions through — and the fragment shader gets a 0..1 UV via `gl_FragCoord.xy / u_resolution.xy`. The [shader-sandbox asset](../assets/shader-sandbox.html) is exactly this scaffold with `u_resolution`, `u_time`, and `u_mouse` already wired up.

Inside the fragment shader:

```glsl
vec2 uv = gl_FragCoord.xy / u_resolution.xy;          // 0..1, with origin at bottom-left
vec2 st = (gl_FragCoord.xy * 2.0 - u_resolution.xy)   // -1..1, aspect-corrected
        / min(u_resolution.x, u_resolution.y);
```

`uv` is easy to reason about for 2D layouts; `st` is better when you want a circle to look like a circle regardless of aspect ratio.

## `step` and `smoothstep` — The Building Blocks

```glsl
float step(float edge, float x);            // 0 if x < edge, 1 otherwise — hard edge
float smoothstep(float e0, float e1, float x); // 0 below e0, 1 above e1, smooth Hermite curve between
```

`smoothstep` is the single most-used function in shader art. Use it to soften an edge:

```glsl
float circle = 1.0 - smoothstep(0.45, 0.5, length(st));
// 0 outside radius 0.5, 1 inside 0.45, smooth in the 0.05 band — soft-edged white circle
```

## `mix` — Linear Interpolation

```glsl
vec3 a = vec3(1, 0, 0);  // red
vec3 b = vec3(0, 0, 1);  // blue
vec3 c = mix(a, b, t);    // t=0 → red, t=1 → blue
```

Combine with `smoothstep` to mix two values based on a soft threshold:

```glsl
vec3 color = mix(skyColor, sunColor, smoothstep(0.0, 1.0, sunMask));
```

## Mouse-Following Soft Circle

The "hello world" of interactive shaders.

```glsl
uniform vec2 u_resolution;
uniform vec2 u_mouse;       // pixels, origin top-left (set in JS — see note below)

void main() {
  vec2 fragPos = gl_FragCoord.xy;
  vec2 mousePos = vec2(u_mouse.x, u_resolution.y - u_mouse.y);  // flip Y if mouse is top-origin
  float d = distance(fragPos, mousePos);
  float radius = 60.0;
  float soft = 1.0 - smoothstep(radius - 10.0, radius, d);
  outColor = vec4(vec3(soft), 1.0);
}
```

In JS:

```javascript
canvas.addEventListener("mousemove", (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * devicePixelRatio;
  const y = (e.clientY - rect.top) * devicePixelRatio;
  gl.uniform2f(u_mouse, x, y);
});
```

The Y-flip matters: DOM events have origin top-left, `gl_FragCoord` has origin bottom-left. Either flip on the JS side or in the shader — pick one and document it.

## Hash and Value Noise

Random in a shader uses a deterministic hash, not a real RNG. The standard one-liner:

```glsl
float hash(vec2 p) {
  return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}
```

Value noise is bilinear-interpolated hash on a grid:

```glsl
float valueNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);   // Smoothstep curve for interpolation
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
```

Cheap, blocky look — fine for fire / clouds at low scale, less good for fine detail.

## Simplex / Perlin Noise

For smoother, more organic noise, drop in [Ashima Arts' WebGL noise](https://github.com/ashima/webgl-noise) (`snoise2`, `snoise3`, `cnoise2`, etc.) — copy-paste a 50-line GLSL function and you have proper simplex noise. Bundle it as a string constant in your JS or load via `fetch`. Don't try to derive simplex from scratch — it's well-trodden territory and the reference implementations are correct.

## Fractal Brownian Motion (fBM)

Layer multiple octaves of noise to get clouds, terrain, fire:

```glsl
float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 5; i++) {
    v += a * valueNoise(p);
    p *= 2.0;
    a *= 0.5;
  }
  return v;
}
```

Each octave doubles the frequency and halves the amplitude. 4–6 octaves usually looks great; more gets expensive without obvious gain.

## Signed Distance Fields (SDFs)

A signed distance function returns the distance from a point to a shape — negative inside, positive outside, zero on the boundary. Combine them with `min` (union), `max(-a, b)` (subtraction), and smooth variants (`smin`) to build complex shapes from primitives.

```glsl
float sdCircle(vec2 p, float r) {
  return length(p) - r;
}

float sdBox(vec2 p, vec2 b) {
  vec2 d = abs(p) - b;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

float opUnion(float a, float b)        { return min(a, b); }
float opSubtract(float a, float b)     { return max(-a, b); }
float opIntersect(float a, float b)    { return max(a, b); }
```

Render an SDF as a filled-with-soft-edge shape:

```glsl
float d = sdBox(st, vec2(0.3, 0.2));
float mask = 1.0 - smoothstep(0.0, 0.01, d);
vec3 color = mix(bgColor, fgColor, mask);
```

[Inigo Quilez's SDF reference](https://iquilezles.org/articles/distfunctions/) is the canonical catalog of 2D and 3D primitives.

## Polar Coordinates

Convert Cartesian to polar for radial patterns:

```glsl
vec2 toPolar(vec2 p) {
  return vec2(length(p), atan(p.y, p.x));
}
```

Spirals, sunburst, kaleidoscope effects all live in polar space. Combine with `fract(theta * N)` to make N-fold symmetry.

## Color

Hue rotation via HSV ↔ RGB:

```glsl
vec3 hsv2rgb(vec3 c) {
  vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
```

`vec3(time * 0.1, 0.8, 0.9)` cycles through a saturated spectrum over time.

For palettes, Inigo Quilez's [palette generator](https://iquilezles.org/articles/palettes/):

```glsl
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
  return a + b * cos(6.28318 * (c * t + d));
}
```

Plug in palette constants from [a palette gallery](http://dev.thi.ng/gradients/) — instant good-looking gradients.

## Composing — A Cheap Lava Lamp

Stacking the above:

```glsl
void main() {
  vec2 st = (gl_FragCoord.xy * 2.0 - u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  vec2 q = st + vec2(0.0, u_time * 0.1);
  float n = fbm(q * 3.0);                                  // turbulence
  vec3 color = palette(n + u_time * 0.05,
                       vec3(0.5), vec3(0.5),
                       vec3(1.0), vec3(0.0, 0.33, 0.67));
  outColor = vec4(color, 1.0);
}
```

Two functions, one palette, and you have something to look at. The whole vocabulary of fragment-shader art is variations on this pattern.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Shader output looks fine on square canvas, stretches on rectangular | You used `gl_FragCoord.xy / u_resolution.xy` (which is per-axis 0..1, stretching). Use the aspect-corrected `st` form for shapes that should stay round. |
| Mouse uniform's Y is upside down | DOM events are top-origin; `gl_FragCoord` is bottom-origin. Flip on the JS side: `y = canvas.height - e.clientY * dpr`. |
| `hash` returns banded patterns at scale | The classic `sin/dot/fract` hash is low-quality at high frequencies. For better, use a real simplex noise implementation. |
| fBM looks "stripy" or "swirly" instead of organic | Frequency scaling is integer (`p *= 2.0`); pick non-integer (`p = p * 2.0 + vec2(1.7, 0.3)`) to break alignment artifacts. |
| SDF edge looks pixelated | The `smoothstep` band is in shader units. Use `fwidth(d)` to get per-pixel derivative width: `mask = 1.0 - smoothstep(0.0, fwidth(d), d)`. |
| Color palette comes out gray | One of the cosine arguments is overwhelming. The palette formula is sensitive — start with `iq`'s example values and tweak from there. |
| Animation is frame-rate dependent | Drive everything off `u_time` (in seconds), not a per-frame counter. Update from `performance.now() / 1000` in JS. |
