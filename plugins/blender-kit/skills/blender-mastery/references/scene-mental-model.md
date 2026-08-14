# Scene Mental Model

The conceptual structure that makes `bpy` make sense. Most scripting bugs trace back to confusing two layers of this model — usually object vs mesh, or mode vs API surface.

## Table of Contents

| Section | Covers |
|---|---|
| [Data-blocks](#data-blocks) | Everything addressable by name lives in a `bpy.data.*` collection |
| [Object vs mesh data](#object-vs-mesh-data) | The most-confused pair. They share names by default, which makes the confusion easy |
| [Modes](#modes) | The mode determines which APIs work and what selection means |
| [Units and coordinate system](#units-and-coordinate-system) | Blender coordinates, metric defaults, and Euler-versus-quaternion rotation storage |
| [Parent/child and collections](#parentchild-and-collections) | Two organizational hierarchies, which behave differently |
| [Scenes and view layers](#scenes-and-view-layers) | A `.blend` file can have multiple scenes (rare) |
| [Linked vs appended data](#linked-vs-appended-data) | When pulling data from another .blend file (`File → Append` / `File → Link`) |
| [Depsgraph in one paragraph](#depsgraph-in-one-paragraph) | The dependency graph is what Blender uses to evaluate the scene each frame: it figures out |
| [Sources](#sources) | Authoritative references that ground this guidance |

## Data-blocks

Everything addressable by name lives in a `bpy.data.*` collection. Each entry is a "data-block". Common ones:

| Collection | What it holds | Example |
|---|---|---|
| `bpy.data.objects` | Scene objects (mesh containers, cameras, lights) | `bpy.data.objects["Cube"]` |
| `bpy.data.meshes` | Mesh data (vertices, edges, faces, uvs) | `bpy.data.meshes["Cube"]` |
| `bpy.data.materials` | Materials (with their node trees) | `bpy.data.materials["Wood"]` |
| `bpy.data.images` | Images (textures, render results) | `bpy.data.images["wood_diffuse.jpg"]` |
| `bpy.data.armatures` | Armature data (bones) | `bpy.data.armatures["Rig"]` |
| `bpy.data.actions` | Animation actions (fcurves) | `bpy.data.actions["Walk"]` |
| `bpy.data.cameras` | Camera data (lens, sensor) | `bpy.data.cameras["Camera"]` |
| `bpy.data.lights` | Light data (color, energy) | `bpy.data.lights["Sun"]` |
| `bpy.data.collections` | Collections (organizational groups) | `bpy.data.collections["Furniture"]` |
| `bpy.data.scenes` | Scenes (top-level containers) | `bpy.data.scenes["Scene"]` |
| `bpy.data.worlds` | World settings (background, ambient) | `bpy.data.worlds["World"]` |

## Object vs mesh data

The most-confused pair. They share names by default, which makes the confusion easy.

- **`bpy.data.objects["Cube"]`** is the *object*: a position in space, a parent, modifiers, material slots, visibility flags.
- **`bpy.data.meshes["Cube"]`** is the *mesh data*: the actual vertices, edges, faces, UVs.

An object references its mesh data through `obj.data`:

```python
obj = bpy.data.objects["Cube"]
mesh = obj.data        # bpy.data.meshes["Cube"]
print(len(mesh.vertices), len(mesh.polygons))
```

Multiple objects can share the same mesh data (via instancing or `bpy.ops.object.make_links_data()`). Editing the shared mesh affects all of them.

The same split applies to other types: `bpy.data.objects["Camera"]` (transform) wraps `bpy.data.cameras["Camera"]` (lens settings); `bpy.data.objects["Sun"]` wraps `bpy.data.lights["Sun"]`; etc.

## Modes

The mode determines which APIs work and what selection means.

| Mode | When it applies | What works |
|---|---|---|
| `OBJECT` | Default; manipulating whole objects | Most data API; transforms; modifiers |
| `EDIT_MESH` | Active object is a mesh; editing verts/edges/faces | `bmesh` API; mesh-edit operators |
| `EDIT_ARMATURE` | Active object is an armature; bone topology | Bone creation/deletion |
| `POSE` | Active object is an armature; posing bones | Bone constraints, IK, keyframes |
| `SCULPT` | Active object is a mesh; sculpt brushes | Sculpt operators |
| `WEIGHT_PAINT` | Mesh with armature; vertex weights | Weight-paint operators |
| `TEXTURE_PAINT` | Mesh with material/texture; painting on UVs | Texture paint operators |

Switch modes via `bpy.ops.object.mode_set(mode='EDIT')` (the active object must be a valid type).

Edit mode uses a separate API: `bmesh`. See `bpy.ops.object.mode_set(mode='EDIT')` followed by `bmesh.from_edit_mesh(obj.data)`. Most edit-mesh work is bmesh, not direct mesh-data manipulation.

## Units and coordinate system

- **Coordinate system:** Z-up, right-handed. (Many other tools — Unity, three.js, glTF — use Y-up. Conversions happen on import/export.)
- **Default unit:** meters. `obj.location.x = 1.0` means 1 meter.
- **Rotation storage:** Euler XYZ by default; quaternions if `obj.rotation_mode = 'QUATERNION'`. Read whichever attribute matches the current mode (`obj.rotation_euler` vs `obj.rotation_quaternion`).
- **Scene-level units:** `scene.unit_settings.system` ("METRIC" / "IMPERIAL") and `scene.unit_settings.scale_length` (meters per Blender unit). Most scenes leave these at defaults; scripts that bake measurements should respect them.

## Parent/child and collections

Two organizational hierarchies, which behave differently:

### Parenting

Affects transforms. A child object's world position = parent's world matrix × child's local matrix.

```python
child.parent = parent
child.matrix_parent_inverse = parent.matrix_world.inverted()  # avoids snap on parent
```

Set the inverse manually if you want the child to keep its current world position.

### Collections

Organizational only — they don't affect transforms. A collection is a named bag of objects; an object can be in multiple collections.

```python
coll = bpy.data.collections.new("Furniture")
bpy.context.scene.collection.children.link(coll)
coll.objects.link(obj)
```

Hidden collections hide everything in them (useful for grouping props). View-layer-level visibility is separate from collection-level visibility.

Old "groups" (pre-2.80) no longer exist; collections replaced them.

## Scenes and view layers

A `.blend` file can have multiple scenes (rare). Each scene has multiple view layers (more common — used for compositing render passes). For most scripts:

- `bpy.context.scene` is the current scene.
- `bpy.context.view_layer` is the current view layer.
- `bpy.context.view_layer.objects.active` is the active object (yes, it's per-view-layer).

When iterating "all objects in the scene," `scene.objects` returns the objects linked into the scene's master collection plus all nested collections. `bpy.data.objects` returns *every* object in the .blend file, including ones not linked into any scene.

## Linked vs appended data

When pulling data from another .blend file (`File → Append` / `File → Link`):

- **Append** copies the data-block into your file. Independent thereafter.
- **Link** creates a reference. The data lives in the source file; your file just points at it. Linked data is read-only locally; the source file is the source of truth.

Linked data has `.library` set; appended data has `.library = None`. Useful for distinguishing in scripts.

## Depsgraph in one paragraph

The dependency graph is what Blender uses to evaluate the scene each frame: it figures out which objects have animation, constraints, drivers, or modifiers, and produces the *evaluated* state used for rendering and the viewport. The data API (`bpy.data.objects[X]`) shows the *source* (un-evaluated) data; the depsgraph (`bpy.context.evaluated_depsgraph_get()`) gives access to the evaluated copy. For most non-animation work the source is what you want; for anything reading an animated/driven/constraint-affected value, use the depsgraph. See `bpy-essentials.md` for the pattern.

## Sources

- [Blender Manual: Data System](https://docs.blender.org/manual/en/5.2/files/data_blocks.html)
- [Blender Manual: Editors → Outliner → Collections](https://docs.blender.org/manual/en/5.2/scene_layout/collections/introduction.html)
- [Blender Manual: Modes](https://docs.blender.org/manual/en/5.2/editors/3dview/modes.html)
- [Blender Python API: bpy.types.Depsgraph](https://docs.blender.org/api/5.2/bpy.types.Depsgraph.html)
