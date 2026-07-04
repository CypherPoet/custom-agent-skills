#!/usr/bin/env python3
"""Append a straight connector (arrow) between two points in an Excalidraw scene.

A quick way to wire up two positions without hand-writing the arrow element and
its relative `points` array. Optionally labels the arrow and sets a line style.
For arrows that should *stay attached* when shapes move, bind them instead (set
startBinding/endBinding to element ids) — see references/elements.md. Pure stdlib.

Usage:
    python add_arrow.py <diagram.excalidraw> <from_x> <from_y> <to_x> <to_y> [OPTIONS]

Options:
    --style {solid|dashed|dotted}   Line style (default: solid)
    --color HEX                     Stroke color (default: #1e1e1e)
    --label TEXT                    Text label near the arrow midpoint
    --no-safe-edit                  Write in place instead of via a .edit rename
"""

from __future__ import annotations

import argparse
import json
import uuid
import zlib
from pathlib import Path


def unique_id() -> str:
    return uuid.uuid4().hex[:16]


def stable_seed(text: str) -> int:
    return zlib.crc32(text.encode("utf-8")) % 2_000_000_000


def make_arrow(from_x, from_y, to_x, to_y, style, color, label) -> list[dict]:
    key = f"{from_x},{from_y},{to_x},{to_y}"
    arrow = {
        "id": unique_id(),
        "type": "arrow",
        "x": from_x,
        "y": from_y,
        "width": to_x - from_x,
        "height": to_y - from_y,
        "angle": 0,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": style,
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 2},
        "seed": stable_seed(key),
        "version": 1,
        "versionNonce": stable_seed("nonce" + key),
        "isDeleted": False,
        "boundElements": [],
        "link": None,
        "locked": False,
        # points are relative to (x, y); the first point is always the origin.
        "points": [[0, 0], [to_x - from_x, to_y - from_y]],
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "lastCommittedPoint": None,
    }
    elements = [arrow]
    if label:
        mid_x = (from_x + to_x) / 2 - (len(label) * 5)
        mid_y = (from_y + to_y) / 2 - 10
        elements.append({
            "id": unique_id(),
            "type": "text",
            "x": mid_x,
            "y": mid_y,
            "width": len(label) * 10,
            "height": 20,
            "angle": 0,
            "strokeColor": color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "groupIds": [],
            "frameId": None,
            "roundness": None,
            "seed": stable_seed("label" + label + key),
            "version": 1,
            "versionNonce": stable_seed("labelnonce" + label + key),
            "isDeleted": False,
            "boundElements": [],
            "link": None,
            "locked": False,
            "text": label,
            "fontSize": 14,
            "fontFamily": 5,
            "textAlign": "center",
            "verticalAlign": "top",
            "containerId": None,
            "originalText": label,
            "autoResize": True,
            "lineHeight": 1.25,
        })
    return elements


def add_arrow(diagram_path: Path, coords, style, color, label) -> None:
    elements = make_arrow(*coords, style, color, label)
    diagram = json.loads(diagram_path.read_text(encoding="utf-8"))
    diagram.setdefault("elements", []).extend(elements)
    diagram_path.write_text(json.dumps(diagram, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Added arrow{' + label' if label else ''}; {diagram_path} now has {len(diagram['elements'])} elements")


def edit_paths(diagram_path: Path, safe_edit: bool) -> tuple[Path, Path | None]:
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
    parser = argparse.ArgumentParser(description="Append an arrow connector to an Excalidraw scene.")
    parser.add_argument("diagram", type=Path)
    parser.add_argument("from_x", type=float)
    parser.add_argument("from_y", type=float)
    parser.add_argument("to_x", type=float)
    parser.add_argument("to_y", type=float)
    parser.add_argument("--style", choices=["solid", "dashed", "dotted"], default="solid")
    parser.add_argument("--color", default="#1e1e1e")
    parser.add_argument("--label", default=None)
    parser.add_argument("--no-safe-edit", action="store_true", help="Write in place")
    args = parser.parse_args()

    if not args.diagram.exists():
        parser.error(f"Diagram not found: {args.diagram}")

    coords = (args.from_x, args.from_y, args.to_x, args.to_y)
    work_path, final_path = edit_paths(args.diagram, safe_edit=not args.no_safe_edit)
    try:
        add_arrow(work_path, coords, args.style, args.color, args.label)
    finally:
        finalize(work_path, final_path)


if __name__ == "__main__":
    main()
