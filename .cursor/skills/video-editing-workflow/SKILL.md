---
name: video-editing-workflow
description: >-
  General-purpose video editing workflow using FFmpeg, mcp-video MCP server,
  and Python scripts in a Conda environment. Use when editing videos, creating
  montages, adding BGM with beat-sync, trimming clips, merging with transitions,
  or exporting final video files. Works with any project folder structure.
---

# Video Editing Workflow

## Environment Setup

### Conda Environment

Name: `video_edit`

```bash
conda create -n video_edit python=3.11 -y
conda activate video_edit
pip install mcp-video static-ffmpeg librosa numpy yt-dlp
conda install -c conda-forge liblzma    # needed by librosa
```

### FFmpeg Binaries

`static-ffmpeg` provides self-contained `ffmpeg` and `ffprobe` for all major platforms (Windows, macOS, Linux). In Python scripts, call `static_ffmpeg.add_paths()` before any FFmpeg operation so the binaries are on PATH. This avoids needing a system-level FFmpeg install.

### MCP Server Config

The `mcp-video` MCP server needs to be registered with whatever AI coding tool you use. The server definition is the same across tools — only the config file location differs:

| Tool | Config location |
|------|----------------|
| Cursor | `.cursor/mcp.json` (project-level) |
| Claude Code | `.mcp.json` (project-level) or `~/.claude/claude_desktop_config.json` (global) |
| Other MCP-compatible tools | Check the tool's documentation for MCP config path |

