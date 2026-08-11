#!/usr/bin/env python3
"""SF Symbols toolkit: search, inspect, render, and author Apple SF Symbols.

Metadata commands (stdlib only, run with any python3):
    search             find symbols by natural-language keywords
    list               enumerate symbols with filters
    info               everything known about one symbol
    categories         list category keys and display names
    custom             wrap arbitrary SVG art into a custom-symbol template
    validate-template  structural lint for custom-symbol template SVGs
    import             validate + import a template into the SF Symbols app (macOS)

Rendering commands (macOS + PyObjC, lazily imported):
    svg                emit one symbol as a clean single-path SVG
    build-all          batch-export symbols to a directory tree
    gallery            generate a filterable HTML gallery
    template           export an editable custom-symbol template of a system symbol

Metadata is read live from the installed SF Symbols app
(/Applications/SF Symbols.app). Override with --metadata-dir or
SF_SYMBOLS_METADATA_DIR for non-default install locations.
"""
import argparse
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

DEFAULT_METADATA_DIR = "/Applications/SF Symbols.app/Contents/Resources/Metadata"

WEIGHT_NAMES = ["ultralight", "thin", "light", "regular", "medium",
                "semibold", "bold", "heavy", "black"]
SCALE_NAMES = ["small", "medium", "large"]


# --------------------------------------------------------------------------
# Variant classification (localized-script / right-to-left mirror names)
# --------------------------------------------------------------------------

# SF Symbols localization uses ISO script/language codes as the trailing segment.
# These are scripts, never directional words — kept explicit to avoid false matches.
LANGS = {
    "ar": "Arabic", "he": "Hebrew", "hi": "Devanagari/Hindi", "th": "Thai",
    "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "my": "Burmese",
    "km": "Khmer", "lo": "Lao", "si": "Sinhala", "ne": "Nepali", "bn": "Bengali",
    "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi",
    "or": "Odia", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "sa": "Sanskrit",
}


def classify(name, names):
    """Return (category, base) where category is 'base', 'rtl', or 'loc:<code>'.

    A name counts as a variant only when stripping its trailing suffix yields a
    base symbol that ALSO exists in the catalog — so directional suffixes like
    `.up` (arrow.up -> arrow) are never mistaken for the Punjabi code `.pa`.
    """
    head, _, last = name.rpartition(".")
    if last == "rtl" and head in names:
        return "rtl", head
    if last in LANGS and head in names:
        return "loc:" + last, head
    return "base", name


# --------------------------------------------------------------------------
# Metadata loading
# --------------------------------------------------------------------------

def _parse_strings_file(path):
    """Parse a NeXTSTEP-format .strings file ("key" = "value"; lines)."""
    pairs = {}
    if not os.path.exists(path):
        return pairs
    with open(path, encoding="utf-8") as fh:
        for match in re.finditer(r'"([^"]+)"\s*=\s*"([^"]+)"\s*;', fh.read()):
            pairs[match.group(1)] = match.group(2)
    return pairs


class Metadata:
    """Lazy loader over the SF Symbols app's metadata plists."""

    def __init__(self, directory):
        self.directory = directory
        self._cache = {}
        if not os.path.isdir(directory):
            sys.exit(
                f"error: SF Symbols metadata not found at {directory}\n"
                "Install the SF Symbols app (https://developer.apple.com/sf-symbols/)\n"
                "or point at it with --metadata-dir / SF_SYMBOLS_METADATA_DIR."
            )

    def _plist(self, fname):
        if fname not in self._cache:
            import plistlib
            with open(os.path.join(self.directory, fname), "rb") as fh:
                self._cache[fname] = plistlib.load(fh)
        return self._cache[fname]

    @property
    def years(self):
        """{symbol name: release year string}"""
        return self._plist("name_availability.plist")["symbols"]

    @property
    def year_to_release(self):
        """{year string: {platform: minimum OS version}}"""
        return self._plist("name_availability.plist")["year_to_release"]

    @property
    def names(self):
        if "names" not in self._cache:
            self._cache["names"] = set(self.years)
        return self._cache["names"]

    @property
    def keywords(self):
        """{symbol name: [search keywords]} (Apple curates ~3,200 of these)"""
        return self._plist("symbol_search.plist")

    @property
    def symbol_categories(self):
        """{symbol name: [category keys]}"""
        return self._plist("symbol_categories.plist")

    @property
    def categories(self):
        """[{key, label, icon}] in the app's sidebar order"""
        return self._plist("categories.plist")

    @property
    def layersets(self):
        """{symbol name: {layerset: year}} — extra rendering modes"""
        return self._plist("layerset_availability.plist")["symbols"]

    @property
    def aliases(self):
        """{alias: canonical} merged from current + legacy alias tables"""
        if "aliases" not in self._cache:
            merged = _parse_strings_file(os.path.join(self.directory, "name_aliases.strings"))
            merged.update(_parse_strings_file(os.path.join(self.directory, "legacy_aliases.strings")))
            self._cache["aliases"] = merged
        return self._cache["aliases"]

    def base_names(self):
        """Catalog names minus localized-script and .rtl mirror variants."""
        if "base_names" not in self._cache:
            names = self.names
            self._cache["base_names"] = sorted(
                n for n in names if classify(n, names)[0] == "base"
            )
        return self._cache["base_names"]


def metadata_from(args):
    directory = (getattr(args, "metadata_dir", None)
                 or os.environ.get("SF_SYMBOLS_METADATA_DIR")
                 or DEFAULT_METADATA_DIR)
    return Metadata(directory)


# --------------------------------------------------------------------------
# Renderer (lazy PyObjC import)
# --------------------------------------------------------------------------

def load_renderer():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import sf_render
        return sf_render
    except ImportError:
        sys.exit(
            "error: this command renders symbols via macOS AppKit and needs PyObjC.\n"
            "Install it with:    python3 -m pip install pyobjc-framework-cocoa\n"
            "          (or):    uv pip install pyobjc-framework-cocoa\n"
            "Rendering requires macOS. The metadata commands (search/list/info/\n"
            "categories/custom/validate-template) run anywhere with no dependencies."
        )


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

