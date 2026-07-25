---
name: obsidian-plugin-crafting
description: >
  Use whenever work touches an Obsidian plugin — scaffolding one, editing its
  main.ts or manifest.json, wiring the vault/editor/workspace APIs, fixing
  eslint-plugin-obsidianmd violations, or preparing it for community-directory
  submission — even when "Obsidian" is only implied by a .obsidian folder or
  vault. Covers the full scaffold-to-submission lifecycle with current API facts.
  Not for authoring notes or markdown inside a vault.
---

# Obsidian Plugin Crafting

**Verified:** 2026-07-24

*Grounded in the official [Obsidian developer docs](https://docs.obsidian.md/) (source repo fetched 2026-07-23), the [obsidian-sample-plugin](https://github.com/obsidianmd/obsidian-sample-plugin) template, and [`eslint-plugin-obsidianmd`](https://github.com/obsidianmd/eslint-plugin) v0.4.1. Structure inspired by the community [gapmiss/obsidian-plugin-skill](https://github.com/gapmiss/obsidian-plugin-skill) (MIT).*

Working knowledge for building Obsidian plugins that pass automated and human review the first time. Use it to scaffold correctly, reach for the right API instead of a workaround, and ship through the community directory — grounded in the docs above, not training-data guesses.

## Mental Model (read this first — it prevents most rejections)

- **A plugin is three files Obsidian loads from `<vault>/.obsidian/plugins/<plugin-id>/`:** `main.js` (bundled by esbuild from TypeScript), `manifest.json`, and optional `styles.css`. The `obsidian` npm package is typings only — it's an esbuild external, never bundled. Never develop in your real vault; use a dedicated dev vault.
- **Everything you register must die with the plugin.** Route every listener, interval, and event through `this.registerEvent` / `registerDomEvent` / `registerInterval` so unload cleans up. Never store view references on the plugin; find views via `getLeavesOfType()` + `instanceof`. Don't detach leaves in `onunload`.
- **`onload` runs before the app is interactive.** Registrations only; put startup work (and `vault.on('create')` handlers, which fire for every file during vault init) inside `this.app.workspace.onLayoutReady(...)`.
- **The API is `instanceof`-driven, and pop-out windows break `instanceof`.** Narrow `TAbstractFile` with `instanceof TFile` — never cast. For DOM objects that may live in another window, use `el.instanceOf(HTMLElement)`, `activeWindow`, `activeDocument`.
- **Review is automated and strict.** The linter ships 41 rules at v0.4.1; the directory bot validates your manifest; humans re-review UI text. The recurring rejections: `innerHTML`, `fetch` instead of `requestUrl`, Title Case UI text, default hotkeys, sample code left in, missing mobile gates.

## Identify the Task First

- **Start a new plugin** → [Scaffold](#core-workflows) below, then [`references/plugin-anatomy.md`](references/plugin-anatomy.md).
- **Add a feature** (command, view, settings, file ops, editor work) → the matching row in [Reference Files](#reference-files).
- **Fix lint violations / pre-submission review** → [`references/linting-and-review.md`](references/linting-and-review.md) + run the preflight script.
- **Release or submit to the community directory** → [`references/submission-and-release.md`](references/submission-and-release.md).

## Reference Files

Load only the rows the task touches — usually one or two.

| Asking about… | Read |
|---|---|
| `manifest.json` field rules, `versions.json`, folder layout, esbuild/sample-plugin tooling, the dev loop | [`references/plugin-anatomy.md`](references/plugin-anatomy.md) |
| `onload`/`onunload`, `register*` helpers, views/leaves, deferred views, pop-out windows, leak patterns the linter can't see | [`references/lifecycle-and-memory.md`](references/lifecycle-and-memory.md) |
| Vault vs Adapter, reading/writing files, `FileManager`, frontmatter, `MetadataCache`, path handling | [`references/vault-and-files.md`](references/vault-and-files.md) |
| Commands, ribbon/status bar, icons, modals, menus, the Editor API, CM6 editor extensions, DOM helpers | [`references/editor-and-ui.md`](references/editor-and-ui.md) |
| Settings tabs — classic `PluginSettingTab` and the 1.13 declarative API, migration, secrets | [`references/settings.md`](references/settings.md) |
| Mobile support, `Platform` gates, `isDesktopOnly`, `requestUrl`, load-time optimization | [`references/mobile-and-performance.md`](references/mobile-and-performance.md) |
| ESLint setup, the full rule catalog, guideline review comments, security and accessibility rules | [`references/linting-and-review.md`](references/linting-and-review.md) |
| Developer policies, submission requirements, the community.obsidian.md flow, GitHub Actions releases, beta testing | [`references/submission-and-release.md`](references/submission-and-release.md) |

## Core Workflows

### Scaffold a new plugin
1. Create a **dev vault**, then clone the [sample plugin template](https://github.com/obsidianmd/obsidian-sample-plugin) into `<dev-vault>/.obsidian/plugins/<plugin-id>/`.
2. Set `manifest.json` fields against the rules in [`plugin-anatomy.md`](references/plugin-anatomy.md) — id and name restrictions are enforced at submission, so get them right now. The dev folder name must match `id`.
3. `npm install`, then `npm run dev` (esbuild watch). Enable the plugin in Settings → Community plugins.
4. Reload after changes: toggle the plugin off/on, or install the community Hot-Reload plugin ([pjeby/hot-reload](https://github.com/pjeby/hot-reload)) to reload automatically. If the official Obsidian CLI is available, its reload/eval/logging commands make this loop faster still — use it when present, but never depend on it.
5. Before the first commit: rename the `MyPlugin`/`SampleSettingTab` placeholders and delete all sample code — leftover sample code is an automatic review flag.

### Add a feature
Map the feature to its API surface via the [reference table](#reference-files) and follow that file's patterns. Prefer the specific API over the general one (`Editor` over `Vault.modify` for the active file, `FileManager.processFrontMatter` over string-editing frontmatter, `getFileByPath` over iterating all files) — most review comments are "you used the low-level API".

### Review before submitting
1. Set up the official linter and fix its findings: [`linting-and-review.md`](references/linting-and-review.md).
2. Run the bundled preflight — `node scripts/validate-plugin.mjs <plugin-dir>` — for the manifest/`versions.json`/release checks the linter doesn't cover. Fix every ERROR; treat WARNs as review comments in waiting.
3. Walk the review checklist in [`linting-and-review.md`](references/linting-and-review.md) for what neither tool can see (UI text tone, accessibility, mobile behavior).

### Release and submit
Create a GitHub release whose **tag exactly matches `manifest.json` `version` (no `v` prefix)** with `main.js`, `manifest.json`, and `styles.css` attached, then submit once at [community.obsidian.md](https://community.obsidian.md). Automate future releases with the GitHub Actions workflow. Details, policies, and the update cycle: [`submission-and-release.md`](references/submission-and-release.md).

## Accuracy Notes

- **Obsidian 1.13 features are marked "insider build" in the docs as of the Verified date** — the declarative settings API and settings-window behavior may have since reached public release. When `minAppVersion` decisions hinge on it, check the [Obsidian changelog](https://obsidian.md/changelog/).
- **`eslint-plugin-obsidianmd` is v0.4.1 here** (npm, 2026-07-02). The rule catalog grows between minor versions — when a rule id isn't in [`linting-and-review.md`](references/linting-and-review.md), trust the installed package's README over this corpus.
- **The `obsidian` typings package is 1.13.1** (npm, 2026-06-09); the sample plugin pins `"obsidian": "latest"`.

## Primary Sources

- [Obsidian developer docs](https://docs.obsidian.md/) ([source repo](https://github.com/obsidianmd/obsidian-developer-docs)) — official; authoritative for API usage, guidelines, policies, and submission requirements.
- [obsidian-sample-plugin](https://github.com/obsidianmd/obsidian-sample-plugin) — official template; authoritative for scaffold tooling and build configuration.
- [eslint-plugin-obsidianmd on npm](https://registry.npmjs.org/eslint-plugin-obsidianmd) / [GitHub](https://github.com/obsidianmd/eslint-plugin) — official linter; authoritative for rule ids, versions, and configs.
- [obsidian on npm](https://registry.npmjs.org/obsidian) — official typings; authoritative for API-typings versions.
- [Obsidian changelog](https://obsidian.md/changelog/) — authoritative for app release status.
