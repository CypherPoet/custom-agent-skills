# Physics with Rapier

`@react-three/rapier` (v2 line, 2.2.0) wraps the Rapier physics engine (WASM) in declarative R3F components. It requires fiber `^9.0.4`, React `^19`, and three `>=0.159` — the current R3F v9 stack. This file covers the React layer: bodies, colliders, events, joints, and world access.

> Scene/Canvas setup: see [../SKILL.md](../SKILL.md). Frame-loop mechanics: [hooks.md](./hooks.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Setup](#setup) | Suspended WASM loading, world gravity and debug display, fixed or variable stepping, interpolation, collider defaults, pause control, and independent updates for demand rendering |
| [RigidBody](#rigidbody) | Physics-owned transforms, dynamic, fixed, and two kinematic movement models, material and damping properties, axis locks, sleeping, and selective continuous collision detection |
| [Colliders](#colliders) | Cost-aware automatic shapes, static-only trimeshes, half-extent primitive arguments, fixed standalone and compound colliders, and simplified mesh proxies |
| [Imperative Body API](#imperative-body-api) | One-time impulses versus persistent forces and resets, wake behavior, transform and velocity access, Rapier-to-three conversions, and type-correct kinematic driving |
| [Collision Events and Sensors](#collision-events-and-sensors) | Body-wide and collider-specific contact events, object identification and manifold data, high-frequency force handling, sleep events, and nonphysical overlap sensors |
| [Collision Filtering](#collision-filtering) | Sixteen membership and filter groups, bidirectional acceptance, body-wide application, and broad-phase pruning |
| [Joints](#joints) | Local anchors and constraints for fixed, hinge, ball-socket, slider, spring, and rope joints plus one-time motor configuration |
| [Instanced Physics](#instanced-physics) | One rigid body per rendered instance, unique keys and overrides, indexed body refs, stable instance arrays, and matching draw capacity |
| [World Access, Stepping, and Snapshots](#world-access-stepping-and-snapshots) | Raw world and WASM access, direct gravity and ray operations, deterministic paused stepping, and complete serialized restore points |
| [Attractors](#attractors) | Optional-package attraction and repulsion, static, linear, and Newtonian falloff, range, strength, and collision-group scope |
| [Character Controllers](#character-controllers) | Capsule-based kinematic movement, collision-corrected sliding, slopes, autostep, ground snapping, dynamic-body impulses, and the higher-level community controller |
| [Performance Rules](#performance-rules) | Sleeping, collider choice, rigid-body counts, event costs, and timestep guidance |
| [Common Mistakes](#common-mistakes) | Collider half-extents, type-correct kinematic movement, persistent forces and wake behavior, continuous collision detection, static-only trimeshes, physics-owned transforms, demand-loop pairing, ref timing, collider rescaling, bidirectional filtering, WASM Suspense, motor setup, and high-frequency events |
| [See Also](#see-also) | Frame-loop performance, root hooks, pointer-driven impulses, kinematic animation, stack setup, and upstream Rapier or character-controller guidance |

## Setup

```bash
npm install @react-three/rapier
```

`<Physics>` creates the world and steps it. It **suspends** while the Rapier WASM module loads — wrap it in `<Suspense>` inside `<Canvas>`.

```jsx
import { Canvas } from "@react-three/fiber";
import { Physics, RigidBody, CuboidCollider } from "@react-three/rapier";
import { Suspense } from "react";

function App() {
  return (
    <Canvas>
      <Suspense fallback={null}>
        <Physics gravity={[0, -9.81, 0]} debug={import.meta.env.DEV}>
          <RigidBody position={[0, 5, 0]}>
            <mesh>
              <boxGeometry />
              <meshStandardMaterial color="orange" />
            </mesh>
          </RigidBody>
          {/* Standalone collider = static world geometry (half-extents!) */}
          <CuboidCollider position={[0, -1, 0]} args={[10, 0.5, 10]} />
        </Physics>
      </Suspense>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} />
    </Canvas>
  );
}
```

| `<Physics>` prop | Default | Meaning |
|---|---|---|
| `gravity` | `[0, -9.81, 0]` | World gravity vector |
| `debug` | `false` | Wireframe overlay of every collider — dev only, costs performance |
| `timeStep` | `1/60` | Fixed step in seconds, or `"vary"` to step by wall-clock delta (less stable) |
| `paused` | `false` | Halts stepping; pair with `step()` from `useRapier` for manual control |
| `interpolate` | `true` | Smooths rendered transforms between fixed physics steps |
| `colliders` | `"cuboid"` | Default auto-collider shape inherited by every `RigidBody` |
| `updateLoop` | `"follow"` | `"follow"` steps inside the R3F frame loop; `"independent"` runs its own loop |

### On-Demand Rendering Pairing

With `<Canvas frameloop="demand">` the frame loop stops when nothing invalidates — and `updateLoop="follow"` stops with it, freezing physics. Pair demand mode with an independent physics loop; Rapier then invalidates frames only while bodies are awake:

```jsx
<Canvas frameloop="demand">
  <Suspense fallback={null}>
    <Physics updateLoop="independent">{/* bodies */}</Physics>
  </Suspense>
</Canvas>
```

## RigidBody

`<RigidBody>` registers its mesh children with the simulation and drives their transform. Once mounted, **physics owns the pose** — `position`/`rotation` props are the initial pose only; move bodies through the [imperative API](#imperative-body-api), never by mutating the child mesh or re-rendering new position props per frame.

| `type` | Semantics | How you move it |
|---|---|---|
| `"dynamic"` (default) | Full simulation: gravity, forces, collisions | Forces/impulses, or `setTranslation`/`setLinvel` |
| `"fixed"` | Immovable, infinite mass (floors, walls) | You don't |
| `"kinematicPosition"` | Ignores forces; you dictate pose, engine derives velocity (pushes dynamic bodies correctly) | `setNextKinematicTranslation(vec)` / `setNextKinematicRotation(quat)` per frame |
| `"kinematicVelocity"` | Ignores forces; you dictate velocity, engine integrates pose | `setLinvel(vec, wake)` / `setAngvel(vec, wake)` |

Note the split: `setNextKinematic*` is **only** for `kinematicPosition`; `kinematicVelocity` bodies are driven with `setLinvel`/`setAngvel`.

```jsx
<RigidBody
  type="dynamic"
  position={[0, 5, 0]}            // initial pose only
  colliders="hull"                // "cuboid" | "ball" | "hull" | "trimesh" | false
  mass={2}                        // overrides mass derived from collider density
  restitution={0.6}               // bounciness, 0 (none) – 1 (elastic); default 0
  friction={0.8}                  // default 0.5
  linearDamping={0.2}             // air-drag on velocity; default 0
  angularDamping={0.2}
  gravityScale={1}                // 0 = floats, negative = falls up
  canSleep={true}                 // leave true — sleeping is the main perf win
  ccd={false}                     // continuous collision detection for FAST bodies
  lockRotations={false}           // freeze all rotation (e.g. upright characters)
  lockTranslations={false}
  enabledTranslations={[true, false, true]}  // per-axis: lock Y here
  enabledRotations={[false, true, false]}    // per-axis: only yaw
  name="crate"                    // read back in collision events
>
  <mesh castShadow>
    <boxGeometry />
    <meshStandardMaterial />
  </mesh>
</RigidBody>
```

Enable `ccd` only on fast movers (bullets, pinballs) — it prevents tunneling through thin colliders but costs extra narrow-phase work.

## Colliders

### Auto-Collider Strategy

`colliders` (on `<Physics>` as the default, overridable per `<RigidBody>`) generates colliders from child mesh geometry:

| Value | Shape | Cost | Use for |
|---|---|---|---|
| `"cuboid"` | Bounding box | Cheapest | Crates, walls, platforms — prefer whenever plausible |
| `"ball"` | Bounding sphere | Cheapest | Balls, roughly spherical props |
| `"hull"` | Convex hull of vertices | Moderate | **Dynamic** complex shapes; convex approximation of anything |
| `"trimesh"` | Exact triangle mesh | Expensive | **Static concave geometry only** (terrain, level shells) — never on dynamic bodies |
| `false` | None | — | Opt out; supply explicit collider components |

Trimesh colliders are hollow (no interior volume) and have no well-defined mass — a dynamic trimesh body misbehaves and small objects tunnel into it. Dynamic + concave → decompose into several hulls or primitives instead.

### Explicit Colliders — Args Are Half-Extents

```jsx
import {
  CuboidCollider, BallCollider, CapsuleCollider,
  CylinderCollider, ConeCollider,
} from "@react-three/rapier";

<CuboidCollider args={[hw, hh, hd]} />          {/* HALF width/height/depth: a 2×1×2 box is [1, 0.5, 1] */}
<BallCollider args={[radius]} />
<CapsuleCollider args={[halfHeight, radius]} /> {/* halfHeight = cylinder section only, caps excluded */}
<CylinderCollider args={[halfHeight, radius]} />
<ConeCollider args={[halfHeight, radius]} />
```

A collider outside any `<RigidBody>` is fixed world geometry (cheapest possible ground plane). Inside a `<RigidBody colliders={false}>`, multiple colliders form a **compound body** — one rigid body, several shapes:

```jsx
<RigidBody colliders={false}>
  <mesh geometry={hammerGeometry} material={material} />
  <CuboidCollider args={[0.5, 0.2, 0.2]} position={[0, 1, 0]} />  {/* head */}
  <CapsuleCollider args={[0.5, 0.08]} position={[0, 0.3, 0]} />   {/* handle */}
</RigidBody>
```

### MeshCollider

Generate a collider from a *specific* child mesh instead of the whole body:

```jsx
import { MeshCollider } from "@react-three/rapier";

<RigidBody colliders={false}>
  <MeshCollider type="hull">
    <mesh geometry={rockGeometry} material={rockMaterial} />
  </MeshCollider>
  <mesh geometry={detailGeometry} material={detailMaterial} /> {/* visual only */}
</RigidBody>
```

Standard trick: give the body one cheap `MeshCollider type="hull"` (or primitive colliders) for a simplified proxy mesh, and render the detailed mesh with no collider at all.

## Imperative Body API

Grab the body with a ref — the type is `RapierRigidBody`. React 19: pass `ref` directly, no `forwardRef`.

```tsx
import { RigidBody, vec3, quat, euler } from "@react-three/rapier";
import type { RapierRigidBody } from "@react-three/rapier";
import { useRef } from "react";

function Jumper() {
  const body = useRef<RapierRigidBody>(null);

  const jump = () => {
    // One-time momentum kick. Second arg wakes the body — a sleeping body ignores forces otherwise.
    body.current?.applyImpulse({ x: 0, y: 8, z: 0 }, true);
    body.current?.applyTorqueImpulse({ x: 0, y: 1, z: 0 }, true);
  };

  return (
    <RigidBody ref={body} restitution={0.4}>
      <mesh onClick={jump}>
        <boxGeometry />
        <meshStandardMaterial />
      </mesh>
    </RigidBody>
  );
}
```

**`applyImpulse` vs `addForce`:** an impulse is an instantaneous momentum change (jumps, explosions, hits). `addForce` registers a **persistent** force that Rapier applies every timestep until `resetForces(true)` — calling it once is enough for a constant thruster. Calling `addForce` every frame *without resetting* stacks new forces on top of old ones and the body runs away:

```jsx
useFrame(() => {
  const b = body.current;
  if (!b) return;
  b.resetForces(true);                       // clear last frame's registration
  b.addForce({ x: 0, y: 15, z: 0 }, true);   // hover thruster
});
```

Same pairing for rotation: `addTorque(vec, wake)` / `resetTorques(true)`.

Transform and velocity accessors (getters return Rapier `{x,y,z}` structs; setters take the same plus a `wakeUp` boolean):

```jsx
const p = body.current.translation();          // { x, y, z }
const r = body.current.rotation();             // { x, y, z, w }
body.current.setTranslation({ x: 0, y: 10, z: 0 }, true);  // teleport
body.current.setRotation({ x: 0, y: 0, z: 0, w: 1 }, true);
body.current.setLinvel({ x: 0, y: 0, z: 0 }, true);        // zero velocity on respawn
body.current.setAngvel({ x: 0, y: 0, z: 0 }, true);
```

The `vec3()`, `quat()`, `euler()` helpers convert Rapier structs to `THREE.Vector3` / `THREE.Quaternion` / `THREE.Euler` so you get vector math back:

```jsx
const pos = vec3(body.current.translation());       // THREE.Vector3
const dist = pos.distanceTo(playerPosition);
```

Kinematic driving (note which setter matches which type):

```jsx
// type="kinematicPosition" — dictate the pose each frame:
useFrame(({ clock }) => {
  const t = clock.elapsedTime;
  platform.current?.setNextKinematicTranslation({ x: Math.sin(t) * 4, y: 1, z: 0 });
  platform.current?.setNextKinematicRotation(quat().setFromEuler(euler().set(0, t, 0)));
});

// type="kinematicVelocity" — dictate the velocity instead:
conveyor.current?.setLinvel({ x: 2, y: 0, z: 0 }, true);
conveyor.current?.setAngvel({ x: 0, y: 1, z: 0 }, true);
```

Prefer `kinematicPosition` + `setNextKinematic*` for moving platforms: the engine computes the implied velocity so riders get carried correctly, unlike teleporting a `fixed` body with `setTranslation`.

## Collision Events and Sensors

Handlers go on `<RigidBody>` (fires for any of its colliders) or on individual collider components (fires for that shape only):

```jsx
<RigidBody
  name="player"
  onCollisionEnter={({ manifold, target, other }) => {
    // target = this body's side; other = what it hit
    if (other.rigidBodyObject?.name === "lava") respawn();
    const contact = manifold.solverContactPoint(0);   // world-space contact point
  }}
  onCollisionExit={({ other }) => {}}
  onContactForce={({ totalForce, totalForceMagnitude }) => {
    // fires EVERY frame while contact persists — keep it light, no setState
    if (totalForceMagnitude > 400) playImpactSound();
  }}
  onSleep={() => {}}
  onWake={() => {}}
>
  <mesh>{/* ... */}</mesh>
</RigidBody>
```

`target` and `other` each expose `rigidBody` (the `RapierRigidBody`), `collider`, `rigidBodyObject` (the three.js `Object3D` — its `.name` comes from the `name` prop), and `colliderObject`. Identify *what* you hit via `other.rigidBodyObject?.name` or `other.rigidBody?.userData`.

Do not `setState` from `onContactForce` or from enter events that can fire in bursts — mutate refs or write to a store, exactly as with `useFrame` (see [performance.md](./performance.md)).

### Sensors

A collider with `sensor` detects overlap but produces no physical response — triggers, goals, pickup zones. Sensors fire `onIntersectionEnter`/`onIntersectionExit` instead of collision events:

```jsx
<RigidBody type="fixed" colliders={false}>
  <GoalPostsModel />
  <CuboidCollider
    args={[2.5, 1.5, 0.5]}
    sensor
    onIntersectionEnter={({ other }) => {
      if (other.rigidBodyObject?.name === "ball") scoreGoal();
    }}
    onIntersectionExit={() => {}}
  />
</RigidBody>
```

## Collision Filtering

`interactionGroups(memberships, filters?)` packs group data into the number the engine expects. There are 16 groups (0–15); `memberships` = which group(s) this collider belongs to, `filters` = which groups it collides with. Omitting `filters` means "collides with everything".

```jsx
import { interactionGroups } from "@react-three/rapier";

const GROUP_PLAYER = 0, GROUP_ENEMY = 1, GROUP_TERRAIN = 2, GROUP_DEBRIS = 3;

// Player: member of 0, hits enemies and terrain but ignores debris
<RigidBody collisionGroups={interactionGroups(GROUP_PLAYER, [GROUP_ENEMY, GROUP_TERRAIN])}>

// Debris: member of 3, only hits terrain (and other debris if listed)
<CuboidCollider args={[0.1, 0.1, 0.1]}
  collisionGroups={interactionGroups(GROUP_DEBRIS, [GROUP_TERRAIN])} />
```

The test is **bidirectional**: A and B collide only if A's filter contains B's membership *and* B's filter contains A's membership. Setting groups on only one of the pair is a classic silent failure. On a `<RigidBody>`, `collisionGroups` applies to all of its auto-generated colliders.

Filtering is also a perf tool — culling impossible pairs (debris×debris, enemy×enemy) shrinks the broad phase.

## Joints

Six hooks connect two body refs. Anchors are in each body's **local space**; each hook returns a ref to the created joint.

| Hook | Constraint | Args tuple |
|---|---|---|
| `useFixedJoint(a, b, data)` | Weld — no relative motion | `[anchorA, quatA, anchorB, quatB]` |
| `useRevoluteJoint(a, b, data)` | Hinge — rotation about one axis | `[anchorA, anchorB, axis]` |
| `useSphericalJoint(a, b, data)` | Ball-socket — free rotation | `[anchorA, anchorB]` |
| `usePrismaticJoint(a, b, data)` | Slider — translation along one axis | `[anchorA, anchorB, axis]` |
| `useSpringJoint(a, b, data)` | Elastic distance | `[anchorA, anchorB, restLength, stiffness, damping]` |
| `useRopeJoint(a, b, data)` | Max-distance tether | `[anchorA, anchorB, length]` |

```tsx
import { RigidBody, useRevoluteJoint } from "@react-three/rapier";
import type { RapierRigidBody } from "@react-three/rapier";
import { useRef, useEffect } from "react";

function Door() {
  const frame = useRef<RapierRigidBody>(null);
  const panel = useRef<RapierRigidBody>(null);

  // Hinge at the frame's right edge / panel's left edge, swinging about Y
  const joint = useRevoluteJoint(frame, panel, [
    [0.05, 0, 0],   // anchor in frame local space
    [-0.5, 0, 0],   // anchor in panel local space
    [0, 1, 0],      // hinge axis
  ]);

  // Motorize: configure ONCE, not per frame
  useEffect(() => {
    joint.current?.configureMotorVelocity(1.5, 2); // targetVelocity, dampingFactor
  }, [joint]);

  return (
    <>
      <RigidBody ref={frame} type="fixed">
        <mesh><boxGeometry args={[0.1, 2, 0.1]} /><meshStandardMaterial /></mesh>
      </RigidBody>
      <RigidBody ref={panel}>
        <mesh><boxGeometry args={[1, 2, 0.05]} /><meshStandardMaterial /></mesh>
      </RigidBody>
    </>
  );
}
```

Revolute and prismatic joints support motors (`configureMotorVelocity(vel, factor)`, `configureMotorPosition(pos, stiffness, damping)`) — wheels, elevators, turrets. A rope joint from a fixed anchor plus a chain of spherical joints gives you swinging ropes and ragdoll limbs.

## Instanced Physics

`<InstancedRigidBodies>` pairs one `instancedMesh` with one rigid body **per instance** — the way to simulate hundreds of similar objects without hundreds of components:

```tsx
import { InstancedRigidBodies } from "@react-three/rapier";
import type { RapierRigidBody, InstancedRigidBodyProps } from "@react-three/rapier";
import { useRef, useMemo } from "react";

const COUNT = 200;

function RubbleField() {
  const bodies = useRef<RapierRigidBody[]>(null);

  const instances = useMemo<InstancedRigidBodyProps[]>(
    () =>
      Array.from({ length: COUNT }, (_, i) => ({
        key: `rubble-${i}`,
        position: [(Math.random() - 0.5) * 10, 5 + i * 0.2, (Math.random() - 0.5) * 10],
        rotation: [Math.random(), Math.random(), Math.random()],
      })),
    []
  );

  const blastCenter = () =>
    bodies.current?.forEach((body) =>
      body.applyImpulse({ x: 0, y: 6, z: 0 }, true)
    );

  return (
    <InstancedRigidBodies ref={bodies} instances={instances} colliders="cuboid">
      <instancedMesh args={[undefined, undefined, COUNT]} count={COUNT} onClick={blastCenter}>
        <boxGeometry args={[0.4, 0.4, 0.4]} />
        <meshStandardMaterial color="tan" />
      </instancedMesh>
    </InstancedRigidBodies>
  );
}
```

Each instance entry needs a unique `key` and accepts per-instance `RigidBody` overrides (`linearVelocity`, `scale`, …). The ref resolves to an array of `RapierRigidBody` — index it for per-instance impulses. Memoize `instances`; a new array identity re-creates the bodies. The `instancedMesh` count must cover `instances.length`.

## World Access, Stepping, and Snapshots

```jsx
import { useRapier } from "@react-three/rapier";

const { world, rapier, step, setWorld, isPaused } = useRapier();
```

- `world` — the live Rapier `World`: `world.gravity = { x, y, z }` (a plain field — there is no `setGravity()` in the JS binding), `world.bodies.forEach(...)`, raw raycasts via `world.castRay(...)`.
- `rapier` — the raw Rapier WASM module (constructors, `rapier.Ray`, `rapier.World`).
- `step(dt)` — advance manually; pair with `<Physics paused>` for deterministic replays or turn-based stepping:

```jsx
function StepButton() {
  const { step } = useRapier();
  return <button onClick={() => step(1 / 60)}>advance one tick</button>;
}
```

- Snapshots serialize the entire world state — save/rewind mechanics:

```jsx
const snapshot = useRef(null);
const save = () => { snapshot.current = world.takeSnapshot(); };            // Uint8Array
const load = () => {
  if (snapshot.current) setWorld(rapier.World.restoreSnapshot(snapshot.current));
};
```

## Attractors

`Attractor` lives in the separate `@react-three/rapier-addons` package. It applies attraction (or repulsion, with negative `strength`) to dynamic bodies within `range`:

```jsx
import { Attractor } from "@react-three/rapier-addons";

<Attractor position={[0, 2, 0]} range={12} strength={4} type="linear" />
<Attractor position={[6, 0, 0]} range={8} strength={-3} />              {/* repulsor */}
<Attractor range={10} strength={9.8} type="newtonian" />                 {/* gravity-well falloff */}
```

`type` is `"static" | "linear" | "newtonian"`; `collisionGroups` scopes which bodies it affects.

## Character Controllers

Rapier ships a `KinematicCharacterController` (slide-along-walls, autostep, snap-to-ground) that you drive manually against a `kinematicPosition` body:

```tsx
import type { RapierCollider, RapierRigidBody } from "@react-three/rapier";

const bodyRef = useRef<RapierRigidBody>(null);      // <RigidBody type="kinematicPosition" ref={bodyRef}>
const colliderRef = useRef<RapierCollider>(null);   // <CapsuleCollider ref={colliderRef}>
const { world } = useRapier();
const controller = useMemo(() => {
  const c = world.createCharacterController(0.01);   // skin offset
  c.enableAutostep(0.4, 0.2, true);                   // maxStepHeight, minWidth, includeDynamic
  c.enableSnapToGround(0.4);
  c.setApplyImpulsesToDynamicBodies(true);            // push crates around
  return c;
}, [world]);

useFrame((_, delta) => {
  const body = bodyRef.current;
  const collider = colliderRef.current;
  if (!body || !collider) return;
  const desired = { x: input.x * speed * delta, y: -9.81 * delta, z: input.z * speed * delta };
  controller.computeColliderMovement(collider, desired);
  const move = controller.computedMovement();          // slide-corrected
  const pos = body.translation();
  body.setNextKinematicTranslation({
    x: pos.x + move.x, y: pos.y + move.y, z: pos.z + move.z,
  });
});
```

Use a `CapsuleCollider` on the body and `lockRotations`. For a batteries-included option, the community package `ecctrl` (pmndrs) builds a full floating-capsule character controller on `@react-three/rapier`, with `KeyboardControls` integration from drei.

## Performance Rules

- **Let bodies sleep.** Keep `canSleep` (default). Sleeping bodies cost ~nothing; a constant `addForce` or per-frame poke keeps them awake forever.
- **Primitive colliders first**: cuboid/ball ≫ capsule/cylinder ≫ hull ≫ trimesh. Approximate; nobody sees the collider.
- **Never dynamic trimesh.** Hull or compound primitives for moving concave shapes; trimesh for static level geometry only.
- **Collision groups** prune pair checks and event volume.
- **Fixed `timeStep`** (default) is more stable than `"vary"` — keep it unless you must sync physics to slow-frame wall time.
- **`ccd` sparingly** — only the fast bodies that actually tunnel.
- **`InstancedRigidBodies`** for swarms; one draw call and no per-body React overhead.
- **`debug` off in production** — the wireframe overlay rebuilds every frame.
- Idle-heavy scenes: `frameloop="demand"` + `updateLoop="independent"` render only while the simulation is active.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Colliders visibly twice as big as meshes | Collider `args` are **half**-extents: a 2×1×2 box is `CuboidCollider args={[1, 0.5, 1]}` |
| `kinematicVelocity` body never moves despite `setNextKinematicTranslation` calls | `setNextKinematic*` only works on `kinematicPosition`; drive `kinematicVelocity` with `setLinvel`/`setAngvel` |
| Body accelerates out of control with `addForce` in `useFrame` | `addForce` is persistent and stacks — call `resetForces(true)` first each frame, or use `applyImpulse` for one-time kicks |
| `applyImpulse` on a resting body does nothing | The body is asleep — pass the `wakeUp` arg: `applyImpulse(v, true)` |
| Fast projectile passes through walls | Enable `ccd` on the projectile body; keep static colliders reasonably thick |
| Dynamic body with `colliders="trimesh"` jitters, has weird mass, or lets objects sink in | Trimesh is hollow and static-only — use `"hull"` or compound primitive colliders for dynamic bodies |
| Mutating `mesh.position` inside a `RigidBody` (or animating its `position` prop) does nothing / fights physics | Physics owns the transform after mount — use `setTranslation`, forces, or a kinematic type |
| Physics freezes under `<Canvas frameloop="demand">` | Set `<Physics updateLoop="independent">` — the default `"follow"` steps inside the (stopped) frame loop |
| Crash: reading `body.current` during render | Refs are `null` until commit — touch the body only in handlers, effects, or `useFrame`, with optional chaining |
| Scaling a mesh after mount doesn't resize its collider | Auto-colliders bake scale at creation — remount (change `key`) or size explicit collider `args` yourself |
| Set `collisionGroups` on one object but it still collides with everything | Filtering is bidirectional — both colliders need memberships/filters that admit each other |
| `<Physics>` renders nothing / suspends forever outside Canvas | Mount it inside `<Canvas>` within `<Suspense>` — it suspends while the Rapier WASM loads |
| Motor joint reconfigured every frame in `useFrame` | `configureMotorVelocity` once in `useEffect`; call again only when the target changes |
| `setState` inside `onContactForce`/collision handlers tanks the frame rate | These fire per contact per frame — mutate refs or write to a store outside React, same rule as `useFrame` |

## See Also

- [performance.md](./performance.md) — frame-loop discipline, instancing, on-demand rendering.
- [hooks.md](./hooks.md) — `useFrame` priorities and `useThree`, which Rapier's update loop rides on.
- [events-and-interaction.md](./events-and-interaction.md) — pointer events for click-to-apply-impulse patterns.
- [animation.md](./animation.md) — blending animation with kinematic bodies.
- [../SKILL.md](../SKILL.md) — stack versions and setup.
- Official docs: [react-three-rapier](https://github.com/pmndrs/react-three-rapier) · [Rapier user guide](https://rapier.rs/docs/) · [ecctrl](https://github.com/pmndrs/ecctrl)
