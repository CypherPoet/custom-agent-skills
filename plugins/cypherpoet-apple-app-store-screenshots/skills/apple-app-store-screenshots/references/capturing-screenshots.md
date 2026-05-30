# Capturing & automating App Store screenshots

How to produce pixel-correct, store-ready screenshots — by hand for a quick set, or automated
when you have several locales and device classes to keep in sync. Dimensions and the
upload-the-largest rule are in [device-specifications.md](device-specifications.md).

## What "store-ready" means

- **Native resolution, never upscaled.** Capture on a device/simulator whose screen matches an
  accepted size for the class (see [device-specifications.md](device-specifications.md)). Scaling a
  small capture up to a larger size produces soft, rejected-looking art.
- **Clean status bar.** A real battery percentage, carrier name, or 4:17 PM clock dates the shot
  and looks sloppy. Normalize it — full bars, full battery, a fixed time.
- **Real content, not Lorem Ipsum.** Empty states and placeholder data convert poorly and can draw
  a compliance flag (the listing must represent the actual app — that's the
  `apple-app-store-best-practices` half of the job).

## Manual route (a few screenshots, one language)

1. Run the app in the **Simulator** for a device in your target class (e.g. an iPhone 16 Pro Max
   for the 6.9" class).
2. Clean the status bar before capturing:
   ```shell
   xcrun simctl status_bar booted override \
     --time "9:41" --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3
   ```
   (9:41 is Apple's convention.) Reset later with `xcrun simctl status_bar booted clear`.
3. Capture at native resolution:
   ```shell
   xcrun simctl io booted screenshot ~/Desktop/shot-01.png
   ```
   (Simulator → File → Save Screen also works, but the CLI is scriptable.)
4. Repeat for the iPad 13" class. Every smaller class auto-scales, so you usually only capture the
   two canonical sizes.

## Automated route — `fastlane snapshot` (many locales × classes)

When you have more than one language or want screenshots regenerated on every release,
[`fastlane snapshot`](https://docs.fastlane.tools/actions/snapshot/) is the standard tool. It
drives a UI test that walks the app and captures each screen across the device + locale matrix you
declare, so a single command yields the full localized set at the correct native sizes.

The pieces:

- A **UI test** (`XCUITest`) that navigates to each screen and calls `snapshot("01LaunchScreen")`
  at the moments you want captured.
- A **`Snapfile`** listing the `devices` (one per size class you care about — typically just the
  6.9" iPhone and 13" iPad) and the `languages`.
- `fastlane snapshot` runs the test once per device × language and writes named PNGs, then builds
  an HTML overview so you can eyeball the whole set.

It also handles the clean status bar automatically (it overrides to 9:41, full bars) — one of the
main reasons to use it over manual capture.

## Add device frames & captions — `frameit`

[`frameit`](https://docs.fastlane.tools/actions/frameit/) wraps each raw screenshot in the
matching Apple device bezel and can place a localized title/keyword band above it (driven by a
`Framefile.json` and per-locale `.strings`). This is how you get the framed, captioned
"marketing" screenshots most listings use — while keeping the real app UI prominently visible
(required for review). Pair the band copy with the design guidance in
[design-and-conversion.md](design-and-conversion.md).

## Upload — `fastlane deliver`

[`deliver`](https://docs.fastlane.tools/actions/deliver/) uploads the `screenshots/` tree (it
infers device class and locale from the folder layout) along with the rest of your metadata to App
Store Connect, so the generated set ships without hand-uploading each image.

## Localization workflow

- Screenshots live **per language**. `snapshot` produces one folder per locale automatically;
  uploading via `deliver` maps each folder to the matching App Store localization.
- A default set can stand in for languages you haven't localized, but localized caption bands
  convert better — localize the `frameit` strings even if the underlying captures are shared.
- **Apple Watch is special:** one screenshot size must be used across *all* localizations
  (see [device-specifications.md](device-specifications.md)).

## Common rejection / quality traps

- Wrong dimensions for the class → the upload is rejected outright. Confirm against
  [device-specifications.md](device-specifications.md), and prefer producing the canonical
  (largest) size so the rest auto-scale.
- Upscaled or blurry captures, or a screenshot that's mostly marketing art with little real UI.
- Stale status bar (live clock/battery/carrier).
- Showing features or content that aren't in the shipping build — a compliance issue; see
  `apple-app-store-best-practices`.
