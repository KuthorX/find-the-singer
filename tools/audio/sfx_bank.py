"""Tone bank for the SFX: every pitched layer the effects need, rendered once.

Each instrument plays its notes one per 2-second slot; sfx.py cuts the slots
out of the rendered stems and layers them with the numpy pen-and-paper foley,
so no effect ships a single unprocessed preset hit.
"""

import os

import numpy as np

import orchestra as O

SLOT_SECONDS = 2.0
BPM = 120  # 1 beat = 0.5 s, so a slot is 4 beats
SLOT_BEATS = SLOT_SECONDS * BPM / 60

# name -> (instrument, transpose, note names). Ceramic sounds about three octaves
# and three semitones up (its partials are inharmonic), hence -39.
BANK = {
    "musicbox": (O.MUSICBOX, O.KINDERJOY_SHIFT,
                 ["D5", "F#5", "A5", "D6", "E6", "F#6", "A6", "D7", "F#7"]),
    "glass": (O.CERAMIC, -39, ["G#6", "A6", "D7"]),
    "harp": (O.GM_HARP, 0, ["D4", "D5", "E5", "F#5", "A5", "B5", "D6", "Eb5"]),
    "pizz": (O.GM_PIZZ, 0, ["D3"]),
    "xylo": (O.XYLO, 0, ["A4", "D5"]),
}


def note_num(name: str) -> int:
    pcs = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    semi, rest = pcs[name[0]], name[1:]
    while rest and rest[0] in "#b":
        semi += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + semi


def write_midi(midi_dir: str) -> None:
    import midi_io  # audiokit

    for name, (_inst, _shift, notes) in BANK.items():
        events = [(i * SLOT_BEATS, 0.5, note_num(n), 100, 0) for i, n in enumerate(notes)]
        midi_io.write_midi(f"{midi_dir}/bank_{name}.mid", [events], bpm=BPM)


def tracks(midi_dir: str):
    return [O.track(f"bank_{name}", f"{midi_dir}/bank_{name}.mid", None, inst, 0.0, 0.0, (), shift)
            for name, (inst, shift, _notes) in BANK.items()]


def length_seconds() -> float:
    return max(len(notes) for _i, _s, notes in BANK.values()) * SLOT_SECONDS


class ToneBank:
    """Reads the rendered bank stems; tone(name, note) -> mono float array peaking at 1."""

    def __init__(self, stems_dir: str, sr: int):
        import soundfile as sf

        self.sr = sr
        self.stems = {}
        for name in BANK:
            x, rate = sf.read(os.path.join(stems_dir, f"bank_{name}.wav"), always_2d=True)
            if rate != sr:
                raise ValueError(f"bank_{name}: expected {sr} Hz, got {rate}")
            self.stems[name] = x.mean(axis=1)

    def tone(self, name: str, note: str, dur: float) -> np.ndarray:
        notes = BANK[name][2]
        if note not in notes:
            raise KeyError(f"{note} is not in the {name} bank; add it to sfx_bank.BANK")
        start = int(notes.index(note) * SLOT_SECONDS * self.sr)
        x = self.stems[name][start:start + int(min(dur, SLOT_SECONDS) * self.sr)].copy()
        onset = int(np.argmax(np.abs(x) > np.abs(x).max() * 0.02))
        x = x[max(0, onset - int(0.001 * self.sr)):]
        x -= np.mean(x)
        return x / max(np.abs(x).max(), 1e-9)
