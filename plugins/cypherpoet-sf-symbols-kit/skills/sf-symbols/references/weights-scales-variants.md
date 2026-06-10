# Weights, Scales, and Design Variants

Distilled from the SF Symbols HIG
(<https://developer.apple.com/design/human-interface-guidelines/sf-symbols>,
Weights and scales / Design variants sections). Use this when picking the
right weight/scale/variant for a context, or explaining the 27-variant grid.

## Nine Weights

Each symbol weight — ultralight, thin, light, regular, medium, semibold,
bold, heavy, black — corresponds 1:1 to a San Francisco font weight, so a
symbol can weight-match adjacent text exactly. The CLI exposes all nine via
`--weight` (they map to the `NSFontWeight*` AppKit constants).

## Three Scales

Small, medium (default), large — defined **relative to the cap height** of
the SF font at the same point size. Scale changes a symbol's visual emphasis
next to text *without* breaking the weight match or changing the point size:

- Small ≈ 0.783× medium; large ≈ 1.29× medium (Apple's template scale factors).
- At medium scale a round symbol slightly overshoots cap height and baseline
  (optical rounding); at small it sits within them; at large it dominates.

9 weights × 3 scales = the 27-variant grid a static custom-symbol template
contains. In template coordinates (100 pt design size) the cap height is
70.459 units — the geometry the `custom`/`template` emitters use.

## Design Variants (Choosing Between Symbol Family Members)

The catalog encodes variants as separate names (see
[naming-conventions.md](naming-conventions.md)). HIG guidance on when to use
which:

- **Outline** (the unsuffixed base) — the most common variant; no solid
  areas, resembles text. Best in toolbars, lists, and anywhere a symbol sits
  beside text.
- **Fill** (`.fill`) — solid areas give more visual emphasis. Preferred for
  iOS tab bars, swipe actions, and selected states with an accent color.
- **Slash** (`.slash`) — unavailable/disabled/prohibited states
  (`bell.slash`, `wifi.slash`).
- **Enclosed** (`.circle`, `.square`, `.rectangle`, …) — the enclosing shape
  improves legibility at small sizes and gives a larger tap target feel.
  Enclosures combine with fill (`heart.circle.fill`).
- **Localized/script variants** (`.ar`, `.he`, `.zh`, …, `.rtl`) — adapt
  automatically to the device language and writing direction; never select
  them manually by name.

Note: many system views pick outline vs fill for you (iOS tab bars prefer
fill, toolbars prefer outline) — you often don't need to specify the variant
in code, just the base symbol.

## CLI Tie-Ins

- `svg <name> --weight bold --scale large` exports any of the 27 variants.
- `list --contains <base>` reveals a symbol's whole variant family.
- `build-all --weights all` exports the full 9-weight set per symbol.
