"""
US Trip 2026 - Video Edit v2
- Animated 3x3 grid intro with title
- 29 clips, shuffled order, beat-synced
- More scenery + male shots
- 4K output (3840x2160)
- ~90s total
"""
import os
import subprocess
import json
import static_ffmpeg
static_ffmpeg.add_paths()

BASE = r'C:\Video Editing\2026 US Trip'
LA = os.path.join(BASE, 'LA')
HI = os.path.join(BASE, 'Hawaii')
OUT = os.path.join(BASE, 'output_v2')
BGM = os.path.join(BASE, 'music', '01_Sunshine_Smiles_Chill_HipHop.mp3')
FFMPEG = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE'
FFPROBE = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffprobe.EXE'

os.makedirs(OUT, exist_ok=True)

MEASURE_DUR = 1.493  # 4 beats at 160.7 BPM
CLIP_DUR = 2 * MEASURE_DUR  # ~2.986s per clip

def run_ff(cmd, desc=""):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ERROR ({desc}): {result.stderr[-300:]}")
        return False
    return True

def get_duration(path):
    probe = subprocess.run(
        [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', path],
        capture_output=True, text=True
    )
    return float(json.loads(probe.stdout)['format']['duration'])

# ============================================================
# STEP 1: Create 3x3 grid intro with title (~3s)
# ============================================================
print("=== Step 1: Creating animated intro ===")

intro_sources = [
    (os.path.join(LA, 'DJI_20260329091659_0909_D.MP4'), 2.0),
    (os.path.join(LA, 'LA4.MP4'), 6.0),
    (os.path.join(LA, 'DJI_20260329141537_0921_D.MP4'), 30.0),
    (os.path.join(LA, 'DJI_20260329151216_0941_D.MP4'), 30.0),
    (os.path.join(LA, 'DJI_20260329154450_0947_D.MP4'), 5.0),
    (os.path.join(HI, 'DJI_20260401125853_0969_D.MP4'), 3.0),
    (os.path.join(HI, 'DJI_20260402152637_0003_D.MP4'), 28.0),
    (os.path.join(HI, 'DJI_20260404181912_0042_D.MP4'), 6.0),
    (os.path.join(HI, 'DJI_20260404182001_0045_D.MP4'), 1.0),
]

INTRO_DUR = 3.0
CELL_W = 1280
CELL_H = 720

intro_clips = []
for i, (src, ss) in enumerate(intro_sources):
    clip_path = os.path.join(OUT, f'intro_cell_{i}.mp4')
    intro_clips.append(clip_path)
    run_ff([
        FFMPEG, '-y', '-ss', str(ss), '-i', src, '-t', str(INTRO_DUR),
        '-vf', f'scale={CELL_W}:{CELL_H}:force_original_aspect_ratio=decrease,pad={CELL_W}:{CELL_H}:(ow-iw)/2:(oh-ih)/2',
        '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-pix_fmt', 'yuv420p', '-an', clip_path
    ], f"intro cell {i}")

print("  Creating 3x3 grid...")
grid_path = os.path.join(OUT, 'intro_grid.mp4')
filter_parts = []
for i in range(9):
    filter_parts.append(f'[{i}:v]setpts=PTS-STARTPTS[v{i}]')

grid_layout = (
    f'[v0][v1][v2]hstack=inputs=3[row0];'
    f'[v3][v4][v5]hstack=inputs=3[row1];'
    f'[v6][v7][v8]hstack=inputs=3[row2];'
    f'[row0][row1][row2]vstack=inputs=3[grid]'
)
filter_str = ';'.join(filter_parts) + ';' + grid_layout

inputs = []
for c in intro_clips:
    inputs.extend(['-i', c])

run_ff([
    FFMPEG, '-y', *inputs,
    '-filter_complex', filter_str,
    '-map', '[grid]',
    '-t', str(INTRO_DUR),
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-r', '30',
    grid_path
], "grid layout")

print("  Adding title text overlay...")
intro_final = os.path.join(OUT, 'intro_final.mp4')

title_filter = (
    "drawtext=text='LA  &  Hawaii':"
    "fontfile='C\\:/Windows/Fonts/comicbd.ttf':"
    "fontsize=90:fontcolor=white:borderw=3:bordercolor=black:"
    "x=(w-text_w)/2:y=(h/2)-80:"
    "enable='gte(t,0.3)',"
    "drawtext=text='Trip Vlog':"
    "fontfile='C\\:/Windows/Fonts/comicbd.ttf':"
    "fontsize=70:fontcolor=white:borderw=3:bordercolor=black:"
    "x=(w-text_w)/2:y=(h/2)+30:"
    "enable='gte(t,0.8)',"
    "fade=t=in:st=0:d=0.5,"
    "fade=t=out:st=2.5:d=0.5"
)

run_ff([
    FFMPEG, '-y', '-i', grid_path,
    '-vf', title_filter,
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-an',
    intro_final
], "title overlay")

intro_4k = os.path.join(OUT, 'intro_4k.mp4')
run_ff([
    FFMPEG, '-y', '-i', intro_final,
    '-vf', 'scale=3840:2160:flags=lanczos',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-an',
    intro_4k
], "upscale intro to 4K")

print(f"  Intro done: {intro_4k}")

# ============================================================
# STEP 2: Trim all 29 clips at 4K, beat-synced
# ============================================================
print("\n=== Step 2: Trimming 29 clips at 4K ===")

cuts = [
    # === LA SECTION (shuffled: scenery first, then male, then couple) ===
    (os.path.join(LA, 'DJI_20260329091659_0909_D.MP4'), 1.0, "Griffith city panorama"),
    (os.path.join(LA, 'LA1.MP4'), 5.0, "Evening palm street driving"),
    (os.path.join(LA, 'DJI_20260329114633_0918_D.MP4'), 8.0, "Highway driving POV"),
    (os.path.join(LA, 'LA4.MP4'), 4.0, "Beverly Hills palm road"),
    (os.path.join(LA, 'DJI_20260329151216_0941_D.MP4'), 28.0, "Coastal highway palms"),
    (os.path.join(LA, 'DJI_20260329150932_0937_D.MP4'), 12.0, "Hillside town driving"),
    (os.path.join(LA, 'DJI_20260329154450_0947_D.MP4'), 5.0, "Arms spread intersection"),
    (os.path.join(LA, 'DJI_20260329154426_0946_D.MP4'), 4.0, "Cactus street walk"),
    (os.path.join(LA, 'DJI_20260329161119_0957_D.MP4'), 6.0, "Theater facade"),
    (os.path.join(LA, 'DJI_20260329154032_0943_D.MP4'), 2.0, "Street couple selfie"),
    (os.path.join(LA, 'DJI_20260329141537_0921_D.MP4'), 28.0, "Beach couple selfie"),
    (os.path.join(LA, 'DJI_20260329141727_0923_D.MP4'), 5.0, "Boardwalk selfie"),
    (os.path.join(LA, 'DJI_20260329141956_0924_D.MP4'), 10.0, "Palm tree couple"),
    (os.path.join(LA, 'DJI_20260329141644_0922_D.MP4'), 3.0, "Looking at beach"),
    (os.path.join(LA, 'DJI_20260329144254_0933_D.MP4'), 15.0, "Small town ice cream street"),

    # === HAWAII SECTION (shuffled: scenery first, then male, then couple) ===
    (os.path.join(HI, 'DJI_20260401125745_0968_D.MP4'), 10.0, "Beach plaza ocean view"),
    (os.path.join(HI, 'DJI_20260401125853_0969_D.MP4'), 2.0, "Waikiki Diamond Head"),
    (os.path.join(HI, 'DJI_20260401131945_0970_D.MP4'), 5.0, "Waikiki beach crowd"),
    (os.path.join(HI, 'DJI_20260402152637_0003_D.MP4'), 25.0, "Koolau mountains palms"),
    (os.path.join(HI, 'DJI_20260402152810_0004_D.MP4'), 40.0, "Tropical rainforest green"),
    (os.path.join(HI, 'DJI_20260402153817_0006_D.MP4'), 5.0, "Mountain McDonalds view"),
    (os.path.join(HI, 'DJI_20260401132117_0972_D.MP4'), 8.0, "Honolulu street male"),
    (os.path.join(HI, 'DJI_20260401143137_0978_D.MP4'), 8.0, "Eating snack male"),
    (os.path.join(HI, 'DJI_20260401193144_0991_D.MP4'), 20.0, "Driving in Hawaii male"),
    (os.path.join(HI, 'DJI_20260401132027_0971_D.MP4'), 12.0, "Beach couple selfie HI"),
    (os.path.join(HI, 'DJI_20260401132359_0977_D.MP4'), 8.0, "Kalakaua Ave peace sign"),
    (os.path.join(HI, 'DJI_20260401192300_0989_D.MP4'), 6.0, "Laughing together palms"),
    (os.path.join(HI, 'DJI_20260404181912_0042_D.MP4'), 5.0, "Sunset beach couple"),
    # Last clip: combine 0044 + 0045 sunset ending
]

trimmed_clips = []
for i, (src, start, desc) in enumerate(cuts):
    out_path = os.path.join(OUT, f'clip_{i:02d}.mp4')
    trimmed_clips.append(out_path)
    print(f"  Clip {i:02d}: {desc} ({CLIP_DUR:.2f}s)")
    run_ff([
        FFMPEG, '-y', '-ss', str(start), '-i', src, '-t', str(CLIP_DUR),
        '-vf', 'scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2',
        '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart',
        out_path
    ], desc)

# Last clip: sunset ending (0044 + 0045 combined)
print(f"  Clip 29: Sunset ending (0044 + 0045 combined)")
sunset_a = os.path.join(OUT, 'sunset_a.mp4')
sunset_b = os.path.join(OUT, 'sunset_b.mp4')
sunset_combined = os.path.join(OUT, 'clip_29.mp4')

run_ff([
    FFMPEG, '-y', '-ss', '1.0', '-i', os.path.join(HI, 'DJI_20260404181954_0044_D.MP4'),
    '-t', str(CLIP_DUR / 2),
    '-vf', 'scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2',
    '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-an', sunset_a
], "sunset A")

run_ff([
    FFMPEG, '-y', '-ss', '0.3', '-i', os.path.join(HI, 'DJI_20260404182001_0045_D.MP4'),
    '-t', str(CLIP_DUR / 2),
    '-vf', 'scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2',
    '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-an', sunset_b
], "sunset B")

sunset_list = os.path.join(OUT, 'sunset_list.txt')
with open(sunset_list, 'w') as f:
    f.write(f"file '{sunset_a}'\nfile '{sunset_b}'\n")
run_ff([
    FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', sunset_list,
    '-c', 'copy', sunset_combined
], "sunset concat")
trimmed_clips.append(sunset_combined)

# ============================================================
# STEP 3: Merge LA clips (0-14) and Hawaii clips (15-29)
# ============================================================
print("\n=== Step 3: Merging LA section ===")
la_list = os.path.join(OUT, 'la_list.txt')
with open(la_list, 'w') as f:
    for clip in trimmed_clips[:15]:
        f.write(f"file '{clip}'\n")

la_section = os.path.join(OUT, 'la_section.mp4')
run_ff([
    FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', la_list,
    '-c', 'copy', '-movflags', '+faststart', la_section
], "LA merge")
la_dur = get_duration(la_section)
print(f"  LA section: {la_dur:.1f}s")

print("\n=== Step 4: Merging Hawaii section ===")
hi_list = os.path.join(OUT, 'hi_list.txt')
with open(hi_list, 'w') as f:
    for clip in trimmed_clips[15:]:
        f.write(f"file '{clip}'\n")

hi_section = os.path.join(OUT, 'hi_section.mp4')
run_ff([
    FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', hi_list,
    '-c', 'copy', '-movflags', '+faststart', hi_section
], "HI merge")
hi_dur = get_duration(hi_section)
print(f"  Hawaii section: {hi_dur:.1f}s")

# ============================================================
# STEP 4: Add fade transition between LA and Hawaii
# ============================================================
print("\n=== Step 5: Adding LA->Hawaii dissolve transition ===")
transition_dur = 1.0
merged_body = os.path.join(OUT, 'merged_body.mp4')

run_ff([
    FFMPEG, '-y', '-i', la_section, '-i', hi_section,
    '-filter_complex',
    f'[0:v][1:v]xfade=transition=fade:duration={transition_dur}:offset={la_dur - transition_dur}[v]',
    '-map', '[v]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    merged_body
], "xfade transition")
body_dur = get_duration(merged_body)
print(f"  Merged body: {body_dur:.1f}s")

# ============================================================
# STEP 5: Combine intro + body
# ============================================================
print("\n=== Step 6: Combining intro + body ===")
final_list = os.path.join(OUT, 'final_list.txt')
with open(final_list, 'w') as f:
    f.write(f"file '{intro_4k}'\n")
    f.write(f"file '{merged_body}'\n")

combined_no_audio = os.path.join(OUT, 'combined_no_audio.mp4')
run_ff([
    FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', final_list,
    '-c', 'copy', '-movflags', '+faststart', combined_no_audio
], "concat intro+body")
total_dur = get_duration(combined_no_audio)
print(f"  Combined video: {total_dur:.1f}s")

# ============================================================
# STEP 6: Add BGM with fade in/out
# ============================================================
print("\n=== Step 7: Adding BGM ===")
final_output = os.path.join(BASE, 'US_Trip_2026_Final_v2.mp4')
fade_out_start = total_dur - 3.0

run_ff([
    FFMPEG, '-y',
    '-i', combined_no_audio,
    '-i', BGM,
    '-filter_complex',
    f'[1:a]atrim=0:{total_dur},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_start}:d=3.0,asetpts=PTS-STARTPTS[a]',
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k',
    '-shortest',
    '-movflags', '+faststart',
    final_output
], "add BGM")

final_dur = get_duration(final_output)
final_size = os.path.getsize(final_output)
print(f"\n{'='*50}")
print(f"DONE! Final video: {final_output}")
print(f"Duration: {final_dur:.1f}s")
print(f"Size: {final_size // 1024 // 1024}MB")
print(f"Resolution: 3840x2160 (4K)")
print(f"{'='*50}")
