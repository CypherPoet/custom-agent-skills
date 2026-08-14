# Platform — visionOS

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG platform pages: Designing for visionOS, Spatial layout, Immersive experiences, Ornaments.

### Designing for visionOS
*Last changed: 2024-02*

**Purpose:** Apps run in an infinite 3D space where people engage with content while staying connected to their real surroundings.

**Best practices:**
- **Space.** Place virtual content — windows, volumes, 3D objects — on a limitless canvas; let people open, close, and relocate windows freely.
- **Immersion.** Default launch is the *Shared Space* (multiple apps side-by-side); apps can transition to a *Full Space* (the only app running) for deeper immersion. Find the *minimum* immersion that suits each moment — not every moment needs to be fully immersive.
- **Passthrough.** Live video from external cameras keeps people aware of surroundings; people control the amount with the Digital Crown.
- **Input (eyes + hands).** People mostly look at an object (eyes) and make an *indirect* gesture like a tap to activate it; *direct* gestures (touching with a finger) are also supported. Prefer indirect so hands can rest in the lap or at the sides.
- **Ergonomics.** The system places content relative to the wearer's head regardless of height or posture (sitting, standing, lying down). Bring content to people rather than making them move; let them stay at rest.
- **Windows.** Prefer standard windows (planes in space with familiar controls) for contained, UI-centric tasks; dynamic scaling keeps content legible near or far.
- **Comfort.** Keep content in the field of view, positioned relative to the head; avoid head-anchored content. Avoid overwhelming, jarring, or too-fast motion, or motion without a stationary frame of reference. Keep direct-gesture targets close and short-lived. Avoid encouraging movement in fully immersive experiences.
- **Audio.** Spatial Audio models the room's acoustics so audio sounds natural; with permission it can be fine-tuned to surroundings.
- **Sharing.** Use SharePlay so participants appear as *spatial Personas*, making it feel like everyone shares one space.
- **Accessibility.** Supports VoiceOver, Switch Control, Dwell Control, Guided Access, Head Pointer, and more; system components are accessible by default.

### Spatial layout
*Last changed: 2024-03*

**Purpose:** Place content on the infinite canvas comfortably, using field of view, depth, and scale to make 2D and 3D content feel natural.

**Best practices:**
- **Field of view.** Center important content; the system launches apps directly in front of people. Avoid distracting motion or bright, high-contrast objects in the periphery.
- **Head anchoring.** Anchor content in the person's *space*, not to their head — head-anchored content feels confining and reduces the apparent stability of surroundings.
- **Depth.** Add small amounts of depth throughout (even in 2D windows) to look natural; the system applies color temperature, reflections, and shadow automatically. Use depth to communicate hierarchy (a sheet comes forward as its window recedes along z). Avoid depth on text (hovering text is hard to read). Make depth add value — don't overuse it; refocusing across many depths is tiring. Use volumes (RealityKit) for content needing real 3D depth.
- **Scale.** *Dynamic scale* keeps interactive content legible and the same apparent size at any distance (the system grows a window as it recedes). *Fixed scale* keeps real size constant, so objects shrink with distance like physical ones — reserve it for noninteractive objects that must look life-size. A point is defined as an *angle* in visionOS (not pixels).
- **Gestures.** Prioritize standard *indirect* gestures (hand can stay down); reserve *direct* gestures for nearby objects inviting brief close inspection.
- **Recentering.** People press the Digital Crown to recenter windows; the app needs to do nothing to support this.
- **Spacing.** Leave room around interactive components so the hover effect doesn't crowd neighbors; don't let controls overlap other interactive elements.
- **Floor.** Place large immersive content extending up from a flat horizontal plane aligned with the floor.
- **Stationary use.** Let people use the app with minimal or no physical movement unless movement is essential.

**Specs:**

| Item | Value |
| --- | --- |
| Field-of-view reference rings | 30°, 60°, 90° (concentric, from straight ahead) |
| Button spacing (center-to-center) | ≥ 60 pt |
| Gap between adjacent buttons | ≥ 16 pt |

### Immersive experiences
*Last changed: 2025-06*

