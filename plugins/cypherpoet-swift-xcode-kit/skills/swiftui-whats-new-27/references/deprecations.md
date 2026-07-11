# Deprecations
**SDK Version:** 27.0 and later

APIs hard-deprecated in SDK 27.0. Soft-deprecated APIs are covered by the `swiftui-specialist` skill's `soft-deprecated-apis.md` reference.

## `View.statusBarHidden(_:)` → `toolbarVisibility(_:for:)` (remove on visionOS)

**Platforms:** iOS, iPadOS, Mac Catalyst, visionOS

**Issue:**
`statusBarHidden(_:)` is hard-deprecated at version 27.0 on every platform that has it. On iOS, iPadOS, and Mac Catalyst the warning is:

```
'statusBarHidden' was deprecated in iOS 27.0: Use .toolbarVisibility(_, for: .statusBar) instead
```

On visionOS the warning is `'statusBarHidden' was deprecated in visionOS 27.0: Has no effect on visionOS`.

**Before:**
```swift
struct PlayerView: View {
    var body: some View {
        ZStack {
            Color.black
            Text("Now Playing")
        }
        .statusBarHidden(true)
    }
}
```

**Fix (iOS / iPadOS / Mac Catalyst):**
Replace with `toolbarVisibility(_:for:)` targeting the status bar (`ToolbarPlacement.statusBar` is new in SDK 27):

```swift
struct PlayerView: View {
    var body: some View {
        ZStack {
            Color.black
            Text("Now Playing")
        }
        .toolbarVisibility(.hidden, for: .statusBar)
    }
}
```

**Fix (visionOS):**
Remove the call entirely — it has no effect on visionOS:

```swift
struct ImmersiveView: View {
    var body: some View {
        ZStack {
            Color.black
            Text("Immersive Content")
        }
    }
}
```

**Reason:**
Status-bar visibility now routes through the unified toolbar-visibility API on iOS-family platforms. visionOS does not have a status bar in the iOS sense, so there the modifier was always a no-op and the deprecation surfaces it so cross-platform code can be cleaned up.
