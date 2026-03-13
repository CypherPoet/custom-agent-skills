# expo-snack-prototyper

Generate self-contained React Native prototypes that run immediately in [Expo Snack](https://snack.expo.dev/) — no local setup required.

## Purpose

Use this skill when you need to visually verify a layout, animation, or rendering technique before integrating it into the main codebase. It enforces constraints that ensure the generated code runs in Expo Snack without modification.

## Usage

Invoke the skill when requesting a prototype:

> "Prototype a card component with a gradient background and drop shadow"
> "Show me how this animation would look before I implement it"

The skill will output a single `App.js` code block ready to paste into [snack.expo.dev](https://snack.expo.dev/).

## Examples

**Layout exploration**
> "I need to see how a sticky header with a collapsing hero image would work in React Native."
→ Skill generates a self-contained scroll view prototype with `Animated` and `expo-linear-gradient`.

**SVG + shadow combination**
> "Can you show me how SVG icons look inside a card with a shadow on Android?"
→ Skill generates a prototype using `react-native-svg` and platform-appropriate shadow styles.

## Configuration

No setup required. The skill uses only libraries pre-supported by Expo Snack:

| Library | Available |
|---------|-----------|
| `react-native` | Yes |
| `expo-linear-gradient` | Yes |
| `react-native-svg` | Yes |
| `@expo/vector-icons` | Yes |
| Custom fonts (`expo-font`) | No — use system fonts |
| Local image assets | No — use remote URIs |

## Changelog

| Version | Notes |
|---------|-------|
| 1.0 | Initial skill — single-file rule, supported library list, boilerplate requirements |
