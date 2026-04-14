import os, subprocess, json, static_ffmpeg
static_ffmpeg.add_paths()

base = r'C:\Video Editing\2026 US Trip'
ffprobe = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffprobe.EXE'
ffmpeg = r'C:\Users\dahon\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE'

for folder in ['LA', 'Hawaii']:
    folder_path = os.path.join(base, folder)
    out_dir = os.path.join(base, f'{folder}_storyboards')
    os.makedirs(out_dir, exist_ok=True)
    files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.mp4')])
    
    for f in files:
        fp = os.path.join(folder_path, f)
        name = os.path.splitext(f)[0]
        out_file = os.path.join(out_dir, f'{name}_mid.jpg')
        
        if os.path.exists(out_file):
            print(f"  SKIP {f} (already done)")
            continue

        probe = subprocess.run(
            [ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_format', fp],
            capture_output=True, text=True
        )
        dur = float(json.loads(probe.stdout)['format']['duration'])
        mid = dur / 2

        subprocess.run(
            [ffmpeg, '-y', '-ss', str(mid), '-i', fp, '-frames:v', '1',
             '-vf', 'scale=480:-1', '-q:v', '5', out_file],
            capture_output=True
        )
        print(f"  {f}: frame@{mid:.1f}s -> {out_file}")

print("\nDone!")
