---
name: expo-snack-prototyper
description: Use when the user requests a visual prototype, styling exploration, or complex UI component drafted in React Native. This skill enforces rules for generating self-contained, single-file `App.js` code that runs flawlessly in Expo Snack for immediate user review.
---
# Expo Snack Prototyper

When the user needs to visually verify a complex layout, animation, or rendering trick (like combining SVGs, gradients, and shadows) before implementing it into the main codebase, generate an **Expo Snack-ready prototype**.

Snack supports multi-file projects, package dependencies, and uploaded assets. This skill deliberately produces a self-contained `App.js` so the user can copy and run the prototype with minimal setup.

## Core Directives

### 1. The Single-File Rule

- All prototype code MUST belong in a single file representing `App.js`.
- Do not split the prototype into multiple components across multiple files; define any child components in the same file as `export default function App()`.

### 2. Supported Core Libraries

Snack can import supported modules from npm. Prefer these common libraries for portable prototypes:

- `react-native` (View, Text, StyleSheet, Animated, etc.)
- `expo-linear-gradient`
- `react-native-svg`
- `@expo/vector-icons`

### 3. Missing Dependencies & Setup

- **Fonts:** A one-block handoff cannot carry local `.ttf` or `.otf` assets. Use standard system fonts (`fontWeight: 'bold'`, `fontStyle: 'italic'`).
- **Local Images:** Snack accepts files and assets by drag-and-drop, but this skill's default code-only handoff does not include them. Do not use `require('./local-image.png')`; use a remote image URL inside `<Image source={{ uri: '...' }} />` when the prototype needs an image.

### 4. Boilerplate Requirements

- You MUST `export default function App()`.
- Import only the APIs the prototype uses; a blanket `import React from 'react';` is not required.
- Include a dark or light environment container depending on the project's design system so the user isn't prototyping white-on-white text by accident.

### 5. Delivery Format

When delivering the code to the user, wrap it in a single markdown code block with the language set to `tsx` or `jsx`. Precede the block with instructions directing the user to copy/paste the block directly into [snack.expo.dev](https://snack.expo.dev/).
