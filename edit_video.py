"""
Beat-synced video edit for 2026 US Trip (LA + Hawaii)
BGM: Sunshine Smiles (01) - ~160 BPM (felt as ~80 BPM)
Target: ~60s total, beat-matched cuts

Each "measure" = 4 beats @ ~1.49s
We cut on measure boundaries for clean beat-sync.
"""
import os
import subprocess
import json
import static_ffmpeg
static_ffmpeg.add_paths()

BASE = r'C:\Video Editing\2026 US Trip'
LA = os.path.join(BASE, 'LA')
HI = os.path.join(BASE, 'Hawaii')
OUT = os.path.join(BASE, 'output')
BGM = os.path.join(BASE, 'music', '01_Sunshine_Smiles_Chill_HipHop.mp3')
FFMPEG = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE'
FFPROBE = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffprobe.EXE'

os.makedirs(OUT, exist_ok=True)

MEASURE_DUR = 1.493  # 4 beats at 160.7 BPM

# --- CUT LIST ---
# Each entry: (source_file, start_time_in_source, duration_in_measures, description)
# LA section: measures 1-20 (~29.9s)
# Transition: measure 21 (dissolve ~1.5s)
# Hawaii section: measures 21-40 (~29.9s)
# Total: ~60s

cuts = [
    # === LA SECTION (measures 1-20, ~29.9s) ===
    # Opening: Griffith Observatory panorama
    (os.path.join(LA, 'DJI_20260329091659_0909_D.MP4'), 1.0, 2, "Griffith city view"),
    # LA evening palms
    (os.path.join(LA, 'LA1.MP4'), 5.0, 2, "LA evening palm street"),
    # Beverly Hills palm road
    (os.path.join(LA, 'LA4.MP4'), 4.0, 2, "Beverly Hills palms"),
    # Couple selfie at beach
    (os.path.join(LA, 'DJI_20260329141537_0921_D.MP4'), 28.0, 2, "Beach couple selfie"),
    # Looking at the beach
    (os.path.join(LA, 'DJI_20260329141644_0922_D.MP4'), 3.0, 2, "Looking at beach"),
    # Boardwalk selfie
    (os.path.join(LA, 'DJI_20260329141727_0923_D.MP4'), 5.0, 2, "Boardwalk selfie"),
    # Palm tree couple
    (os.path.join(LA, 'DJI_20260329141956_0924_D.MP4'), 10.0, 2, "Palm tree couple"),
    # Coastal road drive palms
    (os.path.join(LA, 'DJI_20260329151216_0941_D.MP4'), 28.0, 2, "Coastal road palms"),
    # Flower street walk
    (os.path.join(LA, 'DJI_20260329154240_0944_D.MP4'), 20.0, 2, "Flower street walk"),
    # Arms spread intersection
    (os.path.join(LA, 'DJI_20260329154450_0947_D.MP4'), 5.0, 2, "Arms spread freedom"),

    # === HAWAII SECTION (measures 21-40, ~29.9s) ===
    # Waikiki beach Diamond Head
    (os.path.join(HI, 'DJI_20260401125853_0969_D.MP4'), 2.0, 2, "Waikiki Diamond Head"),
    # Beach couple selfie Hawaii
    (os.path.join(HI, 'DJI_20260401132027_0971_D.MP4'), 12.0, 2, "Hawaii beach selfie"),
    # Kalakaua Ave peace sign
    (os.path.join(HI, 'DJI_20260401132359_0977_D.MP4'), 8.0, 2, "Kalakaua peace sign"),
    # Ko'olau mountains palms
    (os.path.join(HI, 'DJI_20260402152637_0003_D.MP4'), 25.0, 2, "Koolau mountains"),
    # Tropical rainforest green
    (os.path.join(HI, 'DJI_20260402152810_0004_D.MP4'), 40.0, 2, "Tropical rainforest"),
    # Tropical garden flowers
    (os.path.join(HI, 'DJI_20260402153249_0020_D.MP4'), 10.0, 2, "Tropical garden"),
    # Garden pond
    (os.path.join(HI, 'DJI_20260402154310_0028_D.MP4'), 5.0, 2, "Garden pond"),
    # Sunset beach couple
    (os.path.join(HI, 'DJI_20260404181912_0042_D.MP4'), 5.0, 2, "Sunset beach couple"),
    # Sunset silhouette
    (os.path.join(HI, 'DJI_20260404181954_0044_D.MP4'), 1.0, 2, "Sunset silhouette"),
    # Sunset palm twirl - ENDING
    (os.path.join(HI, 'DJI_20260404182001_0045_D.MP4'), 0.5, 2, "Sunset twirl ending"),
]

