"""
US Trip 2026 - Video Edit v6
- New BGM: Everything's Good (Phil Good) at 125 BPM
- Beat-synced cuts: 1.920s (4 beats / 1 measure) and 3.840s (8 beats / 2 measures)
- Vertical video IMG_8887.MOV with blur background fill
- 4K output (3840x2160)
- Target: ~90s (1:30)
"""
import os
import subprocess
import json
import static_ffmpeg
static_ffmpeg.add_paths()

BASE = r'C:\Video Editing\2026 US Trip'
LA = os.path.join(BASE, 'LA')
HI = os.path.join(BASE, 'Hawaii')
OUT = os.path.join(BASE, 'output_v6')
BGM = os.path.join(BASE, 'music', 'Everythings_Good_Phil_Good.mp3')
FFMPEG = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE'
FFPROBE = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffprobe.EXE'

os.makedirs(OUT, exist_ok=True)

W, H = 3840, 2160
BPM = 125.0
BEAT = 60.0 / BPM          # 0.480s
MEASURE = 4 * BEAT          # 1.920s
SHORT = MEASURE             # 1.920s (4 beats) - fast cut
LONG = 2 * MEASURE          # 3.840s (8 beats) - scenic
XFADE = 1.0                 # transition overlap

SCALE_PAD = f'scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2'


def run_ff(cmd, desc=""):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ERROR ({desc}): {result.stderr[-500:]}", flush=True)
        return False
    return True


