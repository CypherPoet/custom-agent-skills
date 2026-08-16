# MCP Workflow

How to drive Blender productively through the official MCP server (the lab extension, listed as **MCP** in Preferences ‣ Extensions). Its tool surface groups into: **code execution** (`execute_blender_code`), **scene inspection** (`get_objects_summary`, `get_object_detail_summary`, `get_blendfile_summary_*`), **screenshots & renders** (`get_screenshot_of_area_as_image`, `get_screenshot_of_window_as_image` / `_as_json`, `render_thumbnail_to_path`, `render_viewport_to_path`), **bundled-docs search** (`search_manual_docs`, `search_api_docs`, `get_python_api_docs`), and **UI navigation** (`jump_to_tab_by_name`, `jump_to_view3d_object_by_name`, …). `_for_cli` variants of the execution and blendfile-summary tools exist for the background/CLI flavor of the server. Everything not covered by a dedicated tool is `bpy` Python through `execute_blender_code`.

The single biggest mistake under MCP is treating it like a stateless REPL. Blender has no preview-of-pending-edits, no cheap rollback, no protection against context drift between calls. The patterns below exist to compensate.

## Table of Contents

| Section | Covers |
|---|---|
| [The loop, in detail](#the-loop-in-detail) | Read, propose, execute, verify, and iterate after Blender mutations |
| [Look it up: bundled docs search](#look-it-up-bundled-docs-search) | Searching Blender's bundled manual and Python API documentation |
| [Idempotent-edit patterns](#idempotent-edit-patterns) | Scripts that can re-run safely save you from half-completed-state hell |
| [Persistent helpers module](#persistent-helpers-module) | Sharing reusable Blender helper modules across `execute_blender_code` calls |
| [Fresh files without read_homefile](#fresh-files-without-read_homefile) | In-session file reloads are the one reliable way to lose the MCP mid-session |
| [Chunking large operations](#chunking-large-operations) | If an operation might exceed the MCP timeout (~15–30 seconds), split it |
| [The headless CLI escape hatch](#the-headless-cli-escape-hatch) | For long-running ops, drop out of the MCP and run Blender directly |
| [Handling large output](#handling-large-output) | `execute_blender_code` returns printed output in a `stdout` field |
| [When the MCP misbehaves](#when-the-mcp-misbehaves) | Timeout, connection, traceback, and dependency-graph checks for failed MCP operations |
| [Sources](#sources) | Authoritative references that ground this guidance |

## The loop, in detail

### 1. Read

Before any mutation, get a compact picture of what's there. `get_objects_summary` is the cheap first look; drop to a custom inspection script for anything it doesn't cover. Don't dump everything — Blender scenes can have thousands of objects. Ask for what's relevant to the task.

A reusable scene-summary snippet (run via `execute_blender_code`):

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

Run a `bpy` script via `execute_blender_code`. Keep individual scripts short and focused — one logical change per call. Long scripts are harder to debug when something goes sideways, and you lose the chance to verify between sub-steps.

### 4. Verify

For visual changes (materials, lighting, geometry, camera), take a screenshot (`get_screenshot_of_window_as_image`, or `get_screenshot_of_area_as_image` for one editor). For data-only changes (renames, property assignments, modifier additions), re-read with a targeted inspection script.

Don't skip verification. The MCP runs Python in-process, so a script that half-completes leaves visible state in the scene that you'd otherwise miss.

When the extension's screenshot tools misbehave (all observed on the official lab extension
v1.0.0 / Blender 5.1, and not re-tested since — the extension versions independently of
Blender, so treat these as symptoms to recognize rather than a current version claim):

- The area-screenshot tool can fail with `Invalid response … Unterminated string` regardless of any size cap — the bridge chokes on large payloads.
- `render_viewport_to_path`-style tools may ignore the requested output path and write to a sandboxed temp directory; the *returned* filepath in the result is the real one — copy the file out rather than assuming your path was honored.
- The robust fallback is an OpenGL viewport render written to a path you choose, then read from disk:

```python
scene = bpy.context.scene
scene.render.filepath = "/path/of/your/choice.png"
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.ops.render.opengl(write_still=True, view_context=True)
            break
```

Caveat: empty objects' display axes render into OpenGL captures — stray black lines poking out of meshes are usually pivots, not broken geometry.

### 5. Iterate

If verification fails:

- Prefer **rebuilding from a known-good read** over `bpy.ops.ed.undo()`. Undo under scripts is unreliable — see `errors.md`.
- If you applied a modifier or made a destructive change, the scene may not be cleanly recoverable. Tell the user; offer to revert by reloading the .blend file (they'll need to do that themselves).

## Look it up: bundled docs search

The server ships the full Blender manual and Python API reference as searchable text: `search_manual_docs` and `search_api_docs` (plus `get_python_api_docs` for a whole module page). They're offline and version-matched to the running Blender — more trustworthy than trained recall for exactly the things that break between releases: operator signatures, enum identifiers, property names, feature renames (`use_auto_smooth`, edge bevel weights, and the boolean solver names all changed across 4.x–5.x).

Reach for them when an operator errors with an unexpected-keyword or invalid-enum message, before writing code against an API you haven't verified this session, or when answering "how does X work" for a versioned feature. Queries are tokenized full-text with stop-words dropped — search `bevel harden normals`, not "how do I harden normals on a bevel". Re-query a promising hit with its `index` and a `context` value to widen it to the enclosing section.

## Idempotent-edit patterns

Scripts that can re-run safely save you from half-completed-state hell. Some patterns:

- **Existence-check before create.** `obj = bpy.data.objects.get("Table") or bpy.data.objects.new("Table", mesh)` rather than blindly `bpy.data.objects.new(...)`.
- **Use stable names, not auto-numbered ones.** Blender appends `.001`, `.002` on conflicts. Always set names explicitly when creating data so re-runs find the same object.
- **Clear-then-rebuild for node trees.** When setting up a material's node tree, `nodes.clear()` first, then build. Trying to "patch" an existing tree is fragile.
- **Don't trust the active object across calls.** It can shift if the user clicks something between MCP calls. Set it explicitly: `bpy.context.view_layer.objects.active = bpy.data.objects["X"]`.

## Persistent helpers module

`execute_blender_code` calls share one interpreter, so a module registered in `sys.modules` once
is importable in every later call — build a helper library in call #1 instead of re-sending
helper code each time:

```python
import sys, types

LIB_SRC = '''
import bpy, bmesh
def box(name, dims, loc=(0,0,0)):
    ...
'''
lib = types.ModuleType("scene_lib")
exec(LIB_SRC, lib.__dict__)
sys.modules["scene_lib"] = lib
```

Later calls just `import scene_lib`. The module survives across MCP calls but **not** file
reloads or Blender restarts — re-register after either.

## Fresh files without read_homefile

In-session file reloads are the one reliable way to lose the MCP mid-session. Two distinct
failure modes, both measured on 5.2.0/macOS `--background`:

- **`bpy.ops.wm.read_homefile(use_empty=True)` still crashes outright** — SIGABRT, exit 134.
  (On 5.1.1 the whole family crashed; by 5.2 plain `read_homefile()` and `open_mainfile()`
  no longer do.)
- **Surviving the reload isn't enough.** A successful `open_mainfile()` clears
  `bpy.app.timers` and every handler not marked `@persistent` — which is exactly what an
  addon server is built on, so the bridge dies even though Blender lives.

So the rule is unchanged, only better understood: never reload in-session. Instead:

1. Headless, clean the *default* scene and save — no reload involved:

```bash
blender --background --factory-startup --python-expr "
import bpy
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials, bpy.data.worlds):
    for block in list(coll):
        coll.remove(block)
bpy.ops.wm.save_as_mainfile(filepath='/path/to/new.blend')
"
```

2. Launch the GUI directly into it: `open -a Blender /path/to/new.blend` (macOS). The
   official lab MCP extension auto-starts its server on launch when the preference is set,
   so the MCP reconnects without user action.

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

`execute_blender_code` returns printed output in a `stdout` field — and, the cleaner channel for structured data, any JSON-serializable dict assigned to a variable named `result` comes back as the tool result. If you dump a megabyte of scene JSON either way, the conversation gets unwieldy. Patterns:

- **Slice before printing.** `print(json.dumps(out["objects"][:50], indent=2))` instead of all of them.
- **Save to a file, then read.** Write JSON to `/tmp/scene.json`, then read it back via the MCP if needed.
- **Aggregate, don't enumerate.** `print(f"{len(meshes)} meshes, {sum(len(m.data.polygons) for m in meshes)} polys")` is often what you actually wanted.

## When the MCP misbehaves

Symptoms and first checks:

- **Timeout.** The script ran too long. Either chunk it or escape to headless.
- **Connection refused.** The MCP addon isn't running in Blender. Have the user check Preferences → Add-ons → MCP → enabled.
- **Script errors with no useful trace.** `execute_blender_code` may swallow some details. Wrap risky code in `try/except` and `print(traceback.format_exc())` for visibility.
- **Edits don't appear visible.** The depsgraph hasn't been re-evaluated. Try `bpy.context.view_layer.update()` or `bpy.context.evaluated_depsgraph_get()` before screenshotting.

See `errors.md` for the full table.

## Sources

- [Blender Python API Reference](https://docs.blender.org/api/5.2/) — the canonical source for `bpy` calls.
- [Blender MCP Server (lab page)](https://www.blender.org/lab/mcp-server/).
