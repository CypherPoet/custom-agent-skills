# Three.js Migration Notes

Use this reference when upgrading across Three.js releases. Confirm the installed version first;
do not apply a future migration to code that still targets an earlier release.

## r185 to r186 — Ahead of the Release Feed

As of 2026-08-21, the configured Three.js release feed ends at r185 while the migration guide
already contains an r185-to-r186 section. Treat these entries as preview migration guidance until
r186 appears in the release feed:

- `Object3D` adds `dispose()`. A custom `Object3D` subclass that implements `dispose()` must call
  `super.dispose()`.
- `GTAONode.distanceExponent` and `GTAONode.distanceFallOff` are deprecated and no longer affect
  ambient occlusion.
- `BufferGeometryUtils.toTrianglesDrawMode()` changes the geometry index in place instead of
  cloning the geometry. Call `clone()` first when the caller needs the previous behavior.
- `LightProbeGrid` becomes `LightProbeGridWebGL`, and `LightProbeGridHelper` becomes
  `LightProbeGridHelperWebGL`.
- `PCFSoftShadowMap` is removed for `WebGPURenderer`. Use `PCFShadowMap`, which is soft in that
  renderer.
- `SimplifyModifier.modify()` uses a new `meshoptimizer` implementation, produces different
  simplified output, and is asynchronous.
- `Source` becomes `TextureSource`.

**Sources:** [Three.js migration guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide) ·
[Three.js releases](https://github.com/mrdoob/three.js/releases)
