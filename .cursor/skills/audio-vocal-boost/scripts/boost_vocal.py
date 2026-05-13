#!/usr/bin/env python3
"""
boost_vocal.py — Separate vocals from instrumental in a video and re-mix
with user-specified gains, then mux back into the original video without
re-encoding the video stream.

Pipeline:
    src.mp4
      └─ ffmpeg          → audio.wav             (lossless extract)
           └─ demucs     → vocals.wav + no_vocals.wav
                └─ ffmpeg amix + alimiter → audio_boosted.wav
                     └─ ffmpeg copy video + new aac audio → out.mp4

Stems are cached in --workdir so re-running with new dB values takes ~10s.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import static_ffmpeg

static_ffmpeg.add_paths()

DEFAULT_MODEL = "htdemucs_ft"
LIMITER = "alimiter=limit=0.95:attack=5:release=50"


def run(cmd: list[str], err_label: str) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:])
        raise SystemExit(f"{err_label} failed (exit {r.returncode})")


def loudness(path: Path) -> tuple[str, str]:
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    mean = peak = "?"
    for line in r.stderr.splitlines():
        if "mean_volume" in line:
            mean = line.split("mean_volume:")[1].strip()
        if "max_volume" in line:
            peak = line.split("max_volume:")[1].strip()
    return mean, peak


def extract_audio(src: Path, dst: Path) -> None:
    run(
        ["ffmpeg", "-y", "-i", str(src),
         "-map", "0:a:0", "-ac", "2", "-ar", "48000",
         "-c:a", "pcm_s16le", str(dst)],
        "extract_audio",
    )


def run_demucs(audio_wav: Path, output_dir: Path, model: str, device: str) -> None:
    run(
        [sys.executable, "-m", "demucs",
         "--two-stems=vocals", "-d", device, "-n", model,
         "-o", str(output_dir), str(audio_wav)],
        f"demucs ({model})",
    )


def mix(vocal: Path, instr: Path, vocal_db: float, instr_db: float, out: Path) -> None:
    fc = (
        f"[0:a]volume={vocal_db}dB[v];"
        f"[1:a]volume={instr_db}dB[i];"
        "[v][i]amix=inputs=2:duration=longest:normalize=0[mix];"
        f"[mix]{LIMITER}[a]"
    )
    run(
        ["ffmpeg", "-y", "-i", str(vocal), "-i", str(instr),
         "-filter_complex", fc, "-map", "[a]",
         "-c:a", "pcm_s16le", "-ar", "48000", str(out)],
        "mix",
    )


def mux(src_video: Path, audio_wav: Path, out_video: Path) -> None:
    run(
        ["ffmpeg", "-y", "-i", str(src_video), "-i", str(audio_wav),
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-movflags", "+faststart", str(out_video)],
        "mux",
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Boost vocals (or instrumental) in a video via AI source separation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("input", help="Source video file (.mov, .mp4, etc.)")
    p.add_argument("-o", "--output",
                   help="Output video path (default: <input>_vocal_boost.mp4 next to input)")
    p.add_argument("--vocal-db", type=float, default=4.0,
                   help="Gain for the vocal stem (singing + speech)")
    p.add_argument("--instr-db", type=float, default=0.0,
                   help="Gain for the instrumental stem (music + ambient)")
    p.add_argument("--workdir",
                   help="Stem cache dir (default: <input_dir>/output/vocal_boost_<stem>)")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   choices=["htdemucs", "htdemucs_ft", "mdx_extra"],
                   help="demucs model (htdemucs_ft = best quality, slowest)")
    p.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"],
                   help="Compute device. NOTE: htdemucs/htdemucs_ft FAIL on mps "
                        "(known PyTorch limit on Apple GPU). Use cpu.")
    p.add_argument("--force-demucs", action="store_true",
                   help="Re-run demucs even if cached stems exist")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    src = Path(args.input).resolve()
    if not src.exists():
        raise SystemExit(f"Not found: {src}")

    out = Path(args.output).resolve() if args.output \
        else src.with_name(f"{src.stem}_vocal_boost.mp4")

    workdir = Path(args.workdir).resolve() if args.workdir \
        else src.parent / "output" / f"vocal_boost_{src.stem}"
    workdir.mkdir(parents=True, exist_ok=True)

    audio_wav = workdir / "audio.wav"
    stems_dir = workdir / "stems"
    vocal_wav = stems_dir / args.model / "audio" / "vocals.wav"
    instr_wav = stems_dir / args.model / "audio" / "no_vocals.wav"
    mixed_wav = workdir / "audio_boosted.wav"

    print(f"Input:   {src}")
    print(f"Output:  {out}")
    print(f"Workdir: {workdir}")
    print(f"Mix:     vocal {args.vocal_db:+.1f} dB   instr {args.instr_db:+.1f} dB   "
          f"(+ alimiter)")
    print()

    if not audio_wav.exists():
        print("[1/4] Extracting audio from video ...", flush=True)
        t0 = time.time()
        extract_audio(src, audio_wav)
        print(f"      OK in {time.time()-t0:.1f}s  ({audio_wav.stat().st_size/1e6:.1f} MB)")
    else:
        print(f"[1/4] audio.wav cached ({audio_wav.stat().st_size/1e6:.1f} MB)")

    if args.force_demucs or not (vocal_wav.exists() and instr_wav.exists()):
        print(f"[2/4] Running demucs {args.model} on {args.device.upper()} "
              f"(SLOW: ~5-15 min on CPU for ~4 min audio) ...", flush=True)
        t0 = time.time()
        run_demucs(audio_wav, stems_dir, args.model, args.device)
        print(f"      OK in {time.time()-t0:.1f}s")
    else:
        print(f"[2/4] stems cached ({vocal_wav.parent})")

    print(f"[3/4] Mixing vocal {args.vocal_db:+.1f}dB / instr {args.instr_db:+.1f}dB "
          f"+ limiter ...", flush=True)
    t0 = time.time()
    mix(vocal_wav, instr_wav, args.vocal_db, args.instr_db, mixed_wav)
    print(f"      OK in {time.time()-t0:.1f}s")

    print("[4/4] Muxing video (copy) + new audio (AAC 256k) ...", flush=True)
    t0 = time.time()
    mux(src, mixed_wav, out)
    print(f"      OK in {time.time()-t0:.1f}s")

    om, op = loudness(audio_wav)
    nm, np_ = loudness(mixed_wav)
    print()
    print(f"Done -> {out}")
    print(f"Size:   {out.stat().st_size/1e6:.1f} MB")
    print(f"Loudness: original mean={om:>8s} peak={op:>8s}")
    print(f"          boosted  mean={nm:>8s} peak={np_:>8s}")


if __name__ == "__main__":
    main()
