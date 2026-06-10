---
name: sf-symbols
description: >-
  Work with Apple SF Symbols end to end. Use whenever the user wants to find or
  look up an SF Symbol ("what symbol/icon fits X?", "is there an SF Symbol for
  a coffee mug?"), list or browse SF Symbols (including an HTML gallery),
  inspect a symbol's availability/keywords/categories, generate or export an SF
  Symbol as a clean SVG at any weight, build an SF Symbol icon set for a
  web/THREE.js/design project, or create CUSTOM SF Symbols — converting their
  own SVG art into an importable symbol template, exporting an editable
  template of a system symbol, or validating a template file. Triggers include
  "SF Symbol(s)", "Apple icons", "system symbol", "symbol image set",
  "convert this SVG to an SF Symbol", and "custom symbol".
---

# SF Symbols

One bundled CLI does everything: `scripts/sf_symbols.py` (paths relative to this
skill's directory). Lookup commands need only the Python stdlib; rendering
commands need macOS + PyObjC and import it lazily.

```shell
python3 scripts/sf_symbols.py <subcommand> --help   # every flag, per subcommand
```

| Subcommand | What it does | Needs |
|---|---|---|
| `search <query>` | Rank symbols by name/keyword/category match | stdlib |
| `list` | Enumerate symbols (`--category`, `--contains`, `--starts-with`) | stdlib |
| `info <name>` | Year, min OS per platform, keywords, categories, aliases | stdlib |
| `categories` | Category keys + display names + counts | stdlib |
| `custom <art.svg>` | Wrap arbitrary SVG art into a custom-symbol template | stdlib |
| `validate-template <file>` | Structural lint for a symbol template SVG | stdlib |
| `import <file>` | Validate a template, then import it into the SF Symbols app | macOS |
| `svg <name>` | One symbol as a clean single-path SVG (`--weight`, `--scale`) | PyObjC |
| `build-all` | Batch-export to `OUT/<weight>/<name>.svg` | PyObjC |
| `gallery` | Filterable, click-to-copy HTML gallery | PyObjC |
| `template <name>` | Editable custom-symbol template of a system symbol | PyObjC |

Requirements: metadata is read live from the installed SF Symbols app
(`/Applications/SF Symbols.app`); override with `--metadata-dir` or
`SF_SYMBOLS_METADATA_DIR`. Rendering needs `pip install pyobjc-framework-cocoa`
(the CLI prints this hint itself if missing) — prefer a venv that already has it.

## Finding a Symbol from a Vague Description

Apple's curated keywords cover ~3,200 symbols, so lexical search works well —
but expand the user's phrasing into synonyms yourself before giving up:

1. Run `search` with the user's words: `search "coffee mug"` → `mug`,
   `cup.and.saucer`, `cup.and.heat.waves` (with matched-on reasons per hit).
2. No good hit? Re-run with synonyms and related concepts ("trash" → "delete
   bin garbage", "settings" → "gear preferences"). Try `--limit 40`.
3. Still unsure which fits? Offer a visual pass:
   `gallery --search "<query>" --out /tmp/symbols.html` and open it.
4. Present the top candidates with one-line descriptions, then offer to export
   (`svg`) or show `info` for the chosen one.

Name conventions help searching: style suffixes like `.fill`, `.circle`,
`.slash` are separate catalog entries; localized (`.ar`, `.hi`, …) and `.rtl`
mirror variants are excluded by default (include with `--all-variants`).

## Exporting SVGs

`svg <name> --weight bold --out heart.svg` emits a tight-viewBox, single-path
SVG with `fill="currentColor"` — recolorable via CSS or a THREE.js material.
All 9 weights (`ultralight`…`black`) and 3 optical scales work. For full icon
sets use `build-all --out DIR --weights regular bold` (or `--weights all`);
existing files are skipped unless `--force`, so reruns are resumable.

## Custom SF Symbols (SVG → Symbol)

The conversion pipeline targets Apple's documented template format
(<https://developer.apple.com/documentation/uikit/creating-custom-symbol-images-for-your-app>):

- `custom art.svg --out my.symbol.svg` fits the art to the symbol cap-height
  box and emits a **variable template** (interpolation masters `Ultralight-S`,
  `Regular-S`, `Black-S` — identical copies, so every weight renders the same
  until a designer refines the masters in a vector editor). `--static` emits a
  single `Regular-M` instead; `--scale 1.2` makes the art 20% larger relative
  to cap height (useful optical compensation for round shapes).
- Input must be **path-based**: solid flat fills only. The CLI converts
  `rect`/`circle`/`ellipse`/`polygon`/`polyline` + transforms automatically and
  fails with actionable guidance on strokes, gradients, text, or clip paths
  (most need one "outline/expand" step in the user's vector editor first).
- `template <system-symbol> --out base.svg` exports an editable template of an
  existing symbol — Apple's recommended starting point for a new design.
- `validate-template <file>` lints structure (required `template-version` note,
  layers, variant ids, master path-count/control-point parity). Authoritative
  validation: the SF Symbols app (File > Validate Templates) or an Xcode asset
  catalog import; `xcrun actool` compile also works headlessly.

**Getting it into the SF Symbols app** is automated: `custom … --import` (or
`import <file>` for a template edited elsewhere) validates the file and hands
it to the app via `open -a "SF Symbols"` — the app registers as an SVG viewer
and treats an opened SVG as a custom-symbol import, no dialogs. The **filename
stem becomes the symbol's display name** (`--out my.bolt.svg` → `my.bolt`), so
name the output file what the symbol should be called. For Xcode, drop the
file into a **Symbol Image Set** in an asset catalog instead. Color annotations
(multicolor/hierarchical/variable color) are applied afterwards in the SF
Symbols app GUI — the emitted template is monochrome v3.0 (iOS 15+).

## Licensing Note

When exporting symbol artwork, remind the user once: Apple licenses SF Symbols
for use "as is" in apps for Apple platforms per the Xcode/SF Symbols agreements;
symbols may not be used as app icons, logos, or trademarks, and some symbols
representing Apple features/devices have usage restrictions (the `info` command
and the SF Symbols app flag these contexts). Custom symbols made from the
user's own art carry no such restriction.
