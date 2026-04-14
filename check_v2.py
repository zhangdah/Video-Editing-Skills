import subprocess, json, static_ffmpeg
static_ffmpeg.add_paths()

fp = r'C:\Video Editing\2026 US Trip\US_Trip_2026_Final_v2.mp4'
probe = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', fp],
    capture_output=True, text=True
)
for s in json.loads(probe.stdout)['streams']:
    t = s['codec_type']
    if t == 'video':
        print(f"Video: {s['codec_name']} profile={s.get('profile','?')} pix_fmt={s.get('pix_fmt','?')} {s['width']}x{s['height']}")
    else:
        print(f"Audio: {s['codec_name']} profile={s.get('profile','?')}")
