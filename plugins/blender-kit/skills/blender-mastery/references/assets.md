# Asset Integrations

These asset-provider integrations are **not** part of the official Blender Lab MCP server — they ship with the separate third-party community server [`ahujasid/blender-mcp`](https://github.com/ahujasid/blender-mcp). On the official server there are no provider tool calls: fetch the asset yourself (PolyHaven's API, a Sketchfab download, a Rodin/Hunyuan3D generation) and import it with `bpy` through `execute_blender_code`. Prefer that over hand-modeling whenever a suitable asset exists.

| Integration | What it gives you | Free? | Auth required? |
|---|---|---|---|
| **PolyHaven** | HDRIs, PBR texture sets, models — all CC0 | Yes | No |
| **Sketchfab** | Marketplace models (free + paid) | Mixed | Yes (API token) |
| **Hyper3D Rodin** | AI generation from text or image (cloud) | Credits | Yes (API key) |
| **Hunyuan3D** | AI generation from text/image (local) | Yes | No (runs locally) |

## Table of Contents

| Section | Covers |
|---|---|
| [PolyHaven: HDRIs, textures, models](#polyhaven-hdris-textures-models) | PolyHaven is the first-call source for environment lighting and surface materials |
| [Sketchfab: marketplace models](#sketchfab-marketplace-models) | Sketchfab requires an API token, configured in the third-party `blender-mcp` addon's settings |
| [Hyper3D Rodin: cloud AI generation](#hyper3d-rodin-cloud-ai-generation) | Generates from a text prompt and/or reference images |
| [Hunyuan3D: local AI generation](#hunyuan3d-local-ai-generation) | Local text-to-3D and image-to-3D generation with the Hunyuan3D Blender addon |
| [Picking the right integration](#picking-the-right-integration) | Blender asset-integration approaches matched to project needs |
| [Sources](#sources) | Authoritative references that ground this guidance |

## PolyHaven: HDRIs, textures, models

PolyHaven is the first-call source for environment lighting and surface materials. Everything is CC0, so it's safe in commercial work.

### HDRI environment

```python
import bpy

def load_hdri(filepath, strength=1.0):
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")

    env.image = bpy.data.images.load(filepath)
    bg.inputs["Strength"].default_value = strength

    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
```

The Mapping node is optional but useful — it lets you rotate the HDRI by adjusting `mapping.inputs["Rotation"].default_value`.

### PBR texture set

The PBR helper from `materials.md` handles the wiring. PolyHaven texture sets typically come with:

| File suffix | Maps to | Color space |
|---|---|---|
| `_diff_*` | Base Color | sRGB |
| `_rough_*` | Roughness | Non-Color |
| `_metal_*` | Metallic | Non-Color |
| `_nor_gl_*` | Normal (OpenGL convention) | Non-Color |
| `_ao_*` | Ambient Occlusion | Non-Color |
| `_disp_*` | Displacement | Non-Color |

Choose the GL-convention normal map (`_nor_gl_`) over the DirectX convention (`_nor_dx_`) — Blender uses the GL convention.

### Resolution choice

PolyHaven offers 1K, 2K, 4K, 8K. Default to 1K for prototyping and 2K for final. 4K+ assets need to be resized before web export — see `texture-optimization.md`.

Displacement maps don't survive GLTF export. Skip the displacement file or bake it into the normal map first.

## Sketchfab: marketplace models

Sketchfab requires an API token, configured in the third-party `blender-mcp` addon's settings — the official Blender Lab MCP add-on has no Sketchfab integration and no token field. After download, the model imports into the active scene.

### Post-import checklist

```python
import bpy, json

def audit_imported(prefix=None):
    """Return scale issues and material concerns for recently imported objects."""
    out = []
    for obj in bpy.context.scene.objects:
        if prefix and not obj.name.startswith(prefix):
            continue
        if obj.type != 'MESH':
            continue
        bb_size = max(obj.dimensions)
        materials = []
        for slot in obj.material_slots:
            if not slot.material:
                continue
            mat = slot.material
            if mat.use_nodes:
                node_types = {n.type for n in mat.node_tree.nodes}
                materials.append({"name": mat.name, "node_types": list(node_types)})
        out.append({
            "name": obj.name,
            "size_m": round(bb_size, 3),
            "verts": len(obj.data.vertices),
            "materials": materials,
        })
    return out

print(json.dumps(audit_imported(), indent=2))
```

Watch for:

- **Wrong scale.** Sketchfab models often come in at 1cm = 1m or similar. Bounding box size in meters tells you. If a "human" comes in at 0.018m tall, scale up by 100.
- **Diffuse BSDF instead of Principled.** Convert via the snippet in `materials.md`.
- **Missing textures.** Run `File → External Data → Report Missing Files` (no programmatic equivalent — surface this to the user).

## Hyper3D Rodin: cloud AI generation

Generates from a text prompt and/or reference images. Watertight meshes with PBR textures, but typically over-triangulated for runtime use.

### Post-generation cleanup

```python
import bpy

def cleanup_rodin_import():
    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH':
        return None

    # Rodin tends to come in with rotation already applied — verify by checking
    # the active rotation; if it's non-zero, apply transforms:
    if any(abs(v) > 0.001 for v in obj.rotation_euler):
        bpy.ops.object.transform_apply(rotation=True)

    # Rodin's poly counts are usually 50k-200k. Add a Decimate modifier;
    # don't apply (let runtime / export decide):
    if len(obj.data.polygons) > 30000:
        decim = obj.modifiers.new("Decimate", "DECIMATE")
        decim.ratio = min(0.3, 30000 / len(obj.data.polygons))
        print(f"Added decimate: target {len(obj.data.polygons) * decim.ratio:.0f} faces")

    return obj
```

Rodin textures export cleanly to GLTF — they're real image textures, not procedural. If the model needs to be web-ready, skip the decimate and instead use `gltf-transform` post-export — see `texture-optimization.md`.

## Hunyuan3D: local AI generation

Tencent's open-source model. Runs locally, requires substantial VRAM (16GB+ for full quality). Privacy-friendly and avoids API rate limits, but slower per generation than Rodin.

Output characteristics:

- Single mesh with a baked UV-unwrapped texture atlas — ideal for GLTF.
- Quality is similar to or better than Rodin for textured detail.
- Geometry can be denser; consider decimation for runtime use.

Inspection script (works for any imported asset, not just Hunyuan):

```python
import bpy, json

def material_atlas_summary(obj):
    out = []
    for slot in obj.material_slots:
        if not slot.material or not slot.material.use_nodes:
            continue
        textures = []
        for node in slot.material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                textures.append({
                    "image": node.image.name,
                    "size": list(node.image.size),
                    "filepath": node.image.filepath,
                    "colorspace": node.image.colorspace_settings.name,
                })
        out.append({"material": slot.material.name, "textures": textures})
    return out

print(json.dumps(material_atlas_summary(bpy.context.active_object), indent=2))
```

## Picking the right integration

| Need | Best fit |
|---|---|
| Environment lighting (HDRI) | PolyHaven |
| Generic surface material (wood, concrete, metal) | PolyHaven |
| Specific real-world object (a 1969 Mustang, a Toledo katana) | Sketchfab |
| Quick concept-to-3D iteration | Rodin |
| Final asset, privacy-sensitive, willing to wait | Hunyuan3D |
| The user has the asset already | Skip integrations; just import the file |

## Sources

- [PolyHaven licensing (CC0)](https://polyhaven.com/license)
- [Blender Manual: Image Textures and Color Management](https://docs.blender.org/manual/en/5.2/render/color_management/index.html)
