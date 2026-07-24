# Lifecycle, Memory Safety, Views, and Pop-Out Windows

`Plugin extends Component`. `onload()` runs when the plugin is enabled, `onunload()` when it's disabled — and every resource acquired in between must be released. Obsidian's `register*` helpers exist so that release is automatic; memory leaks here are the most common serious plugin defect, and several variants are invisible to the linter.

## The register* Helpers (auto-cleanup on unload)

| Helper | Use for |
|---|---|
| `this.registerEvent(eventRef)` | Any `.on(...)` event — `this.registerEvent(this.app.vault.on('create', cb))`. |
| `this.registerDomEvent(el, type, cb, options?)` | DOM listeners on elements you don't own — detached on unload. |
| `this.registerInterval(id)` | Timers — pass `window.setInterval(...)` (gets the right numeric type). |
| `this.register(cb)` | Arbitrary teardown callback for anything else. |

❌ `el.addEventListener(...)` / bare `setInterval(...)` in a plugin — survives unload.
✅ Route through the helpers above; then unload is provably clean.

Other lifecycle surface worth knowing: `onUserEnable()` (1.7.2+; the user explicitly enabled the plugin — the safe place to open custom views), `onExternalSettingsChange()` (1.5.7+; `data.json` changed on disk, e.g. via Sync), `removeCommand(commandId)` (1.7.2+).

## Registration Surface

All of these are `this.register…` calls in `onload`: `addCommand`, `addRibbonIcon`, `addStatusBarItem` (desktop only), `addSettingTab`, `registerView`, `registerExtensions`, `registerEditorExtension` (CM6), `registerEditorSuggest`, `registerMarkdownPostProcessor`, `registerMarkdownCodeBlockProcessor`, `registerObsidianProtocolHandler` (`obsidian://` URLs), `registerHoverLinkSource` (1.1.0+), `registerBasesView`, `registerCliHandler`.

Two non-obvious behaviors:

- `registerEditorExtension` takes an array you can mutate in place; after mutating, call `this.app.workspace.updateOptions()` to reconfigure live editors.
- `import { moment } from 'obsidian'` — the app already ships moment; bundling your own copy is a review flag.

## Custom Views: the Leak-Proof Pattern

```ts
export const VIEW_TYPE_EXAMPLE = 'example-view';

export class ExampleView extends ItemView {
  getViewType() { return VIEW_TYPE_EXAMPLE; }
  getDisplayText() { return 'Example view'; }
  async onOpen() { /* build into this.contentEl */ }
  async onClose() { /* tear down what onOpen built */ }
}

// in onload:
this.registerView(VIEW_TYPE_EXAMPLE, (leaf) => new ExampleView(leaf));
```

- ❌ **Never store the view instance on the plugin** (`this.view = new ExampleView(...)`). The factory can run multiple times, and a stored reference pins detached views in memory. The linter enforces this (`no-view-references-in-plugin`).
- ✅ Find live instances when needed: `this.app.workspace.getLeavesOfType(VIEW_TYPE_EXAMPLE)`, then `instanceof` the `.view`.
- ❌ **Don't detach your leaves in `onunload`** (`detachLeavesOfType`) — it breaks the user's layout restore when the plugin updates. The linter enforces this too (`detach-leaves`).

**Activate/reveal pattern:** reuse an existing leaf from `getLeavesOfType()`, else `getRightLeaf(false)` + `await leaf.setViewState({ type: VIEW_TYPE_EXAMPLE, active: true })`, then `workspace.revealLeaf(leaf)`.

### Deferred Views (1.7.2+)

All views start as `DeferredView` until visible — `leaf.view` may not be your class yet.

- Always `instanceof`-check `leaf.view` before using it.
- To force your instance: `await workspace.revealLeaf(leaf)`, or (advanced, without revealing) `await leaf.loadIfDeferred()` guarded by `requireApiVersion('1.7.2')`.
- Keep view constructors near-empty — construction cost defeats the deferral optimization. Build in `onOpen`.

## Workspace Model

The workspace is a tree of `WorkspaceItem`s: parent containers (`WorkspaceSplit`, `WorkspaceTabs`) holding `WorkspaceLeaf`s, in three regions (left sidebar, right sidebar, root). Leaf management: `getLeaf(true)` (new tab), `getLeftLeaf()`/`getRightLeaf()`, `createLeafInParent()`, `leaf.detach()`, `leaf.setGroup()` for linked views.

Access the active context through typed accessors, never `workspace.activeLeaf`:

- Active markdown view → `workspace.getActiveViewOfType(MarkdownView)` (null when something else is focused — handle it).
- Active editor → `workspace.activeEditor?.editor`.

Plugin-added leaves persist after the plugin is disabled; provide a way for users to close them — just not in `onunload`.

## Pop-Out Windows (desktop, 0.15.0+)

Each pop-out window has its own `window`/`document` globals, which breaks naive DOM code:

| ❌ Main-window-only | ✅ Window-aware |
|---|---|
| `document.body` | `activeDocument.body`, or `el.doc` for a specific element |
| `window.something` | `activeWindow.something`, or `el.win` |
| `x instanceof HTMLElement` | `el.instanceOf(HTMLElement)` (same for events: `evt.instanceOf(MouseEvent)`) |
| bare `setTimeout` | `window.setTimeout` via the owning window (`el.win.setTimeout`) |

React to a view migrating between windows with `HTMLElement.onWindowMigrated(cb)`.

**Linter-invisible leak:** capturing `activeDocument` once (`const doc = activeDocument`) and attaching listeners to it — the getter drifts as focus moves between windows, so your cleanup later targets a *different* document than the one you attached to. Resolve `activeDocument`/`activeWindow` at use time, and scope DOM listeners to the component that owns the element via `registerDomEvent`.

## onload Discipline

Obsidian loads every plugin before the app becomes interactive, so `onload` cost is startup cost for every user:

- `onload` = registrations only. No data fetching, no computation, no UI construction.
- Startup work → `this.app.workspace.onLayoutReady(cb)`.
- `vault.on('create')` fires once per file during vault init — register it inside `onLayoutReady`, or check `workspace.layoutReady` in the handler.
- Debounce bursty vault events. Measure with Settings → General → Advanced → the stopwatch icon (plugin load-time profiler).
