---
name: dependency-tag-check
description: Manually-triggered, read-only audit of git-tag coverage for version-constrained plugin dependencies. Confirms every pinned dependency has a satisfying `<plugin>--v<version>` tag on the source repo, so a depended-on plugin won't fail to install with `no-matching-tag`. Reports MISSING / UNSATISFIABLE / DRIFT / OK and points at `claude plugin tag` for fixes — never writes anything.
disable-model-invocation: true
---

# dependency-tag-check

Report whether every **version-constrained** plugin dependency in this repo has a git tag that can actually satisfy it. A constrained dependency on a `git-subdir` source resolves its range against tags named `<plugin-name>--v<version>` on the **source repo** (this one), and with no satisfying tag the install hard-fails with `no-matching-tag`. This skill catches that gap *before* a consumer hits it.

**Read-only** — never create or push a tag, never edit a `plugin.json`, never commit or open a PR. Just report coverage and hand off to `claude plugin tag` for anything the user wants to fix.

This is a plain procedure to run with your normal tools (`git`, `jq`, and `npx semver` for range math) — adapt as needed.

## When this matters (and when it's a clean no-op)

This repo's default is **bare-string** dependencies (`"dependencies": ["other-plugin"]`), which track latest and need no tags. Tags only enter the picture for a **constrained** dependency — an object with a `version` range, e.g. `{ "name": "other-plugin", "version": "~0.1.0" }` — which is the deliberate exception (a pinned line, e.g. holding a consumer on `0.1.x` while a `0.2.x` line develops). See [`docs/PLUGIN-CONVENTIONS.md`](../../../docs/PLUGIN-CONVENTIONS.md) → Dependencies for the full rationale.

So if the audit finds zero constrained dependencies, "nothing to check — all clean" is the **expected, correct** result, not a sign something is wrong. Say so plainly and stop.

## Procedure

1. **Collect every constrained dependency.** Walk all manifests at once; keep object-form entries that carry a `version`, drop bare strings. Record the declaring plugin, the dependency name, and the range:
   ```bash
   jq -r '
     (input_filename | split("/")[1]) as $declarer
     | .dependencies[]?
     | select(type == "object" and has("version"))
     | "\($declarer)\t\(.name)\t\(.version)"
   ' plugins/*/.claude-plugin/plugin.json
   ```
   No rows → no constrained deps. Report the clean no-op (see above) and stop.

   An entry whose `name` is **not** a local plugin under `plugins/`, or that carries a `marketplace` field pointing at a different marketplace, resolves against *that* source repo's tags — out of scope here. Note it as "external — audit in its own source repo" and move on.

2. **For each constrained dependency `<dep>` with range `<range>`, gather three facts:**
   - **Current version** of the depended-on plugin, from its own manifest:
     ```bash
     jq -r '.version' plugins/<dep>/.claude-plugin/plugin.json
     ```
   - **Tags on origin** (what consumers actually resolve against — pushed tags, not local-only ones):
     ```bash
     git ls-remote --tags origin "refs/tags/<dep>--v*" \
       | sed -E 's#.*refs/tags/##; s#\^\{\}$##' | sort -u
     ```
     Strip the `<dep>--v` prefix from each to get the bare versions.
   - **Local-only tags** (created but never pushed — they resolve for nobody):
     ```bash
     git tag --list '<dep>--v*'
     ```
     A `<dep>--v*` tag present locally but absent from the `ls-remote` output is local-only.

3. **Decide which version the range resolves to.** Use `semver` for the range math — don't eyeball it (`~0.1.0` excludes `0.2.0`, prerelease boundaries are subtle):
   ```bash
   # Highest origin tag-version that satisfies the range (empty = none satisfy):
   npx --yes semver -r "<range>" <origin-tag-version> <origin-tag-version> ...
   # Does the dep's CURRENT version satisfy the range?
   npx --yes semver -r "<range>" "<current-version>"
   ```
   `semver -r` prints the satisfying inputs in ascending order (highest last) and nothing if none qualify.

4. **Classify into one bucket per constrained dependency:**

   | Bucket | Condition | What it means |
   |---|---|---|
   | **OK** | An origin tag satisfies the range | Resolves cleanly to the highest satisfying tag. |
   | **MISSING** | No origin tag satisfies, **but the current version does** | The fix is a tag. If a satisfying tag exists *local-only*, the fix is just to push it; otherwise tag the current version. |
   | **UNSATISFIABLE** | No tag satisfies **and the current version is outside the range** | Tagging can't help — e.g. dep bumped to `0.2.0` but the dependent pins `~0.1.0`. The dependent needs a widened constraint, or you must maintain and tag an older line. |
   | **DRIFT** *(best-effort)* | A satisfying tag exists, but its committed manifest version ≠ the tag's version | A force-moved or stale tag. Verify with: `git show <dep>--v<ver>:plugins/<dep>/.claude-plugin/plugin.json` and compare `.version` to `<ver>` (needs the tag fetched locally; skip if unavailable). |

5. **Report plainly and stop.** Group by bucket; lead with anything actionable (MISSING, UNSATISFIABLE, DRIFT) and list OK / external entries briefly. For each non-OK row, name the declaring plugin, the dependency, the range, the current version, and the tags that exist. **Change nothing.** Hand off remediation per below.

## Remediation (handoff only — never run it yourself)

- **MISSING, current version satisfies the range** → once that version is on `main`, the user runs, from the depended-on plugin's directory:
  ```bash
  claude plugin tag --push   # creates <plugin>--v<version> on origin
  ```
- **MISSING, satisfying tag is local-only** → the user pushes the existing tag (`git push origin <dep>--v<version>`).
- **UNSATISFIABLE** → tagging won't fix it. The user either widens the dependent's constraint in its `plugin.json` (and republishes that plugin per the version-bump rule) or deliberately maintains an older tagged line.
- **DRIFT** → the user decides whether the tag should move; this skill only flags the mismatch.

Re-running after a fix re-confirms coverage. This skill never writes anything — it only tells the user what to run.
