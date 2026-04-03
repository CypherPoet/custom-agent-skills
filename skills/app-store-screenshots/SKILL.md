---
name: app-store-screenshots
description: "Apple App Store screenshot creation with exact iOS platform specs. Covers iPhone/iPad/Watch/Mac/TV/Vision Pro dimensions, gallery ordering, device mockups, and preview videos. Use for: app store optimization, ASO, ios screenshots, app store images, app mockup, device mockup, app gallery, store listing. Triggers: app store screenshots, aso, app store optimization, app preview, app listing, ios screenshots, app store images, app mockup, device mockup, app gallery, store listing"
allowed-tools: Bash(infsh *)
---

# App Store Screenshots

Create app store screenshots and preview videos via [inference.sh](https://inference.sh) CLI.

## Quick Start

> Requires inference.sh CLI (`infsh`). [Install instructions](https://raw.githubusercontent.com/inference-sh/skills/refs/heads/main/cli-install.md)

```bash
infsh login

# Generate a device mockup scene
infsh app run falai/flux-dev-lora --input '{
  "prompt": "iPhone 15 Pro showing a clean modern app interface with analytics dashboard, floating at slight angle, soft gradient background, professional product photography, subtle shadow, marketing mockup style",
  "width": 1024,
  "height": 1536
}'
```

## Platform Specifications

### Apple App Store

**Source of truth:** [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/) — Apple Developer docs

Up to **3 app previews** and **10 screenshots** per device size per localization. Formats: PNG or JPEG (no alpha). First **3 screenshots** are visible without scrolling.

#### iPhone

| Display | Portrait (px)                                 | Landscape (px)                                | Devices                                                                      | Required?                       |
| ------- | --------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------- |
| 6.9"    | 1260 x 2736 _or_ 1320 x 2868 _or_ 1290 x 2796 | 2736 x 1260 _or_ 2868 x 1320 _or_ 2796 x 1290 | iPhone Air, 17 Pro Max, 16 Pro Max, 16 Plus, 15 Pro Max, 15 Plus, 14 Pro Max | **Yes** (covers 6.5"/6.7"/6.9") |
| 6.5"    | 1284 x 2778 _or_ 1242 x 2688                  | 2778 x 1284 _or_ 2688 x 1242                  | iPhone 14 Plus, 13 Pro Max, 12 Pro Max, 11 Pro Max, 11, XS Max, XR           | Yes if no 6.9"                  |
| 6.3"    | 1179 x 2556 _or_ 1206 x 2622                  | 2556 x 1179 _or_ 2622 x 1206                  | iPhone 17 Pro, 17, 16 Pro, 16, 15 Pro, 15, 14 Pro                            | Optional                        |
| 6.1"    | 1170 x 2532 _or_ 1125 x 2436 _or_ 1080 x 2340 | 2532 x 1170 _or_ 2436 x 1125 _or_ 2340 x 1080 | iPhone 17e, 16e, 14, 13 Pro, 13, 13 mini, 12 Pro, 12, 12 mini, 11 Pro, XS, X | Optional                        |
| 5.5"    | 1242 x 2208                                   | 2208 x 1242                                   | iPhone 8 Plus, 7 Plus, 6S Plus, 6 Plus                                       | Optional                        |
| 4.7"    | 750 x 1334                                    | 1334 x 750                                    | iPhone SE (3rd/2nd), 8, 7, 6S, 6                                             | Optional                        |
| 4"      | 640 x 1136                                    | 1136 x 640                                    | iPhone SE (1st), 5S, 5C, 5                                                   | Optional                        |
| 3.5"    | 640 x 960                                     | 960 x 640                                     | iPhone 4S, 4                                                                 | Optional                        |

**Recommended simulators for required sizes:**

- 6.9" → iPhone 16 Pro Max
- 6.5" → iPhone 14 Plus (newest device in this category — newer Plus/Max models moved to 6.9")

#### iPad

| Display         | Portrait (px)                                                  | Landscape (px)                                                 | Devices                                                                        | Required?             |
| --------------- | -------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------ | --------------------- |
| 13"             | 2064 x 2752 _or_ 2048 x 2732                                   | 2752 x 2064 _or_ 2732 x 2048                                   | iPad Pro (M5/M4/6th–1st), iPad Air (M4/M3/M2)                                  | **Yes** (if iPad app) |
| 12.9" (2nd gen) | 2048 x 2732                                                    | 2732 x 2048                                                    | iPad Pro (2nd gen)                                                             | Optional              |
| 11"             | 1488 x 2266 _or_ 1668 x 2420 _or_ 1668 x 2388 _or_ 1640 x 2360 | 2266 x 1488 _or_ 2420 x 1668 _or_ 2388 x 1668 _or_ 2360 x 1640 | iPad Pro (M5–1st), iPad Air (M4–4th), iPad (A16/10th), iPad mini (A17 Pro/6th) | Optional              |
| 10.5"           | 1668 x 2224                                                    | 2224 x 1668                                                    | iPad Pro, iPad Air (3rd), iPad (9th–7th)                                       | Optional              |
| 9.7"            | 1536 x 2048 _or_ 768 x 1024                                    | 2048 x 1536 _or_ 1024 x 768                                    | iPad Air 1–2, iPad (6th–3rd), iPad mini (5th–2)                                | Optional              |

