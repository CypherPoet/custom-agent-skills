---
description: A bold, energetic design system.
version: "1.0"

colors:
  brandPrimary: "#FF3B"
  secondary-500: "rgb(120, 80, 200)"
  accent: red
  neutral:
    "100": "#F5F5F5"
    "900": "#111111"

typography:
  display:
    fontFamily: "Poppins"
    fontSize: 48
    fontWeight: 800
  body:
    fontFamily: "Poppins"
    fontSize: "16px"
    lineHeight: "24px"

spacing:
  small: "8px"
  medium: "16px"
  large: "32px"

components:
  button:
    backgroundColor: "{colors.primary}"
    textColor: "$colors.neutral.100"
    typography: "{typography.body}"
---

# Pulse

## Components

Buttons are bold and unapologetic. The primary button uses the brand color and a heavy weight to assert presence.

## Overview

Pulse is for fitness, social, and live-event apps. It should feel kinetic.

## Colors

The brand color is a bright pink-orange. Secondary is a deep purple. Accent red is reserved for emergencies.

## Typography

Display sizes are large and chunky. Body text is set in Poppins.

## Colors

A second Colors section because we forgot we already had one above.

## Layout

Generous spacing throughout.

## Shapes

Sharp corners and bold radii. We use `{rounded.dramatic}` for hero cards.
