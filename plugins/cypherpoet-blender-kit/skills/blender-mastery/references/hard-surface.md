# Hard-Surface Modeling & Topology Cleanup

Doctrine and executable patterns for hard-surface work: non-destructive modifier stacks, boolean workflows, normal management, and topology remediation. Each topic states its decision rule once, then the `bpy` route (primary) and — where it earns its place — a keyboard route for agents driving Blender's UI (see [Driving the UI as an agent](#driving-the-ui-as-an-agent)). API claims here are verified against Blender 5.1; workflow defaults are professional doctrine, labeled as such. Operator/context traps: `bpy-essentials.md`.

## The non-destructive spine

Stay parametric until hand-off. A live modifier stack keeps wall thickness, fillet radii, and silhouette editable in seconds; applied ("baked") geometry makes every revision a rebuild. The doctrine default for a mirrored, solid, filleted, smoothed part:

**Mirror → Solidify → Bevel → Subdivision Surface**

Modifiers evaluate top to bottom, so this order *is* the design: symmetry first so everything downstream sees the whole form, thickness before bevel so rims get filleted too, and bevel before subdivision so fillet edges pinch the smoothing. Swapping Bevel and Subsurf melts fillets into blobs. Two manual-documented gotchas: new modifiers append at the *bottom* of the stack, and applying a modifier that isn't first evaluates it as if it were first.

**Apply rotation and scale before trusting the stack.** Mirror works across the object's *local* axes (or a Mirror Object's), and Solidify computes thickness in local coordinates — the manual is explicit that non-uniform scale varies wall thickness and says to apply or clear scale. Bevel widths behave the same way in practice. Consequence: unapplied rotation mirrors across a tilted plane; unapplied scale gives lopsided walls and fillets.

```python
obj = bpy.data.objects["Bracket"]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

mirror = obj.modifiers.new("Mirror", 'MIRROR')
mirror.use_axis[0] = True
mirror.use_bisect_axis[0] = True       # cut geometry crossing the plane, keep one side
# mirror.use_bisect_flip_axis[0] = True  # keep the other side instead
# mirror.mirror_object = bpy.data.objects["PivotEmpty"]  # mirror across an Empty's axes

solid = obj.modifiers.new("Solidify", 'SOLIDIFY')
solid.thickness = 0.004

bevel = obj.modifiers.new("Bevel", 'BEVEL')
bevel.limit_method = 'WEIGHT'          # only weighted edges get filleted — see Edge control
bevel.width = 0.006
bevel.segments = 3
bevel.harden_normals = True

subsurf = obj.modifiers.new("Subsurf", 'SUBSURF')
subsurf.levels = 2
subsurf.render_levels = 2              # keep viewport and render matched
```

For symmetry that isn't centered on the object origin, parent an Empty at the world origin (or snap it to the 3D cursor) and point `mirror_object` at it. Bisect + Flip resolve overlapping halves into a clean center seam.

## Primitives & topology standards

- **Vertex counts divisible by four** (doctrine). A 16-vertex cylinder — Blender's default is 32 — splits into clean quadrants, so Mirror with Bisect on X and Y rebuilds the whole part from one quarter of the cleanup work. Add segments only when the silhouette visibly needs them; subdivision supplies the rest. `bpy.ops.mesh.primitive_cylinder_add(vertices=16)`.
- **N-gons only on confirmed-planar faces** (doctrine). Flat caps: fine. Curved surfaces or anything under a Subdivision Surface: quads, or expect shading artifacts. Game-engine targets: triangulate on export (see `export.md`).
- **Planar validation — the flattening routine** (doctrine; the mechanics are manual-documented). "Looks flat" is not flat; booleans and Harden Normals both punish near-planar faces. Force exact coplanarity by assigning the coordinate:

```python
bm = bmesh.from_edit_mesh(obj.data)   # edit mode
for v in bm.verts:
    if v.select:
        v.co.x = 0.0                  # or any exact datum
bmesh.update_edit_mesh(obj.data)
```