#### Apple Watch

| Device                   | Dimensions (px) |
| ------------------------ | --------------- |
| Ultra 3                  | 422 x 514       |
| Ultra 2, Ultra           | 410 x 502       |
| Series 11, 10            | 416 x 496       |
| Series 9, 8, 7           | 396 x 484       |
| Series 6, 5, 4, SE 3, SE | 368 x 448       |
| Series 3                 | 312 x 390       |

Required for watchOS apps. Must use same screenshot size across all localizations.

#### Mac

| Dimensions (px) | Aspect Ratio |
| --------------- | ------------ |
| 2880 x 1800     | 16:10        |
| 2560 x 1600     | 16:10        |
| 1440 x 900      | 16:10        |
| 1280 x 800      | 16:10        |

Required for Mac apps.

#### Apple TV

| Dimensions (px)  |
| ---------------- |
| 3840 x 2160 (4K) |
| 1920 x 1080      |

#### Apple Vision Pro

| Dimensions (px) |
| --------------- |
| 3840 x 2160     |

## Getting Started — Practical Minimum

The spec tables above list every possible size, but most are optional fallbacks. Here's the minimum viable screenshot set:

### What you actually need

| Size            | Why                                         | Simulator             |
| --------------- | ------------------------------------------- | --------------------- |
| **6.9" iPhone** | Required for all iPhone apps                | iPhone 16 Pro Max     |
| **6.5" iPhone** | Different aspect ratio, huge installed base | iPhone 14 Plus        |
| **13" iPad**    | Only if your app supports iPad              | iPad Pro 13-inch (M4) |

All smaller iPhone sizes fall back to the nearest larger size you provide. Two sets of iPhone screenshots cover every device.

### Capture with Xcode Simulator

1. Boot the simulator: `open -a Simulator`
2. Choose the right device (File → Open Simulator → iOS → device name)
3. Run your app in that simulator
4. Navigate to each screen you want to capture
5. **`Cmd+S`** to save — outputs at exact App Store pixel dimensions
6. Screenshots save to Desktop by default

### Automated capture with Fastlane

If you'll regenerate screenshots each release, set up [Fastlane snapshot](https://docs.fastlane.tools/actions/snapshot/):

- Define UI tests that navigate to each screen
- Runs across multiple simulators and languages automatically
- More upfront setup, but pays off over time

### How many screenshots?

Aim for **3–5 per size**. The first 3 are critical (see below). Beyond 5, diminishing returns unless you have distinct features to show.

## The First 3 Rule

**80% of App Store impressions show only the first 3 screenshots** (before the user scrolls). These three must:

1. Communicate the core value proposition
2. Show the best feature/outcome
3. Differentiate from competitors

### Screenshot Gallery Order

| Position | Content                         | Purpose                                        |
| -------- | ------------------------------- | ---------------------------------------------- |
| **1**    | Hero — core value, best feature | Stop the scroll, communicate what the app does |
| **2**    | Key differentiator              | What makes you unique vs competitors           |
| **3**    | Most popular feature            | The thing users love most                      |
| **4**    | Social proof or outcome         | Ratings, results, testimonials                 |
| **5-8**  | Additional features             | Supporting features, settings, integrations    |
| **9-10** | Edge cases                      | Specialized features for niche users           |

## Screenshot Styles

### 1. Device Frame with Caption

The standard: device mockup showing the app, caption text above/below.

```
┌──────────────────────────┐
│   "Track Your Habits     │  ← Caption (benefit-focused)
│    Effortlessly"         │
│                          │
│   ┌──────────────────┐   │
│   │                  │   │
│   │   App Screen     │   │  ← Actual app UI in device frame
│   │   Content        │   │
│   │                  │   │
│   │                  │   │
│   └──────────────────┘   │
│                          │
└──────────────────────────┘
```

### 2. Full-Bleed UI (No Device Frame)

The app UI fills the entire screenshot. Works for immersive apps.

### 3. Lifestyle Context

The device shown in a real-world context (person holding phone, on desk, etc.).

### 4. Feature Highlight with Callouts

