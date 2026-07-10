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

The scene is written atomically (temp file + os.replace), so an interrupted write
leaves the original intact rather than corrupting it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
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
        "width": abs(to_x - from_x),
        "height": abs(to_y - from_y),
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


def add_arrow(diagram_path: Path, coords, style, color, label) -> None:
    elements = make_arrow(*coords, style, color, label)
    diagram = json.loads(diagram_path.read_text(encoding="utf-8"))
    diagram.setdefault("elements", []).extend(elements)
    write_atomic(diagram_path, diagram)
    print(f"Added arrow{' + label' if label else ''}; {diagram_path} now has {len(diagram['elements'])} elements")


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
    args = parser.parse_args()

    if not args.diagram.exists():
        parser.error(f"Diagram not found: {args.diagram}")

    coords = (args.from_x, args.from_y, args.to_x, args.to_y)
    try:
        add_arrow(args.diagram, coords, args.style, args.color, args.label)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
