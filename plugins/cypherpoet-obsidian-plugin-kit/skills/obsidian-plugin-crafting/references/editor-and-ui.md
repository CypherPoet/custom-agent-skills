# Editor API, Commands, and UI Components

## Commands

```ts
this.addCommand({
  id: 'insert-timestamp',            // NO plugin id prefix — Obsidian adds it
  name: 'Insert timestamp',          // sentence case; NO plugin name prefix
  editorCallback: (editor, view) => { … },
});
```

- Pick the right callback type — reviewers check this:
  - `callback` — always executable.
  - `checkCallback(checking)` — conditionally available; runs twice (once with `checking: true` to ask "should this appear?", once to execute).
  - `editorCallback(editor, view)` / `editorCheckCallback` — needs an active editor; receives it directly.
- **No default hotkeys** (`hotkeys:` left unset) — collisions with user/app bindings are a rejection reason. `Mod` = Ctrl/Cmd if you document suggested bindings.
- Command `id` and `name` are auto-prefixed with your plugin's id/name — including them yourself produces "MyPlugin: MyPlugin: …".

## Ribbon and Status Bar

- `this.addRibbonIcon(icon, title, cb)` — users can hide/remove ribbon icons, so every ribbon action must also exist as a command. Don't add ribbon entries that just toggle your own UI chrome.
- `this.addStatusBarItem()` returns an `HTMLElement`; **not available on mobile**. Multiple items get visual gaps — group `createEl('span')`s inside one item for tight layouts.

## Icons

Built-in icons are [Lucide](https://lucide.dev) — but only up to **v0.446.0**; newer Lucide icons don't exist in-app. `setIcon(el, 'info')` applies one. Custom icons: `addIcon('my-icon', '<path …>')` — SVG inner content (no `<svg>` wrapper) in a `0 0 100 100` viewBox; match Lucide's design language (24×24 grid, 2px strokes, round joins/caps) or the icon will look alien.

## Modals

```ts
class ConfirmModal extends Modal {
  onOpen() {
    this.setTitle('Delete note?');
    new Setting(this.contentEl)
      .addButton((btn) => btn.setButtonText('Delete').setWarning()
        .onClick(() => { …; this.close(); }));
  }
  onClose() { this.contentEl.empty(); }
}
new ConfirmModal(this.app).open();
```

- `SuggestModal<T>` — implement `getSuggestions(query)`, `renderSuggestion(item, el)`, `onChooseSuggestion(item, evt)`.
- `FuzzySuggestModal<T>` — fuzzy matching for free: `getItems()`, `getItemText(item)`, `onChooseItem(item, evt)`.
- For inline (non-modal) suggestions on a text input, use `AbstractInputSuggest` — the linter suggests it over custom dropdowns (`prefer-abstract-input-suggest`).

## Context Menus

```ts
const menu = new Menu();
menu.addItem((item) => item.setTitle('Copy path').setIcon('copy').onClick(…));
menu.showAtMouseEvent(evt);   // or showAtPosition({ x, y })
```

Extend Obsidian's own menus by hooking `workspace.on('file-menu', …)` and `workspace.on('editor-menu', …)` (wrapped in `registerEvent`).

## Editor API

`Editor` bridges CodeMirror 6 (and CM5 on legacy mobile). Get it from `editorCallback` or `this.app.workspace.activeEditor?.editor` — never assume it exists.

Core operations: `getSelection()`, `replaceSelection(text)`, `getCursor()`, `setCursor(pos)`, `getLine(n)`, `replaceRange(text, from, to)`, `getValue()`.

Use the Editor API for all edits to the **active file** — it preserves cursor, selection, and fold state, where `Vault.modify` clobbers them.

## Extending Rendering and Editing

Pick the layer by which mode you're changing:

- **Reading view** → Markdown post processors: `registerMarkdownPostProcessor(cb)`, or `registerMarkdownCodeBlockProcessor('mylang', cb)` for ```` ```mylang ```` blocks.
- **Live Preview / editing** → CM6 editor extensions via `registerEditorExtension(extension)`. The CM6 concepts (in docs under Plugins → Editor): state is immutable and changes via transactions; persistent extension state lives in a `StateField` (updated by `StateEffect`s); presentation logic lives in a `ViewPlugin` (cheap, viewport-scoped); visual changes are `Decoration`s (mark/widget/replace/line). Rule of thumb from the docs: decorations that must exist outside the viewport or change layout → build from a `StateField`; otherwise build in a `ViewPlugin` for performance.
- The raw CM6 `EditorView` is reachable as `view.editor.cm` — untyped, needs `@ts-expect-error`; use sparingly.

## DOM Construction (security-reviewed)

- ❌ `innerHTML` / `outerHTML` / `insertAdjacentHTML` — XSS surface; hard review rejection (`no-forbidden-elements`).
- ✅ Obsidian's helpers: `el.createEl('a', { text: 'Docs', cls: 'my-link', href: … })`, `createDiv()`, `createSpan()`; clear with `el.empty()`; toggle with `el.toggleClass(cls, on)`.
- ❌ Inline styles from JS (`el.style.color = …`) or injected `<style>` elements (`no-static-styles-assignment`).
- ✅ CSS classes in `styles.css`, themed with Obsidian's CSS variables (`var(--text-normal)`, `var(--background-primary)`, `var(--interactive-accent)`, …the full catalog is in the docs under Reference → CSS variables). No `!important`; avoid `:has()` (performance). This keeps the plugin working across themes without doing anything.

## UI Text Rules (human-reviewed)

- **Sentence case everywhere** ("Copy file path", not "Copy File Path") — `ui/sentence-case` auto-fixes most of it.
- Headings in settings via `new Setting(containerEl).setName('Sync').setHeading()` — never raw `<h1>`/`<h2>`.
- No "settings" in section headings; general section at top gets no heading at all.
- Accessibility is mandatory, not optional: interactive elements need keyboard reachability, ARIA labels (`setAttribute('aria-label', …)` or the `data-tooltip-position` attr for tooltips), visible `:focus-visible` states, and ≥44×44px touch targets on mobile.
