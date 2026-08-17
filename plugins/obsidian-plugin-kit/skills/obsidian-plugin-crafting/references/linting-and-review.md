# Linting and Review: eslint-plugin-obsidianmd + the Human Checklist

The official linter encodes most review feedback as rules; what it can't see, human reviewers check. Work in that order: lint clean first, then walk the checklist.

## Table of Contents

| Section | Covers |
|---|---|
| [Setup](#setup) | The npm package is `eslint-plugin-obsidianmd` (repo: obsidianmd/eslint-plugin); the fetched 2026-07-23 corpus used v0.4.1 |
| [Rule Catalog (v0.4.1)](#rule-catalog-v041) | Command registration, lifecycle cleanup, type and API correctness, DOM and styling, settings tabs, UI text, manifest hygiene, and recommended severities |
| [Linter-Invisible Pitfalls](#linter-invisible-pitfalls) | Static analysis can't catch these — check them by reading the code |
| [Human Review Checklist](#human-review-checklist) | Manifest, commands, settings, cleanup, accessibility, compatibility, and release-readiness checks |

## Setup

The npm package is **`eslint-plugin-obsidianmd`** (repo: [obsidianmd/eslint-plugin](https://github.com/obsidianmd/eslint-plugin)); the fetched 2026-07-23 corpus used v0.4.1. Peer deps: `eslint >= 9.19.0`, `typescript-eslint ^8.35.1`. The sample plugin already wires it up; adding it to an older project (flat config, ESLint 9):

```js
// eslint.config.mjs
import obsidianmd from 'eslint-plugin-obsidianmd';

export default [
  ...obsidianmd.configs.recommended,
  // or recommendedWithLocalesEn to also lint sentence case in locale JSON/TS files
];
```

Run with `npx eslint .` (the sample plugin's `npm run lint`). Legacy ESLint ≤8 uses `plugin:obsidianmd/recommended`. Rules that inspect `manifest.json` need `@eslint/json` (a peer dep) so JSON files are lintable.

## Rule Catalog (v0.4.1)

Severity in the `recommended` config: ✅ error, ⚠️ warn, 🚫 off. 🔧 = auto-fixable. When a rule fires, fix the cause — don't disable the rule; reviewers see disables.

### Commands
| Rule | | Meaning |
|---|---|---|
| `commands/no-command-in-command-id` | ⚠️ | No "command" in command ids |
| `commands/no-command-in-command-name` | ⚠️ | No "command" in command names |
| `commands/no-default-hotkeys` | ⚠️ | Don't ship default hotkeys |
| `commands/no-plugin-id-in-command-id` | ⚠️ | Obsidian auto-prefixes ids |
| `commands/no-plugin-name-in-command-name` | ⚠️ | Obsidian auto-prefixes names |

### Memory and lifecycle
| Rule | | Meaning |
|---|---|---|
| `detach-leaves` | ✅🔧 | Don't `detachLeavesOfType` in `onunload` |
| `no-view-references-in-plugin` | ✅ | Don't store view instances on the plugin |
| `no-plugin-as-component` | ✅ | Don't pass the plugin as the component to `MarkdownRenderer.render` — pass an owning component (leaks otherwise) |
| `prefer-window-timers` | ⚠️🔧 | `window.setTimeout`/`setInterval`, not bare globals |

### Type safety and API correctness
| Rule | | Meaning |
|---|---|---|
| `no-tfile-tfolder-cast` | ⚠️ | `instanceof TFile`, never `as TFile` |
| `prefer-instanceof` | ⚠️🔧 | Prefer `instanceof` narrowing generally |
| `no-unsupported-api` | ✅ | Flags APIs newer than your `minAppVersion` |
| `no-global-this` | ⚠️🔧 | No `globalThis`-hung state |
| `object-assign` | ⚠️ | Two-arg `Object.assign` mutates your defaults |
| `no-nodejs-modules` | ⚠️ | Node imports break mobile — gate or go `isDesktopOnly` |
| `platform` | ✅ | Use `Platform`, not `navigator` sniffing |
| `regex-lookbehind` | ✅ | Lookbehind crashes iOS < 16.4 |
| `hardcoded-config-path` | ⚠️ | `vault.configDir`, not `".obsidian"` |
| `vault/iterate` | ⚠️🔧 | `getFileByPath`, not scanning all files |
| `prefer-file-manager-trash-file` | ⚠️ | Respect the user's trash preference |
| `prefer-abstract-input-suggest` | ⚠️ | Use the built-in suggest machinery |
| `prefer-get-language` | ⚠️ | Use `getLanguage()` for locale detection |
| `prefer-active-doc` | 🚫 | (off in recommended) pop-out-aware `activeDocument` |
| `editor-drop-paste` | ⚠️ | Use editor-level drop/paste events correctly |

### DOM and styling
| Rule | | Meaning |
|---|---|---|
| `no-forbidden-elements` | ✅ | No `innerHTML`/`outerHTML`/`insertAdjacentHTML` |
| `prefer-create-el` | ⚠️🔧 | Use `createEl` helpers |
| `no-static-styles-assignment` | ✅ | No JS inline styles — CSS classes + variables |

### Settings tabs
| Rule | | Meaning |
|---|---|---|
| `settings-tab/prefer-setting-definitions` | ⚠️ | Adopt the declarative API so settings appear in 1.13+ settings search |
| `settings-tab/require-display` | ⚠️ | Keep `display()` while `minAppVersion < 1.13.0` |
| `settings-tab/prefer-update-over-display` | ⚠️🔧 | Call `update()`, not `display()`, on 1.13+ |
| `settings-tab/no-deprecated-display` | ⚠️🔧 | Migrate deprecated display usage |
| `settings-tab/no-manual-html-headings` | ✅🔧 | `setHeading()`, not `<h2>` |
| `settings-tab/no-problematic-settings-headings` | ✅🔧 | No "settings"/redundant words in headings |

### UI text, manifest, hygiene
| Rule | | Meaning |
|---|---|---|
| `ui/sentence-case` | ⚠️🔧 | Sentence case for UI strings |
| `ui/sentence-case-json` / `ui/sentence-case-locale-module` | (locales config) 🔧 | Same, for locale files |
| `validate-manifest` | ⚠️ | Manifest field rules ([`plugin-anatomy.md`](plugin-anatomy.md)) |
| `validate-license` | ⚠️ | LICENSE present/consistent |
| `no-sample-code` | ✅🔧 | Sample-plugin leftovers |
| `sample-names` | ✅ | `MyPlugin`/`SampleSettingTab` placeholders |
| `rule-custom-message` | ✅ | (internal consistency rule) |

## Linter-Invisible Pitfalls

Static analysis can't catch these — check them by reading the code:

- **`activeDocument` drift**: capturing `activeDocument`/`activeWindow` in a variable and cleaning up later against a different window ([`lifecycle-and-memory.md`](lifecycle-and-memory.md)).
- **`onload` weight**: nothing flags a slow `onload`; profile with the stopwatch ([`mobile-and-performance.md`](mobile-and-performance.md)).
- **Race-prone writes**: `read()`+`modify()` instead of `Vault.process` ([`vault-and-files.md`](vault-and-files.md)).
- **`:has()` selectors and `!important`** in `styles.css` — performance and theme-override problems, respectively.
- **Missing README disclosures** for network/accounts/payments — a policy violation the linter never sees ([`submission-and-release.md`](submission-and-release.md)).

## Human Review Checklist

Before submitting, verify each:

1. Lint passes with zero findings — warnings included, they're tomorrow's review comments.
2. `python3 scripts/validate_plugin.py <plugin-dir>` passes — manifest, `versions.json`, release readiness. The script ships with this skill, so `scripts/` resolves against **this skill's directory**, not the plugin repo; prefix the command with it.
3. All sample code and placeholder names gone.
4. No `console.log` in the shipping path (`onload` especially); log errors only.
5. `this.app`, never the global `app`.
6. UI text: sentence case, no command/plugin-name prefixes, headings via `setHeading()`.
7. Accessibility: keyboard-only walkthrough works; interactive elements have ARIA labels; `:focus-visible` visible; touch targets ≥44×44px.
8. Mobile: tested with `emulateMobile(true)` or `isDesktopOnly: true` declared honestly.
9. Styling via CSS classes + Obsidian CSS variables; verify in light and dark themes.
10. `async`/`await` over promise chains; `const`/`let`, no `var`.
11. Every listener/interval routed through `register*` helpers; unload leaves nothing behind (toggle the plugin off and watch the console).
12. README discloses network use, accounts, payments, and any file access outside the vault.
