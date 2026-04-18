---
name: video-annotation-workflow
description: >-
  Annotate an existing screen-recorded or demo video with dynamic highlight
  boxes, captions, and (optionally) zoom regions to explain a UI walk-through.
  Use when the user wants to add callouts, dim-out overlays, labeled bounding
  boxes, or step-by-step descriptions on top of an existing video — typically
  product demos, tutorials, feature walkthroughs, or screen recordings. Works
  on any input video, drives a parallel OpenCV + Pillow renderer, and includes
  a coordinate-grid debug mode for fast box-alignment iteration with the user.
---

# Video Annotation Workflow

This skill is for **annotating an existing video** (not cutting/joining clips —
for that, see `video-editing-workflow`). The output is the same video with:

- Semi-transparent dim layer outside the focus area
- Rounded orange highlight box around the UI element being explained
- Caption pill above the box describing what the user is doing
- Smooth fade in/out and keyframe-interpolated box motion
- Optional debug grid overlay for measuring/aligning boxes

The workflow runs in three phases: **alignment** (lock the segment timeline +
captions), **debug-grid iteration** (visually correct box coordinates with the
user), then **clean render**.

---

## Environment Setup

Reuse the `video_edit` conda environment from `video-editing-workflow`. Add
OpenCV + Pillow if not already present:

```bash
conda activate video_edit
pip install opencv-python pillow numpy static-ffmpeg
```

The renderer uses `cv2.VideoCapture` for per-chunk decoding, Pillow for
text/box drawing (anti-aliased + alpha), and a final `ffmpeg` pass for
concat + H.264 re-encode. `static-ffmpeg` provides cross-platform binaries.

---

## Phase 0 — Requirements Gathering (do BEFORE writing any code)

Before generating any annotation script, **explicitly confirm** these items
with the user. Misalignment here causes the most rework downstream.

### Required from the user

| Item | Why it matters |
|------|---------------|
| **Source video file** | Path to the input `.mp4`/`.mov`. Confirm the file exists and probe with `ffprobe` for resolution, fps, duration. |
| **Output file name** | Where to write the final annotated video (e.g. `Demo - Annotated.mp4`). |
| **Caption language** | English / Chinese / both. Default to English unless told otherwise. |
| **Tone of captions** | Action-oriented imperative ("Click Generate"), descriptive ("AI performs research"), or neutral ("Profile Quality Assessment"). Pick one and use it consistently. |
| **Visual style** | Highlight color (default orange `RGB(230,160,40)`), label background (default dark slate), corner radius, fade duration. Defaults are fine for most demos. |
| **Whether to zoom** | Recommend starting **without zoom**. Box alignment is hard enough — adding zoom multiplies the failure modes. Add zoom only after boxes are locked. |

### Have the user walk through the video first

Ask the user to **scrub through the source video and call out the segments
they want annotated**, in roughly this format:

```
00:00 - 00:02   Click Chat button (top-right) to open AI Assistant
00:03 - 00:07   Type research query in chat input
00:08 - 00:20   AI performs web search + shows corporate profile
...
```

Lock down the **segment list (start, end, label)** before touching coordinates.
Coordinates are easy to fix later; reorganizing segments after rendering
wastes time.

### Source video prep checklist

```
- [ ] Source video path confirmed and ffprobe-able
- [ ] Output resolution and fps captured (pin these as constants)
- [ ] Full segment list (start, end, label) drafted and approved by user
- [ ] Caption language + tone agreed
- [ ] Zoom: deferred until boxes are locked
- [ ] Output filename agreed
```

Only proceed to Phase 1 once all six are checked.

---

## Phase 1 — Build Initial Annotation Script

Use `scripts/annotate_template.py` as the starting point. Copy it to the
project root (e.g. `annotate_demo.py`) and customize:

1. **Constants block** — set `VIDEO_IN`, `FINAL_OUT`, `W`, `H`, `FPS` from
   `ffprobe`. Pin `FPS` to the source's actual value (typically 25, 30, or
   60). Mismatches cause visible stutter.