Server definition (adapt the JSON wrapper to your tool's format):

```json
{
  "mcp-video": {
    "command": "<CONDA_ENV_PATH>/python.exe",
    "args": ["-m", "mcp_video"],
    "env": {
      "PATH": "<CONDA_ENV_PATH>/Lib/site-packages/static_ffmpeg/bin/<PLATFORM>;%PATH%"
    }
  }
}
```

- Replace `<CONDA_ENV_PATH>` with the actual conda env path (e.g. `C:\Users\<user>\anaconda3\envs\video_edit` on Windows, `~/anaconda3/envs/video_edit` on macOS/Linux).
- Replace `<PLATFORM>` with `win32`, `darwin`, or `linux` depending on OS. On non-Windows, use `python3` instead of `python.exe` and `:` instead of `;` in PATH.
- After editing the config, restart or reload the AI tool for changes to take effect.

---

## Prerequisites — Initial Project State

Before starting any editing workflow, the project folder should have source materials organized as follows:

### Required

| Item | Description |
|------|-------------|
| **Source video folder(s)** | Raw footage in one or more subfolders (e.g. `LA/`, `Hawaii/`, or `day1/`, `day2/`). Any common format works: `.mp4`, `.mov`, `.avi`, `.mkv`, `.mts`. Mixed resolutions and codecs are handled automatically during trimming. |
| **MCP config** | `.cursor/mcp.json` (or equivalent) with `mcp-video` server registered and working. Verify by calling `video_info` on any source file. |
| **Conda env** | `video_edit` environment activated with all dependencies installed (see Environment Setup above). |

### Recommended

| Item | Description |
|------|-------------|
| **Music folder** | A `music/` subfolder containing BGM audio files (`.mp3`, `.wav`, `.flac`). If no local BGM is available, `yt-dlp` can download from YouTube — use `--ffmpeg-location` pointing to the static-ffmpeg bin directory. |
| **Flat source structure** | Keep source videos at most one level deep (e.g. `Hawaii/*.MP4`). Deeply nested folders slow down discovery and make path management harder. |

### Source Video Notes

- **Format/codec**: No specific requirements — FFmpeg handles virtually all formats. HEVC (H.265), H.264, ProRes, etc. all work.
- **Resolution**: Mixed resolutions are fine. The trim step uses `force_original_aspect_ratio=decrease` + `pad` to normalize everything to the target output resolution (e.g. 3840×2160 or 1920×1080).
- **Rotation metadata**: iPhone/smartphone MOV files often embed rotation in metadata (e.g. `-90°` for portrait). FFmpeg auto-rotates by default. If a vertical video needs to become horizontal without rotating the content, use blur-fill or pillarbox padding (see Workflow Steps §4).
- **Frame rate**: Source clips can have different frame rates (24, 30, 60fps). The trim step normalizes to a consistent rate (typically 30fps) with `-r 30`.

### What the Agent Should Do First

1. **Scan the workspace** — List all folders and video files to understand what source material exists.
2. **Probe metadata** — Run `video_info` or `ffprobe` on representative files to check resolution, duration, codec, and rotation.
3. **Confirm output specs with the user** — Before writing any script, explicitly ask:
   - **Target resolution**: 1080p (1920x1080) or 4K (3840x2160)?
   - **Target duration**: How long should the final video be?
   - **BGM**: Use an existing file from `music/`, or download a specific song?
   - **Special requests**: Specific clip ordering, vertical video handling, transitions, etc.
4. **Set processing time expectations** — Inform the user upfront how long each step will take. See the table below.
5. **Create output directories** — `output/` for intermediates, or versioned folders like `output_v2/` for iterative edits.

### Resolution Choice & Processing Time

The resolution choice has a **major impact on processing time**. Always confirm with the user before starting.

| Step | 1080p estimate | 4K estimate | Notes |
|------|---------------|-------------|-------|
| Trim each clip | ~3s | ~10-15s | Per clip, from source to encoded output |
| Re-encode concat (for xfade) | ~20s per 40s section | ~2-3 min per 40s section | Required before xfade to fix PTS gaps |
| xfade transition | ~10s | ~2-3 min | Re-encodes the overlapping region |
| Add BGM (audio only) | ~2s | ~2s | Video is copied, only audio re-encoded |
| Full pipeline (30 clips, ~90s) | **~5-8 min** | **~15-25 min** | End-to-end including all steps |
| Downscale 4K to 1080p | N/A | ~1-2 min | Post-processing if user wants both |
| Face/beauty processing | ~3-5 min | ~10-15 min | Frame-by-frame with ML model |

**Recommendation to present to users:**
- For **draft/preview** edits: use 1080p (fast iteration, fix issues quickly)
- For **final export**: render at 4K, then optionally downscale a 1080p copy
- If the user doesn't specify, **default to 1080p** and offer 4K as an upgrade after the edit is approved

### Re-edit & Iteration Workflow

When the user requests changes (swap a clip, adjust timing, etc.):
1. **Skip unchanged steps** — Check if intermediate files (trimmed clips) already exist before re-trimming. Only re-process what changed.
2. **Re-run from the changed step onward** — If clip_24 is replaced, only re-trim clip_24 and re-run merge/concat/BGM steps.
3. **Communicate which steps will re-run** — Tell the user: "Only need to re-trim 1 clip and re-merge, should take ~5 min" rather than letting them assume the full pipeline runs again.

---

## General Principles

1. **Discover before editing** — Always scan the workspace first to understand what source files exist, their resolutions, durations, and folder structure.
2. **Use variables, not hardcoded paths** — Scripts should derive source folders, output folders, and filenames dynamically from the workspace root or user-provided arguments.
3. **Consistent output format** — Always encode with `-pix_fmt yuv420p` for maximum playback compatibility. Use `-movflags +faststart` for web-friendly MP4.
4. **Incremental output** — Write intermediate files (trimmed clips, sections) to an `output/` subfolder so the pipeline can be resumed or debugged at any step.

---

## Workflow Steps

### 1. Analyze Source Videos

Scan all source folders and print metadata for every video file:

```python
import os, static_ffmpeg
static_ffmpeg.add_paths()

WORKSPACE = os.getcwd()  # or accept as argument
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.mts'}

for root, dirs, files in os.walk(WORKSPACE):
    for f in sorted(files):
        if os.path.splitext(f)[1].lower() in VIDEO_EXTS:
            filepath = os.path.join(root, f)
            # use ffprobe or mcp_video to get duration, resolution, fps
            print(f"{filepath}: ...", flush=True)
```

Alternatively, use the MCP `video_info` tool on individual files.

### 2. Extract Preview Frames

Grab a single mid-point frame from each clip for quick visual review:

```python
ffprobe_cmd = [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
ffmpeg_cmd = [FFMPEG, '-y', '-ss', str(midpoint), '-i', filepath,
              '-frames:v', '1', '-vf', 'scale=480:-1', '-q:v', '5', output_jpg]
```

Save preview frames to a `previews/` folder for visual clip selection.

### 3. Analyze BGM Beats (if beat-syncing)

Use `librosa` for BPM detection and beat timestamps:

```python
import librosa, numpy as np
y, sr = librosa.load(audio_path, sr=None)
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)
bpm = float(np.atleast_1d(tempo)[0])
beat_interval = 60 / bpm          # seconds per beat
measure_dur = 4 * beat_interval   # seconds per 4-beat measure
```

Use `measure_dur` or multiples as clip duration for beat-synced cuts.

### 3.5. Present Cut Plan for User Approval

**Before trimming**, build the full clip plan and present it to the user as a table. Do NOT proceed to encoding until the user confirms.

The table should include every clip in playback order, with:

```
| #  | Section | Source File          | Start  | Duration | Beats | Description        |
|----|---------|----------------------|--------|----------|-------|--------------------|
| 00 | INTRO   | (grid from multiple) | -      | 3.00s    | -     | 3x3 grid + title   |
| 01 | LA      | DJI_...0909_D.MP4    | 1.0s   | 3.84s    | 8     | Griffith panorama   |
| 02 | LA      | LA1.MP4              | 5.0s   | 1.92s    | 4     | Palm street driving |
| ...| ...     | ...                  | ...    | ...      | ...   | ...                |
| 27 | HI      | IMG_8887.MOV         | 1.0s   | 3.84s    | 8     | Pigeons (blur fill) |
| 28 | HI      | DJI_...0042_D.MP4    | 0.0s   | 5.00s    | -     | Sunset ending       |
|    |         |                      | TOTAL: | ~90.0s   |       |                    |
```

Also include:
- **BGM**: song name, BPM, which portion of the song will be used
- **Transitions**: where dissolves/xfades occur (e.g. "LA->HI dissolve at ~40s")
- **Special processing**: vertical video blur-fill, fade-to-black ending, etc.

This gives the user a chance to:
- Reorder clips
- Swap out clips they don't like
- Adjust start times within source videos
- Change clip durations (e.g. make a scenic shot longer)
- Remove clips entirely

Only proceed to Step 4 after the user says the plan looks good.

### 4. Trim Clips

Trim each source video to the desired duration and target resolution:

```python
[FFMPEG, '-y', '-ss', str(start_time), '-i', source,
 '-t', str(clip_duration),
 '-vf', f'scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2',
 '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
 '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart',
 output_path]
```

Set `W` and `H` based on desired output resolution (e.g. 3840x2160 for 4K, 1920x1080 for 1080p).

### 5. Create Animated Intro (optional)

Build a grid from short preview clips and overlay title text:

1. Trim N source clips to cell size
2. `hstack` inputs per row, `vstack` rows into grid
3. `drawtext` for title overlay with custom font
4. `scale` grid up to target resolution

### 6. Merge & Transition

Concatenate clips per section with `ffmpeg -f concat`, then crossfade between sections:

```python
[FFMPEG, '-y', '-i', section_a, '-i', section_b,
 '-filter_complex',
 f'[0:v][1:v]xfade=transition=fade:duration={xfade_dur}:offset={section_a_dur - xfade_dur}[v]',
 '-map', '[v]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
 '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output]
```

Common transitions: `fade`, `slideleft`, `slideright`, `dissolve`, `wipeleft`.

### 7. Add BGM

Trim BGM to match video length, apply fade-in/fade-out:

```python
audio_filter = (
    f'[1:a]atrim=0:{total_dur},'
    f'afade=t=in:st=0:d={fade_in_dur},'
    f'afade=t=out:st={total_dur - fade_out_dur}:d={fade_out_dur},'
    f'asetpts=PTS-STARTPTS[a]'
)
[FFMPEG, '-y', '-i', video, '-i', bgm,
 '-filter_complex', audio_filter,
 '-map', '0:v', '-map', '[a]',
 '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
 '-shortest', '-movflags', '+faststart', output]
```

### 8. Fade-to-Black Ending (optional)

Apply a video fade-out on the last N seconds:

```python
'-vf', f'...,fade=t=out:st={fade_start}:d={fade_duration}:color=black'
```

### 9. Compress / Downscale (optional)

Convert 4K to 1080p or other target resolution:

```bash
ffmpeg -y -i input.mp4 \
  -vf "scale=1920:1080" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a copy -movflags +faststart output_1080p.mp4
```

### 10. Validate Output

After export, run automated checks on the final video:

```python
# Essential checks (always run):
# - Duration within tolerance of target
# - Resolution matches requested (1080p or 4K)
# - Pixel format is yuv420p
# - Video codec is H.264, audio codec is AAC
# - Audio stream exists and duration matches video
# - No unexpected black frames (exclude intentional fade-to-black)

# Optional checks (informational):
# - Scene detection to estimate clip count vs expected
# - Beat-sync accuracy if using beat-matched editing
```

Report results to the user. Technical spec failures (wrong resolution, missing audio, wrong pixel format) should be fixed before delivery. Scene count and beat-sync metrics are informational only since detection accuracy is limited.

---

## Key Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| "Format not supported" on playback | Pixel format `yuv444p10le` | Always use `-pix_fmt yuv420p` |
| FFprobe not found | `static-ffmpeg` paths not loaded | Call `static_ffmpeg.add_paths()` early |
| Python print not showing during long runs | stdout buffered | Add `flush=True` to `print()` |
| Shell `&&` fails on PowerShell | PowerShell uses `;` not `&&` | Use `;` on PowerShell, `&&` on bash/zsh |
| MCP server not available after config change | Tool not reloaded | Restart or reload your AI coding tool |
| 4K processing is slow | Expected; H.264 encoding is CPU-heavy | Monitor output files for progress |
| Aspect ratio distortion | Mixed source resolutions | Use `force_original_aspect_ratio=decrease` + `pad` |
| xfade truncates output | `-c copy` concat produces PTS gaps that confuse xfade | Re-encode the concat step (`-c:v libx264`) before feeding into xfade |
| Vertical video in horizontal edit | Smartphone portrait footage with rotation metadata | Use blur-fill (`split→scale+gblur→overlay`) or pillarbox padding, NOT rotation |

---

## Recommended Project Structure

```
<project_root>/
├── .cursor/mcp.json           # MCP server config (Cursor); adapt path for other tools
│
│   ── INPUT (prepare before editing) ──
├── <location_a>/              # raw footage grouped by location, day, or theme
│   ├── DJI_*.MP4              #   camera files (any naming convention)
│   └── IMG_*.MOV              #   smartphone files (may have rotation metadata)
├── <location_b>/
│   └── ...
├── music/                     # BGM audio files (.mp3, .wav, .flac)
│
│   ── OUTPUT (generated by scripts) ──
├── previews/                  # extracted preview frames (.jpg)
├── output/                    # intermediate trimmed clips and sections
│   ├── clip_00.mp4 … clip_N.mp4
│   ├── la_section.mp4, hi_section.mp4
│   └── combined.mp4
├── <ProjectName>_Final.mp4    # final exported video (top-level for easy access)
│
│   ── SCRIPTS ──
├── analyze.py                 # video metadata scanner
├── extract_frames.py          # preview frame extractor
├── analyze_beats.py           # BGM beat analysis
└── edit_video.py              # main editing pipeline (versioned: _v2, _v3, …)
```

The key principle: **input** folders (source footage + music) are prepared by the user; **output** folders and scripts are created by the agent. Keep them clearly separated.

---

## Available MCP Tools (mcp-video)

Frequently used:
- `video_info` / `video_info_detailed` — get metadata
- `video_trim` — cut a segment
- `video_merge` — concatenate clips
- `video_add_text` — text overlay
- `video_fade` — fade in/out
- `video_resize` — scale resolution
- `video_storyboard` — generate visual storyboard (slow on 4K)
- `video_extract_frame` — grab a single frame
- `video_convert` — transcode format/codec
- `video_add_audio` — overlay audio track

For complex multi-step edits, Python scripts with direct `subprocess` FFmpeg calls give more control and explicit error handling than chaining MCP tool calls.

---

## Shell Compatibility Notes

- All `bash` code blocks in this document use Unix-style syntax (`&&`, `/`, `\` for line continuation).
- On **Windows PowerShell**: use `;` instead of `&&`, `\` path separators, and backtick `` ` `` for line continuation.
- On **Windows cmd**: use `&` instead of `&&` for unconditional chaining.
- Python scripts with `os.path` / `pathlib` are cross-platform by default — prefer scripting over raw shell commands for portability.
