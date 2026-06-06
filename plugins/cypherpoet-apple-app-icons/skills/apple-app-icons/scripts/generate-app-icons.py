#!/usr/bin/env python3
"""Generate Apple app icon assets from a single source image.

Cleans one source (trim a baked-in edge frame, recenter the dominant content,
flatten to RGB) and emits a Liquid Glass `.icon` bundle and/or a classic
`.appiconset`, so the `.icon` layer and every appiconset size stay identical.

Examples
--------
    # Both formats, cleaned and recentered:
    generate-app-icons.py source.png --clean --recenter \
        --icon AppIcon.icon --appiconset AppIcon.appiconset

    # Just the appiconset, trimming a known 5px frame:
    generate-app-icons.py source.png --trim 5 --appiconset AppIcon.appiconset

Requires Pillow (`pip install pillow`).
"""

import argparse
import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("This script needs Pillow:  pip install pillow")

# (size, name, [(scale, point_size), ...]) — iOS uses one universal 1024.
APPICONSET = [
    ("AppIcon-1024.png", 1024, [("universal-ios", 1024)]),
    ("AppIcon-mac-16.png", 16, [("mac-1x", 16)]),
    ("AppIcon-mac-32.png", 32, [("mac-2x", 16), ("mac-1x", 32)]),
    ("AppIcon-mac-64.png", 64, [("mac-2x", 32)]),
    ("AppIcon-mac-128.png", 128, [("mac-1x", 128)]),
    ("AppIcon-mac-256.png", 256, [("mac-2x", 128), ("mac-1x", 256)]),
    ("AppIcon-mac-512.png", 512, [("mac-2x", 256), ("mac-1x", 512)]),
    ("AppIcon-mac-1024.png", 1024, [("mac-2x", 512)]),
]


def luminance_grid(img, step):
    g = img.convert("L")
    return g.load(), g.size


def detect_frame(img, threshold=200, max_frac=0.06):
    """Count contiguous bright lines inward from each edge (a baked-in frame)."""
    px, (w, h) = luminance_grid(img, 1)
    limit = int(min(w, h) * max_frac)

    def bright_row(y):
        return sum(px[x, y] for x in range(0, w, 7)) / len(range(0, w, 7)) > threshold

    def bright_col(x):
        return sum(px[x, y] for y in range(0, h, 7)) / len(range(0, h, 7)) > threshold

    top = next((y for y in range(limit) if not bright_row(y)), limit)
    bottom = next((y for y in range(limit) if not bright_row(h - 1 - y)), limit)
    left = next((x for x in range(limit) if not bright_col(x)), limit)
    right = next((x for x in range(limit) if not bright_col(w - 1 - x)), limit)
    return max(top, bottom, left, right)


def content_center(img, bg, tol=24):
    """Geometric center of the non-background region (intensity-robust bbox)."""
    px = img.load()
    w, h = img.size

    def fg(x, y):
        p = px[x, y]
        return abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > tol

    cols = [x for x in range(0, w, 2) if any(fg(x, y) for y in range(0, h, 8))]
    rows = [y for y in range(0, h, 2) if any(fg(x, y) for x in range(0, w, 8))]
    if not cols or not rows:
        return w // 2, h // 2
    return (cols[0] + cols[-1]) // 2, (rows[0] + rows[-1]) // 2


def prepare(path, trim, clean, recenter):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    crop = trim if trim is not None else (detect_frame(img) if clean else 0)
    if crop:
        img = img.crop((crop, crop, w - crop, h - crop))
    if not recenter:
        return img.resize((w, h), Image.LANCZOS) if crop else img

    cw, ch = img.size
    bg = img.load()[2, 2]
    cx, cy = content_center(img, bg)
    canvas = Image.new("RGB", (w, h), bg)
    canvas.paste(img, (w // 2 - cx, h // 2 - cy))
    return canvas


def write_icon(canvas, icon_path, scale):
    name = "app-icon.png"
    assets = os.path.join(icon_path, "Assets")
    os.makedirs(assets, exist_ok=True)
    canvas.save(os.path.join(assets, name), "PNG")
    manifest = {
        "fill": {"automatic-gradient": "extended-srgb:0.0,0.53,1.0,1.0"},
        "groups": [{
            "name": "App Icon",
            "layers": [{
                "image-name": name,
                "name": "app-icon",
                "position": {"scale": scale, "translation-in-points": [0, 0]},
            }],
        }],
        "supported-platforms": {"circles": ["watchOS"], "squares": "shared"},
    }
    with open(os.path.join(icon_path, "icon.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"wrote {icon_path}")


def write_appiconset(canvas, set_path):
    os.makedirs(set_path, exist_ok=True)
    for filename, size, _ in APPICONSET:
        canvas.resize((size, size), Image.LANCZOS).save(
            os.path.join(set_path, filename), "PNG"
        )
    images = []
    for filename, _, entries in APPICONSET:
        for kind, pt in entries:
            if kind == "universal-ios":
                images.append({"filename": filename, "idiom": "universal",
                               "platform": "ios", "size": f"{pt}x{pt}"})
            else:
                images.append({"filename": filename, "idiom": "mac",
                               "scale": kind.split("-")[1], "size": f"{pt}x{pt}"})
    contents = {"images": images, "info": {"author": "xcode", "version": 1}}
    with open(os.path.join(set_path, "Contents.json"), "w") as f:
        json.dump(contents, f, indent=2)
    print(f"wrote {set_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="source image (ideally >= 2048x2048, square)")
    ap.add_argument("--icon", metavar="PATH.icon", help="write a single-layer .icon bundle")
    ap.add_argument("--appiconset", metavar="PATH.appiconset", help="write an .appiconset")
    ap.add_argument("--clean", action="store_true", help="auto-detect and trim a bright edge frame")
    ap.add_argument("--trim", type=int, metavar="N", help="trim exactly N px from each edge (overrides --clean)")
    ap.add_argument("--recenter", action="store_true", help="center the dominant content in the tile")
    ap.add_argument("--scale", type=float, default=0.52, help="icon.json layer scale (default: 0.52)")
    args = ap.parse_args()

    if not args.icon and not args.appiconset:
        ap.error("nothing to do: pass --icon and/or --appiconset")

    canvas = prepare(args.source, args.trim, args.clean, args.recenter)
    if args.icon:
        write_icon(canvas, args.icon, args.scale)
    if args.appiconset:
        write_appiconset(canvas, args.appiconset)


if __name__ == "__main__":
    main()