2. **`SEGMENTS` list** — one dict per annotation segment:

   ```python
   {"start": 19.8, "end": 22.2,
    "label": "One-click apply research to KYC draft",
    "zoom": None,
    "keyframes": [
        (19.8, (1762, 173, 1825, 200)),
        (20.5, (1762, 173, 1825, 200)),
        (21.5, (1762, 173, 1825, 200)),
    ]},
   ```

   - `start`, `end` are in seconds.
   - `label` is the caption pill text.
   - `keyframes` is a list of `(t_seconds, (x1, y1, x2, y2))` tuples. The
     renderer linearly interpolates with ease-in-out between consecutive
     keyframes, so you only need anchors at moments where the box should
     change position/size. **For static boxes, repeat the same coordinates
     at start and end** — this avoids accidental drift if the renderer is
     ever changed to extrapolate.
3. **Initial coordinates** — give your best guess. Don't burn time
   measuring pixels yet; the debug-grid phase will fix everything.

For the first render, **always set `DEBUG_GRID = True`** so the user can
review with the coordinate overlay.

### Estimating processing time

| Source length | Render time (8-core M-class CPU, 1080p) |
|--------------|-----------------------------------------|
| 1 min  | ~10 s |
| 3 min  | ~30 s |
| 5 min  | ~60 s |
| 10 min | ~2 min |

Tell the user upfront. Renders are fast enough that 5-10 iteration cycles
are practical in a single session.

---

## Phase 2 — Debug-Grid Iteration Loop (the core of this skill)

This is the workflow that makes annotation tractable. Without the grid, you
end up extracting frames and probing pixels, which is slow and the user
can't give precise feedback ("a bit to the left" — by how much?).

### How it works

When `DEBUG_GRID = True`, the renderer overlays:

- **Cyan grid lines**: faint every 50px, brighter every 100px
- **Cyan axis labels** along the top (x) and left (y) edges, every 100px
- **Yellow corner labels** at each of the 4 corners of the active box,
  showing the exact `(x, y)` coordinates
- **Yellow timestamp** in the top-right corner, formatted `t=66.00s`

The script writes to a separate file (e.g.
`Demo - Annotated (DEBUG GRID).mp4`) so the clean version isn't clobbered.

### Iteration protocol

1. **Render with grid on**, share the output path with the user.
2. **User watches the video** and reports adjustments using one of these
   formats:
   - **Absolute coordinates** (preferred): "at t=66, change to (605, 95, 1395, 620)"
   - **Relative deltas**: "at t=66, right edge +80, bottom -30"
   - **Whole-segment fixes**: "make t=130-145 a fixed box at (500, 280, 1900, 880)"
   - **Add/remove keyframes** for dynamic boxes: "the panel slides in at
     t=84.36, finish the transition by t=85.0"
3. **Apply edits** to the `SEGMENTS` list. Use targeted `StrReplace` edits,
   not full file rewrites — this preserves diff clarity for the user.
4. **Re-render with grid still on** (~30-60 s for a typical demo).
5. Repeat until the user signs off on every segment.

### Tips for the iteration loop

- **Use the box's 4 corner labels in the grid as the source of truth.** They
  show the exact current coordinates so the user can compute deltas
  themselves and tell you the new numbers directly.
- **Do not pixel-probe in this phase.** The user is now your measurement
  tool. Pixel probing is only useful in Phase 1 to seed initial guesses,
  or in Phase 4 if the user can't easily eyeball a coordinate.
- **For dynamic boxes (panels sliding in, modals appearing)**, ask the user
  for the **transition start timestamp** down to ~0.05s precision. They can
  scrub the source video and read it directly. Add a keyframe at the
  start-of-transition (old box still in place) and another at the
  end-of-transition (new box position) so the interpolation matches the
  actual UI animation.
- **Batch related fixes**: if the user lists 10 segments to adjust, apply
  all 10 in one edit pass and re-render once.

