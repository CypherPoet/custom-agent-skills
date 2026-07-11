# Animation and Rigging

Armatures (the bones), pose mode (the deformations), drivers (logic), and fcurves (the keyframes). Rigging is where Blender's mode discipline (`bpy-essentials.md` P3) matters most — almost every script bug here traces to being in the wrong mode.

## Object vs armature data

Same split as object/mesh (see `scene-mental-model.md`):

- `bpy.data.objects["Rig"]` — the object: position, scale, parent, modifiers (the `Armature` modifier on the *deformed mesh* points back at this object).
- `bpy.data.armatures["Rig"]` — the armature data: bones (in rest position), bone hierarchy, custom shapes.
- Pose data lives on the *object*, not the armature: `bpy.data.objects["Rig"].pose.bones["Spine"]` — these are `PoseBone` objects with constraints, custom properties, and current transform.

## Building an armature from script

```python
import bpy

def make_armature(name, bones):
    """
    bones: list of dicts with keys 'name', 'head', 'tail', and optional 'parent'.
    """
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)

    # Bones can only be created in EDIT mode on the armature:
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = arm_data.edit_bones
    created = {}
    for spec in bones:
        b = edit_bones.new(spec['name'])
        b.head = spec['head']
        b.tail = spec['tail']
        if spec.get('parent') and spec['parent'] in created:
            b.parent = created[spec['parent']]
            b.use_connect = spec.get('connect', False)
        created[spec['name']] = b

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj
```

Three things to know:

- Bone topology (creation, parenting, head/tail positions) lives in `armature.edit_bones` and is only accessible in **edit mode**.
- After exiting edit mode, `armature.bones` (rest data) and `armature_object.pose.bones` (deform data) become available.
- `bone.use_connect = True` snaps the child's head to the parent's tail and removes the gap between them.

## Pose mode: posing and constraining

Pose mode operates on `pose_bones` (the deformable layer):

```python
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

pose_bone = arm_obj.pose.bones["Spine"]
pose_bone.location = (0, 0, 0.5)
pose_bone.rotation_quaternion = (1, 0, 0, 0)  # identity
pose_bone.rotation_mode = 'QUATERNION'  # or 'XYZ', 'YXZ', etc.
```

`pose_bone.location/rotation/scale` are *deltas* from the rest pose — not world transforms. To get world transform of a posed bone, use `pose_bone.matrix` (in armature object space) or `arm_obj.matrix_world @ pose_bone.matrix` (world).

## Bone constraints

```python
ik = pose_bone.constraints.new("IK")
ik.target = arm_obj                    # IK chain root is part of the same armature
ik.subtarget = "IK_target_bone"        # the controller bone
ik.chain_count = 2                     # how many bones up the chain to solve
ik.pole_target = arm_obj
ik.pole_subtarget = "IK_pole_bone"
ik.pole_angle = 0
```

Common constraint types:

