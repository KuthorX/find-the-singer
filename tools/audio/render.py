"""Render the score with Vital / Serum 2 / MS Basic (via /tmp/audiokit) and master it.

Stages (all offline; nothing is ever played):
  1. score.py -> MIDI (one loop each; the audiokit renderer folds the tail onto
     the loop start, so reverb and releases wrap across the seam).
  2. One audiokit process renders every spec under the shared render lock and
     writes a stem per instrument.
  3. Mastering here: per-instrument trims, loop folding, gameplay stems grouped
     with one shared gain (the full mix lands on -18 LUFS), jingles, Ogg Vorbis export.

Run with the audiokit venv:
  arch -arm64 /tmp/audiokit/venv/bin/python tools/audio/render.py [build_dir] [--master-only]
"""

import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, "/tmp/audiokit")
import mixing as M  # noqa: E402  (audiokit)

import orchestra as O  # noqa: E402
import score  # noqa: E402
import sfx_bank  # noqa: E402

SR = 44100
AUDIOKIT_PY = ["arch", "-arm64", "/tmp/audiokit/venv/bin/python"]
LOCK = ["lockf", "-t", "3600", "/tmp/audiokit/render.lock"]
HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC_LUFS = -18.0
JINGLE_LUFS = -17.0
PEAK_CEILING_DB = -1.5  # dBTP, leaves room for codec overshoot
PLAY_LOOP = len(score.PLAY_CHORDS) * 4 * 60 / score.PLAY_BPM
MENU_LOOP = len(score.MENU_CHORDS) * 4 * 60 / score.MENU_BPM
STEMS = ["play_base", "play_mel1", "play_mel2", "play_mel3", "play_mel4"]

# Mix trims in dB applied to the rendered per-instrument stems (balance by analysis).
TRIM = {
    "base_keys": -4.0, "base_bass": 6.0, "base_drums": 8.0, "base_strings": 3.0,
    "base_harpsichord": 7.0, "mel1_xylo": 3.0, "mel2_xylo": 3.0, "mel3_xylo": 3.0,
    "mel4_harmony": -4.0, "mel4_glock": 2.0,
    "menu_keys": -2.0, "menu_bass": 9.0, "menu_strings": 2.0, "menu_hum": -5.0,
    "complete_bass": 8.0, "complete_xylo": 3.0, "gameover_keys": -3.0,
}


def spec_files(build: str):
    midi = f"{build}/midi"
    specs = {
        "play": {"loop": PLAY_LOOP, "tail": 4.0, "tracks": O.play_tracks(midi)},
        "menu": {"loop": MENU_LOOP, "tail": 5.0, "tracks": O.menu_tracks(midi)},
        "jingle_complete": {"tail": 3.5, "tracks": O.jingle_complete_tracks(midi)},
        "jingle_gameover": {"tail": 3.0, "tracks": O.jingle_gameover_tracks(midi)},
        "bank": {"length": sfx_bank.length_seconds(), "tail": 0.5, "tracks": sfx_bank.tracks(midi)},
    }
    paths = []
    for name, spec in specs.items():
        spec.update(out=f"{build}/ref/{name}.wav", lufs=MUSIC_LUFS, ceiling_dbtp=PEAK_CEILING_DB,
                    stems_dir=f"{build}/stems/{name}")
        path = f"{build}/specs/{name}.json"
        with open(path, "w") as fh:
            json.dump(spec, fh, indent=1)
        paths.append(path)
    return paths


def render_all(build: str) -> None:
    for sub in ("midi", "specs", "ref", "stems"):
        os.makedirs(f"{build}/{sub}", exist_ok=True)
    score.LOOP_REPEATS = 1
    score.main(f"{build}/midi")
    sfx_bank.write_midi(f"{build}/midi")
    paths = spec_files(build)
    cmd = LOCK + AUDIOKIT_PY + [f"{HERE}/render_specs.py"] + paths
    subprocess.run(cmd, check=True)


# ------------------------------------------------------------------ mastering

def load_stems(build: str, song: str, names) -> dict:
    out = {}
    for name in names:
        x, rate = sf.read(f"{build}/stems/{song}/{name}.wav", always_2d=True)
        assert rate == SR, f"{song}/{name}: {rate} Hz"
        out[name] = x.T.astype(np.float64) * 10 ** (TRIM.get(name, 0.0) / 20)
    # renderers can differ by a sample in length; pad everything to the longest
    n = max(x.shape[1] for x in out.values())
    return {k: np.pad(x, ((0, 0), (0, n - x.shape[1]))) for k, x in out.items()}


def track_names(tracks):
    return [t["name"] for t in tracks]


def fit(x: np.ndarray, target_lufs: float) -> float:
    """Gain that puts x on target_lufs without passing the true-peak ceiling."""
    gain_db = target_lufs - M.lufs(x)
    peak = M.true_peak_db(x * 10 ** (gain_db / 20))
    if peak > PEAK_CEILING_DB:
        gain_db += PEAK_CEILING_DB - peak
    return 10 ** (gain_db / 20)


def write(path: str, x: np.ndarray) -> None:
    sf.write(path, x.T.astype(np.float32), SR, subtype="PCM_16")


# libsndfile Vorbis compression level (0 = best, 1 = smallest): 0.7 is about 110 kbps stereo.
OGG_LEVEL = 0.7


