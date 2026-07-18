# Designing the screenshot set for conversion

Sizes and capture get you a *valid* listing; design gets you *downloads*. Screenshots and the app
preview are the largest visual conversion lever on a product page. This is the screenshot-specific
design guidance — for keyword/subtitle/description strategy and review compliance, that's the
`apple-app-store-best-practices` skill.

## Order for the scroll

- The **first 2–3 screenshots are what a user sees in search results before tapping in**, and most
  people never scroll the full set. Put your single strongest value proposition in shot 1, the next
  two strongest in shots 2–3.
- If you ship an **app preview video**, it occupies the first slot and autoplays (muted) — design
  shots 1–2 to still carry the message for users who don't watch it.

## One idea per screenshot

- Each screenshot should land **one** feature or benefit. A shot trying to show five things reads
  as noise at thumbnail size.
- Use all the slots you can fill meaningfully (up to 10 per class). More distinct, well-made shots
  give more reasons to download — but a weak shot 7 is worse than stopping at 6.

## Captions: short, legible, localized

- Add a concise caption band above or below the UI ("Track every habit in one tap"), not a
  paragraph. It's a billboard, not documentation.
- **Legibility is the whole game at thumbnail scale:** large type, high contrast, minimal words.
  Test how it reads shrunk to search-result size, not just full screen.
- Localize the caption copy per market (see the `frameit` strings workflow in
  [capturing-screenshots.md](capturing-screenshots.md)) — a translated band converts far better than
  English shown to a non-English store.

## Portrait vs landscape

- Most apps: **portrait**, because search results and the product page favor it and you fit more
  per row.
- **Games and video apps** that are played in landscape should show landscape — match the actual
  experience. (App previews for macOS/tvOS are landscape-only regardless; see
  [app-preview-specs.md](app-preview-specs.md).)

## Patterns by category

- **Games:** lead with the most visually striking gameplay/hero art; show real gameplay, not
  pre-rendered cinematics.
- **Utilities / productivity:** show the core task being completed with realistic data; captions
  name the outcome ("Scan a receipt in 3 seconds").
- **Social / content:** show real (or realistic) populated feeds and the moment of value, never
  empty states.

## Test it — Product Page Optimization

App Store Connect has a native A/B testing tool, **Product Page Optimization (PPO)**: run up to
three treatments of your screenshots/preview/icon against the live page and measure conversion on
real traffic before committing. Use it to settle "which order / which hero shot" with data instead
of opinion.

- **Custom Product Pages** are the related tool for showing *different* screenshot sets to
  different audiences (e.g. a campaign-specific page), each with its own URL.
- Overview: <https://developer.apple.com/help/app-store-connect/create-product-page-optimization-tests/overview-of-product-page-optimization>

## The compliance guardrail

Whatever the design, the screenshots must represent the **actual current app** — invented UI,
features that don't ship, or content from another app is a review rejection (§2.3.3). Marketing
frames and caption bands are fine *as long as real app UI is prominently shown*. Compliance detail
lives in the `apple-app-store-best-practices` skill.
