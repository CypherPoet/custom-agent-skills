# Arrangement Views

`ArrangementView` presents primary and secondary content in an adaptive layout that responds to its
environment. Apply `arrangementViewStyle(_:)` to choose how the two pieces of content relate.

## Built-In Styles

- The `split` style places the primary and secondary views side by side. Restrict the axes it can
  use with `SplitArrangementViewStyle.axes(_:)`.
- The `overlay` style layers the primary view over the secondary view. Restrict the axes on which
  it can transition to a side-by-side layout with `OverlayArrangementViewStyle.axes(_:)`, and use
  `overlayArrangementEdge(_:)` to anchor the overlaid content to a horizontal or vertical edge.

Inside arranged content, read `splitArrangementAxis` from the environment to discover the active
split axis, or read `overlayArrangementZIndex` to discover a view's position in the overlay's
z-order.

## Split Sizing

Express a preferred ratio between the related views with `splitArrangementLayoutRatio(_:)`. Use
`splitArrangementLayoutRatio(minHorizontal:idealHorizontal:maxHorizontal:minVertical:idealVertical:maxVertical:)`
when each axis needs its own constrained range.

Use `splitArrangementLayoutSize(minWidth:idealWidth:maxWidth:minHeight:idealHeight:maxHeight:)` for
absolute size constraints, or `splitArrangementFixedLayoutSize(horizontal:vertical:)` when a view
should prefer its own ideal size on an axis.

## Custom Styles

Create a custom style by conforming to `ArrangementViewStyle` and implementing
`makeBody(configuration:)`. The configuration exposes the arrangement's `primary` and `secondary`
content.

Apple's SwiftUI updates page names these APIs but doesn't publish complete declarations or
availability there. Before emitting code, inspect the selected API in the target Xcode SDK and use
that declaration for initializer labels, closure shapes, supported platforms, and availability
gates.

**Source:** <https://developer.apple.com/documentation/updates/swiftui>
