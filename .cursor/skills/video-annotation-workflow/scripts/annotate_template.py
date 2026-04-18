"""
Video annotation renderer — template.

Drop this file into your project root as `annotate_demo.py` (or any name),
edit the CONSTANTS and SEGMENTS sections, then run:

    python annotate_demo.py

Required:  pip install opencv-python pillow numpy static-ffmpeg
Static ffmpeg binaries are placed on PATH automatically below.

Workflow:
  1. Set DEBUG_GRID = True for the iteration phase. Output goes to DEBUG_OUT.
  2. Iterate on SEGMENTS coordinates with the user (see the SKILL.md).
  3. When approved, set DEBUG_GRID = False and re-run for the clean FINAL_OUT.
"""

import cv2
import numpy as np
import os
import subprocess
import multiprocessing as mp
from PIL import Image, ImageDraw, ImageFont

import static_ffmpeg
static_ffmpeg.add_paths()


# =============================================================================
# CONSTANTS — set these from `ffprobe <source_video>`
# =============================================================================

VIDEO_IN = "source_video.mp4"
FINAL_OUT = "Demo - Annotated.mp4"
DEBUG_OUT = "Demo - Annotated (DEBUG GRID).mp4"

W, H = 1920, 1080            # source video resolution
FPS = 30                     # source video fps (pin to ffprobe's value)

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"  # any TTF works
BOX_COLOR_RGB = (230, 160, 40)
LABEL_BG = (35, 48, 55, 230)
LABEL_FG = (255, 255, 255, 255)
FADE_FRAMES = 7                            # ~0.25s fade in/out per segment
NUM_WORKERS = mp.cpu_count()

# Toggle for the coordinate-grid debug overlay. True -> writes to DEBUG_OUT.
DEBUG_GRID = True


# =============================================================================
# SEGMENTS — the data you edit constantly during Phase 2 iteration
# =============================================================================
#
# Each segment dict:
#   start, end       -- when the highlight is visible (seconds)
#   label            -- caption pill text
#   zoom             -- (x1,y1,x2,y2) zoom region in source coords, or None
#   keyframes        -- [(t_seconds, (x1,y1,x2,y2)), ...]
#                       linearly interpolated with ease-in-out smoothing
#
# For STATIC boxes, repeat the same coordinates at start and end.
# For DYNAMIC boxes (sliding panels, modals appearing), add a keyframe at the
# moment the animation starts (with the OLD position) and another at the
# moment it ends (with the NEW position).

SEGMENTS = [
    # Example 1: static highlight on a top-right button
    {"start": 0.5, "end": 2.5,
     "label": "Click the menu button",
     "zoom": None,
     "keyframes": [
         (0.5, (1750, 20, 1900, 70)),
         (2.5, (1750, 20, 1900, 70)),
     ]},

    # Example 2: dynamic box that grows as a panel expands
    {"start": 5.0, "end": 9.0,
     "label": "Side panel expands to show details",
     "zoom": None,
     "keyframes": [
         (5.0, (300, 200, 800, 600)),    # initial size
         (5.6, (300, 200, 800, 600)),    # hold briefly
         (6.2, (300, 200, 1500, 600)),   # animation completes
         (9.0, (300, 200, 1500, 600)),   # hold until end
     ]},
]


# =============================================================================
# Renderer (typically no edits needed below this line)
# =============================================================================

def ease_in_out(t):
    return t * t * (3 - 2 * t)


def get_active_segment(t):
    for seg in SEGMENTS:
        if seg["start"] <= t < seg["end"]:
            return seg
    return None


def lerp_box(keyframes, t):
    """Linearly interpolate box coordinates between keyframes (ease-in-out)."""
    if not keyframes:
        return None
    if len(keyframes) == 1:
        return keyframes[0][1]
    if t <= keyframes[0][0]:
        return keyframes[0][1]
    if t >= keyframes[-1][0]:
        return keyframes[-1][1]
    for i in range(len(keyframes) - 1):
        t0, box0 = keyframes[i]
        t1, box1 = keyframes[i + 1]
        if t0 <= t <= t1:
            frac = (t - t0) / (t1 - t0) if t1 > t0 else 0
            frac = ease_in_out(frac)
            return tuple(int(box0[j] + (box1[j] - box0[j]) * frac)
                         for j in range(4))
    return keyframes[-1][1]


def get_box_at_time(seg, t):
    keyframes = seg.get("keyframes")
    if keyframes:
        return lerp_box(keyframes, t)
    return seg.get("box")


def get_segment_alpha(t, seg):
    fade_dur = FADE_FRAMES / FPS
    if t < seg["start"] + fade_dur:
        return ease_in_out((t - seg["start"]) / fade_dur)
    elif t > seg["end"] - fade_dur:
        return ease_in_out((seg["end"] - t) / fade_dur)
    return 1.0


