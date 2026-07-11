# Confirmation Dialog and Alert Item Binding
**SDK Version:** 27.0 and later

The APIs in this reference (the `confirmationDialog(_:item:…)` and `alert(_:item:…)` overloads) are new in SDK 27 but **back-deployed**: Apple's documentation marks them available on iOS 15 / macOS 12 / watchOS 8 / tvOS 15 / visionOS 1 (Mac Catalyst 15). Compiling them requires the SDK 27 toolchain, but they run on those earlier OS versions — no `#available(iOS 27)` runtime gate is needed. See "No availability gating needed" below.

`confirmationDialog` and `alert` gain overloads that take an `item: Binding<T?>` in place of an `isPresented: Binding<Bool>`. The dialog or alert presents while the binding holds a value, the unwrapped value is passed to the `actions` (and optional `message`) closures, and SwiftUI resets the binding to `nil` when it is dismissed. This is the presentation shape of `sheet(item:)` applied to dialogs and alerts; the earlier forms drove presentation from a separate `Bool` and read the data from a stored optional or a `presenting:` argument. `T` has no `Identifiable` requirement. When a dialog or alert acts on a specific value, such as the row a person tapped or the item pending deletion, prefer this `item:` overload over a separate `isPresented` Bool, a `presenting:` argument, or the older `Alert`-returning `alert(item:)`: one optional drives presentation and hands the value to the `actions`/`message` builders.

## Confirmation dialog from an item binding

`confirmationDialog(_:item:titleVisibility:actions:)` presents while `item` is non-nil and passes the unwrapped value to `actions`; the overload with a trailing `message:` closure receives the value as well. The title is a `LocalizedStringKey`, `Text`, or `StringProtocol`, and `titleVisibility` defaults to `.automatic`.

```swift
struct PhotoGrid: View {
    @State private var photoToDelete: Photo?

    var body: some View {
        PhotoList(deleteAction: { photoToDelete = $0 })
            .confirmationDialog("Delete photo?", item: $photoToDelete) { photo in
                Button("Delete \(photo.name)", role: .destructive) {
                    delete(photo)
                }
            } message: { photo in
                Text("\(photo.name) will be removed from all of your devices.")
            }
    }
}
```

**Availability:** iOS 15, macOS 12, watchOS 8, tvOS 15, visionOS 1 (back-deployed; the SDK 27 toolchain is required to compile).

## Alert from an item binding

`alert(_:item:actions:)` presents while `item` is non-nil and passes the unwrapped value to `actions`; the overload with a trailing `message:` closure receives the value as well. Like `confirmationDialog(_:item:)`, it takes a title plus `actions` (and optional `message`) builders. For a per-item alert, this is the form to use; do not synthesize a `Binding<Bool>` and pair it with `presenting:`, and do not reach for the `Alert`-returning `alert(item:) { _ in Alert(...) }` overload.

```swift
struct FolderView: View {
    @State private var pendingRename: Folder?

    var body: some View {
        FolderList(renameAction: { pendingRename = $0 })
            .alert("Rename folder", item: $pendingRename) { folder in
                Button("Rename") { rename(folder) }
                Button("Cancel", role: .cancel) {}
            } message: { folder in
                Text("Choose a new name for \(folder.name).")
            }
    }
}
```

**Availability:** iOS 15, macOS 12, watchOS 8, tvOS 15, visionOS 1 (back-deployed; the SDK 27 toolchain is required to compile).

## No availability gating needed

The `item:` overloads are back-deployed to iOS 15 / macOS 12 / watchOS 8 / tvOS 15 / visionOS 1 — at or below the floor of every fallback you could gate to (`confirmationDialog(_:isPresented:titleVisibility:presenting:actions:)` and `alert(_:isPresented:presenting:actions:)` require iOS 16 / macOS 13). There is no OS version where an `isPresented:`/`presenting:` fallback compiles but the `item:` overload doesn't run, so do **not** wrap calls in `#available(iOS 27, *)` and do not emit a fallback branch for their sake — the gate compiles but wrongly withholds the API from users on iOS 15–26. The only requirement is building with the SDK 27 toolchain, which declares the overloads.

## Availability summary

| API | iOS | macOS | watchOS | tvOS | visionOS |
|---|---|---|---|---|---|
| `confirmationDialog(_:item:titleVisibility:actions:)` / `…actions:message:)` | 15 | 12 | 8 | 15 | 1 |
| `alert(_:item:actions:)` / `…actions:message:)` | 15 | 12 | 8 | 15 | 1 |

All rows are back-deployed SDK 27 APIs: they need the SDK 27 toolchain to compile but run on the OS versions listed.