Keyboard route: `S X 0 Return` (scale-to-zero on the axis — see the orientation caveat below). To nudge stray verts without denting the silhouette, slide them along their edges (`G G`) instead of free-moving; from scripts, reposition along the edge with bmesh rather than calling the viewport-modal slide operator.

## Booleans: cut fast, clean deliberately

Solver choice on 5.x (the enum: `FLOAT`, `EXACT`, `MANIFOLD`):

| Solver | Character | Use when |
|---|---|---|
| `EXACT` (default) | Slowest, handles overlapping/coplanar geometry | Operands touch, overlap, or share faces |
| `MANIFOLD` (4.5+) | Usually fastest; **requires watertight operands** (exception: difference-with-a-plane) | Clean closed cutters — the hard-surface common case |
| `FLOAT` | Fast, simple, no overlap support | Quick sketching where artifacts are acceptable |

Stale-code trap: `FLOAT` is the 5.0 rename of `Fast` — `boo.solver = 'FAST'` raises `TypeError` on 5.x.

```python
boo = obj.modifiers.new("Cut", 'BOOLEAN')
boo.operation = 'DIFFERENCE'
boo.object = cutter
boo.solver = 'MANIFOLD'
cutter.display_type = 'WIRE'
cutter.hide_render = True
```

Match cutter density to base density (doctrine): a 6-vert cutter through a 64-vert curve leaves shading scars along the intersection.

**Stash originals, shrinkwrap back** (doctrine — the pro cleanup pattern). Before destructive joins, duplicate the pristine surface into a hidden `Originals` collection. After cleanup mangles the curvature, a Shrinkwrap modifier targeting the original sucks the repaired topology back onto the mathematically correct surface:

```python
orig = obj.copy()
orig.data = obj.data.copy()
orig.name = obj.name + ".original"
stash = bpy.data.collections.get("Originals") or bpy.data.collections.new("Originals")
if stash.name not in {c.name for c in bpy.context.scene.collection.children}:
    bpy.context.scene.collection.children.link(stash)
stash.objects.link(orig)
orig.hide_set(True)

sw = obj.modifiers.new("Restore", 'SHRINKWRAP')
sw.target = orig
sw.wrap_method = 'NEAREST_SURFACEPOINT'   # 'TARGET_PROJECT' = smoother result, slower
```

Post-boolean vertex hygiene — naming split to know: the UI calls it *Merge ‣ By Distance*, the API still calls it `remove_doubles`:

```python
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
bm.to_mesh(me)
bm.free()
```

For interactive cleanup sessions, enable auto-merge so slid verts weld on contact: `bpy.context.scene.tool_settings.use_mesh_automerge = True` (UI: Sidebar ‣ Tool ‣ Options ‣ Auto Merge).

## Normals & shading on 4.1+/5.x

**The break every stale tutorial trips over:** Blender 4.1 removed mesh-level Auto Smooth. `mesh.use_auto_smooth` no longer exists — an `AttributeError` on it marks pre-4.1 code. The 5.1 surface:

- `Object ‣ Shade Auto Smooth` → `bpy.ops.object.shade_auto_smooth(angle=radians(30))` — adds a **"Smooth by Angle"** node-group modifier (bundled Essentials asset), pinned to stay last in the stack (`use_pin_to_last`). The non-destructive default; pairs cleanly with the spine.
- `bpy.ops.object.shade_smooth_by_angle(...)` — one-shot write of the `sharp_edge` attribute, **no modifier**, and no menu entry on 5.1 ("Shade Smooth by Angle" as a menu item is 4.1-era naming). Use for flattened, final meshes.
- Gotcha: plain `Shade Smooth` / `Shade Flat` *remove* Smooth by Angle modifiers.
- Edit-mode variant: `Edge ‣ Set Sharpness by Angle` (`mesh.set_sharpness_by_angle`).

