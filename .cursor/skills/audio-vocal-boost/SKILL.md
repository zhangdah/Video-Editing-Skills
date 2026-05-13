---
name: audio-vocal-boost
description: >-
  Boost or attenuate vocals (singing / speech) versus instrumental (music /
  ambient) in a video. Uses Meta's demucs htdemucs_ft model to separate the two
  audio sources, applies user-specified gains in dB to each, runs a brick-wall
  limiter to prevent clipping, and muxes the new audio back into the original
  video without re-encoding the video stream. Use when the user wants to make
  the singer / speaker louder, soften background music, isolate a karaoke
  vocal, or any "突出人声" / "vocal boost" / "vocal isolation" task on an
  existing video file. Stems are cached so re-tuning dB values takes ~10
  seconds.
---

# Audio Vocal Boost

Given a video, separate its audio into vocal and instrumental stems, re-mix
each with user-specified gain in dB, and write back into the original video
losslessly (video stream is copied, not re-encoded — works on any resolution
including 4K@60fps).

## When to use

Trigger on requests like:
- "把视频里的人声/歌声调大一点"
- "vocal +6dB / 伴奏 -3dB"
- "突出主唱"
- "make the singer louder"
- "remove / reduce background music"

Skip this skill if:
- The user wants to **separate singer from crowd chatter**. demucs only does
  vocal-vs-instrumental; UVR karaoke models can attempt singer-vs-chatter but
  results are usually poor on hand-recorded audio. Tell the user this is a
  hard problem and the audio is what was captured.
- The audio doesn't have separable vocal+music (e.g. pure speech, pure music).

## Environment

Requires the project's `video_edit` conda env plus three extra dependencies.
**One-time setup** (skip if `python -c "import demucs, torchcodec"` succeeds):

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate video_edit
pip install demucs torchcodec "audio-separator[cpu]"
conda install -c conda-forge -y ffmpeg   # supplies libavutil that torchcodec links to
```

`torchcodec` and the conda-forge `ffmpeg` shared libs are needed by the
post-2.10 `torchaudio` backend. `audio-separator` is optional (only used if
the user later wants to try lead-vs-backing vocal sub-separation).

## Quick usage

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate video_edit
python .cursor/skills/audio-vocal-boost/scripts/boost_vocal.py path/to/video.mov \
    --vocal-db 4 --instr-db 0
# -> path/to/video_vocal_boost.mp4
```

Re-run with different dB values — stems are cached, only the 10-second mix
step re-runs:

```bash
python .cursor/skills/audio-vocal-boost/scripts/boost_vocal.py path/to/video.mov \
    --vocal-db 8 --instr-db 0     # louder vocal
```

Full CLI:

```
boost_vocal.py INPUT [-o OUTPUT] [--vocal-db N] [--instr-db N]
                     [--workdir DIR] [--model {htdemucs,htdemucs_ft,mdx_extra}]
                     [--device {cpu,mps,cuda}] [--force-demucs]
```

## Choosing dB levels

Both stems mix back into a single AAC track. A built-in limiter at -0.45 dBFS
prevents clipping no matter what gains you choose, so you can be aggressive
without artifacts (extreme settings will sound "compressed" though).

| Goal | vocal_dB | instr_dB | Effect |
|------|---------:|---------:|--------|
| Subtle vocal lift | +3 | -2 | Vocal slightly more present |
| Clear vocal focus | +4 | 0 | Default; vocal stands out, music intact |
| Strong vocal | +6 | 0 | Vocal pushes forward, music is bed |
| Very strong vocal | +8 | 0 | Singing dominates; tested limit before sounding compressed |
| Karaoke-style | -∞ (or very low) | 0 | Use `--vocal-db -100` to mute vocal entirely |
| Acapella-style | 0 | -100 | Mute the music, keep vocal |

If the user says "比 v1 更猛" / "再大一点", add 2-3 dB to vocal and re-run
(takes ~10 s).

## Workflow internals (for understanding output / debugging)

The script does four steps and reports timing for each:

1. **Extract audio** — ffmpeg pulls the first audio stream as 48 kHz / 16-bit
   PCM stereo WAV. ~1 second.
2. **demucs separation** — `python -m demucs --two-stems=vocals -n htdemucs_ft`.
   This is the slow step:
   - 4-min audio on Apple Silicon CPU: **~5-12 min** (htdemucs_ft = bag of 4
     models, all averaged).
   - Use `--model htdemucs` for ~4× faster, slightly lower quality.
   - **DO NOT use `--device mps`** for htdemucs / htdemucs_ft. There is a
     PyTorch MPS limit (`Output channels > 65536 not supported`) that crashes
     these models on Apple GPU. Stick with CPU.
3. **Mix** — ffmpeg `amix` with per-stream `volume=NdB` filters, then
   `alimiter=limit=0.95` to catch any peaks above -0.45 dBFS. Fast (<1 s).
4. **Mux** — ffmpeg `-c:v copy -c:a aac` writes the final mp4. Video stream is
   copied byte-for-byte (no quality loss, no re-encode time).
   - 4K @ 60fps 3.2 GB file: ~10-15 s.
   - 1080p file: ~3-5 s.

## Cache behavior

For input `~/path/foo.mov`, the script writes to:

```
~/path/output/vocal_boost_foo/
├── audio.wav                                    (extracted source audio)
├── stems/htdemucs_ft/audio/vocals.wav           (separated vocal)
├── stems/htdemucs_ft/audio/no_vocals.wav        (separated instrumental)
└── audio_boosted.wav                            (last remix output)
```

Steps 1 and 2 are skipped if their outputs already exist. To force a full
re-run pass `--force-demucs`.

## Common follow-ups after first run

The user will usually listen and want to tune. Don't run demucs again — just
re-run the script with new `--vocal-db` / `--instr-db`. It takes ~10 seconds
because steps 1-2 are cached.

| User says | Adjust |
|-----------|--------|
| "vocal 还是不够大" | `--vocal-db` +2 to +4 |
| "vocal 太炸了" | `--vocal-db` -2 to -3 |
| "伴奏盖过 vocal 了" | `--instr-db` -2 to -3 |
| "整体太轻" | both +2 to +3 (limiter handles peaks) |
| "想要纯 vocal" | `--instr-db -100` |

## Limitations to communicate up front

If the user wants something this skill can't deliver, say so directly:

- **Cannot separate singer from surrounding chatter.** demucs treats both as
  "vocal". UVR karaoke models (`audio-separator` with
  `mel_band_roformer_karaoke_*`) can attempt this but quality on
  amateur/handheld recordings is usually poor — the singer ends up sounding
  hollow because the model removes vocal-like content too aggressively.
- **Cannot remove specific noises** (clapping, doors, laughter). They will be
  lumped into the instrumental stem.
- **Recording quality is the ceiling.** If the singer was off-mic and the
  surroundings were loud, no model can fix that — be honest with the user.
