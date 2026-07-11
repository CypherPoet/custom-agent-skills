# Export

GLTF, FBX, OBJ, USD pipelines. Export is almost always a headless-CLI job — the MCP times out on real exports.

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
    export_apply=False,
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
| `export_apply` | `False` | `True` only if you have to (Array/Mirror modifiers can balloon file size) |
| `export_yup` | `True` | Leave on — most runtimes expect Y-up |
| `export_animations` | `True` | `False` for static scenes |
| `export_skins` | `True` | `False` if no rigs present |
| `export_morph` | `True` | `False` if no shape keys |
| `export_cameras` | `False` | `True` for products / virtual tours |
| `export_lights` | `False` | `True` if lights are part of the asset (Filament etc.) |
| `export_extras` | `False` | `True` if you've stored custom properties on objects you want preserved |
| `export_image_format` | `AUTO` | `JPEG` if you can't tolerate PNG file size |

### The modifier-apply trap

`export_apply=True` bakes the modifier stack into the exported mesh. Two reasons to think twice:

- **Array / Mirror modifiers explode size.** A 1MB mesh with an Array×50 becomes ~50MB after baking. Better: export with `export_apply=False` and replicate at runtime.
- **Subsurf modifiers exponentially grow vertex counts.** Level 3 = 64× the polys of level 0.

If the runtime doesn't honor modifiers, you have to bake — but consider whether the runtime should grow up first.

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

Verified on Blender 5.1: four objects with `WheelsRolling` tracks export as a single
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

The newer `wm.obj_export` (in Blender 3.4+) is faster and more accurate than the older `export_scene.obj`.

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

def pre_export_audit():
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
        # Suspicious modifiers (Array/Mirror with high counts)
        for mod in obj.modifiers:
            if mod.type == 'ARRAY' and getattr(mod, 'count', 0) > 20:
                issues.append(f"{obj.name}: Array modifier count={mod.count} — consider runtime instancing")
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

- [Blender Manual: GLTF 2.0 Export](https://docs.blender.org/manual/en/5.1/addons/import_export/scene_gltf2.html)
- [Blender Manual: FBX Export](https://docs.blender.org/manual/en/5.1/addons/import_export/scene_fbx.html)
- [Blender Manual: OBJ Export](https://docs.blender.org/manual/en/5.1/files/import_export/obj.html)
- [Blender Manual: USD Export](https://docs.blender.org/manual/en/5.1/files/import_export/usd.html)
- [glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