**Harden Normals** (on the Bevel modifier): adjusts bevel-face vertex normals to match the surrounding flats, so panels stay flat and the fillet carries the shading blend — the fix for smooth-shading "bulge" around bevels. Its only prerequisite on 5.x is a `custom_normal` attribute, auto-created on enable (the 3.x-era Auto Smooth requirements are gone). Bevel's *Face Strength* option pairs with Weighted Normal's *Face Influence* when you need finer arbitration.

**Weighted Normal modifier**: biases vertex normals toward larger faces — the "flat panels shade flat" workhorse for medium-poly work. `weight` reads like a contrast dial: 50 weights all faces uniformly; 60–100 (doctrine) favors the big flats on architectural panels. Keep Sharp preserves marked-sharp edges. No shading prerequisites on 5.x.

**Custom normals from another object** (Data Transfer modifier): transfer `CUSTOM_NORMAL` as Face Corner Data — the classic trick for foliage or grafted panels borrowing a smooth donor's shading. Click *Generate Data Layers* after configuring or the transfer silently no-ops.

**Eevee forgives, Cycles doesn't** (doctrine + documented settings). Normal tricks bend shading, not geometry — Cycles computes shadows from the true polygonal silhouette, so a low-poly curve casts faceted shadow seams no matter how clean the normals look. Mitigate per object, or add real geometry for path-traced targets:

```python
obj.cycles.shadow_terminator_geometry_offset = 0.1  # preferred: offsets shadow rays, minimal lighting impact
obj.cycles.shadow_terminator_offset = 0.0           # pushes the terminator; not energy-conserving
```

UI: Object Properties ‣ Shading ‣ Shadow Terminator (Cycles).

## Edge control

Bevel weights let one Bevel modifier carry many fillet widths. Since 4.0 they live in a mesh attribute — `MeshEdge.bevel_weight` is gone (second stale-code trap):

```python
me = obj.data
attr = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", 'FLOAT', 'EDGE')
for i, edge in enumerate(me.edges):
    if wants_fillet(edge):
        attr.data[i].value = 1.0     # 0..1 scales the modifier's Width
```

With `limit_method='WEIGHT'`, only weighted edges fillet — tag silhouette edges at 1.0, soften interior seams at 0.3, leave the rest alone. UI routes: `Ctrl+E ‣ Edge Bevel Weight` then type a value and `Return`; or Sidebar ‣ Item ‣ Transform ‣ Edge Data ‣ Bevel Weight (labeled *Mean* Bevel Weight when several edges are selected; edge-select mode required).

**Control loops** (doctrine): a loop slid close to a corner pinches Subdivision Surface sharp at that corner while the rest stays smooth. Scripting note: interactive `Ctrl+R` loop cut is hover-driven (see below); from `bpy`, prefer weighted bevels or `bmesh.ops.subdivide_edges` on a chosen edge ring instead of simulating the modal tool.

## The hand-off audit

Run before export, bake, or delivery (all checks data-API, headless-safe):

```python
bm = bmesh.new()
bm.from_mesh(obj.data)
report = {
    "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
    "ngons": sum(1 for p in obj.data.polygons if len(p.vertices) > 4),
    "scale_applied": all(abs(s - 1.0) < 1e-6 for s in obj.scale),
    "rotation_applied": all(abs(r) < 1e-6 for r in obj.rotation_euler),
    "viewport_render_parity": all(m.show_viewport == m.show_render for m in obj.modifiers),
}
bm.free()
```

| Check | Failing symptom | Fix |
|---|---|---|
| Non-manifold edges = 0 | Broken booleans, failed 3D prints, physics leaks | `Select ‣ Select All by Trait ‣ Non Manifold` (vertex/edge mode), also `select_interior_faces`; weld or rebuild |
| No n-gons on curved regions | Subdivision artifacts, engine re-triangulation surprises | Requad or triangulate deliberately |
| Scale/rotation applied | Lopsided bevels and walls, tilted mirrors | `Ctrl+A ‣ Rotation & Scale` (All Transforms also applies location — moves the origin to world origin) |
| Viewport/render parity | Renders don't match the viewport | Align `levels`/`render_levels` and `show_viewport`/`show_render` |

