---
name: expo-snack-prototyper
description: Use when the user requests a visual prototype, styling exploration, or complex UI component drafted in React Native. This skill enforces rules for generating self-contained, single-file `App.js` code that runs flawlessly in Expo Snack for immediate user review.
---
# Expo Snack Prototyper

**Verified:** 2026-07-17

When the user needs to visually verify a complex layout, animation, or rendering trick (like combining SVGs, gradients, and shadows) before implementing it into the main codebase, you should generate an **Expo Snack ready prototype**.

Expo Snack requires specific boilerplate and constraints to run smoothly without a local simulator.

## Core Directives

### 1. The Single File Rule
- All prototype code MUST belong in a single file representing `App.js`.
- Do not split the prototype into multiple components across multiple files; define any child components in the same file as `export default function App()`.

### 2. Supported Core Libraries
Expo Snack supports common Expo libraries automatically. You may freely use:
- `react-native` (View, Text, StyleSheet, Animated, etc.)
- `expo-linear-gradient`
- `react-native-svg`
- `@expo/vector-icons`

### 3. Missing Dependencies & Setup
- **Fonts:** Do NOT attempt to load custom `.ttf` or `.otf` font files via `expo-font`. Snack struggles to resolve local assets unless specifically configured in an accompanying `assets/` folder. Instead, use standard system fonts (`fontWeight: 'bold'`, `fontStyle: 'italic'`).
- **Local Images:** Do not use `require('./local-image.png')`. If an image is required for the prototype, use a remote generic high-quality URL (e.g., from Unsplash) inside `<Image source={{ uri: '...' }} />`.

### 4. Boilerplate Requirements
- You MUST `export default function App()`.
- You MUST import React: `import React from 'react';`.
- Include a dark or light environment container depending on the project's design system so the user isn't prototyping white-on-white text by accident.

### 5. Delivery Format
When delivering the code to the user, wrap it in a single markdown code block with the language set to `tsx` or `jsx`. Precede the block with instructions directing the user to copy/paste the block directly into [snack.expo.dev](https://snack.expo.dev/).

## Primary Sources

- [Expo Snack](https://snack.expo.dev/) — the runtime itself; authoritative for supported SDK versions and Snack behavior.
- [Expo changelog](https://expo.dev/changelog) — release channel; authoritative for SDK releases.
- [Expo documentation](https://docs.expo.dev/) — authoritative for API syntax and SDK package facts.
