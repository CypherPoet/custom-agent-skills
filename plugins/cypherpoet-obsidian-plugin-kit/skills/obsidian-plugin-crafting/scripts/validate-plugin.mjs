#!/usr/bin/env node
/**
 * Obsidian plugin submission preflight.
 *
 * Validates manifest.json, versions.json, and release readiness against the
 * rules in Obsidian's developer docs (docs.obsidian.md — Reference/Manifest,
 * Releasing/Submission requirements). Complements eslint-plugin-obsidianmd's
 * validate-manifest rule: this runs with no install, no network, no writes,
 * and covers versions.json + release-readiness checks the linter doesn't.
 *
 * Usage: node validate-plugin.mjs [path-to-plugin-repo]   (default: cwd)
 * Exit code: 1 if any ERROR, else 0. WARNs are review comments in waiting.
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { resolve, basename, dirname, relative } from 'node:path';

const root = resolve(process.argv[2] ?? '.');
const resolveFromRoot = (path) => resolve(root, path);
const existsInRoot = (path) => existsSync(resolveFromRoot(path));

const problems = { error: 0, warn: 0 };

const report = (level, message) => {
  problems[level] += 1;
  console.log(`[${level.toUpperCase()}] ${message}`);
};
const error = (message) => report('error', message);
const warn = (message) => report('warn', message);
const ok = (message) => console.log(`[OK] ${message}`);

const SEMVER = /^\d+\.\d+\.\d+$/;
const BASIC_LATIN = /^[\x20-\x7E]+$/;
const NON_BASIC_LATIN = /[^\x20-\x7E]/g;
// The exact set eslint-plugin-obsidianmd's validate-manifest rule permits in a
// description — narrower than Basic Latin: no parentheses, colons, or ampersands.
const DESCRIPTION_ALLOWED = /[A-Za-z0-9\s.,!?'"-]/g;
const asString = (value) => (typeof value === 'string' ? value : '');
const distinctCharacters = (text) => [...new Set(text)].join('');

// ---------- manifest.json ----------

const manifestPath = resolveFromRoot('manifest.json');
if (!existsSync(manifestPath)) {
  error(`manifest.json not found at ${manifestPath} — it must live at the repo root.`);
  finish();
}

let manifest;
try {
  manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
} catch (parseError) {
  error(`manifest.json is not valid JSON: ${parseError.message}`);
  finish();
}

// Valid JSON isn't necessarily a manifest — `null`, an array, or a bare literal
// all parse. Bail here so the field checks below can't dereference a non-object.
if (typeof manifest !== 'object' || manifest === null || Array.isArray(manifest)) {
  error('manifest.json must contain a JSON object mapping manifest fields to values.');
  finish();
}

for (const field of ['id', 'name', 'version', 'minAppVersion', 'description', 'author']) {
  if (typeof manifest[field] !== 'string' || manifest[field].length === 0) {
    error(`manifest.${field} is required and must be a non-empty string.`);
  }
}
if (typeof manifest.isDesktopOnly !== 'boolean') {
  error('manifest.isDesktopOnly is required and must be a boolean (true if any Node.js/Electron API is used).');
}

// Coerce to strings so a malformed (non-string) field is reported above without
// crashing the string checks below — a bad manifest should still get a full report.
const id = asString(manifest.id);
const name = asString(manifest.name);
const version = asString(manifest.version);
const minAppVersion = asString(manifest.minAppVersion);
const description = asString(manifest.description);

// id rules
if (id) {
  // Docs/Reference/Manifest: "The ID must contain only lowercase letters and
  // hyphens" — digits included. Some long-published plugins predate the rule.
  if (!/^[a-z-]+$/.test(id)) {
    error(`manifest.id "${id}" may only contain lowercase letters and hyphens (no digits, underscores, or capitals). Fix this before your first release — ids can't change afterward, so already-published plugins keep the id they shipped with.`);
  }
  if (/plugin$/i.test(id)) error(`manifest.id "${id}" must not end with "plugin".`);
  if (/obsidian/i.test(id)) error(`manifest.id "${id}" must not contain "obsidian".`);
  // The id-matches-folder rule governs the vault install dir (<vault>/.obsidian/plugins/<id>),
  // so only check it when root actually is one — not when pointed at a git checkout.
  const insideVaultPluginsDir = basename(dirname(root)) === 'plugins'
    && basename(dirname(dirname(root))) === '.obsidian';
  const folder = basename(root);
  if (insideVaultPluginsDir && folder !== id) {
    warn(`plugin folder "${folder}" != manifest.id "${id}" — inside a vault the folder must match the id, or callbacks like onExternalSettingsChange won't fire.`);
  }
}

// name rules
if (name) {
  if (/obsidian|obsi-|-sidian/i.test(name)) {
    error(`manifest.name "${name}" must not contain "Obsidian" or variations.`);
  }
  if (/\bplugins?\b/i.test(name)) error(`manifest.name "${name}" must not contain the word "Plugin".`);
  if (!BASIC_LATIN.test(name)) {
    error(`manifest.name "${name}" must use Basic Latin characters only (no emoji or extended Unicode).`);
  }
  // Judge punctuation on the Basic Latin subset: a non-Latin character is already
  // reported above, and counting it here too would call it "punctuation". Both
  // defects still surface on one run, so a name with each needs only one pass.
  const disallowedPunctuation = name.replace(NON_BASIC_LATIN, '').replace(/[a-zA-Z0-9 ()+\-]/g, '');
  if (disallowedPunctuation.length > 0) {
    error(`manifest.name "${name}" contains disallowed punctuation "${distinctCharacters(disallowedPunctuation)}" — only hyphens, "+", and parentheses are allowed.`);
  }
}

// version rules
if (version && !SEMVER.test(version)) {
  error(`manifest.version "${version}" must be SemVer x.y.z with no "v" prefix.`);
}
if (minAppVersion && !SEMVER.test(minAppVersion)) {
  warn(`manifest.minAppVersion "${minAppVersion}" doesn't look like an Obsidian version (x.y.z).`);
}

// description rules
if (description) {
  if (description.length > 250) error(`manifest.description is ${description.length} chars — the maximum is 250.`);
  if (!description.endsWith('.')) error('manifest.description must end with a period.');
  if (/this is a plugin/i.test(description)) error('manifest.description must not say "This is a plugin…" — start with an action statement instead.');
  // Basic Latin is too permissive here — validate-manifest rejects parentheses,
  // colons, and ampersands, which read as perfectly ordinary in a description.
  const disallowedInDescription = distinctCharacters(description.replace(DESCRIPTION_ALLOWED, ''));
  if (disallowedInDescription.length > 0) {
    warn(`manifest.description contains characters the linter's validate-manifest rule rejects ("${disallowedInDescription}") — allowed: letters, digits, whitespace, and . , ! ? ' " -`);
  }
}

// fundingUrl shape
if ('fundingUrl' in manifest) {
  const funding = manifest.fundingUrl;
  const isUrlString = typeof funding === 'string' && funding.startsWith('https://');
  const isLabelMap = typeof funding === 'object' && funding !== null && !Array.isArray(funding)
    && Object.keys(funding).length > 0
    && Object.values(funding).every((url) => typeof url === 'string' && url.startsWith('https://'));
  if (!isUrlString && !isLabelMap) {
    error('manifest.fundingUrl must be an https URL string or a non-empty object mapping labels to https URLs.');
  } else {
    // Only worth asking about a well-formed value — advising "keep it only if…"
    // about one just rejected as malformed inverts the order of the fixes.
    warn('fundingUrl present — keep it only if it points at actual financial support; otherwise remove it (submission requirement).');
  }
}

if (problems.error === 0) ok('manifest.json passes field rules.');

// ---------- versions.json ----------

const versionsPath = resolveFromRoot('versions.json');
if (existsSync(versionsPath)) {
  try {
    const versions = JSON.parse(readFileSync(versionsPath, 'utf8'));
    if (typeof versions !== 'object' || versions === null || Array.isArray(versions)) {
      error('versions.json must be an object mapping plugin version -> minAppVersion.');
    } else {
      for (const [pluginVersion, appVersion] of Object.entries(versions)) {
        if (!SEMVER.test(pluginVersion)) error(`versions.json key "${pluginVersion}" is not SemVer x.y.z.`);
        if (typeof appVersion !== 'string' || !SEMVER.test(appVersion)) {
          error(`versions.json["${pluginVersion}"] = "${appVersion}" is not a valid minAppVersion.`);
        }
      }
      // The invariant version-bump.mjs maintains: versions[manifest.version] is
      // the minAppVersion that release shipped with. A stale entry silently sends
      // older installs to the wrong release, and nothing else checks for it.
      const declaredForThisVersion = versions[version];
      if (version && typeof declaredForThisVersion === 'string' && declaredForThisVersion !== minAppVersion) {
        error(`versions.json["${version}"] is "${declaredForThisVersion}" but manifest.minAppVersion is "${minAppVersion}" — they must agree, or Obsidian offers older installs the wrong release.`);
      }
      ok(`versions.json parses (${Object.keys(versions).length} entries). Only add an entry when minAppVersion changes.`);
    }
  } catch (parseError) {
    error(`versions.json is not valid JSON: ${parseError.message}`);
  }
} else {
  warn('versions.json not found at repo root — the sample plugin\'s version-bump.mjs maintains it; older Obsidian installs use it to find a compatible release.');
}

// ---------- release readiness ----------

if (!['LICENSE', 'LICENSE.md', 'LICENSE.txt'].some(existsInRoot)) {
  error('LICENSE file missing at repo root — required by the developer policies.');
}
if (!existsInRoot('README.md')) {
  error('README.md missing at repo root — required for submission (and for network/account/payment disclosures).');
}

if (existsInRoot('main.js')) {
  let gitignore = '';
  try { gitignore = readFileSync(resolveFromRoot('.gitignore'), 'utf8'); } catch { /* no .gitignore */ }
  const ignoresMainJs = gitignore.split('\n').some((raw) => {
    const line = raw.trim().replace(/^\//, '');
    return line === 'main.js' || line === '*.js';
  });
  if (!ignoresMainJs) {
    warn('main.js exists at repo root and .gitignore does not ignore it — built output belongs in release assets, not the repo.');
  }
}

