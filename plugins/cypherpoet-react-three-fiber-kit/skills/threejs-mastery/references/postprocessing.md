# Post-Processing

Two pipelines exist:

- **TSL `PostProcessing` (modern, primary).** Node-based, integrates with `WebGPURenderer` natively, also runs under `WebGLRenderer` via the TSL backend. Imports come from `three/tsl`, plus `three/addons/tsl/display/` for the built-in effect passes. This is the recommended path for new code.
- **`EffectComposer` (legacy).** The classic WebGL pipeline of `Pass` objects. Still supported, large existing ecosystem of passes. Use when porting older code or when a specific pass has no TSL equivalent yet.

> Scene/renderer setup: see [../SKILL.md#setup](../SKILL.md#setup).

**Contents:** [TSL Post-Processing](#tsl-post-processing-modern) · [EffectComposer](#effectcomposer-legacy-webgl-pipeline) · [Multi-Scene Compositing](#multi-scene-compositing) · [Render to Texture](#render-to-texture-both-pipelines) · [Performance Tips](#performance-tips) · [Common Mistakes](#common-mistakes)

## TSL Post-Processing (Modern)

### Minimal Setup

```javascript
import * as THREE from "three/webgpu";
import { pass } from "three/tsl";
import { bloom } from "three/addons/tsl/display/BloomNode.js";

const postProcessing = new THREE.PostProcessing(renderer);

const scenePass = pass(scene, camera);
const bloomPass = bloom(scenePass, /* strength */ 0.5, /* radius */ 0.4, /* threshold */ 0.85);

postProcessing.outputNode = scenePass.add(bloomPass);

// Render in the animation loop — replaces renderer.render()
renderer.setAnimationLoop(() => {
  postProcessing.render();
});
```

The `scene.environment`, `renderer.toneMapping`, and color-space settings still apply; output is automatically transformed unless you opt out (see *Custom Output Transform* below).

### Resize

```javascript
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  postProcessing.setSize(window.innerWidth, window.innerHeight);
});
```

### Built-in TSL Passes

`pass`, `mrt`, `output`, `emissive`, and `renderOutput` come from `three/tsl`. The effect passes — `bloom`, `dof`, and `fxaa` — are addons, each imported from its own module under `three/addons/tsl/display/`:

| Node | Purpose | Import from |
|------|---------|-------------|
| `pass(scene, camera)` | Render scene to a texture pass | `three/tsl` |
| `output` / `emissive` | MRT output channels for selective effects | `three/tsl` |
| `renderOutput(input)` | Apply tone mapping + sRGB conversion manually | `three/tsl` |
| `bloom(input, strength, radius, threshold)` | Unreal-style bloom | `three/addons/tsl/display/BloomNode.js` |
| `dof(input, viewZNode, focusDistance, focalLength, bokehScale)` | Depth-of-field | `three/addons/tsl/display/DepthOfFieldNode.js` |
| `fxaa(input)` | Fast approximate anti-aliasing | `three/addons/tsl/display/FXAANode.js` |

### Bloom (TSL)

```javascript
import { pass } from "three/tsl";
import { bloom } from "three/addons/tsl/display/BloomNode.js";

const scenePass = pass(scene, camera);
const bloomPass = bloom(scenePass, 0.8, 0.4, 0.85);

postProcessing.outputNode = scenePass.add(bloomPass);
```

### Selective Bloom via MRT

Use Multi-Render-Target output to bloom only emissive surfaces:

```javascript
import { pass, mrt, output, emissive } from "three/tsl";
import { bloom } from "three/addons/tsl/display/BloomNode.js";

const scenePass = pass(scene, camera);
scenePass.setMRT(mrt({ output, emissive }));

const sceneColor = scenePass.getTextureNode("output");
const emissiveTex = scenePass.getTextureNode("emissive");

const bloomPass = bloom(emissiveTex);

postProcessing.outputNode = sceneColor.add(bloomPass);
```

Set `material.emissive` and `material.emissiveIntensity` on the surfaces you want to glow. Everything else stays untouched.

### Depth of Field (TSL)

```javascript
import { pass } from "three/tsl";
import { dof } from "three/addons/tsl/display/DepthOfFieldNode.js";

const scenePass = pass(scene, camera);
const viewZ = scenePass.getViewZNode();   // dof needs scene depth (viewZ) as its 2nd argument
postProcessing.outputNode = dof(scenePass, viewZ, /* focus */ 5, /* focal length */ 0.2, /* bokeh */ 4);
```

### FXAA (TSL)

```javascript
import { pass } from "three/tsl";
import { fxaa } from "three/addons/tsl/display/FXAANode.js";

const scenePass = pass(scene, camera);
postProcessing.outputNode = fxaa(scenePass);
```

### Upscaling: FSR1 and TAAU (r184, WebGPU)

Render the scene below display resolution and reconstruct to full res — a large GPU win on heavy scenes.

**FSR1** (spatial, simplest) — AMD FidelityFX Super Resolution 1:

```javascript
import { pass } from "three/tsl";
import { fsr1 } from "three/addons/tsl/display/FSR1Node.js";

const scenePass = pass(scene, camera);     // render target sized below display res
postProcessing.outputNode = fsr1(scenePass, /* sharpness */ 0.2, /* denoise */ false);
```

**TAAU** (temporal, higher quality) reconstructs from motion. Its signature is `taau(beauty, depth, velocity, camera)`, so the scene pass must expose depth plus a `velocity` MRT channel:

```javascript
import { pass, mrt, output, velocity } from "three/tsl";
import { taau } from "three/addons/tsl/display/TAAUNode.js";

const scenePass = pass(scene, camera);
scenePass.setMRT(mrt({ output, velocity }));

postProcessing.outputNode = taau(
  scenePass.getTextureNode("output"),
  scenePass.getTextureNode("depth"),
  scenePass.getTextureNode("velocity"),
  camera
);
```

### Custom Output Transform (Tonemap Where You Need It)

Tonemapping and sRGB conversion normally happen at the end of the pipeline. To insert effects *after* tonemapping (e.g., FXAA which expects sRGB input), disable the automatic transform and apply it explicitly:

```javascript
import { pass, renderOutput } from "three/tsl";
import { bloom } from "three/addons/tsl/display/BloomNode.js";
import { fxaa } from "three/addons/tsl/display/FXAANode.js";

postProcessing.outputColorTransform = false;     // Disable auto

const scenePass  = pass(scene, camera);
const withBloom  = scenePass.add(bloom(scenePass, 0.5, 0.4, 0.85));
const transformed = renderOutput(withBloom);     // Apply tonemap + sRGB here

postProcessing.outputNode = fxaa(transformed);   // FXAA on sRGB pixels
```

### Custom Effect with a TSL Function Node

Write your own screen-space effect as a node function. Example: chromatic aberration applied to a scene pass:

```javascript
import { pass, Fn, uv, vec4 } from "three/tsl";

const scenePass = pass(scene, camera);
const sceneColor = scenePass.getTextureNode("output");

const chromaticAberration = Fn(() => {
  const amount = 0.005;
  const dir = uv().sub(0.5);
  const r = sceneColor.sample(uv().sub(dir.mul(amount))).r;
  const g = sceneColor.sample(uv()).g;
  const b = sceneColor.sample(uv().add(dir.mul(amount))).b;
  return vec4(r, g, b, 1);
});

postProcessing.outputNode = chromaticAberration();
```

Full TSL reference is in [shaders.md](./shaders.md).

## EffectComposer (Legacy WebGL Pipeline)

Use this with `WebGLRenderer` when porting existing code or when you need a pass that hasn't migrated to TSL yet.

### Minimal Setup

```javascript
import { EffectComposer }   from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass }       from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass }  from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass }       from "three/addons/postprocessing/OutputPass.js";

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

composer.addPass(new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  1.5,    // strength
  0.4,    // radius
  0.85    // threshold
));

// OutputPass handles tonemapping + sRGB conversion. Add it after effects
// that need linear input; FXAA-style passes go AFTER OutputPass.
composer.addPass(new OutputPass());

function animate() {
  composer.render();          // NOT renderer.render()
}
renderer.setAnimationLoop(animate);
```

### Resize

```javascript
function onResize() {
  const w = window.innerWidth, h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer.setSize(w, h);
}
```

### Bloom (UnrealBloomPass)

```javascript
const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  1.5,
  0.4,
  0.85
);
bloomPass.strength = 2.0;
bloomPass.radius   = 0.8;
bloomPass.threshold = 0.5;
composer.addPass(bloomPass);
```

### Selective Bloom (Two-Pass Trick)

`UnrealBloomPass` blooms everything by default. To bloom only specific objects, layer-mask the scene:

```javascript
const BLOOM_LAYER = 1;
const bloomLayer = new THREE.Layers();
bloomLayer.set(BLOOM_LAYER);

glowingMesh.layers.enable(BLOOM_LAYER);

const darkMaterial = new THREE.MeshBasicMaterial({ color: 0x000000 });
const materials = {};

function darkenNonBloomed(obj) {
  if (obj.isMesh && !bloomLayer.test(obj.layers)) {
    materials[obj.uuid] = obj.material;
    obj.material = darkMaterial;
  }
}
function restoreMaterial(obj) {
  if (materials[obj.uuid]) {
    obj.material = materials[obj.uuid];
    delete materials[obj.uuid];
  }
}

function render() {
  scene.traverse(darkenNonBloomed);
  composer.render();
  scene.traverse(restoreMaterial);
  renderer.render(scene, camera);     // Final composite over bloom
}
```

### FXAA

```javascript
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { FXAAShader } from "three/addons/shaders/FXAAShader.js";

const fxaa = new ShaderPass(FXAAShader);
fxaa.material.uniforms.resolution.value.set(
  1 / window.innerWidth,
  1 / window.innerHeight
);
composer.addPass(fxaa);
```

### SMAA

```javascript
import { SMAAPass } from "three/addons/postprocessing/SMAAPass.js";

composer.addPass(new SMAAPass(
  window.innerWidth * renderer.getPixelRatio(),
  window.innerHeight * renderer.getPixelRatio()
));
```

### SSAO

```javascript
import { SSAOPass } from "three/addons/postprocessing/SSAOPass.js";

const ssao = new SSAOPass(scene, camera, window.innerWidth, window.innerHeight);
ssao.kernelRadius = 16;
ssao.minDistance  = 0.005;
ssao.maxDistance  = 0.1;
composer.addPass(ssao);

// Output modes
ssao.output = SSAOPass.OUTPUT.Default;
// .Default | .SSAO | .Blur | .Depth | .Normal
```

### Depth of Field (Bokeh)

```javascript
import { BokehPass } from "three/addons/postprocessing/BokehPass.js";

const bokeh = new BokehPass(scene, camera, {
  focus: 10.0,
  aperture: 0.025,
  maxblur: 0.01,
});
composer.addPass(bokeh);

bokeh.uniforms.focus.value = distanceToTarget;
```

### Film / Vignette / Color Correction / Gamma

```javascript
import { FilmPass } from "three/addons/postprocessing/FilmPass.js";
composer.addPass(new FilmPass(0.35, 0.5, 648, false));

import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { VignetteShader }       from "three/addons/shaders/VignetteShader.js";
import { ColorCorrectionShader } from "three/addons/shaders/ColorCorrectionShader.js";
import { GammaCorrectionShader } from "three/addons/shaders/GammaCorrectionShader.js";

const vignette = new ShaderPass(VignetteShader);
vignette.uniforms.offset.value   = 1.0;
vignette.uniforms.darkness.value = 1.0;
composer.addPass(vignette);

const colorPass = new ShaderPass(ColorCorrectionShader);
colorPass.uniforms.powRGB.value = new THREE.Vector3(1.2, 1.2, 1.2);
colorPass.uniforms.mulRGB.value = new THREE.Vector3(1.0, 1.0, 1.0);
composer.addPass(colorPass);

composer.addPass(new ShaderPass(GammaCorrectionShader));    // Or OutputPass()
```

### Pixelation / Glitch / Halftone

```javascript
import { RenderPixelatedPass } from "three/addons/postprocessing/RenderPixelatedPass.js";
composer.addPass(new RenderPixelatedPass(6, scene, camera));

import { GlitchPass } from "three/addons/postprocessing/GlitchPass.js";
const glitch = new GlitchPass();
glitch.goWild = false;
composer.addPass(glitch);

import { HalftonePass } from "three/addons/postprocessing/HalftonePass.js";
composer.addPass(new HalftonePass(window.innerWidth, window.innerHeight, {
  shape: 1,                            // 1=dot, 2=ellipse, 3=line, 4=square
  radius: 4,
  rotateR: Math.PI / 12,
  rotateB: (Math.PI / 12) * 2,
  rotateG: (Math.PI / 12) * 3,
  scatter: 0,
  blending: 1,
  blendingMode: 1,
  greyscale: false,
}));
```

### Outline

```javascript
import { OutlinePass } from "three/addons/postprocessing/OutlinePass.js";

const outline = new OutlinePass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  scene,
  camera
);
outline.edgeStrength  = 3;
outline.edgeGlow      = 0;
outline.edgeThickness = 1;
outline.pulsePeriod   = 0;
outline.visibleEdgeColor.set(0xffffff);
outline.hiddenEdgeColor.set(0x190a05);
outline.selectedObjects = [mesh1, mesh2];

composer.addPass(outline);
```

### Custom ShaderPass

```javascript
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";

const WaveShader = {
  uniforms: {
    tDiffuse:  { value: null },          // Required — input texture
    time:      { value: 0 },
    intensity: { value: 1.0 },
  },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */`
    uniform sampler2D tDiffuse;
    uniform float time;
    uniform float intensity;
    varying vec2 vUv;
    void main() {
      vec2 p = vUv;
      p.x += sin(p.y * 10.0 + time) * 0.01 * intensity;
      gl_FragColor = texture2D(tDiffuse, p);
    }
  `,
};

const wavePass = new ShaderPass(WaveShader);
composer.addPass(wavePass);
wavePass.uniforms.time.value = clock.getElapsedTime();
```

For TSL equivalents and a fuller shader reference, see [shaders.md](./shaders.md).

## Multi-Scene Compositing

Render multiple scenes into one output (e.g., a background scene and a foreground scene with different effects):

```javascript
const bgComposer = new EffectComposer(renderer);
bgComposer.addPass(new RenderPass(bgScene, camera));

const fgComposer = new EffectComposer(renderer);
fgComposer.addPass(new RenderPass(fgScene, camera));
fgComposer.addPass(new UnrealBloomPass(/* ... */));

function animate() {
  renderer.autoClear = false;
  renderer.clear();
  bgComposer.render();
  renderer.clearDepth();
  fgComposer.render();
}
```

## Render to Texture (Both Pipelines)

```javascript
const renderTarget = new THREE.WebGLRenderTarget(512, 512);

renderer.setRenderTarget(renderTarget);
renderer.render(scene, camera);
renderer.setRenderTarget(null);

otherMaterial.map = renderTarget.texture;
```

## Performance Tips

- **Each pass is a full-screen render.** Three passes → three full screens of fragment work per frame. Budget accordingly.
- **Lower-resolution blur passes.** Bloom and DOF look the same at half resolution, run 4× faster:

```javascript
new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth / 2, window.innerHeight / 2),
  strength, radius, threshold
);
```

- **Toggle passes by device tier.** Disable expensive passes on mobile or low-end GPUs.
- **`pass.enabled = false`** suppresses a pass without rebuilding the chain.
- **FXAA is cheap** compared to `samples > 0` on the render target. Use it as the default AA in post-processing chains.
- **Render below display resolution and upscale** with FSR1 or TAAU (r184) for a large GPU win on heavy scenes — see *Upscaling* above.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Scene renders but effects don't appear | The render loop still calls `renderer.render(scene, camera)`. Use `composer.render()` (legacy) or `postProcessing.render()` (TSL) instead. |
| Blurry effects after window resize | Forgot to call `composer.setSize(width, height)` or `postProcessing.setSize(...)`. |
| Colors look too dark/bright after adding effects | Tonemapping/sRGB conversion applies once at the end. If you add a manual `GammaCorrectionShader`/`OutputPass`/`renderOutput()` somewhere else, you may be double-applying it. Pick one and disable the other (`postProcessing.outputColorTransform = false` on TSL). |
| FXAA on a tonemapped scene produces banding | FXAA must operate on sRGB pixels. Place `OutputPass()` *before* FXAA in `EffectComposer`; in TSL, do `fxaa(renderOutput(...))` with `outputColorTransform = false`. |
| Adding legacy `EffectComposer` to `WebGPURenderer` doesn't work as expected | The legacy WebGL passes don't compose cleanly with WebGPU. Migrate to the TSL `PostProcessing` pipeline. |
| `UnrealBloomPass` blooms the whole scene when you only wanted one mesh | Use the selective-bloom layer trick (legacy) or MRT-based emissive bloom (TSL). |
| Bloom looks tiled or has hard edges | Bloom resolution must match the canvas size; on resize, the legacy pass needs `bloomPass.resolution.set(width, height)`. |
| Outline pass selects update but render doesn't change | `outlinePass.selectedObjects` is a normal array — reassign or push and ensure references are still valid meshes. |

## See Also

- [shaders.md](./shaders.md) — full TSL/GLSL reference for writing custom effects.
- [textures.md](./textures.md) — render targets and depth textures.
- [lighting.md](./lighting.md) — tonemapping interacts with bloom/HDR.
