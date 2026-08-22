# Settings and Entitlements Catalog

Complete catalog of security build settings and entitlements managed by this skill, organized by application order.

**Language relevance:** Only enable or inquire about a setting if the codebase contains code in a language the setting applies to. The Scope column indicates which languages each setting is relevant to. Do not enable clang-only settings for pure Swift codebases.

**Filtering recipe.** `scripts/filter_build_settings.py` filters `GetTargetBuildSettings` output to catalog entries; it derives its filter regex from this file at runtime by extracting backtick-quoted macro names. Adding a new setting to this catalog automatically extends the filter. See `references/reading-build-settings.md` for usage.

## Table of Contents

| Section | Covers |
|---|---|
| [Basic Clang Safety Warnings — Always Enable](#basic-clang-safety-warnings--always-enable) | Clang warning and analyzer settings that are safe to enable by default |
| [Enhanced Security — Capability](#enhanced-security--capability) | Capability and arm64e settings, cascaded compiler and allocator hardening, required and default-on entitlements, manual memory-tagging options, and deprecated entitlement removal |
| [Additional Settings — Potentially More False Positives](#additional-settings--potentially-more-false-positives) | Noisier conversions, overflow, branch, enum, and sign checks plus language-gated DriverKit, Blocks, and Objective-C diagnostics |
| [Not Auto-Enabled (Mentioned in Report)](#not-auto-enabled-mentioned-in-report) | Manual-only C and C++ bounds migrations and hardware memory tagging with their semantic, rewrite, or platform costs |
| [Default-ON Security Checkers — Audit Only](#default-on-security-checkers--audit-only) | Keychain, unchecked security returns, insecure legacy APIs, temporary files, process creation, and format-string checks to flag only when explicitly disabled |

## Basic Clang Safety Warnings — Always Enable

| Build Setting | Value | CLI Flag | Scope | Why Safe |
|---|---|---|---|---|
| `GCC_WARN_ABOUT_RETURN_TYPE` | `YES_ERROR` | `-Werror=return-type` | C/C++/ObjC/ObjC++ | Missing returns are always bugs |
| `GCC_WARN_UNINITIALIZED_AUTOS` | `YES_AGGRESSIVE` | `-Wuninitialized -Wconditional-uninitialized` | C/C++/ObjC/ObjC++ | Real bugs, rarely false |
| `CLANG_WARN_IMPLICIT_FALLTHROUGH` | `YES` | `-Wimplicit-fallthrough` | C/C++/ObjC/ObjC++ | Catches logic bugs in switch |
| `GCC_WARN_64_TO_32_BIT_CONVERSION` | `YES` | `-Wshorten-64-to-32` | C/C++/ObjC/ObjC++ | Truncation is a real issue |
| `GCC_TREAT_IMPLICIT_FUNCTION_DECLARATIONS_AS_ERRORS` | `YES` | `-Werror=implicit-function-declaration` | C/ObjC/ObjC++ | Implicit decls cause wrong return types |
| `CLANG_ANALYZER_SECURITY_FLOATLOOPCOUNTER` | `YES` | checker: `security.FloatLoopCounter` | C/C++/ObjC/ObjC++ | Low false-positive rate |
| `CLANG_ANALYZER_SECURITY_INSECUREAPI_RAND` | `YES` | checker: `security.insecureAPI.rand` | C/C++/ObjC/ObjC++ | Flags insecure random |
| `CLANG_ANALYZER_SECURITY_INSECUREAPI_STRCPY` | `YES` | checker: `security.insecureAPI.strcpy` | C/C++/ObjC/ObjC++ | Flags unsafe string ops |

## Enhanced Security — Capability

### Build Settings

| Build Setting | Value | CLI Flag / Effect | Note |
|---|---|---|---|
| `ENABLE_ENHANCED_SECURITY` | `YES` | Enables the Enhanced Security capability (build-setting + entitlements) | See `enhanced-security.md` |
| `ENABLE_POINTER_AUTHENTICATION` | `YES` | Builds for arm64e pointer signing | Set at project level; override to NO on non-arm64e targets. NO is expected on unsupported platforms. |

**Cascaded by `ENABLE_ENHANCED_SECURITY` (do not set manually):**

| Build Setting | Value | Effect | Note |
|---|---|---|---|
| `GCC_WARN_SHADOW` | `YES` | `-Wshadow` — variable declarations that shadow other variables | See `security-compiler-warnings.md` |
| `CLANG_WARN_EMPTY_BODY` | `YES` | `-Wempty-body` — empty bodies in control flow statements | See `security-compiler-warnings.md` |
| `ENABLE_SECURITY_COMPILER_WARNINGS` | `YES` | Enables additional security warnings (`-Wformat-nonliteral`, `-Warray-bounds`, etc.) | See `security-compiler-warnings.md` |
| `CLANG_CXX_STANDARD_LIBRARY_HARDENING` | `fast` / `debug` | Hardened libc++ runtime checks (fast in Release, debug in Debug — cascade handles per-configuration automatically) | Does not include unsafe buffer warnings — see `cpp-hardening.md` |
| `CLANG_ENABLE_C_TYPED_ALLOCATOR_SUPPORT` | `YES` | Communicates type information to the allocator for C code | Most effective with `hardened-heap` entitlement |
| `CLANG_ENABLE_CPLUSPLUS_TYPED_ALLOCATOR_SUPPORT` | `YES` | Communicates type information to the allocator for C++ code | Most effective with `hardened-heap` entitlement |

### Entitlements

These are managed per-target in each target's `.entitlements` file. See `enhanced-security.md` Part B for full details.

**Required (always add when enabling Enhanced Security):**

- `com.apple.security.hardened-process` = `<true/>` — main toggle for runtime protections
- `com.apple.security.hardened-process.enhanced-security-version-string` = `"2"` — selects v2 protections

**Default-ON (add when missing):**

- `com.apple.security.hardened-process.hardened-heap` — adds type-isolation buckets to the allocator at runtime; most effective with the cascaded `CLANG_ENABLE_C_TYPED_ALLOCATOR_SUPPORT` / `CLANG_ENABLE_CPLUSPLUS_TYPED_ALLOCATOR_SUPPORT` build settings (Memory Safety)
- `com.apple.security.hardened-process.dyld-ro` — marks dyld state read-only (Runtime Protections)
- `com.apple.security.hardened-process.platform-restrictions-string` = `"2"` — dyld + Mach messaging restrictions (Runtime Protections)

**Default-OFF (report state, do not auto-enable):**

- `com.apple.security.hardened-process.checked-allocations` — hardware memory tagging (MTE)
- `com.apple.security.hardened-process.checked-allocations.soft-mode` — simulated crash reports without termination
- `com.apple.security.hardened-process.checked-allocations.enable-pure-data` — tag non-pointer heap allocations
- `com.apple.security.hardened-process.checked-allocations.no-tagged-receive` — opt out of receiving tagged pointers via Mach IPC

**Deprecated (remove if present):**

- `com.apple.security.hardened-process.platform-restrictions` — superseded by `-string` variant
- `com.apple.security.hardened-process.enhanced-security-version` — superseded by `-version-string` variant

## Additional Settings — Potentially More False Positives

| Build Setting | Value | CLI Flag | Scope | Note |
|---|---|---|---|---|
| `CLANG_WARN_SUSPICIOUS_IMPLICIT_CONVERSION` | `YES` | `-Wsuspicious-implicit-conversion` | C/C++/ObjC/ObjC++ | May be noisy in some codebases |
| `CLANG_ANALYZER_SECURITY_BUFFER_OVERFLOW_EXPERIMENTAL` | `YES` | checker: `security.ArrayBound` | C/C++/ObjC/ObjC++ | Higher false-positive rate |
| `CLANG_TIDY_BUGPRONE_REDUNDANT_BRANCH_CONDITION` | `YES` | clang-tidy: `bugprone-redundant-branch-condition` | C/C++/ObjC/ObjC++ | Code quality |
| `CLANG_WARN_ASSIGN_ENUM` | `YES` | `-Wassign-enum` | C/C++/ObjC/ObjC++ | Code quality |
| `GCC_WARN_SIGN_COMPARE` | `YES` | `-Wsign-compare` | C/C++/ObjC/ObjC++ | Code quality |

### C++ / DriverKit / IOKit (only if C++ present)

| Build Setting | Value | CLI Flag |
|---|---|---|
| `CLANG_ANALYZER_OSOBJECT_C_STYLE_CAST` | `YES` | checker: `optin.osx.OSObjectCStyleCast` |

### Blocks (only if ObjC, ObjC++, or C with -fblocks present)

| Build Setting | Value | CLI Flag |
|---|---|---|
| `CLANG_WARN_COMPLETION_HANDLER_MISUSE` | `YES` | `-Wcompletion-handler` |

### ObjC-Specific (only if ObjC/ObjC++ present)

| Build Setting | Value | CLI Flag |
|---|---|---|
| `CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF` | `YES` | `-Wimplicit-retain-self` |
| `CLANG_WARN_OBJC_REPEATED_USE_OF_WEAK` | `YES` | `-Warc-repeated-use-of-weak` |

## Not Auto-Enabled (Mentioned in Report)

| Setting | User-Facing Build Setting | Why Not Auto-Enabled |
|---|---|---|
| C bounds safety | `ENABLE_C_BOUNDS_SAFETY` | Requires annotations, changes language semantics |
| C++ unsafe buffer usage | `ENABLE_CPLUSPLUS_BOUNDS_SAFE_BUFFERS` | Requires rewriting buffer patterns |
| Hardware memory tagging | `com.apple.security.hardened-process.checked-allocations` | See `hardware-memory-tagging.md` for supported hardware |

## Default-ON Security Checkers — Audit Only

These default to YES in Xcode. The skill does not actively enable them, but Phase 3 will flag them if explicitly set to NO.

| Build Setting | Value | What It Checks | Scope |
|---|---|---|---|
| `CLANG_ANALYZER_SECURITY_KEYCHAIN_API` | `YES` | Improper Keychain API usage | C/C++/ObjC/ObjC++ |
| `CLANG_ANALYZER_SECURITY_INSECUREAPI_UNCHECKEDRETURN` | `YES` | Unchecked return values from security APIs | C/C++/ObjC/ObjC++ |
| `CLANG_ANALYZER_SECURITY_INSECUREAPI_GETPW_GETS` | `YES` | Use of insecure `getpw()` and `gets()` | C/C++/ObjC/ObjC++ |
| `CLANG_ANALYZER_SECURITY_INSECUREAPI_MKSTEMP` | `YES` | Insecure use of `mkstemp()` / `mktemp()` | C/C++/ObjC/ObjC++ |
| `CLANG_ANALYZER_SECURITY_INSECUREAPI_VFORK` | `YES` | Use of `vfork()` | C/C++/ObjC/ObjC++ |
| `GCC_WARN_TYPECHECK_CALLS_TO_PRINTF` | `YES` | Format string type checking (`-Wformat`) | C/C++/ObjC/ObjC++ |
