---
name: Cobalt
version: alpha

colors:
  primary: "#0047AB"
  secondary: "#6B7280"
  surface: "#FFFFFF"
  on-surface: "#000000"
  error: "#B91C1C"
  success: "#15803D"
  warning: "#CA8A04"
  unused-accent: "#EC4899"

typography:
  text-lg:
    fontFamily: "Roboto"
    fontSize: "20px"
    fontWeight: 500
    lineHeight: "28px"
    letterSpacing: "0em"
  text-md:
    fontFamily: "Roboto"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "24px"
    letterSpacing: "0em"
  text-sm:
    fontFamily: "Roboto"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "20px"
    letterSpacing: "0em"
  headline-large:
    fontFamily: "Roboto"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: "40px"
    letterSpacing: "-0.01em"

spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  xl: "64px"

rounded:
  sm: "4px"
  md: "8px"
  lg: "16px"

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.text-md}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.text-md}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# Cobalt

## Overview

We use modern design.

## Colors

Primary is blue. Secondary is gray. Status colors handle errors, success, and warnings.

## Typography

Roboto throughout. Four sizes.

## Layout

Standard spacing scale.

## Shapes

Three corner radii.

## Components

Buttons and inputs are defined.

## Do's and Don'ts

- Don't use too many colors.
- Do keep things simple.
- Don't break the system.
