# Texture Optimization

Cutting GLB / GLTF size and GPU memory for web targets. The pipeline: `gltf-transform` (Node CLI) handles the post-export work — Blender doesn't optimize textures directly.

## The web target reality

A raw Blender GLTF export at 4K textures is typically 20-50 MB. Web-friendly is sub-5MB. The gap closes through three independent dimensions:

| Dimension | Tool | Affects |
|---|---|---|
| **Texture pixel size** | `gltf-transform resize` | GPU memory + download size |
| **Texture compression** | `gltf-transform webp` / `ktx2` | Download size only (not GPU memory) |
| **Mesh compression** | `gltf-transform draco` | Download size only |

Always resize first. Compression alone leaves the GPU footprint the same — a 4K texture at WebP is still 4K in VRAM.

## VRAM budgets by target

Approximate. Real numbers depend on format and mip levels.

| Target | Typical budget | Texture size |
|---|---|---|
| Low-end mobile | 20-50 MB | 512² – 1024² |
| Mid mobile / web | 100-200 MB | 1024² – 2048² |
| Desktop web (good GPU) | 200-500 MB | 2048² – 4096² |
| Native desktop | unlimited | original |

## Setup

```bash
npm install -g @gltf-transform/cli
gltf-transform --version
```

## The pipeline (steps you actually want)

```bash
# 1. Inspect the baseline:
gltf-transform inspect input.glb

# 2. Resize textures down to 1024×1024 max:
gltf-transform resize input.glb resized.glb --width 1024 --height 1024

# 3. Convert to WebP at quality 85:
gltf-transform webp resized.glb webp.glb --quality 85

# 4. Apply Draco mesh compression (must be the LAST step):
gltf-transform draco webp.glb final.glb --quantize-position 14 --quantize-normal 10 --quantize-texcoord 12

# 5. Verify:
gltf-transform inspect final.glb
```

In practice this drops a 22MB raw export to ~1MB. Roughly: ~75% from texture resize, ~85% of remaining from WebP, ~50% of remaining from Draco.

## What NOT to do

- **Don't run `gltf-transform optimize`.** The bundled `optimize` command includes `simplify`, which destroys mesh detail. Use the individual commands above.
- **Don't apply Draco twice.** If you exported from Blender with Draco compression on, then ran `gltf-transform draco` again, the result is corrupt. Always export from Blender *without* Draco; let `gltf-transform` handle it.
- **Don't WebP if the runtime doesn't support it.** Older WebGL/three.js viewers may need PNG. Check the target.

## KTX2 / Basis Universal — when WebP isn't enough

WebP saves download bandwidth but textures get decoded back to RGBA8 in VRAM. KTX2 / Basis is a GPU-compressed format that saves *both* download size and VRAM:

```bash
gltf-transform uastc input.glb out.glb --level 4 --rdo 1.0
# or for ETC1S (smaller, lower quality):
gltf-transform etc1s input.glb out.glb --quality 128
```

Tradeoffs:

- KTX2 is supported by three.js, Babylon.js, model-viewer, and most modern WebGL/WebGPU runtimes. Older viewers may not decode it.
- UASTC is higher quality but larger; ETC1S is smaller but with visible artifacts on detailed textures.
- Encoding is slow (10-60s per texture for UASTC).

## Texture atlasing

When a model has many small textures, atlasing combines them into one larger texture — fewer draw calls, often smaller total size. Blender doesn't atlas during export, so it's a `gltf-transform`-time op:

```bash
gltf-transform palette input.glb out.glb --min 5 --block-size 4
```

This works for solid-color materials. For image-textured atlasing, you typically build the atlas in Blender via UV unwrap into a shared image first.

## Texture format quick reference

| Format | Use case | Notes |
|---|---|---|
| PNG | Lossless, broad support | Largest files |
| JPEG | Lossy color-only | No alpha |
| WebP | Lossy or lossless, good compression | Wide support; not in older runtimes |
| KTX2 (UASTC) | High-quality GPU-compressed | Slow to encode, smaller VRAM |
| KTX2 (ETC1S) | Low-bitrate GPU-compressed | Fast, visible artifacts on detail |

## When the size still won't budge

Common culprits, in order of likely impact:

1. **Unused textures** — materials reference images that aren't actually wired into a node. `gltf-transform prune` removes them.
2. **Modifier-baked Array/Mirror** — file has 50× the geometry it needs. Re-export with `export_apply=False`.
3. **Animation tracks for unused bones** — `gltf-transform optimize-animation` (without other transforms) trims redundant keyframes.
4. **Per-vertex color where a material color would do** — strip with `gltf-transform color`.

## Sources

- [glTF-Transform documentation](https://gltf-transform.dev/)
- [KTX2 format spec](https://www.khronos.org/ktx/)
- [Draco mesh compression](https://google.github.io/draco/)
