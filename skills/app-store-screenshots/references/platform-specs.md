# Platform Specifications

## Apple App Store

**Source of truth:** [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/) — Apple Developer docs

Up to **3 app previews** and **10 screenshots** per device size per localization. Formats: PNG or JPEG (no alpha). First **3 screenshots** are visible without scrolling.

### iPhone

| Display | Portrait (px)                                 | Landscape (px)                                | Devices                                                                      | Required?                       |
| ------- | --------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------- |
| 6.9"    | 1260 x 2736 _or_ 1320 x 2868 _or_ 1290 x 2796 | 2736 x 1260 _or_ 2868 x 1320 _or_ 2796 x 1290 | iPhone Air, 17 Pro Max, 16 Pro Max, 16 Plus, 15 Pro Max, 15 Plus, 14 Pro Max | **Yes** (covers 6.5"/6.7"/6.9") |
| 6.5"    | 1284 x 2778 _or_ 1242 x 2688                  | 2778 x 1284 _or_ 2688 x 1242                  | iPhone 14 Plus, 13 Pro Max, 12 Pro Max, 11 Pro Max, 11, XS Max, XR           | Yes if no 6.9"                  |
| 6.3"    | 1179 x 2556 _or_ 1206 x 2622                  | 2556 x 1179 _or_ 2622 x 1206                  | iPhone 17 Pro, 17, 16 Pro, 16, 15 Pro, 15, 14 Pro                            | Optional                        |
| 6.1"    | 1170 x 2532 _or_ 1125 x 2436                   | 2532 x 1170 _or_ 2436 x 1125                   | iPhone 17e, 16e, 14, 13 Pro, 13, 12 Pro, 12, 11 Pro, XS, X                   | Optional                        |
| 5.4"    | 1080 x 2340                                    | 2340 x 1080                                    | iPhone 13 mini, 12 mini                                                       | Optional                        |
| 5.5"    | 1242 x 2208                                   | 2208 x 1242                                   | iPhone 8 Plus, 7 Plus, 6S Plus, 6 Plus                                       | Optional                        |
| 4.7"    | 750 x 1334                                    | 1334 x 750                                    | iPhone SE (3rd/2nd), 8, 7, 6S, 6                                             | Optional                        |
| 4"      | 640 x 1136                                    | 1136 x 640                                    | iPhone SE (1st), 5S, 5C, 5                                                   | Optional                        |
| 3.5"    | 640 x 960                                     | 960 x 640                                     | iPhone 4S, 4                                                                 | Optional                        |

**Recommended simulators for required sizes:**

- 6.9" → iPhone 16 Pro Max
- 6.5" → iPhone 14 Plus (newest device in this category — newer Plus/Max models moved to 6.9")

### iPad

| Display         | Portrait (px)                                                  | Landscape (px)                                                 | Devices                                                                        | Required?             |
| --------------- | -------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------ | --------------------- |
| 13"             | 2064 x 2752 _or_ 2048 x 2732                                   | 2752 x 2064 _or_ 2732 x 2048                                   | iPad Pro (M5/M4/6th–1st), iPad Air (M4/M3/M2)                                  | **Yes** (if iPad app) |
| 12.9" (2nd gen) | 2048 x 2732                                                    | 2732 x 2048                                                    | iPad Pro (2nd gen)                                                             | Optional              |
| 11"             | 1488 x 2266 _or_ 1668 x 2420 _or_ 1668 x 2388 _or_ 1640 x 2360 | 2266 x 1488 _or_ 2420 x 1668 _or_ 2388 x 1668 _or_ 2360 x 1640 | iPad Pro (M5–1st), iPad Air (M4–4th), iPad (A16/10th), iPad mini (A17 Pro/6th) | Optional              |
| 10.5"           | 1668 x 2224                                                    | 2224 x 1668                                                    | iPad Pro, iPad Air (3rd), iPad (9th–7th)                                       | Optional              |
| 9.7"            | 1536 x 2048 _or_ 768 x 1024                                    | 2048 x 1536 _or_ 1024 x 768                                    | iPad Air 1–2, iPad (6th–3rd), iPad mini (5th–2)                                | Optional              |

### Apple Watch

| Device                   | Dimensions (px) |
| ------------------------ | --------------- |
| Ultra 3                  | 422 x 514       |
| Ultra 2, Ultra           | 410 x 502       |
| Series 11, 10            | 416 x 496       |
| Series 9, 8, 7           | 396 x 484       |
| Series 6, 5, 4, SE 3, SE | 368 x 448       |
| Series 3                 | 312 x 390       |

Required for watchOS apps. Must use same screenshot size across all localizations.

### Mac

| Dimensions (px) | Aspect Ratio |
| --------------- | ------------ |
| 2880 x 1800     | 16:10        |
| 2560 x 1600     | 16:10        |
| 1440 x 900      | 16:10        |
| 1280 x 800      | 16:10        |

Required for Mac apps.

### Apple TV

| Dimensions (px)  |
| ---------------- |
| 3840 x 2160 (4K) |
| 1920 x 1080      |

### Apple Vision Pro

| Dimensions (px) |
| --------------- |
| 3840 x 2160     |

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
