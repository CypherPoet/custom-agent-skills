# SVGO CLI flags — full reference

Verified against SVGO 4.0.1. Run `npx svgo --help` to confirm against the version installed in any given project.

## Input / output

### `-i, --input <files…>`

Files to optimize. Multiple paths are accepted. Use `-` to read a single SVG from stdin:

```bash
cat icon.svg | svgo -i - -o -
```

Positional arguments are treated the same as `-i`:

```bash
svgo a.svg b.svg c.svg          # equivalent to: svgo -i a.svg b.svg c.svg
```

### `-s, --string <svg>`

Optimize an SVG passed inline as a shell argument. Quote carefully; the SVG must be a single argv entry.

```bash
svgo -s '<svg xmlns="http://www.w3.org/2000/svg"><circle r="5"/></svg>' -o out.svg
```

### `-f, --folder <dir>`

Treat `<dir>` as the input. SVGO finds every `*.svg` directly inside it (not recursive unless `-r` is passed). Without `-o`, the files are **rewritten in place**.

### `-o, --output <paths…>`

Output destination. Behavior depends on input mode:

- **Single file in:** `-o file.svg` writes to that path. `-o -` writes to stdout.
- **Multiple files in:** `-o` accepts the same number of paths, positionally matched to inputs.
- **Folder in:** `-o <dir>` writes the optimized tree to a parallel directory. SVGO creates the directory if it doesn't exist.

If `-o` is omitted, SVGO overwrites each input in place.

### `-r, --recursive`

Recurse into subdirectories under `--folder`. No effect without `-f`. With `-f` and `-o`, SVGO mirrors the directory tree under the output path.

### `--exclude <patterns…>`

Skip files matching one or more **regular expressions** (not glob patterns). Only meaningful with `--folder`.

```bash
svgo -rf src/icons --exclude '\.tmp\.svg$' --exclude '^_'
```

Patterns are matched against file paths as SVGO sees them.

## Optimization tuning

### `-p, --precision <integer>`

Number of digits after the decimal point. Plugins that accept a precision parameter (`convertPathData`, `cleanupNumericValues`, etc.) honor this override. Range is 0–20; sensible values are 1–4. Default behavior (no `-p`) varies per plugin but is typically 3.

`-p 0` and `-p 1` are aggressive — paths visibly distort, especially on small or curved geometry. Avoid below 2 unless the output is being inspected.

### `--multipass`

Re-runs the entire pipeline until output is byte-stable. Each plugin can expose optimizations the next iteration can shrink further. Typically converges in 2–4 passes. Cost is roughly N× a single pass.

Use for committed assets; skip in fast dev loops.

### `--config <path>`

Load a custom config from the given path. `.js`, `.mjs`, `.cjs` are supported. Path is resolved relative to the current working directory.

If the path doesn't exist or fails to load, SVGO falls back to `preset-default` silently. Always verify the config loaded by checking an observable side effect.

## Output formatting

### `--pretty`

Pretty-print the output (newlines and indentation). Increases file size; useful when committing SVGs to source control where you want readable diffs.

### `--indent <integer>`

Spaces per indent level when `--pretty` is on. Default is 4.

### `--eol <lf | crlf>`

Force line endings. Without this flag, SVGO uses the platform default — be explicit in cross-platform projects.

### `--final-newline`

Append a trailing newline to the output. Off by default; some linters and POSIX tooling expect a trailing newline.

## Data URI mode

### `--datauri <format>`

Emit the optimized SVG as a data URI. Three formats:

- `base64` — `data:image/svg+xml;base64,…`. Largest of the three but bypasses URL-encoding issues; safest for CSS `background-image`.
- `enc` — `data:image/svg+xml,…` with URI-encoded payload. Smaller than base64 for most SVGs.
- `unenc` — raw SVG inline as the data URI body. Smallest, but the SVG must not contain characters that conflict with the surrounding context (CSS, attribute values).

Output goes to stdout unless `-o` is set. With `-o`, the file written is the data URI string, not an SVG.

## Other

### `--show-plugins`

Print every plugin SVGO knows about, with a one-line description and `(preset-default)` annotation for default-on plugins. Exits without doing any optimization.

### `-q, --quiet`

Suppress per-file status messages. Errors still print.

### `--no-color`

Disable ANSI color in stdout/stderr. Useful in CI logs.

### `-v, --version`

Print the SVGO version and exit.

### `-h, --help`

Print help and exit.

## Notes on flag combinations

- `-f` without `-o` rewrites the source folder.
- `-r` without `-f` does nothing — recursion requires folder mode.
- `--exclude` without `-f` does nothing.
- `-p` overrides plugin-level precision settings everywhere.
- `-i -` (stdin) cannot be combined with `-f` (folder).
- `--datauri` ignores `--pretty` (data URIs are always single-line).