// Leftover sample-plugin code is an automatic review flag. Cover every extension
// a plugin's sources can use, not just .ts — the skill documents React and Svelte
// as supported, so .tsx and .svelte carry placeholders just as readily. Built
// output (.js/.mjs) is deliberately excluded: main.js is a bundle, and flagging it
// would just echo a warning already raised against the source it was built from.
const SOURCE_EXTENSIONS = ['.ts', '.tsx', '.mts', '.cts', '.jsx', '.svelte'];
const isSourceFile = (filename) => SOURCE_EXTENSIONS.some((ext) => filename.endsWith(ext));

// Scan the repo root (classic single-file layout, plus any siblings a split left
// there) and everything under src/ (the current sample uses src/main.ts).
const collectSourceFiles = (dir) => {
  if (!existsSync(dir)) return [];
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = resolve(dir, entry.name);
    if (entry.isDirectory()) return collectSourceFiles(full);
    return isSourceFile(entry.name) ? [full] : [];
  });
};
const rootSourceFiles = readdirSync(root, { withFileTypes: true })
  .filter((entry) => entry.isFile() && isSourceFile(entry.name))
  .map((entry) => resolveFromRoot(entry.name));

// The same placeholders the linter's sample-names rule looks for. Word-bounded so
// a file holding only MyPluginSettings isn't also reported for MyPlugin — the
// message should name the identifiers actually present. Compiled once, not per file.
const SAMPLE_PLACEHOLDERS = ['MyPlugin', 'MyPluginSettings', 'SampleModal', 'SampleSettingTab']
  .map((identifier) => ({ identifier, pattern: new RegExp(`\\b${identifier}\\b`) }));

for (const file of [...rootSourceFiles, ...collectSourceFiles(resolveFromRoot('src'))]) {
  const source = readFileSync(file, 'utf8');
  const leftovers = SAMPLE_PLACEHOLDERS.filter(({ pattern }) => pattern.test(source));
  if (leftovers.length > 0) {
    const names = leftovers.map(({ identifier }) => identifier).join(', ');
    warn(`${relative(root, file)} still contains sample-plugin placeholder names (${names}) — rename before submitting.`);
  }
}

console.log(`\nRelease reminder: the GitHub release tag must exactly match manifest.version ("${version}"), with no "v" prefix, and attach main.js, manifest.json${existsInRoot('styles.css') ? ', and styles.css' : ''}.`);

finish();

function finish() {
  console.log(`\n${problems.error} error(s), ${problems.warn} warning(s).`);
  process.exit(problems.error > 0 ? 1 : 0);
}