### Phase 2 done = user explicitly says "looks good, generate the clean version"

Never assume sign-off. Always wait for the explicit confirmation before
flipping the grid off.

---

## Phase 3 — Clean Final Render

Once the user signs off:

1. Set `DEBUG_GRID = False`.
2. Re-run the script. Output goes to the clean file (e.g.
   `Demo - Annotated.mp4`).
3. Tell the user the output path and that grid is now off.

If the user spots one more issue after seeing the clean render, **flip the
grid back on for that adjustment** rather than trying to eyeball it without
the grid. The few extra seconds for one debug render save much more time
than blind trial and error.

---

## Phase 4 — Optional Zoom Pass

Only attempt zoom after every box is aligned in the no-zoom version.

For each segment that should zoom:

```python
{"start": ..., "end": ...,
 "label": ...,
 "zoom": (zx1, zy1, zx2, zy2),   # region to zoom into (source coords)
 "keyframes": [...]},
```

The template includes a `compute_zoom_viewport()` helper that smoothly
interpolates from the full frame to the zoom region. Re-enable the
`if zoom_region is not None:` block in `annotate_frame()` (it's commented
out by default).

After zoom is added, redo a Phase-2 grid pass — zoom changes the apparent
box positions, and some boxes that looked perfect at full frame may need
nudging.

---

## Script Architecture Reference

The template script structure:

```
scripts/annotate_template.py
├── Constants (paths, dimensions, fps, colors, debug flag)
├── SEGMENTS = [ ... ]                  # data — edit this constantly
├── ease_in_out(t)                      # smoothing for fades + interpolation
├── lerp_box(keyframes, t)              # piecewise-linear box interpolation
├── get_active_segment(t)               # which segment is live at time t
├── get_box_at_time(seg, t)             # interpolated box for a segment
├── get_segment_alpha(t, seg)           # fade-in/out alpha
├── compute_zoom_viewport(...)          # zoom math (optional)
├── draw_debug_grid(frame, t, box)      # grid + corner labels overlay
├── annotate_frame(frame, t, font)      # the main per-frame render
├── process_chunk(args)                 # mp worker: decode + annotate + write
└── main()                              # split into N chunks, mp pool, ffmpeg concat
```

### Key implementation choices (don't change without reason)

- **`mp.Pool` over `mp.cpu_count()` chunks**: empirically fastest. Each
  worker decodes its own frame range with `cv2.VideoCapture`, annotates,
  and writes to a temporary `mp4v` file. After all workers finish, a
  single `ffmpeg -f concat -c:v libx264` pass produces the final H.264
  output.
- **`mp4v` for intermediates, H.264 only for the final concat**: `mp4v`
  encoding is dramatically faster, and re-encoding once at the end avoids
  having every worker pay the H.264 cost.
- **Pillow over OpenCV for text/boxes**: anti-aliased text, true alpha
  compositing, and `rounded_rectangle` are all native in Pillow. OpenCV's
  text rendering is ugly and lacks alpha.
- **Linear interpolation between keyframes with `ease_in_out` smoothing**:
  natural-looking motion without requiring per-frame coordinates. The
  user only specifies coordinates at moments of change.

---

## Captions — Style Guide

A consistent voice across captions makes the video feel professional.

- **Length**: aim for 4-8 words. Long captions wrap awkwardly and obscure
  the UI.
