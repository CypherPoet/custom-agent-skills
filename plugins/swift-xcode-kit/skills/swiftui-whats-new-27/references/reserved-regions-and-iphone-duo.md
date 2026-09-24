# Reserved Regions and iPhone Duo

## Hardware-Reserved Regions

`ReservedRegion` describes an area that hardware reserves, such as a camera or hinge. Query the
regions that intersect a view through
`GeometryProxy.reservedRegions(kind:options:layoutDirectionBehavior:)`.

- Choose a region kind such as `.occlusion` or `.division`.
- Add `ReservedRegion.QueryOptions.includeInactive` when the layout needs regions that aren't
  currently active.
- Use a region's opaque `ReservedRegion.ID` to identify it across coordinate spaces or track it as
  the layout changes.

## Hinge State

On iPhone Duo, `onHingeChange(isEnabled:_:)` reports hinge updates through
`DeviceHingeContext`. Read the `DeviceHinge` value for the current angle and a status such as
`.closed`, `.partiallyOpen`, or `.fullyOpen`.

## Outer-Display Camera Content

`CameraCaptureAccessory` presents content on iPhone Duo's outer display while all three documented
conditions hold: the device is open, the app is in the foreground, and a camera capture session is
active.

Apple's SwiftUI updates page doesn't publish complete declarations or availability for these APIs.
Before emitting code, inspect the target Xcode SDK for the exact initializers, context properties,
supported platforms, and availability gates.

**Source:** <https://developer.apple.com/documentation/updates/swiftui>
