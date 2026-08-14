#!/usr/bin/env python3
"""Seed (or re-seed) filament-sync-manifest.json from the raw upstream corpus.

The manifest records, for the pinned Filament tag:
  - each upstream SOURCE file (repo path + raw URL + a raw_hash of its content)
    and which distilled reference files it feeds, and
  - each distilled REFERENCE file with a content_hash.

raw_hash / content_hash are COMPUTED here (never hand-written) via the shared
canonicalization in compute_hash.py, so they're reproducible and trustworthy.

The SOURCES map below is design intent — the human-authored knowledge of which
upstream doc feeds which reference. Hashes are derived from it.

Usage:
  python build_manifest.py \
      --raw-dir <workspace>/raw \
      --references-dir <skill>/references \
      --out <skill>/sync/filament-sync-manifest.json \
      --tag v1.75.0 --version 1.75.0 --date 2026-08-14
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compute_hash as ch

RAW_BASE_URL = "https://raw.githubusercontent.com/google/filament"

# (local path under --raw-dir, repo-relative path at the tag, category, [reference files fed])
SOURCES = [
    # The two core books (Markdeep source).
    ("books/filament-book.md.html", "docs_src/src_markdeep/Filament.md.html", "book",
     ["concepts-pbr-shading.md", "concepts-lighting-ibl.md", "concepts-imaging-pipeline.md"]),
    ("books/materials-book.md.html", "docs_src/src_markdeep/Materials.md.html", "book",
     ["materials-models.md", "materials-definition-language.md", "materials-compiling-matc.md",
      "materials-properties-reference.md"]),
    # Technical notes (mdBook source).
    ("notes/material_properties.md", "docs_src/src_mdbook/src/notes/material_properties.md", "note",
     ["materials-properties-reference.md"]),
    ("notes/framegraph.md", "docs_src/src_mdbook/src/notes/framegraph.md", "note", ["tooling.md"]),
    ("notes/performance_analysis.md", "docs_src/src_mdbook/src/notes/performance_analysis.md", "note", ["tooling.md"]),
    ("notes/metal_debugging.md", "docs_src/src_mdbook/src/notes/metal_debugging.md", "note", ["tooling.md"]),
    ("notes/vulkan_debugging.md", "docs_src/src_mdbook/src/notes/vulkan_debugging.md", "note", ["tooling.md"]),
    # Public C++ headers (API ground truth).
    ("headers/Engine.h", "filament/include/filament/Engine.h", "header", ["engine-api-core.md"]),
    ("headers/SwapChain.h", "filament/include/filament/SwapChain.h", "header", ["engine-api-core.md"]),
    ("headers/Renderer.h", "filament/include/filament/Renderer.h", "header", ["engine-api-core.md"]),
    ("headers/View.h", "filament/include/filament/View.h", "header",
     ["engine-api-core.md", "concepts-imaging-pipeline.md"]),
    ("headers/Scene.h", "filament/include/filament/Scene.h", "header", ["engine-api-core.md"]),
    ("headers/Camera.h", "filament/include/filament/Camera.h", "header",
     ["engine-api-core.md", "concepts-imaging-pipeline.md"]),
    ("headers/RenderableManager.h", "filament/include/filament/RenderableManager.h", "header",
     ["engine-api-entities-components.md"]),
    ("headers/LightManager.h", "filament/include/filament/LightManager.h", "header",
     ["engine-api-entities-components.md", "concepts-lighting-ibl.md"]),
    ("headers/TransformManager.h", "filament/include/filament/TransformManager.h", "header",
     ["engine-api-entities-components.md"]),
    ("headers/Box.h", "filament/include/filament/Box.h", "header", ["engine-api-entities-components.md"]),
    ("headers/VertexBuffer.h", "filament/include/filament/VertexBuffer.h", "header", ["engine-api-resources.md"]),
    ("headers/IndexBuffer.h", "filament/include/filament/IndexBuffer.h", "header", ["engine-api-resources.md"]),
    ("headers/BufferObject.h", "filament/include/filament/BufferObject.h", "header", ["engine-api-resources.md"]),
    ("headers/Texture.h", "filament/include/filament/Texture.h", "header", ["engine-api-resources.md"]),
    ("headers/TextureSampler.h", "filament/include/filament/TextureSampler.h", "header", ["engine-api-resources.md"]),
    ("headers/Material.h", "filament/include/filament/Material.h", "header", ["engine-api-resources.md"]),
    ("headers/MaterialInstance.h", "filament/include/filament/MaterialInstance.h", "header", ["engine-api-resources.md"]),
    ("headers/Skybox.h", "filament/include/filament/Skybox.h", "header",
     ["engine-api-resources.md", "concepts-lighting-ibl.md"]),
    ("headers/IndirectLight.h", "filament/include/filament/IndirectLight.h", "header",
     ["engine-api-resources.md", "concepts-lighting-ibl.md"]),
    ("headers/Exposure.h", "filament/include/filament/Exposure.h", "header", ["concepts-imaging-pipeline.md"]),
    ("headers/ColorGrading.h", "filament/include/filament/ColorGrading.h", "header", ["concepts-imaging-pipeline.md"]),
    ("headers/ToneMapper.h", "filament/include/filament/ToneMapper.h", "header", ["concepts-imaging-pipeline.md"]),
    ("headers/Options.h", "filament/include/filament/Options.h", "header", ["concepts-imaging-pipeline.md"]),
    ("headers/Color.h", "filament/include/filament/Color.h", "header", ["concepts-imaging-pipeline.md"]),
    ("headers/ColorSpace.h", "filament/include/filament/ColorSpace.h", "header", ["concepts-imaging-pipeline.md"]),
    ("headers/RenderTarget.h", "filament/include/filament/RenderTarget.h", "header", ["engine-api-resources.md"]),
    ("headers/Viewport.h", "filament/include/filament/Viewport.h", "header", ["engine-api-core.md"]),
    ("headers/Frustum.h", "filament/include/filament/Frustum.h", "header", ["engine-api-core.md"]),
    # gltfio public headers.
    ("gltfio-headers/AssetLoader.h", "libs/gltfio/include/gltfio/AssetLoader.h", "gltfio-header", ["assets-gltf.md"]),
    ("gltfio-headers/ResourceLoader.h", "libs/gltfio/include/gltfio/ResourceLoader.h", "gltfio-header", ["assets-gltf.md"]),
    ("gltfio-headers/FilamentAsset.h", "libs/gltfio/include/gltfio/FilamentAsset.h", "gltfio-header", ["assets-gltf.md"]),
    ("gltfio-headers/FilamentInstance.h", "libs/gltfio/include/gltfio/FilamentInstance.h", "gltfio-header", ["assets-gltf.md"]),
    ("gltfio-headers/Animator.h", "libs/gltfio/include/gltfio/Animator.h", "gltfio-header", ["assets-gltf.md"]),
    ("gltfio-headers/MaterialProvider.h", "libs/gltfio/include/gltfio/MaterialProvider.h", "gltfio-header", ["assets-gltf.md"]),
    ("gltfio-headers/TextureProvider.h", "libs/gltfio/include/gltfio/TextureProvider.h", "gltfio-header", ["assets-gltf.md"]),
    # Android utility binding.
    ("headers-android/KTX1Loader.kt",
     "android/filament-utils-android/src/main/java/com/google/android/filament/utils/KTX1Loader.kt",
     "android-binding", ["platform-android.md"]),
    # CLI tools (tools/<name>/README.md).
    ("tools/cmgen.md", "tools/cmgen/README.md", "tool", ["tooling.md", "concepts-lighting-ibl.md"]),
    ("tools/filamesh.md", "tools/filamesh/README.md", "tool", ["tooling.md", "assets-gltf.md"]),
    ("tools/mipgen.md", "tools/mipgen/README.md", "tool", ["tooling.md"]),
    ("tools/matinfo.md", "tools/matinfo/README.md", "tool", ["tooling.md"]),
    ("tools/specgen.md", "tools/specgen/README.md", "tool", ["tooling.md"]),
    ("tools/normal-blending.md", "tools/normal-blending/README.md", "tool", ["tooling.md"]),
    ("tools/roughness-prefilter.md", "tools/roughness-prefilter/README.md", "tool", ["tooling.md"]),
    # Libraries (libs/<name>/README.md).
    ("libs/gltfio.md", "libs/gltfio/README.md", "lib", ["assets-gltf.md"]),
    ("libs/iblprefilter.md", "libs/iblprefilter/README.md", "lib", ["concepts-lighting-ibl.md", "tooling.md"]),
    ("libs/matdbg.md", "libs/matdbg/README.md", "lib", ["tooling.md"]),
    ("libs/filamat.md", "libs/filamat/README.md", "lib", ["materials-compiling-matc.md", "tooling.md"]),
    ("libs/viewer.md", "libs/viewer/README.md", "lib", ["tooling.md"]),
    # Setup / integration.
    ("setup/repo-README.md", "README.md", "setup",
     ["platform-cpp.md", "platform-android.md", "engine-api-core.md"]),
    ("setup/BUILDING.md", "BUILDING.md", "setup", ["platform-cpp.md"]),
    ("setup/ios.md", "docs_src/src_mdbook/src/samples/ios.md", "setup", ["platform-cpp.md"]),
    ("setup/samples-README.md", "docs_src/src_mdbook/src/samples/README.md", "setup", ["platform-cpp.md"]),
    # Web tutorials.
    ("web/tutorials.md", "docs_src/src_mdbook/src/samples/web/tutorials.md", "web", ["platform-web.md"]),
    ("web/triangle.md", "web/examples/triangle.md", "web", ["platform-web.md"]),
    ("web/redball.md", "web/examples/redball.md", "web", ["platform-web.md"]),
    ("web/suzanne.md", "web/examples/suzanne.md", "web", ["platform-web.md", "assets-gltf.md"]),
    ("web/samples.md", "docs_src/src_mdbook/src/samples/web/samples.md", "web", ["platform-web.md"]),
    # C++ samples.
    ("samples-cpp/hellotriangle.cpp", "samples/hellotriangle.cpp", "sample-cpp",
     ["engine-api-core.md", "platform-cpp.md"]),
    ("samples-cpp/hellopbr.cpp", "samples/hellopbr.cpp", "sample-cpp", ["engine-api-entities-components.md"]),
    ("samples-cpp/lightbulb.cpp", "samples/lightbulb.cpp", "sample-cpp",
     ["engine-api-resources.md", "concepts-lighting-ibl.md"]),
    ("samples-cpp/suzanne.cpp", "samples/suzanne.cpp", "sample-cpp",
     ["assets-gltf.md", "engine-api-resources.md"]),
    # Android samples.
    ("samples-android/hellotriangle-MainActivity.kt",
     "android/samples/sample-hello-triangle/src/main/java/com/google/android/filament/hellotriangle/MainActivity.kt",
     "sample-android", ["platform-android.md"]),
    ("samples-android/litcube-MainActivity.kt",
     "android/samples/sample-lit-cube/src/main/java/com/google/android/filament/litcube/MainActivity.kt",
     "sample-android", ["platform-android.md"]),
    ("samples-android/ibl-MainActivity.kt",
     "android/samples/sample-image-based-lighting/src/main/java/com/google/android/filament/ibl/MainActivity.kt",
     "sample-android", ["platform-android.md"]),
    # Release / versioning.
    ("release/maven.md", "docs_src/src_mdbook/src/release/maven.md", "release", ["platform-android.md"]),
    ("release/versioning.md", "docs_src/src_mdbook/src/release/versioning.md", "release", []),
]


def main():
    ap = argparse.ArgumentParser(description="Seed the Filament sync manifest.")
    ap.add_argument("--raw-dir", required=True, help="workspace raw/ dir of downloaded sources")
    ap.add_argument("--references-dir", required=True, help="skill references/ dir")
    ap.add_argument("--out", required=True, help="output manifest path")
    ap.add_argument("--tag", default="v1.75.0")
    ap.add_argument("--version", default="1.75.0")
    ap.add_argument("--date", required=True, help="sync date YYYY-MM-DD (pass in; not derived)")
    args = ap.parse_args()

    referenced = set()
    sources_out = []
    missing = []
    for local, repo_path, category, refs in SOURCES:
        raw_path = os.path.join(args.raw_dir, local)
        if not os.path.exists(raw_path):
            missing.append(local)
            continue
        sources_out.append({
            "repo_path": repo_path,
            "url": f"{RAW_BASE_URL}/{args.tag}/{repo_path}",
            "category": category,
            "raw_hash": ch.hash_file(raw_path),
            "reference_files": sorted(refs),
        })
        referenced.update(refs)

    refs_out = []
    for fname in sorted(os.listdir(args.references_dir)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(args.references_dir, fname)
        feeding = sorted(repo_path for (local, repo_path, cat, rfs) in SOURCES if fname in rfs)
        refs_out.append({
            "file": fname,
            "content_hash": ch.hash_file(path),
            "source_count": len(feeding),
        })

    manifest = {
        "schema_version": 1,
        "skill": "google-filament-mastery",
        "source_repo": "https://github.com/google/filament",
        "source_tag": args.tag,
        "filament_version": args.version,
        "last_full_sync": args.date,
        "hash_algorithm": "sha256",
        "hash_canonicalization": ch.CANONICALIZATION_VERSION,
        "sources": sorted(sources_out, key=lambda s: s["repo_path"]),
        "reference_files": refs_out,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"wrote {args.out}")
    print(f"  sources: {len(sources_out)}  reference_files: {len(refs_out)}")
    if missing:
        print(f"  WARNING: {len(missing)} source(s) missing from raw-dir: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
