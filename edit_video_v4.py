"""
US Trip 2026 - Video Edit v4
- Remove sunset ending clip (29)
- Reorder Hawaii: street -> mountain -> beach
- Add fade-to-black ending
"""
import os
import subprocess
import json
import static_ffmpeg
static_ffmpeg.add_paths()

BASE = r'C:\Video Editing\2026 US Trip'
OUT = os.path.join(BASE, 'output_v2')
BGM = os.path.join(BASE, 'music', '01_Sunshine_Smiles_Chill_HipHop.mp3')
FFMPEG = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE'
FFPROBE = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffprobe.EXE'

def run_ff(cmd, desc=""):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ERROR ({desc}): {result.stderr[-300:]}", flush=True)
        return False
    return True

def get_duration(path):
    probe = subprocess.run(
        [FFPROBE, '-v', 'quiet', '-print_format', 'json', '-show_format', path],
        capture_output=True, text=True
    )
    return float(json.loads(probe.stdout)['format']['duration'])

# LA clips: same as v3 (removed 09)
la_clips = [os.path.join(OUT, f'clip_{i:02d}.mp4') for i in range(15) if i != 9]

# Hawaii clips: reordered - street -> mountain -> beach
# Street: 21 (Honolulu street), 25 (Kalakaua Ave), 22 (eating snack), 23 (driving)
# Mountain: 18 (Ko'olau mountains), 19 (tropical rainforest), 20 (mountain McD)
# Beach: 15 (beach plaza), 16 (Waikiki Diamond Head), 17 (Waikiki crowd), 24 (beach couple)
hi_order = [21, 25, 22, 23, 18, 19, 20, 15, 16, 17, 24]
hi_clips = [os.path.join(OUT, f'clip_{i:02d}.mp4') for i in hi_order]

print(f"LA clips: {len(la_clips)}", flush=True)
print(f"Hawaii clips: {len(hi_clips)}", flush=True)
print(f"Hawaii order: street(21,25,22,23) -> mountain(18,19,20) -> beach(15,16,17,24)", flush=True)

# Merge LA
print("\nMerging LA section...", flush=True)
la_list = os.path.join(OUT, 'la_list_v4.txt')
with open(la_list, 'w') as f:
    for c in la_clips:
        f.write(f"file '{c}'\n")

la_section = os.path.join(OUT, 'la_section_v4.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', la_list, '-c', 'copy', la_section], "LA merge")
la_dur = get_duration(la_section)
print(f"  LA: {la_dur:.1f}s", flush=True)

# Merge Hawaii
print("Merging Hawaii section...", flush=True)
hi_list = os.path.join(OUT, 'hi_list_v4.txt')
with open(hi_list, 'w') as f:
    for c in hi_clips:
        f.write(f"file '{c}'\n")

hi_section = os.path.join(OUT, 'hi_section_v4.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', hi_list, '-c', 'copy', hi_section], "HI merge")
hi_dur = get_duration(hi_section)
print(f"  Hawaii: {hi_dur:.1f}s", flush=True)

# Transition LA -> Hawaii
print("Adding LA->Hawaii dissolve...", flush=True)
merged_body = os.path.join(OUT, 'merged_body_v4.mp4')
run_ff([
    FFMPEG, '-y', '-i', la_section, '-i', hi_section,
    '-filter_complex',
    f'[0:v][1:v]xfade=transition=fade:duration=1.0:offset={la_dur - 1.0}[v]',
    '-map', '[v]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    merged_body
], "xfade")
body_dur = get_duration(merged_body)
print(f"  Body: {body_dur:.1f}s", flush=True)

# Combine intro + body
print("Combining intro + body...", flush=True)
intro_4k = os.path.join(OUT, 'intro_4k.mp4')
final_list = os.path.join(OUT, 'final_list_v4.txt')
with open(final_list, 'w') as f:
    f.write(f"file '{intro_4k}'\n")
    f.write(f"file '{merged_body}'\n")

combined = os.path.join(OUT, 'combined_v4.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', final_list, '-c', 'copy', combined], "concat")
total_dur = get_duration(combined)
print(f"  Total before fade: {total_dur:.1f}s", flush=True)

# Add fade-to-black ending (last 2 seconds)
print("Adding fade-to-black ending...", flush=True)
fade_start = total_dur - 2.0
combined_faded = os.path.join(OUT, 'combined_v4_faded.mp4')
run_ff([
    FFMPEG, '-y', '-i', combined,
    '-vf', f'fade=t=out:st={fade_start}:d=2.0:color=black',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart',
    combined_faded
], "fade to black")
print(f"  Fade-to-black applied at {fade_start:.1f}s", flush=True)

# Add BGM
print("Adding BGM...", flush=True)
final_output = os.path.join(BASE, 'US_Trip_2026_Final_v4.mp4')
fade_out_audio = total_dur - 3.0

run_ff([
    FFMPEG, '-y',
    '-i', combined_faded, '-i', BGM,
    '-filter_complex',
    f'[1:a]atrim=0:{total_dur},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_audio}:d=3.0,asetpts=PTS-STARTPTS[a]',
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
    '-shortest', '-movflags', '+faststart',
    final_output
], "BGM")

final_dur = get_duration(final_output)
final_size = os.path.getsize(final_output)
print(f"\n{'='*50}", flush=True)
print(f"DONE! {final_output}", flush=True)
print(f"Duration: {final_dur:.1f}s", flush=True)
print(f"Size: {final_size // 1024 // 1024}MB", flush=True)
print(f"{'='*50}", flush=True)
