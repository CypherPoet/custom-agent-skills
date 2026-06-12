# NOTICE

The skills bundled in this plugin (everything under `skills/`) are **third-party content**, not
original work of this repository.

They appear to originate from Apple's Swift/Xcode developer skills — for example SwiftUI guidance for
the 2027 SDK, the C `-fbounds-safety` language extension, and Xcode security build settings. They are
redistributed here essentially unmodified. The only change is a minimal frontmatter normalization in
[`skills/c-bounds-safety/SKILL.md`](skills/c-bounds-safety/SKILL.md) (its `when_to_use:`/`effort:` fields
were folded into `description:` so Claude Code triggers the skill correctly); the skill bodies are
verbatim.

- **Skill content** (`skills/**`): © Apple Inc. and/or the respective original authors. All rights
  reserved by them. Provided here for convenience; the original authors' terms apply.
- **Plugin packaging** (the manifest, this NOTICE, and `README.md`): MIT, © CypherPoet.

## Tool-environment caveat

Two of the skills were written for Apple's in-Xcode coding-intelligence environment and call tools that
**do not exist in a standalone Claude Code install**:

- `device-interaction` — drives `DeviceInteractionStartSession`, `DeviceInteractionInstallAndRun`, and
  `DeviceEventSynthesize`. Its tool-driven workflow does not run outside Xcode.
- `audit-xcode-security-settings` — reads build settings via `GetTargetBuildSettings`. Its reference
  material and the `filter_build_settings.py` script still apply, but that one retrieval step degrades.

The remaining five skills (`c-bounds-safety`, `swiftui-specialist`, `swiftui-whats-new-27`,
`test-modernizer`, `uikit-app-modernization`) are knowledge/reference skills and work anywhere.

If you are the rights holder and want this redistribution changed or removed, please open an issue on
the [repository](https://github.com/CypherPoet/custom-agent-skills).
