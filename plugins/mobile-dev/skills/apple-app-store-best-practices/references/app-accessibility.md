# App Accessibility declarations (Accessibility Nutrition Labels)

App Store Connect has an **App Accessibility** page where you declare which accessibility features your
app supports. Those declarations render on the product page as **Accessibility Nutrition Labels** — a
checklist users (especially users who rely on these features) read before downloading.

Two things make it easy to get wrong:

- It's **metadata, not part of the build.** It lives on the app record, edits without a new binary, and
  can be updated after launch. So it's never a submission blocker — but it should still reflect the
  *shipping* build's real behavior.
- Each label is a **promise to a user who depends on it.** A wrong claim is worse than a blank one: a
  blind user who downloads on the strength of a false VoiceOver label has a worse experience than one who
  saw it undeclared. So the governing rule is **verify before you declare.**

## The rule: verify-before-declare

Only check a feature after you've confirmed it on device. Don't infer support from "we used standard
SwiftUI" — standard controls get you *most* of the way, but the labels Apple lists are specific behaviors
a real user exercises, and the gaps (an unlabeled custom control, a readout VoiceOver can't parse, motion
that ignores the setting) are exactly what the label is asking about. When unsure, leave it undeclared.

## The labels, and how to decide each (typical utility app)

The current label set (trust the live page; Apple's exact list evolves):

| Label | Decide by | Typical call |
|-------|-----------|--------------|
| **VoiceOver** | Sweep every screen with VoiceOver on: every control reachable, correctly labeled, right traits, logical order | Declare **only after** a real pass — custom readouts/controls are where it breaks |
| **Voice Control** | Controls have names Voice Control can target (follows from good accessibility labels) | Usually declarable once VoiceOver labels are right |
| **Larger Text** | Turn on the largest accessibility Dynamic Type size (AX5); reading text scales and reflows without clipping | Declare if your reading/chrome text scales (a fixed-size dense keypad alone doesn't disqualify if the readable text scales) |
| **Sufficient Contrast** | Text/controls meet WCAG AA contrast across your themes/accents | Declare if you've actually checked the ratios |
| **Differentiate Without Color** | Meaning isn't carried by color alone (states have a shape/label/icon too) | Declare if true; easy to overlook in themed UIs |
| **Reduced Motion** | With Reduce Motion on, animations rest / cross-fade instead of moving; nothing loops | Declare after verifying on device |
| **Dark Interface** | The app honors Dark Mode app-wide | **Careful**: if a dark theme is gated behind IAP or only some screens go dark, it isn't universally available — leave it undeclared rather than over-claim |
| **Captions** | Closed captions for your video/audio media | **Skip** if the app has no media |
| **Audio Descriptions** | Audio description tracks for your video | **Skip** if the app has no media |

## How to verify, concretely

- **VoiceOver** — enable it (Settings → Accessibility, or the Accessibility Shortcut) and swipe through each
  screen on device. An automated `performAccessibilityAudit()` XCUITest catches unlabeled controls and
  hit-target/contrast issues as a regression guard, but it doesn't replace the manual sweep.
- **Reduced Motion** — Settings → Accessibility → Motion → Reduce Motion, then exercise launch/boot and a
  few transitions. (For deterministic capture in the simulator there's no `simctl` toggle; set the
  `com.apple.Accessibility ReduceMotionEnabled` default.)
- **Larger Text** — set Dynamic Type to AX5 and check reading text grows/reflows without clipping.
- **Sufficient Contrast** — measure the actual foreground/background ratios against WCAG AA (4.5:1 body),
  across every theme and accent, not just the default.

Treat this page like the rest of the listing: **trust the live screen** over any fixed list here, and
declare conservatively. It's cheap to add a label later once you've verified it; it's expensive to walk
back a claim a user relied on.
