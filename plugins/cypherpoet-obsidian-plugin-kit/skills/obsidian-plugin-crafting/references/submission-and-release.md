# Submission, Releases, and Developer Policies

How a plugin reaches the community directory, stays updated, and what the policies forbid. The current submission flow goes through **community.obsidian.md** — older guides (including the sample plugin's README) describe a pull request against `obsidianmd/obsidian-releases`; treat the directory flow below as current.

## Developer Policies (binding for the directory)

**Never allowed:**
- Code obfuscation.
- Client-side telemetry.
- Self-update mechanisms — no remote code loading, no updating outside GitHub releases.
- Dynamic ads loaded over the internet; static ads outside the plugin's own UI.

**Allowed with README disclosure:**
- Payment for full access (link what's paid).
- Requiring an account.
- **Network use — name each remote service and why it's needed.**
- Accessing files outside the vault.
- Static ads inside the plugin's UI.
- Server-side telemetry — must link a privacy policy.
- Closed-source components (case-by-case with the Obsidian team).

**Copyright/trademark:** a LICENSE file is required; comply with licenses of code you reuse; respect the Obsidian trademark (also enforced by the manifest `name` rules). Forks need publicly verifiable approval from the original author, or proof the author is unreachable and the plugin unmaintained ≥6 months, with credit kept.

Violations: reported via GitHub issue → 7 days to respond → escalation to the Obsidian team; removal for malicious, uncooperative, or repeatedly-broken plugins.

## Release Mechanics

1. Repo root must contain `README.md`, `LICENSE`, and `manifest.json`.
2. Build production artifacts (`npm run build`).
3. Create a GitHub release whose **tag exactly matches `manifest.json` `version` — no `v` prefix** (`1.0.1`, not `v1.0.1`).
4. Attach as release assets: `main.js`, `manifest.json`, and `styles.css` if present. Installs download these three from the release matching the manifest version; the directory reads `manifest.json` from the HEAD of your default branch.

The sample plugin's `npm version patch|minor|major` handles the manifest bump and `versions.json` ([`plugin-anatomy.md`](plugin-anatomy.md)).

### Automating with GitHub Actions

The official workflow (docs: "Release your plugin with GitHub Actions") triggers on tag push, builds, and creates a draft release with the three assets via `gh release create "$tag" --draft main.js manifest.json styles.css`. Requirements: repo Settings → Actions → "Read and write permissions"; push an annotated tag named exactly the version. You then edit notes and publish the draft.

## Submitting to the Directory

One-time, at [community.obsidian.md](https://community.obsidian.md) (Obsidian account with linked GitHub required): sidebar → Plugins → New plugin → repo URL → agree to the developer policies → Submit.

Review is largely automated. Feedback arrives on the submission; fix by pushing a **new release with an incremented version**, and the review re-runs. Pre-empt the bot with the requirements in [`plugin-anatomy.md`](plugin-anatomy.md) (manifest rules) and the checklist in [`linting-and-review.md`](linting-and-review.md); two more submission-specific rules:

- `fundingUrl` must point at actual financial support, or be removed.
- Command ids must not embed your plugin id (auto-prefixed).

**After acceptance, updates need no re-submission** — each new GitHub release (with the tag = version rule) reaches users through the in-app updater. `minAppVersion` honesty matters here: users on older apps get the newest release their app supports via `versions.json`.

## Beta Testing

There's no official beta channel. The community standard is [BRAT](https://github.com/TfTHacker/obsidian42-brat) (`obsidian42-brat`): beta testers add your repo in BRAT, which installs from pre-release GitHub releases — useful for validating fixes with real vaults before a directory-visible release.
