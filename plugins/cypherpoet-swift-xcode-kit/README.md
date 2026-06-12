# cypherpoet-swift-xcode-kit

Swift and Xcode development kit: SwiftUI best practices and 2027 SDK migration, UIKit multi-window modernization, XCTest-to-Swift-Testing migration, security-hardening audits of Xcode build settings, C -fbounds-safety guidance, and on-device/simulator UI verification.

## Installation

Install via the marketplace this plugin is published to:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install cypherpoet-swift-xcode-kit@cypherpoet-toolchest
```

## Skills

| Skill | Description |
|---|---|
| [audit-xcode-security-settings](skills/audit-xcode-security-settings/SKILL.md) | Audit and progressively enable security-oriented Xcode build settings — Enhanced Security, compiler warnings, and static-analyzer checkers for C/C++/Objective-C/Swift. |
| [c-bounds-safety](skills/c-bounds-safety/SKILL.md) | Guide to the C `-fbounds-safety` language extension: the language model, pointer annotations, adoption, build settings, and runtime debugging. |
| [device-interaction](skills/device-interaction/SKILL.md) | Verify iOS app behavior on device or simulator via screenshots, UI hierarchy, and touch interactions. |
| [swiftui-specialist](skills/swiftui-specialist/SKILL.md) | Best practices and idiomatic patterns for SwiftUI — structure, data flow, environment, modifiers, animations, and localization. |
| [swiftui-whats-new-27](skills/swiftui-whats-new-27/SKILL.md) | New SwiftUI APIs, behaviors, and deprecations in the 2027 OS releases (iOS / macOS / watchOS / tvOS / visionOS 27). |
| [test-modernizer](skills/test-modernizer/SKILL.md) | Modernize test suites to use Swift Testing, or migrate them from XCTest. |
| [uikit-app-modernization](skills/uikit-app-modernization/SKILL.md) | Modernize UIKit apps for multi-window environments by replacing legacy shared-state APIs with context-appropriate alternatives. |

## Attribution

The bundled skills are third-party content — they appear to originate from Apple's Swift/Xcode developer
skills — and are redistributed under the terms described in [NOTICE](NOTICE.md). Note that
`device-interaction` and `audit-xcode-security-settings` reference Xcode-host tools that are unavailable
in a standalone Claude Code install; see the [NOTICE](NOTICE.md) for details.
