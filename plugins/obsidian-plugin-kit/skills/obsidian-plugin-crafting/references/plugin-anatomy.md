# Plugin Anatomy: Manifest, Tooling, and the Dev Loop

What a plugin physically is, the exact `manifest.json` rules the submission bot enforces, and the sample-plugin build setup.

## The Three Loaded Files

Obsidian loads a plugin from `<vault>/.obsidian/plugins/<plugin-id>/`:

| File | Role |
|---|---|
| `main.js` | The bundled plugin code (CommonJS). Built from TypeScript — never hand-written, never committed to git. |
| `manifest.json` | Identity and compatibility metadata (below). |
| `styles.css` | Optional stylesheet, auto-loaded with the plugin. |

Everything else (`src/`, `esbuild.config.mjs`, `node_modules`) is build-time only. For local development the plugin folder name must match the manifest `id`, or callbacks like `onExternalSettingsChange` won't fire.

## manifest.json Fields

Required for plugins: `id`, `name`, `version`, `minAppVersion`, `description`, `author`, `isDesktopOnly`. Optional: `authorUrl`, `fundingUrl` (a URL string, or an object mapping labels to URLs — only for actual financial support links).

Field rules (enforced at submission; several also break local dev):

- **`id`** — lowercase letters and hyphens only; must not end with `plugin`; must not contain `obsidian`; unique across the directory; **never changes after release**.
- **`name`** — short, descriptive, Basic Latin characters; no punctuation except hyphens, `+`, and parentheses; no emoji; must not contain "Obsidian" or variations ("Obsi-", "-sidian"); must not contain the word "Plugin"; must not reuse core plugin/feature names (e.g. "Live Preview", "Bases"). Names *can* change post-publish via a manifest edit.
- **`version`** — SemVer `x.y.z`, no `v` prefix. Must exactly match the GitHub release tag.
- **`minAppVersion`** — the minimum Obsidian app version that actually runs the plugin. Be honest; if unsure, use the latest stable build number. The linter's `no-unsupported-api` rule flags API calls newer than this value.
- **`description`** — max 250 characters, ends with `.`, starts as an action statement ("Translate selected text into…"), no emoji or special characters, never "This is a plugin…", correct trademark capitalization.
- **`isDesktopOnly`** — must be `true` if any Node.js or Electron API is used (see [`mobile-and-performance.md`](mobile-and-performance.md)).

## versions.json

A repo-root file mapping plugin version → `minAppVersion`:

```json
{ "1.0.0": "1.5.0", "1.2.0": "1.7.2" }
```

Obsidian consults it when a user's app is older than the current release's `minAppVersion`, so they get the newest *compatible* older release. Only add an entry when `minAppVersion` changes. The sample plugin's `version-bump.mjs` maintains it automatically.

## Sample-Plugin Tooling (the canonical scaffold)

[obsidianmd/obsidian-sample-plugin](https://github.com/obsidianmd/obsidian-sample-plugin) is a GitHub template repo. Its current shape:

- **Source layout:** `src/main.ts`, `src/settings.ts`; `"type": "module"`; strict tsconfig (`strict`, `noUncheckedIndexedAccess`, `isolatedModules`, target ES2021 + DOM).
- **esbuild** (`esbuild.config.mjs`): entry `src/main.ts` → `main.js`, `bundle: true`, `format: 'cjs'`, `target: 'es2021'`; inline sourcemaps in dev, minified with no sourcemap in production. Externals: `obsidian`, `electron`, all `@codemirror/*`, all `@lezer/*`, and Node builtins — these are provided by the app and must never be bundled.
- **npm scripts:**
  - `dev` — esbuild watch build.
  - `build` — `tsc -noEmit -skipLibCheck` (type check) then production esbuild.
  - `version` — `node version-bump.mjs && git add manifest.json versions.json`, so `npm version patch|minor|major` bumps the manifest, maintains `versions.json`, and stages both.
  - `lint` — `eslint .` with `...obsidianmd.configs.recommended` (see [`linting-and-review.md`](linting-and-review.md)).
- **Pinned devDependencies** in the 2026-07-23 sample-plugin snapshot: `esbuild 0.25.5`, `eslint ^9.39.4`, `eslint-plugin-obsidianmd ^0.4.0`, `typescript ^5.8.3`, `typescript-eslint ^8.59.1`, `obsidian: "latest"`.

Keep `main.ts` lifecycle-only (registrations and wiring); real logic lives in modules it imports. Never commit `main.js` or `node_modules`; do commit a lockfile.

## The Dev Loop

1. **Dedicated dev vault** — never develop in a vault you care about.
2. Clone the template into `<dev-vault>/.obsidian/plugins/<plugin-id>/`, `npm install`, `npm run dev`.
3. Enable the plugin: Settings → Community plugins (turn off Restricted mode in the dev vault).
4. After each change, reload: toggle the plugin off/on, or run the "Reload app without saving" command. The community [Hot-Reload plugin](https://github.com/pjeby/hot-reload) watches `main.js`/`styles.css` and reloads for you — the standard quality-of-life install for plugin dev.
5. Debug with the developer console (Ctrl/Cmd-Shift-I). To emulate mobile: `this.app.emulateMobile(true)` from the console.

If the official Obsidian CLI is installed, it can drive this loop headlessly — reloading plugins, evaluating JS in the app, and capturing errors — which is especially useful for agent-driven iteration. Treat it as an accelerator, not a dependency.

## Framework Notes

React and Svelte both work (official guides exist for each): mount into a view's `contentEl`, unmount in `onClose`/`onunload`. The constraint is the same as everywhere else — whatever you mount, you must tear down.
