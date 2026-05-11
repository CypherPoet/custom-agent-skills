# MCP Workflow

How to drive Blender productively through the official MCP server. Blender is a stateful, single-user application; the MCP gives Claude three primary capabilities — `get_scene_info`, `execute_python`, and `screenshot` — plus whatever the addon's asset integrations expose. Everything else is `bpy` Python through `execute_python`.

The single biggest mistake under MCP is treating it like a stateless REPL. Blender has no preview-of-pending-edits, no cheap rollback, no protection against context drift between calls. The patterns below exist to compensate.

## The loop, in detail

### 1. Read

Before any mutation, get a compact picture of what's there. Don't dump everything — Blender scenes can have thousands of objects. Ask for what's relevant to the task.

A reusable scene-summary snippet (paste into `execute_python`):

```python
import bpy, json

def summarize_scene():
    scene = bpy.context.scene
    out = {
        "active": bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None,
        "selected": [o.name for o in bpy.context.selected_objects],
        "mode": bpy.context.mode,
        "frame": scene.frame_current,
        "engine": scene.render.engine,
        "objects": [],
    }
    for obj in scene.objects:
        out["objects"].append({
            "name": obj.name,
            "type": obj.type,
            "hidden": obj.hide_get(),
            "location": list(obj.location),
            "modifiers": [m.type for m in obj.modifiers] if hasattr(obj, "modifiers") else [],
            "materials": [s.material.name for s in obj.material_slots if s.material] if hasattr(obj, "material_slots") else [],
        })
    return out

print(json.dumps(summarize_scene(), indent=2))
```

For larger scenes, project to just the slice you need (e.g. `[o.name for o in bpy.data.objects if o.type == 'MESH']`).

### 2. Propose

Before running code, say what you're about to do and why, in one or two sentences. This isn't ceremony — it's a forcing function. If the proposal is hard to write, the plan probably isn't ready.

### 3. Execute

Run a `bpy` script via `execute_python`. Keep individual scripts short and focused — one logical change per call. Long scripts are harder to debug when something goes sideways, and you lose the chance to verify between sub-steps.

### 4. Verify

For visual changes (materials, lighting, geometry, camera), call `screenshot`. For data-only changes (renames, property assignments, modifier additions), re-read with a targeted inspection script.

Don't skip verification. The MCP runs Python in-process, so a script that half-completes leaves visible state in the scene that you'd otherwise miss.

### 5. Iterate

If verification fails:

- Prefer **rebuilding from a known-good read** over `bpy.ops.ed.undo()`. Undo under scripts is unreliable — see `errors.md`.
- If you applied a modifier or made a destructive change, the scene may not be cleanly recoverable. Tell the user; offer to revert by reloading the .blend file (they'll need to do that themselves).

## Idempotent-edit patterns

Scripts that can re-run safely save you from half-completed-state hell. Some patterns:

- **Existence-check before create.** `obj = bpy.data.objects.get("Table") or bpy.data.objects.new("Table", mesh)` rather than blindly `bpy.data.objects.new(...)`.
- **Use stable names, not auto-numbered ones.** Blender appends `.001`, `.002` on conflicts. Always set names explicitly when creating data so re-runs find the same object.
- **Clear-then-rebuild for node trees.** When setting up a material's node tree, `nodes.clear()` first, then build. Trying to "patch" an existing tree is fragile.
- **Don't trust the active object across calls.** It can shift if the user clicks something between MCP calls. Set it explicitly: `bpy.context.view_layer.objects.active = bpy.data.objects["X"]`.

## Chunking large operations

If an operation might exceed the MCP timeout (~15–30 seconds), split it. Examples:

- Iterating over thousands of objects → process in batches; emit progress via `print()` and check the log between batches.
- Building a complex scene → one phase per call (geometry, then materials, then lighting), each verified before the next.
- Anything that bakes, exports, or renders → escape to the headless CLI (next section).

## The headless CLI escape hatch

For long-running ops, drop out of the MCP and run Blender directly:

```bash
blender --background path/to/file.blend --python script.py
```

Or for one-liners:

```bash
blender --background path/to/file.blend --python-expr "import bpy; bpy.ops.export_scene.gltf(filepath='/tmp/out.glb', use_selection=False, export_apply=False)"
```

After the CLI run finishes, the MCP can re-inspect the scene (or the output file) to verify. The CLI is part of the loop, not an exit from it.

Common headless tasks:

| Task | Why headless |
|---|---|
| GLTF / FBX / USD export | MCP timeout |
| Texture / lightmap baking | MCP timeout, may need GPU access |
| Full-quality renders | Always; rendering through MCP is a footgun |
| Batch processing many .blend files | Loop in shell, not in `bpy` |

When writing `script.py` for headless use, remember:

- `bpy.context.scene` may be `None` immediately after launch — use `bpy.data.scenes[0]` or `bpy.context.window.scene` if needed.
- No viewport, so anything depending on `bpy.context.area.type` will fail.
- `print()` lands in the terminal; that's your only feedback channel.

## Handling large output

`execute_python` returns whatever you `print()`. If you dump a megabyte of scene JSON, the conversation gets unwieldy. Patterns:

- **Slice before printing.** `print(json.dumps(out["objects"][:50], indent=2))` instead of all of them.
- **Save to a file, then read.** Write JSON to `/tmp/scene.json`, then read it back via the MCP if needed.
- **Aggregate, don't enumerate.** `print(f"{len(meshes)} meshes, {sum(len(m.data.polygons) for m in meshes)} polys")` is often what you actually wanted.

## When the MCP misbehaves

Symptoms and first checks:

- **Timeout.** The script ran too long. Either chunk it or escape to headless.
- **Connection refused.** The MCP addon isn't running in Blender. Have the user check Preferences → Add-ons → Blender MCP → enabled.
- **Script errors with no useful trace.** `execute_python` may swallow some details. Wrap risky code in `try/except` and `print(traceback.format_exc())` for visibility.
- **Edits don't appear visible.** The depsgraph hasn't been re-evaluated. Try `bpy.context.view_layer.update()` or `bpy.context.evaluated_depsgraph_get()` before screenshotting.

See `errors.md` for the full table.

## Sources

- [Blender Python API Reference](https://docs.blender.org/api/5.1/) — the canonical source for `bpy` calls.
- [Blender MCP Server (lab page)](https://www.blender.org/lab/mcp-server/).
