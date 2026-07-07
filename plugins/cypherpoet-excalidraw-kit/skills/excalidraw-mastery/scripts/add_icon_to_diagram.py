#!/usr/bin/env python3
"""Insert an icon from a split Excalidraw library into an existing scene.

Reads an icon's element array (produced by split_excalidraw_library.py), offsets
it to a target position, regenerates every id / groupId (and rewrites internal
bindings, containerIds, and boundElements to match) so it can't collide with the
diagram it's dropped into, then appends it. Works with any library (AWS, GCP,
Azure, Kubernetes, ...). Pure standard library.

Usage:
    python add_icon_to_diagram.py <diagram.excalidraw> <icon_name> <x> <y> [OPTIONS]

Options:
    --library-path PATH    Icon library directory (default: libraries/aws-architecture-icons)
    --label TEXT           Add a text label centered below the icon
    --no-safe-edit         Write the file in place instead of via a .edit rename
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
import zlib
from pathlib import Path


def unique_id() -> str:
    return uuid.uuid4().hex[:16]


def stable_seed(text: str) -> int:
    return zlib.crc32(text.encode("utf-8")) % 2_000_000_000


def bounding_box(elements: list[dict]) -> tuple[float, float, float, float]:
    xs = [e["x"] for e in elements if "x" in e]
    ys = [e["y"] for e in elements if "y" in e]
    if not xs or not ys:
        return (0.0, 0.0, 0.0, 0.0)
    min_x, min_y = min(xs), min(ys)
    max_x = max(e["x"] + e.get("width", 0) for e in elements if "x" in e)
    max_y = max(e["y"] + e.get("height", 0) for e in elements if "y" in e)
    return (min_x, min_y, max_x, max_y)


def transform_icon(elements: list[dict], target_x: float, target_y: float) -> list[dict]:
    """Offset to (target_x, target_y) and remap every id so nothing collides."""
    if not elements:
        return []
    min_x, min_y, _, _ = bounding_box(elements)
    offset_x, offset_y = target_x - min_x, target_y - min_y

    id_map = {e["id"]: unique_id() for e in elements if "id" in e}
    group_map: dict[str, str] = {}
    for el in elements:
        for gid in el.get("groupIds", []) or []:
            group_map.setdefault(gid, unique_id())

    out: list[dict] = []
    for el in elements:
        new = dict(el)
        if "x" in new:
            new["x"] += offset_x
        if "y" in new:
            new["y"] += offset_y
        if "id" in new:
            new["id"] = id_map[new["id"]]
        if new.get("groupIds"):
            new["groupIds"] = [group_map[g] for g in new["groupIds"]]
        for side in ("startBinding", "endBinding"):
            binding = new.get(side)
            if isinstance(binding, dict) and binding.get("elementId") in id_map:
                binding = dict(binding)
                binding["elementId"] = id_map[binding["elementId"]]
                new[side] = binding
        if new.get("containerId") in id_map:
            new["containerId"] = id_map[new["containerId"]]
        if isinstance(new.get("boundElements"), list):
            new["boundElements"] = [
                {**b, "id": id_map[b["id"]]} if isinstance(b, dict) and b.get("id") in id_map else b
                for b in new["boundElements"]
            ]
        out.append(new)
    return out


def load_icon(icon_name: str, library_path: Path) -> list[dict]:
    icon_file = library_path / "icons" / f"{icon_name}.json"
    if not icon_file.exists():
        raise FileNotFoundError(f"Icon not found: {icon_file}")
    return json.loads(icon_file.read_text(encoding="utf-8")).get("elements", [])


def text_label(text: str, x: float, y: float) -> dict:
    return {
        "id": unique_id(),
        "type": "text",
        "x": x,
        "y": y,
        "width": len(text) * 10,
        "height": 20,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": stable_seed(text),
        "version": 1,
        "versionNonce": stable_seed("nonce" + text),
        "isDeleted": False,
        "boundElements": [],
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": 16,
        "fontFamily": 5,
        "textAlign": "center",
        "verticalAlign": "top",
        "containerId": None,
        "originalText": text,
        "autoResize": True,
        "lineHeight": 1.25,
    }


def add_icon(diagram_path: Path, icon_name: str, x: float, y: float, library_path: Path, label: str | None) -> None:
    elements = transform_icon(load_icon(icon_name, library_path), x, y)
    print(f"Loaded '{icon_name}' ({len(elements)} elements) -> ({x}, {y})")

    if label and elements:
        min_x, _, max_x, max_y = bounding_box(elements)
        label_x = min_x + (max_x - min_x) / 2 - (len(label) * 5)
        elements.append(text_label(label, label_x, max_y + 10))
        print(f"Added label: {label!r}")

    diagram = json.loads(diagram_path.read_text(encoding="utf-8"))
    diagram.setdefault("elements", []).extend(elements)
    diagram_path.write_text(json.dumps(diagram, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {diagram_path} (now {len(diagram['elements'])} elements)")


def edit_paths(diagram_path: Path, safe_edit: bool) -> tuple[Path, Path | None]:
    """Rename to a .edit sidecar during the write so a live editor can't clobber it."""
    if not safe_edit or diagram_path.suffix != ".excalidraw":
        return diagram_path, None
    edit_path = diagram_path.with_suffix(".excalidraw.edit")
    if edit_path.exists():
        raise FileExistsError(f"Edit sidecar already exists: {edit_path}")
    diagram_path.rename(edit_path)
    return edit_path, diagram_path


def finalize(work_path: Path, final_path: Path | None) -> None:
    if final_path is None:
        return
    if final_path.exists():
        final_path.unlink()
    work_path.rename(final_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert an icon from a split Excalidraw library.")
    parser.add_argument("diagram", type=Path)
    parser.add_argument("icon_name")
    parser.add_argument("x", type=float)
    parser.add_argument("y", type=float)
    default_lib = Path(__file__).parent / "libraries" / "aws-architecture-icons"
    parser.add_argument("--library-path", type=Path, default=default_lib)
    parser.add_argument("--label", default=None)
    parser.add_argument("--no-safe-edit", action="store_true", help="Write in place")
    args = parser.parse_args()

    if not args.diagram.exists():
        parser.error(f"Diagram not found: {args.diagram}")
    if not args.library_path.exists():
        parser.error(f"Library path not found: {args.library_path}")

    try:
        work_path, final_path = edit_paths(args.diagram, safe_edit=not args.no_safe_edit)
        try:
            add_icon(work_path, args.icon_name, args.x, args.y, args.library_path, args.label)
        finally:
            finalize(work_path, final_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
