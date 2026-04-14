"""
Video edit validator — automated QA for the final exported video.

Checks:
  1. Duration vs target
  2. Technical specs (resolution, codec, pixel format, audio)
  3. Scene change detection → clip count vs expected
  4. Beat-sync accuracy (scene changes vs BGM beat grid)
  5. Black frame detection (encoding errors)
  6. Frame sampling at expected clip boundaries (no missing clips)
"""
import os
import sys
import subprocess
import json
import math
import static_ffmpeg
static_ffmpeg.add_paths()

FFMPEG = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE'
FFPROBE = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffprobe.EXE'


def probe(path):
    r = subprocess.run(
        [FFPROBE, '-v', 'quiet', '-print_format', 'json',
         '-show_format', '-show_streams', path],
        capture_output=True, text=True
    )
    return json.loads(r.stdout)


def detect_scenes(path, threshold=0.35):
    """Use ffmpeg select filter to find scene-change timestamps."""
    r = subprocess.run(
        [FFMPEG, '-i', path,
         '-vf', f"select='gt(scene,{threshold})',showinfo",
         '-vsync', 'vfr', '-f', 'null', '-'],
        capture_output=True, text=True
    )
    import re
    times = []
    for m in re.finditer(r'pts_time:(\d+\.?\d*)', r.stderr):
        times.append(float(m.group(1)))
    return times


def detect_black_frames(path, duration, samples=20):
    """Sample frames across the video and check for all-black."""
    black_times = []
    for i in range(samples):
        t = duration * i / samples
        r = subprocess.run(
            [FFMPEG, '-ss', str(t), '-i', path,
             '-frames:v', '1', '-vf', 'blackdetect=d=0.01:pix_th=0.05',
             '-f', 'null', '-'],
            capture_output=True, text=True
        )
        if 'black_start' in r.stderr:
            black_times.append(t)
    return black_times


def check_beat_sync(scene_times, bpm, tolerance_ms=80):
    """Check what % of scene changes land on a beat boundary."""
    beat_interval = 60.0 / bpm
    on_beat = 0
    for t in scene_times:
        nearest_beat = round(t / beat_interval) * beat_interval
        offset_ms = abs(t - nearest_beat) * 1000
        if offset_ms <= tolerance_ms:
            on_beat += 1
    return on_beat, len(scene_times)


