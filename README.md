# Video Editing Skills

A collection of reusable [Cursor Skills](https://cursor.com/docs/agent/skills) for AI-assisted video editing workflows. Drop these skills into any project and let your coding agent (Cursor, Claude Code, or any MCP-compatible tool) drive the editing pipeline end-to-end.

Each skill is a self-contained markdown file (plus optional template scripts and worked examples) that teaches the agent how to perform a specific class of video tasks: cutting and joining clips, beat-syncing music, annotating screen recordings with highlight boxes, etc.

---

## Available Skills

| Skill | What it does | When to use |
|-------|--------------|-------------|
| [`video-editing-workflow`](.cursor/skills/video-editing-workflow/SKILL.md) | Cuts, trims, and joins source footage; builds montages; adds BGM with beat-sync; applies transitions; exports to a chosen resolution. | Travel videos, montages, multi-clip edits with music. |
| [`video-annotation-workflow`](.cursor/skills/video-annotation-workflow/SKILL.md) | Annotates an existing video with dynamic highlight boxes, captions, and dim-out overlays. Includes a coordinate-grid debug mode for fast box-alignment iteration with the user. | Product demos, tutorials, feature walkthroughs, screen-recording explainers. |

Both skills share the same conda environment (`video_edit`) and FFmpeg binaries (`static-ffmpeg`).

---

## Installing the Skills in Your Project

Cursor and other agentic tools auto-discover skills from `.cursor/skills/` (project) or `~/.cursor/skills/` (personal). Pick whichever scope fits your needs.

### Option A — Use this whole repo as a starting point

```bash
git clone https://github.com/zhangdah/Video-Editing-Skills.git my-video-project
cd my-video-project
# Replace mcp.json with your platform's path (see below), drop in your source
# media, and you're ready to go.
```

### Option B — Copy individual skills into an existing project

```bash
# From your project root:
mkdir -p .cursor/skills
cp -R /path/to/Video-Editing-Skills/.cursor/skills/video-annotation-workflow .cursor/skills/
```

### Option C — Install as personal (user-wide) skills

```bash
mkdir -p ~/.cursor/skills
cp -R .cursor/skills/* ~/.cursor/skills/
```

After copying, restart your AI tool so it picks up the new skills.

---

## Environment Setup

All skills assume a single shared conda environment.

```bash
conda create -n video_edit python=3.11 -y
conda activate video_edit
pip install mcp-video static-ffmpeg librosa numpy yt-dlp opencv-python pillow
conda install -c conda-forge liblzma    # needed by librosa
```

`static-ffmpeg` provides self-contained `ffmpeg` and `ffprobe` binaries for macOS, Linux, and Windows — no system FFmpeg install required.

### MCP Server Config

The included [`.cursor/mcp.json`](.cursor/mcp.json) registers the `mcp-video` MCP server. **You must edit the `command` and `PATH` values** to match your platform and conda env location:

| Platform | Example `command` | Example `PATH` |
|----------|-------------------|----------------|
| macOS (M-series) | `~/miniconda3/envs/video_edit/bin/python` | `~/miniconda3/envs/video_edit/lib/python3.11/site-packages/static_ffmpeg/bin/darwin_arm64:$PATH` |
| Linux | `~/miniconda3/envs/video_edit/bin/python` | `~/miniconda3/envs/video_edit/lib/python3.11/site-packages/static_ffmpeg/bin/linux:$PATH` |
| Windows | `C:\Users\<you>\anaconda3\envs\video_edit\python.exe` | `C:\Users\<you>\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32;%PATH%` |

After editing, restart your AI tool. Confirm the server is live by asking the agent to call `video_info` on any video file.

---

## Quick Start Examples

Once the skills are installed and the conda env is active, try prompts like:

```
"Edit a 90-second beat-synced montage from the footage in LA/ and Hawaii/.
Use any track from music/ that fits. Render at 1080p first, then 4K."
```

→ triggers `video-editing-workflow`

```
"Annotate Demo.mp4 with highlight boxes around the cursor at each click,
and add English captions explaining each step. Use the debug grid so I can
help align the boxes."
```

→ triggers `video-annotation-workflow`

The agent will follow the skill's phased workflow: gather requirements → confirm with you → render → iterate.

---

## Repository Structure

```
Video-Editing-Skills/
├── README.md
├── .gitignore                          # ignores video files + per-project work
├── .cursor/
│   ├── mcp.json                        # MCP server registration (edit per platform)
│   └── skills/
│       ├── video-editing-workflow/
│       │   └── SKILL.md
│       └── video-annotation-workflow/
│           ├── SKILL.md
│           ├── scripts/
│           │   └── annotate_template.py    # generic renderer, customize CONSTANTS + SEGMENTS
│           └── examples/
│               └── kyc_demo_segments.py    # real-world SEGMENTS reference
```

Source media (`*.mp4`, `*.mov`, etc.), per-project scripts, and intermediate output folders are all gitignored — this repo only contains the reusable skills.

---

## Contributing a New Skill

1. Create `.cursor/skills/<skill-name>/SKILL.md` with YAML frontmatter:

   ```markdown
   ---
   name: my-skill-name
   description: >-
     One or two sentences explaining what the skill does AND when the agent
     should apply it (include trigger keywords).
   ---

   # My Skill Name
   ...
   ```

2. Keep `SKILL.md` under ~500 lines. Put long reference material in sibling files (`reference.md`, `examples/`, `scripts/`) and link to them.

3. Use clear phased workflows when the task is multi-step, especially anything involving user feedback loops.

4. Add a row to the Available Skills table above.

5. Open a PR.

---

## License

MIT — use, modify, and share freely.
