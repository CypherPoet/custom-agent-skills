# Typed Allocators

Typed allocator support has two complementary pieces that can be enabled separately but are most effective in combination:

1. **Entitlement (`com.apple.security.hardened-process.hardened-heap`)** — adds extra type-isolation buckets to the allocator at runtime, regardless of compiler settings. This provides baseline type isolation.
2. **Build settings (`CLANG_ENABLE_C_TYPED_ALLOCATOR_SUPPORT`, `CLANG_ENABLE_CPLUSPLUS_TYPED_ALLOCATOR_SUPPORT`)** — the compiler communicates type information to the allocator, allowing it to do a better job isolating different types and improving protection against use-after-free vulnerabilities.

Both are enabled by default when you add the Enhanced Security capability (the entitlement as a default-ON sub-option, the build settings as cascaded settings).

## What It Does

When the build settings are enabled, the compiler tracks the intended type of memory allocations. It
automatically rewrites `malloc`, `calloc`, `realloc`, `posix_memalign`, related calls, and C++ `new`
to their type-aware equivalents when the allocated type is statically known. Combined with the
`hardened-heap` entitlement's runtime type-isolation buckets, this makes it harder for an attacker to
exploit type confusion vulnerabilities where memory allocated for one type is used as another.

## What Vulnerabilities It Mitigates

- **Type confusion** — treating a pointer to type A as a pointer to type B after allocation
- **Allocator-based exploitation** — abusing custom allocator wrappers to bypass type safety

## How to Enable

**Xcode UI:** Signing & Capabilities > Enhanced Security > check "Enable Typed Allocators"

**Build settings:**
- C code: `CLANG_ENABLE_C_TYPED_ALLOCATOR_SUPPORT = Yes`
- C++ code: `CLANG_ENABLE_CPLUSPLUS_TYPED_ALLOCATOR_SUPPORT = Yes`

**Entitlement:** `com.apple.security.hardened-process.hardened-heap`

All are enabled by default when you add the Enhanced Security capability (build settings are cascaded by `ENABLE_ENHANCED_SECURITY`; entitlement is a default-ON sub-option).

## Code Changes Required

Standard allocations whose type is statically known typically require no changes. Two cases do:

- **Runtime-selected types:** call the matching `malloc_type_*` function yourself and supply a
  `malloc_type_descriptor_v0_t` type ID.
- **Custom allocator wrappers:** remove a wrapper when possible so the compiler sees the original
  allocation. Otherwise provide a typed variant and annotate the existing wrapper with
  `_MALLOC_TYPED(typed_variant, size_argument_index)` so the compiler can propagate the descriptor.

Avoid unions that use the same storage location for either a pointer or plain data; typed allocation
can't isolate that ambiguous storage.

For details on updating custom allocators, see [Adopting type-aware memory allocation](https://developer.apple.com/documentation/xcode/adopting-type-aware-memory-allocation).

## How to Disable

**Build settings:**
- C: `CLANG_ENABLE_C_TYPED_ALLOCATOR_SUPPORT = No`
- C++: `CLANG_ENABLE_CPLUSPLUS_TYPED_ALLOCATOR_SUPPORT = No`

**Xcode UI:** Uncheck "Enable Typed Allocators" in the Enhanced Security capability.

## Platform Availability

- iOS, iPadOS, macOS, visionOS
- Available on all supported hardware

## Performance and Stability Impact

- **Performance:** Minimal overhead — type tracking is primarily a compile-time mechanism.
- **Stability:** Custom allocator wrappers may need updates. Standard allocator usage is unaffected.