def tokenize(text):
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def search_symbols(meta, query, limit):
    """Rank base symbols by name-token + Apple-keyword + category overlap.

    Returns [(name, score, [reasons])] sorted best-first.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    keywords = meta.keywords
    symbol_categories = meta.symbol_categories
    category_labels = {c["key"]: c["label"].lower() for c in meta.categories}
    alias_of = {}  # canonical -> [aliases], to match old names too
    for alias, canonical in meta.aliases.items():
        alias_of.setdefault(canonical, []).append(alias)

    results = []
    for name in meta.base_names():
        name_tokens = set(tokenize(name))
        kw_tokens = set()
        for kw in keywords.get(name, []):
            kw_tokens.update(tokenize(kw))
        alias_tokens = set()
        for alias in alias_of.get(name, []):
            alias_tokens.update(tokenize(alias))
        cat_tokens = set()
        for key in symbol_categories.get(name, []):
            cat_tokens.update(tokenize(category_labels.get(key, key)))

        score = 0
        reasons = []
        for token in query_tokens:
            if token in name_tokens:
                score += 3
                reasons.append(f"name:{token}")
            elif any(token in nt for nt in name_tokens):
                score += 1
                reasons.append(f"name~{token}")
            if token in kw_tokens:
                score += 2
                reasons.append(f"keyword:{token}")
            if token in alias_tokens:
                score += 2
                reasons.append(f"alias:{token}")
            if token in cat_tokens:
                score += 1
                reasons.append(f"category:{token}")
        if score > 0:
            results.append((name, score, reasons))

    # Prefer higher scores, then shorter (more canonical) names.
    results.sort(key=lambda r: (-r[1], len(r[0]), r[0]))
    return results[:limit]


def cmd_search(args):
    meta = metadata_from(args)
    results = search_symbols(meta, args.query, args.limit)
    if args.json:
        print(json.dumps(
            [{"name": n, "score": s, "matched": r} for n, s, r in results], indent=2))
        return
    if not results:
        print("no matches — try different keywords (Claude: expand synonyms and retry)")
        return
    width = max(len(n) for n, _, _ in results)
    for name, score, reasons in results:
        print(f"{name:<{width}}  score={score:<3} {', '.join(sorted(set(reasons)))}")


# --------------------------------------------------------------------------
# List / info / categories
# --------------------------------------------------------------------------

def select_names(meta, args):
    """Shared filtering for `list` and `gallery`."""
    names = meta.base_names() if getattr(args, "base_only", True) else sorted(meta.names)
    if getattr(args, "category", None):
        cats = meta.symbol_categories
        names = [n for n in names if args.category in cats.get(n, [])]
    if getattr(args, "contains", None):
        names = [n for n in names if args.contains in n]
    if getattr(args, "starts_with", None):
        names = [n for n in names if n.startswith(args.starts_with)]
    if getattr(args, "search", None):
        ranked = search_symbols(meta, args.search, limit=len(names))
        selected = set(names)
        names = [n for n, _, _ in ranked if n in selected]
    return names


def cmd_list(args):
    meta = metadata_from(args)
    names = select_names(meta, args)
    total = len(names)
    if args.limit:
        names = names[: args.limit]
    if args.json:
        years = meta.years
        print(json.dumps([{"name": n, "year": years.get(n)} for n in names], indent=2))
        return
    for name in names:
        print(name)
    if args.limit and total > args.limit:
        print(f"... {total - args.limit} more (raise --limit or add filters)", file=sys.stderr)


def cmd_info(args):
    meta = metadata_from(args)
    name = args.name
    canonical = meta.aliases.get(name)
    if name not in meta.names and canonical:
        print(f"note: '{name}' is an alias of '{canonical}'\n")
        name = canonical
    if name not in meta.names:
        sys.exit(f"error: unknown symbol '{name}' — try: sf_symbols.py search \"{args.name}\"")

    kind, base = classify(name, meta.names)
    year = meta.years.get(name)
    releases = meta.year_to_release.get(year, {})
    category_labels = {c["key"]: c["label"] for c in meta.categories}
    cats = [category_labels.get(k, k) for k in meta.symbol_categories.get(name, [])]
    also_known = sorted(a for a, c in meta.aliases.items() if c == name)
    layersets = meta.layersets.get(name, {})

    payload = {
        "name": name,
        "kind": kind if kind == "base" else f"variant ({kind}) of {base}",
        "introduced": year,
        "minimum_os": releases,
        "categories": cats,
        "apple_keywords": meta.keywords.get(name, []),
        "aliases": also_known,
        "extra_rendering_modes": layersets,
        "weights": WEIGHT_NAMES,
        "scales": SCALE_NAMES,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    for key, value in payload.items():
        if isinstance(value, dict):
            value = ", ".join(f"{k} {v}" for k, v in value.items()) or "—"
        elif isinstance(value, list):
            value = ", ".join(value) or "—"
        print(f"{key:>22}: {value}")


def cmd_categories(args):
    meta = metadata_from(args)
    counts = {}
    for keys in meta.symbol_categories.values():
        for key in keys:
            counts[key] = counts.get(key, 0) + 1
    if args.json:
        print(json.dumps(
            [{"key": c["key"], "label": c["label"], "symbols": counts.get(c["key"], 0)}
             for c in meta.categories], indent=2))
        return
    for c in meta.categories:
        print(f"{c['key']:<18} {c['label']:<22} {counts.get(c['key'], 0):>5}")


# --------------------------------------------------------------------------
# Custom-symbol template format (geometry verified against the Apple-authored
# variable template at /Applications/SF Symbols.app/Contents/Resources/badge.svg)
# --------------------------------------------------------------------------

TEMPLATE_CANVAS = (3300, 2200)
TEMPLATE_POINT_SIZE = 100.0          # all coordinates assume a 100 pt design size
GUIDE_X = (263, 3036)                # horizontal span of baseline/capline guides
BASELINE_Y = {"S": 696.0, "M": 1126.0, "L": 1556.0}
CAP_HEIGHT = 70.459                  # SF cap height at 100 pt
MARGIN_PAD = (95.215, 24.121)        # margin guide extent above/below the baseline
WEIGHT_CENTER_X = {
    "Ultralight": 559.711, "Thin": 856.422, "Light": 1153.13,
    "Regular": 1449.84, "Medium": 1746.56, "Semibold": 2043.27,
    "Bold": 2339.98, "Heavy": 2636.69, "Black": 2933.4,
}
INTERPOLATION_MASTERS = ["Ultralight-S", "Regular-S", "Black-S"]
TEMPLATE_VERSION = "3.0"             # monochrome + explicit margins (iOS 15+)


def _fmt(value):
    return f"{value:.3f}".rstrip("0").rstrip(".")


def emit_template(variants):
    """Build a custom-symbol template SVG.

    `variants` is a list of (variant_id, [path d strings], width) where path
    coordinates are group-local: origin at (left margin, baseline), y up = negative.
    """
    notes = [
        '  <rect height="2200" id="artboard" style="fill:white;opacity:1" width="3300" x="0" y="0"/>',
        '  <text id="template-version" style="stroke:none;fill:black;font-family:sans-serif;'
        f'font-size:13;" transform="matrix(1 0 0 1 263 292)">Template v.{TEMPLATE_VERSION}</text>',
    ]
    guides = []
    for scale, baseline in BASELINE_Y.items():
        for label, y in (("Baseline", baseline), ("Capline", baseline - CAP_HEIGHT)):
            guides.append(
                f'  <line id="{label}-{scale}" style="fill:none;stroke:#27AAE1;opacity:1;'
                f'stroke-width:0.5;" x1="{GUIDE_X[0]}" x2="{GUIDE_X[1]}" '
                f'y1="{_fmt(y)}" y2="{_fmt(y)}"/>'
            )
    symbols = []
    for variant_id, paths, width in variants:
        weight, scale = variant_id.rsplit("-", 1)
        center_x = WEIGHT_CENTER_X[weight]
        baseline = BASELINE_Y[scale]
        left = center_x - width / 2.0
        right = center_x + width / 2.0
        y1, y2 = baseline - MARGIN_PAD[0], baseline + MARGIN_PAD[1]
        notes.append(
            '  <text style="stroke:none;fill:black;font-family:sans-serif;font-size:13;'
            f'text-anchor:middle;" transform="matrix(1 0 0 1 {_fmt(center_x)} '
            f'{_fmt(y1 - 12)})">{variant_id}</text>'
        )
        for side, x in (("left", left), ("right", right)):
            guides.append(
                f'  <line id="{side}-margin-{variant_id}" style="fill:none;stroke:#00AEEF;'
                f'stroke-width:0.5;opacity:1.0;" x1="{_fmt(x)}" x2="{_fmt(x)}" '
                f'y1="{_fmt(y1)}" y2="{_fmt(y2)}"/>'
            )
        path_elements = "\n".join(f'   <path d="{d}"/>' for d in paths)
        symbols.append(
            f'  <g id="{variant_id}" transform="matrix(1 0 0 1 {_fmt(left)} {_fmt(baseline)})">\n'
            f"{path_elements}\n  </g>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE svg\n"
        'PUBLIC "-//W3C//DTD SVG 1.1//EN"\n'
        '       "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" width="3300" height="2200">\n'
        " <!--Generated by sf_symbols.py (sf-symbols-kit); "
        f"point size: {TEMPLATE_POINT_SIZE}-->\n"
        ' <g id="Notes">\n' + "\n".join(notes) + "\n </g>\n"
        ' <g id="Guides">\n' + "\n".join(guides) + "\n </g>\n"
        ' <g id="Symbols">\n' + "\n".join(symbols) + "\n </g>\n"
        "</svg>\n"
    )


# --------------------------------------------------------------------------
# SVG input parsing (for `custom`)
# --------------------------------------------------------------------------

class CustomSymbolError(Exception):
    pass


_NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _style_dict(element):
    style = {}
    for part in element.get("style", "").split(";"):
        if ":" in part:
            key, _, value = part.partition(":")
            style[key.strip()] = value.strip()
    for attr in ("fill", "stroke", "stroke-width", "clip-path", "mask", "filter",
                 "fill-rule", "display", "visibility", "opacity"):
        if element.get(attr) is not None and attr not in style:
            style[attr] = element.get(attr)
    return style


def _quad_to_cubic(p0, q, p2):
    c1 = (p0[0] + 2.0 / 3.0 * (q[0] - p0[0]), p0[1] + 2.0 / 3.0 * (q[1] - p0[1]))
    c2 = (p2[0] + 2.0 / 3.0 * (q[0] - p2[0]), p2[1] + 2.0 / 3.0 * (q[1] - p2[1]))
    return c1, c2


def _arc_to_cubics(p0, rx, ry, rotation_deg, large_arc, sweep, p1):
    """SVG elliptical arc -> cubic Béziers (spec appendix F.6 conversion)."""
    if rx == 0 or ry == 0 or p0 == p1:
        return [("L", [p1[0], p1[1]])]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(rotation_deg % 360)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    dx2, dy2 = (p0[0] - p1[0]) / 2.0, (p0[1] - p1[1]) / 2.0
    x1p = cos_phi * dx2 + sin_phi * dy2
    y1p = -sin_phi * dx2 + cos_phi * dy2
    # Scale radii up if the endpoints can't be reached.
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:
        scale = math.sqrt(lam)
        rx, ry = rx * scale, ry * scale
    num = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    coef = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large_arc == sweep:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (p0[0] + p1[0]) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (p0[1] + p1[1]) / 2.0

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        norm = math.sqrt((ux**2 + uy**2) * (vx**2 + vy**2))
        ang = math.acos(max(-1.0, min(1.0, dot / norm)))
        return -ang if ux * vy - uy * vx < 0 else ang

    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    delta = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                  (-x1p - cxp) / rx, (-y1p - cyp) / ry) % (2 * math.pi)
    if not sweep and delta > 0:
        delta -= 2 * math.pi
    if sweep and delta < 0:
        delta += 2 * math.pi

    segments = max(1, int(math.ceil(abs(delta) / (math.pi / 2))))
    step = delta / segments
    commands = []
    t = theta1
    for _ in range(segments):
        t2 = t + step
        k = 4.0 / 3.0 * math.tan(step / 4.0)

        def point(theta):
            x = rx * math.cos(theta)
            y = ry * math.sin(theta)
            return (cos_phi * x - sin_phi * y + cx, sin_phi * x + cos_phi * y + cy)

        def derivative(theta):
            x = -rx * math.sin(theta)
            y = ry * math.cos(theta)
            return (cos_phi * x - sin_phi * y, sin_phi * x + cos_phi * y)

        start, end = point(t), point(t2)
        d1, d2 = derivative(t), derivative(t2)
        commands.append(("C", [start[0] + k * d1[0], start[1] + k * d1[1],
                               end[0] - k * d2[0], end[1] - k * d2[1],
                               end[0], end[1]]))
        t = t2
    return commands


def parse_path_d(d):
    """Parse an SVG path `d` into absolute (op, points) tuples with op in M/L/C/Z.

    Shorthands (H/V/S/T/Q), relative commands, and arcs are all normalized away
    so downstream code only handles moves, lines, cubics, and closes.
    """
    tokens = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|" + _NUMBER.pattern, d)
    commands = []
    pos = (0.0, 0.0)
    start = (0.0, 0.0)
    last_cubic_control = None
    last_quad_control = None
    i = 0
    op = None
    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            op = token
            i += 1
            if op in "Zz":
                commands.append(("Z", []))
                pos = start
                last_cubic_control = last_quad_control = None
                continue
        if op is None:
            raise CustomSymbolError("path data does not start with a command")

        def take(count):
            nonlocal i
            values = [float(v) for v in tokens[i:i + count]]
            if len(values) < count:
                raise CustomSymbolError(f"path data ends mid-{op} command")
            i += count
            return values

        relative = op.islower()
        upper = op.upper()
        if upper == "M":
            x, y = take(2)
            if relative:
                x, y = pos[0] + x, pos[1] + y
            commands.append(("M", [x, y]))
            pos = start = (x, y)
            op = "l" if relative else "L"  # subsequent pairs are implicit lineto
            last_cubic_control = last_quad_control = None
        elif upper == "L":
            x, y = take(2)
            if relative:
                x, y = pos[0] + x, pos[1] + y
            commands.append(("L", [x, y]))
            pos = (x, y)
            last_cubic_control = last_quad_control = None
        elif upper == "H":
            (x,) = take(1)
            if relative:
                x = pos[0] + x
            commands.append(("L", [x, pos[1]]))
            pos = (x, pos[1])
            last_cubic_control = last_quad_control = None
        elif upper == "V":
            (y,) = take(1)
            if relative:
                y = pos[1] + y
            commands.append(("L", [pos[0], y]))
            pos = (pos[0], y)
            last_cubic_control = last_quad_control = None
        elif upper in ("C", "S"):
            if upper == "C":
                x1, y1, x2, y2, x, y = take(6)
                if relative:
                    x1, y1 = pos[0] + x1, pos[1] + y1
                    x2, y2 = pos[0] + x2, pos[1] + y2
                    x, y = pos[0] + x, pos[1] + y
            else:
                x2, y2, x, y = take(4)
                if relative:
                    x2, y2 = pos[0] + x2, pos[1] + y2
                    x, y = pos[0] + x, pos[1] + y
                if last_cubic_control is not None:
                    x1 = 2 * pos[0] - last_cubic_control[0]
                    y1 = 2 * pos[1] - last_cubic_control[1]
                else:
                    x1, y1 = pos
            commands.append(("C", [x1, y1, x2, y2, x, y]))
            pos = (x, y)
            last_cubic_control = (x2, y2)
            last_quad_control = None
        elif upper in ("Q", "T"):
            if upper == "Q":
                qx, qy, x, y = take(4)
                if relative:
                    qx, qy = pos[0] + qx, pos[1] + qy
                    x, y = pos[0] + x, pos[1] + y
            else:
                x, y = take(2)
                if relative:
                    x, y = pos[0] + x, pos[1] + y
                if last_quad_control is not None:
                    qx = 2 * pos[0] - last_quad_control[0]
                    qy = 2 * pos[1] - last_quad_control[1]
                else:
                    qx, qy = pos
            c1, c2 = _quad_to_cubic(pos, (qx, qy), (x, y))
            commands.append(("C", [c1[0], c1[1], c2[0], c2[1], x, y]))
            pos = (x, y)
            last_quad_control = (qx, qy)
            last_cubic_control = None
        elif upper == "A":
            rx, ry, rotation, large_arc, sweep, x, y = take(7)
            if relative:
                x, y = pos[0] + x, pos[1] + y
            commands.extend(_arc_to_cubics(pos, rx, ry, rotation,
                                           bool(large_arc), bool(sweep), (x, y)))
            pos = (x, y)
            last_cubic_control = last_quad_control = None
        else:
            raise CustomSymbolError(f"unsupported path command '{op}'")
    return commands


def _parse_transform(text):
    """Parse an SVG transform attribute into a 2x3 affine matrix."""
    matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    def multiply(m, n):
        a1, b1, c1, d1, e1, f1 = m
        a2, b2, c2, d2, e2, f2 = n
        return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
                a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
                a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)

    for name, raw_args in re.findall(r"(\w+)\s*\(([^)]*)\)", text or ""):
        values = [float(v) for v in _NUMBER.findall(raw_args)]
        if name == "matrix" and len(values) == 6:
            other = tuple(values)
        elif name == "translate":
            tx = values[0]
            ty = values[1] if len(values) > 1 else 0.0
            other = (1, 0, 0, 1, tx, ty)
        elif name == "scale":
            sx = values[0]
            sy = values[1] if len(values) > 1 else sx
            other = (sx, 0, 0, sy, 0, 0)
        elif name == "rotate":
            angle = math.radians(values[0])
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            other = (cos_a, sin_a, -sin_a, cos_a, 0, 0)
            if len(values) == 3:
                cx, cy = values[1], values[2]
                other = multiply(multiply((1, 0, 0, 1, cx, cy), other),
                                 (1, 0, 0, 1, -cx, -cy))
        else:
            raise CustomSymbolError(f"unsupported transform '{name}({raw_args})'")
        matrix = multiply(matrix, other)
    return matrix


def _apply_matrix(matrix, commands):
    a, b, c, d, e, f = matrix
    transformed = []
    for op, points in commands:
        new_points = []
        for i in range(0, len(points), 2):
            x, y = points[i], points[i + 1]
            new_points.extend([a * x + c * y + e, b * x + d * y + f])
        transformed.append((op, new_points))
    return transformed


def _shape_to_commands(element):
    """Convert basic SVG shapes to path commands; None if not a drawable shape."""
    tag = _local(element.tag)
    get = lambda attr, default="0": float(element.get(attr, default))
    if tag == "path":
        return parse_path_d(element.get("d", ""))
    if tag == "rect":
        x, y, w, h = get("x"), get("y"), get("width"), get("height")
        rx, ry = element.get("rx"), element.get("ry")
        rx = float(rx) if rx is not None else (float(ry) if ry is not None else 0.0)
        ry = float(ry) if ry is not None else rx
        rx, ry = min(rx, w / 2), min(ry, h / 2)
        if rx <= 0 or ry <= 0:
            return [("M", [x, y]), ("L", [x + w, y]), ("L", [x + w, y + h]),
                    ("L", [x, y + h]), ("Z", [])]
        commands = [("M", [x + rx, y]), ("L", [x + w - rx, y])]
        commands += _arc_to_cubics((x + w - rx, y), rx, ry, 0, False, True, (x + w, y + ry))
        commands += [("L", [x + w, y + h - ry])]
        commands += _arc_to_cubics((x + w, y + h - ry), rx, ry, 0, False, True, (x + w - rx, y + h))
        commands += [("L", [x + rx, y + h])]
        commands += _arc_to_cubics((x + rx, y + h), rx, ry, 0, False, True, (x, y + h - ry))
        commands += [("L", [x, y + ry])]
        commands += _arc_to_cubics((x, y + ry), rx, ry, 0, False, True, (x + rx, y))
        commands += [("Z", [])]
        return commands
    if tag in ("circle", "ellipse"):
        cx, cy = get("cx"), get("cy")
        rx = get("r") if tag == "circle" else get("rx")
        ry = rx if tag == "circle" else get("ry")
        commands = [("M", [cx + rx, cy])]
        commands += _arc_to_cubics((cx + rx, cy), rx, ry, 0, False, True, (cx - rx, cy))
        commands += _arc_to_cubics((cx - rx, cy), rx, ry, 0, False, True, (cx + rx, cy))
        commands += [("Z", [])]
        return commands
    if tag in ("polygon", "polyline"):
        values = [float(v) for v in _NUMBER.findall(element.get("points", ""))]
        if len(values) < 4:
            return None
        commands = [("M", values[0:2])]
        for i in range(2, len(values) - 1, 2):
            commands.append(("L", values[i:i + 2]))
        if tag == "polygon":
            commands.append(("Z", []))
        return commands
    return None


def load_svg_paths(svg_path, ignore_strokes=False):
    """Extract filled path geometry from an SVG file.

    Returns (paths, warnings) where paths is a list of absolute command lists.
    Raises CustomSymbolError for art the template format can't express.
    """
    try:
        tree = ET.parse(svg_path)
    except ET.ParseError as err:
        raise CustomSymbolError(f"not well-formed XML: {err}")

    paths = []
    warnings = []

    def walk(element, matrix, inherited_style):
        tag = _local(element.tag)
        if tag in ("defs", "symbol", "clipPath", "mask", "filter", "marker",
                   "metadata", "title", "desc", "style"):
            return
        style = dict(inherited_style)
        style.update(_style_dict(element))
        if style.get("display") == "none" or style.get("visibility") == "hidden":
            return
        matrix = _apply_transform_attr(matrix, element)
        if tag in ("text", "tspan"):
            raise CustomSymbolError(
                "the SVG contains <text> — convert text to outlines in your "
                "vector editor first (e.g. Object > Expand / Create Outlines)")
        if tag in ("image", "use"):
            raise CustomSymbolError(
                f"the SVG contains <{tag}> — flatten it to plain paths in your "
                "vector editor first")
        for attr in ("clip-path", "mask", "filter"):
            if style.get(attr) and style[attr] != "none":
                raise CustomSymbolError(
                    f"the SVG uses {attr} — flatten/expand it to plain paths first "
                    "(symbol templates allow only solid filled shapes)")

        commands = _shape_to_commands(element)
        if commands is not None:
            fill = style.get("fill", "black")
            stroke = style.get("stroke", "none")
            stroke_width = style.get("stroke-width", "1")
            has_stroke = stroke not in ("none", "", "transparent") and \
                _NUMBER.match(stroke_width) and float(_NUMBER.match(stroke_width).group(0)) > 0
            if "url(" in fill or "url(" in stroke:
                raise CustomSymbolError(
                    "the SVG uses gradients/patterns — symbol templates need solid "
                    "flat fills (annotate colors later in the SF Symbols app)")
            if has_stroke and not ignore_strokes:
                raise CustomSymbolError(
                    "the SVG contains stroked shapes. Symbol templates are path-based: "
                    "convert strokes to outlines in your vector editor first\n"
                    "(Illustrator: Object > Path > Outline Stroke; Sketch: Layer > "
                    "Convert to Outlines; Figma: Object > Outline Stroke),\n"
                    "or re-run with --ignore-strokes to keep only the filled geometry.")
            if fill in ("none", "transparent"):
                if not has_stroke:
                    warnings.append(f"skipped invisible <{tag}> (fill=none, no stroke)")
                return
            if style.get("fill-rule") == "evenodd":
                warnings.append(
                    "fill-rule=evenodd detected — symbol rendering assumes nonzero "
                    "winding; holes may fill differently. Verify in the SF Symbols app.")
            if commands:
                paths.append(_apply_matrix(matrix, commands))
            return
        for child in element:
            walk(child, matrix, style)

    def _apply_transform_attr(matrix, element):
        transform = element.get("transform")
        if not transform:
            return matrix
        a, b, c, d, e, f = matrix
        a2, b2, c2, d2, e2, f2 = _parse_transform(transform)
        return (a * a2 + c * b2, b * a2 + d * b2,
                a * c2 + c * d2, b * c2 + d * d2,
                a * e2 + c * f2 + e, b * e2 + d * f2 + f)

    root = tree.getroot()
    for child in root:
        walk(child, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0), {})
    if not paths:
        raise CustomSymbolError("no filled shapes found in the SVG")
    return paths, warnings


def _cubic_axis_extrema(p0, c1, c2, p3):
    """Parameter values in (0,1) where a cubic Bézier axis component peaks."""
    a = -p0 + 3 * c1 - 3 * c2 + p3
    b = 2 * (p0 - 2 * c1 + c2)
    c = c1 - p0
    roots = []
    if abs(a) < 1e-12:
        if abs(b) > 1e-12:
            roots.append(-c / b)
    else:
        disc = b * b - 4 * a * c
        if disc >= 0:
            sqrt_disc = math.sqrt(disc)
            roots.extend([(-b + sqrt_disc) / (2 * a), (-b - sqrt_disc) / (2 * a)])
    return [t for t in roots if 0 < t < 1]


def paths_bbox(paths):
    """Exact bounding box over command lists (solves cubic extrema)."""
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    def include(x, y):
        nonlocal min_x, min_y, max_x, max_y
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)

    for commands in paths:
        pos = (0.0, 0.0)
        for op, points in commands:
            if op in ("M", "L"):
                pos = (points[0], points[1])
                include(*pos)
            elif op == "C":
                x0, y0 = pos
                x1, y1, x2, y2, x3, y3 = points
                include(x3, y3)
                for axis, (a0, a1, a2, a3) in (("x", (x0, x1, x2, x3)),
                                               ("y", (y0, y1, y2, y3))):
                    for t in _cubic_axis_extrema(a0, a1, a2, a3):
                        mt = 1 - t
                        value = (mt**3 * a0 + 3 * mt**2 * t * a1 +
                                 3 * mt * t**2 * a2 + t**3 * a3)
                        if axis == "x":
                            include(value, pos[1])
                        else:
                            include(pos[0], value)
                pos = (x3, y3)
    if min_x > max_x:
        raise CustomSymbolError("could not compute the artwork's bounding box")
    return min_x, min_y, max_x - min_x, max_y - min_y


def commands_to_d(commands, transform=None):
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


def cmd_custom(args):
    try:
        paths, warnings = load_svg_paths(args.input, ignore_strokes=args.ignore_strokes)
    except CustomSymbolError as err:
        sys.exit(f"error: {err}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    min_x, min_y, width, height = paths_bbox(paths)
    if width <= 0 or height <= 0:
        sys.exit("error: the artwork has zero width or height")

    # Fit the art into the cap-height box (symbols are designed vertically
    # centered on the cap-height midpoint), preserving aspect ratio.
    target_height = CAP_HEIGHT * args.scale
    factor = target_height / height
    scaled_width = width * factor

    def to_local(x, y):
        # group-local coordinates: x from the left margin, y up = negative,
        # art bbox centered on the cap-height midpoint.
        local_x = (x - min_x) * factor
        local_y = (y - (min_y + height / 2.0)) * factor - CAP_HEIGHT / 2.0
        return local_x, local_y

    d_strings = [commands_to_d(commands, to_local) for commands in paths]
    if args.static:
        variants = [("Regular-M", d_strings, scaled_width)]
    else:
        variants = [(vid, d_strings, scaled_width) for vid in INTERPOLATION_MASTERS]
    document = emit_template(variants)

    if args.do_import and not args.out:
        sys.exit("error: --import needs --out — the output filename becomes the "
                 "symbol's display name in the app (e.g. --out my.bolt.svg)")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(document)
        kind = "static (Regular-M)" if args.static else "variable (3 interpolation masters)"
        print(f"wrote {kind} template: {args.out}")
        if args.do_import:
            open_in_sf_symbols(args.out)
        else:
            print("next: validate it (validate-template), then import it — re-run "
                  "with --import, or drop the file into the SF Symbols app or an "
                  "Xcode Symbol Image Set.")
    else:
        sys.stdout.write(document)


# --------------------------------------------------------------------------
# validate-template
# --------------------------------------------------------------------------

VARIANT_ID = re.compile(
    r"^(Ultralight|Thin|Light|Regular|Medium|Semibold|Bold|Heavy|Black)-(S|M|L)$")


def validate_template_file(path):
    """Structural lint. Returns (problems, warnings, version, variant_ids)."""
    problems = []
    warnings = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as err:
        return [f"not well-formed XML: {err}"], [], None, []
    root = tree.getroot()
    by_id = {}
    for element in root.iter():
        identifier = element.get("id")
        if identifier:
            by_id.setdefault(identifier, element)

    # Required layers and the template-version note.
    for layer in ("Notes", "Guides", "Symbols"):
        if layer not in by_id:
            problems.append(f"missing <g id=\"{layer}\"> layer")
    version_node = by_id.get("template-version")
    if version_node is None or not (version_node.text or "").strip():
        problems.append('missing <text id="template-version"> in the Notes layer '
                        "(SF Symbols can't read the file without it)")

    for guide in ("Baseline-S", "Capline-S", "Baseline-M", "Capline-M",
                  "Baseline-L", "Capline-L"):
        if guide not in by_id:
            warnings.append(f"missing guide line '{guide}'")

    # Collect symbol variants.
    variants = {}
    symbols_layer = by_id.get("Symbols")
    if symbols_layer is not None:
        for group in symbols_layer:
            identifier = group.get("id", "")
            if VARIANT_ID.match(identifier):
                variants[identifier] = group
            elif _local(group.tag) == "g":
                warnings.append(f"unrecognized variant id '{identifier}' "
                                "(expected <Weight>-<S|M|L>)")
    if not variants:
        problems.append("no symbol variants found (need at least one "
                        "<g id=\"<Weight>-<S|M|L>\"> inside Symbols)")

    # Path-based check + interpolation source comparison.
    def signature(group):
        sigs = []
        for path in group.iter():
            if _local(path.tag) != "path":
                continue
            style = _style_dict(path)
            stroke = style.get("stroke", "none")
            if stroke not in ("none", "", "transparent"):
                problems.append(f"stroked path inside '{group.get('id')}' — "
                                "templates must be path-based (solid fills only)")
            try:
                ops = "".join(op for op, _ in parse_path_d(path.get("d", "")))
            except CustomSymbolError as err:
                problems.append(f"unparseable path in '{group.get('id')}': {err}")
                ops = "?"
            sigs.append(ops)
        return sigs

    signatures = {vid: signature(group) for vid, group in variants.items()}
    masters = [vid for vid in INTERPOLATION_MASTERS if vid in variants]
    if len(masters) == 3:
        counts = {vid: len(signatures[vid]) for vid in masters}
        if len(set(counts.values())) > 1:
            problems.append(f"interpolation masters have differing path counts: {counts}")
        else:
            for index in range(counts[masters[0]]):
                shapes = {signatures[vid][index] for vid in masters}
                if len(shapes) > 1:
                    problems.append(
                        f"path #{index + 1} differs in command structure across the "
                        "three masters — interpolation needs matching control points")
        for vid in masters:
            for side in ("left", "right"):
                if f"{side}-margin-{vid}" not in by_id:
                    warnings.append(f"missing margin guide '{side}-margin-{vid}'")
    elif masters:
        warnings.append(
            f"only {len(masters)} of the 3 interpolation masters "
            f"({', '.join(INTERPOLATION_MASTERS)}) present — the system can't "
            "interpolate the other weights; it will use the variants as-is")

    version = (version_node.text or "").strip() if version_node is not None else None
    return problems, warnings, version, sorted(variants)


def cmd_validate_template(args):
    problems, warnings, version, variants = validate_template_file(args.file)
    for warning in warnings:
        print(f"warn: {warning}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        sys.exit(1)
    print(f"PASS: {args.file} looks structurally valid ({version}; "
          f"variants: {', '.join(variants)})")
    print("note: authoritative validation is the SF Symbols app "
          "(File > Validate Templates) or an Xcode Symbol Image Set import.")


def open_in_sf_symbols(path):
    """Import a template into the SF Symbols app via its SVG document handler.

    The app registers as a viewer for public.svg-image and treats an opened
    SVG as a custom-symbol template import — no dialogs, lands in the
    Custom Symbols category with the filename stem as its display name.
    """
    import subprocess
    result = subprocess.run(["open", "-a", "SF Symbols", path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit("error: could not hand the file to the SF Symbols app — is it "
                 f"installed?\n{result.stderr.strip()}\n"
                 "Get it at https://developer.apple.com/sf-symbols/")
    name = os.path.splitext(os.path.basename(path))[0]
    print(f"imported into the SF Symbols app as '{name}' "
          "(Custom Symbols category — rename or annotate it there)")


def cmd_import(args):
    problems, warnings, _, _ = validate_template_file(args.file)
    for warning in warnings:
        print(f"warn: {warning}", file=sys.stderr)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        sys.exit("error: template failed structural validation — fix the issues "
                 "above before importing (the app rejects or mangles bad templates)")
    open_in_sf_symbols(args.file)


# --------------------------------------------------------------------------
# Rendering commands
# --------------------------------------------------------------------------

def cmd_svg(args):
    renderer = load_renderer()
    svg = renderer.symbol_to_svg(args.name, args.point_size, args.weight, args.scale)
    if svg is None:
        sys.exit(f"error: macOS could not resolve symbol '{args.name}' — "
                 f"check the name with: sf_symbols.py search \"{args.name}\"")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(svg)


def cmd_build_all(args):
    renderer = load_renderer()
    meta = metadata_from(args)
    names = meta.base_names() if args.base_only else sorted(meta.names)
    if args.limit:
        names = names[: args.limit]
    weights = WEIGHT_NAMES if "all" in args.weights else args.weights

    exported = skipped = unresolved = 0
    for weight in weights:
        out_dir = os.path.join(args.out, weight)
        os.makedirs(out_dir, exist_ok=True)
        for index, name in enumerate(names):
            out_path = os.path.join(out_dir, name + ".svg")
            if os.path.exists(out_path) and not args.force:
                skipped += 1
                continue
            with renderer.autorelease_pool():
                svg = renderer.symbol_to_svg(name, args.point_size, weight, args.scale)
            if svg is None:
                unresolved += 1
                continue
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(svg)
            exported += 1
            if (index + 1) % 500 == 0:
                print(f"  [{weight}] {index + 1}/{len(names)} "
                      f"ok={exported} skip={skipped} unresolved={unresolved}", flush=True)
    print(f"done: exported={exported} skipped={skipped} unresolved={unresolved} -> {args.out}")


GALLERY_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>SF Symbols gallery</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 14px -apple-system, sans-serif; margin: 1.5rem; }}
  header {{ display: flex; gap: 1rem; align-items: baseline; flex-wrap: wrap; }}
  #filter {{ font-size: 1rem; padding: .4rem .6rem; min-width: 18rem; }}
  #grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
          gap: .5rem; margin-top: 1rem; }}
  .card {{ border: 1px solid color-mix(in srgb, currentColor 25%, transparent);
          border-radius: .5rem; padding: .8rem .5rem; text-align: center;
          cursor: pointer; overflow: hidden; }}
  .card svg {{ height: 2.5rem; max-width: 90%; display: block; margin: 0 auto .5rem; }}
  .card .name {{ font-size: .72rem; word-break: break-all; opacity: .85; }}
  .card.copied {{ outline: 2px solid #34c759; }}
</style></head><body>
<header><h1>SF Symbols</h1>
  <input id="filter" type="search" placeholder="filter by name or keyword…" autofocus>
  <span id="count"></span><span style="opacity:.6">weight: {weight} — click a card to copy its name</span>
</header>
<div id="grid">{cards}</div>
<script>
  const cards = [...document.querySelectorAll('.card')];
  const count = document.getElementById('count');
  const update = () => {{
    const q = document.getElementById('filter').value.toLowerCase().trim();
    let visible = 0;
    for (const card of cards) {{
      const match = !q || card.dataset.terms.includes(q);
      card.style.display = match ? '' : 'none';
      if (match) visible++;
    }}
    count.textContent = visible + ' / ' + cards.length;
  }};
  document.getElementById('filter').addEventListener('input', update);
  update();
  for (const card of cards) card.addEventListener('click', async () => {{
    await navigator.clipboard.writeText(card.dataset.name);
    card.classList.add('copied');
    setTimeout(() => card.classList.remove('copied'), 600);
  }});
</script></body></html>
"""


