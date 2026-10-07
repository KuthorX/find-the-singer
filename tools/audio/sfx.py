"""Sound effects for Find The Singer.

Palette: one gel pen on manuscript paper (taps, scribbles, tears; numpy
synthesis) layered with the song's own instruments rendered offline from
Serum 2 / Vital / MS Basic (music box, glass, harp, pizzicato, xylophone; see
sfx_bank.py), always in D major so every effect sits inside the music.
Deterministic for a given tone bank. Run render.py first (it renders the bank),
then with the audiokit venv: python sfx.py [out_dir] [bank_stems_dir]
"""

import os

import numpy as np
from scipy import signal

from dsp import SR, db, lufs, true_peak_db, write_wav
from sfx_bank import ToneBank

RNG = np.random.default_rng(1647)
PEAK_CEILING_DB = -1.5


def hz(name: str) -> float:
    pcs = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    semi = pcs[name[0]]
    rest = name[1:]
    while rest and rest[0] in "#b":
        semi += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    midi = 12 * (int(rest) + 1) + semi
    return 440.0 * 2 ** ((midi - 69) / 12)


def t_axis(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def decay(dur: float, tau: float, attack: float = 0.002) -> np.ndarray:
    t = t_axis(dur)
    env = np.exp(-t / tau)
    a = max(1, int(attack * SR))
    env[:a] *= np.linspace(0, 1, a)
    return env


def taper(x: np.ndarray, ms: float = 12.0) -> np.ndarray:
    """Raised-cosine fade at the end so no layer stops on a click."""
    n = min(len(x), int(ms / 1000 * SR))
    out = x.copy()
    out[len(x) - n:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, n))
    return out


def place(total: np.ndarray, x: np.ndarray, at: float, gain: float = 1.0) -> np.ndarray:
    out = total.copy()
    x = taper(x)
    i = int(at * SR)
    end = min(len(out), i + len(x))
    out[i:end] += x[:end - i] * gain
    return out


def silence(dur: float) -> np.ndarray:
    return np.zeros(int(dur * SR))


