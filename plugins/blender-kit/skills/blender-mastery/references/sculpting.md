# Sculpting

Sculpting is more interactive than scriptable — most of the actual sculpting happens through brush strokes, which Claude can't drive through the MCP. The script-relevant parts: setting up the right topology before sculpting, switching brushes, and the retopology / bake workflow afterward.

## The sculpt mode lifecycle

1. **Prepare topology** — choose multires (subdivide a base mesh) or dyntopo (real-time tessellation). They're not interchangeable; pick before you start.
2. **Sculpt** — interactive. From the MCP this means asking the user to do the actual sculpting.
3. **Retopologize** (optional, often essential) — produce a clean, animation-ready mesh from the sculpt.
4. **Bake details** — high-poly sculpt → low-poly retopo via normal map / displacement bake.
5. **Texture and finish** — the retopologized mesh becomes the deliverable.

## Multires vs Dyntopo

| | Multires | Dyntopo |
|---|---|---|
| **Topology** | Fixed base mesh, subdivided | Adaptive — adds/removes triangles in real time |
| **UVs** | Survive subdivision | Lost (Dyntopo wipes them) |
| **Vertex groups / shape keys** | Survive | Lost |
| **Memory** | Predictable | Spikes with detail |
| **Best for** | Characters with planned topology, baking down | Concepting, organic blobby work |
| **Bake-friendly** | Yes | Less so — need to retopo first anyway |

Add a multires modifier:

```python
import bpy

def add_multires(obj, levels=3):
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("Multires", "MULTIRES")
    for _ in range(levels):
        bpy.ops.object.multires_subdivide(modifier=mod.name, mode='CATMULL_CLARK')
    return mod
```

Levels go up exponentially — level 4 is 16× the polys of level 0. Don't overshoot.

For dyntopo, just enter sculpt mode and enable it via the brush settings in the UI. It's not really set up programmatically.

## Switching brushes from script

```python
def set_sculpt_brush(brush_name):
    """brush_name: 'Draw', 'Clay', 'Crease', 'Smooth', 'Inflate', 'Grab', etc."""
    brush = bpy.data.brushes.get(brush_name)
    if brush is None:
        return False
    bpy.context.tool_settings.sculpt.brush = brush
    return True
```

Brush settings (radius, strength) are then on the brush itself: `brush.size`, `brush.strength`. Changes affect future strokes by the user.

## Common brush use cases

| Brush | What it's for |
|---|---|
| Draw | General-purpose surface displacement |
| Clay | Building up volume in flat passes |
| Clay Strips | Building up volume in chunky strokes |
| Crease | Sharpening edges |
| Smooth | Removing detail |
| Grab | Bulk reshaping (no detail change, just push verts) |
| Inflate | Expanding mass evenly |
| Snake Hook | Pulling out spikes / horns / appendages |
| Pinch | Tightening edges |
| Mask | Painting masks for protected areas (used by other brushes) |

## Retopology workflow

The high-poly sculpt is rarely the final asset. To produce a clean low-poly mesh:

1. **Quad Remesher / RetopoFlow / manual retopo** — Blender's built-in `Remesh` modifier (Voxel mode) generates clean topology from a sculpt:

   ```python
   def voxel_remesh(obj, voxel_size=0.05):
       obj.data.remesh_voxel_size = voxel_size
       bpy.context.view_layer.objects.active = obj
       bpy.ops.object.voxel_remesh()
   ```

   Voxel remeshing is fast and works well for blobby organic sculpts; it produces uniform topology but no edge flow, so it's not animation-friendly.

2. **Manual retopo** is interactive — the user builds a clean low-poly mesh on top of the sculpt using snapping. The MCP can set up snapping config:

   ```python
   ts = bpy.context.scene.tool_settings
   ts.use_snap = True
   ts.snap_elements = {'FACE'}
   ts.snap_target = 'CLOSEST'
   ts.use_snap_project = True  # project new verts onto the high-poly
   ```

3. **Shrinkwrap modifier** — a programmatic way to bind a low-poly mesh to a sculpt surface:

   ```python
   def shrinkwrap_to_sculpt(low_poly_obj, high_poly_obj):
       mod = low_poly_obj.modifiers.new("Shrinkwrap", "SHRINKWRAP")
       mod.target = high_poly_obj
       mod.wrap_method = 'PROJECT'
       mod.project_axis_negative = True
       mod.use_negative_direction = True
   ```

## Baking sculpt detail to normals

After retopology, bake the sculpt's surface detail into a normal map on the low-poly. See `rendering.md` for the bake workflow — type=`NORMAL`, with `use_selected_to_active=True`:

```python
def bake_normal_from_high_to_low(low, high, image_size=2048):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'NORMAL'

    # Selection: high-poly first, low-poly active.
    bpy.ops.object.select_all(action='DESELECT')
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low

    # Set up bake target image and material on low-poly (see rendering.md).
    # ...

    bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True)
```

`use_selected_to_active=True` reads the surface from the selected (non-active) high-poly object and writes into the active low-poly's UV map.

## Common pitfalls

- **Modifying mesh data in sculpt mode** — bmesh API doesn't apply in sculpt mode. Switch to OBJECT mode first to add modifiers, change material slots, etc.
- **Multires + non-unique mesh data** — multires modifies mesh data, so if two objects share data and only one has multires, edits leak across.
- **Forgetting to apply scale before sculpting** — non-uniform scale produces stretched brush strokes. Do `bpy.ops.object.transform_apply(scale=True)` first.
- **Dynotopo + UVs** — dyntopo blows away UV maps. If the asset needs UVs, plan to retopo + unwrap after, or use multires instead.

## Sources

- [Blender Manual: Sculpt Mode](https://docs.blender.org/manual/en/5.2/sculpt_paint/sculpting/introduction/index.html)
- [Blender Manual: Multires Modifier](https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/multiresolution.html)
- [Blender Manual: Remesh Modifier](https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/remesh.html)
- [Blender Python API: Brush](https://docs.blender.org/api/5.2/bpy.types.Brush.html)
