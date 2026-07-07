#!/usr/bin/env python3
"""Split an Excalidraw library (`*.excalidrawlib`) into per-icon JSON files.

Downloaded icon sets (AWS, GCP, Azure, Kubernetes, ...) ship as one big
`.excalidrawlib`. Splitting it lets an agent read a lightweight `reference.md`
to find an icon, then load only the one icon file it needs — instead of pulling
the whole library into context.

Layout expected:
    <skill>/scripts/libraries/<icon-set>/
        <icon-set>.excalidrawlib     # place this first

Usage:
    python split_excalidraw_library.py <path-to-library-directory>

Pure standard library — no dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Turn an icon name into a filesystem-safe stem."""
    filename = name.replace(" ", "-")
    filename = re.sub(r"[^\w\-.]", "", filename)
    filename = re.sub(r"-+", "-", filename)
    return filename.strip("-")


def find_library_file(directory: Path) -> Path:
    library_files = list(directory.glob("*.excalidrawlib"))
    if not library_files:
        print(f"Error: no .excalidrawlib file found in {directory}", file=sys.stderr)
        print("Download one from https://libraries.excalidraw.com/ and place it here first.", file=sys.stderr)
        sys.exit(1)
    if len(library_files) > 1:
        print(f"Error: multiple .excalidrawlib files in {directory}; keep only one.", file=sys.stderr)
        sys.exit(1)
    return library_files[0]


def split_library(library_dir: Path) -> None:
    if not library_dir.is_dir():
        print(f"Error: not a directory: {library_dir}", file=sys.stderr)
        sys.exit(1)

    library_path = find_library_file(library_dir)
    print(f"Found library: {library_path.name}")

    library_data = json.loads(library_path.read_text(encoding="utf-8"))
    if "libraryItems" not in library_data:
        print("Error: invalid library file (missing 'libraryItems')", file=sys.stderr)
        sys.exit(1)

    icons_dir = library_dir / "icons"
    icons_dir.mkdir(exist_ok=True)

    icon_list: list[dict[str, str]] = []
    used: set[str] = set()
    for i, item in enumerate(library_data["libraryItems"]):
        icon_name = item.get("name", "Unnamed")
        # Disambiguate stems that collide (or sanitize to empty) so no icon is
        # silently overwritten by a later one with the same sanitized name.
        stem = sanitize_filename(icon_name) or f"icon-{i}"
        candidate, n = stem, 2
        while candidate in used:
            candidate, n = f"{stem}-{n}", n + 1
        if candidate != stem:
            print(f"  note  name collision for {icon_name!r}; writing as {candidate}.json")
        used.add(candidate)
        filename = candidate + ".json"
        (icons_dir / filename).write_text(
            json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        icon_list.append({"name": icon_name, "filename": filename})
        print(f"  ok  {icon_name} -> {filename}")

    icon_list.sort(key=lambda x: x["name"])
    reference_path = library_dir / "reference.md"
    with reference_path.open("w", encoding="utf-8") as fh:
        fh.write(f"# {library_path.stem} Reference\n\n")
        fh.write(f"{len(icon_list)} icons extracted from `{library_path.name}`.\n\n")
        fh.write("| Icon Name | Filename |\n|---|---|\n")
        for icon in icon_list:
            fh.write(f"| {icon['name']} | `icons/{icon['filename']}` |\n")

    print(f"\nSplit into {len(icon_list)} icons. Reference: {reference_path}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print("Usage: python split_excalidraw_library.py <path-to-library-directory>", file=sys.stderr)
        sys.exit(1)
    split_library(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
