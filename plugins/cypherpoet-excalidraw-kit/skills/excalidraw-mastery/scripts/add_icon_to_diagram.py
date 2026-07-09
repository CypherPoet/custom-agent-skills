#!/usr/bin/env python3
"""Insert an icon from a split Excalidraw library into an existing scene.

Reads an icon's element array (produced by split_excalidraw_library.py), offsets
it to a target position, regenerates every id / groupId (and rewrites internal
bindings, containerIds, frameIds, and boundElements to match) so it can't collide
with the diagram it's dropped into, then appends it. Works with any library (AWS,
GCP, Azure, Kubernetes, ...). Pure standard library.

The scene is written atomically (temp file + os.replace), so an interrupted write
leaves the original intact rather than corrupting it.

Usage:
    python add_icon_to_diagram.py <diagram.excalidraw> <icon_name> <x> <y> [OPTIONS]

Options:
    --library-path PATH    Icon library directory (default: libraries/aws-architecture-icons)
    --label TEXT           Add a text label centered below the icon
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
import zlib
from pathlib import Path


def unique_id() -> str:
    return uuid.uuid4().hex[:16]


def stable_seed(text: str) -> int:
    return zlib.crc32(text.encode("utf-8")) % 2_000_000_000


def _num(value: object) -> float:
    """Coerce a coordinate/size to a number; treat missing/non-numeric as 0."""
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def bounding_box(elements: list[dict]) -> tuple[float, float, float, float]:
    """Min/max extent across elements, honoring arrow/line `points` and abs sizes.

    Matches render_excalidraw.py's box: linear elements carry their real extent in
    `points` (with possibly zero/negative width/height), so we walk those.
    """
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for el in elements:
        x, y = _num(el.get("x")), _num(el.get("y"))
        if el.get("type") in ("arrow", "line") and isinstance(el.get("points"), list):
            for pt in el["points"]:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    px, py = _num(pt[0]), _num(pt[1])
                    min_x, min_y = min(min_x, x + px), min(min_y, y + py)
                    max_x, max_y = max(max_x, x + px), max(max_y, y + py)
        else:
            w, h = abs(_num(el.get("width"))), abs(_num(el.get("height")))
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x + w), max(max_y, y + h)
    if min_x == float("inf"):
        return (0.0, 0.0, 0.0, 0.0)
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
        if new.get("frameId") in id_map:
            new["frameId"] = id_map[new["frameId"]]
        if isinstance(new.get("boundElements"), list):
            new["boundElements"] = [
                {**b, "id": id_map[b["id"]]} if isinstance(b, dict) and b.get("id") in id_map else b
                for b in new["boundElements"]
            ]
        out.append(new)
    return out


def _sanitize(name: str) -> str:
    """Mirror split_excalidraw_library.py's filename sanitization."""
    stem = re.sub(r"[^\w\-.]", "", name.replace(" ", "-"))
    return re.sub(r"-+", "-", stem).strip("-")


def load_icon(icon_name: str, library_path: Path) -> list[dict]:
    icons_dir = library_path / "icons"
    # Accept either the raw display name (as shown in reference.md) or the
    # sanitized filename stem — split writes files under the sanitized name.
    for stem in dict.fromkeys([icon_name, _sanitize(icon_name)]):
        icon_file = icons_dir / f"{stem}.json"
        if icon_file.exists():
            return json.loads(icon_file.read_text(encoding="utf-8")).get("elements", [])
    raise FileNotFoundError(f"Icon not found: {icons_dir / (icon_name + '.json')} (also tried the sanitized name)")


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


def write_atomic(path: Path, data: dict) -> None:
    """Write JSON to a temp file in the same directory, then atomically replace
    `path`. The original is never truncated, so an interrupted write leaves it
    intact — unlike an in-place write or a rename-the-original-away sidecar."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


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
    write_atomic(diagram_path, diagram)
    print(f"Wrote {diagram_path} (now {len(diagram['elements'])} elements)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert an icon from a split Excalidraw library.")
    parser.add_argument("diagram", type=Path)
    parser.add_argument("icon_name")
    parser.add_argument("x", type=float)
    parser.add_argument("y", type=float)
    default_lib = Path(__file__).parent / "libraries" / "aws-architecture-icons"
    parser.add_argument("--library-path", type=Path, default=default_lib)
    parser.add_argument("--label", default=None)
    args = parser.parse_args()

    if not args.diagram.exists():
        parser.error(f"Diagram not found: {args.diagram}")
    if not args.library_path.exists():
        parser.error(f"Library path not found: {args.library_path}")

    try:
        add_icon(args.diagram, args.icon_name, args.x, args.y, args.library_path, args.label)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