# Step 1: Trim each clip to exact beat-synced duration
print("=== Step 1: Trimming clips ===")
trimmed_clips = []
for i, (src, start, measures, desc) in enumerate(cuts):
    dur = measures * MEASURE_DUR
    out_path = os.path.join(OUT, f'clip_{i:02d}.mp4')
    trimmed_clips.append(out_path)

    cmd = [
        FFMPEG, '-y',
        '-ss', str(start),
        '-i', src,
        '-t', str(dur),
        '-vf', 'scale=1920:1080',
        '-r', '30',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-an',
        '-movflags', '+faststart',
        out_path
    ]
    print(f"  Clip {i:02d}: {desc} ({dur:.2f}s from {os.path.basename(src)})")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ERROR: {result.stderr[-200:]}")

# Step 2: Build concat file
print("\n=== Step 2: Concatenating clips ===")
concat_file = os.path.join(OUT, 'concat_list.txt')
with open(concat_file, 'w') as f:
    for clip in trimmed_clips:
        f.write(f"file '{clip}'\n")

concat_video = os.path.join(OUT, 'concat_no_transition.mp4')
cmd = [
    FFMPEG, '-y',
    '-f', 'concat', '-safe', '0',
    '-i', concat_file,
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-movflags', '+faststart',
    concat_video
]
subprocess.run(cmd, capture_output=True, text=True)
print(f"  Concatenated: {concat_video}")

# Step 3: Add crossfade transition between LA and Hawaii (at clip 10 boundary)
# LA = clips 0-9, Hawaii = clips 10-19
# We'll add a dissolve between clip 9 and clip 10
print("\n=== Step 3: Adding LA->Hawaii dissolve transition ===")

la_concat = os.path.join(OUT, 'la_section.mp4')
hi_concat = os.path.join(OUT, 'hi_section.mp4')

la_list = os.path.join(OUT, 'la_list.txt')
hi_list = os.path.join(OUT, 'hi_list.txt')

with open(la_list, 'w') as f:
    for clip in trimmed_clips[:10]:
        f.write(f"file '{clip}'\n")

with open(hi_list, 'w') as f:
    for clip in trimmed_clips[10:]:
        f.write(f"file '{clip}'\n")

for lst, out_sec in [(la_list, la_concat), (hi_list, hi_concat)]:
    cmd = [
        FFMPEG, '-y',
        '-f', 'concat', '-safe', '0', '-i', lst,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-movflags', '+faststart',
        out_sec
    ]
    subprocess.run(cmd, capture_output=True, text=True)

# Get LA duration
probe = subprocess.run(
    [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', la_concat],
    capture_output=True, text=True
)
la_dur = float(json.loads(probe.stdout)['format']['duration'])

transition_dur = 1.0
merged_with_transition = os.path.join(OUT, 'merged_with_transition.mp4')

cmd = [
    FFMPEG, '-y',
    '-i', la_concat,
    '-i', hi_concat,
    '-filter_complex',
    f'[0:v][1:v]xfade=transition=fade:duration={transition_dur}:offset={la_dur - transition_dur}[v]',
    '-map', '[v]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-movflags', '+faststart',
    merged_with_transition
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"  Transition failed, falling back to simple concat")
    print(f"  Error: {result.stderr[-300:]}")
    merged_with_transition = concat_video
else:
    print(f"  Transition applied: {merged_with_transition}")

# Step 4: Trim BGM to match video length, add audio with fade
print("\n=== Step 4: Adding BGM with fade ===")

probe = subprocess.run(
    [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', merged_with_transition],
    capture_output=True, text=True
)
video_dur = float(json.loads(probe.stdout)['format']['duration'])
print(f"  Video duration: {video_dur:.2f}s")

final_output = os.path.join(BASE, 'US_Trip_2026_Final.mp4')

fade_out_start = video_dur - 3.0

cmd = [
    FFMPEG, '-y',
    '-i', merged_with_transition,
    '-i', BGM,
    '-filter_complex',
    f'[1:a]atrim=0:{video_dur},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_start}:d=3.0,asetpts=PTS-STARTPTS[a]',
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k',
    '-shortest',
    '-movflags', '+faststart',
    final_output
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"  ERROR: {result.stderr[-300:]}")
else:
    probe = subprocess.run(
        [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', final_output],
        capture_output=True, text=True
    )
    final_info = json.loads(probe.stdout)['format']
    print(f"\n{'='*50}")
    print(f"DONE! Final video: {final_output}")
    print(f"Duration: {float(final_info['duration']):.1f}s")
    print(f"Size: {int(final_info['size'])//1024//1024}MB")
    print(f"{'='*50}")