def cmd_gallery(args):
    renderer = load_renderer()
    meta = metadata_from(args)
    names = select_names(meta, args)
    total = len(names)
    if args.limit and total > args.limit:
        names = names[: args.limit]
        print(f"note: rendering {args.limit} of {total} matches "
              "(raise --limit, or --limit 0 for all)", file=sys.stderr)

    keywords = meta.keywords
    cards = []
    for name in names:
        with renderer.autorelease_pool():
            svg = renderer.symbol_to_svg(name, 64.0, args.weight, "medium")
        if svg is None:
            continue
        terms = " ".join([name] + keywords.get(name, [])).lower()
        cards.append(f'<div class="card" data-name="{name}" data-terms="{terms}">'
                     f'{svg.strip()}<div class="name">{name}</div></div>')
    html = GALLERY_HTML.format(weight=args.weight, cards="\n".join(cards))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote {args.out} ({len(cards)} symbols) — open it in a browser")


def cmd_template(args):
    renderer = load_renderer()
    variants = []
    for master in INTERPOLATION_MASTERS:
        weight = master.split("-", 1)[0].lower()
        with renderer.autorelease_pool():
            outline = renderer.symbol_outline(args.name, TEMPLATE_POINT_SIZE, weight, "small")
        if outline is None:
            sys.exit(f"error: macOS could not resolve symbol '{args.name}' — "
                     f"check the name with: sf_symbols.py search \"{args.name}\"")
        commands, (min_x, min_y, width, height) = outline

        def to_local(x, y, min_x=min_x, min_y=min_y, height=height):
            # outlinePath is top-left oriented; recenter the bbox on the
            # cap-height midpoint (how the system aligns symbols vertically).
            return (x - min_x), (y - (min_y + height / 2.0)) - CAP_HEIGHT / 2.0

        d_strings = []
        current = []
        for op, points in commands:
            current.append((op, points))
        d_strings.append(renderer.path_data(current, to_local))
        variants.append((master, d_strings, width))

    document = emit_template(variants)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(document)
        print(f"wrote editable template for '{args.name}': {args.out}")
        print("note: vertical placement uses cap-height centering — symbols with "
              "intentional baseline overshoot may sit a touch off; nudge in your editor.")
    else:
        sys.stdout.write(document)


