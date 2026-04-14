from mcp_video import Client
import os, static_ffmpeg
static_ffmpeg.add_paths()

editor = Client()
base = r'C:\Video Editing\2026 US Trip'

for folder in ['LA', 'Hawaii']:
    folder_path = os.path.join(base, folder)
    files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.mp4')])
    print(f"\n=== {folder} ({len(files)} files) ===")
    total = 0
    for f in files:
        fp = os.path.join(folder_path, f)
        try:
            info = editor.info(fp)
            dur = info.duration
            total += dur
            print(f"  {f}: {dur:.1f}s  {info.resolution}  {info.fps}fps  {info.size_mb:.0f}MB")
        except Exception as e:
            print(f"  {f}: ERROR - {e}")
    print(f"  TOTAL: {total:.0f}s ({total/60:.1f} min)")
