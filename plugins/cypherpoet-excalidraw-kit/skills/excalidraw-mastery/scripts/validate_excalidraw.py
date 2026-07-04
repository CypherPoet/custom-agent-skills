#!/usr/bin/env python3
"""Structurally validate an Excalidraw scene file.

Checks the things that silently break a `.excalidraw` file when you author it by
hand: malformed JSON, a wrong wrapper, duplicate element ids, and dangling
references (an arrow bound to an element that doesn't exist, a text whose
`containerId` points nowhere, a `boundElements` entry with no matching element).
Pure standard library — no dependencies, runs anywhere Python 3.8+ does.

Usage:
    python validate_excalidraw.py <file.excalidraw> [more.excalidraw ...]
    python validate_excalidraw.py scene.excalidraw --strict   # warnings fail too
    python validate_excalidraw.py scene.excalidraw --json      # machine-readable report

Exit code: 0 if every file passes (warnings allowed unless --strict), else 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Verified against packages/common/src/constants.ts (excalidraw/excalidraw).
KNOWN_TYPES = {
    "rectangle", "ellipse", "diamond", "arrow", "line", "draw",
    "text", "image", "frame", "magicframe", "embeddable", "iframe", "selection",
}
LINEAR_TYPES = {"arrow", "line"}
VALID_FONT_FAMILY = {1, 2, 3, 5, 6, 7, 8, 9, 10}
VALID_STROKE_WIDTH = {1, 2, 4, 8}
VALID_ROUGHNESS = {0, 1, 2}
VALID_FILL_STYLE = {"solid", "hachure", "cross-hatch", "zigzag"}
VALID_STROKE_STYLE = {"solid", "dashed", "dotted"}


class Report:
    def __init__(self, path: str) -> None:
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def _elem_label(el: dict, index: int) -> str:
    eid = el.get("id")
    etype = el.get("type")
    return f"elements[{index}] (id={eid!r}, type={etype!r})"


def validate(data: object, report: Report) -> None:
    """Populate `report` with errors/warnings for a parsed scene object."""
    if not isinstance(data, dict):
        report.error(f"Top level must be a JSON object, got {type(data).__name__}")
        return

    if data.get("type") != "excalidraw":
        report.error(f"Top-level 'type' must be 'excalidraw', got {data.get('type')!r}")

    version = data.get("version")
    if version != 2:
        report.warn(f"Top-level 'version' is {version!r}; the current scene format is 2")

    elements = data.get("elements")
    if elements is None:
        report.error("Missing 'elements' array")
        return
    if not isinstance(elements, list):
        report.error(f"'elements' must be an array, got {type(elements).__name__}")
        return

    live = [el for el in elements if isinstance(el, dict) and not el.get("isDeleted")]
    if not live:
        report.warn("'elements' has no live (non-deleted) elements — nothing will render")

    # First pass: collect ids, catch duplicates and missing required fields.
    ids: dict[str, int] = {}
    id_set: set[str] = set()
    for i, el in enumerate(elements):
        if not isinstance(el, dict):
            report.error(f"elements[{i}] must be an object, got {type(el).__name__}")
            continue
        eid = el.get("id")
        etype = el.get("type")
        if not isinstance(eid, str) or not eid:
            report.error(f"elements[{i}] is missing a non-empty string 'id'")
        else:
            if eid in ids:
                report.error(f"Duplicate id {eid!r} (elements[{ids[eid]}] and elements[{i}])")
            ids.setdefault(eid, i)
            id_set.add(eid)
        if not isinstance(etype, str) or not etype:
            report.error(f"{_elem_label(el, i)} is missing a non-empty string 'type'")
        elif etype not in KNOWN_TYPES:
            report.warn(f"{_elem_label(el, i)} has an unrecognized type {etype!r}")

    # Second pass: geometry, style ranges, and reference integrity.
    for i, el in enumerate(elements):
        if not isinstance(el, dict) or el.get("isDeleted"):
            continue
        etype = el.get("type")
        where = _elem_label(el, i)

        for axis in ("x", "y"):
            if not isinstance(el.get(axis), (int, float)):
                report.warn(f"{where} is missing numeric '{axis}'")

        _check_style(el, where, report)

        if etype in LINEAR_TYPES:
            pts = el.get("points")
            if not isinstance(pts, list) or len(pts) < 2:
                report.warn(f"{where} should have a 'points' array with at least 2 points")
            for side in ("startBinding", "endBinding"):
                _check_binding(el.get(side), side, where, id_set, report)

        if etype == "text":
            cid = el.get("containerId")
            if cid is not None and cid not in id_set:
                report.error(f"{where} containerId {cid!r} references no existing element")

        _check_bound_elements(el, where, id_set, report)


def _check_style(el: dict, where: str, report: Report) -> None:
    fam = el.get("fontFamily")
    if fam is not None and fam not in VALID_FONT_FAMILY:
        report.warn(
            f"{where} fontFamily {fam!r} is not a standard value "
            f"(5=Excalifont, 6=Nunito, 8=Comic Shanns, 3=Cascadia, 2=Helvetica, 1=Virgil)"
        )
    sw = el.get("strokeWidth")
    if sw is not None and sw not in VALID_STROKE_WIDTH:
        report.warn(f"{where} strokeWidth {sw!r} is nonstandard (use 1=thin, 2=medium, 4=bold)")
    rough = el.get("roughness")
    if rough is not None and rough not in VALID_ROUGHNESS:
        report.warn(f"{where} roughness {rough!r} is out of range (0=architect, 1=artist, 2=cartoonist)")
    fill = el.get("fillStyle")
    if fill is not None and fill not in VALID_FILL_STYLE:
        report.warn(f"{where} fillStyle {fill!r} is nonstandard ({sorted(VALID_FILL_STYLE)})")
    stroke = el.get("strokeStyle")
    if stroke is not None and stroke not in VALID_STROKE_STYLE:
        report.warn(f"{where} strokeStyle {stroke!r} is nonstandard ({sorted(VALID_STROKE_STYLE)})")


def _check_binding(binding: object, side: str, where: str, id_set: set[str], report: Report) -> None:
    if binding is None:
        return
    if not isinstance(binding, dict):
        report.warn(f"{where} {side} should be an object or null")
        return
    target = binding.get("elementId")
    if target is None:
        report.warn(f"{where} {side} has no 'elementId'")
    elif target not in id_set:
        report.error(f"{where} {side}.elementId {target!r} references no existing element")


def _check_bound_elements(el: dict, where: str, id_set: set[str], report: Report) -> None:
    bound = el.get("boundElements")
    if bound is None:
        return
    if not isinstance(bound, list):
        report.warn(f"{where} boundElements should be an array or null")
        return
    for entry in bound:
        if isinstance(entry, dict) and "id" in entry:
            if entry["id"] not in id_set:
                report.warn(f"{where} boundElements references missing id {entry['id']!r}")


def validate_file(path: Path) -> Report:
    report = Report(str(path))
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.error(f"Cannot read file: {exc}")
        return report
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        report.error(f"Invalid JSON: {exc}")
        return report
    validate(data, report)
    return report


def _print_human(report: Report, strict: bool) -> None:
    status = "PASS" if (report.ok and (not strict or not report.warnings)) else "FAIL"
    print(f"[{status}] {report.path}")
    for msg in report.errors:
        print(f"  ERROR: {msg}")
    for msg in report.warnings:
        print(f"  WARN:  {msg}")
    if report.ok and not report.warnings:
        print("  No issues found.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Structurally validate .excalidraw scene files.")
    parser.add_argument("files", nargs="+", type=Path, help="One or more .excalidraw files")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit a JSON report")
    args = parser.parse_args()

    reports = [validate_file(p) for p in args.files]

    if args.as_json:
        payload = [
            {"file": r.path, "ok": r.ok, "errors": r.errors, "warnings": r.warnings}
            for r in reports
        ]
        print(json.dumps(payload, indent=2))
    else:
        for r in reports:
            _print_human(r, args.strict)

    failed = any(not r.ok or (args.strict and r.warnings) for r in reports)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
