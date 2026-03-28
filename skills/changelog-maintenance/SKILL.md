---
name: changelog-maintenance
description: |
  Maintain a project's CHANGELOG.md, write user-facing release notes, and generate
  migration guides following Keep a Changelog format and Semantic Versioning. Use this
  skill whenever the user asks to update a changelog, prepare or cut a release, write
  release notes, document breaking changes, create a migration or upgrade guide, catch
  up on unreleased changes, or do a version bump. Also use when the user references
  CHANGELOG.md directly, asks "what changed since the last release", says "prep for
  release", or wants to know what version number to use next. This is for the user's
  own project changelog — not for fetching external release notes.
---

# Changelog Maintenance

A structured approach to documenting software changes so that humans — not just machines — can understand what happened and why. Based on [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## Why This Matters

A changelog exists for humans. Git logs are noisy, full of merge commits, typo fixes, and work-in-progress messages that obscure meaningful changes. A good changelog tells users and contributors what actually changed between releases, whether anything will break their code, and what they need to do about it. Structured changelogs also make it possible to automate release notes and detect version bump requirements.

## Workflow

### Phase 1: Assess the Current State

1. Check if a `CHANGELOG.md` exists in the project root. If it does, read it to understand the current format, the latest version, and what's in the Unreleased section.
2. If no changelog exists, ask the user whether to initialize one. Start with the standard header and an `## [Unreleased]` section.
3. Identify the latest tagged version by running `git tag --sort=-v:refname` and checking what's already documented.

### Phase 2: Gather Changes

1. Find the commit range: from the last documented version tag to HEAD.
2. Run `git log <last-tag>..HEAD --oneline --no-merges` to get the raw list of changes.
3. Read the actual diffs for anything ambiguous — commit messages alone don't always tell the full story.
4. If the project uses PRs, check merged PR titles and descriptions for additional context.

### Phase 3: Categorize and Write Entries

Sort each change into the appropriate category (see format below). Write entries that are:

- **Specific**: "Add retry logic to payment webhook handler" not "Bug fixes"
- **User-oriented**: Describe the impact, not the implementation detail
- **Linkable**: Reference issue/PR numbers where relevant (e.g., `([#42](link))`)

Drop changes that don't affect users — CI config tweaks, internal refactors with no behavior change, dependency bumps with no user-facing impact — unless the user specifically wants a comprehensive log.

### Phase 4: Determine the Version

If the user hasn't specified a version number, recommend one based on the changes:

- **MAJOR** (e.g., 1.0.0 → 2.0.0): Any breaking change — removed features, renamed APIs, changed default behavior, incompatible data format changes
- **MINOR** (e.g., 1.1.0 → 1.2.0): New features or capabilities that are backward-compatible
- **PATCH** (e.g., 1.1.1 → 1.1.2): Bug fixes, security patches, performance improvements with no API changes

When in doubt between minor and patch, lean toward minor if new functionality was added. Present the recommendation with reasoning and let the user confirm.

### Phase 5: Update CHANGELOG.md

1. Move entries from `## [Unreleased]` into a new version section: `## [X.Y.Z] - YYYY-MM-DD`
2. Add a fresh empty `## [Unreleased]` section at the top
3. Add a comparison link at the bottom of the file for the new version
4. Preserve all existing entries — never edit or remove prior versions

### Phase 6: Release Notes and Migration Guide (When Requested)

If the user asks for release notes or a migration guide, generate them as described in the sections below. Ask if they want these as separate files or inline in the conversation.

## CHANGELOG.md Format

Follow the [Keep a Changelog](https://keepachangelog.com/) specification:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- New feature descriptions

## [1.2.0] - 2026-03-15

### Added
- User-facing features that were introduced

### Changed
- Modifications to existing functionality

### Deprecated
- Features that will be removed in a future release

### Removed
- Features that were removed in this release

### Fixed
- Bug fixes

### Security
- Vulnerability patches and security improvements

## [1.1.0] - 2026-02-01

### Added
- ...

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/user/repo/compare/v1.0.0...v1.1.0
```

### Category Definitions

| Category       | Use For                                                        |
|----------------|----------------------------------------------------------------|
| **Added**      | New features, new capabilities, new files                      |
| **Changed**    | Modifications to existing behavior or APIs                     |
| **Deprecated** | Features marked for future removal (still functional for now)  |
| **Removed**    | Features, APIs, or files that were deleted                     |
| **Fixed**      | Bug fixes, corrections to existing behavior                    |
| **Security**   | Vulnerability patches, security-related changes                |

Only include categories that have entries — don't add empty sections.

### Formatting Rules

- Dates use ISO 8601: `YYYY-MM-DD`
- Versions are in reverse chronological order (newest first)
- Each entry is a bullet point starting with a capital letter
- The `[Unreleased]` section always sits at the top, capturing work-in-progress
- Comparison links go at the bottom of the file, one per version

## Release Notes

When generating user-facing release notes, use a friendlier format than the raw changelog. These are meant for end users who care about what's new, not the full technical history.

```markdown
# Release Notes — v2.1.0

## ✨ What's New
- Describe new features in user-friendly language

## 🔧 Improvements
- Enhancements to existing features

## 🐛 Bug Fixes
- Issues that were resolved

## ⚠️ Breaking Changes
- Anything that requires user action (with migration steps)

## 🔒 Security
- Security fixes (level of detail depends on disclosure policy)
```

Keep the language approachable — explain what changed and why it matters, not how it was implemented. Link to documentation or migration guides for breaking changes.

## Migration Guides

Generate a migration guide when a release includes breaking changes. The guide should make it straightforward for users to upgrade.

Structure:

```markdown
# Migrating from vX to vY

## Overview
Brief summary of what changed and why.

## Breaking Changes

### Change title
**Before:**
\```python
old_api_call(arg1, arg2)
\```

**After:**
\```python
new_api_call(config=Config(arg1, arg2))
\```

**Why:** Explain the motivation — performance, consistency, security, etc.

### Another change
...

## Deprecations
List anything deprecated with its removal timeline.

## Step-by-Step Upgrade
1. Numbered steps to migrate
2. Each step is concrete and actionable
3. Include commands to run where applicable
```

Place migration guides in `docs/migration/` (e.g., `docs/migration/v1-to-v2.md`) unless the project has a different convention.

## Constraints

- **No git log dumps.** The changelog is a curated summary, not a copy of `git log --oneline`. Summarize, group, and rewrite entries for clarity.
- **No vague entries.** "Bug fixes" and "Performance improvements" are not changelog entries. Be specific about what was fixed or improved.
- **Respect the existing format.** If the project already has a changelog in a different format (e.g., GNU-style, plain text), match that format rather than converting to Keep a Changelog — unless the user asks to convert.
- **Don't fabricate changes.** Every entry should trace back to an actual commit, PR, or issue. If unsure about a change, ask.

## Automation Note

This skill is designed for explicit invocation. Projects that want changelog updates to happen automatically (e.g., on every commit or PR merge) can add that instruction to their project-level `CLAUDE.md` file.