def compute_zoom_viewport(frame_w, frame_h, zoom_region, alpha):
    """Smoothly interpolate from full frame -> zoom region as alpha rises."""
    if zoom_region is None:
        return 0, 0, frame_w, frame_h
    zx1, zy1, zx2, zy2 = zoom_region
    zw, zh = zx2 - zx1, zy2 - zy1
    min_w, min_h = int(frame_w * 0.55), int(frame_h * 0.55)
    if zw < min_w:
        cx = (zx1 + zx2) // 2
        zx1, zx2 = cx - min_w // 2, cx + min_w // 2
    if zh < min_h:
        cy = (zy1 + zy2) // 2
        zy1, zy2 = cy - min_h // 2, cy + min_h // 2
    if zx1 < 0: zx1, zx2 = 0, zx2 - zx1
    if zy1 < 0: zy1, zy2 = 0, zy2 - zy1
    if zx2 > frame_w: zx1, zx2 = zx1 - (zx2 - frame_w), frame_w
    if zy2 > frame_h: zy1, zy2 = zy1 - (zy2 - frame_h), frame_h
    full = np.array([0, 0, frame_w, frame_h], dtype=float)
    target = np.array([zx1, zy1, zx2, zy2], dtype=float)
    zoom_strength = min(alpha, 0.7)
    viewport = full + zoom_strength * (target - full)
    return (int(viewport[0]), int(viewport[1]),
            int(viewport[2]), int(viewport[3]))


