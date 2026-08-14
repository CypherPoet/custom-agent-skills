# Settings: Classic Tab, Declarative API (1.13+), and Secrets

Two generations of settings API coexist. Which you target is a `minAppVersion` decision: the declarative API requires **Obsidian 1.13.0**, which is publicly released. Check the [changelog](https://obsidian.md/changelog/) before depending on later additions.

## The Data Layer (both generations)

```ts
interface MyPluginSettings { apiEndpoint: string; showRibbon: boolean; }
const DEFAULT_SETTINGS: MyPluginSettings = { apiEndpoint: '', showRibbon: true };

async loadSettings() {
  this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
}
async saveSettings() { await this.saveData(this.settings); }
```

Note the three-argument `Object.assign({}, defaults, loaded)` — the two-argument form mutates your defaults object and the linter flags it (`object-assign`). Save on change, not on a submit button.

## Classic: Imperative `PluginSettingTab`

```ts
class MySettingTab extends PluginSettingTab {
  constructor(app: App, private plugin: MyPlugin) { super(app, plugin); }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    new Setting(containerEl)
      .setName('API endpoint')
      .setDesc('Where sync requests are sent.')
      .addText((text) => text
        .setValue(this.plugin.settings.apiEndpoint)
        .onChange(async (value) => {
          this.plugin.settings.apiEndpoint = value;
          await this.plugin.saveSettings();
        }));
  }
}
// onload: this.addSettingTab(new MySettingTab(this.app, this));
```

Control adders: `addText`, `addTextArea`, `addToggle`, `addDropdown`, `addSlider`, `addSearch`, `addMomentFormat`, `addButton`, `addExtraButton`, `addProgressBar`. Headings: `new Setting(containerEl).setName('Section').setHeading()`.

Style rules reviewers enforce: sentence case; no top-level heading; headings only when there are 2+ sections (and the general section at top stays unheaded); never the word "settings" in a heading; one control per row; `desc` kept to a sentence; avoid textareas in the main tab.

## Declarative: `getSettingDefinitions()` (1.13.0+)

Override `getSettingDefinitions()` on the setting tab and return definitions; Obsidian renders, persists (auto-`saveData`), validates, and — the headline feature — **indexes your settings into the app-wide settings search**. The linter nudges toward it (`settings-tab/prefer-setting-definitions`).

- Definition kinds: `control` (declarative one-key binding), `render` (escape hatch to a full imperative `Setting`; does *not* auto-save; may return a cleanup function), `action` (clickable row), a plain name/desc row, `type: 'group'` (heading + items; supports `search`, `extraButtons`, `cls`, `visible`), `type: 'list'` (`onDelete`, `onReorder`, `emptyState`, `addItem`), `type: 'page'` (sub-pages; sibling page names must be unique). `control`/`render`/`action` are mutually exclusive on one definition.
- Control types: `toggle`, `text`, `textarea` (`rows`), `number` (`min`/`max`/`step`), `slider` (min/max/step required, plus `displayFormat` in 1.13.1+), `dropdown` (`options` map), `file` (`filter: (file: TFile) => boolean`), `folder` (`filter`, `includeRoot`), `color` (hex), and `secret` (1.13.2+ — see [Secrets](#secrets-secretstorage)). All accept `defaultValue` and `validate` (return an error string to reject; async allowed — but it's a UI gate, not a stored-data invariant, and the typings note it's aimed at the text-bearing controls).
- Dynamic UI: `visible`/`disabled` take booleans or predicates. `this.refreshDomState()` re-evaluates predicates; `this.update()` re-runs `getSettingDefinitions()`. On 1.13+, when definitions are non-empty, `display()` is bypassed — call `update()`, never `display()` (`settings-tab/prefer-update-over-display`).
- Keep `getSettingDefinitions()` cheap — it runs on every update, plus once at registration for search indexing.
- Custom storage: override `getControlValue(key)` / `setControlValue(key, value)` (this replaces auto-save; persist yourself).
- Scope: setting *tabs* only. Modals still build `Setting`s imperatively.

### Migration Paths (from the official guide)

- **Path A — 1.13-only:** bump `minAppVersion` to `1.13.0`, move everything into `getSettingDefinitions()`, delete `display()`.
- **Path B — dual support:** keep both. 1.13+ calls `getSettingDefinitions()` and ignores `display()`; older versions call `display()`. The linter's `settings-tab/require-display` warns if `minAppVersion < 1.13.0` and `display()` is missing.

Related linter rules: `settings-tab/no-deprecated-display`, `settings-tab/no-manual-html-headings`, `settings-tab/no-problematic-settings-headings`.

## Secrets (SecretStorage)

Never store API keys in `data.json` (it syncs, and it's plain text in the vault). Use the SecretStorage API. In every form, your settings store the secret's **name**; values live in vault-keyed local storage outside the vault files.

- **In a settings tab on 1.13.2+, use the declarative `secret` control** — one definition, no component wiring:

  ```ts
  { name: 'API key', control: { type: 'secret', key: 'apiKeyName' } }
  ```

- **Imperative fallback** (below 1.13.2, or inside a modal, where definitions don't apply): `new Setting(el).addComponent((wrapper) => new SecretComponent(this.app, wrapper))`.
- Read the value anywhere with `app.secretStorage.getSecret(name)`.

Version floors come from the typings, not the prose docs: `secretStorage`/`getSecret` are `@since 1.11.4`, `addComponent` is `@since 1.11.0`, and the `secret` control is `@since 1.13.2`. So the imperative route needs `minAppVersion` ≥ **1.11.4** and the declarative one ≥ **1.13.2**. That's enforced, not advisory: `no-unsupported-api` is error-severity and flags API calls newer than your declared `minAppVersion`.
