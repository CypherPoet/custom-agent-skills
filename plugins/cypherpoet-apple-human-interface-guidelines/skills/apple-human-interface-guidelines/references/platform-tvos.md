# Platform — tvOS

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG platform pages: Designing for tvOS, Top Shelf, Live-viewing apps.

## Contents
- [Designing for tvOS](#designing-for-tvos)
- [Top Shelf](#top-shelf)
- [Live-viewing apps](#live-viewing-apps)

### Designing for tvOS
*Last changed: 2022-09*

**Purpose:** Shared, 10-foot "living room" experiences built around the focus engine and remote-based interaction on a large, high-resolution display.

**Best practices:**
- **Display & ergonomics.** Design for a large, high-resolution screen viewed from 8+ feet away; keep content clear, legible, and captivating from across the room. People may keep interacting while moving around the room.
- **Inputs.** Support the Siri Remote, game controllers, voice (Siri), and companion apps on other devices. Build on the fluid, familiar gestures of the Siri Remote.
- **Focus.** Embrace the tvOS focus system — let it gently highlight and expand onscreen items as people move among them, so they always know what to do and where they are. Small movements on the remote's Touch surface animate the focused item (parallax/lighting; 3D effect for layered images).
- **Content.** Deliver edge-to-edge artwork, subtle fluid animations, and engaging audio for a rich, cinematic experience.
- **App interactions.** Support deep, hours-long immersion, but also picture-in-picture so people can follow an alternative app or video at the same time.
- **Multiuser.** Make sign-in easy and infrequent, handle shared sign-in, and switch profiles automatically when the current viewer changes.
- **System integration.** Integrate with the TV app, SharePlay, Top Shelf, and TV provider accounts.

### Top Shelf

**Purpose:** Showcase new, featured, or recommended content in a rich area above the Apple TV Dock that links straight into your app.

**Best practices:**
- **Content.** Feature new content (new releases/episodes, upcoming titles); avoid promoting content people already purchased, rented, or watched. Personalize recommendations; let people resume playback or jump back into active gameplay.
- **Entry.** Help people jump right in — the carousel-actions and carousel-details templates each provide a primary play button plus a More Info button by default.
- **Dynamic over static.** Prefer compelling dynamic content (full-screen video/images), ideally built as layered images. Supply at least one static fallback image; the system shows it (flipped and blurred) when the app is focused in the Dock and full-screen content is unavailable. A static image isn't focusable — don't imply interactivity.
- **No ads/prices.** Avoid advertisements; showing purchasable content is fine, but keep the focus on new/exciting content and only surface prices when people show interest.
- **Layout styles.** Carousel actions (full-screen video/images + unobtrusive controls + title/optional subtitle); carousel details (adds metadata like plot, cast); sectioned content row (labeled, focusable row — fill the full screen width, include at least one label); scrolling inset banner (auto-scrolls on a timer until focused; 3–8 images; bake any text into the image and add it to the accessibility label).
- **Mixed sizes.** In a sectioned content row, images scale up to match the tallest image's height (e.g., a 16:9 image scales to 500 px tall beside a poster or square).

**Specs:**

Static fallback image (16:9, fit to 1920 px wide):

| Image size |
| --- |
| 2320x720 pt (2320x720 px @1x, 4640x1440 px @2x) |

Sectioned content row — Poster (2:3):

| Aspect | Image size |
| --- | --- |
| Actual size | 404x608 pt (404x608 px @1x, 808x1216 px @2x) |
| Focused/Safe zone size | 380x570 pt (380x570 px @1x, 760x1140 px @2x) |
| Unfocused size | 333x570 pt (333x570 px @1x, 666x1140 px @2x) |

Sectioned content row — Square (1:1):

| Aspect | Image size |
| --- | --- |
| Actual size | 608x608 pt (608x608 px @1x, 1216x1216 px @2x) |
| Focused/Safe zone size | 570x570 pt (570x570 px @1x, 1140x1140 px @2x) |
| Unfocused size | 500x500 pt (500x500 px @1x, 1000x1000 px @2x) |

Sectioned content row — 16:9:

| Aspect | Image size |
| --- | --- |
| Actual size | 908x512 pt (908x512 px @1x, 1816x1024 px @2x) |
| Focused/Safe zone size | 852x479 pt (852x479 px @1x, 1704x958 px @2x) |
| Unfocused size | 782x440 pt (782x440 px @1x, 1564x880 px @2x) |

Scrolling inset banner:

| Aspect | Image size |
| --- | --- |
| Actual size | 1940x692 pt (1940x692 px @1x, 3880x1384 px @2x) |
| Focused/Safe zone size | 1740x620 pt (1740x620 px @1x, 3480x1240 px @2x) |
| Unfocused size | 1740x560 pt (1740x560 px @1x, 3480x1120 px @2x) |

### Live-viewing apps

**Purpose:** Elevate live content above video-on-demand so people can distinguish, reach, and immerse in it at a glance.

**Best practices:**
- **Prioritize live.** Feature live content prominently and make it easy to access — put it in the first tab so playback starts with one tap or none (e.g., a Watch Now button that disappears and goes full-screen on tap).
- **Signal liveness.** Make live content look live; playing it is best, but also mark it with a badge, symbol, or sash and group it (e.g., a "Live" row). Consider a progress indicator so people know where they'll land when joining in-progress content. Give instant visual feedback on channel change to confirm arrival and mask load time.
- **Actions.** Playback is always primary; offer record, restart/start over, download, and favorite in a consistent order throughout the app. Surface alternate showtimes when applicable.
- **Content footer.** For browsing channels during playback, use a subtly darkened footer that keeps text legible; badge or tint the currently playing thumbnail; match its categories to the EPG; make invoke/dismiss simple and symmetric (swipe up to show, swipe down to hide).
- **Audio.** Keep audio matched to the current context — continue while browsing over live content in the background, but stop when people leave the live tab.
- **EPG.** Prominently show the current program/channel/time and make returning to playback easy. Help people page, scroll, and jump; offer My Channels/Favorites. Group content into familiar categories (Movies, TV Shows, Kids, Sports, Popular) matching the content footer. Let people browse the EPG without leaving current content (PiP or background playback).
- **Cloud DVR.** Let people start/stop recording from the info panel, and schedule future programs (this episode, only new episodes, or specific games) from a details view. Allow play/delete and recording-setting changes within the DVR area. Offer storage management — delete watched or aged content, and automatic overwrite of oldest/already-viewed content to avoid running out of space.
