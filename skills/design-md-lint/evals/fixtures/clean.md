---
name: Lighthouse
version: alpha
description: A calm, navigational design system for productivity tools.

colors:
  primary:
    "500": "#2563EB"
    "600": "#1D4ED8"
    "700": "#1E40AF"
  neutral:
    "50": "#F8FAFC"
    "500": "#64748B"
    "900": "#0F172A"
  surface: "#FFFFFF"
  on-surface: "#0F172A"
  error: "#DC2626"
  success: "#16A34A"

typography:
  headline-lg:
    fontFamily: "Inter"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: "40px"
    letterSpacing: "-0.02em"
  headline-md:
    fontFamily: "Inter"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: "32px"
    letterSpacing: "-0.01em"
  headline-sm:
    fontFamily: "Inter"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: "28px"
    letterSpacing: "-0.01em"
  body-lg:
    fontFamily: "Inter"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: "28px"
    letterSpacing: "0em"
  body-md:
    fontFamily: "Inter"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "24px"
    letterSpacing: "0em"
  body-sm:
    fontFamily: "Inter"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "20px"
    letterSpacing: "0.01em"
  label-lg:
    fontFamily: "Inter"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "20px"
    letterSpacing: "0.02em"
  label-md:
    fontFamily: "Inter"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: "18px"
    letterSpacing: "0.02em"
  label-sm:
    fontFamily: "Inter"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: "16px"
    letterSpacing: "0.04em"

rounded:
  none: "0px"
  sm: "4px"
  md: "8px"
  lg: "12px"
  full: "9999px"

spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"

components:
  button-primary:
    backgroundColor: "{colors.primary.500}"
    textColor: "{colors.surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  button-primary-hover:
    backgroundColor: "{colors.primary.600}"
    textColor: "{colors.surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  button-primary-disabled:
    backgroundColor: "{colors.neutral.500}"
    textColor: "{colors.surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  button-primary-focus:
    backgroundColor: "{colors.primary.500}"
    textColor: "{colors.surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
    outlineColor: "{colors.primary.700}"
    outlineWidth: "2px"
    outlineOffset: "2px"
  input-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm} {spacing.md}"
  input-focus:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm} {spacing.md}"
    outlineColor: "{colors.primary.500}"
    outlineWidth: "2px"
---

# Lighthouse

## Overview

Lighthouse is for focused, long-session productivity tools — calendar, notes, task manager. The aesthetic is calm and navigational: confident blues for direction, generous neutrals for breathing room, sharp typography for legibility under fatigue. Three adjectives anchor every design decision: **clear**, **composed**, **trustworthy**. The audience is professionals working 4+ hour blocks, often on second monitors, often returning to the same view dozens of times per day.

## Colors

The primary blue (`{colors.primary.500}`) is the system's anchor — it carries direction (links, active states, primary buttons) and never appears purely decoratively. The neutral palette does most of the heavy lifting: backgrounds and surfaces draw from `{colors.neutral.50}` and `{colors.neutral.500}`; body and headline text use `{colors.on-surface}` for primary content. Status colors `{colors.error}` and `{colors.success}` are reserved for genuine status communication, never for emphasis. Because these tools run for hours, palettes lean cool and slightly desaturated to reduce eye strain.

## Typography

Inter is the only font family. The size progression follows a roughly 1.2x scale from `body-md` (16px) outward, which produces clear hierarchy without dramatic jumps. Weights stay between 400 and 700 — heavier weights are reserved for headlines and primary labels to maintain calm. Headlines render in `{colors.neutral.900}` for maximum contrast against `{colors.surface}`; body and label tokens use `{colors.on-surface}`. Letter spacing tightens slightly on headlines and opens slightly on small labels to preserve legibility at every size.

## Layout

The grid is 8px-based. `{spacing.xs}` (4px) is the only sub-8 step and is reserved for icon-adjacent rhythm; `{spacing.sm}` (8px) and `{spacing.md}` (16px) drive component padding and intra-control gaps; `{spacing.lg}` (24px) anchors container gutters and section spacing; `{spacing.xl}` (32px) handles layout-level rhythm between major regions. Containers cap at 1200px on desktop. The 8px cadence keeps every surface aligned to the same rhythm.

## Elevation & Depth

Elevation is communicated through subtle borders and a single shadow level rather than layered shadows. The system favors flatness — depth is implied by neutral background tone shifts (`surface` → `neutral.50`) rather than dramatic drop shadows.

## Shapes

Corners are rounded but restrained. `rounded.md` (8px) is the default for buttons; `rounded.sm` (4px) anchors smaller affordances like inputs and chips; `rounded.lg` (12px) is reserved for surface-level containers (cards, modals). `rounded.full` belongs to avatars and status pills. Sharp corners (`rounded.none`) are unused — the system has no place for them.

## Components

Buttons follow a simple primary/secondary split. Primary buttons (`button-primary`) use `{colors.primary.500}` and shift to `{colors.primary.600}` on hover. Focus adds a 2px outline in `{colors.primary.700}`. Disabled state uses `{colors.neutral.500}` and removes the cursor affordance. Inputs (`input-default`, `input-focus`) use `{colors.surface}` backgrounds with `{colors.on-surface}` text; focus replaces the default border with a 2px `{colors.primary.500}` outline.

## Do's and Don'ts

- **Do** combine `primary.500` and `surface` for primary CTAs.
- **Do** reinforce status colors with an icon — never communicate status by hue alone.
- **Don't** mix `primary` blue with the `error` red on the same surface; they fight visually.
- **Don't** use font weight 800 or 900 — they break the system's calm feel.
- **Don't** introduce new corner radii outside the `rounded` scale.
- **Note:** `button-primary-disabled` intentionally relaxes contrast below WCAG AA — the system targets AA for active interactive elements only, mirroring Material 3 conventions for disabled controls.
