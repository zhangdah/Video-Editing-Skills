"""
US Trip 2026 - Video Edit v3
Remove 3 couple clips from v2: clip_09, clip_26, clip_27
Re-merge and re-add BGM.
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

# Clips to REMOVE: 09 (street couple selfie), 26 (laughing palms), 27 (sunset beach couple)
remove_set = {9, 26, 27}

# LA clips: 00-14, minus 09
la_clips = [os.path.join(OUT, f'clip_{i:02d}.mp4') for i in range(15) if i not in remove_set]
# Hawaii clips: 15-25, 28(was27 in old), 29
hi_clips = [os.path.join(OUT, f'clip_{i:02d}.mp4') for i in range(15, 28) if i not in remove_set]
hi_clips.append(os.path.join(OUT, 'clip_29.mp4'))

print(f"LA clips: {len(la_clips)}", flush=True)
print(f"Hawaii clips: {len(hi_clips)}", flush=True)

# Merge LA
print("\nMerging LA section...", flush=True)
la_list = os.path.join(OUT, 'la_list_v3.txt')
with open(la_list, 'w') as f:
    for c in la_clips:
        f.write(f"file '{c}'\n")

la_section = os.path.join(OUT, 'la_section_v3.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', la_list, '-c', 'copy', la_section], "LA merge")
la_dur = get_duration(la_section)
print(f"  LA: {la_dur:.1f}s", flush=True)

# Merge Hawaii
print("Merging Hawaii section...", flush=True)
hi_list = os.path.join(OUT, 'hi_list_v3.txt')
with open(hi_list, 'w') as f:
    for c in hi_clips:
        f.write(f"file '{c}'\n")

hi_section = os.path.join(OUT, 'hi_section_v3.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', hi_list, '-c', 'copy', hi_section], "HI merge")
hi_dur = get_duration(hi_section)
print(f"  Hawaii: {hi_dur:.1f}s", flush=True)

# Transition
print("Adding dissolve transition...", flush=True)
merged_body = os.path.join(OUT, 'merged_body_v3.mp4')
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
final_list = os.path.join(OUT, 'final_list_v3.txt')
with open(final_list, 'w') as f:
    f.write(f"file '{intro_4k}'\n")
    f.write(f"file '{merged_body}'\n")

combined = os.path.join(OUT, 'combined_v3.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', final_list, '-c', 'copy', combined], "concat")
total_dur = get_duration(combined)
print(f"  Total: {total_dur:.1f}s", flush=True)

# Add BGM
print("Adding BGM...", flush=True)
final_output = os.path.join(BASE, 'US_Trip_2026_Final_v3.mp4')
fade_out_start = total_dur - 3.0

run_ff([
    FFMPEG, '-y',
    '-i', combined, '-i', BGM,
    '-filter_complex',
    f'[1:a]atrim=0:{total_dur},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_start}:d=3.0,asetpts=PTS-STARTPTS[a]',
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
