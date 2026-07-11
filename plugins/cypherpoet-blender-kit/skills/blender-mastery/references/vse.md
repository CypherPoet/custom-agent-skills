# Video Sequence Editor

The VSE is Blender's non-linear video editor. From script: build sequences, add strips, set transitions, and render. Most editing work is interactive (cuts, fades), but the structure can be assembled programmatically.

## Mental model

A *scene* in Blender has one VSE timeline (`scene.sequence_editor`). The timeline holds *strips* arranged on *channels* (numbered tracks, 1 to 32). Strips can be video, image, sound, color, transition, or effect.

```python
import bpy

def get_or_create_vse():
    scene = bpy.context.scene
    if scene.sequence_editor is None:
        scene.sequence_editor_create()
    return scene.sequence_editor
```

## Adding strips

```python
def add_video_strip(filepath, channel=1, frame_start=1, name=None):
    seq = get_or_create_vse()
    strip = seq.sequences.new_movie(
        name=name or filepath.split("/")[-1],
        filepath=filepath,
        channel=channel,
        frame_start=frame_start,
    )
    return strip

def add_image_strip(filepath, channel=1, frame_start=1, frame_duration=24):
    seq = get_or_create_vse()
    strip = seq.sequences.new_image(
        name=filepath.split("/")[-1],
        filepath=filepath,
        channel=channel,
        frame_start=frame_start,
    )
    strip.frame_final_duration = frame_duration
    return strip

def add_sound_strip(filepath, channel=2, frame_start=1):
    seq = get_or_create_vse()
    strip = seq.sequences.new_sound(
        name=filepath.split("/")[-1],
        filepath=filepath,
        channel=channel,
        frame_start=frame_start,
    )
    return strip
```

## Transitions

Transitions are *effect strips* placed between two video / image strips. They reference the strips on either side:

```python
def add_crossfade(seq, strip_a, strip_b, channel=3):
    """Crossfade from strip_a to strip_b. strip_b should overlap strip_a's tail."""
    fade = seq.sequences.new_effect(
        name="Crossfade",
        type='CROSS',
        channel=channel,
        frame_start=strip_b.frame_final_start,
        frame_end=strip_a.frame_final_end,
        seq1=strip_a,
        seq2=strip_b,
    )
    return fade
```

Effect types include `CROSS` (crossfade), `WIPE`, `GAUSSIAN_BLUR`, `GLOW`, `COLORMIX`, `SPEED`, `MULTICAM`, and others. The effect strip must overlap its source strips on the timeline — Blender handles the actual blend during render.

## Audio sync

The most common pain point: video frame rate vs audio sample rate. The VSE shows everything in frames, but audio is samples per second.

- Set the scene's frame rate first: `scene.render.fps = 24` (or 25, 30, 29.97, …).
- For audio-driven cuts, use the waveform display in the VSE — interactive, can't script.
- `strip.frame_offset_start` lets you trim the head; `frame_final_duration` controls overall length.

To programmatically align an audio strip to start at a specific time-in-seconds:

```python
def add_sound_at_time(filepath, seconds_in, channel=2):
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    frame = int(seconds_in * fps)
    return add_sound_strip(filepath, channel=channel, frame_start=frame)
```

## Speed / time remapping

For slow motion or speed-up of a video clip:

```python
speed = seq.sequences.new_effect(
    name="Speed",
    type='SPEED',
    channel=4,
    frame_start=video.frame_final_start,
    frame_end=video.frame_final_end,
    seq1=video,
)
speed.use_default_fade = False
speed.speed_factor = 0.5  # half-speed
```

## Render output settings (VSE)

The VSE renders the scene timeline; output settings come from `scene.render`:

```python
scene = bpy.context.scene
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'  # 'HIGH'/'PERC_LOSSLESS' for higher quality
scene.render.filepath = "/tmp/output.mp4"

scene.frame_start = 1
scene.frame_end = 240
```

## Render the timeline

VSE rendering goes through the same render pipeline. From script use the standard `bpy.ops.render.render(animation=True)` — but this should always run via the headless CLI for any non-trivial render:

```bash
blender --background project.blend --render-anim
```

## Inspecting a timeline

```python
def list_strips(seq=None):
    seq = seq or get_or_create_vse()
    for s in seq.sequences_all:
        print(f"{s.type:10s} ch{s.channel:2d}  {s.frame_final_start:>5d}-{s.frame_final_end:<5d}  {s.name}")
```

`sequences_all` is recursive (includes meta-strip contents). `sequences` is just the top level.

## When the VSE isn't the right tool

For programmatic video assembly that doesn't need Blender-specific effects, `ffmpeg` directly is usually faster. Use the VSE when:

- The composition needs render-pipeline integration (3D scene → comped clip)
- You want artist-editable transitions and color grading after assembly
- You're producing a final from scenes with layered audio + 3D + 2D mix

For pure video concatenation or trimming, drop to `ffmpeg`.

## Sources

- [Blender Manual: Video Sequencer](https://docs.blender.org/manual/en/5.1/video_editing/index.html)
- [Blender Python API: Sequence](https://docs.blender.org/api/5.1/bpy.types.Sequence.html)
- [Blender Python API: SequenceEditor](https://docs.blender.org/api/5.1/bpy.types.SequenceEditor.html)
