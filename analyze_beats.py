import librosa
import numpy as np

audio_path = r'C:\Video Editing\2026 US Trip\music\01_Sunshine_Smiles_Chill_HipHop.mp3'

y, sr = librosa.load(audio_path, sr=None)
duration = librosa.get_duration(y=y, sr=sr)

tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

tempo_val = float(np.atleast_1d(tempo)[0])

print(f"=== BGM Analysis ===")
print(f"Duration: {duration:.1f}s")
print(f"BPM: {tempo_val:.1f}")
print(f"Beat interval: {60/tempo_val:.3f}s")
print(f"Total beats detected: {len(beat_times)}")
print(f"\nFirst 60s beat timestamps:")

for i, t in enumerate(beat_times):
    if t > 65:
        break
    print(f"  Beat {i+1:3d}: {t:.3f}s")

print(f"\nBeats in groups of 4 (measures) within first 65s:")
for i in range(0, len(beat_times), 4):
    if beat_times[i] > 65:
        break
    group = beat_times[i:i+4]
    labels = [f"{t:.2f}" for t in group]
    measure_num = i // 4 + 1
    print(f"  Measure {measure_num:2d}: [{', '.join(labels)}]")
