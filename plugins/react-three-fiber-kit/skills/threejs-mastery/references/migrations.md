# Three.js Migration Notes

Use this reference when upgrading across Three.js releases. Confirm the installed version first;
do not apply a future migration to code that still targets an earlier release.

## r185 to r186 — Released September 8, 2026

r186 is the latest Three.js release as of 2026-09-15. Apply these changes when moving from r185:

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
- The `up` uniform is removed from `Sky` and `SkyMesh`; both now always assume a +Y up axis.
- The `angle`, `amount`, and `scale` constructor parameters on `DotScreenNode` and `RGBShiftNode`
  now accept numbers or node objects; numeric arguments are converted to node constants.

## r186 to r187 — Preview

As of 2026-09-15, the release feed ends at r186 while the migration guide already contains an
r186-to-r187 section. Treat these entries as preview guidance until r187 appears in the release
feed:

- `WebGPURenderer` and `WebGLRenderer` now use `WeakRef` and `FinalizationRegistry` internally.
- The XR camera's transformation and projection matrix are derived from the first subcamera, such
  as the left eye in a stereo setup.
- `WebGLRenderer.setViewport()` and `setScissor()` no longer scale by pixel ratio while a render
  target is bound.
- The `pixelSize` parameter of the `pixelationPass()` TSL function now accepts only a number; node
  objects are no longer supported.

**Sources:** [Three.js migration guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide) ·
[Three.js releases](https://github.com/mrdoob/three.js/releases)
