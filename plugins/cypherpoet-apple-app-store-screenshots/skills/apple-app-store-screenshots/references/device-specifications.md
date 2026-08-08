# Apple App Store screenshot specifications

Exact pixel dimensions for every device class App Store Connect accepts, plus the required-size
and auto-scaling rules. This is the exhaustive table; the durable decision rules live in
[SKILL.md](../SKILL.md).

**Source:** <https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications>
**Verified:** 2026-08-08. Apple edits this table whenever new hardware ships, so re-check the
source after each major iPhone/iPad release and re-stamp this date — don't trust a number here as
final without reconciling it.

**Contents:** [Universal rules](#universal-rules) · [iPhone](#iphone) · [iPad](#ipad) · [Mac](#mac) · [Apple TV](#apple-tv) · [Apple Vision Pro](#apple-vision-pro) · [Apple Watch](#apple-watch)

## Universal rules

- **Count:** 1–10 screenshots per device class, per localization.
- **Formats:** `.png`, `.jpg`, `.jpeg`. PNG is the safe default for crisp UI text. **No alpha channel** — App Store Connect rejects screenshots with transparency, so flatten to opaque RGB before upload (`magick in.png -alpha remove -alpha off out.png`). Export **sRGB**; a wide-gamut/Display-P3 file can shift on the store page.
- **Landscape** sizes are the portrait sizes transposed (swap width × height). Tables list portrait.
- **Auto-scaling:** App Store Connect generates the smaller classes from the largest one you
  upload, so you rarely produce every size. Each platform's fallback chain is in the "If omitted"
  column. The lone exception is **Apple Watch**, which does not auto-scale.

## iPhone

The **6.9" display is the canonical size**: upload it and every smaller iPhone class is generated
for you. Apple's literal requirement reads "6.5" is required if the app runs on iPhone and 6.9"
screenshots aren't provided" — so you satisfy the iPhone requirement by providing **either 6.9"
or 6.5"**, and 6.9" is the better choice because everything cascades from it.

| Display class | Accepted portrait sizes (px) | Example devices | If omitted |
|---|---|---|---|
| **6.9"** (required\*) | 1290×2796 · 1320×2868 · 1260×2736 | iPhone 17 Pro Max, 16 Pro Max, iPhone Air, 15 Pro Max, 16/15 Plus, 14 Pro Max | — (canonical) |
| **6.5"** (required\*) | 1284×2778 · 1242×2688 | iPhone 14 Plus, 13/12/11 Pro Max, 11, XS Max, XR | scaled from 6.9" |
| 6.3" | 1179×2556 · 1206×2622 | iPhone 17, 17 Pro, 16, 16 Pro, 15, 15 Pro, 14 Pro | scaled from 6.5" |
| 6.1" | 1170×2532 · 1125×2436 · 1080×2340 | iPhone 17e, 16e, 14, 13/13 Pro, 13 mini, 12/12 Pro, 12 mini, 11 Pro, XS, X | scaled from 6.5" |
| 5.5" | 1242×2208 | iPhone 8/7/6S/6 Plus | scaled from 6.1" |
| 4.7" | 750×1334 | iPhone SE (3rd/2nd gen), 8, 7, 6S, 6 | scaled from 5.5" |
| 4" | 640×1096 (no status bar) · 640×1136 (with status bar) | iPhone SE (1st gen), 5S, 5C, 5 | scaled from 4.7" |
| 3.5" | 640×920 (no status bar) · 640×960 (with status bar) | iPhone 4S, 4 | scaled from 4" |

\* Satisfy the iPhone requirement by uploading **6.9" or 6.5"**; the rest cascade by auto-scaling.

## iPad

Upload the **13" display** and the smaller iPad classes are generated for you.

| Display class | Accepted portrait sizes (px) | Example devices | If omitted |
|---|---|---|---|
| **13"** (required) | 2064×2752 · 2048×2732 | iPad Pro (M5/M4), iPad Pro (6th–3rd gen, 1st gen), iPad Air (M4/M3/M2) | — (canonical) |
| 12.9" | 2048×2732 | iPad Pro (2nd gen) | scaled from 13" |
| 11" | 1488×2266 · 1668×2420 · 1668×2388 · 1640×2360 | iPad Pro (M5/M4, 4th–1st gen), iPad Air (M4–M2, 5th/4th gen), iPad (A16, 10th gen), iPad mini (A17 Pro, 6th gen) | scaled from 13" |
| 10.5" | 1668×2224 | iPad Pro 10.5", iPad Air (3rd gen), iPad (9th–7th gen) | scaled from 12.9" |
| 9.7" | 1536×2008 (no status bar) · 1536×2048 (with) · 768×1004 (no status bar) · 768×1024 (with) | iPad Pro 9.7", iPad Air / Air 2, iPad (3rd–6th gen), iPad mini 2–5 | scaled from 10.5" |

## Mac

Required for Mac apps. One of these **16:10** sizes: **1280×800 · 1440×900 · 2560×1600 · 2880×1800**.

## Apple TV

Required for Apple TV apps: **1920×1080** or **3840×2160** (4K).

## Apple Vision Pro

Required for Apple Vision Pro apps: **3840×2160**.

## Apple Watch

Required for Apple Watch apps. Watch is the **only platform that doesn't auto-scale**: pick the
size matching your newest target and **use that same size across every localization** (Apple
enforces this for Watch).

| Size (px) | Models |
|---|---|
| 422×514 | Ultra 3 |
| 410×502 | Ultra 2, Ultra |
| 416×496 | Series 11, Series 10 |
| 396×484 | Series 9, 8, 7 |
| 368×448 | Series 6, 5, 4, SE 3, SE |
| 312×390 | Series 3 |
