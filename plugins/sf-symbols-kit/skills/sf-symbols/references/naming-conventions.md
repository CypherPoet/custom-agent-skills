# SF Symbol Naming Conventions

How symbol names are structured — for predicting names when searching, and for
naming custom symbols consistently. The grammar below is derived empirically
from the SF Symbols 7.2 catalog (9,184 names, read live from the app's
`name_availability.plist`); counts cited are from that analysis.

## The Grammar

Names are lowercase, dot-separated, reading roughly **base concept → state
modifiers → enclosure → fill → badge → script/direction variants**:

```
<base>[.<detail>…][.slash][.<enclosure>][.fill][.badge.<content>][.<lang>|.rtl]
```

Examples spanning the pattern: `heart`, `heart.fill`, `heart.slash`,
`heart.circle`, `heart.circle.fill`, `bag.fill.badge.plus`,
`textformat.size.ar`, `arrow.left.rtl`.

## Ordering Rules (with Catalog Evidence)

- **`.fill` comes last** within the styled core: 2,635 names end in `.fill`.
  The main exception is badges — fill binds to the *base*, then the badge
  follows: `bag.fill.badge.plus`, `camera.fill.badge.ellipsis` (~106 cases).
- **Enclosure precedes fill**: `heart.circle.fill` means "filled circle
  enclosing a heart" — `.circle.fill` appears 829 times vs `.fill.circle` 5.
- **Slash precedes the enclosure**: `bell.slash.circle` (52 `.slash.circle`
  vs 1 `.circle.slash`).
- **Enclosures by frequency**: circle (1,801 names), square (922),
  rectangle (297), triangle (273), shield (30), diamond (27), capsule (13),
  octagon (4).
- **Badges** read `<base>.badge.<content>` where content is the badge glyph:
  `app.badge`, `person.badge.plus`, `wifi.badge.exclamationmark` (656 names).
- **Directional suffixes** (`.up`, `.down`, `.left`, `.right`, `.forward`,
  `.backward`) belong to the base concept (`arrow.up.right`,
  `chevron.left`) — they are not style modifiers.
- **Script/locale variants** terminate the name: ISO-ish script codes
  (`.ar`, `.he`, `.hi`, `.th`, `.zh`, `.ja`, `.ko`, …) and `.rtl` for
  right-to-left mirrors. These are auto-selected by the system at runtime;
  the CLI's `classify()` treats them as variants of the base name.

## Practical Implications for Search

- A "filled" request maps to `<name>.fill` — 2,548 bases have a `.fill` twin,
  so check both (`list --contains <base>` shows the family).
- Users describing "X in a circle" want `<x>.circle(.fill)`; "crossed-out X"
  wants `<x>.slash`.
- Newer names sometimes use `.filled` as an inner segment for variants of
  enclosing shapes (e.g. `rectangle.inset.filled`) — try both `fill` and
  `filled` when a literal lookup misses.

## Naming Custom Symbols

Apple's convention for custom symbols mirrors the system grammar; following it
keeps call sites readable and lets variants slot in later:

- Lowercase, dot-separated, base-first: `burger`, `burger.fill`,
  `burger.circle.fill` — not `FilledBurgerIcon`.
- Avoid names that collide with system symbols (check with
  `python3 scripts/sf_symbols.py info <name>` — "unknown symbol" means free).
  Some teams prefix a namespace (`acme.burger`) to guarantee no collision
  with future system releases.
- **For this skill's import flow, the name comes from the filename**: the
  `--out` filename stem becomes the symbol's display name in the SF Symbols
  app (`--out burger.fill.svg` → `burger.fill`). Pick the final symbol name
  before generating, not after.
- Margin guide ids inside templates follow their own fixed pattern —
  `left-margin-<Weight>-<S|M|L>` (e.g. `left-margin-Regular-M`). Keep that
  exact form when hand-editing; the system matches on it (HIG, Custom
  symbols section).

Sources: catalog analysis as above;
<https://developer.apple.com/design/human-interface-guidelines/sf-symbols>
(Design variants, Custom symbols).