def draw_debug_grid(frame, t, box):
    """Coordinate grid + box-corner labels for visual measurement.

    - Cyan minor grid lines every 50px, brighter major lines every 100px
    - Cyan x/y axis labels every 100px
    - Yellow corner-coordinate labels at the 4 box corners
    - Yellow timestamp `t=NN.NNs` in the top-right
    """
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img, "RGBA")
    try:
        gfont = ImageFont.truetype(FONT_PATH, 14)
        bigfont = ImageFont.truetype(FONT_PATH, 18)
    except Exception:
        gfont = ImageFont.load_default()
        bigfont = gfont

    minor = (255, 255, 255, 40)
    major = (0, 255, 255, 110)
    label_bg = (0, 0, 0, 160)
    label_fg = (0, 255, 255, 255)

    for x in range(0, W, 50):
        draw.line([(x, 0), (x, H)],
                  fill=major if x % 100 == 0 else minor, width=1)
    for y in range(0, H, 50):
        draw.line([(0, y), (W, y)],
                  fill=major if y % 100 == 0 else minor, width=1)

    for x in range(100, W, 100):
        txt = str(x)
        bbox = gfont.getbbox(txt)
        tw = bbox[2] - bbox[0]
        draw.rectangle([x - tw // 2 - 3, 2, x + tw // 2 + 3, 18], fill=label_bg)
        draw.text((x - tw // 2, 1), txt, fill=label_fg, font=gfont)
    for y in range(100, H, 100):
        txt = str(y)
        bbox = gfont.getbbox(txt)
        tw = bbox[2] - bbox[0]
        draw.rectangle([2, y - 9, tw + 8, y + 9], fill=label_bg)
        draw.text((4, y - 8), txt, fill=label_fg, font=gfont)

    if box is not None:
        bx1, by1, bx2, by2 = box
        for (cx, cy, anchor) in [
            (bx1, by1, "tl"), (bx2, by1, "tr"),
            (bx1, by2, "bl"), (bx2, by2, "br"),
        ]:
            txt = f"({cx},{cy})"
            bbox = gfont.getbbox(txt)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pad = 3
            if anchor == "tl":
                lx, ly = cx + 4, cy + 4
            elif anchor == "tr":
                lx, ly = cx - tw - 2 * pad - 4, cy + 4
            elif anchor == "bl":
                lx, ly = cx + 4, cy - th - 2 * pad - 4
            else:
                lx, ly = cx - tw - 2 * pad - 4, cy - th - 2 * pad - 4
            lx = max(2, min(lx, W - tw - 2 * pad - 2))
            ly = max(2, min(ly, H - th - 2 * pad - 2))
            draw.rectangle([lx, ly, lx + tw + 2 * pad, ly + th + 2 * pad],
                           fill=(0, 0, 0, 200))
            draw.text((lx + pad, ly + pad - 1), txt,
                      fill=(255, 230, 0, 255), font=gfont)

    tstr = f"t={t:6.2f}s"
    bbox = bigfont.getbbox(tstr)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rectangle([W - tw - 22, 4, W - 4, th + 14],
                   fill=(0, 0, 0, 200))
    draw.text((W - tw - 14, 6), tstr, fill=(255, 255, 0, 255), font=bigfont)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def annotate_frame(frame, t, font):
    seg = get_active_segment(t)
    if seg is None:
        if DEBUG_GRID:
            frame = draw_debug_grid(frame, t, None)
        return frame
    alpha = get_segment_alpha(t, seg)
    if alpha < 0.01:
        if DEBUG_GRID:
            frame = draw_debug_grid(frame, t, None)
        return frame

    box = get_box_at_time(seg, t)
    if box is None:
        if DEBUG_GRID:
            frame = draw_debug_grid(frame, t, None)
        return frame
    bx1, by1, bx2, by2 = box
    zoom_region = seg.get("zoom")

    # ZOOM (disabled by default - re-enable after Phase-3 sign-off if desired)
    # if zoom_region is not None:
    #     vx1, vy1, vx2, vy2 = compute_zoom_viewport(W, H, zoom_region, alpha)
    #     vw, vh = max(vx2 - vx1, 1), max(vy2 - vy1, 1)
    #     crop = frame[vy1:vy2, vx1:vx2]
    #     frame = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LANCZOS4)
    #     scale_x, scale_y = W / vw, H / vh
    #     bx1 = int((bx1 - vx1) * scale_x)
    #     by1 = int((by1 - vy1) * scale_y)
    #     bx2 = int((bx2 - vx1) * scale_x)
    #     by2 = int((by2 - vy1) * scale_y)

    bx1, by1 = max(0, min(bx1, W - 1)), max(0, min(by1, H - 1))
    bx2, by2 = max(bx1 + 1, min(bx2, W)), max(by1 + 1, min(by2, H))

    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img, "RGBA")

    dim_alpha = int(80 * alpha)
    dim_color = (0, 0, 0, dim_alpha)
    draw.rectangle([0, 0, W, by1], fill=dim_color)
    draw.rectangle([0, by2, W, H], fill=dim_color)
    draw.rectangle([0, by1, bx1, by2], fill=dim_color)
    draw.rectangle([bx2, by1, W, by2], fill=dim_color)

    box_alpha = int(255 * alpha)
    outline_color = (BOX_COLOR_RGB[0], BOX_COLOR_RGB[1], BOX_COLOR_RGB[2],
                     box_alpha)
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=6,
                           outline=outline_color, width=3)

    label_text = seg["label"]
    bbox = font.getbbox(label_text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 12, 7
    label_h = th + 2 * pad_y
    label_x = bx1
    label_y = by1 - label_h - 6
    if label_y < 5:
        label_y = by2 + 6
    if label_y + label_h > H - 5:
        label_y = by1 + 6
    if label_x + tw + 2 * pad_x > W - 10:
        label_x = W - tw - 2 * pad_x - 10
    if label_x < 5:
        label_x = 5

    bg_alpha = int(230 * alpha)
    lbl_bg = (LABEL_BG[0], LABEL_BG[1], LABEL_BG[2], bg_alpha)
    lbl_fg = (LABEL_FG[0], LABEL_FG[1], LABEL_FG[2], int(255 * alpha))
    draw.rounded_rectangle(
        [label_x, label_y, label_x + tw + 2 * pad_x, label_y + th + 2 * pad_y],
        radius=8, fill=lbl_bg)
    draw.text((label_x + pad_x, label_y + pad_y - 2), label_text,
              fill=lbl_fg, font=font)

    out = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    if DEBUG_GRID:
        out = draw_debug_grid(out, t, (bx1, by1, bx2, by2))
    return out


def process_chunk(args):
    """Worker: decode a frame range, annotate, write to mp4v temp file."""
    chunk_id, start_frame, end_frame = args
    font = ImageFont.truetype(FONT_PATH, 24)

    cap = cv2.VideoCapture(VIDEO_IN)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    tmp_path = f"output/chunk_{chunk_id:03d}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp_path, fourcc, FPS, (W, H))

    count = end_frame - start_frame
    for i in range(count):
        ret, frame = cap.read()
        if not ret:
            break
        t = (start_frame + i) / FPS
        frame = annotate_frame(frame, t, font)
        out.write(frame)

    cap.release()
    out.release()
    return tmp_path


def main():
    """Parallel chunk render (mp4v) -> single ffmpeg concat + H.264 pass."""
    os.makedirs("output", exist_ok=True)

    cap = cv2.VideoCapture(VIDEO_IN)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    frames_per_chunk = max(1, total_frames // NUM_WORKERS)
    chunks = []
    for i in range(NUM_WORKERS):
        start = i * frames_per_chunk
        end = min((i + 1) * frames_per_chunk, total_frames)
        if i == NUM_WORKERS - 1:
            end = total_frames
        if start < end:
            chunks.append((i, start, end))

    print(f"Processing {total_frames} frames: {len(chunks)} chunks, "
          f"{NUM_WORKERS} workers...", flush=True)

    with mp.Pool(len(chunks)) as pool:
        chunk_files = []
        for path in pool.imap_unordered(process_chunk, chunks):
            chunk_files.append(path)
            print(f"  {path} done ({len(chunk_files)}/{len(chunks)})",
                  flush=True)

    chunk_files = sorted(chunk_files)

    concat_list = "output/concat_list.txt"
    with open(concat_list, "w") as f:
        for path in chunk_files:
            f.write(f"file '../{path}'\n")

    out_path = DEBUG_OUT if DEBUG_GRID else FINAL_OUT
    print(f"Merging + encoding H.264 -> {out_path}", flush=True)
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        out_path,
    ], check=True)

    for path in chunk_files:
        os.remove(path)
    os.remove(concat_list)

    print(f"Done! Output: {out_path}", flush=True)


if __name__ == "__main__":
    main()