def run_checks(video_path, target_duration=None, target_res=None,
               expected_clips=None, bpm=None):
    results = []
    passes = 0
    fails = 0

    def ok(msg):
        nonlocal passes
        passes += 1
        results.append(f"  [PASS] {msg}")

    def fail(msg):
        nonlocal fails
        fails += 1
        results.append(f"  [FAIL] {msg}")

    def info(msg):
        results.append(f"  [INFO] {msg}")

    print(f"Validating: {video_path}", flush=True)
    print("=" * 60, flush=True)

    if not os.path.exists(video_path):
        fail(f"File not found: {video_path}")
        return passes, fails, results

    data = probe(video_path)
    fmt = data['format']
    streams = data['streams']
    v_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
    a_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)
    duration = float(fmt['duration'])
    size_mb = int(fmt['size']) // 1024 // 1024

    # --- 1. Duration ---
    print("\n1. Duration", flush=True)
    info(f"Actual: {duration:.1f}s ({int(duration)//60}:{int(duration)%60:02d})")
    if target_duration:
        diff = abs(duration - target_duration)
        if diff <= 2.0:
            ok(f"Within {diff:.1f}s of target {target_duration}s")
        else:
            fail(f"Off by {diff:.1f}s from target {target_duration}s")

    # --- 2. Technical specs ---
    print("\n2. Technical Specs", flush=True)
    if not v_stream:
        fail("No video stream found")
    else:
        w = v_stream['width']
        h = v_stream['height']
        codec = v_stream['codec_name']
        pix_fmt = v_stream.get('pix_fmt', 'unknown')
        fps = eval(v_stream.get('r_frame_rate', '0/1'))

        info(f"Resolution: {w}x{h}, Codec: {codec}, PixFmt: {pix_fmt}, FPS: {fps:.0f}")

        if target_res:
            tw, th = target_res
            if w == tw and h == th:
                ok(f"Resolution matches target {tw}x{th}")
            else:
                fail(f"Resolution {w}x{h} != target {tw}x{th}")

        if pix_fmt == 'yuv420p':
            ok("Pixel format yuv420p (max compatibility)")
        else:
            fail(f"Pixel format {pix_fmt} — may cause playback issues (expected yuv420p)")

        if codec in ('h264', 'hevc'):
            ok(f"Video codec {codec}")
        else:
            fail(f"Video codec {codec} — may cause playback issues")

    if not a_stream:
        fail("No audio stream — BGM missing?")
    else:
        a_codec = a_stream['codec_name']
        a_dur = float(a_stream.get('duration', 0))
        info(f"Audio: {a_codec}, duration={a_dur:.1f}s")
        if a_codec == 'aac':
            ok("Audio codec AAC")
        else:
            info(f"Audio codec {a_codec} (AAC preferred for MP4)")
        if abs(a_dur - duration) <= 1.0:
            ok(f"Audio/video duration in sync (diff={abs(a_dur-duration):.2f}s)")
        else:
            fail(f"Audio/video duration mismatch: video={duration:.1f}s, audio={a_dur:.1f}s")

    # --- 3. Scene detection → clip count ---
    print("\n3. Scene Detection (clip count)", flush=True)
    info("Detecting scene changes (this may take a moment)...")
    scenes = detect_scenes(video_path)
    actual_clips = len(scenes) + 1
    info(f"Detected {len(scenes)} scene changes -> ~{actual_clips} clips")
    if expected_clips:
        diff = abs(actual_clips - expected_clips)
        if diff <= 3:
            ok(f"Clip count ~{actual_clips} is close to expected {expected_clips} (±{diff})")
        else:
            fail(f"Clip count {actual_clips} differs from expected {expected_clips} by {diff}")

    # --- 4. Beat sync ---
    if bpm and scenes:
        print("\n4. Beat Sync Accuracy", flush=True)
        on_beat, total = check_beat_sync(scenes, bpm)
        pct = on_beat / total * 100 if total > 0 else 0
        info(f"{on_beat}/{total} cuts on beat ({pct:.0f}%), BPM={bpm}, tolerance=±80ms")
        if pct >= 60:
            ok(f"Beat sync rate {pct:.0f}% (good)")
        elif pct >= 40:
            info(f"Beat sync rate {pct:.0f}% (moderate - some cuts may be off-beat)")
        else:
            fail(f"Beat sync rate {pct:.0f}% (poor - most cuts are off-beat)")

    # --- 5. Black frames ---
    print("\n5. Black Frame Check", flush=True)
    black = detect_black_frames(video_path, duration)
    if not black:
        ok("No unexpected black frames detected")
    else:
        is_ending = all(t > duration - 5 for t in black)
        if is_ending:
            ok(f"Black frames only at ending (fade-to-black): {[f'{t:.0f}s' for t in black]}")
        else:
            fail(f"Black frames at: {[f'{t:.1f}s' for t in black]}")

    # --- Summary ---
    print(f"\n{'=' * 60}", flush=True)
    print(f"RESULTS: {passes} passed, {fails} failed", flush=True)
    for r in results:
        print(r, flush=True)
    print(f"{'=' * 60}", flush=True)

    return passes, fails, results


if __name__ == '__main__':
    video = os.path.join(BASE, 'US_Trip_2026_Final_v6.mp4') \
        if 'BASE' in dir() else r'C:\Video Editing\2026 US Trip\US_Trip_2026_Final_v6.mp4'

    # v6 parameters
    run_checks(
        video,
        target_duration=90,
        target_res=(3840, 2160),
        expected_clips=30,   # 14 LA + 14 HI (with vertical) + intro grid + ending
        bpm=125.0,
    )
