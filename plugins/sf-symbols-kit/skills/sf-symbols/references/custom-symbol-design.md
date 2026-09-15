# Designing Custom Symbols

Distilled from the SF Symbols HIG (Custom symbols section,
<https://developer.apple.com/design/human-interface-guidelines/sf-symbols>)
and Apple's template format article
(<https://developer.apple.com/documentation/uikit/creating-custom-symbol-images-for-your-app>).
Use this when advising on custom-symbol artwork, hand-editing a template, or
debugging an import/validation failure.

## Design Principles (HIG)

A custom symbol should match the system set in level of detail, optical
weight, alignment, position, and perspective. Strive for: **simple,
recognizable, inclusive, directly related** to what it represents.

- **Start from a similar system symbol.** Apple's recommended flow is to
  export an existing symbol's template and modify it — that's exactly what
  this skill's `template <name>` command produces.
- **Don't rebuild common variants by hand.** The SF Symbols app has a
  *component library* for adding enclosures, badges, and slashes to a custom
  symbol — use it instead of drawing `.circle`/`.badge` variants yourself, so
  the variants stay visually consistent with the system set.
- **Draw whole shapes, not cutouts.** A figure partially hidden behind
  another should still be drawn complete, with a separate offset path
  annotated later as an *erase layer*. Whole shapes preserve the layer
  information animations need (a person-behind-person symbol animates wrong
  if the back figure is a cutout).
- **Provide accessibility labels.** Custom symbols need alternative text so
  VoiceOver can describe them.
- **Never replicate Apple products** (copyrighted), and symbols the app
  flags as representing Apple features/products can't be customized.

## Template Anatomy (What the Emitted/Imported SVG Contains)

A 3300×2200 canvas with three layers:

- `#Notes` — required `<text id="template-version">` plus an artboard rect.
  Removing the version note makes the file unreadable to SF Symbols.
- `#Guides` — `Baseline-{S,M,L}` / `Capline-{S,M,L}` lines (cap height
  70.459 units at the 100 pt design size; baselines y = 696/1126/1556), and
  optional per-variant margins `left-margin-<Variant>` /
  `right-margin-<Variant>`. Negative margins are allowed and help optical
  alignment of badge-widened symbols.
- `#Symbols` — variant groups id'd `<Weight>-<S|M|L>`, each translated so the
  group origin is (left margin, baseline) with art above the baseline in
  negative y.

**Interpolation:** a template is *variable* when `Ultralight-S`, `Regular-S`,
and `Black-S` are present, path-based, and share path count and control-point
structure — the system then generates the other 24 variants. Any explicitly
present variant overrides interpolation for that configuration. Scale factors
S/M/L = 0.783/1.0/1.29.

**Path rules:** solid flat fills only — convert strokes to outlines, no
gradients/effects; nested paths with opposite winding punch holes. The CLI's
`custom` enforces these and `validate-template` lints them.

**Versions:** v2 = monochrome only (iOS 14); v3 = + annotations & explicit
margins (iOS 15+, what this skill emits); v4 = + variable-color thresholds
(iOS 16+). Deploying to iOS 14 requires exporting v2 + v3 + v4 and switching
on OS version; iOS 15+ needs only v3+.

## Workflow Map (Skill Commands → Apple's Steps)

| Apple's step | This skill |
|---|---|
| Export a template to start from | `template <system-symbol> --out base.svg` |
| Create art / edit in vector tool | user's editor (export SVG at ≥7 decimal precision from Illustrator) |
| Convert arbitrary art to a template | `custom art.svg --out name.svg` |
| Validate | `validate-template` (lint) → SF Symbols app File > Validate Templates or Xcode import (authoritative) |
| Import into the app | `import name.svg` or `custom … --import` |
| Annotate layers/colors or Draw guide points, add variants via components | SF Symbols app GUI |
| Distribute | app File > Export Symbol (choose version per deployment target) |
| Use it in your app | add to an asset-catalog Symbol Image Set; load by asset name with the *named* initializer (not `systemName`) |

## Using a Custom Symbol in Your App

Once the template is ready, a custom symbol ships inside your Xcode **asset
catalog** as a Symbol Image Set — select the catalog, then Editor ▸ Add New
Asset ▸ Symbol Image Set and drag the SVG into the Symbol SVG well (Xcode
re-validates and shows errors if the file doesn't conform). You then load it
much like a system symbol, with one catch: custom and system symbols live in
**separate namespaces**, so the initializer differs by image type.

| Framework | System symbol | Custom symbol (asset catalog) |
|---|---|---|
| SwiftUI | `Image(systemName: "multiply.circle.fill")` | `Image("custom.multiply.circle")` |
| UIKit | `UIImage(systemName: "multiply.circle.fill")` | `UIImage(named: "custom.multiply.circle")` |
| AppKit | `NSImage(systemSymbolName:accessibilityDescription:)` | `NSImage(named: "custom.multiply.circle")` |

Each loader resolves only its own image type — Apple's docs note this "avoids
namespace collisions between your custom images and the system images." So
passing a custom symbol's name to `systemName:` returns nil; use the plain
`named:` / `Image(_:)` form and pass the **asset name** (what you called the
Symbol Image Set), which need not equal the original filename. After loading,
configure weight, scale, and rendering mode exactly as for a system symbol — see
Apple's [Configuring and displaying symbol images in your UI](https://developer.apple.com/documentation/uikit/configuring-and-displaying-symbol-images-in-your-ui)
and [Use your custom symbol images](https://developer.apple.com/documentation/uikit/creating-custom-symbol-images-for-your-app#Use-your-custom-symbol-images).