## Driving the UI as an agent

For agents with keyboard/screen control (or advising a human at the keyboard), Blender is unusually automatable *through typed input*: modal transforms accept exact numbers — the manual's own example is `S 2 Return` to double a scale. Keystrokes beat pixel-hunting; type values, never drag them.

- **Keys land in the editor under the pointer.** Position the cursor over the 3D viewport before sending shortcuts, and screenshot-verify after each mutating sequence.
- **Axis keys are orientation-dependent**: first press of `X`/`Y`/`Z` constrains to the *current transform orientation*; the second press switches to global (or local, if the orientation is already Global); third clears. Deterministic sequences either assert Global orientation first or use tap-count semantics. `Shift+X/Y/Z` locks the perpendicular plane.
- Manual key spellings: confirm is `Return`; decimal `.`; negate `-`; `Backspace` resets the number.

| Goal | Route (default keymap, Edit/Object mode as implied) |
|---|---|
| Flatten selection to a datum | `S` `X` `0` `Return` (assumes Global orientation) |
| Slide vert/edge along its rails | `G G`, move (typed factor works in practice; undocumented), `LMB` confirm |
| Merge selected by distance | `M`, choose *By Distance* |
| Apply rotation + scale | `Ctrl+A`, *Rotation & Scale* |
| Tag fillet edges | `Ctrl+E`, *Edge Bevel Weight*, type `1`, `Return` |
| Smooth with hard-surface angles | Object menu, *Shade Auto Smooth* |

**Mouse-fragile — script these instead:** loop-cut placement (`Ctrl+R` picks its loop from the hovered edge; no keyboard alternative; `RMB` during the slide step still cuts at the center — it is not a cancel), knife tool, and addon pie menus.

## Third-party ecosystem (if installed)

Never assume an addon; detect, then adapt: `installed = set(bpy.context.preferences.addons.keys())` (extension IDs look like `bl_ext.<repo>.<name>`). The native patterns above cover the critical path without any of these. Verified 2026-07 — Blender Market is now Superhive; vendor compatibility shifts, so re-check before recommending a purchase.