- `IK` — inverse kinematics. The constraint goes on the *last* bone in the chain (e.g. the lower leg if you're solving for foot position).
- `Copy Rotation` / `Copy Location` / `Copy Transforms` — slave one bone to another.
- `Limit Rotation` / `Limit Location` / `Limit Scale` — clamp values, useful for physically sensible joints.
- `Track To` / `Damped Track` — point a bone at a target.
- `Stretch To` — squash-and-stretch with target distance.
- `Child Of` — parenting that can be toggled at runtime.

Constraint type strings come from the operator reference: `bpy.ops.pose.constraint_add` lists them, but for direct creation, `pose_bone.constraints.new("IK")` uses the same enum.

## Building a basic IK leg setup

```python
def setup_ik_leg(arm_obj, upper_name, lower_name, target_name, pole_name=None):
    pose = arm_obj.pose
    lower = pose.bones[lower_name]
    ik = lower.constraints.new("IK")
    ik.target = arm_obj
    ik.subtarget = target_name
    ik.chain_count = 2  # upper + lower
    if pole_name:
        ik.pole_target = arm_obj
        ik.pole_subtarget = pole_name
        ik.pole_angle = 0
    # FK fallback: leave the upper bone unconstrained — animator can keyframe FK
    # rotations on it directly when IK influence is set to 0.
```

For an FK/IK switch, drive `ik.influence` from a custom property on the rig's root bone — keyframing 0 → 1 toggles. See "Drivers" below.

## Drivers

A driver makes one property follow another, evaluated every frame. Used everywhere in rigs (FK/IK switching, bone scale by distance, custom rig UIs).

```python
# Drive a constraint's influence by a custom property:
fcurves = bsdf_or_constraint.driver_add("influence")
driver = fcurves.driver
driver.type = 'AVERAGE'  # or 'SCRIPTED'

var = driver.variables.new()
var.name = "ik_switch"
var.type = 'SINGLE_PROP'
var.targets[0].id_type = 'OBJECT'
var.targets[0].id = arm_obj
var.targets[0].data_path = 'pose.bones["Root"]["ik_switch"]'
```

For scripted expressions, set `driver.type = 'SCRIPTED'` and `driver.expression = "ik_switch * 1.0"`.

Drivers are on the *fcurve*, not the property — `driver_add` returns the fcurve(s) and adds the driver. To remove, use `driver_remove`.

### Custom property UI metadata (`id_properties_ui`)

When the custom property is the user-facing handle for a rig feature (an FK/IK switch, a stretchiness slider, a face-shape selector), set its UI metadata so the animator sees the right slider range, default, description, and snap behavior. From Blender 4.0 onward this lives on `id_properties_ui`:

```python
bone = arm_obj.pose.bones["Root"]
bone["ik_switch"] = 1.0  # create the property with an initial value

ui = bone.id_properties_ui("ik_switch")
ui.update(
    default=1.0,
    min=0.0,
    max=1.0,
    soft_min=0.0,
    soft_max=1.0,
    description="0 = full FK, 1 = full IK",
    subtype='FACTOR',  # gives a 0-1 progress-bar slider in the UI
)
```

Without this, the property defaults to a free-range float editor that's miserable to animate. Always set `min`/`max` for switches; always set `description` so other riggers know what the property is for.

## Keyframes and fcurves

```python
# Keyframe a property:
pose_bone.keyframe_insert(data_path='location', frame=1)
pose_bone.location = (0, 0, 1)
pose_bone.keyframe_insert(data_path='location', frame=10)
```

The action holding the keyframes lives on `arm_obj.animation_data.action`. To inspect:

```python
action = arm_obj.animation_data.action
for fcu in iter_action_fcurves(action):
    print(fcu.data_path, fcu.array_index, len(fcu.keyframe_points))
```

Each fcurve covers one scalar (e.g., `location[0]`, `rotation_quaternion[2]`). Vector properties become multiple fcurves with `array_index` 0..n-1.

### Slotted actions (Blender 5.x): `action.fcurves` is gone

Blender 4.4 introduced slotted (layered) actions; Blender 5.x removed the legacy
`action.fcurves` collection — accessing it raises
`AttributeError: 'Action' object has no attribute 'fcurves'` (as of 5.1). Fcurves now
live under `action.layers[].strips[].channelbags[].fcurves`. `obj.keyframe_insert()`
still works and creates the slot machinery for you — it's the write path that needs no
migration. For reading, use a version-safe accessor:

```python
def iter_action_fcurves(action):
    if hasattr(action, "fcurves"):          # legacy API (<= 4.x)
        yield from action.fcurves
        return
    for layer in action.layers:             # slotted actions (5.x)
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves
```

## NLA strips

The NLA editor combines multiple actions into a non-linear timeline (walk → run → idle blends). Programmatically:

```python
nla = arm_obj.animation_data.nla_tracks
track = nla.new()
track.name = "Walk"
strip = track.strips.new("walk_strip", start=1, action=walk_action)
strip.frame_end = 24
strip.influence = 1.0
strip.blend_type = 'REPLACE'  # or 'ADD', 'COMBINE', etc.
```

NLA strips combine into a single evaluated animation per frame. The fcurves you see in the action editor reflect only the *active* action; NLA blending is applied on top during evaluation.

## Weight painting from script

Vertex weights live on the deformed mesh, not on the armature:

```python
mesh_obj = bpy.data.objects["Character"]
vg = mesh_obj.vertex_groups.new(name="Spine")
# Add weight 1.0 to vertex 42:
vg.add([42], 1.0, type='REPLACE')
```

The Armature modifier on the mesh references the rig object; weight groups must have names matching bone names for the deformation to bind.

QA check after weight painting:

```python
def check_weights(obj):
    """Report vertices not weighted to any bone, or weighted >1.0 in total."""
    issues = []
    for v in obj.data.vertices:
        total = sum(g.weight for g in v.groups)
        if total < 0.01:
            issues.append((v.index, "unweighted"))
        elif total > 1.5:
            issues.append((v.index, f"over-weighted: {total:.2f}"))
    return issues
```

## Sources

- [Blender Manual: Armatures](https://docs.blender.org/manual/en/5.1/animation/armatures/introduction.html)
- [Blender Manual: Constraints](https://docs.blender.org/manual/en/5.1/animation/constraints/index.html)
- [Blender Manual: Drivers](https://docs.blender.org/manual/en/5.1/animation/drivers/index.html)
- [Blender Python API: PoseBone](https://docs.blender.org/api/5.1/bpy.types.PoseBone.html)
- [Blender Python API: NlaStrip](https://docs.blender.org/api/5.1/bpy.types.NlaStrip.html)
