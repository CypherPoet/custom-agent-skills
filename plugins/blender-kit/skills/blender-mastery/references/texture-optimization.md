# Texture Optimization

Cutting GLB / GLTF size and GPU memory for web targets. The pipeline: `gltf-transform` (Node CLI) handles the post-export work — Blender doesn't optimize textures directly.

## Table of Contents

| Section | Covers |
|---|---|
| [The web target reality](#the-web-target-reality) | A raw Blender GLTF export at 4K textures is typically 20-50 MB |
| [VRAM budgets by target](#vram-budgets-by-target) | Typical VRAM budgets and texture-size ranges for low-end mobile, mobile and web, desktop web, and native desktop |
| [What one texture actually costs](#what-one-texture-actually-costs) | Pick a resolution and a format from the sections above and you have implicitly spent a fixed number of bytes |
| [Setup](#setup) | Installing and verifying the glTF Transform CLI |
| [The pipeline (steps you actually want)](#the-pipeline-steps-you-actually-want) | Inspect, resize, convert textures to WebP, apply Draco last, and verify the optimized glTF |
| [What NOT to do](#what-not-to-do) | Optimization commands and texture workflows that damage or inflate assets |
| [KTX2 / Basis Universal — when WebP isn't enough](#ktx2--basis-universal--when-webp-isnt-enough) | WebP saves download bandwidth but textures get decoded back to RGBA8 in VRAM |
| [Texture atlasing](#texture-atlasing) | When a model has many small textures, atlasing combines them into one larger texture — fewer draw calls, often smaller total size |
| [Texture format quick reference](#texture-format-quick-reference) | Texture formats, their best use cases, and important constraints |
| [When the size still won't budge](#when-the-size-still-wont-budge) | Common culprits, in order of likely impact |
| [Sources](#sources) | Authoritative references that ground this guidance |

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

## What one texture actually costs

Pick a resolution and a format from the sections above and you have implicitly spent a fixed number of bytes. Check that number against your **file** budget before committing to it — "2048² is fine for desktop web" and "the file should come in under 5 MB" are each reasonable in isolation and can be impossible together.

Block-compressed formats are content-independent in VRAM, so these are exact:

| Format | Bytes/texel in VRAM | 512² | 1024² | 2048² | 4096² |
|---|---|---|---|---|---|
| RGBA8 (what PNG/JPEG/WebP decode to) | 4 | 1 MiB | 4 MiB | 16 MiB | 64 MiB |
| KTX2 UASTC → BC7 / ASTC 4×4 | 1 | 256 KiB | 1 MiB | 4 MiB | 16 MiB |
| KTX2 ETC1S → BC1 / ETC1 | 0.5 | 128 KiB | 512 KiB | 2 MiB | 8 MiB |

A full mip chain adds about a third on top of every figure.

On **disk**, the story splits:

- **UASTC** stores those same block bytes with Zstd supercompression on top. Expect a modest reduction, not a transformative one — a 2048² UASTC map is still multiple MB in the file. Encoding with RDO enabled (`--rdo`) trades a little quality for a meaningfully better ratio.
- **ETC1S** stores a Basis codebook plus entropy coding rather than raw blocks, so its on-disk size is much smaller than its VRAM figure and genuinely content-dependent. It is the right pick for photographic or noisy maps; avoid it for crisp lettering, logos, and hard-edged decals, where its artifacts are most visible.
- **PNG / JPEG / WebP** are content-dependent on disk and tell you nothing about VRAM. This is the trap worth internalizing: a 2048² map that compresses to a 300 KB WebP still occupies 16 MiB of VRAM once decoded.

Worked example: a model with three 2048² UASTC maps has spent ~12 MiB of VRAM and several MB of file before a single triangle is counted. If the file budget is 5 MB, the resolution has to come down, the map count has to come down, or the budget was wrong.

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
3. **Animation tracks for unused bones** — `gltf-transform resample` losslessly deduplicates redundant keyframes.
4. **Per-vertex color where a material color would do** — strip with `gltf-transform color`.

## Sources

- [glTF-Transform documentation](https://gltf-transform.dev/)
- [KTX2 format spec](https://www.khronos.org/ktx/)
- [Draco mesh compression](https://google.github.io/draco/)