| Addon | License | What it adds | Native fallback |
|---|---|---|---|
| [Hard Ops](https://superhivemarket.com/products/hardopsofficial) | Paid | Hard-surface workflow accelerator (vendor lists ≤5.0 as of mid-2026 — check before 5.1 use) | This file's spine |
| [Boxcutter](https://superhivemarket.com/products/boxcutter) | Paid | Draw-to-cut boolean sketching | Boolean modifier + cutters |
| [MESHmachine](https://mesh.machin3.io/) | Paid | Unbevel/Unfuse/Unchamfer, Stashes, fillet surgery | None clean — rebuild edges manually |
| [MACHIN3tools](https://superhivemarket.com/products/machin3tools) | Paid | Pies/workflow speedups (the name is MACHIN3tools — "Machine Tools" is a garble; no longer free) | Vanilla keymap |
| [DECALmachine](https://decal.machin3.io/) | Paid | Decal/trim-sheet surface detail without topology edits | Real geometry or texture work |
| [ND](https://extensions.blender.org/add-ons/nd/) | Free | Non-destructive utility layer (vendor name is "ND", not "ND Toolkit") | This file's spine |
| [Bool Tool](https://extensions.blender.org/add-ons/bool-tool/) | Free | Boolean convenience ops (bundled pre-4.2; now an extension) | Boolean modifier |
| [3D Print Toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/) | Free | Batch mesh diagnostics | The hand-off audit above |
| [rotor](https://extensions.blender.org/add-ons/rotor/) | Free | Gizmo-driven mirroring (it's a mirror tool — not a general hard-surface suite) | Mirror modifier |
| [Blockout](https://extensions.blender.org/add-ons/blockout/) | Free | Boxcutter-style boolean sketching | Boolean modifier + cutters |
| [BH Smart Sym](https://extensions.blender.org/add-ons/bh-smart-sym/) | Free | Click-arrow face symmetrize helper | `Mesh ‣ Symmetrize` |

## Sources

- [Modifier stack introduction](https://docs.blender.org/manual/en/5.1/modeling/modifiers/introduction.html) — evaluation order, append-at-bottom, apply-out-of-order behavior
- [Mirror](https://docs.blender.org/manual/en/5.1/modeling/modifiers/generate/mirror.html) · [Solidify](https://docs.blender.org/manual/en/5.1/modeling/modifiers/generate/solidify.html) · [Bevel](https://docs.blender.org/manual/en/5.1/modeling/modifiers/generate/bevel.html) · [Boolean](https://docs.blender.org/manual/en/5.1/modeling/modifiers/generate/booleans.html) · [Shrinkwrap](https://docs.blender.org/manual/en/5.1/modeling/modifiers/deform/shrinkwrap.html) modifier pages
- [Weighted Normal](https://docs.blender.org/manual/en/5.1/modeling/modifiers/normals/weighted_normal.html) · [Smooth By Angle](https://docs.blender.org/manual/en/5.1/modeling/modifiers/normals/smooth_by_angle.html) · [object shading operators](https://docs.blender.org/manual/en/5.1/scene_layout/object/editing/shading.html) · [Data Transfer](https://docs.blender.org/manual/en/5.1/modeling/modifiers/modify/data_transfer.html)
- [Attributes reference](https://docs.blender.org/manual/en/5.1/modeling/geometry_nodes/attributes_reference.html) (`bevel_weight_edge`, `custom_normal`) · [4.0 Python API release notes](https://developer.blender.org/docs/release_notes/4.0/python_api/) (bevel-weight move) · [4.1 modeling notes](https://developer.blender.org/docs/release_notes/4.1/modeling/) (Auto Smooth removal) · [4.5](https://developer.blender.org/docs/release_notes/4.5/modeling/) & [5.0 modeling notes](https://developer.blender.org/docs/release_notes/5.0/modeling/) (Manifold solver; Fast→Float)
- [Merge](https://docs.blender.org/manual/en/5.1/modeling/meshes/editing/mesh/merge.html) · [Select All by Trait](https://docs.blender.org/manual/en/5.1/modeling/meshes/selecting/all_by_trait.html) · [Edge Data](https://docs.blender.org/manual/en/5.1/modeling/meshes/editing/edge/edge_data.html) · [sidebar Transform panel](https://docs.blender.org/manual/en/5.1/modeling/meshes/editing/mesh/transform/basic.html) · [tool settings (Auto Merge)](https://docs.blender.org/manual/en/5.1/modeling/meshes/tools/tool_settings.html)
- [Numeric input](https://docs.blender.org/manual/en/5.1/scene_layout/object/editing/transform/control/numeric_input.html) · [axis locking](https://docs.blender.org/manual/en/5.1/scene_layout/object/editing/transform/control/axis_locking.html) · [apply transforms](https://docs.blender.org/manual/en/5.1/scene_layout/object/editing/apply.html) · [loop cut](https://docs.blender.org/manual/en/5.1/modeling/meshes/editing/edge/loopcut_slide.html) · [edge slide](https://docs.blender.org/manual/en/5.1/modeling/meshes/editing/edge/edge_slide.html)
- [Cycles object settings](https://docs.blender.org/manual/en/5.1/render/cycles/object_settings/object_data.html) — Shadow Terminator offsets
- Addon table verified against vendor pages (extensions.blender.org, superhivemarket.com, machin3.io), 2026-07
