# Cross-Fade Sheet Transitions

Use `NavigationTransition.crossFade` when a presented sheet should appear by fading in over the
content beneath it.

Apple's SwiftUI updates page names `NavigationTransition.crossFade` and this sheet behavior, but it
does not state availability or show a call site there. Before emitting code, open the symbol
documentation in the target Xcode SDK and use its declaration as the authority for the exact
modifier overload and any availability gate.

**Source:** <https://developer.apple.com/documentation/updates/swiftui>