def ogg(wav: str, out: str, level: float = OGG_LEVEL) -> None:
    """Ogg Vorbis from the 16-bit master; decoded length equals the master to the sample."""
    x, sr = sf.read(wav, always_2d=True)
    with sf.SoundFile(out, "w", sr, x.shape[1], format="OGG", subtype="VORBIS",
                      compression_level=level) as fh:
        for i in range(0, len(x), 65536):  # chunked: one huge write segfaults libsndfile 1.2.2
            fh.write(x[i:i + 65536])
    if sf.info(out).frames != len(x):
        raise RuntimeError(f"{out}: Vorbis length {sf.info(out).frames} != {len(x)}")


def master_play(build: str, music_dir: str, report: dict) -> None:
    tracks = load_stems(build, "play", track_names(O.play_tracks(f"{build}/midi")))
    groups = {}
    for name, x in tracks.items():
        stem = "play_base" if name.startswith("base_") else "play_" + name.split("_")[0]
        groups[stem] = groups.get(stem, 0) + M.fold_loop(x, PLAY_LOOP)
    groups = {k: g - g.mean(axis=1, keepdims=True) for k, g in groups.items()}  # no DC
    full = sum(groups.values())
    gain = fit(full, MUSIC_LUFS)
    for stem in STEMS:
        y = groups[stem] * gain
        wav = f"{build}/{stem}.wav"
        write(wav, y)
        ogg(wav, f"{music_dir}/{stem}.ogg")
        report[stem] = summary(y, loop=True)
    write(f"{build}/play_full.wav", full * gain)
    report["play_full(mix)"] = summary(full * gain, loop=True)
    partial = (groups["play_base"] + groups["play_mel1"]) * gain
    report["play_base+mel1"] = summary(partial, loop=True)


def master_menu(build: str, music_dir: str, report: dict) -> None:
    tracks = load_stems(build, "menu", track_names(O.menu_tracks(f"{build}/midi")))
    mix = M.fold_loop(sum(tracks.values()), MENU_LOOP)
    mix = mix - mix.mean(axis=1, keepdims=True)
    y = mix * fit(mix, MUSIC_LUFS)
    write(f"{build}/menu.wav", y)
    ogg(f"{build}/menu.wav", f"{music_dir}/menu.ogg")
    report["menu"] = summary(y, loop=True)


def trim_tail(x: np.ndarray, floor_db: float = -38.0, fade_ms: float = 500.0) -> np.ndarray:
    level = np.abs(x).max(axis=0)
    above = np.nonzero(level > 10 ** (floor_db / 20) * level.max())[0]
    end = min(x.shape[1], (above[-1] if len(above) else x.shape[1]) + int(0.05 * SR))
    y = x[:, :end].copy()
    n = min(end, int(fade_ms / 1000 * SR))
    y[:, -n:] *= np.linspace(1, 0, n)
    return y


def run_down(x: np.ndarray, start_frac: float = 0.35, end_rate: float = 0.55) -> np.ndarray:
    """Music-box spring running out: playback rate glides from 1 to end_rate."""
    n = x.shape[1]
    s = int(n * start_frac)
    rate = np.ones(n * 2)
    rate[s:] = 1 + (end_rate - 1) * np.linspace(0, 1, n * 2 - s) ** 1.3
    pos = np.concatenate([[0], np.cumsum(rate)])
    pos = pos[pos < n - 1]
    idx = np.arange(n)
    return np.stack([np.interp(pos, idx, x[c]) for c in range(x.shape[0])])


def master_jingles(build: str, sfx_dir: str, report: dict) -> None:
    makers = {"jingle_complete": O.jingle_complete_tracks, "jingle_gameover": O.jingle_gameover_tracks}
    for name, maker in makers.items():
        tracks = load_stems(build, name, track_names(maker(f"{build}/midi")))
        y = trim_tail(sum(tracks.values()))
        if name == "jingle_gameover":
            y = trim_tail(run_down(y))
        y = y * fit(y, JINGLE_LUFS)
        write(f"{build}/{name}.wav", y)
        ogg(f"{build}/{name}.wav", f"{sfx_dir}/{name}.ogg")
        report[name] = summary(y, loop=False)


def summary(y: np.ndarray, loop: bool) -> dict:
    out = {"seconds": round(y.shape[1] / SR, 3), "lufs": round(M.lufs(y), 1),
           "true_peak_dbtp": round(M.true_peak_db(y), 1),
           "dc": round(float(np.abs(y.mean(axis=1)).max()), 5)}
    if loop:
        out["seam"] = M.seam_report(y)
    return out


def main(build: str, master_only: bool) -> None:
    root = os.path.dirname(os.path.dirname(HERE))
    music_dir, sfx_dir = f"{root}/audio/music", f"{root}/audio/sfx"
    if not master_only:
        render_all(build)
    report = {}
    master_play(build, music_dir, report)
    master_menu(build, music_dir, report)
    master_jingles(build, sfx_dir, report)
    with open(f"{build}/music_report.json", "w") as fh:
        json.dump(report, fh, indent=1, default=float)
    for name, info in report.items():
        print(f"{name:18s} {json.dumps(info, default=float)}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "/tmp/fts_rescore/build", "--master-only" in sys.argv)
