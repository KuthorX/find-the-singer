"""Report duration / LUFS / true peak for every shipped audio file, check loop
seams and draw spectrograms. Usage: python3 analyze.py [spectrogram_dir]"""

import glob
import os
import subprocess
import sys

import numpy as np

from dsp import SR, lufs, read_wav, true_peak_db

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOOPS = ("menu", "play_base", "play_mel1", "play_mel2", "play_mel3", "play_mel4")


def decode(path: str, tmp: str) -> np.ndarray:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ar", str(SR), "-c:a", "pcm_s16le", tmp], check=True)
    return read_wav(tmp)


def seam(x: np.ndarray) -> str:
    """Wrap-around step vs. the largest step inside the 50 ms windows on either side."""
    w = int(0.05 * SR)
    joined = np.concatenate([x[-w:], x[:w]])
    steps = np.abs(np.diff(joined, axis=0)).max(axis=1)
    wrap = steps[w - 1]
    inner = np.delete(steps, w - 1).max()
    rms_end = np.sqrt(np.mean(x[-w:] ** 2))
    rms_start = np.sqrt(np.mean(x[:w] ** 2))
    ok = wrap <= inner * 1.05
    return (f"seam step {wrap:.4f} vs max inner {inner:.4f}, rms end/start "
            f"{20*np.log10(rms_end+1e-9):.1f}/{20*np.log10(rms_start+1e-9):.1f} dB -> {'OK' if ok else 'CHECK'}")


def main(spec_dir: str) -> None:
    os.makedirs(spec_dir, exist_ok=True)
    files = sorted(glob.glob(f"{ROOT}/audio/music/*.mp3") + glob.glob(f"{ROOT}/audio/sfx/*.wav")
                   + glob.glob(f"{ROOT}/audio/sfx/*.mp3"))
    total = 0
    for path in files:
        total += os.path.getsize(path)
        name = os.path.splitext(os.path.basename(path))[0]
        x = decode(path, f"{spec_dir}/_tmp.wav")
        line = f"{name:18s} {len(x)/SR:7.3f}s {lufs(x):6.1f} LUFS {true_peak_db(x):6.1f} dBTP"
        if name in LOOPS:
            line += "  " + seam(x)
        print(line)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-lavfi",
                        "showspectrumpic=s=800x300:legend=0", f"{spec_dir}/{name}.png"], check=True)
    os.remove(f"{spec_dir}/_tmp.wav")
    print(f"total audio size: {total/1024/1024:.2f} MB in {len(files)} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/fts_audio/spec")
