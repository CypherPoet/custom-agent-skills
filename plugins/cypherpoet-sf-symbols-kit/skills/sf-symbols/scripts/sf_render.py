"""AppKit-backed SF Symbol rendering: system symbol name -> clean vector outline.

The macOS system resolves each symbol name (`NSImage(systemSymbolName:)`) and
`NSSymbolImageRep.outlinePath()` returns the true vector outline — the same one
the OS draws. This module translates that NSBezierPath into SVG path data.

Requires macOS + PyObjC (`pip install pyobjc-framework-cocoa`). `sf_symbols.py`
imports this module lazily so the metadata-only commands stay dependency-free;
keep that contract when editing.
"""
import objc
import AppKit

# NSBezierPathElement values
MOVETO, LINETO, CURVETO, CLOSE = 0, 1, 2, 3  # 4 = quadratic (rare)

# SF Symbols ships 9 weights; these map to the AppKit NSFontWeight constants.
WEIGHTS = {
    "ultralight": AppKit.NSFontWeightUltraLight,
    "thin": AppKit.NSFontWeightThin,
    "light": AppKit.NSFontWeightLight,
    "regular": AppKit.NSFontWeightRegular,
    "medium": AppKit.NSFontWeightMedium,
    "semibold": AppKit.NSFontWeightSemibold,
    "bold": AppKit.NSFontWeightBold,
    "heavy": AppKit.NSFontWeightHeavy,
    "black": AppKit.NSFontWeightBlack,
}

# NSImageSymbolScale: 1=small 2=medium 3=large
SCALES = {"small": 1, "medium": 2, "large": 3}

autorelease_pool = objc.autorelease_pool


def _fmt(value):
    return f"{value:.3f}".rstrip("0").rstrip(".")


def symbol_outline(name, point_size, weight_name, scale_name):
    """Return (commands, bounds) for `name`, or None if the OS can't resolve it.

    `commands` is a list of (op, points) tuples with op in "MLCQZ" and points a
    flat [x0, y0, x1, y1, ...] list in outlinePath's top-left-oriented image
    coordinates. `bounds` is (min_x, min_y, width, height).
    """
    image = AppKit.NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
    if image is None:
        return None
    config = AppKit.NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(
        point_size, WEIGHTS[weight_name], SCALES[scale_name]
    )
    configured = image.imageWithSymbolConfiguration_(config)
    if configured is not None:
        image = configured

    rep = None
    for candidate in image.representations():
        if candidate.className() == "NSSymbolImageRep":
            rep = candidate
            break
    if rep is None:
        return None

    path = rep.outlinePath()
    if path is None or path.elementCount() == 0:
        return None

    bounds = path.bounds()
    if bounds.size.width <= 0 or bounds.size.height <= 0:
        return None

    commands = []
    for index in range(path.elementCount()):
        element_type, points = path.elementAtIndex_associatedPoints_(index)
        if element_type == MOVETO:
            commands.append(("M", [points[0].x, points[0].y]))
        elif element_type == LINETO:
            commands.append(("L", [points[0].x, points[0].y]))
        elif element_type == CURVETO:
            commands.append(("C", [points[0].x, points[0].y,
                                   points[1].x, points[1].y,
                                   points[2].x, points[2].y]))
        elif element_type == CLOSE:
            commands.append(("Z", []))
        else:  # quadratic fallback (2 control points)
            commands.append(("Q", [points[0].x, points[0].y,
                                   points[1].x, points[1].y]))
    return commands, (bounds.origin.x, bounds.origin.y, bounds.size.width, bounds.size.height)


def path_data(commands, transform=None):
    """Serialize `commands` to an SVG `d` string, mapping each point through
    `transform(x, y) -> (x, y)` when given."""
    parts = []
    for op, points in commands:
        if op == "Z":
            parts.append("Z")
            continue
        coords = []
        for i in range(0, len(points), 2):
            x, y = points[i], points[i + 1]
            if transform is not None:
                x, y = transform(x, y)
            coords.append(f"{_fmt(x)} {_fmt(y)}")
        parts.append(op + " ".join(coords))
    return "".join(parts)


def symbol_to_svg(name, point_size, weight_name, scale_name):
    """Return a standalone recolorable SVG string for `name`, or None."""
    outline = symbol_outline(name, point_size, weight_name, scale_name)
    if outline is None:
        return None
    commands, (min_x, min_y, width, height) = outline

    data = path_data(commands, lambda x, y: (x - min_x, y - min_y))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_fmt(width)} {_fmt(height)}">'
        f'<path fill="currentColor" fill-rule="nonzero" d="{data}"/></svg>\n'
    )
