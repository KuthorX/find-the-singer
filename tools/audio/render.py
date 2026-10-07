"""Render the MIDI score with FluidSynth + MS Basic.sf3 and master the results.

Loops are rendered 3x back to back and the middle copy is kept, so reverb
tails wrap across the seam. Gameplay stems share one gain so their balance
is preserved; the full mix (all stems) lands on -18 LUFS.
"""

import os
import subprocess

import numpy as np

import score
from dsp import SR, db, lufs, read_wav, true_peak_db, write_wav

SOUNDFONT = "/Applications/MuseScore 4.app/Contents/Resources/sound/MS Basic.sf3"
MUSIC_LUFS = -18.0
JINGLE_LUFS = -17.0
PEAK_CEILING_DB = -1.5  # dBTP, leaves room for mp3 overshoot


def fluidsynth(mid: str, wav: str) -> np.ndarray:
    subprocess.run(
        ["fluidsynth", "-ni", "-q", "-g", "0.6", "-F", wav, "-r", str(SR), SOUNDFONT, mid],
        check=True,
    )
    return read_wav(wav)


def loop_slice(x: np.ndarray, bars: int, bpm: float) -> np.ndarray:
    length = int(round(bars * 4 * 60 / bpm * SR))
    assert len(x) >= 2 * length + 1, "render shorter than two loops"
    return x[length:2 * length]


def mp3(wav: str, out: str, kbps: int, mono: bool = False) -> None:
    args = ["lame", "--quiet", "--noreplaygain", "-q", "2", "-b", str(kbps)]
    if mono:
        args += ["-m", "m", "-a"]
    subprocess.run(args + [wav, out], check=True)


def trim_tail(x: np.ndarray, floor_db: float = -60.0, fade_ms: float = 80.0) -> np.ndarray:
    level = np.max(np.abs(x), axis=1)
    above = np.nonzero(level > db(floor_db))[0]
    end = min(len(x), (above[-1] if len(above) else len(x)) + int(0.05 * SR))
    y = x[:end].copy()
    n = int(fade_ms / 1000 * SR)
    y[-n:] *= np.linspace(1, 0, n)[:, None]
    return y


def run_down(x: np.ndarray, start_frac: float = 0.35, end_rate: float = 0.55) -> np.ndarray:
    """Music-box spring running out: playback rate glides from 1 to end_rate."""
    n = len(x)
    s = int(n * start_frac)
    rate = np.ones(n * 2)
    ramp_len = n * 2 - s
    rate[s:] = 1 + (end_rate - 1) * np.linspace(0, 1, ramp_len) ** 1.3
    pos = np.concatenate([[0], np.cumsum(rate)])
    pos = pos[pos < n - 1]
    idx = np.arange(n)
    return np.stack([np.interp(pos, idx, x[:, c]) for c in range(x.shape[1])], axis=1)


def master_loops(build: str, out_dir: str) -> dict:
    report = {}
    stems = ["play_base", "play_mel1", "play_mel2", "play_mel3", "play_mel4"]
    loops = {}
    for name in stems:
        raw = fluidsynth(f"{build}/midi/{name}.mid", f"{build}/{name}_raw.wav")
        loops[name] = loop_slice(raw, len(score.PLAY_CHORDS), score.PLAY_BPM)
    n = min(len(v) for v in loops.values())
    mix = sum(v[:n] for v in loops.values())
    gain = db(MUSIC_LUFS - lufs(mix))
    peak = true_peak_db(mix * gain)
    if peak > PEAK_CEILING_DB:
        gain *= db(PEAK_CEILING_DB - peak)
    for name in stems:
        y = loops[name][:n] * gain
        wav = f"{build}/{name}.wav"
        write_wav(wav, y)
        mp3(wav, f"{out_dir}/{name}.mp3", 128 if name == "play_base" else 80, mono=name != "play_base")
        report[name] = (len(y) / SR, lufs(y), true_peak_db(y))
    write_wav(f"{build}/play_full.wav", mix * gain)
    report["play_full(mix)"] = (n / SR, lufs(mix * gain), true_peak_db(mix * gain))

    raw = fluidsynth(f"{build}/midi/menu.mid", f"{build}/menu_raw.wav")
    y = loop_slice(raw, len(score.MENU_CHORDS), score.MENU_BPM)
    y = y * db(MUSIC_LUFS - lufs(y))
    peak = true_peak_db(y)
    if peak > PEAK_CEILING_DB:
        y *= db(PEAK_CEILING_DB - peak)
    write_wav(f"{build}/menu.wav", y)
    mp3(f"{build}/menu.wav", f"{out_dir}/menu.mp3", 128)
    report["menu"] = (len(y) / SR, lufs(y), true_peak_db(y))
    return report


def master_jingles(build: str, out_dir: str) -> dict:
    report = {}
    for name in ("jingle_complete", "jingle_gameover"):
        raw = fluidsynth(f"{build}/midi/{name}.mid", f"{build}/{name}_raw.wav")
        y = trim_tail(raw)
        if name == "jingle_gameover":
            y = trim_tail(run_down(y))
        y = y * db(JINGLE_LUFS - lufs(y))
        peak = true_peak_db(y)
        if peak > PEAK_CEILING_DB:
            y *= db(PEAK_CEILING_DB - peak)
        write_wav(f"{build}/{name}.wav", y)
        mp3(f"{build}/{name}.wav", f"{out_dir}/{name}.mp3", 128)
        report[name] = (len(y) / SR, lufs(y), true_peak_db(y))
    return report


def main(build: str, music_dir: str, sfx_dir: str) -> None:
    os.makedirs(f"{build}/midi", exist_ok=True)
    os.makedirs(music_dir, exist_ok=True)
    os.makedirs(sfx_dir, exist_ok=True)
    score.main(f"{build}/midi")
    report = master_loops(build, music_dir)
    report.update(master_jingles(build, sfx_dir))
    for name, (dur, loud, peak) in report.items():
        print(f"{name:18s} {dur:7.2f}s {loud:6.1f} LUFS {peak:6.1f} dBTP")


if __name__ == "__main__":
    import sys

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    build_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fts_audio"
    main(build_dir, f"{root}/audio/music", f"{root}/audio/sfx")
