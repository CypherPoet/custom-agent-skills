# SVGO programmatic API

Use the Node API from `'svgo'` when optimizing inside a build script, test, or library — it's faster than spawning the CLI and gives you structured errors.

Verified against SVGO 4.0.1.

## `optimize(input, config?)`

Synchronously optimize a single SVG string. Returns `{ data: string }`.

```js
import { optimize } from 'svgo';

const result = optimize(svgString, {
  path: 'icons/foo.svg',
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

### Parameters

- **`input`** *(string, required)* — the SVG source to optimize.
- **`config`** *(object, optional)* — same shape as a config file's default export. The accepted top-level fields:

| Field | Type | Notes |
|-------|------|-------|
| `path` | `string` | Logical path of the SVG. Some plugins (notably `prefixIds`) use this to generate stable, reproducible prefixes. Pass it whenever you have it. |
| `multipass` | `boolean` | Re-run the pipeline until output is byte-stable. |
| `floatPrecision` | `number` | Decimal precision; analogous to the CLI's `-p`. |
| `plugins` | `array` | Plugin list. Same shape rules as the config file (strings, `{ name, params }` objects, custom plugin functions). |
| `js2svg` | `object` | Output-stringifier options: `{ indent, pretty, eol, finalNewline }`. |
| `datauri` | `'base64' \| 'enc' \| 'unenc'` | When set, `result.data` is a data URI string, not raw SVG. |

### Return value

```ts
{ data: string }
```

`data` is the optimized SVG (or data URI, if `datauri` was set).

### Errors

`optimize` throws on parse/serialization failure. Wrap in `try/catch` if the input may be malformed:

```js
try {
  const result = optimize(svgString, config);
  return result.data;
} catch (error) {
  // error.message describes the parse failure; line/col info varies by error
  console.error('SVGO failed to optimize:', error.message);
  throw error;
}
```

## `loadConfig(configFile?, cwd?)`

Asynchronously load an `svgo.config.{js,mjs,cjs}` and return its default export.

```js
import { loadConfig, optimize } from 'svgo';

const config = await loadConfig();             // looks for svgo.config.{mjs,js,cjs} in cwd
const config = await loadConfig('custom.mjs'); // explicit file (relative to cwd)
const config = await loadConfig(null, '/abs/project'); // search starting from a different dir

const result = optimize(svgString, config);
```

### Behavior notes

- Returns `null` if no config is found and no explicit path was given. Callers should handle the null and either fall back to `preset-default` (i.e., call `optimize` with no config) or throw a clearer error.
- Throws if an explicit `configFile` path is given but the file fails to load.
- The returned object can be passed straight into `optimize()`.

## Common patterns

### Batch a folder programmatically

```js
import { readFile, writeFile } from 'node:fs/promises';
import { glob } from 'glob';
import { optimize, loadConfig } from 'svgo';

const config = (await loadConfig()) ?? {};
const files = await glob('src/icons/**/*.svg');

await Promise.all(
  files.map(async (path) => {
    const source = await readFile(path, 'utf8');
    const { data } = optimize(source, { ...config, path });
    await writeFile(path, data);
  }),
);
```

### Emit a data URI for CSS embedding

```js
const { data } = optimize(svgString, {
  datauri: 'enc',
  plugins: [
    {
      name: 'preset-default',
      params: { overrides: { removeXMLNS: false } },
    },
  ],
});

// data === 'data:image/svg+xml,%3Csvg…'
```

(`removeXMLNS` stays off — standalone data URIs need `xmlns`.)

### Per-file plugin choices

The `path` option is more than informational. Pass it so plugins like `prefixIds` produce filename-derived prefixes that stay stable across builds:

```js
optimize(source, {
  path: 'icons/arrow-left.svg',
  plugins: ['preset-default', 'prefixIds'],
});
```

Without `path`, `prefixIds` falls back to a generic prefix and you'll see noisier diffs.

## Custom plugins

A plugin is a `{ name, fn }` object where `fn` receives the AST root and returns a visitor. The plugin authoring API is documented at https://svgo.dev/docs/plugins-api/. Custom plugins go in the same `plugins` array as built-ins:

```js
const myPlugin = {
  name: 'addBuildId',
  fn: () => ({
    element: {
      enter: (node, parentNode) => {
        if (parentNode.type === 'root' && node.name === 'svg') {
          node.attributes['data-build'] = process.env.BUILD_ID ?? 'dev';
        }
      },
    },
  }),
};

const { data } = optimize(svgString, {
  plugins: ['preset-default', myPlugin],
});
```

## Types

SVGO ships TypeScript types. Useful imports:

```ts
import type { Config, Output, PluginConfig } from 'svgo';
```

- `Config` — the options object passed to `optimize()`.
- `Output` — the return shape (`{ data: string }`).
- `PluginConfig` — entries in the `plugins` array.
