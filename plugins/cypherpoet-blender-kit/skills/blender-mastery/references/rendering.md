# Rendering and Baking

Engine selection, baking workflows, render passes, and light setup. Most of this lives in `bpy.context.scene.render` and `bpy.context.scene.cycles` / `scene.eevee`.

## Cycles vs Eevee

Pick by the requirement, not the default:

| Need | Engine |
|---|---|
| Final-pixel quality, photorealism, accurate global illumination | Cycles |
| Fast iteration, real-time previews, viewport-quality renders | Eevee |
| Baking (lightmaps, AO, normals) | Cycles — Eevee can't bake |
| GPU-accelerated path tracing | Cycles (with CUDA / OPTIX / METAL / HIP) |
| Stylized / NPR work | Either, but Eevee is more flexible for shader experiments |
| Hair, smoke, volumetrics with physical accuracy | Cycles |

Switch via:

```python
bpy.context.scene.render.engine = 'CYCLES'   # or 'BLENDER_EEVEE' (Eevee)
```

Note: through Blender 4.2–4.5 the Eevee engine identifier was `BLENDER_EEVEE_NEXT`; Blender 5.0 renamed it back to `BLENDER_EEVEE`, which is correct at this 5.1 baseline.

## GPU acceleration in Cycles

GPU rendering needs the Cycles addon prefs configured *and* the scene's device set to GPU:

```python
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'   # 'OPTIX' (NVIDIA), 'METAL' (Apple), 'HIP' (AMD), 'ONEAPI' (Intel)
for device in prefs.devices:
    device.use = True

bpy.context.scene.cycles.device = 'GPU'
```

Headless mode honors these settings; renders on the CLI use whatever the prefs file has.

## Baking workflow (the order matters)

```python
def bake_ao(obj, image_size=1024, samples=64, output_path=None):
    # 1. Make the object active and selected.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # 2. Engine must be Cycles for baking.
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = samples

    # 3. The mesh must be UV-unwrapped. If not, unwrap first:
    if not obj.data.uv_layers:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=66)
        bpy.ops.object.mode_set(mode='OBJECT')

    # 4. Create / find the target image.
    img_name = f"{obj.name}_AO"
    img = bpy.data.images.get(img_name) or bpy.data.images.new(img_name, image_size, image_size)

    # 5. The active material must have a selected Image Texture node pointing at the target image.
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        # Find or create an image texture node:
        target = None
        for n in nt.nodes:
            if n.type == 'TEX_IMAGE' and n.image == img:
                target = n
                break
        if target is None:
            target = nt.nodes.new("ShaderNodeTexImage")
            target.image = img
        # Bake reads the *active* node:
        for n in nt.nodes:
            n.select = False
        target.select = True
        nt.nodes.active = target

    # 6. Bake.
    bpy.ops.object.bake(type='AO')

    # 7. Save the image to disk if requested.
    if output_path:
        img.filepath_raw = output_path
        img.file_format = 'PNG'
        img.save()
    return img
```

The two parts most scripts get wrong:

- **No UV map.** Cycles bakes into UV space, so the target mesh must be unwrapped. Without UVs the bake silently produces a black image.
- **No active Image Texture node.** Cycles bakes into the active node on the active material. If the script doesn't make a target node active, the bake either errors or writes into the wrong image.

## Common bake types

| Type | Use case |
|---|---|
| `COMBINED` | Final color pass — diffuse + indirect + emission |
| `AO` | Ambient occlusion only |
| `NORMAL` | Tangent-space normal map |
| `ROUGHNESS` | Roughness pass (reads material, not lighting) |
| `DIFFUSE` | Direct + indirect diffuse only |
| `GLOSSY` | Reflective contribution |
| `EMIT` | Emission pass |
| `SHADOW` | Shadow contribution |

For lightmaps (AO + GI baked into a texture for runtime), use `COMBINED` with `bpy.context.scene.cycles.use_world_indirect_lighting = True` and the appropriate pass filters.

## Render passes (separating contributions)

For compositing or post-production, enable individual passes:

```python
view_layer = bpy.context.view_layer
view_layer.use_pass_z = True
view_layer.use_pass_normal = True
view_layer.use_pass_ambient_occlusion = True
view_layer.cycles.use_pass_diffuse_direct = True
view_layer.cycles.use_pass_diffuse_indirect = True
```

After rendering, passes are accessible from the Render Result image data-block via the compositor. For programmatic save, render with `OpenEXR (Multilayer)` format — each pass becomes a layer.

## Light setups

### 3-point setup (key + fill + rim)

```python
import bpy

def make_light(name, light_type='AREA', energy=1000, color=(1, 1, 1)):
    light_data = bpy.data.lights.new(name=name, type=light_type)
    light_data.energy = energy
    light_data.color = color
    obj = bpy.data.objects.new(name=name, object_data=light_data)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def three_point_setup(target=(0, 0, 1), distance=3.0):
    key = make_light("Key", "AREA", energy=500, color=(1.0, 0.95, 0.9))
    fill = make_light("Fill", "AREA", energy=200, color=(0.85, 0.9, 1.0))
    rim = make_light("Rim", "AREA", energy=300, color=(1.0, 1.0, 1.0))

    import math
    cx, cy, cz = target
    key.location = (cx + distance * math.cos(math.radians(45)),
                    cy + distance * math.sin(math.radians(45)),
                    cz + 1.0)
    fill.location = (cx + distance * math.cos(math.radians(-30)),
                     cy + distance * math.sin(math.radians(-30)),
                     cz + 0.3)
    rim.location = (cx + distance * math.cos(math.radians(180)),
                    cy + distance * math.sin(math.radians(180)),
                    cz + 1.5)

    # Point each light at the target:
    for light in (key, fill, rim):
        track = light.constraints.new("TRACK_TO")
        empty = bpy.data.objects.new("LightTarget", None)
        empty.location = target
        bpy.context.scene.collection.objects.link(empty)
        track.target = empty
        track.track_axis = 'TRACK_NEGATIVE_Z'
        track.up_axis = 'UP_Y'

    return key, fill, rim
```

### HDRI-only

For product / studio shots, often a single HDRI environment is enough — no key lights needed. See `assets.md` for the HDRI loader and `materials.md` for the World shader setup.

## Camera placement

```python
def add_camera(name="Camera", location=(0, -5, 1.5), look_at=(0, 0, 1), focal_mm=50):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = focal_mm
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location

    # Track-to constraint, so subsequent moves stay aimed:
    target = bpy.data.objects.new("CameraTarget", None)
    target.location = look_at
    bpy.context.scene.collection.objects.link(target)
    track = cam.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    bpy.context.scene.camera = cam
    return cam
```

## Output settings

```python
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.filepath = "/tmp/render.png"
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'  # or '16'

# Frame range for animation:
scene.frame_start = 1
scene.frame_end = 60
```

## When to escape to headless

Renders are the canonical case for the headless escape hatch. The MCP will time out long before a real render finishes.

```bash
blender --background scene.blend --render-output /tmp/frame_#### --render-frame 1
# or for animation:
blender --background scene.blend --render-anim
```

For baking workflows that take more than a few seconds, same — bake via headless and let the MCP read the resulting image.

## Sources

- [Blender Manual: Cycles](https://docs.blender.org/manual/en/5.1/render/cycles/index.html)
- [Blender Manual: Eevee](https://docs.blender.org/manual/en/5.1/render/eevee/index.html)
- [Blender Manual: Baking](https://docs.blender.org/manual/en/5.1/render/cycles/baking.html)
- [Blender Python API: RenderSettings](https://docs.blender.org/api/5.1/bpy.types.RenderSettings.html)