UI screenshot with arrows/circles pointing to specific features.

## Caption Writing

### Rules

- **Max 2 lines** of text
- **Benefit-focused**, not feature-focused
- **30pt+ equivalent** font size (must be readable in store)

### Examples

```
❌ Feature-focused:
"Push Notification System"
"Calendar View with Filters"
"Data Export Functionality"

✅ Benefit-focused:
"Never Miss a Deadline Again"
"See Your Week at a Glance"
"Share Reports in One Tap"
```

## Generating Screenshots

### Hero Screenshot (Position 1)

```bash
# Clean device mockup with hero feature
infsh app run falai/flux-dev-lora --input '{
  "prompt": "modern iPhone showing a beautiful fitness tracking app with activity rings and workout summary, device floating at slight angle against soft purple gradient background, professional product shot, clean minimal composition, subtle reflection",
  "width": 1024,
  "height": 1536
}'
```

### Feature Highlight

```bash
# Feature callout style
infsh app run bytedance/seedream-4-5 --input '{
  "prompt": "app store screenshot style, iPhone showing a messaging app with AI writing suggestions highlighted, clean white background, subtle UI callout arrows, professional marketing asset, modern design",
  "size": "2K"
}'
```

### Lifestyle Context

```bash
# Device in real-world setting
infsh app run falai/flux-dev-lora --input '{
  "prompt": "person holding iPhone showing a cooking recipe app, kitchen background with ingredients, warm natural lighting, over-the-shoulder perspective, lifestyle photography, authentic feeling",
  "width": 1024,
  "height": 1536
}'
```

### Before/After

```bash
# Split comparison
infsh app run infsh/stitch-images --input '{
  "images": ["before-screenshot.png", "after-screenshot.png"],
  "direction": "horizontal"
}'
```

## Preview Videos

### Apple App Store

| Spec        | Value                              |
| ----------- | ---------------------------------- |
| Duration    | 15-30 seconds                      |
| Orientation | Portrait or landscape (match app)  |
| Audio       | Optional (loops silently in store) |
| Format      | H.264, .mov or .mp4                |

### Preview Video Structure

| Segment   | Duration | Content                           |
| --------- | -------- | --------------------------------- |
| Hook      | 0-3s     | Show the core outcome/wow moment  |
| Feature 1 | 3-10s    | Demonstrate top feature in action |
| Feature 2 | 10-18s   | Second key feature                |
| Feature 3 | 18-25s   | Third feature or social proof     |
| CTA       | 25-30s   | End screen with app icon          |

```bash
# Generate preview video scenes
infsh app run google/veo-3-1-fast --input '{
  "prompt": "smooth screen recording style, finger tapping on a modern mobile app interface, swiping between screens showing charts and data visualizations, clean UI transitions, professional app demo"
}'
```

## Localization

Each language gets its own set of screenshots. Priorities:

| Market            | Localization Level                          |
| ----------------- | ------------------------------------------- |
| Primary markets   | Full: new screenshots + translated captions |
| Secondary markets | Translated captions, same screenshots       |
| Other             | English defaults                            |

Key localization markets: English, Japanese, Korean, Chinese (Simplified), German, French, Spanish, Portuguese (Brazilian)

## Common Mistakes

| Mistake                       | Problem                     | Fix                                            |
| ----------------------------- | --------------------------- | ---------------------------------------------- |
| Settings screen as screenshot | Nobody cares about settings | Show core value, not infrastructure            |
| Onboarding flow screenshots   | Shows friction, not value   | Show the app in-use state                      |
| Too much text                 | Unreadable in store         | Max 2 lines, 30pt+ font                        |
| Wrong dimensions              | Rejected by store           | Use exact platform specs                       |
| All screenshots look the same | No reason to scroll         | Vary composition and content                   |
| Feature-focused captions      | Doesn't communicate benefit | "Never Miss a Deadline" > "Push Notifications" |
| Outdated UI                   | Looks abandoned             | Update screenshots with each major release     |
| No hero screenshot            | Weak first impression       | Position 1 = your best shot                    |

## Checklist

- [ ] Correct dimensions for target platform
- [ ] First 3 screenshots communicate core value
- [ ] Captions are benefit-focused, max 2 lines
- [ ] No onboarding or settings screens
- [ ] Preview video is 15-30s with hook in first 3s
- [ ] Localized for top markets
- [ ] Screenshots updated for current app version

## Related Skills

```bash
npx skills add inference-sh/skills@ai-image-generation
npx skills add inference-sh/skills@ai-video-generation
npx skills add inference-sh/skills@image-upscaling
npx skills add inference-sh/skills@prompt-engineering
```

Browse all apps: `infsh app list`
