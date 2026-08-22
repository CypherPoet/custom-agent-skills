# Gesture Input Sources

SwiftUI gesture initializers can limit which input sources they recognize. Apple names direct and
indirect touches, Apple Pencil, and pointer input as examples and routes the source set through
`GestureInputKinds`.

The update applies to initializers for these gestures:

- `DragGesture`
- `LongPressGesture`
- `MagnifyGesture`
- `RotateGesture`
- `RotateGesture3D`
- `SpatialEventGesture`
- `SpatialTapGesture`
- `TapGesture`
- `WindowDragGesture`

Do not guess enum case spellings or availability from the descriptive labels above: Apple's
SwiftUI updates page does not publish those declarations. Open `GestureInputKinds` and the chosen
gesture initializer in the target Xcode SDK before emitting code.

**Source:** <https://developer.apple.com/documentation/updates/swiftui>
