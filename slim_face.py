"""
Face slimming post-processor for video.
Uses MediaPipe FaceLandmarker (Tasks API) to detect jaw landmarks,
then applies a radial warp to slim the jawline/cheeks.

Optimized: face detection at reduced resolution, warping at full res on ROI only.
"""
import os
import subprocess
import json
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions
from mediapipe.tasks.python import BaseOptions
import static_ffmpeg
static_ffmpeg.add_paths()

BASE = r'C:\Video Editing\2026 US Trip'
OUT = os.path.join(BASE, 'output_v6')
FFMPEG = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE'
FFPROBE = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffprobe.EXE'
BGM = os.path.join(BASE, 'music', 'Everythings_Good_Phil_Good.mp3')
MODEL = os.path.join(BASE, 'face_landmarker.task')

SLIM_STRENGTH = 0.35
SLIM_RADIUS_SCALE = 1.2

LEFT_JAW = [234, 127, 162, 21, 54, 103, 67, 109]
RIGHT_JAW = [454, 356, 389, 251, 284, 332, 297, 338]
NOSE_TIP = 1


def get_duration(path):
    probe = subprocess.run(
        [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', path],
        capture_output=True, text=True
    )
    return float(json.loads(probe.stdout)['format']['duration'])


def warp_point(img, center, ctrl, strength, radius):
    h, w = img.shape[:2]
    cx, cy = center
    px, py = ctrl
    dx = cx - px
    dy = cy - py

    r_int = int(radius) + 1
    x_min = max(0, px - r_int)
    x_max = min(w, px + r_int)
    y_min = max(0, py - r_int)
    y_max = min(h, py + r_int)

    if x_max <= x_min or y_max <= y_min:
        return img

    xx, yy = np.meshgrid(
        np.arange(x_min, x_max, dtype=np.float32),
        np.arange(y_min, y_max, dtype=np.float32)
    )

    dist_sq = (xx - px) ** 2 + (yy - py) ** 2
    r_sq = radius * radius
    mask = dist_sq < r_sq

    weight = np.zeros_like(dist_sq)
    weight[mask] = (1.0 - dist_sq[mask] / r_sq) ** 2

    map_x = xx - strength * dx * weight
    map_y = yy - strength * dy * weight

    roi = img[y_min:y_max, x_min:x_max]
    warped_roi = cv2.remap(
        roi, map_x - x_min, map_y - y_min,
        cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )
    img[y_min:y_max, x_min:x_max] = warped_roi
    return img


def slim_face(img, landmarks, w_img, h_img, strength=SLIM_STRENGTH):
    nose = landmarks[NOSE_TIP]
    center_x = int(nose.x * w_img)
    center_y = int(nose.y * h_img)

    left_pts = [(int(landmarks[i].x * w_img), int(landmarks[i].y * h_img)) for i in LEFT_JAW]
    right_pts = [(int(landmarks[i].x * w_img), int(landmarks[i].y * h_img)) for i in RIGHT_JAW]

    face_width = abs(left_pts[0][0] - right_pts[0][0])
    if face_width < 50:
        return img

    radius = face_width * SLIM_RADIUS_SCALE * 0.3

    for px, py in left_pts:
        img = warp_point(img, (center_x, center_y), (px, py), strength, radius)
    for px, py in right_pts:
        img = warp_point(img, (center_x, center_y), (px, py), strength, radius)

    return img


def process_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    tmp_raw = output_path.replace('.mp4', '_raw.mp4')
    writer = cv2.VideoWriter(tmp_raw, fourcc, fps, (w, h))

    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=2,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = FaceLandmarker.create_from_options(options)

    frame_idx = 0
    faces_processed = 0

    print(f"Processing {total_frames} frames ({w}x{h} @ {fps:.0f}fps)...", flush=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_ms = int(frame_idx * 1000 / fps)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        if result.face_landmarks:
            for face_lm in result.face_landmarks:
                frame = slim_face(frame, face_lm, w, h)
                faces_processed += 1

        writer.write(frame)
        frame_idx += 1

        if frame_idx % 100 == 0:
            pct = frame_idx / total_frames * 100
            print(f"  Frame {frame_idx}/{total_frames} ({pct:.0f}%) - {faces_processed} face warps", flush=True)

    cap.release()
    writer.release()
    landmarker.close()

    print(f"  Warping done: {frame_idx} frames, {faces_processed} face warps", flush=True)
    print("  Re-encoding with H.264...", flush=True)
    r = subprocess.run([
        FFMPEG, '-y', '-i', tmp_raw,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
        output_path
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ENCODE ERROR: {r.stderr[-300:]}", flush=True)

    if os.path.exists(tmp_raw):
        os.remove(tmp_raw)
    print(f"  Output: {output_path}", flush=True)


if __name__ == '__main__':
    input_video = os.path.join(OUT, 'combined.mp4')
    output_video = os.path.join(OUT, 'combined_slim.mp4')

    print("=" * 60, flush=True)
    print("Face Slimming Post-Processor", flush=True)
    print(f"  Strength: {SLIM_STRENGTH}", flush=True)
    print("=" * 60, flush=True)

    process_video(input_video, output_video)

    print("\nAdding BGM...", flush=True)
    total_dur = get_duration(output_video)
    final_output = os.path.join(BASE, 'US_Trip_2026_Final_v6.mp4')
    fade_out_start = total_dur - 4.0

    audio_filter = (
        f'[1:a]atrim=0:{total_dur},'
        f'afade=t=in:st=0:d=1.5,'
        f'afade=t=out:st={fade_out_start}:d=4.0,'
        f'asetpts=PTS-STARTPTS[a]'
    )

    r = subprocess.run([
        FFMPEG, '-y',
        '-i', output_video, '-i', BGM,
        '-filter_complex', audio_filter,
        '-map', '0:v', '-map', '[a]',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-shortest', '-movflags', '+faststart',
        final_output
    ], capture_output=True, text=True)

    final_dur = get_duration(final_output)
    final_size = os.path.getsize(final_output)
    print(f"\n{'=' * 60}", flush=True)
    print(f"DONE!", flush=True)
    print(f"  Output:   {final_output}", flush=True)
    print(f"  Duration: {final_dur:.1f}s ({int(final_dur)//60}:{int(final_dur)%60:02d})", flush=True)
    print(f"  Size:     {final_size // 1024 // 1024} MB", flush=True)
    print(f"{'=' * 60}", flush=True)
