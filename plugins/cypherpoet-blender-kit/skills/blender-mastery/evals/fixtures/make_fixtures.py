"""Deterministic fixture generation for the hard-surface evals (ids 10 and 11).

Run headless; no .blend binaries live in git:

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
        --python make_fixtures.py -- --out /path/to/output/dir

Produces:
  bracket_dirty.blend — boolean-aftermath mess for the repair eval: a hole
    (non-manifold boundary edges), exact duplicate vertices at the joint
    seam of two unwelded shells, and unapplied rotation + non-uniform
    scale. Self-checked before saving.
  part.blend — clean stepped slab for the smoothing/bevel-weight trap eval:
    a mix of >45° edges (plateau walls) and coplanar edges (flat top ring).
"""
import argparse
import math
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector


def clean_file():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(coll):
            coll.remove(block)


def link_object(name, me):
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_bracket_dirty(out_dir):
    clean_file()
    me = bpy.data.meshes.new("bracket_dirty")
    bm = bmesh.new()

    # Two abutting boxes forming an L, created separately (unwelded shells).
    # Two of box B's base corners coincide exactly with box A verts — the
    # duplicate-vert defect the repair must merge; the other two sit as
    # T-junctions on box A's top edge.
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts_a = ret["verts"]
    bmesh.ops.transform(bm, verts=verts_a, matrix=Matrix.Diagonal((2.0, 0.5, 0.5, 1.0)))
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts_b = ret["verts"]
    bmesh.ops.transform(bm, verts=verts_b, matrix=Matrix.Diagonal((0.5, 0.5, 2.0, 1.0)))
    bmesh.ops.translate(bm, verts=verts_b, vec=Vector((-0.75, 0.0, 1.25)))

    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # Defect: hole — delete the +X end cap of the long arm.
    end_face = max(bm.faces, key=lambda f: f.calc_center_median().x)
    bmesh.ops.delete(bm, geom=[end_face], context='FACES')

    bm.to_mesh(me)
    bm.free()

    obj = link_object("bracket_dirty", me)
    obj.rotation_euler = (0.1, 0.0, 0.2)
    obj.scale = (1.25, 1.0, 0.8)

    # Self-check: the defects must actually exist.
    check = bmesh.new()
    check.from_mesh(me)
    non_manifold = sum(1 for e in check.edges if not e.is_manifold)
    coords = {}
    doubles = 0
    for v in check.verts:
        key = (round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6))
        doubles += coords.get(key, 0)
        coords[key] = coords.get(key, 0) + 1
    check.free()
    assert non_manifold > 0, "fixture bug: no non-manifold edges"
    assert doubles > 0, "fixture bug: no duplicate vertices"
    assert any(abs(r) > 1e-6 for r in obj.rotation_euler), "fixture bug: rotation already applied"
    assert len({round(s, 6) for s in obj.scale}) > 1, "fixture bug: scale is uniform"

    path = f"{out_dir}/bracket_dirty.blend"
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f"FIXTURE-OK bracket_dirty.blend non_manifold={non_manifold} doubles={doubles}")


def make_part(out_dir):
    clean_file()
    me = bpy.data.meshes.new("part")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=list(bm.verts), matrix=Matrix.Diagonal((2.0, 2.0, 0.5, 1.0)))

    # Raise a plateau: inset the top face, extrude the inset upward — one
    # welded shell with 90° plateau walls and coplanar ring edges on top.
    bm.faces.ensure_lookup_table()
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    # inset shrinks `top` in place into the inner face and rings it with new
    # quads. Reuse `top` as the plateau: re-deriving it with max(z) would tie
    # among the inner face and its four coplanar ring faces and resolve by
    # iteration order, so a future Blender that reorders faces could silently
    # extrude a border quad instead of the centre.
    bmesh.ops.inset_individual(bm, faces=[top], thickness=0.5)
    plateau = top
    ext = bmesh.ops.extrude_face_region(bm, geom=[plateau])
    new_verts = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=new_verts, vec=Vector((0.0, 0.0, 0.5)))
    # extrude_face_region leaves the original face behind — remove interior face
    bmesh.ops.delete(bm, geom=[plateau], context='FACES')

    bm.to_mesh(me)
    bm.free()

    obj = link_object("part", me)

    check = bmesh.new()
    check.from_mesh(me)
    non_manifold = sum(1 for e in check.edges if not e.is_manifold)
    steep = sum(1 for e in check.edges if len(e.link_faces) == 2 and e.calc_face_angle() > math.radians(45))
    flat = sum(1 for e in check.edges if len(e.link_faces) == 2 and e.calc_face_angle() < math.radians(5))
    check.free()
    assert non_manifold == 0, f"fixture bug: part not manifold ({non_manifold})"
    assert steep > 0 and flat > 0, f"fixture bug: need angle mix (steep={steep} flat={flat})"

    path = f"{out_dir}/part.blend"
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f"FIXTURE-OK part.blend steep_edges={steep} flat_edges={flat}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    make_bracket_dirty(args.out)
    make_part(args.out)
    print("FIXTURES-DONE")