def band(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lowpass(x: np.ndarray, f: float) -> np.ndarray:
    return signal.sosfilt(signal.butter(2, f, fs=SR, output="sos"), x)


def noise(dur: float) -> np.ndarray:
    return RNG.standard_normal(int(dur * SR))


# --- instruments ----------------------------------------------------------

TONES = None  # sfx_bank.ToneBank, loaded in main()


def shaped(x: np.ndarray, dur: float, tau: float) -> np.ndarray:
    """Fit a rendered tone to dur seconds with an exponential decay of time constant tau."""
    x = np.pad(x, (0, max(0, int(dur * SR) - len(x))))[:int(dur * SR)]
    return x * decay(dur, tau, 0.001)


def bell(note: str, dur: float = 0.6, tau: float = 0.22, bright: float = 1.0) -> np.ndarray:
    """Music-box tine (Serum 2 Kinderjoy, rendered at pitch). bright scales the decay."""
    return shaped(TONES.tone("musicbox", note, dur), dur, tau * (1.2 + 0.3 * bright))


def glass(note: str, dur: float = 0.25, tau: float = 0.05) -> np.ndarray:
    """Tiny glassy tick (Vital Ceramic)."""
    return shaped(TONES.tone("glass", note, dur), dur, tau * 1.5)


def pluck(note: str, dur: float = 0.4, damp: float = 0.996, bright: float = 0.5) -> np.ndarray:
    """Harp (MS Basic GM 46); the low D3 landing uses pizzicato strings (GM 45)."""
    bank = "pizz" if note == "D3" else "harp"
    x = TONES.tone(bank, note, dur)
    x = lowpass(x, 1500 + 9000 * bright)
    return shaped(x / max(np.abs(x).max(), 1e-9), dur, dur / 3 * (1 + 50 * (damp - 0.99)))


def marimba(note: str, dur: float = 0.35) -> np.ndarray:
    """Wooden mallet (Serum 2 Xylo Pluck)."""
    return shaped(TONES.tone("xylo", note, dur), dur, 0.15)


def pen_tap(dur: float = 0.09, body_hz: float = 150.0) -> np.ndarray:
    """Gel-pen tip on paper over a desk: a tick plus a soft body thump."""
    t = t_axis(dur)
    tick = band(noise(dur), 2500, 7000) * np.exp(-t / 0.004)
    thump = np.sin(2 * np.pi * body_hz * t * (1 - 0.3 * t / dur)) * np.exp(-t / 0.025)
    return 0.6 * tick + thump


def paper(dur: float, lo: float = 1500, hi: float = 6000, grain: float = 0.6) -> np.ndarray:
    """Paper rustle/crinkle: band-limited noise with random crackle grains."""
    n = int(dur * SR)
    base = band(noise(dur), lo, hi)
    clicks = (RNG.random(n) < 0.004).astype(float) * RNG.uniform(0.5, 1.0, n)
    clicks = signal.lfilter([1], [1, -0.93], clicks)
    crack = band(clicks * RNG.choice([-1, 1], n), lo, hi)
    env = np.minimum(1, np.linspace(0, 1, n) * 12) * np.linspace(1, 0.2, n)
    return (base * (1 - grain) + crack * grain * 4) * env


def scribble(dur: float, strokes_hz: float = 13.0) -> np.ndarray:
    """Pencil scribble: paper friction pulsing at the stroke rate."""
    t = t_axis(dur)
    pulse = 0.5 + 0.5 * np.sin(2 * np.pi * strokes_hz * t) ** 2
    pitch = band(noise(dur), 2200, 5200)
    return pitch * pulse * np.minimum(1, t * 40) * np.exp(-t / (dur * 0.6))


def chirp(f0: float, f1: float, dur: float, tau: float) -> np.ndarray:
    t = t_axis(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    phase = 2 * np.pi * np.cumsum(f) / SR
    tri = 2 / np.pi * np.arcsin(np.sin(phase))
    return (0.7 * np.sin(phase) + 0.3 * tri) * decay(dur, tau, 0.004)


# --- the effects ------------------------------------------------------------

def sfx_jump():
    x = chirp(hz("A4"), hz("E5"), 0.16, 0.06)
    return place(x, paper(0.03, 3000, 8000), 0, 0.25)


def sfx_land_measure():
    # plain measure: a whole note landing - pen thump + low D pizzicato
    x = place(silence(0.32), pen_tap(0.1, 140), 0)
    return place(x, pluck("D3", 0.3, 0.995, 0.3), 0.0, 0.45)


def sfx_land_fragile():
    # dashed measure: a brittle glassy tick with a tritone shadow and paper crinkle
    x = place(silence(0.3), pen_tap(0.06, 260), 0, 0.6)
    x = place(x, glass("D7", 0.25, 0.05), 0, 0.35)
    x = place(x, glass("G#6", 0.25, 0.04), 0.012, 0.2)
    return place(x, paper(0.18, 2000, 7000, 0.8), 0.01, 0.35)


def sfx_land_repeat():
    # repeat signs: "again!" - two marimba notes, A then D
    x = place(silence(0.4), pen_tap(0.07, 180), 0, 0.5)
    x = place(x, marimba("A4", 0.3), 0, 0.7)
    return place(x, marimba("D5", 0.3), 0.075, 0.7)


def sfx_bounce():
    # sagging spring measure with marcato accents: accent thump + rising boing
    t = t_axis(0.38)
    f = hz("D4") * 2 ** (1.0 * (1 - np.exp(-t / 0.08)))
    f *= 1 + 0.03 * np.sin(2 * np.pi * 18 * t) * np.exp(-t / 0.15)
    phase = 2 * np.pi * np.cumsum(f) / SR
    boing = (np.sin(phase) + 0.3 * np.sin(2 * phase)) * decay(0.38, 0.12, 0.003)
    x = place(silence(0.4), pen_tap(0.08, 110), 0, 0.8)
    return place(x, boing, 0.005, 0.8)


def sfx_land_gliss():
    # glissando measure: a quick harp run up the D pentatonic
    x = place(silence(0.5), pen_tap(0.06, 170), 0, 0.4)
    for i, n in enumerate(("D5", "E5", "F#5", "A5", "B5", "D6")):
        x = place(x, pluck(n, 0.3, 0.997, 0.7), 0.022 * i, 0.32)
    return x


def sfx_fragile_crack():
    # warning: the dashed lines start to split - crackle + a small bending creak
    t = t_axis(0.4)
    creak_f = 210 * (1 - 0.06 * t / 0.4)
    creak = lowpass(signal.sawtooth(2 * np.pi * np.cumsum(creak_f) / SR), 1200) * decay(0.4, 0.15, 0.02)
    x = place(silence(0.45), paper(0.4, 1800, 6500, 0.9), 0, 0.8)
    return place(x, creak, 0.02, 0.25)


def sfx_fragile_break():
    # paper tears through, the measure is gone: the tear's pitch rises low -> high
    dur = 0.45
    t = t_axis(dur)
    rip = noise(dur)
    grain = 0.5 + 0.5 * np.abs(band(noise(dur), 20, 90)) * 6
    sweep = t / dur
    tear = band(rip, 900, 2400) * (1 - sweep) + band(rip, 2600, 7000) * sweep
    tear = tear * np.minimum(grain, 1.5) * np.minimum(1, t * 30) * np.exp(-t / 0.2)
    x = place(silence(0.5), tear, 0, 1.0)
    return place(x, pen_tap(0.12, 95), 0, 0.5)


def sfx_fragile_restore():
    # redrawn: a pencil scribble that settles on a soft celesta D
    x = place(silence(0.6), scribble(0.3), 0, 0.6)
    return place(x, bell("D6", 0.35, 0.12, 0.6), 0.22, 0.35)


def sfx_letter():
    # an envelope from a fan: paper flick + music-box D6 (pitched per letter in-game)
    x = place(silence(0.7), paper(0.06, 2500, 8000, 0.4), 0, 0.35)
    x = place(x, bell("D6", 0.65, 0.2, 1.4), 0.02, 0.9)
    return place(x, glass("D7", 0.3, 0.06), 0.02, 0.15)


def sfx_checkpoint():
    # the blue pennant: the song is remembered here - D6 + A6 + D7 bells
    x = silence(1.1)
    for i, (n, g) in enumerate((("D6", 0.7), ("A6", 0.55), ("D7", 0.4))):
        x = place(x, bell(n, 1.0, 0.35, 1.2), 0.07 * i, g)
    return place(x, pluck("D4", 0.6, 0.997, 0.4), 0, 0.3)


def sfx_hurt():
    # fell off the staff: a sour minor second sagging down, dry crumple
    x = place(silence(0.5), pluck("Eb5", 0.3, 0.993, 0.5), 0, 0.6)
    x = place(x, pluck("D5", 0.4, 0.99, 0.4), 0.11, 0.55)
    x = place(x, chirp(hz("A4"), hz("D4"), 0.3, 0.1), 0.0, 0.35)
    return place(x, paper(0.2, 900, 4000, 0.7), 0, 0.3)


def sfx_respawn():
    # redrawn at the checkpoint: quick scribble then a music-box arpeggio
    x = place(silence(0.7), scribble(0.14, 20), 0, 0.45)
    for i, n in enumerate(("D5", "F#5", "A5", "D6")):
        x = place(x, bell(n, 0.4, 0.12, 1.0), 0.1 + 0.045 * i, 0.55)
    return x


def sfx_life_up():
    # ten letters read: a new heart - sparkle arpeggio to the top D
    x = silence(1.0)
    for i, n in enumerate(("D6", "F#6", "A6", "D7", "F#7")):
        x = place(x, bell(n, 0.6, 0.18, 1.2), 0.06 * i, 0.5)
    return x


def sfx_ui_hover():
    x = place(silence(0.08), band(noise(0.02), 3000, 8000) * decay(0.02, 0.004), 0, 0.5)
    return place(x, glass("A6", 0.06, 0.015), 0.002, 0.3)


def sfx_ui_click():
    x = place(silence(0.2), pen_tap(0.05, 220), 0, 0.6)
    return place(x, pluck("A5", 0.18, 0.99, 0.6), 0, 0.5)


def sfx_ui_confirm():
    x = place(silence(0.45), pen_tap(0.05, 220), 0, 0.5)
    x = place(x, bell("D6", 0.3, 0.1, 1.0), 0, 0.6)
    return place(x, bell("A6", 0.35, 0.12, 1.0), 0.08, 0.6)


def sfx_ui_back():
    x = place(silence(0.4), pen_tap(0.05, 180), 0, 0.5)
    x = place(x, bell("A5", 0.25, 0.08, 0.8), 0, 0.55)
    return place(x, bell("D5", 0.3, 0.1, 0.8), 0.08, 0.55)


def sfx_ui_toggle():
    x = place(silence(0.15), pen_tap(0.04, 300), 0, 0.5)
    return place(x, bell("E6", 0.12, 0.03, 0.6), 0, 0.4)


# name -> (generator, loudness target in LUFS); feedback hierarchy:
# rewards > movement > UI, hover the quietest
SFX = {
    "jump": (sfx_jump, -21),
    "land_measure": (sfx_land_measure, -21),
    "land_fragile": (sfx_land_fragile, -20),
    "land_repeat": (sfx_land_repeat, -20),
    "land_gliss": (sfx_land_gliss, -20),
    "bounce": (sfx_bounce, -18),
    "fragile_crack": (sfx_fragile_crack, -19),
    "fragile_break": (sfx_fragile_break, -18),
    "fragile_restore": (sfx_fragile_restore, -24),
    "letter": (sfx_letter, -17),
    "checkpoint": (sfx_checkpoint, -16),
    "hurt": (sfx_hurt, -17),
    "respawn": (sfx_respawn, -18),
    "life_up": (sfx_life_up, -16),
    "ui_hover": (sfx_ui_hover, -29),
    "ui_click": (sfx_ui_click, -22),
    "ui_confirm": (sfx_ui_confirm, -20),
    "ui_back": (sfx_ui_back, -21),
    "ui_toggle": (sfx_ui_toggle, -23),
}


def finish(x: np.ndarray, target: float) -> np.ndarray:
    x = x - np.mean(x)
    fade = int(0.01 * SR)
    x[-fade:] *= np.linspace(1, 0, fade)
    rise = int(0.0015 * SR)  # no click on the very first sample
    x[:rise] *= np.linspace(0, 1, rise)
    x = x * db(target - lufs(x))
    peak = true_peak_db(x)
    if peak > PEAK_CEILING_DB:
        x = x * db(PEAK_CEILING_DB - peak)
    return x


# Cues longer than this ship as Ogg Vorbis (libsndfile level 0.6); shorter ones stay WAV,
# where Vorbis headers would cost more than Godot's QOA import saves.
OGG_MIN_SECONDS = 0.5
OGG_LEVEL = 0.6


def write_cue(out_dir: str, name: str, x: np.ndarray) -> None:
    ext = "ogg" if len(x) / SR > OGG_MIN_SECONDS else "wav"
    stale = os.path.join(out_dir, f"{name}.{'wav' if ext == 'ogg' else 'ogg'}")
    if os.path.exists(stale):
        os.remove(stale)
    path = os.path.join(out_dir, f"{name}.{ext}")
    if ext == "wav":
        write_wav(path, x)
        return
    import soundfile as sf

    pcm = np.clip(np.round(x * 32767.0), -32768, 32767) / 32767.0  # same quantisation as the WAVs
    sf.write(path, pcm, SR, format="OGG", subtype="VORBIS", compression_level=OGG_LEVEL)


def main(out_dir: str, bank_dir: str) -> None:
    global TONES
    TONES = ToneBank(bank_dir, SR)
    os.makedirs(out_dir, exist_ok=True)
    for name, (gen, target) in SFX.items():
        x = finish(gen(), target)
        write_cue(out_dir, name, x)
        print(f"{name:16s} {len(x)/SR:5.2f}s {lufs(x):6.1f} LUFS {true_peak_db(x):6.1f} dBTP")


if __name__ == "__main__":
    import sys

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = sys.argv[1] if len(sys.argv) > 1 else f"{root}/audio/sfx"
    main(out, sys.argv[2] if len(sys.argv) > 2 else "/tmp/fts_rescore/build/stems/bank")
