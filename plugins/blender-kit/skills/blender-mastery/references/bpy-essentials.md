# `bpy` Essentials

Cross-cutting Python patterns for working with `bpy` through the MCP. The themes that come up in almost every Blender script: data API vs operators, context, modes, depsgraph, undo, and naming.

## Table of Contents

| Section | Covers |
|---|---|
| [Data API vs operators](#data-api-vs-operators) | Direct, context-independent `bpy.data` access versus context-sensitive `bpy.ops` actions, with selection rules and task examples |
| [Context: where operators get tripped up](#context-where-operators-get-tripped-up) | Operators read `bpy.context` to know what to act on |
| [The select-active-edit triad](#the-select-active-edit-triad) | Three closely-related but distinct concepts that scripts routinely confuse |
| [Modes](#modes) | `bpy.context.mode` is one of `OBJECT`, `EDIT_MESH`, `EDIT_CURVE`, `SCULPT`, `POSE`, `WEIGHT_PAINT`, `TEXTURE_PAINT`, etc |
| [Depsgraph: when "current state" lies](#depsgraph-when-current-state-lies) | `bpy.data.objects[X].matrix_world` reflects the un-evaluated transform |
| [Undo behavior under scripts](#undo-behavior-under-scripts) | Undo in `bpy` is unreliable when called from `execute_blender_code` |
| [Naming and uniqueness](#naming-and-uniqueness) | Blender enforces unique names within each data block type |
| [Modifier budgeting (don't bake what you don't have to)](#modifier-budgeting-dont-bake-what-you-dont-have-to) | Keeping reusable modifiers live instead of baking geometry unnecessarily |
| [Common helper snippets](#common-helper-snippets) | Find every Principled BSDF in the scene, Iterate every mesh and report poly count |
| [Sources](#sources) | Authoritative references that ground this guidance |

## Data API vs operators

The single most important bpy distinction. Blender exposes two layers:

- **`bpy.data.*`** — the data API. Direct access to objects, meshes, materials, etc. Stateless, doesn't depend on selection or active object.
- **`bpy.ops.*`** — operators. Mirror of UI actions. Depend on context (active object, selection, mode, area) and can fail with `Operator … poll() failed` when context isn't right.

**Default to the data API.** Use operators only when nothing in the data API can do the job (export, bake, modifier-apply, mesh boolean), or when the operator is the canonical entry point for a complex multi-step internal pipeline.

| Task | Data API | Operator |
|---|---|---|
| Move an object | `obj.location.z = 2` | `bpy.ops.transform.translate(value=(0,0,2))` |
| Rename | `obj.name = "Table"` | (no equivalent) |
| Add a modifier | `obj.modifiers.new("Subdiv", "SUBSURF")` | `bpy.ops.object.modifier_add(type='SUBSURF')` |
| Apply a modifier | (no clean equivalent) | `bpy.ops.object.modifier_apply(modifier="Subdiv")` |
| Delete an object | `bpy.data.objects.remove(obj, do_unlink=True)` | `bpy.ops.object.delete()` |
| Set a material | `obj.data.materials.append(mat)` | (no equivalent) |
| Export GLTF | (no equivalent) | `bpy.ops.export_scene.gltf(...)` |
| Bake | (no equivalent) | `bpy.ops.object.bake(type='AO')` |

The operator-only rows are the legitimate `bpy.ops` cases — those operators implement non-trivial logic that's not exposed as data.

## Context: where operators get tripped up

Operators read `bpy.context` to know what to act on. Under MCP, the context Claude sees is whatever Blender's main thread has at that moment — which is rarely exactly what your script assumes.

Symptoms: `RuntimeError: Operator bpy.ops.X.poll() failed`, or the operator runs but on the wrong object.

Fixes, in order of preference:

1. **Don't use the operator.** Switch to the data API.
2. **Set context explicitly before the call.**
   ```python
   bpy.context.view_layer.objects.active = bpy.data.objects["Cube"]
   bpy.data.objects["Cube"].select_set(True)
   bpy.ops.object.modifier_apply(modifier="Subdiv")
   ```
3. **Use `temp_override`** (the modern context-override API — pass kwargs matching `bpy.context` member names):
   ```python
   with bpy.context.temp_override(active_object=obj, selected_objects=[obj]):
       bpy.ops.object.modifier_apply(modifier="Subdiv")
   ```

   For preserving the rest of the current context, copy first then override:
   ```python
   override = bpy.context.copy()
   override["selected_objects"] = list(bpy.context.scene.objects)
   with bpy.context.temp_override(**override):
       bpy.ops.object.delete()
   ```

Older code that passed a context dict as a positional arg to operators (`bpy.ops.X(override_dict, ...)`) is no longer in the docs and shouldn't be used in new scripts.

## The select-active-edit triad

Three closely-related but distinct concepts that scripts routinely confuse:

- **Selected objects** — `bpy.context.selected_objects`. The set highlighted in the viewport.
- **Active object** — `bpy.context.view_layer.objects.active`. The "primary" object, drawn with a brighter outline. There's exactly one (or zero).
- **Edit-mode object** — only meaningful in edit mode. `bpy.context.edit_object`.

To make an object both selected and active:

```python
obj = bpy.data.objects["Cube"]
bpy.ops.object.select_all(action='DESELECT')   # or iterate and clear
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
```

Many `bpy.ops` operators silently use the active object; selection-aware ones use `selected_objects`. Read the operator docs to know which.

## Modes

`bpy.context.mode` is one of `OBJECT`, `EDIT_MESH`, `EDIT_CURVE`, `SCULPT`, `POSE`, `WEIGHT_PAINT`, `TEXTURE_PAINT`, etc. Most scripts assume `OBJECT` mode — verify and switch when you can't.

```python
if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
```

Mode switches require an active object of the right type — you can't enter edit mode without an active mesh. Sculpt mode requires the active object to be a mesh, etc.

See `scene-mental-model.md` for the full mode/data interaction.

## Depsgraph: when "current state" lies

`bpy.data.objects[X].matrix_world` reflects the *un-evaluated* transform. If you've animated something, applied a constraint, or driven a property, the data API still shows the source values — not the resolved result.

For evaluated state, use the depsgraph:

```python
deps = bpy.context.evaluated_depsgraph_get()
obj_eval = bpy.data.objects["Cube"].evaluated_get(deps)
print(obj_eval.matrix_world)  # the actual on-screen transform
```

When this matters: animations, constraints, drivers, geometry-nodes-modified meshes, instancing.

When it doesn't: pure data inspection (counting verts, listing modifiers), setting properties (you write to the source, not the evaluated copy).

## Undo behavior under scripts

Undo in `bpy` is unreliable when called from `execute_blender_code`:

- `bpy.ops.ed.undo()` may not roll back script-driven changes the way it rolls back UI actions.
- Multiple operations within one script call land as a single undo step (or zero) — there's no fine-grained history.
- After `bpy.ops.object.modifier_apply()`, there's no clean revert.

**Don't rely on undo as your safety net.** Prefer:

- Read-then-edit so you can rebuild from the read.
- Save the file before destructive ops (`bpy.ops.wm.save_mainfile()` if the user is okay with that).
- For exploratory work, use a duplicate: `bpy.ops.object.duplicate()` before mutating.

## Naming and uniqueness

Blender enforces unique names within each data block type. Conflicts auto-append `.001`, `.002`, etc.

Implications:

- Re-running a script that creates `bpy.data.objects.new("Cube", ...)` produces `Cube.001`, `Cube.002`, … unless you check first.
- After `bpy.ops.object.duplicate()`, the new object's name has `.001` appended — script paths that reference by name need to track the new name.
- Don't rely on guessed names (`bpy.data.objects["Cube.001"]`) being stable — better to track returned references.

Pattern for safe creation:

```python
def get_or_create_object(name, mesh):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
    return obj
```

## Modifier budgeting (don't bake what you don't have to)

Modifiers are typically displayed at the source resolution and only "baked into the mesh" when applied or exported with `export_apply=True`. This matters because:

- An Array modifier with count=50 turns 1MB of source mesh into ~50MB after apply — and you can't undo it cleanly.
- Subdivision Surface goes exponential: level 4 = 16x the polys.
- Boolean modifiers can produce non-manifold geometry when applied; the modifier itself often hides this until apply.

Rule: keep modifiers as modifiers as long as possible. Apply only when you must (some sculpt workflows, some export targets that don't honor modifiers). For GLTF, set `export_apply=False` and let the runtime instance arrays — see `export.md`.

## Common helper snippets

### Find every Principled BSDF in the scene

```python
import bpy
hits = []
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            hits.append((mat.name, node.name))
print(hits)
```

### Iterate every mesh and report poly count

```python
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"{obj.name}: {len(obj.data.polygons)} faces")
```

### Reset selection and make a single object active

```python
def make_only_active(obj):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
```

## Sources

- [Blender Python API: Data Access](https://docs.blender.org/api/5.2/info_quickstart.html)
- [Blender Python API: Context](https://docs.blender.org/api/5.2/bpy.context.html)
- [Blender Python API: Operators](https://docs.blender.org/api/5.2/bpy.ops.html)
- [Blender Python API: `Context.temp_override`](https://docs.blender.org/api/5.2/bpy.types.Context.html#bpy.types.Context.temp_override)
