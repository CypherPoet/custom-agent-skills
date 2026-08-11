# Mobile Support, Platform Gates, Network, and Load Time

Obsidian runs on desktop (Electron) and mobile (Capacitor). Mobile has no Node.js, no Electron, an older JS engine floor, and a different filesystem adapter — and the directory requires you to either support it or declare you don't.

## The Platform Decision

- Plugin uses Node.js or Electron APIs anywhere → `"isDesktopOnly": true` in the manifest. Non-negotiable; the linter flags Node imports (`no-nodejs-modules`).
- Plugin can gate the desktop-only parts → keep `isDesktopOnly: false` and branch:

```ts
import { Platform } from 'obsidian';

if (Platform.isDesktopApp) {
  const { shell } = require('electron');   // runtime require, inside the gate
}
```

`Platform` flags: `isDesktopApp`, `isMobileApp`, `isIosApp`, `isAndroidApp`, `isDesktop`, `isMobile`. Detect platform **only** via `Platform` — never `navigator.userAgent` sniffing (`platform` rule).

## Mobile Landmines

| Desktop habit | Mobile reality |
|---|---|
| `fetch` / `axios` / Node `http` | CORS and platform issues — use **`requestUrl`** from `'obsidian'` for all HTTP |
| Regex lookbehind `(?<=…)` | Unsupported below iOS 16.4 — crashes at parse time (`regex-lookbehind` rule) |
| `vault.adapter instanceof FileSystemAdapter` | Mobile adapter is `CapacitorAdapter` — `instanceof`-gate before adapter-specific calls |
| Node crypto / fs | Web APIs: `SubtleCrypto`, the Vault API |
| Tiny click targets | Touch targets ≥ 44×44px |

Test without hardware: run `this.app.emulateMobile(true)` in the dev console (persists until toggled back with `false`).

## Network Use Is a Policy Surface

Any network access must be disclosed in the README (which remote services, and why) — a developer-policy requirement, not a style point. Telemetry from the client is banned outright; server-side telemetry requires a linked privacy policy. See [`submission-and-release.md`](submission-and-release.md).

## Load-Time Optimization

Obsidian loads all enabled plugins before the app is interactive — your `onload` is part of every startup. From the official "Optimize plugin load time" guide:

1. **Ship minified production builds** (`npm run build`; the sample config minifies and drops sourcemaps).
2. **`onload` = registrations only.** No fetching, no filesystem scans, no UI building, no heavy imports at module top level.
3. **Defer to `onLayoutReady`:** `this.app.workspace.onLayoutReady(() => { /* startup work */ })`. This is also where `vault.on('create')` belongs — it fires for every file during vault indexing.
4. **Keep view constructors light** — deferred views (1.7.2+) only pay off if constructing your view is cheap.
5. **Debounce** handlers for bursty events (`vault.on('modify')` during sync, `metadataCache.on('changed')` during bulk edits).
6. **Measure:** Settings → General → Advanced → stopwatch icon shows per-plugin load times.
7. Timers in pop-out-aware code: `activeWindow`-scoped, not bare globals ([`lifecycle-and-memory.md`](lifecycle-and-memory.md)).

Dependency mindset from the self-critique checklist: *less is safer* — every bundled dependency is startup weight and supply-chain surface. The app already provides `moment` (import it from `'obsidian'`), Lucide icons, and CM6.