- **Tense and voice**: present-tense, action-oriented ("Click Chat to open
  AI Assistant", "Wealth journey chronology generated").
- **Avoid generic words**: "this section", "this thing", "do something" —
  always name the specific UI element or action.
- **Reuse vocabulary**: if you've called it the "Profile Draft" once,
  don't switch to "the draft panel" later. Pick a name and stick with it.
- **Punctuation**: no trailing periods. Captions are labels, not sentences.

When the user wants a wording change, use a targeted `StrReplace` on just
the `"label"` field — never re-render the whole `SEGMENTS` block.

---

## Common Pitfalls and How to Avoid Them

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Initial guess coordinates are wildly off | Box covers the wrong UI region in first render | Don't try to be precise in Phase 1. Get the segment list right, render with grid, fix in Phase 2. |
| Box covers a UI element that disappears mid-segment | Highlight stays visible after the user closes a modal / clicks away | Shorten the segment's `end` time. Frame-by-frame check the source if needed (`ffmpeg -ss T -frames:v 1`). |
| Sliding panel "snaps" instead of sliding smoothly | Single keyframe at the new position, large gap from previous keyframe | Add a keyframe at the **moment the animation starts** (with the OLD position) and another at the **moment it ends** (with the NEW position). Spacing of ~0.4-0.7s usually matches typical UI transitions. |
| Caption overlaps with the box's content | Default placement puts label above the box, but the box starts at y≈0 | The renderer auto-flips to below if there's no room above; if both are bad, it places it inside the box. Verify in the debug render and nudge `by1` down if needed. |
| Render is much slower than expected | `DEBUG_GRID = True` (grid adds ~50% overhead) or 4K source video | Confirm grid is off for the final render. For 4K sources, render at 1080p first by adding a `scale` filter to the per-chunk pipeline. |
| Box drifts during a "static" segment | Only one keyframe given; renderer extrapolates | Always provide keyframes at both `start` and `end` of static segments with the same coordinates. |
| Pixel-format playback errors | Default `mp4v` intermediate isn't web-compatible | The final `ffmpeg` pass uses `-pix_fmt yuv420p` — don't skip this step. |
| User says "the framing is off everywhere" | Underlying source video resolution doesn't match `W, H` constants | Re-probe with `ffprobe` and update `W, H, FPS` constants. All coordinates are in source-pixel space. |

---

## Recommended Project Structure

```
<project_root>/
├── source_video.mp4                                # input (user-provided)
├── annotate_demo.py                                # the rendering script
├── output/                                         # chunk_*.mp4 intermediates (auto-cleaned)
├── previews/probe/                                 # ad-hoc frames for one-off pixel checks
├── Demo - Annotated.mp4                            # clean final output
└── Demo - Annotated (DEBUG GRID).mp4               # grid-overlay version (kept during iteration)
```

The two output files coexist — the clean version is what gets shared, the
debug version stays around for any future re-alignment.

---

## End-to-End Checklist

```
Phase 0 — Alignment
- [ ] Source video probed (resolution, fps, duration)
- [ ] Segment list (start, end, label) drafted and user-approved
- [ ] Caption language + tone agreed
- [ ] Output filename agreed
- [ ] Zoom deferred to Phase 4

Phase 1 — Initial Script
- [ ] Template copied + constants set from source video
- [ ] SEGMENTS populated with rough coordinate guesses
- [ ] DEBUG_GRID = True
- [ ] First render completes successfully

Phase 2 — Grid Iteration
- [ ] User reviews grid render and gives coordinate feedback
- [ ] Edits applied via targeted StrReplace, not full rewrites
- [ ] Iteration loop continues until explicit user sign-off

Phase 3 — Clean Render
- [ ] DEBUG_GRID = False
- [ ] Clean version rendered and delivered to user

Phase 4 (optional) — Zoom
- [ ] Zoom regions added per segment
- [ ] Zoom block uncommented in annotate_frame()
- [ ] Phase 2 grid pass repeated to re-align boxes under zoom
```

---

## Reference Material

- Starter script: [`scripts/annotate_template.py`](scripts/annotate_template.py) — drop-in renderer, edit CONSTANTS and SEGMENTS only
- Worked example: [`examples/kyc_demo_segments.py`](examples/kyc_demo_segments.py) — real 4:40 KYC product demo with ~25 segments; illustrates static boxes, growing boxes, the hold-then-snap pattern for UI layout shifts, very short modal highlights, and panel recentering
- Companion skill (cutting/joining clips, BGM, transitions): `video-editing-workflow`
