---
name: blender-mastery
description: Use whenever the user mentions Blender, `bpy`, a `.blend` file, or asks to model / sculpt / rig / animate / texture / bake / render / export anything in Blender — even if they don't name the skill. Pro tips, `bpy` patterns, and Blender mental models covering modeling (including hard-surface modeling, booleans, and topology cleanup), materials, rigging, geometry nodes, rendering, asset import, and export — driven through the official Blender MCP server or the headless CLI.
---

# Blender Mastery

Pro tips, `bpy` patterns, and Blender mental models — primarily driven through the [official Blender MCP server](https://www.blender.org/lab/mcp-server/), with a headless-CLI escape hatch for long-running work. The body of this file holds the cross-cutting plays and routing table — domain-specific depth lives in `references/` and is loaded only when relevant.

## Setup

Requires Blender 5.1 or newer with the official Blender MCP addon enabled, and the MCP server registered in Claude Code's MCP config. The server runs inside Blender; this skill assumes Claude can reach its tools — `execute_blender_code` for running `bpy` code, `get_objects_summary` / `get_object_detail_summary` for scene inspection, the screenshot and viewport-render tools, and the bundled-docs search (`search_manual_docs`, `search_api_docs`). Reference content in this skill is written against the [Blender 5.2 Python API](https://docs.blender.org/api/5.2/) — **5.2 is the current LTS** (released July 2026, supported to July 2028). Most of it applies unchanged to 4.5 LTS and 5.0–5.1; where a version genuinely diverges, the reference files carry a dated stale-code trap rather than a silent assumption. Confirm the running version with `bpy.app.version` before trusting a version-sensitive snippet.

If the user hasn't set it up, point them at the lab page first and don't simulate the workflow.

## The MCP feedback loop

Drive Blender like a stateful collaborator, not a fire-and-forget terminal:

1. **Read** — call `get_objects_summary` or run a small `execute_blender_code` inspection script before mutating anything. Blender's scene state persists across calls and there's no preview-of-pending-edits.
2. **Propose** — describe the change in one or two sentences before running code.
3. **Execute** — `execute_blender_code` with `bpy` code. Prefer the data API over operators (see P2).
4. **Verify** — for visual edits, take a screenshot (`get_screenshot_of_window_as_image`) and look. For data edits, re-read the relevant `bpy.data` slice. Blind edits are how scenes drift.
5. **Iterate** — if verification fails, undo (or rebuild from the read state) and try again.

See `references/mcp-workflow.md` for inspection idioms, idempotent-edit patterns, and the headless escape hatch.

## Priority plays

Cross-cutting principles that apply across every Blender domain.

- **P1 — Read before write.** Always inspect with `bpy.data.*` or `bpy.context.*` before mutating. Scenes are stateful; edits are immediate; there is no diff preview. → `references/bpy-essentials.md`.
- **P2 — Prefer the data API over operators.** `bpy.data.objects["X"].location.z = 2` is robust; `bpy.ops.transform.translate(...)` depends on context overrides that fail unpredictably under MCP. Reach for `bpy.ops` only when the operation has no data-API equivalent (export, bake, modifier-apply). → `references/bpy-essentials.md`.
- **P3 — Mind modes and the active object.** Sculpt / edit / object mode determines which APIs work. The "active object" and "selected objects" are different concepts; many scripts break by confusing them. → `references/scene-mental-model.md`.
- **P4 — Materials are nodes.** `mat.use_nodes = True`, then build the `node_tree`. Don't touch legacy `mat.diffuse_color`-style props — they only apply when nodes are off. Always check `node.type == 'BSDF_PRINCIPLED'` before assuming Principled BSDF; imported materials may use Diffuse BSDF or stranger shaders. → `references/materials.md`.
- **P5 — Verify visually.** Take a screenshot (`get_screenshot_of_window_as_image`, or `render_viewport_to_path` for a clean viewport render) after non-trivial scene edits, especially for materials, lighting, and geometry-nodes work where the result depends on viewport evaluation.
- **P6 — Asset import beats hand-modeling.** PolyHaven for HDRIs and PBR textures (CC0), Sketchfab for specific models, Hyper3D Rodin or Hunyuan3D for AI generation. Hand-modeling a tree is rarely the right call when the integrations exist. → `references/assets.md`.
- **P7 — Look it up before guessing.** The MCP server ships the Blender manual and Python API reference and exposes `search_manual_docs` / `search_api_docs` over them — offline, and matched to the running Blender's version. Check operator signatures, enum identifiers, and feature behavior there before trusting trained recall; Blender's API breaks across versions (`use_auto_smooth`, edge bevel weights, boolean solver names all changed in the 4.x–5.x line). → `references/mcp-workflow.md`.

## When to escape the MCP

The MCP times out around 15–30 seconds per call. For long-running operations — most exports, full bakes, large procedural builds, real renders — drop to the headless CLI:

```bash
blender --background path/to/file.blend --python script.py
# or for one-liners:
blender --background path/to/file.blend --python-expr "import bpy; ..."
```

The MCP can inspect the result after the CLI run completes. Treat the CLI as an extension of the loop, not an exit from it.

## Reference routing

Load only the file(s) the current task touches. If unsure, `bpy-essentials.md` and `mcp-workflow.md` cover the cross-cutting basics.

| Asking about… | Read |
|---|---|
| Modeling, batch ops, scripting idioms, depsgraph, undo, modifier budgeting | `references/bpy-essentials.md` |
| Hard-surface modeling, modifier stacks, booleans, bevels, topology cleanup, manifold checks, shading artifacts on flat surfaces | `references/hard-surface.md` |
| Modes, data-blocks, units, parent/child, collections | `references/scene-mental-model.md` |
| Materials, shaders, PBR, node trees | `references/materials.md` |
| Procedural geometry, geometry nodes, attributes, fields | `references/geometry-nodes.md` |
| Rigging, armatures, IK/FK, drivers, fcurves, NLA, animation | `references/animation-rigging.md` |
| Sculpting, brushes, multires, dyntopo, retopo | `references/sculpting.md` |
| Cycles vs Eevee, render passes, baking (AO, normals, lightmaps), light setups | `references/rendering.md` |
| Video sequence editor, strips, transitions, audio sync | `references/vse.md` |
| PolyHaven, Sketchfab, Hyper3D, Hunyuan3D, post-import quirks | `references/assets.md` |
| GLTF / FBX / OBJ / USD export, web pipelines | `references/export.md` |
| Web-target texture sizing, format choice, Draco, atlasing | `references/texture-optimization.md` |
| MCP timeouts, mode-context traps, undo surprises, common bpy stack traces | `references/errors.md` |
| The MCP feedback loop itself, headless escape hatch, idempotent edits | `references/mcp-workflow.md` |
