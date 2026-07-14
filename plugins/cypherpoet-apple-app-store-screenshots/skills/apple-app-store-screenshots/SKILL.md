---
name: apple-app-store-screenshots
description: >
  Authoritative spec and workflow for App Store screenshots and app preview
  videos across every Apple device class. Use when preparing, sizing, capturing,
  automating, localizing, or troubleshooting product-page imagery — screenshot
  dimensions ('6.9" display', 1290x2796), upload rejections, counts and formats,
  preview video specs, fastlane snapshot/frameit, or ordering a screenshot set
  for conversion — even when "screenshot" is never said but store imagery is the
  task. For review compliance and broader ASO, defer to
  apple-app-store-best-practices.
---

# Apple App Store Screenshots

App Store Connect rejects the whole listing if one screenshot is the wrong size, and the imagery is
the top conversion lever on the product page — so it's worth getting exactly right. This skill
keeps the specs current and the workflow tight.

The pixel tables drift every time Apple ships new hardware, so **lead with the durable rules below
and treat the exact numbers as a dated snapshot** — reconcile against the source before telling
anyone a dimension is final.

**Source of truth:** <https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications>
(specs here verified 2026-05-30).

## The rule that saves the most time: upload the largest, let Apple scale

You do **not** need a screenshot for every device. App Store Connect generates the smaller size
classes from the largest one you provide. Produce screenshots at the **canonical size per
platform** and the requirement is met:

| Platform | Canonical size to produce | Covers |
|---|---|---|
| iPhone | **6.9"** — 1290×2796 (also accepts 1320×2868 or 1260×2736) | every smaller iPhone class, auto-scaled |
| iPad | **13"** — 2064×2752 (also accepts 2048×2732) | every smaller iPad class, auto-scaled |
| Mac | 2880×1800 (any 16:10 size) | Mac |
| Apple TV | 3840×2160 | Apple TV |
| Apple Vision Pro | 3840×2160 | Vision Pro |
| Apple Watch | size of your newest target (e.g. 416×496) | that Watch tier only |

Two exceptions worth holding in your head: the iPhone requirement is satisfied by **6.9" or 6.5"**,
and **Apple Watch is the only platform that won't auto-scale** — it needs its own screenshots, and
one size must be reused across every localization.

The full per-class tables — alternate accepted sizes, legacy devices, the exact fallback chain — are
in **[references/device-specifications.md](references/device-specifications.md)**. Read it when you
need a number for a specific older device or are debugging a rejected upload.

## Upload rules you'll be asked about

- **Count:** 1–10 screenshots per device class, per localization. Use them — more screenshots, more
  reasons to download.
- **Formats:** `.png`, `.jpg`, `.jpeg`. PNG is the safe default for crisp UI text; skip
  transparency/alpha.
- **Localization:** screenshots are per language. A default set can stand in everywhere, but
  localized captions convert better.

## App preview videos (optional, high-converting)

Up to **3** autoplay videos per device class, **15–30 seconds**, **≤500 MB**, in H.264 or ProRes 422
(HQ). They autoplay muted in search and on the product page, so design for sound-off. Full codec,
bitrate, audio, and per-device upload-resolution tables:
**[references/app-preview-specs.md](references/app-preview-specs.md)**.

## Capturing & automating

Pixel-correct, clean-status-bar screenshots at the right sizes — by hand, or via `fastlane snapshot`
(capture across the device × locale matrix), `frameit` (device frames + caption bands), and
`deliver` (upload): **[references/capturing-screenshots.md](references/capturing-screenshots.md)**.
Reach for it whenever the user mentions fastlane, simulators, clean status bars, device frames, or
generating a localized set at scale.

## Designing the set for conversion

Ordering (the first 2–3 are what users see before scrolling), caption legibility, portrait vs
landscape, category patterns, and running an App Store Connect Product Page Optimization A/B test:
**[references/design-and-conversion.md](references/design-and-conversion.md)**.

## Boundary with apple-app-store-best-practices

This skill owns the **specs and production** of screenshots and previews. For **App Review
compliance** (e.g. screenshots must show the real app — §2.3.3), **rejection-risk audits**, and
broader **ASO/metadata** (keywords, subtitle, description), defer to the
`apple-app-store-best-practices` skill — it's the compliance-and-listing-strategy half of the same
job. (That plugin declares this one as a dependency, so both ship together.)

## Primary Sources

- [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications) — authoritative for accepted screenshot dimensions per device class.
- [App preview specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications) — authoritative for preview video specs (resolutions, duration, codecs, bitrates).
- [fastlane snapshot docs](https://docs.fastlane.tools/actions/snapshot/) — authoritative for capture-automation CLI syntax.
- [fastlane frameit docs](https://docs.fastlane.tools/actions/frameit/) — authoritative for framing CLI syntax.
- [fastlane deliver docs](https://docs.fastlane.tools/actions/deliver/) — authoritative for upload/metadata CLI syntax.
