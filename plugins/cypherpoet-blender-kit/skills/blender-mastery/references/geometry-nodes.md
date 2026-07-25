# Geometry Nodes

Procedural geometry via node graphs. From a script, you build the node tree the same way you'd build a shader tree — create nodes, set inputs, link sockets — then attach the tree to an object as a `NODES` modifier.

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

def socket_by(sockets, name, socket_type):
    """Resolve a socket by visible name *and* data type.

    Polymorphic nodes shuffle socket order between Blender versions; the
    name+type pair survives that where a hard-coded index doesn't. See the
    Random Value trap below.
    """
    return next(s for s in sockets if s.name == name and s.type == socket_type)

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
    socket_by(random_z.inputs, "Min", 'VALUE').default_value = 0.0
    socket_by(random_z.inputs, "Max", 'VALUE').default_value = 6.283185  # ≈ 2π

    combine = nodes.new("ShaderNodeCombineXYZ")
    # X and Y left at 0; only Z carries the random angle:
    links.new(socket_by(random_z.outputs, "Value", 'VALUE'), combine.inputs["Z"])

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
- **Stale-code trap — polymorphic node socket indices moved in 5.2.** Through 5.1, `FunctionNodeRandomValue` declared *every* data-type's sockets at once and hid the inactive ones, so a `FLOAT` sample sat at `inputs[2]`/`inputs[3]` with the float output at `outputs[1]`. Blender 5.2 builds the socket list *from* the active `data_type` instead ([`3a5cd7862b`](https://projects.blender.org/blender/blender/commit/3a5cd7862bc1422188cdc7e6fb9ac3209077f479)): with `data_type='FLOAT'` the inputs are now `Min`, `Max`, `ID`, `Seed`, and there is a **single** `Value` output. Code carrying the 5.1 indices silently writes into `ID`/`Seed` and then raises `IndexError` on `outputs[1]`. Resolve by name **and** type — the `socket_by` helper above is correct on both versions. The same 5.2 rework applies to Compare, Boolean Math, and Rotate Euler.
- For axis-isolated rotations (Z-only is the common case), prefer sampling a `FLOAT` and combining with `ShaderNodeCombineXYZ` rather than zeroing two components of a `FLOAT_VECTOR` — the intent reads cleaner and there's no risk of accidentally bleeding random values into the unwanted axes.

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

# The new socket's identifier is exposed on the modifier:
for socket in nt.interface.items_tree:
    if socket.in_out == 'INPUT' and socket.name == "Density":
        mod[socket.identifier] = 25.0
```

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

- [Blender Manual: Geometry Nodes](https://docs.blender.org/manual/en/5.1/modeling/geometry_nodes/introduction.html)
- [Blender Python API: GeometryNodeTree](https://docs.blender.org/api/5.1/bpy.types.GeometryNodeTree.html)
- [Blender Python API: Attribute](https://docs.blender.org/api/5.1/bpy.types.Attribute.html)
