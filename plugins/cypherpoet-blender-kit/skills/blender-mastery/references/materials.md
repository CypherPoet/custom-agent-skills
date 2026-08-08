# Materials

Materials in Blender are node trees attached to a `Material` data-block. The Principled BSDF is the standard PBR shader and the only one that exports cleanly to GLTF / USD / most game engines.

## The minimum viable Principled BSDF

```python
import bpy

def make_principled_material(name, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    nt = mat.node_tree

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat
```

Always:

- Set `mat.use_nodes = True` before touching `node_tree`. Without it, `node_tree` is `None`.
- Clear the default node tree before building (`nodes.clear()`). The default contains a Principled BSDF and Output that you'll otherwise duplicate.
- Use socket *names* (`bsdf.inputs["Base Color"]`), not indices. Indices change between Blender versions; names stay stable.

## Defensive node access on existing materials

Imported and user-authored materials may not be Principled. Always inspect before assuming:

```python
def find_principled(mat):
    if not mat.use_nodes or not mat.node_tree:
        return None
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None

bsdf = find_principled(mat)
if bsdf:
    bsdf.inputs["Roughness"].default_value = 0.4
```

`KeyError: 'Principled BSDF'` is the canonical "I assumed Principled" failure. Iterate by `node.type`, never by `nodes["Principled BSDF"]`.

## Color space for image textures

Color textures (base color, emission) need `sRGB`. Data textures (roughness, metallic, normal, displacement, ORM) need `Non-Color`. Getting this wrong is the most common reason a material looks slightly off.

```python
img = bpy.data.images.load(filepath)
img.colorspace_settings.name = "sRGB"        # for color
# or
img.colorspace_settings.name = "Non-Color"    # for data
```

## A complete PBR setup with image textures

```python
import bpy, os

def build_pbr_material(name, tex_dir, file_map):
    """
    file_map keys (any subset): 'base_color', 'roughness', 'metallic', 'normal', 'ao'
    file_map values: filenames inside tex_dir
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    def load_tex(fname, colorspace):
        path = os.path.join(tex_dir, fname)
        if not os.path.exists(path):
            return None
        img = bpy.data.images.load(path)
        img.colorspace_settings.name = colorspace
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = img
        return node

    if 'base_color' in file_map:
        n = load_tex(file_map['base_color'], "sRGB")
        if n: nt.links.new(n.outputs["Color"], bsdf.inputs["Base Color"])
    if 'roughness' in file_map:
        n = load_tex(file_map['roughness'], "Non-Color")
        if n: nt.links.new(n.outputs["Color"], bsdf.inputs["Roughness"])
    if 'metallic' in file_map:
        n = load_tex(file_map['metallic'], "Non-Color")
        if n: nt.links.new(n.outputs["Color"], bsdf.inputs["Metallic"])
    if 'normal' in file_map:
        n = load_tex(file_map['normal'], "Non-Color")
        if n:
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(n.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    return mat
```

Notes:

- Wire normal maps through a `ShaderNodeNormalMap`, not directly into `Normal`. Direct connection treats the map as a vector field, not a tangent-space normal map.
- Roughness and metallic textures plug into the corresponding inputs as `Color` outputs (Blender treats single-channel data as grayscale color).
- For an ORM/MR combined texture (occlusion/roughness/metallic packed into RGB), use a Separate Color node and route channels.

## Material slots (objects can have many)

A mesh has a list of material slots; each face has a `material_index` pointing into that list.

```python
obj = bpy.data.objects["Cube"]
mat = bpy.data.materials.new("Wood")
obj.data.materials.append(mat)             # adds a slot, slot index = len-1

# Assign the new material to all faces:
for poly in obj.data.polygons:
    poly.material_index = len(obj.data.materials) - 1
```

`obj.material_slots[i].material` and `obj.data.materials[i]` are usually the same, but the *slot* layer is per-object while the *materials list* is per-mesh-data — relevant when objects share mesh data.

## Converting Diffuse BSDF imports to Principled

Imported models (especially from Sketchfab) often use Diffuse BSDF. Diffuse exports poorly to GLTF and looks flat. Convert:

```python
import bpy

def diffuse_to_principled(mat):
    if not mat.use_nodes:
        return
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    diffuse_nodes = [n for n in nodes if n.type == 'BSDF_DIFFUSE']
    for diff in diffuse_nodes:
        princ = nodes.new("ShaderNodeBsdfPrincipled")
        princ.location = diff.location
        for link in list(links):
            if link.to_node == diff:
                if link.to_socket.name == 'Color':
                    links.new(link.from_socket, princ.inputs['Base Color'])
                elif link.to_socket.name == 'Normal':
                    links.new(link.from_socket, princ.inputs['Normal'])
            if link.from_node == diff:
                links.new(princ.outputs['BSDF'], link.to_socket)
        nodes.remove(diff)

for mat in bpy.data.materials:
    diffuse_to_principled(mat)
```

## Things that don't export

These work in Blender but get lost on GLTF/USD export. If you need them in the final asset, bake to texture before export:

- Procedural textures (Noise, Voronoi, Wave, …)
- Color Ramp value remapping (the *texture* exports; the remap doesn't)
- Bump-from-noise (procedural Bump node chains)
- Mix Shader trees beyond a single-shader Principled
- Most non-Principled BSDFs (Glass and Emission are sometimes mapped, but check the exporter)

See `errors.md` "Material export survival matrix" for the full table.

## World shader (HDRI environment)

The `World` data-block has its own node tree and is shared across the scene:

```python
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()

bg = nt.nodes.new("ShaderNodeBackground")
out = nt.nodes.new("ShaderNodeOutputWorld")
env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load("/path/to/studio.exr")
nt.links.new(env.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
bg.inputs["Strength"].default_value = 1.0
```

For HDRIs from PolyHaven, see `assets.md` for the integration that handles this automatically.

## Sources

- [Blender Manual: Principled BSDF](https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/principled.html)
- [Blender Python API: ShaderNodeTree](https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTree.html)
- [Blender Python API: Material](https://docs.blender.org/api/5.2/bpy.types.Material.html)
