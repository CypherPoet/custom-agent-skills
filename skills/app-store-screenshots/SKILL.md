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

## Reference Files

| File | Contents |
|------|----------|
| [platform-specs.md](references/platform-specs.md) | Exact pixel dimensions for all Apple platforms (iPhone, iPad, Apple Watch, Mac, Apple TV, Vision Pro) + preview video specs |

**Source of truth:** [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/) — Apple Developer docs

Load `references/platform-specs.md` when you need exact pixel dimensions. The practical minimum is covered below.

## Getting Started — Practical Minimum

The full spec tables list every possible size, but most are optional fallbacks. Here's the minimum viable screenshot set:

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

Preview video specs and structure are in [references/platform-specs.md](references/platform-specs.md). Key points: 15-30s, H.264 .mov/.mp4, portrait or landscape matching your app.

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
