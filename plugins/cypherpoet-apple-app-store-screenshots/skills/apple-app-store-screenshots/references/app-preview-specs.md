# Apple App Store app preview (video) specifications

App previews are the optional autoplay videos on a product page — up to 3 per device class. The
durable rules live in [SKILL.md](../SKILL.md); this is the exhaustive reference.

**Source:** <https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications>
**Verified:** 2026-05-30. Re-check after major hardware releases and re-stamp.

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
(track 1 = L, track 2 = R).

## Upload resolutions per device class

"Device resolution" is the screen; the **accepted (upload) resolution** is what you hand App Store
Connect. Provide the largest class and the smaller ones auto-scale, exactly like screenshots.
Landscape values are the portrait values transposed (e.g. `1920×886`).

### iPhone

| Display class | Accepted upload resolution (portrait) | If omitted |
|---|---|---|
| 6.9" | 886×1920 | — (canonical) |
| 6.5" | 886×1920 | scaled from 6.9" |
| 6.3" | 886×1920 | scaled from 6.5" |
| 6.1" | 886×1920 | scaled from 6.5" |
| 5.5" | 1080×1920 | scaled from 6.1" |
| 4.7" | 750×1334 | scaled from 5.5" |
| 4" | 1080×1920 | scaled from 4.7" |
| 3.5" | **App previews not supported** | — |

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