def get_duration(path):
    probe = subprocess.run(
        [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', path],
        capture_output=True, text=True
    )
    return float(json.loads(probe.stdout)['format']['duration'])


def trim_clip(src, start, dur, out_path, desc, extra_vf=""):
    vf = SCALE_PAD
    if extra_vf:
        vf = extra_vf
    return run_ff([
        FFMPEG, '-y', '-ss', str(start), '-i', src, '-t', str(dur),
        '-vf', vf,
        '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart',
        out_path
    ], desc)


def concat_clips(clip_paths, list_path, out_path, desc, reencode=False):
    with open(list_path, 'w') as f:
        for c in clip_paths:
            f.write(f"file '{c}'\n")
    if reencode:
        return run_ff([
            FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', list_path,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out_path
        ], desc)
    return run_ff([
        FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', list_path,
        '-c', 'copy', '-movflags', '+faststart', out_path
    ], desc)


# ============================================================
# STEP 1: Process vertical video (blur background fill)
# ============================================================
print("=" * 60, flush=True)
print("STEP 1: Processing vertical video with blur fill", flush=True)
print("=" * 60, flush=True)

vertical_src = os.path.join(HI, 'IMG_8887.MOV')
vertical_out = os.path.join(OUT, 'clip_vertical_blur.mp4')

if os.path.exists(vertical_out):
    print(f"  [SKIP] Already exists: {get_duration(vertical_out):.2f}s", flush=True)
else:
    blur_vf = (
        f'split[original][blur];'
        f'[blur]scale={W}:{H},gblur=sigma=50[bg];'
        f'[original]scale=-2:{H}[fg];'
        f'[bg][fg]overlay=(W-w)/2:0'
    )
    run_ff([
        FFMPEG, '-y', '-ss', '1.0', '-i', vertical_src,
        '-t', str(LONG),
        '-vf', blur_vf,
        '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart',
        vertical_out
    ], "vertical blur fill")
    print(f"  -> {get_duration(vertical_out):.2f}s", flush=True)

# ============================================================
# STEP 2: Trim all clips at 125 BPM beat boundaries
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 2: Trimming clips (125 BPM beat-sync)", flush=True)
print("=" * 60, flush=True)

# (source_path, start_time, duration, description)
la_cuts = [
    (os.path.join(LA, 'DJI_20260329091659_0909_D.MP4'), 1.0,  LONG,  "Griffith panorama"),
    (os.path.join(LA, 'LA1.MP4'),                        5.0,  SHORT, "Palm street driving"),
    (os.path.join(LA, 'LA4.MP4'),                        4.0,  LONG,  "Beverly Hills palms"),
    (os.path.join(LA, 'DJI_20260329114633_0918_D.MP4'),  8.0,  SHORT, "Highway POV"),
    (os.path.join(LA, 'DJI_20260329151216_0941_D.MP4'),  28.0, LONG,  "Coastal highway palms"),
    (os.path.join(LA, 'DJI_20260329150932_0937_D.MP4'),  12.0, SHORT, "Hillside driving"),
    (os.path.join(LA, 'DJI_20260329154450_0947_D.MP4'),  5.0,  LONG,  "Arms spread freedom"),
    (os.path.join(LA, 'DJI_20260329154426_0946_D.MP4'),  4.0,  SHORT, "Cactus street walk"),
    (os.path.join(LA, 'DJI_20260329161119_0957_D.MP4'),  6.0,  SHORT, "Theater facade"),
    (os.path.join(LA, 'DJI_20260329141537_0921_D.MP4'),  28.0, LONG,  "Beach couple selfie"),
    (os.path.join(LA, 'DJI_20260329141727_0923_D.MP4'),  5.0,  SHORT, "Boardwalk selfie"),
    (os.path.join(LA, 'DJI_20260329141956_0924_D.MP4'),  10.0, LONG,  "Palm tree couple"),
    (os.path.join(LA, 'DJI_20260329141644_0922_D.MP4'),  3.0,  LONG,  "Looking at beach"),
    (os.path.join(LA, 'DJI_20260329144254_0933_D.MP4'),  15.0, SHORT, "Small town street"),
]

hi_cuts = [
    (os.path.join(HI, 'DJI_20260401125745_0968_D.MP4'),  10.0, LONG,  "Beach plaza ocean"),
    (os.path.join(HI, 'DJI_20260401125853_0969_D.MP4'),  2.0,  LONG,  "Waikiki Diamond Head"),
    (os.path.join(HI, 'DJI_20260401131945_0970_D.MP4'),  5.0,  SHORT, "Beach crowd"),
    (os.path.join(HI, 'DJI_20260402152637_0003_D.MP4'),  25.0, LONG,  "Ko'olau mountains"),
    (os.path.join(HI, 'DJI_20260402152810_0004_D.MP4'),  40.0, LONG,  "Tropical rainforest"),
    (os.path.join(HI, 'DJI_20260402153817_0006_D.MP4'),  5.0,  SHORT, "Mountain view"),
    (os.path.join(HI, 'DJI_20260401132117_0972_D.MP4'),  8.0,  SHORT, "Honolulu street"),
    (os.path.join(HI, 'DJI_20260401143137_0978_D.MP4'),  8.0,  SHORT, "Eating snack"),
    (os.path.join(HI, 'DJI_20260401132027_0971_D.MP4'),  12.0, LONG,  "Beach selfie HI"),
    (os.path.join(HI, 'DJI_20260401132359_0977_D.MP4'),  8.0,  SHORT, "Peace sign"),
    (os.path.join(HI, 'DJI_20260401144638_0981_D.MP4'),  12.0, LONG,  "Chopsticks pose"),
    # vertical clip slot (handled separately)
    (os.path.join(HI, 'DJI_20260401193144_0991_D.MP4'),  20.0, SHORT, "Driving Hawaii"),
    (os.path.join(HI, 'DJI_20260404181912_0042_D.MP4'),  5.0,  LONG,  "Sunset beach couple"),
]

all_cuts = la_cuts + hi_cuts

la_dur_expected = sum(d for _, _, d, _ in la_cuts)
hi_dur_expected = sum(d for _, _, d, _ in hi_cuts) + LONG  # +vertical clip
print(f"  LA plan: {len(la_cuts)} clips, {la_dur_expected:.1f}s", flush=True)
print(f"  HI plan: {len(hi_cuts)}+1 clips, {hi_dur_expected:.1f}s", flush=True)

trimmed = []
for i, (src, ss, dur, desc) in enumerate(all_cuts):
    tag = "LA" if i < len(la_cuts) else "HI"
    out_path = os.path.join(OUT, f'clip_{i:02d}.mp4')
    trimmed.append(out_path)
    beats = int(dur / BEAT)
    if os.path.exists(out_path):
        print(f"  [{tag}] clip_{i:02d}: {desc} [SKIP]", flush=True)
    else:
        print(f"  [{tag}] clip_{i:02d}: {desc} ({beats} beats, {dur:.2f}s)", flush=True)
        trim_clip(src, ss, dur, out_path, desc)

# ============================================================
# STEP 3: Ending = first 5s of 0042 (sunset beach couple) with fade-to-black
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 3: Creating ending (0042 first 5s + fade-to-black)", flush=True)
print("=" * 60, flush=True)

ENDING_DUR = 5.0
ending_clip = os.path.join(OUT, 'clip_ending.mp4')
fade_start = ENDING_DUR - 3.0
ending_vf = f'{SCALE_PAD},fade=t=out:st={fade_start}:d=3.0:color=black'

trim_clip(
    os.path.join(HI, 'DJI_20260404181912_0042_D.MP4'),
    0.0, ENDING_DUR, ending_clip, "sunset ending 5s + fade",
    extra_vf=ending_vf
)
print(f"  Ending: {get_duration(ending_clip):.2f}s", flush=True)

# ============================================================
# STEP 4: Merge LA section
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 4: Merging LA section", flush=True)
print("=" * 60, flush=True)

la_clips = trimmed[:len(la_cuts)]
la_section = os.path.join(OUT, 'la_section.mp4')
concat_clips(la_clips, os.path.join(OUT, 'la_list.txt'), la_section, "LA merge", reencode=True)
la_dur = get_duration(la_section)
print(f"  LA section: {la_dur:.1f}s", flush=True)

# ============================================================
# STEP 5: Merge Hawaii section (with vertical clip inserted)
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 5: Merging Hawaii section (+ vertical clip)", flush=True)
print("=" * 60, flush=True)

hi_clips_trimmed = trimmed[len(la_cuts):]
# Insert vertical clip after "Laughing together" (index 10), before "Driving Hawaii" (index 11)
hi_with_vertical = hi_clips_trimmed[:11] + [vertical_out] + hi_clips_trimmed[11:]

hi_section = os.path.join(OUT, 'hi_section.mp4')
concat_clips(hi_with_vertical, os.path.join(OUT, 'hi_list.txt'), hi_section, "HI merge", reencode=True)
hi_dur = get_duration(hi_section)
print(f"  Hawaii section: {hi_dur:.1f}s ({len(hi_with_vertical)} clips)", flush=True)

# ============================================================
# STEP 6: Dissolve LA -> Hawaii
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 6: LA -> Hawaii dissolve transition", flush=True)
print("=" * 60, flush=True)

merged_body = os.path.join(OUT, 'merged_body.mp4')
run_ff([
    FFMPEG, '-y', '-i', la_section, '-i', hi_section,
    '-filter_complex',
    f'[0:v][1:v]xfade=transition=fade:duration={XFADE}:offset={la_dur - XFADE}[v]',
    '-map', '[v]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    merged_body
], "xfade LA->HI")
body_dur = get_duration(merged_body)
print(f"  Body: {body_dur:.1f}s", flush=True)

# ============================================================
# STEP 7: Body -> Ending dissolve
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 7: Body -> Ending dissolve", flush=True)
print("=" * 60, flush=True)

merged_full = os.path.join(OUT, 'merged_full.mp4')
run_ff([
    FFMPEG, '-y', '-i', merged_body, '-i', ending_clip,
    '-filter_complex',
    f'[0:v][1:v]xfade=transition=fade:duration={XFADE}:offset={body_dur - XFADE}[v]',
    '-map', '[v]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    merged_full
], "xfade body->ending")
full_dur = get_duration(merged_full)
print(f"  Full video (no audio): {full_dur:.1f}s", flush=True)

# ============================================================
# STEP 8: Add intro
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 8: Prepending intro", flush=True)
print("=" * 60, flush=True)

intro_4k = os.path.join(BASE, 'output_v2', 'intro_4k.mp4')
combined = os.path.join(OUT, 'combined.mp4')
concat_clips([intro_4k, merged_full],
             os.path.join(OUT, 'final_list.txt'),
             combined, "intro + body")
total_dur = get_duration(combined)
print(f"  Total (no audio): {total_dur:.1f}s", flush=True)

# ============================================================
# STEP 9: Add BGM with fade-in/out
# ============================================================
print("\n" + "=" * 60, flush=True)
print("STEP 9: Adding BGM - Everything's Good", flush=True)
print("=" * 60, flush=True)

final_output = os.path.join(BASE, 'US_Trip_2026_Final_v6.mp4')
fade_in = 1.5
fade_out = 4.0
fade_out_start = total_dur - fade_out

audio_filter = (
    f'[1:a]atrim=0:{total_dur},'
    f'afade=t=in:st=0:d={fade_in},'
    f'afade=t=out:st={fade_out_start}:d={fade_out},'
    f'asetpts=PTS-STARTPTS[a]'
)

run_ff([
    FFMPEG, '-y',
    '-i', combined, '-i', BGM,
    '-filter_complex', audio_filter,
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
    '-shortest', '-movflags', '+faststart',
    final_output
], "add BGM")

final_dur = get_duration(final_output)
final_size = os.path.getsize(final_output)

print(f"\n{'=' * 60}", flush=True)
print(f"DONE!", flush=True)
print(f"  Output:     {final_output}", flush=True)
print(f"  Duration:   {final_dur:.1f}s ({int(final_dur)//60}:{int(final_dur)%60:02d})", flush=True)
print(f"  Size:       {final_size // 1024 // 1024} MB", flush=True)
print(f"  Resolution: {W}x{H}", flush=True)
print(f"  BGM:        Everything's Good (Phil Good) @ {BPM} BPM", flush=True)
print(f"{'=' * 60}", flush=True)
