# Apple App Store app preview (video) specifications

App previews are the optional autoplay videos on a product page — up to 3 per device class. The
durable rules live in [SKILL.md](../SKILL.md); this is the exhaustive reference.

**Source:** <https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications>
The resolutions were reconciled against the live App Store Connect Media Manager on 2026-06-19 — an authenticated console, so source-only reviews cannot repeat it. Re-confirm there after major hardware releases.

## Requirements

| Field | Value |
|---|---|
| Count | Up to 3 per device class, per localization |
| Maximum file size | 500 MB |
| Length | 15–30 seconds |
| Default poster frame | 5 seconds in (changeable in App Store Connect) |
| Orientation | Portrait or landscape (**macOS and tvOS: landscape only**) |
| Formats | H.264 or ProRes 422 (HQ only) |
| Capture/playback OS | iOS 8 or later |

## Video specifications

| | H.264 | ProRes 422 (HQ only) |
|---|---|---|
| Target bit rate | 10–12 Mbps | VBR ~220 Mbps |
| Video characteristics | Progressive, up to High Profile Level 4.0 | Progressive, no external references |
| Max frame rate | 30 fps | 30 fps |
| Audio codec | 256 kbps AAC | PCM or 256 kbps AAC (PCM bit depth 16/24/32) |
| Sample rate | 44.1 or 48 kHz | 44.1 or 48 kHz |
| Extensions | `.mov`, `.m4v`, `.mp4` | `.mov` |

**Audio (both formats):** stereo, all tracks enabled. Stereo configuration is either one track
with 2-channel stereo (channel 1 = L, channel 2 = R) **or** two tracks of 1-channel stereo
(track 1 = L, track 2 = R). A **silent** preview still needs a stereo track present — a video with no
audio track fails validation; mux a silent stereo AAC track if your capture has none.

## Content rules

A technically valid preview still gets rejected if its *content* misleads:

- **Show real in-app capture.** A preview is device-captured app footage, not a marketing sizzle reel.
  Short intro/outro title cards are fine, but the bulk must be the actual UI in motion.
- **Disclose IAP-gated content.** If the preview shows premium/Pro features that require an in-app
  purchase, make that clear (a brief "in-app purchase required" end card or on-screen note) rather than
  presenting paywalled features as if they're free.
- **No prices anywhere in the video.** Prices vary by storefront and over time, so Apple rejects specific
  prices baked into previews (and screenshots). Say "in-app purchase," never "$4.99."
- Same **final-content, no-placeholder** bar as the app itself (§2.1).

## Upload resolutions per device class

"Device resolution" is the screen; the **accepted (upload) resolution** is what you hand App Store
Connect. The modern App Store Connect Media Manager uses ONE combined iPhone drop zone for both
screenshots and app previews ("Drag up to 3 app previews and 10 screenshots here for iPhone 6.5", 6.7"
or 6.9" Displays"), and it validates app previews at the **same device-native resolution as
screenshots** — not the old 886×1920 standalone-preview size. Provide the largest class and the smaller
ones auto-scale, exactly like screenshots. Landscape values are the portrait values transposed (e.g.
`2868×1320`).

> **Apple's published spec lags its own UI.** The app-preview-specifications reference page still lists
> 886×1920 for iPhone — the legacy App Preview size from when previews had their own uploader, separate
> from screenshots. Today's Media Manager rejects 886×1920 for these classes. **Trust the live App Store
> Connect drop zone; it is ground truth.** Confirmed against a live 6.9"/6.5" Media Manager on 2026-06-19.

### iPhone

| Display class | Accepted upload resolution (portrait) | If omitted |
|---|---|---|
| 6.9" | 1320×2868 · 1290×2796 · 1260×2736 | — (canonical; record/upload 1320×2868) |
| 6.5" | 1284×2778 · 1242×2688 | scaled from 6.9" |

The current Media Manager exposes only the 6.9" and 6.5" iPhone slots; every smaller class is generated
from the 6.9" upload, exactly as with screenshots. Record a 6.9" simulator at its native 1320×2868 and
upload as-is — no rescaling, and **not** the legacy 886×1920.

### iPad

| Display class | Accepted upload resolution (portrait) | If omitted |
|---|---|---|
| 13" | 1200×1600 | — (canonical) |
| 12.9" | 1200×1600 · 900×1200 | scaled from 13" |
| 11" | 1200×1600 | scaled from 13" |
| 10.5" | 1200×1600 | scaled from 12.9" |
| 9.7" | 900×1200 | scaled from 10.5" |

### Mac / Apple TV / Apple Vision Pro

| Platform | Accepted upload resolution (landscape) |
|---|---|
| Mac | 1920×1080 |
| Apple TV | 1920×1080 |
| Apple Vision Pro | 3840×2160 |

Apple Watch does not support app previews.
