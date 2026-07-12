# Buffers and Attributes

**Contents:** [The Pieces](#the-pieces) · [Uploading Data](#uploading-data) · [VAOs Are Mandatory in Practice](#vaos-are-mandatory-in-practice) · [`vertexAttribPointer`](#vertexattribpointer--the-most-misread-api) · [Interleaved vs Separate Buffers](#interleaved-vs-separate-buffers) · [Indexed Draws](#indexed-draws) · [Per-Instance Attributes (Instancing)](#per-instance-attributes-instancing) · [Cleanup](#cleanup) · [Common Mistakes](#common-mistakes)

## The Pieces

- **Buffer (VBO)**: a chunk of GPU memory. Holds vertex positions, colors, UVs — anything per-vertex. Created with `gl.createBuffer()`.
- **Index buffer (IBO)**: same thing, but bound to `ELEMENT_ARRAY_BUFFER` and holding vertex indices for `drawElements`.
- **Attribute**: a per-vertex shader input (`in vec3 a_position;` in GLSL ES 3.00). The GPU reads one element per vertex from the bound buffer.
- **Vertex Array Object (VAO)**: a recording of "which buffer is bound to which attribute, with what layout." Bind a VAO, then a draw call uses the recorded setup. Without VAOs you re-set all the pointers every frame — painful.

## Uploading Data

```javascript
const positions = new Float32Array([
   0,  0.5, 0,
  -0.5, -0.5, 0,
   0.5, -0.5, 0,
]);

const buffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
```

The **usage hint** in the third argument is just a hint — the GPU doesn't enforce it, but the driver may pick different memory:

- `gl.STATIC_DRAW` — upload once, draw many times. Most geometry.
- `gl.DYNAMIC_DRAW` — re-uploaded periodically.
- `gl.STREAM_DRAW` — uploaded once per draw, like particle positions.

Update a buffer in place with `bufferSubData`:

```javascript
gl.bufferSubData(gl.ARRAY_BUFFER, byteOffset, newData);
```

## VAOs Are Mandatory in Practice

```javascript
const vao = gl.createVertexArray();
gl.bindVertexArray(vao);

gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
const aPos = gl.getAttribLocation(program, "a_position");
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);

gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
const aCol = gl.getAttribLocation(program, "a_color");
gl.enableVertexAttribArray(aCol);
gl.vertexAttribPointer(aCol, 3, gl.FLOAT, false, 0, 0);

gl.bindVertexArray(null);   // Unbind so other setup doesn't pollute it.
```

Now every frame you only need:

```javascript
gl.useProgram(program);
gl.bindVertexArray(vao);
gl.drawArrays(gl.TRIANGLES, 0, 3);
```

Without a VAO, you'd call `enableVertexAttribArray` + `vertexAttribPointer` every frame. VAOs are a WebGL2 default; WebGL1 needs `OES_vertex_array_object` (almost universal — get it with `gl.getExtension('OES_vertex_array_object')`).

## `vertexAttribPointer` — The Most Misread API

```javascript
gl.vertexAttribPointer(
  location,    // From getAttribLocation
  size,        // Components per vertex (1, 2, 3, or 4)
  type,        // gl.FLOAT, gl.UNSIGNED_BYTE, gl.UNSIGNED_SHORT, gl.HALF_FLOAT, ...
  normalized,  // If type is int: divide by max-int to get 0..1? (true for color bytes)
  stride,      // Bytes between consecutive vertices. 0 = tightly packed.
  offset       // Bytes from the start of this attribute's first element.
);
```

The pointer **records the currently bound `ARRAY_BUFFER`**. There's no buffer argument — it's an implicit input. If you swap which buffer is bound and then call `vertexAttribPointer`, you've pointed the attribute at the new buffer.

`enableVertexAttribArray(location)` must be called for the attribute to actually be read. Without it, the attribute reads a constant value (set by `vertexAttrib4f`).

## Interleaved vs Separate Buffers

**Separate** (one buffer per attribute, tightly packed):

```
positions: [x0,y0,z0, x1,y1,z1, x2,y2,z2, ...]
colors:    [r0,g0,b0, r1,g1,b1, r2,g2,b2, ...]
```

```javascript
gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);

gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
gl.vertexAttribPointer(aCol, 3, gl.FLOAT, false, 0, 0);
```

**Interleaved** (single buffer, fields packed per-vertex):

```
combined: [x0,y0,z0,r0,g0,b0, x1,y1,z1,r1,g1,b1, ...]
```

```javascript
const stride = 6 * 4;  // 6 floats per vertex × 4 bytes per float
gl.bindBuffer(gl.ARRAY_BUFFER, combinedBuffer);
gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, stride, 0);
gl.vertexAttribPointer(aCol, 3, gl.FLOAT, false, stride, 3 * 4);   // 3 floats in
```

Interleaved is usually a small perf win — better cache locality, fewer driver state changes. Separate is easier when one attribute changes more often than the others (e.g., animated positions with static colors).

## Indexed Draws

For meshes with shared vertices (cubes, anything organic), use an index buffer:

```javascript
const indices = new Uint16Array([0, 1, 2,  0, 2, 3]);   // two triangles forming a quad
const ibo = gl.createBuffer();
gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo);
gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
```

The IBO binding **is part of VAO state**. Bind the VAO first, then bind the IBO — the VAO records it.

Draw with:

```javascript
gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);
```

Use `Uint16Array` (max 65,535 indices) for small meshes, `Uint32Array` for larger (requires `OES_element_index_uint` in WebGL1; default in WebGL2).

## Per-Instance Attributes (Instancing)

Add an attribute, then mark it as per-instance instead of per-vertex with `vertexAttribDivisor(loc, 1)`:

```javascript
gl.bindBuffer(gl.ARRAY_BUFFER, instanceOffsetBuffer);  // one vec3 per instance
gl.enableVertexAttribArray(aOffset);
gl.vertexAttribPointer(aOffset, 3, gl.FLOAT, false, 0, 0);
gl.vertexAttribDivisor(aOffset, 1);    // 1 = advance once per instance
```

Then `gl.drawArraysInstanced(gl.TRIANGLES, 0, vertCount, instanceCount)`. See [performance.md](./performance.md) for the full pattern.

A common gotcha: **divisor state lives on the VAO and persists**. If you re-use an attribute slot in a different VAO with `divisor=0` expected, set it explicitly.

## Cleanup

```javascript
gl.deleteBuffer(buffer);
gl.deleteVertexArray(vao);
```

GPU memory isn't garbage-collected. Track and dispose, especially in long-running apps that swap geometry.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Attribute reads zero / draws single point at origin | `enableVertexAttribArray` was never called for that location. |
| Attribute reads from the wrong buffer | `vertexAttribPointer` uses whatever is currently bound to `ARRAY_BUFFER`. Bind the right buffer **immediately** before the pointer call. |
| Setup works for one mesh, breaks when you add a second | You're not using VAOs (or you're polluting the same VAO with multiple meshes). One VAO per mesh-program pairing. |
| `drawElements` ignores the index buffer | The IBO binding has to happen *after* the VAO is bound, so it's captured. |
| Indexed draw with `Uint8Array` doesn't work | WebGL doesn't accept 8-bit indices. Use `Uint16Array` or `Uint32Array`. |
| Color bytes show up as garbage huge numbers | Forgot `normalized: true` for `UNSIGNED_BYTE` color data. Without normalization, byte 255 reads as 255.0, not 1.0. |
| Stride or offset wrong on interleaved buffer | Stride is bytes-per-vertex (not per-attribute). Offset is bytes from the start of the buffer to this attribute's first element. Always count bytes, not floats. |
| Instanced attribute draws solid blob | `vertexAttribDivisor` was never set (or set on the wrong VAO). The attribute is being read per-vertex, not per-instance. |
