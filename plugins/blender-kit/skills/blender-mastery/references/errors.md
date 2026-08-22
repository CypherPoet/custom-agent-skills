# Errors and Gotchas

Common failures when driving Blender via the MCP and writing `bpy` scripts. Organized by where they bite — MCP server, `bpy` runtime, modes/selection, materials, modifiers, textures, GLTF, render/bake.

## Table of Contents

| Section | Covers |
|---|---|
| [MCP server errors](#mcp-server-errors) | Script, socket, and export timeouts, unavailable add-ons, server-breaking file reloads, and noisy save handlers |
| [bpy runtime errors](#bpy-runtime-errors) | Operator context, missing node trees and shaders, deep hierarchy traversal, headless scenes, removed references, and Blender 5 action access |
| [Mode and selection traps](#mode-and-selection-traps) | Failures caused by the wrong mode, inactive objects, hidden state, or stale selections |
| [Material / node tree gotchas](#material--node-tree-gotchas) | Procedural export loss, non-Principled imports, color-space mismatches, and incorrect normal-map wiring |
| [Modifier and geometry traps](#modifier-and-geometry-traps) | Export-time geometry expansion, non-manifold booleans, viewport versus render subdivision, and stack ordering |
| [Texture path issues](#texture-path-issues) | Missing files, relative paths, resource packing, and texture-size problems |
| [GLTF name mapping](#gltf-name-mapping) | GLTF has stricter name rules than Blender |
| [GLTF export survival matrix](#gltf-export-survival-matrix) | What survives a Blender → GLTF export and what doesn't |
| [Draco re-encoding](#draco-re-encoding) | Corruption and simplification failures caused by unsafe Draco re-encoding |
| [Render and bake errors](#render-and-bake-errors) | UV, active-image, light, render-engine, and hardware settings that break renders or bakes |
| [Sources](#sources) | Blender GLTF export and Python operator documentation |

## MCP server errors

| Error | Cause | Fix |
|---|---|---|
| Script execution timeout | Python script ran longer than the MCP allows (~15–30s) | Split into smaller scripts, reduce iteration count, or escape to headless CLI (see `mcp-workflow.md`) |
| Connection refused / can't reach MCP | Blender MCP addon not running or wrong port | Have the user enable the addon (Preferences → Add-ons → MCP) and restart Blender |
| Socket timeout | Blender is busy (rendering, heavy compute) | Wait for current op to finish, then retry |
| Export timeout | Export operation exceeds MCP timeout | Always use the headless CLI for exports — never expect MCP to handle them inline |
| "Empty response from Blender", then connection refused | The script reloaded the file in-session. `bpy.ops.wm.read_homefile(use_empty=True)` still hard-crashes (SIGABRT, exit 134 — reproduced on 5.2.0/macOS `--background`; on 5.1.1 the whole family crashed). Even where it no longer crashes, a reload drops `bpy.app.timers` and non-`@persistent` handlers — the machinery an addon server runs on — so the MCP goes down with it | Never reload or open files through the MCP. Build fresh files headless and relaunch — see `mcp-workflow.md` "Fresh files without read_homefile" |
| Addon tracebacks on every save (e.g. a `save_post` handler error) | A broken user addon hooks save/depsgraph handlers | The save itself still succeeds — look for `Info: Saved` in the same output. Disable the addon, or pass `--factory-startup` for headless jobs so user addons never load |

## bpy runtime errors

| Error | Cause | Fix |
|---|---|---|
| `RuntimeError: Operator bpy.ops.X.poll() failed` | Operator's context preconditions aren't met (wrong active object, wrong mode, no selection) | Set context explicitly; better, switch to the data API. See `bpy-essentials.md` "Context" section |
| `AttributeError: 'NoneType' object has no attribute 'nodes'` | Material has `use_nodes = False` — `mat.node_tree` is None | Check `mat.use_nodes` before accessing `mat.node_tree.nodes` |
| `KeyError: 'Principled BSDF'` | Material uses a non-Principled shader | Iterate `node_tree.nodes` and filter by `node.type == 'BSDF_PRINCIPLED'`, don't index by name |
| `RecursionError` in hierarchy traversal | Deep parent chain hits Python's default recursion limit | Use iterative (stack-based) traversal, or `sys.setrecursionlimit` carefully |
| `bpy.context.scene` is `None` (in `--background`) | Headless launch hasn't fully initialized | Use `bpy.data.scenes[0]` or `bpy.context.window.scene` |
| `ReferenceError: ... has been removed` | Tried to use a Python object after `bpy.data.X.remove()` was called on it | Re-fetch by name, or store names not references when there's a chance of removal |
| `AttributeError: 'Action' object has no attribute 'fcurves'` | Blender 5.0 removed the legacy Action API (slotted actions, introduced in 4.4) | Read fcurves via `action.layers[].strips[].channelbags[].fcurves`; `obj.keyframe_insert()` still works unchanged. See `animation-rigging.md` "Slotted actions" |

## Mode and selection traps

| Symptom | Cause | Fix |
|---|---|---|
| Operator runs on the wrong object | Active object isn't what the script assumed | Set `bpy.context.view_layer.objects.active = obj` and `obj.select_set(True)` before the operator |
| `bpy.ops.object.mode_set` fails | Active object's type can't enter that mode (e.g. trying edit mode with no active mesh) | Set an appropriate active object first |
| Edit-mode changes don't persist | Forgot to `bmesh.update_edit_mesh(obj.data)` | Call update before exiting edit mode |
| Sculpt brush has no effect | Sculpt mode entered but no brush is active | `Paint.brush` is read-only since brushes became assets — activate one with `bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS', relative_asset_identifier=…)`. See `sculpting.md` |

## Material / node tree gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Procedural roughness / color disappears on export | Procedural nodes (Noise, Color Ramp value remapping, procedural Bump) don't export to GLTF | Bake to texture in Blender, or apply at runtime |
| Imported material looks flat | Import used Diffuse BSDF or another non-Principled shader | Convert to Principled BSDF (see `assets.md` for the snippet) |
| Texture is too dark / too bright | Color space mismatch — color textures need `sRGB`, data textures (roughness, normal) need `Non-Color` | Set `image.colorspace_settings.name = "Non-Color"` for data textures |
| Bump map doesn't show up | Bump node connected directly to Base Color rather than through Normal Map / Bump nodes | Wire `Image Texture (Non-Color)` → `Normal Map` → `Principled BSDF.Normal` |

## Modifier and geometry traps

| Symptom | Cause | Fix |
|---|---|---|
| File size explodes after export | Array / Mirror modifiers baked on export | `export_apply=False`; replicate at runtime |
| Boolean produces non-manifold geometry | Source meshes have overlapping faces or coincident vertices | Clean source meshes, or use newer Boolean solver settings |
| Subsurf level too low/high | Source level vs render level confusion | `mod.levels = 2` (viewport), `mod.render_levels = 3` (render) |
| Modifier order matters and you got it wrong | Modifier stack evaluates top-down | Reorder via `bpy.ops.object.modifier_move_up/down` or by manipulating `obj.modifiers` |

## Texture path issues

| Symptom | Cause | Fix |
|---|---|---|
| Textures missing from exported GLB | External file references with relative paths | `File → External Data → Pack Resources` before export |
| Double-nested path (`textures/textures/`) | Bad relative path | Fix via `bpy.data.images[name].filepath = '/correct/path'` |
| 4K texture causes mobile GPU OOM | Texture too large for target VRAM | Resize via `gltf-transform` post-export, or use a 1K source. See `texture-optimization.md` |

## GLTF name mapping

GLTF has stricter name rules than Blender. Names get transformed on export:

| Blender | GLTF |
|---|---|
| `RINGS ball L` | `RINGS_ball_L` |
| `Sphere.003` | `Sphere003` |
| `RINGS S ` (trailing space) | `RINGS_S_` |
| Two objects named `Cube` | `Cube` and `Cube_1` (or similar — order depends on iteration) |

Always reference exported names when writing runtime code that loads the GLB. Don't rely on Blender names matching.

## GLTF export survival matrix

What survives a Blender → GLTF export and what doesn't:

| Blender feature | Exports? | Notes |
|---|---|---|
| Flat roughness/metallic values | Yes | Direct mapping |
| Image textures (baseColor, normal, ORM) | Yes | Packed or referenced |
| Image roughness texture | Partially | Texture exports; Color Ramp remapping is lost |
| Procedural Noise Texture | No | Bake or runtime patch |
| Color Ramp value remapping | No | Range compression lost |
| Bump from Noise node | No | Bake to normal map |
| Baked normal maps | Yes | Standard GLTF |
| Alpha from texture | Yes | Via `alphaMode` |
| Emission | Yes | Via `emissiveFactor` / `emissiveTexture` |
| Metallic + roughness as separate textures | Yes | Combined into one ORM texture |
| Vertex colors | Yes | As `COLOR_0` |
| Custom UV layers | First two | Most viewers only honor `TEXCOORD_0` and `TEXCOORD_1` |
| Armatures and skinning | Yes | Up to 4 weights per vertex |
| NLA strips | As one combined animation (default) | With `export_animation_mode='NLA_TRACKS'`, same-named tracks across objects merge into one *named* clip — see `export.md` "Named animation clips" |
| Drivers | No | Bake to fcurves first |
| Constraints | No | Bake to fcurves first |
| Modifiers (default) | No | `export_apply=False`; runtime instances |
| Modifiers (with `export_apply=True`) | Yes, baked | File size cost — Array modifiers especially |

## Draco re-encoding

| Symptom | Cause | Fix |
|---|---|---|
| Corrupt mesh after `gltf-transform` | Draco applied twice (Blender exporter + gltf-transform) | Export *without* Draco, apply via gltf-transform as the final step |
| `gltf-transform optimize` destroys mesh | The bundled `optimize` command includes `simplify` | Use individual commands: `resize` → `webp` → `draco` |

## Render and bake errors

| Symptom | Cause | Fix |
|---|---|---|
| Bake produces black image | UV map missing, or no Image Texture node selected on the active material | Verify UVs unwrapped; create+select an Image Texture node before baking |
| Cycles render is incredibly slow | GPU not enabled, or device fallback to CPU | `bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'` (or `OPTIX`/`METAL`/`HIP`) |
| Eevee reflections look wrong | No Sphere light probe covering the area | Add a **Sphere** light probe — EEVEE's probe types are Sphere / Plane / Volume; Reflection Cubemaps are pre-4.2 naming. Sphere probes update dynamically; only **Volume** probes need baking |
| Render comes out completely black | No light source, or world background at zero | Add a Sun light or HDRI; check `bpy.data.worlds["World"].use_nodes` |

## Sources

- [Blender Manual: GLTF 2.0 export](https://docs.blender.org/manual/en/5.2/addons/scene_gltf2.html)
- [Blender Python API: bpy.ops](https://docs.blender.org/api/5.2/bpy.ops.html)