# --------------------------------------------------------------------------
# CLI wiring
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="sf_symbols.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--metadata-dir", help="SF Symbols app Metadata directory "
                        "(default: the installed app; env SF_SYMBOLS_METADATA_DIR)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="find symbols by keywords")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("list", help="enumerate symbols with filters")
    p.add_argument("--category", help="category key (see `categories`)")
    p.add_argument("--contains")
    p.add_argument("--starts-with")
    p.add_argument("--all-variants", dest="base_only", action="store_false",
                   help="include localized-script and .rtl variant names")
    p.add_argument("--limit", type=int, default=0, help="0 = no limit")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list, base_only=True)

    p = sub.add_parser("info", help="everything known about one symbol")
    p.add_argument("name")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("categories", help="list category keys and display names")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_categories)

    p = sub.add_parser("svg", help="emit one symbol as a clean single-path SVG")
    p.add_argument("name")
    p.add_argument("--weight", choices=WEIGHT_NAMES, default="regular")
    p.add_argument("--scale", choices=SCALE_NAMES, default="medium")
    p.add_argument("--point-size", type=float, default=256.0)
    p.add_argument("--out", help="output file (default: stdout)")
    p.set_defaults(func=cmd_svg)

    p = sub.add_parser("build-all", help="batch-export symbols to OUT/<weight>/<name>.svg")
    p.add_argument("--out", default="sf-symbol-svgs")
    p.add_argument("--weights", nargs="+", choices=WEIGHT_NAMES + ["all"],
                   default=["regular"])
    p.add_argument("--scale", choices=SCALE_NAMES, default="medium")
    p.add_argument("--point-size", type=float, default=256.0)
    p.add_argument("--all-variants", dest="base_only", action="store_false",
                   help="include localized-script and .rtl variant names")
    p.add_argument("--limit", type=int, default=0, help="first N names only (smoke test)")
    p.add_argument("--force", action="store_true", help="re-export existing files")
    p.set_defaults(func=cmd_build_all, base_only=True)

    p = sub.add_parser("gallery", help="generate a filterable HTML gallery")
    p.add_argument("--out", default="sf-symbols-gallery.html")
    p.add_argument("--weight", choices=WEIGHT_NAMES, default="regular")
    p.add_argument("--category", help="category key (see `categories`)")
    p.add_argument("--search", help="rank/filter by a search query first")
    p.add_argument("--contains")
    p.add_argument("--starts-with")
    p.add_argument("--limit", type=int, default=400, help="0 = render everything")
    p.set_defaults(func=cmd_gallery, base_only=True)

    p = sub.add_parser("custom",
                       help="wrap arbitrary SVG art into a custom-symbol template")
    p.add_argument("input", help="source SVG file (filled paths; no strokes/gradients)")
    p.add_argument("--out", help="output template file (default: stdout)")
    p.add_argument("--scale", type=float, default=1.0,
                   help="art height relative to cap height (default 1.0)")
    p.add_argument("--static", action="store_true",
                   help="emit a single Regular-M variant instead of the 3 "
                        "interpolation masters")
    p.add_argument("--ignore-strokes", action="store_true",
                   help="drop stroked shapes instead of failing")
    p.add_argument("--import", dest="do_import", action="store_true",
                   help="after writing, import into the SF Symbols app "
                        "(the --out filename stem becomes the symbol's name)")
    p.set_defaults(func=cmd_custom)

    p = sub.add_parser("validate-template",
                       help="structural lint for custom-symbol template SVGs")
    p.add_argument("file")
    p.set_defaults(func=cmd_validate_template)

    p = sub.add_parser("import",
                       help="validate a template, then import it into the "
                            "SF Symbols app (macOS; filename stem = symbol name)")
    p.add_argument("file")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("template",
                       help="export an editable custom-symbol template of a system symbol")
    p.add_argument("name")
    p.add_argument("--out", help="output template file (default: stdout)")
    p.set_defaults(func=cmd_template)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