**Purpose:** Extend beyond windows and volumes by immersing people in content, choosing the level that fits each moment.

**Best practices:**
- **Spaces.** Choose the Shared Space (runs alongside other apps, easy switching) or a Full Space (runs alone). Transition fluidly between them at any time.
- **Immersion styles.** Four levels: dimmed/tinted passthrough (bring attention without hiding others); `mixed` (blend content with passthrough, no boundary — content goes semi-opaque as people near physical objects); `progressive` (custom environment partially replaces passthrough, Digital Crown adjusts amount); `full` (360° environment fully replaces passthrough). Prefer launching in the Shared Space or `mixed`, letting people choose to increase immersion.
- **Passthrough + Digital Crown.** People press-and-hold to recenter, or double-click to briefly hide content and reveal surroundings. The system dims content briefly when someone nears a physical object in `mixed`.
- **Reserve immersion for meaningful moments.** Not every task benefits from immersion, and not every immersive task needs to be full. Design immersion around the unique content.
- **Tint.** Prefer subtle passthrough tints (visionOS 2+); avoid bright or dramatic tints that distract and reduce immersion.
- **Comfort.** Keep 3D content within the field of view even though it can go anywhere in a Full Space. Choose an immersion style matching the movements people will make; avoid `progressive`/`full` (or transition back to `mixed`) if people might cross the ~1.5 m boundary. Don't encourage movement — let people pull objects closer rather than walking to them. In `mixed`, don't obscure too much passthrough (switch to `full`/`progressive` if objects would block the view).
- **Transitions.** Make transitions smooth and predictable so people can visually track changes; avoid sudden, jarring shifts. Let people choose when to enter or exit deeper immersion via a clear in-app control (don't require system controls).
- **Exit controls.** Clarify whether an exit control returns to a less-immersive context or quits the experience; offer a way to pause or save before quitting.
- **Virtual hands.** Match the viewer's hand positions and gestures; avoid oversized hands that block content or feel too close to the face. On hand-tracking loss, fade virtual hands out and reveal real hands; fade back in when data returns.
- **Custom environments.** Minimize distracting content and movement, especially near the field-of-view edges. Create expansive (not claustrophobic) environments. Use Spatial Audio for atmosphere (avoid repetitive looping; lower or stop it if other audio plays). Avoid flat 360° images (no sense of scale) — prefer object meshes with lighting and shaders. Always provide a ground-plane mesh so people feel grounded.
- **ARKit.** Adopt ARKit to blend custom content with surroundings or use hand positions; request permission for sensitive data.

**Specs:**

| Item | Value |
| --- | --- |
| Immersion levels | dimmed/tinted passthrough, `mixed`, `progressive`, `full` |
| Comfort boundary (`progressive` / `full`) | ~1.5 m from initial head position |
| `progressive` default immersion range | 120°–360° (custom range optional) |
| `full` environment coverage | 360° (replaces passthrough entirely) |

### Ornaments
*Last changed: 2024-02*

**Purpose:** A floating panel of controls or information tied to a window, presented without crowding or obscuring the window's contents.

**Best practices:**
- **Placement.** An ornament floats parallel to its window and slightly in front along the z-axis; it moves with the window and keeps its relative position. It can sit on any edge and hold buttons, segmented controls, and other views; scrolling the window doesn't change it.
- **Use cases.** Use an ornament to keep frequently needed controls in a consistent, predictable location (e.g. Now Playing controls). Keep it visible in most cases; hiding it can make sense when people dive into content (watching video, viewing a photo).
- **Multiple ornaments.** Prioritize the window's overall visual balance; constrain the count to avoid added visual weight. Relocate a removed ornament's elements into the main window.
- **Width.** Keep an ornament's width the same as or narrower than its window so it doesn't interfere with a tab bar or other side content.
- **Borderless buttons.** The ornament's background is glass by default, so on-background buttons often need no border; the system applies the hover effect on look.
- **Toolbars and tab bars.** In visionOS these automatically appear as ornaments — use the system-provided components; reach for a custom ornament only for custom components.
