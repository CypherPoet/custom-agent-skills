# Icon Design & App Store Optimization (Apple)

How to make an Apple app icon *convert* — the design and tap-through side that complements the build-and-ship engineering in [`../SKILL.md`](../SKILL.md). This is Apple-focused; Android adaptive icons and Play Store experiments are a separate concern.

**Contents:** [Why the icon is your highest-leverage asset](#why-the-icon-is-your-highest-leverage-asset) · [Design principles](#design-principles) · [Apple icon sizes](#apple-icon-sizes) · [Icon audit rubric](#icon-audit-rubric) · [A/B-testing icons on iOS](#ab-testing-icons-on-ios) · [Designer brief template](#designer-brief-template)

## Why the icon is your highest-leverage asset

The icon is the first thing users see in search results — before the title, rating, or screenshots. In browse and charts it's often the *only* visual competing for attention. A clearer, more distinctive icon can lift tap-through rate (TTR) — the share of people who tap your app after seeing it — substantially with no other change. It's also your brand mark everywhere else: Home Screen, notifications, the press kit, a social avatar, a favicon. Design it to carry all of that.

## Design principles

### 1. Simplicity at small size

Icons render around 60×60 pt in iPhone search results. At that size, detail is invisible.

- At most ~2 elements.
- No text — it's illegible small, and Apple discourages it.
- A strong silhouette recognizable at a glance.
- Mock it up at 60×60 px before committing.

### 2. Contrast against the App Store background — light *and* dark

The App Store renders on a light background (light mode) and a dark one (dark mode), and so does the Home Screen.

- Hold high contrast in **both** modes.
- Avoid near-white fills — they vanish in light mode.
- Avoid near-black fills — they vanish in dark mode.
- Consider a subtle shadow or inner edge on the icon background to separate it from the canvas.

This is the conversion-side reason to author the `.icon`'s **Dark** (and, where it fits, **Clear**) appearance variant deliberately rather than letting it default — see the appearance-variant notes in [`../SKILL.md`](../SKILL.md).

### 3. Category visual language

Match enough to read as "in category," differ enough to stand out:

| Category | Common patterns | How to stand out |
|----------|----------------|-----------------|
| Productivity | Blue, clean, minimal | Warmer colors, bolder marks |
| Health / Fitness | Green, orange, energetic | Premium dark, sophisticated |
| Finance | Blue, green, conservative | Bold, distinctive mark |
| Games | Bright, characters, action | Premium / dark if competitors are loud |
| Social | Round shapes, soft colors | Sharp, distinctive if the feed is soft |
| Meditation | Purple, blue, calm | Unexpected contrast color |
| Photo / Video | Gradient, camera | Single strong mark |

**Rule:** study your top ~20 competitors' icons, then design to be immediately distinguishable from them.

### 4. One recognizable mark

A single, memorable mark — not a scene or a composition. Ask: *can someone describe this in three words?*

- ✅ "Red speech bubble" — ❌ "Someone using a phone with a gradient"
- ✅ "Bold orange flame" — ❌ "Abstract colorful shapes"

### 5. Brand consistency

The icon is your brand mark in the App Store. Keep it consistent with your app's primary palette and with your splash screen, notifications, and marketing, so it works equally as a press-kit asset, social avatar, and favicon.

## Apple icon sizes

Author one **1024×1024 px master** — no alpha, no rounded corners (Apple applies the mask). The system, or the [generation script](../SKILL.md#generation-script), derives the rest.

| Surface | Size |
|---------|------|
| App Store marketing | 1024×1024 px (master) |
| iPhone Home Screen | 60×60 pt @2x / @3x |
| iPad Home Screen | 76×76 pt @1x / @2x, 83.5×83.5 pt @2x |
| Apple Watch | 40–44 pt range (model-dependent) |
| Spotlight / Settings / Notifications | system-derived smaller sizes |

A modern `.icon` collapses this to a single layered source the system renders per platform; the appiconset still needs discrete PNGs for pre-26 OS versions (the script writes them).

## Icon audit rubric

Score a current or proposed icon 1–10 per dimension:

```
Clarity at 60×60 px        [1–10]
  - Recognizable mark at small size?
  - No illegible text?

Light/dark contrast        [1–10]
  - Holds up on a light App Store background?
  - Holds up on a dark one?

Category differentiation   [1–10]
  - Stands out from the top ~10 competitor icons?

Simplicity                 [1–10]
  - ~2 elements max?
  - Describable in three words?

Brand alignment            [1–10]
  - Consistent with the app's visual identity?

Overall: [N]/50
```

A total below ~35/50, or any single dimension at ≤5, is a strong signal to redesign before you ship or spend on an A/B test.

## A/B-testing icons on iOS

Apple's **Product Page Optimization (PPO)** in App Store Connect tests icon variants against your live listing with real traffic.

**PPO, not alternate app icons.** PPO is the *acquisition* test — it changes what prospective users see on your product page and measures installs. Don't confuse it with **alternate app icons** (`setAlternateIconName` / `CFBundleAlternateIcons`), which let an *already-installed* app switch its Home Screen icon at runtime. That's a personalization feature, not a conversion experiment, and it has no effect on installs.

1. App Store Connect → your app → **Product Page Optimization** → create a test.
2. Add up to **3** icon variants (treatments) alongside the current icon (control). Each treatment's icon must also be included in the corresponding app binary.
3. Set traffic allocation per variant (e.g. ~25–33% each).
4. Run for **at least 7 days**, and until the result reaches significance — don't stop on day-two noise.

**Liquid Glass caveat.** PPO tests the flat marketing / springboard icon image App Store Connect ingests, not a live-rendered `.icon`. If you ship a Liquid Glass `.icon`, make sure the 1024 image each treatment uses faithfully represents how the icon actually renders (its appearance variants, the system mask) — otherwise the test optimizes an image users won't quite see. Confirm current asset requirements against Apple's PPO docs.

Reading results:

- **Primary metric:** conversion rate (impressions → installs) per variant.
- **Minimum signal:** ~1,000+ impressions per variant before trusting a direction.
- **Significance:** App Store Connect surfaces a confidence / improvement indicator; treat overlapping confidence intervals as "no winner yet."

Test **one variable at a time** so you can attribute the lift:

| Test | Variants |
|------|---------|
| Color scheme | Same mark, 2–3 background colors |
| Mark style | Flat vs. illustrated vs. dimensional |
| Light vs. dark | Light background vs. dark background |
| Character vs. abstract | Character-based vs. geometric |

For the App Store Connect mechanics around builds, versions, and submission that PPO sits on top of, see the sibling **`app-store-connect-kit`** plugin (`app-store-connect-submission`).

## Designer brief template

```
App: [name + one-line description]
Category: [category]
Primary audience: [who uses it]
Brand colors: [hex values]
Mood: [premium / playful / trustworthy / energetic / calm]

What the icon should convey: [core value or identity]
What to avoid: [don't echo competitor X; avoid Y]

Differentiate from: [3–5 competitors, with their icons]
Reference icons I like: [3–5 from other apps]

Deliverables:
- 3 distinct concepts at 1024×1024 px
- Each shown at a 60×60 px mockup in an App Store search context
- A dark-background check for each (it must hold up in dark mode)
- Final: PNG, no alpha, no rounded corners
- Optional: layered source (or per-element layers) for a Liquid Glass `.icon`
```
