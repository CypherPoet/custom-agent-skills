---
name: svgo
description: >
  Use this skill any time the user is dealing with SVGO or with SVGs that need
  to get smaller. Trigger when they want to shrink, minify, compress, optimize,
  or clean up SVG files or folders — for any reason (Lighthouse, bundle size,
  perf, icon sets, inlined icons, hero illustrations). Also trigger when SVGO
  (or the VSCode SVGO extension, same engine) produced something broken: wrong
  gradients, swapped colors across inlined icons, hover states gone,
  viewBox/scaling lost, hidden elements vanishing, ID collisions. Use for
  choosing or disabling plugins (prefixIds, cleanupIds, removeViewBox,
  multipass), writing or debugging `svgo.config.mjs`, wiring SVGO into a build
  (Vite, webpack, prebuild) via CLI or the Node `optimize()` API, recovering
  when `svgo -f`/`-rf` overwrote sources in place, or comparing CLI flags.
  Skip for: non-SVG formats (PNG/JPEG/WebP), hand-editing SVG content (colors,
  paths, shapes), SVGR / SVG-to-React, and SVG hosting/serving unrelated to
  byte size.
---

# SVGO

A manual for driving [SVGO](https://github.com/svg/svgo), the SVG optimizer. SVGO is a Node CLI and library that runs a configurable pipeline of plugins over an SVG to shrink it. Most of the time you want the default pipeline (`preset-default`); the value of this skill is knowing the few defaults to *turn off* for the SVG to keep working in its target context, and the few non-default plugins to *turn on*.

The deep references live alongside this file:

- `references/cli-flags.md` — every flag with edge cases.
- `references/plugins.md` — every plugin, default-status, when to flip it.
- `references/programmatic-api.md` — `optimize()` and `loadConfig()` from Node.

## Step 1: Check the SVGO version

Before pinning a config, run:

```bash
npx svgo --version
```

SVGO 3.x and 4.x are the current majors; 2.x has a notable rename — `cleanupIDs` (uppercase D) became `cleanupIds` in v3. If you see a v2 config in a project that's being upgraded, that one rename is the most common breakage. Don't pin a major version in code you write unless the user asks.

## Step 2: Invocation

SVGO can run three ways:

- **No install:** `npx svgo …` — fine for one-off tasks.
- **Installed locally:** `npm install --save-dev svgo` then `npx svgo …` (uses the pinned version).
- **As a Node library:** `import { optimize } from 'svgo'` — see `references/programmatic-api.md`.

The most useful CLI commands:

```bash
# Optimize in place (overwrites the original — be sure that's OK)
svgo icon.svg

# Optimize to a new path
svgo icon.svg -o icon.min.svg

# Take SVG from stdin, write to stdout (great for pipelines)
cat icon.svg | svgo -i - -o -

# Optimize an SVG string directly (no file)
svgo -s '<svg>...</svg>' -o out.svg

# Optimize every *.svg under a folder, recursively, writing into a parallel tree
svgo -rf src/icons -o dist/icons

# Output as a base64 data URI (good for inlining into CSS)
svgo icon.svg --datauri base64 -o icon.datauri.txt

# Use a specific config
svgo icon.svg --config svgo.config.mjs
```

`--exclude` works only with `--folder` and takes **regex patterns**, not globs.

## Essential CLI flags

| Flag | What it does |
|------|--------------|
| `-i, --input <files…>` | Input file(s); `-` reads from stdin |
| `-s, --string <svg>` | Read SVG from a string argument |
| `-f, --folder <dir>` | Input folder (rewrites in place unless `-o` is given) |
| `-o, --output <path…>` | Output file/folder; `-` writes to stdout |
| `-r, --recursive` | Recurse into `--folder` (no effect without `-f`) |
| `--exclude <regex…>` | Skip files matching regex (folder mode only) |
| `-p, --precision <int>` | Fractional-digit precision; overrides plugin params |
| `--config <path>` | Custom config (`.js`, `.mjs`, `.cjs`) |
| `--multipass` | Re-run the pipeline until output stops shrinking |
| `--pretty` | Pretty-print the output |
| `--indent <int>` | Spaces per indent level when `--pretty` |
| `--eol <lf\|crlf>` | Force line endings |
| `--final-newline` | Ensure trailing newline |
| `--datauri <fmt>` | Emit a data URI: `base64`, `enc` (URI-encoded), `unenc` |
| `--show-plugins` | Print every available plugin and exit |
| `-q, --quiet` | Suppress non-error output |

Full reference, including edge cases (stdin + folder combinations, `--exclude` regex semantics, what `-p` overrides): `references/cli-flags.md`.

## The plugin model

SVGO is a pipeline of plugins. The default pipeline is the `preset-default` bundle (~34 plugins). You don't list those individually — you reference the bundle and *override* members inside it. Plugins outside the bundle are added explicitly.

Run `npx svgo --show-plugins` in the project to see the complete list at the version SVGO is pinned to.

## High-impact plugin tradeoffs

Most plugins in `preset-default` are safe and you can ignore them. These are the ones whose default behavior most often surprises people, plus the non-default ones worth knowing:

| Plugin | In `preset-default`? | When to flip it |
|--------|----------------------|-----------------|
| `removeViewBox` | No (default off) | Leave off. Turning it on strips `viewBox` and breaks responsive scaling — the SVG no longer fills its container. Only enable for SVGs with fixed `width`/`height` you never resize. |
| `cleanupIds` | Yes | Disable (`cleanupIds: false`) when multiple optimized SVGs get inlined into the same HTML page — short minified IDs (`a`, `b`, …) collide across files. Alternative: pair with `prefixIds`. |
| `prefixIds` | No | Enable when inlining several SVGs into one HTML doc, or when IDs are referenced from external CSS/JS. Prevents the `cleanupIds` collision. |
| `removeHiddenElems` | Yes | Disable if any element is intentionally hidden and revealed by CSS/JS (`display:none` toggled at runtime, off-screen sprite cells). It removes them by default. |
| `removeXMLNS` | No | Only safe when the SVG is inlined into HTML. Breaks standalone use (`<img src>`, CSS `url()`, file viewers). |
| `removeXlink` | No | Enable when targeting SVG 2 only. Rewrites `xlink:href` to `href`; older renderers may still need the namespaced form. |
| `convertPathData` | Yes | Leave on. Disable only if you have JS/animation that targets exact path-command structure. |
| `mergePaths` | Yes | Disable if individual `<path>` elements are styled or animated separately — merging makes them one path. |
| `inlineStyles` | Yes | Disable if the SVG relies on external CSS or runtime style changes; inlining can also bloat output if many CSS rules target few elements. |
| `removeRasterImages` | No | Enable to strip embedded PNG/JPEG fallbacks from a vector-only pipeline. |
| `reusePaths` | No | Enable for aggressive compression when many `<path>`s share identical `d`/`fill`/`stroke`; replaces duplicates with `<use>` references. |
| `removeDimensions` | No | Opposite of `removeViewBox`. Enable when you *want* responsive scaling and the source has both `width`/`height` and `viewBox`. |

Full catalog (every plugin, what it does, default-status, tradeoffs): `references/plugins.md`.

## Config file shape

SVGO looks for `svgo.config.mjs` (or `.js` / `.cjs`) in the working directory. Missing config falls back silently to `preset-default` — no error.

Minimal config (just enables multipass on top of defaults):

```js
// svgo.config.mjs
export default {
  multipass: true,
};
```

Override members of `preset-default`:

```js
// svgo.config.mjs
export default {
  multipass: true,
  plugins: [
    {
      name: 'preset-default',
      params: {
        overrides: {
          // keep viewBox (already the default, shown for clarity)
          removeViewBox: false,
          // disable a default-on plugin
          cleanupIds: false,
          // tune a plugin's params
          inlineStyles: { onlyMatchedOnce: false },
        },
      },
    },
    // add non-default plugins after the preset
    'prefixIds',
    'removeDimensions',
  ],
};
```

Custom pipeline (skip `preset-default` entirely — uncommon, but possible):

```js
export default {
  plugins: [
    'removeDoctype',
    'removeComments',
    'cleanupIds',
    { name: 'prefixIds', params: { prefix: 'icon' } },
    'sortAttrs',
  ],
};
```

`.cjs` is supported if the surrounding project is CommonJS; prefer `.mjs` in new code.

## Gotchas

- **`removeViewBox` is the #1 footgun.** Off by default for good reason. If a user reports an SVG that "won't scale" after optimization, this is the first thing to check.
- **`cleanupIds` collides across inlined SVGs.** Two SVGs both shrunk to use `id="a"` will overwrite each other when placed in the same HTML doc. Use `prefixIds`, or disable `cleanupIds`, or both.
- **Missing config files fall back silently.** If a `--config` path is wrong or `svgo.config.mjs` isn't found, SVGO uses `preset-default` without warning. Confirm the config actually loaded by changing one observable thing (e.g., `--pretty` via config) and checking output.
- **`--multipass` is meaningfully slower.** It re-runs the pipeline until output is stable, often 2–4 passes. Worth it for committed assets; usually overkill in dev loops.
- **Precision over-rounding distorts paths.** `-p 0` or `-p 1` is too aggressive for most icons; `-p 3` is the safe default that plugins use internally. Lowering `-p` overrides every plugin's own precision.
- **`-f` overwrites the source folder by default.** Always pass `-o` when using `-f` unless you mean to rewrite in place.
- **`--exclude` is regex, not glob.** `--exclude 'icon-.*\.svg$'` works; `--exclude 'icon-*.svg'` does not.
- **v2→v3 rename:** `cleanupIDs` (uppercase D) → `cleanupIds`. Old configs and old plugin names break silently on newer SVGO.

## Programmatic use

When optimizing inside a build script or test, use the Node API rather than shelling out:

```js
import { optimize } from 'svgo';

const result = optimize(svgString, {
  path: 'icons/foo.svg', // helps some plugins (e.g., prefixIds) generate stable prefixes
  multipass: true,
  plugins: [
    {
      name: 'preset-default',
      params: { overrides: { removeViewBox: false } },
    },
    'prefixIds',
  ],
});

const optimized = result.data;
```

For the full API surface — `optimize()` options, `loadConfig()`, error shape, types — see `references/programmatic-api.md`.
