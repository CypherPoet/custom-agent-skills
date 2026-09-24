# Vertical-Axis Controls

SwiftUI can place system bars on a vertical edge when the environment calls for it. Read
`toolbarVerticalEdge` from the environment when custom bars or content must align with the edge the
system chose.

## Choose an Axis

- Apply `toolbarVerticalBehavior(_:)` to opt a view out of vertical bar content and fall back to the
  standard horizontal top and bottom toolbars.
- Apply `axisBehavior(_:)` to `ToolbarContent` or `CustomizableToolbarContent` to express where an
  item belongs. Apple's updates page names values including `.horizontalOnly` and
  `.verticalPreferred`.

## Manage Compression

Use `toolbarVerticalCompressionBehavior(_:)` to control how different bar types compress when the
system renders them together in constrained space. Apple's updates page names behaviors including
`.prefersToolbarItems` and `.prefersTabBar`.

The SwiftUI updates page doesn't list every behavior, its exact semantics, or API availability.
Before emitting code, inspect `ToolbarItemAxisBehavior`, `ToolbarVerticalCompressionBehavior`, and
the relevant modifiers in the target Xcode SDK. Don't guess additional cases from the names above.

**Source:** <https://developer.apple.com/documentation/updates/swiftui>
