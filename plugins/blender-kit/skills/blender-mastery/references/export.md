# Export

GLTF, FBX, OBJ, USD pipelines. Export is almost always a headless-CLI job — the MCP times out on real exports.

## Table of Contents

| Section | Covers |
|---|---|
| [The export workflow (in order)](#the-export-workflow-in-order) | Inspect, verify, export, optimize, and validate in order |
| [GLTF — the web standard](#gltf--the-web-standard) | GLTF (`.glb` is the binary single-file form, `.gltf` is JSON+assets) is the right choice for web, AR/VR, and most game engines |
| [FBX — game engines, legacy DCC tools](#fbx--game-engines-legacy-dcc-tools) | Export settings for game engines and legacy digital-content-creation tools |
| [OBJ — geometry only](#obj--geometry-only) | Use OBJ when you need geometry only (no animation, simple materials) |
| [USD — film and pro pipelines](#usd--film-and-pro-pipelines) | USD is the right choice for asset interchange in pro pipelines (Houdini, Nuke, Solaris, Omniverse) |
| [Pre-export sanity script](#pre-export-sanity-script) | Run before any export, especially under MCP where the user can't see the viewport |
| [Validation after export](#validation-after-export) | Format-specific validation with `gltf-transform inspect` and runtime viewers for glTF, FBX, and USD exports |
| [Sources](#sources) | Authoritative references that ground this guidance |

## The export workflow (in order)

A reliable export looks like this:

1. **Inspect** — what's in the scene? Hidden objects, modifiers, materials, animations?
2. **Verify** — modifiers preserved or applied? UV maps present? Materials Principled-only?
3. **Export** — via headless CLI for anything non-trivial.
4. **Optimize** — texture resize, codec choice, mesh compression. See `texture-optimization.md`.
5. **Validate** — file size sane? Materials look right? Animations play in a runtime viewer?

Skipping the inspect / verify steps is how exports go silently wrong (modifiers baked unintentionally, materials reading as flat, missing textures).

## GLTF — the web standard

GLTF (`.glb` is the binary single-file form, `.gltf` is JSON+assets) is the right choice for web, AR/VR, and most game engines. Blender's exporter is mature.

### Headless export

```bash
blender --background scene.blend --python-expr "
import bpy
bpy.ops.export_scene.gltf(
    filepath='/tmp/scene.glb',
    export_format='GLB',
    use_selection=False,
    export_apply=True,   # modifiers build the mesh; False exports the base cage
    export_yup=True,
    export_animations=True,
    export_optimize_animation_size=True,
)
"
```

### Key kwargs and what they mean

| Kwarg | Default | When to change |
|---|---|---|
| `export_format` | `GLB` | `GLTF_SEPARATE` if you want JSON + textures as separate files |
| `use_selection` | `False` | `True` to export only selected objects |
| `use_visible` | `False` | `True` to skip anything hidden (the canonical "skip hidden objects" flag — preferred over post-filtering selection) |
| `export_apply` | `False` | `True` whenever modifiers build the final geometry — the default exports the **un-modified base mesh**. See the trap below |
| `export_yup` | `True` | Leave on — most runtimes expect Y-up |
| `export_animations` | `True` | `False` for static scenes |
| `export_skins` | `True` | `False` if no rigs present |
| `export_morph` | `True` | `False` if no shape keys |
| `export_cameras` | `False` | `True` for products / virtual tours |
| `export_lights` | `False` | `True` if lights are part of the asset (Filament etc.) |
| `export_extras` | `False` | `True` if you've stored custom properties on objects you want preserved |
| `export_image_format` | `AUTO` | `JPEG` if you can't tolerate PNG file size |

### The modifier traps — both directions

Modifiers are where exports most often go silently wrong, and the danger runs both ways.

**`export_apply=False` (the default) discards the stack entirely.** The exporter writes the base mesh as if the modifiers were never there. Grooves cut by an Array, a shell from Solidify, fillets from Bevel, smoothing from Subdivision — all gone, and the result still passes a name check, a triangle budget, and a file-size check. This is the more dangerous direction, because the export *succeeds*. It also directly contradicts `hard-surface.md`'s doctrine of staying parametric until hand-off: follow that advice, export with the default, and you ship the cage.

**`export_apply=True` bakes the stack, which can balloon the file.** An Array×50 turns a 1 MB mesh into ~50 MB; Subdivision level 3 is 64× the polygons of level 0.

Neither flag is a universal default. Decide by asking whether the modifiers *are* the final geometry:

| Situation | Setting |
|---|---|
| Modifiers build the shape you want in the file | `True` |
| Modifiers are viewport-only preview (e.g. a subsurf you don't want baked) | `False` |
| The mesh has shape keys you need exported | `False` — `True` blocks morph export |
| Heavy repetition you'd rather not bake | `True` **plus** real instancing — see below |

**"Replicate at runtime" is not what `export_apply=False` does.** Turning the flag off does not convert an Array modifier into instances; it leaves no record that the array ever existed, so you get neither baked geometry nor instancing. Actual instancing is a different mechanism: restructure the repetition as linked duplicates parented to an Empty and export with `export_gpu_instances=True`, which writes `EXT_mesh_gpu_instancing`. Runtimes that support the extension (three.js, Babylon.js, model-viewer) expand it into GPU instances, cutting both file size and VRAM, and the repetition stays described *inside* the asset rather than hardcoded in application code. Blender's exporter warns that instancing may omit multiple materials per instanced mesh, so check material assignment after export.

### Named animation clips for runtimes

Drivers don't export (glTF carries keyframes only), and the default animation export
flattens NLA into one anonymous clip. To ship a *named*, multi-object clip that runtimes
like Three.js can look up with `AnimationClip.findByName`:

1. Bake the driven motion to keyframes on each object (`obj.keyframe_insert(...)`), with
   `LINEAR` interpolation for seamless loops (e.g. exactly one wheel revolution).
2. Push each object's action onto an NLA track **with the same track name** on every
   object — same-named tracks merge into one glTF animation under that name.
3. Export with `export_animation_mode='NLA_TRACKS'`.

```python
track = obj.animation_data.nla_tracks.new()
track.name = "WheelsRolling"            # same name on every participating object
track.strips.new("WheelsRolling", 0, action)
obj.animation_data.action = None        # active actions would export separately
```

Verified on Blender 5.2: four objects with `WheelsRolling` tracks export as a single
`WheelsRolling` animation with four channels. Validate without a viewer by decoding the
GLB's JSON chunk (`animations[0].channels` → node names) — and for rotation *direction*,
decode the first few output-accessor quaternion keys rather than eyeballing a render.

## FBX — game engines, legacy DCC tools

```bash
blender --background scene.blend --python-expr "
import bpy
bpy.ops.export_scene.fbx(
    filepath='/tmp/scene.fbx',
    use_selection=False,
    apply_unit_scale=True,
    bake_space_transform=True,
    object_types={'ARMATURE', 'MESH', 'EMPTY'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_actions=True,
)
"
```

FBX-specific gotchas:

- **`bake_space_transform=True`** is usually correct. It converts Blender's Z-up to whatever target convention is set via `axis_forward` / `axis_up`.
- **`add_leaf_bones=False`** — Blender's FBX exporter adds invisible "leaf" bones at the end of each chain by default. Most game engines don't want them; turn off.
- **`bake_anim_use_all_actions=True`** — exports every Action in the file, not just the active one. Often what you want for character pipelines (multiple animation clips).
- **Materials in FBX are simplistic.** Don't expect PBR roundtrips through FBX — if material fidelity matters, GLTF or USD is a better choice.

## OBJ — geometry only

Use OBJ when you need geometry only (no animation, simple materials). Cleanest format for inter-DCC mesh exchange.

```bash
blender --background scene.blend --python-expr "
import bpy
bpy.ops.wm.obj_export(
    filepath='/tmp/mesh.obj',
    export_selected_objects=False,
    apply_modifiers=False,
    forward_axis='NEGATIVE_Z',
    up_axis='Y',
    export_uv=True,
    export_normals=True,
    export_materials=True,
)
"
```

`wm.obj_export` (Blender 3.4+) is the only OBJ exporter left: the older `export_scene.obj` is
no longer registered on 5.2, so stale scripts calling it fail. Note that `hasattr(bpy.ops.export_scene,
"obj")` still answers `True` — `bpy.ops` fabricates attributes on demand. To test whether an
operator really exists, call `.get_rna_type()` on it and catch the exception.

## USD — film and pro pipelines

USD is the right choice for asset interchange in pro pipelines (Houdini, Nuke, Solaris, Omniverse). Heavier than GLTF, more capable.

```bash
blender --background scene.blend --python-expr "
import bpy
bpy.ops.wm.usd_export(
    filepath='/tmp/scene.usd',
    selected_objects_only=False,
    visible_objects_only=True,
    export_animation=True,
    export_hair=False,
    export_uvmaps=True,
    export_normals=True,
    export_materials=True,
    generate_preview_surface=True,
)
"
```

`generate_preview_surface=True` produces UsdPreviewSurface materials, which is what most USD-aware viewers (Hydra, USDView, Storm) understand.

## Pre-export sanity script

Run before any export, especially under MCP where the user can't see the viewport:

```python
import bpy

def pre_export_audit(export_apply):
    """Pass the export_apply value you intend to use — the modifier check depends on it."""
    issues = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if not obj.visible_get():
            continue
        # No UV map?
        if not obj.data.uv_layers:
            issues.append(f"{obj.name}: no UV map")
        # Non-applied scale?
        if any(abs(s - 1.0) > 0.001 for s in obj.scale):
            issues.append(f"{obj.name}: non-unit scale {tuple(obj.scale)}")
        # Modifiers that won't survive the export at all (Armatures are excluded by the exporter)
        shaping = [m for m in obj.modifiers if m.type != 'ARMATURE']
        if shaping and not export_apply:
            names = ", ".join(f"{m.name}({m.type})" for m in shaping)
            issues.append(
                f"{obj.name}: {len(shaping)} modifier(s) will be DISCARDED by export_apply=False — {names}"
            )
        # Modifiers that will survive but multiply the mesh
        for mod in shaping:
            if export_apply and mod.type == 'ARRAY' and getattr(mod, 'count', 0) > 20:
                issues.append(f"{obj.name}: Array modifier count={mod.count} — consider EXT_mesh_gpu_instancing")
        # Materials using non-Principled shaders?
        for slot in obj.material_slots:
            if not slot.material or not slot.material.use_nodes:
                continue
            node_types = {n.type for n in slot.material.node_tree.nodes}
            if 'BSDF_PRINCIPLED' not in node_types and 'BSDF_DIFFUSE' in node_types:
                issues.append(f"{obj.name}: material '{slot.material.name}' uses Diffuse BSDF — may export flat")
    return issues
```

Surface the issues to the user before kicking off a long headless export.

## Validation after export

For GLTF, use `gltf-transform inspect` (CLI tool from `@gltf-transform/cli`):

```bash
gltf-transform inspect /tmp/scene.glb
```

Reports mesh counts, texture dimensions, animation tracks, file size breakdown.

For all formats, the cheapest sanity check is open-it-in-a-viewer:

- GLTF → [Babylon.js Sandbox](https://sandbox.babylonjs.com/) or [glTF Viewer](https://gltf-viewer.donmccurdy.com/)
- FBX → Unity / Unreal / Maya
- USD → USDView (ships with USD), Omniverse

## Sources

- [Blender Manual: GLTF 2.0 Export](https://docs.blender.org/manual/en/5.2/addons/scene_gltf2.html)
- [Blender Manual: FBX Export](https://docs.blender.org/manual/en/5.2/files/import_export/fbx_legacy.html)
- [Blender Manual: OBJ Export](https://docs.blender.org/manual/en/5.2/files/import_export/obj.html)
- [Blender Manual: USD Export](https://docs.blender.org/manual/en/5.2/files/import_export/usd.html)
- [glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
