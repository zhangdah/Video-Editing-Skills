"""
US Trip 2026 - Video Edit v5
- Add sunset beach couple (0042) as ending, 6 seconds
- Fade-to-black over last 3 seconds of ending clip
- Audio fade-out synced
"""
import os
import subprocess
import json
import static_ffmpeg
static_ffmpeg.add_paths()

BASE = r'C:\Video Editing\2026 US Trip'
OUT = os.path.join(BASE, 'output_v2')
HI = os.path.join(BASE, 'Hawaii')
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

# Step 1: Trim a 6-second ending clip from 0042 (sunset beach couple)
print("Step 1: Trimming 6s sunset ending clip...", flush=True)
ending_clip = os.path.join(OUT, 'clip_ending_sunset.mp4')
run_ff([
    FFMPEG, '-y', '-ss', '3.0',
    '-i', os.path.join(HI, 'DJI_20260404181912_0042_D.MP4'),
    '-t', '6.0',
    '-vf', 'scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2,fade=t=out:st=3.0:d=3.0:color=black',
    '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart',
    ending_clip
], "sunset ending 6s with fade")
print(f"  Ending clip: {get_duration(ending_clip):.1f}s", flush=True)

# Step 2: Reuse v4's body parts (LA + Hawaii reordered)
# LA clips (no clip 09)
la_clips = [os.path.join(OUT, f'clip_{i:02d}.mp4') for i in range(15) if i != 9]
# Hawaii: street -> mountain -> beach (no ending yet)
hi_order = [21, 25, 22, 23, 18, 19, 20, 15, 16, 17, 24]
hi_clips = [os.path.join(OUT, f'clip_{i:02d}.mp4') for i in hi_order]

print(f"\nLA: {len(la_clips)} clips, Hawaii: {len(hi_clips)} clips + 1 ending", flush=True)

# Merge LA
print("Step 2: Merging LA...", flush=True)
la_list = os.path.join(OUT, 'la_list_v5.txt')
with open(la_list, 'w') as f:
    for c in la_clips:
        f.write(f"file '{c}'\n")
la_section = os.path.join(OUT, 'la_section_v5.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', la_list, '-c', 'copy', la_section], "LA")
la_dur = get_duration(la_section)
print(f"  LA: {la_dur:.1f}s", flush=True)

# Merge Hawaii (without ending)
print("Step 3: Merging Hawaii...", flush=True)
hi_list = os.path.join(OUT, 'hi_list_v5.txt')
with open(hi_list, 'w') as f:
    for c in hi_clips:
        f.write(f"file '{c}'\n")
hi_section = os.path.join(OUT, 'hi_section_v5.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', hi_list, '-c', 'copy', hi_section], "HI")
hi_dur = get_duration(hi_section)
print(f"  Hawaii: {hi_dur:.1f}s", flush=True)

# LA -> Hawaii dissolve
print("Step 4: LA->Hawaii dissolve...", flush=True)
merged_body = os.path.join(OUT, 'merged_body_v5.mp4')
run_ff([
    FFMPEG, '-y', '-i', la_section, '-i', hi_section,
    '-filter_complex',
    f'[0:v][1:v]xfade=transition=fade:duration=1.0:offset={la_dur - 1.0}[v]',
    '-map', '[v]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    merged_body
], "xfade LA-HI")
body_dur = get_duration(merged_body)
print(f"  Body: {body_dur:.1f}s", flush=True)

# Body -> Ending dissolve (smooth transition into sunset)
print("Step 5: Body->Ending dissolve...", flush=True)
merged_with_ending = os.path.join(OUT, 'merged_with_ending_v5.mp4')
run_ff([
    FFMPEG, '-y', '-i', merged_body, '-i', ending_clip,
    '-filter_complex',
    f'[0:v][1:v]xfade=transition=fade:duration=1.0:offset={body_dur - 1.0}[v]',
    '-map', '[v]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    merged_with_ending
], "xfade body-ending")
body_ending_dur = get_duration(merged_with_ending)
print(f"  Body+Ending: {body_ending_dur:.1f}s", flush=True)

# Combine intro + body+ending
print("Step 6: Adding intro...", flush=True)
intro_4k = os.path.join(OUT, 'intro_4k.mp4')
final_list = os.path.join(OUT, 'final_list_v5.txt')
with open(final_list, 'w') as f:
    f.write(f"file '{intro_4k}'\n")
    f.write(f"file '{merged_with_ending}'\n")

combined = os.path.join(OUT, 'combined_v5.mp4')
run_ff([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', final_list, '-c', 'copy', combined], "concat all")
total_dur = get_duration(combined)
print(f"  Total: {total_dur:.1f}s", flush=True)

# Add BGM with matching fade-out
print("Step 7: Adding BGM...", flush=True)
final_output = os.path.join(BASE, 'US_Trip_2026_Final_v5.mp4')
audio_fade_out_start = total_dur - 4.0

run_ff([
    FFMPEG, '-y',
    '-i', combined, '-i', BGM,
    '-filter_complex',
    f'[1:a]atrim=0:{total_dur},afade=t=in:st=0:d=1.5,afade=t=out:st={audio_fade_out_start}:d=4.0,asetpts=PTS-STARTPTS[a]',
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
