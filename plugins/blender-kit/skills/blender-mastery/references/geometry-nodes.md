# Geometry Nodes

Procedural geometry via node graphs. From a script, you build the node tree the same way you'd build a shader tree — create nodes, set inputs, link sockets — then attach the tree to an object as a `NODES` modifier.

## Table of Contents

| Section | Covers |
|---|---|
| [Mental model](#mental-model) | Geometry-node data blocks, socket flow, fields, modifiers, and evaluation |
| [Attaching a Geometry Nodes modifier](#attaching-a-geometry-nodes-modifier) | `nt.interface.new_socket(...)` is the 4.x+ API for declaring tree inputs/outputs |
| [Pattern: scatter instances on a surface](#pattern-scatter-instances-on-a-surface) | Distribute points on a surface, instance source geometry, randomize rotation, and join the instances with the input mesh |
| [Setting attributes from script](#setting-attributes-from-script) | Creating mesh attributes, assigning per-element values, and choosing data domains and types |
| [Reading evaluated geometry](#reading-evaluated-geometry) | Geometry-nodes-modified meshes show their evaluated state through the depsgraph (see `bpy-essentials.md`) |
| [Node-tree modifier inputs](#node-tree-modifier-inputs) | A geometry-node group can expose user-facing inputs |
| [Common patterns and what they're for](#common-patterns-and-what-theyre-for) | Reusable geometry-node patterns and the problems each pattern solves |
| [When to escalate](#when-to-escalate) | Geometry node trees built from script can get long (hundreds of nodes for complex graphs) |
| [Sources](#sources) | Authoritative references that ground this guidance |

## Mental model

- A **Geometry Node Tree** is a `bpy.types.GeometryNodeTree` data-block.
- Object inputs/outputs flow as `Geometry` sockets. The graph transforms one `Geometry` into another.
- **Attributes** are per-element data on geometry (per-point, per-edge, per-face, per-instance). Most node operations read/write attributes.
- **Fields** are deferred computations — when you wire a `Position` output to a `Set Position` input, you're passing a function that gets evaluated per element, not an array of values.
- The graph is non-destructive. The source mesh is unchanged; the modifier produces an evaluated result that lives in the depsgraph (see `bpy-essentials.md`).

## Attaching a Geometry Nodes modifier

```python
import bpy

def add_geo_nodes_modifier(obj, name="GeometryNodes"):
    mod = obj.modifiers.new(name, "NODES")
    nt = bpy.data.node_groups.new(f"{name}_Tree", "GeometryNodeTree")
    mod.node_group = nt
    # Add the standard input/output sockets:
    nt.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    nt.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    group_in = nt.nodes.new("NodeGroupInput")
    group_out = nt.nodes.new("NodeGroupOutput")
    group_in.location = (-300, 0)
    group_out.location = (300, 0)
    nt.links.new(group_in.outputs["Geometry"], group_out.inputs["Geometry"])
    return mod, nt
```

`nt.interface.new_socket(...)` is the 4.x+ API for declaring tree inputs/outputs. (Older `nt.inputs.new(...)` was removed.)

## Pattern: scatter instances on a surface

The classic geometry-nodes example. Distribute points on a mesh surface, then instance another object on each point.

```python
import bpy

def scatter_setup(target_obj, source_obj, density=10.0, seed=0):
    mod, nt = add_geo_nodes_modifier(target_obj, name="Scatter")

    nodes, links = nt.nodes, nt.links
    group_in = next(n for n in nodes if n.bl_idname == "NodeGroupInput")
    group_out = next(n for n in nodes if n.bl_idname == "NodeGroupOutput")
    # Remove the direct passthrough link:
    for l in list(links):
        if l.from_node == group_in and l.to_node == group_out:
            links.remove(l)

    distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute.inputs["Density"].default_value = density
    distribute.inputs["Seed"].default_value = seed

    object_info = nodes.new("GeometryNodeObjectInfo")
    object_info.inputs["Object"].default_value = source_obj
    object_info.transform_space = 'RELATIVE'

    instance = nodes.new("GeometryNodeInstanceOnPoints")

    rotate = nodes.new("GeometryNodeRotateInstances")
    # For Z-only rotation, sample a single FLOAT and build the rotation vector
    # via Combine XYZ. This is cleaner than a FLOAT_VECTOR random with X=Y=0
    # bounds, and signals intent — "rotate around Z by a random angle".
    random_z = nodes.new("FunctionNodeRandomValue")
    random_z.data_type = 'FLOAT'
    random_z.inputs[2].default_value = 0.0       # Min (float socket index)
    random_z.inputs[3].default_value = 6.283185  # Max (≈ 2π)

    combine = nodes.new("ShaderNodeCombineXYZ")
    # X and Y left at 0; only Z carries the random angle:
    links.new(random_z.outputs[1], combine.inputs["Z"])  # float output

    join = nodes.new("GeometryNodeJoinGeometry")

    # Wire it up:
    links.new(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
    links.new(distribute.outputs["Points"], instance.inputs["Points"])
    links.new(object_info.outputs["Geometry"], instance.inputs["Instance"])
    links.new(instance.outputs["Instances"], rotate.inputs["Instances"])
    links.new(combine.outputs["Vector"], rotate.inputs["Rotation"])
    links.new(group_in.outputs["Geometry"], join.inputs["Geometry"])
    links.new(rotate.outputs["Instances"], join.inputs["Geometry"])
    links.new(join.outputs["Geometry"], group_out.inputs["Geometry"])
```

Two things to know about wiring:

- `GeometryNodeDistributePointsOnFaces` in 5.x has a `Mesh` input (renamed from earlier `Geometry`). When in doubt, check `node.inputs.keys()` to see the real socket names.
- `FunctionNodeRandomValue` has output sockets keyed by data-type — indices 0 (`Value` vector), 1 (`Value` float), 2 (`Value` int), 3 (`Value` bool). Use the index matching the active `data_type`. For `FLOAT`, that's `outputs[1]`. Index access is safer than name access because the visible-name disambiguator changes across versions. For axis-isolated rotations (Z-only is the common case), prefer sampling a `FLOAT` and combining with `ShaderNodeCombineXYZ` rather than zeroing two components of a `FLOAT_VECTOR` — the intent reads cleaner and there's no risk of accidentally bleeding random values into the unwanted axes.

## Setting attributes from script

For non-procedural attributes (e.g., a per-point custom value baked into the source mesh):

```python
mesh = obj.data
mesh.attributes.new(name="my_value", type='FLOAT', domain='POINT')
attr = mesh.attributes["my_value"]
for i, val in enumerate(my_values):
    attr.data[i].value = val
```

Domain options: `POINT`, `EDGE`, `CORNER` (face corners — for UVs and split normals), `FACE`, `INSTANCE`, `CURVE`. Type options: `FLOAT`, `INT`, `FLOAT_VECTOR`, `FLOAT_COLOR`, `BYTE_COLOR`, `STRING`, `BOOLEAN`, `FLOAT2`, `INT8`, `QUATERNION`.

## Reading evaluated geometry

Geometry-nodes-modified meshes show their evaluated state through the depsgraph (see `bpy-essentials.md`):

```python
deps = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(deps)
mesh_eval = obj_eval.data
print(f"Source: {len(obj.data.vertices)} verts, evaluated: {len(mesh_eval.vertices)} verts")
```

For instance-heavy scenes, `depsgraph.object_instances` enumerates each instance separately:

```python
for inst in deps.object_instances:
    if inst.is_instance:
        print(inst.object.name, list(inst.matrix_world.translation))
```

## Node-tree modifier inputs

A geometry-node group can expose user-facing inputs. From the modifier, set them by socket *identifier* (a generated id like `Socket_2`), not by name — names aren't guaranteed unique.

```python
# Add an input socket on the tree:
nt.interface.new_socket("Density", in_out='INPUT', socket_type='NodeSocketFloat')

# The new socket's identifier is exposed on the modifier. The identifier is an
# attribute name under mod.properties, so reach it dynamically with getattr:
for socket in nt.interface.items_tree:
    if socket.in_out == 'INPUT' and socket.name == "Density":
        getattr(mod.properties.inputs, socket.identifier).value = 25.0

# Drive that input from an attribute instead of a constant:
inp = getattr(mod.properties.inputs, socket.identifier)
inp.type = 'ATTRIBUTE'
inp.attribute_name = "density_attr"

# Output attribute names live in the matching outputs collection:
getattr(mod.properties.outputs, "Socket_3").attribute_name = "result_attr"
```

Stale-code trap: through Blender 5.1 these inputs were **custom properties**, set by
subscripting the modifier — `mod[socket.identifier] = 25.0`, with sibling keys like
`"<identifier>_use_attribute"` and `"<identifier>_attribute_name"`. Blender 5.2 replaced
them with the real RNA properties above. On 5.2+ the old subscript route raises
`TypeError: bpy_struct[key] = val: id properties not supported for this type` — it fails
loudly rather than silently doing nothing, so stale scripts stop rather than half-work.
If you have to support 5.1 as well, branch on `hasattr(mod, "properties")`.

Socket identifiers for the Compare and Random Value nodes also changed in 5.2 — re-read
`nt.interface.items_tree` rather than reusing identifiers recorded against an earlier version.

## Common patterns and what they're for

| Pattern | Use case |
|---|---|
| Distribute Points on Faces → Instance on Points | Scatter (foliage, debris, grass) |
| Curve to Mesh (with profile curve) | Cables, ropes, beams |
| Boolean (Mesh) — geometry-nodes variant | Procedural cuts that don't bake until needed |
| Set Position with Noise field | Displacement / surface jitter |
| Resample Curve / Sample Curve | Animating along a path, evenly-spaced points on a curve |
| Capture Attribute → Set Material | Per-element material assignment from a procedural source |

## When to escalate

Geometry node trees built from script can get long (hundreds of nodes for complex graphs). If a tree balloons:

- Split into a node group (`GeometryNodeGroup`) and reuse.
- Consider whether the work belongs in geometry nodes at all — sometimes a one-shot mesh edit via `bmesh` is simpler than a procedural setup.
- Build the tree once in the UI, save to a .blend, and link/append from script — faster than reconstructing it programmatically every time.

## Sources

- [Blender Manual: Geometry Nodes](https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/introduction.html)
- [Blender Python API: GeometryNodeTree](https://docs.blender.org/api/5.2/bpy.types.GeometryNodeTree.html)
- [Blender Python API: Attribute](https://docs.blender.org/api/5.2/bpy.types.Attribute.html)
- [5.2 Python API release notes](https://developer.blender.org/docs/release_notes/5.2/python_api/) — the modifier-properties move and the Compare / Random Value identifier changes
