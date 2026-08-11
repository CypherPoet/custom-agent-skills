# Vault, Files, Frontmatter, and Metadata

The file-handling APIs are layered, and review comments cluster around using a lower layer than needed. The ladder, from most to least preferred for a given job: **Editor API** (active file, preserves cursor/selection/folds) → **FileManager** (link-aware, preference-respecting operations) → **Vault** (cached, serialized file I/O) → **Adapter** (raw, last resort).

## Vault API vs Adapter API

Prefer `app.vault` over `app.vault.adapter`: the Vault API adds a caching layer (performance) and serializes operations (no racing writes). The Adapter's one legitimate niche: files hidden from the app (e.g. inside the config directory), which the Vault API can't see.

## Reading

- `vault.cachedRead(file)` — for display; fast, may lag disk by a beat.
- `vault.read(file)` — only when you'll modify and write back (read-modify-write must see current content).
- Enumerate: `vault.getMarkdownFiles()` / `vault.getFiles()`.

## Writing

- ✅ `vault.process(file, (data) => newData)` — atomic read-modify-write; the default choice.
- ❌ `read()` then `modify()` — race window between the two.
- ✅ For the **active** file, use the Editor API instead of `Vault.modify` — it preserves cursor, selection, and folds ([`editor-and-ui.md`](editor-and-ui.md)).
- Async work between read and write: `cachedRead` → do the async work → `process(file, (data) => …)` and verify inside the callback that `data` still matches what you read before applying the change.

## Deleting

✅ `app.fileManager.trashFile(file)` — respects the user's trash preference (system trash vs vault-local `.trash` vs permanent). `FileManager.promptForDeletion(file)` asks first, per user prefs. The raw `vault.delete()` (permanent) and `vault.trash()` bypass that preference — the linter warns on them (`prefer-file-manager-trash-file`).

## Finding Files and Type Narrowing

- ✅ `vault.getFileByPath(path)` / `getFolderByPath(path)` / `getAbstractFileByPath(path)`.
- ❌ Iterating `getFiles()` to find one path — the linter flags it (`vault/iterate`).
- `TAbstractFile` narrows by **`instanceof TFile` / `instanceof TFolder`** — never `as TFile` (`no-tfile-tfolder-cast`).
- User-supplied paths → `normalizePath(userInput)` before use.
- The config directory is `vault.configDir` — never the hardcoded string `.obsidian` (`hardcoded-config-path`).

## FileManager

`app.fileManager` is the "do it the way the user configured" layer:

| Method | Why it exists |
|---|---|
| `processFrontMatter(file, (fm) => { fm.key = value; })` | **The** way to touch frontmatter — atomic, parses/serializes for you. Never string-edit YAML. |
| `generateMarkdownLink(file, sourcePath, subpath?, alias?)` | Builds a link respecting the user's link format (wikilink vs markdown, relative vs absolute). |
| `renameFile(file, newPath)` | Rename/move **with link updates** across the vault. |
| `getAvailablePathForAttachment(filename)` | Where attachments should go per user settings. |
| `getNewFileParent(sourcePath)` | Where new notes should go per user settings. |
| `trashFile(file)` | See Deleting above. |

## MetadataCache

`app.metadataCache` gives parsed structure without re-reading files:

- `getFileCache(file)` / `getCache(path)` — headings, links, embeds, tags, frontmatter, sections of a markdown file.
- `getFirstLinkpathDest(linkpath, sourcePath)` — resolve a wikilink target the way Obsidian does.
- `fileToLinktext(file, sourcePath)` — the shortest unambiguous link text.
- `resolvedLinks` / `unresolvedLinks` — `Record<sourcePath, Record<targetPath, count>>` for the whole vault graph.
- Events: `changed`, `deleted`, `resolve`, `resolved`. **`changed` does not fire on rename** — hook `vault.on('rename')` for that.

## Persistence (`data.json`)

`this.loadData()` / `this.saveData(obj)` persist to `data.json` in the plugin folder — settings and state both. `onExternalSettingsChange()` (1.5.7+) tells you the file changed on disk (Obsidian Sync, git). Settings-specific patterns live in [`settings.md`](settings.md).
