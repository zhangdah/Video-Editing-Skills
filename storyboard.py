from mcp_video import Client
import os, static_ffmpeg
static_ffmpeg.add_paths()

editor = Client()
base = r'C:\Video Editing\2026 US Trip'

for folder in ['LA', 'Hawaii']:
    folder_path = os.path.join(base, folder)
    out_dir = os.path.join(base, f'{folder}_storyboards')
    os.makedirs(out_dir, exist_ok=True)
    files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.mp4')])
    for f in files:
        fp = os.path.join(folder_path, f)
        name = os.path.splitext(f)[0]
        try:
            result = editor.storyboard(fp, output_dir=out_dir, frame_count=4)
            print(f"  {f}: grid -> {result.grid}")
        except Exception as e:
            print(f"  {f}: ERROR - {e}")
