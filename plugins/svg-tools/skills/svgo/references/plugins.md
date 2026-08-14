# SVGO plugin catalog

Every plugin SVGO ships with, grouped by whether it's part of `preset-default`. Verified against SVGO 4.0.1. Run `npx svgo --show-plugins` in the project to see the list at the version installed there — the bundle membership occasionally shifts between majors.

Tables include the one-line behavior and a "when to flip" note. Plugins flagged with ⚠ have safety tradeoffs worth understanding before enabling/disabling.

## Table of Contents

| Section | Covers |
|---|---|
| [Plugins in `preset-default` (on by default)](#plugins-in-preset-default-on-by-default) | `preset-default` plugins, what they do, and when to disable them |
| [Plugins NOT in `preset-default` (opt-in)](#plugins-not-in-preset-default-opt-in) | Opt-in plugins, what they do, and when to enable them |
| [Configuring plugins](#configuring-plugins) | Object, name-plus-params, and preset plugin configuration shapes |
| [Notes](#notes) | Version drift in default plugin bundles and the need to pin explicit configurations |

## Plugins in `preset-default` (on by default)

| Plugin | What it does | When to disable |
|--------|--------------|-----------------|
| `cleanupAttrs` | Cleans up attribute values from newlines, trailing and repeating spaces | Almost never |
| `cleanupEnableBackground` | Removes or cleans the `enable-background` attribute | Almost never |
| `cleanupIds` ⚠ | Removes unused IDs; minifies the rest (`a`, `b`, …) | When multiple optimized SVGs are inlined in the same HTML doc (use `prefixIds` instead, or in addition) |
| `cleanupNumericValues` | Rounds numeric values; strips default `px` units | If exact source numbers must be preserved |
| `collapseGroups` | Collapses useless `<g>` wrappers | If JS/CSS targets group structure |
| `convertColors` | Normalizes colors (`rgb()` → `#rrggbb`, `#rrggbb` → `#rgb` when safe) | Almost never |
| `convertEllipseToCircle` | Rewrites non-eccentric `<ellipse>` as `<circle>` | Almost never |
| `convertPathData` ⚠ | Optimizes path commands (relative coords, shorter forms, applies transforms) | If JS/animation reads exact path command structure |
| `convertShapeToPath` | Converts `<rect>`, `<line>`, etc. to `<path>` | If CSS targets the original element types |
| `convertTransform` | Collapses and shortens `transform=""` chains | Almost never |
| `inlineStyles` ⚠ | Moves `<style>` rules onto matching elements as `style=""` | If the SVG depends on external CSS or runtime style switching; can also bloat output |
| `mergePaths` ⚠ | Combines adjacent `<path>` elements into one | If individual paths are styled or animated separately |
| `mergeStyles` | Merges multiple `<style>` elements into one | Almost never |
| `minifyStyles` | Minifies CSS inside `<style>`; drops unused rules | If runtime CSS selector matching depends on the unused rules |
| `moveElemsAttrsToGroup` | Lifts common attrs from group children to the parent group | Almost never |
| `moveGroupAttrsToElems` | Inverse — pushes group attrs to children | Almost never |
| `removeComments` | Strips `<!-- … -->` | If comments carry license attribution that must remain |
| `removeDeprecatedAttrs` | Strips deprecated SVG attributes | Almost never |
| `removeDesc` | Removes `<desc>` | If `<desc>` is used for accessibility (rare in icons; significant in diagrams) |
| `removeDoctype` | Strips `<!DOCTYPE …>` | Almost never |
| `removeEditorsNSData` | Removes Inkscape/Illustrator/Sketch metadata | Almost never |
| `removeEmptyAttrs` | Drops `attr=""` | Almost never |
| `removeEmptyContainers` | Removes empty `<g>`, `<defs>`, etc. | If a container is populated by JS at runtime |
| `removeEmptyText` | Removes empty `<text>` elements | Almost never |
| `removeHiddenElems` ⚠ | Removes hidden/invisible elements (zero-sized, `display:none`, etc.) | If elements are intentionally hidden and revealed by CSS/JS toggles or sprite offsets |
| `removeMetadata` | Removes `<metadata>` | If license metadata must remain |
| `removeNonInheritableGroupAttrs` | Drops non-inheritable presentation attrs from groups | Almost never |
| `removeUnknownsAndDefaults` | Removes unknown elements/attrs and attrs equal to spec defaults | If a downstream parser depends on explicit default values |
| `removeUnusedNS` | Removes namespace declarations not referenced | Almost never |
| `removeUselessDefs` | Removes `<defs>` children that have no `id` (unreferenceable) | Almost never |
| `removeUselessStrokeAndFill` | Removes redundant `stroke`/`fill` attributes | If a CSS selector relies on them |
| `removeXMLProcInst` | Strips `<?xml … ?>` | Almost never |
| `sortAttrs` | Sorts attributes for compression-friendly output | Almost never |
| `sortDefsChildren` | Sorts `<defs>` children for better compression | Almost never |

## Plugins NOT in `preset-default` (opt-in)

| Plugin | What it does | When to enable |
|--------|--------------|----------------|
| `addAttributesToSVGElement` | Adds attributes to the outer `<svg>` | Inject `fill="currentColor"`, `role="img"`, `aria-hidden`, etc. for icon systems |
| `addClassesToSVGElement` | Adds class names to the outer `<svg>` | Tag icons for CSS-driven sizing/coloring |
| `cleanupListOfValues` | Rounds list-of-values attributes (e.g., `viewBox`, `points`) | Aggressive pixel-grid optimization |
| `convertOneStopGradients` | Replaces 1-stop gradients with the underlying solid color | When upstream tooling emits single-stop gradients |
| `convertStyleToAttrs` | Inverse of `inlineStyles` — moves inline `style=""` to dedicated attributes | When you need attribute-style output (e.g., styled with CSS by attribute selectors) |
| `prefixIds` ⚠ | Prefixes all `id`s to avoid collisions | When inlining multiple SVGs into one HTML page; pair with or replace `cleanupIds` |
| `removeAttributesBySelector` | Removes attributes from elements matching a CSS selector | Targeted cleanup (e.g., strip `fill` from `path.icon-stroke`) |
| `removeAttrs` | Removes specified attributes globally | Strip `data-name`, `class`, etc. from a known authoring tool |
| `removeDimensions` | Removes `width`/`height` when `viewBox` is present | When you want responsive scaling — opposite of `removeViewBox` |
| `removeElementsByAttr` | Removes elements by `id` or `className` | Drop guide layers, named scaffolding |
| `removeOffCanvasPaths` | Removes paths fully outside the `viewBox` | When authoring tools leak off-canvas geometry |
| `removeRasterImages` | Removes embedded raster (`<image>`) | Vector-only pipelines; ensures no PNG/JPEG slips into the bundle |
| `removeScripts` | Removes `<script>` | Almost always desirable for static assets; security hygiene for user-uploaded SVGs |
| `removeStyleElement` | Removes `<style>` entirely | When all styling is handled outside the SVG |
| `removeTitle` | Removes `<title>` | Icons where the title comes from surrounding markup (`<button aria-label>`); keep for standalone SVGs that need accessible names |
| `removeViewBox` ⚠ | Removes `viewBox` when `width`/`height` are set | Only for fixed-size SVGs that never resize — breaks responsive scaling otherwise |
| `removeXlink` | Replaces `xlink:href` with the SVG 2 `href` | When targeting SVG 2 renderers only (modern browsers); legacy renderers may still need the namespaced form |
| `removeXMLNS` ⚠ | Removes the `xmlns` attribute | Only when the SVG is inlined into HTML — breaks standalone use (`<img>`, CSS `url()`, file viewers) |
| `reusePaths` | Replaces duplicate `<path>` elements with `<use>` referencing a single def | Aggressive compression of icon sets with repeated shapes |

## Configuring plugins

Three shapes you'll write:

### Reference by name (uses plugin defaults)

```js
plugins: ['prefixIds', 'removeScripts'];
```

### Configure plugin params

```js
plugins: [
  { name: 'prefixIds', params: { prefix: 'icon', delim: '-' } },
];
```

### Override `preset-default` members

```js
plugins: [
  {
    name: 'preset-default',
    params: {
      overrides: {
        cleanupIds: false,                     // disable
        inlineStyles: { onlyMatchedOnce: false }, // tune params
      },
    },
  },
  'prefixIds', // additional non-default plugin
];
```

`overrides` accepts `false` (disable) or a plugin-params object (tune). Setting `true` is rare and only useful when you want to re-enable a plugin a parent config disabled.

## Notes

- Bundle membership is not stable across SVGO majors. The shift between v2 and v3 also renamed `cleanupIDs` → `cleanupIds`. Verify with `--show-plugins` in any project you don't recognize.
- Plugin order matters for non-default plugins listed in the `plugins` array. `preset-default` always runs as a single ordered block; plugins listed after it run after the preset.
- Custom plugins (functions you author) are supported in the same `plugins` array — see the official docs at https://svgo.dev/docs/plugins/.
