"""The score of Find The Singer, written as code and exported to MIDI.

Concept: "the unfinished song". The singer is missing, so her melody is
missing too. The gameplay track is split into stems:

  play_base  - piano, bass, brushes-like kit, pizzicato, pad, music box
  play_mel1  - melody skeleton (first note of every bar + long notes)
  play_mel2  - remaining on-beat melody notes
  play_mel3  - off-beat melody notes (the syncopation that makes it a song)
  play_mel4  - harmony a third below + glockenspiel sparkle in the chorus

Letters collected in the level fade the melody stems in one by one, so the
song literally fills in as the fans' letters are found.

Every loop is written 3 times in a row; render.py keeps the middle copy so
reverb tails wrap around the loop seam.
"""

import os

from midi import PPQ, Track, write

EIGHTH = PPQ // 2
BAR = 8 * EIGHTH  # 4/4 everywhere
LOOP_REPEATS = 3

PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# chord symbol -> pitch classes, root first
CHORDS = {
    "D": [2, 6, 9], "D7": [2, 6, 9, 0], "Em": [4, 7, 11], "F#m": [6, 9, 1],
    "G": [7, 11, 2], "A": [9, 1, 4], "Asus4": [9, 2, 4], "Bm": [11, 2, 6],
    "A/C#": [9, 1, 4], "F#m/A": [6, 9, 1], "D/F#": [2, 6, 9],
}
SLASH_BASS = {"A/C#": 1, "F#m/A": 9, "D/F#": 6}

# General MIDI programs (0-based)
GM = {
    "piano": 0, "celesta": 8, "glock": 9, "musicbox": 10, "nylon": 24,
    "bass": 32, "strings": 48, "pizz": 45, "oohs": 53, "synthvoice": 54,
    "flute": 73,
}


def note_num(name: str) -> int:
    letter, rest = name[0], name[1:]
    semi = PC[letter]
    while rest and rest[0] in "#b":
        semi += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + semi


def parse_bar(text: str):
    """'A4:1 D5:2 r:1' -> [(start_eighth, len_eighths, pitch|None)]"""
    out, pos = [], 0
    for tok in text.split():
        name, length = tok.split(":")
        length = int(length)
        out.append((pos, length, None if name == "r" else note_num(name)))
        pos += length
    assert pos == 8, f"bar does not add up to 8 eighths: {text} ({pos})"
    return out


def in_range(pc: int, lo: int) -> int:
    """Lowest MIDI note with pitch class pc that is >= lo."""
    return lo + ((pc - lo) % 12)


def voicing(chord: str, lo: int = 59):
    return sorted(in_range(pc, lo) for pc in CHORDS[chord])


def bass_root(chord: str) -> int:
    pc = SLASH_BASS.get(chord, CHORDS[chord][0])
    return in_range(pc, 36)


D_MAJOR = [2, 4, 6, 7, 9, 11, 1]


def third_below(pitch: int) -> int:
    """Diatonic third below in D major."""
    idx = D_MAJOR.index(pitch % 12)
    target = D_MAJOR[(idx - 2) % 7]
    p = pitch - 1
    while p % 12 != target:
        p -= 1
    return p


# --------------------------------------------------------------------------
# Gameplay: "Page of Songs", D major, 120 BPM, 48 bars = 96 s
# --------------------------------------------------------------------------

PLAY_BPM = 120
PLAY_CHORDS = (
    # A: intro + verse (1-16)
    ["D", "Bm", "G", "A", "D", "Bm", "Em", "A"]
    + ["D", "F#m", "G", "A", "Bm", "F#m", ("G", "A"), "D"]
    # B: pre-chorus (17-24)
    + ["G", "A", "F#m", "Bm", "Em", "F#m", "G", "Asus4"]
    # Chorus, royal-road IV-V-iii-vi (25-40)
    + ["G", "A", "F#m", "Bm", "G", "A", "D", "D7"]
    + ["G", "A", "F#m", "Bm", "Em", "A", "D", "D"]
    # Tag (41-48): the song waits for its singer
    + ["Bm", "G", "D", "A", "Bm", "G", "Em", "A"]
)
assert len(PLAY_CHORDS) == 48

REST = "r:8"
PLAY_MELODY = (
    [REST] * 4
    + [
        "r:1 A4:1 D5:2 E5:1 F#5:2 A5:1",
        "F#5:3 E5:1 D5:2 B4:2",
        "G5:2 F#5:1 E5:1 D5:2 E5:2",
        "C#5:2 E5:2 A4:4",
        "r:1 A4:1 D5:2 E5:1 F#5:2 A5:1",
        "C#6:3 B5:1 A5:2 F#5:2",
        "B5:2 A5:1 G5:1 F#5:2 G5:1 A5:1",
        "E5:6 r:2",
        "r:1 D5:1 F#5:2 B5:2 A5:2",
        "A5:2 F#5:1 E5:1 C#5:2 E5:2",
        "D5:2 E5:2 F#5:2 E5:2",
        "D5:6 r:2",
        # B
        "B4:1 D5:1 G5:2 F#5:1 G5:1 A5:2",
        "A5:3 G5:1 F#5:2 E5:2",
        "F#5:1 A5:1 C#6:2 B5:1 A5:1 F#5:2",
        "F#5:3 E5:1 D5:4",
        "G4:1 B4:1 E5:2 F#5:1 G5:1 B5:2",
        "A5:3 G5:1 F#5:2 C#5:2",
        "D5:2 E5:2 G5:2 B5:2",
        "A5:8",
        # Chorus
        "D6:2 C#6:1 B5:1 A5:2 B5:1 D6:1",
        "C#6:3 A5:1 E5:2 A5:2",
        "A5:1 B5:1 C#6:2 B5:1 A5:1 F#5:2",
        "B5:4 A5:2 F#5:2",
        "D6:2 C#6:1 B5:1 A5:2 B5:1 D6:1",
        "E6:3 D6:1 C#6:2 A5:2",
        "D6:2 A5:2 F#5:2 A5:2",
        "D6:6 r:2",
        "D6:2 C#6:1 B5:1 A5:2 B5:1 D6:1",
        "C#6:3 A5:1 E5:2 A5:2",
        "A5:1 B5:1 C#6:2 E6:2 C#6:2",
        "B5:3 A5:1 F#5:2 D5:2",
        "G5:2 F#5:1 G5:1 B5:2 A5:1 G5:1",
        "F#5:2 G5:1 F#5:1 E5:2 C#5:2",
        "D5:8",
    ]
    + [REST] * 9
)
assert len(PLAY_MELODY) == 48
CHORUS_BARS = range(24, 39)  # 0-based bars that get the tier-4 harmony


def melody_tier(start: int, length: int, first_in_bar: bool) -> int:
    if first_in_bar or length >= 4:
        return 1
    if start % 2 == 0:
        return 2
    return 3


def chords_of(bar_chords):
    """bar entry -> [(start_eighth, len_eighths, chord)]"""
    if isinstance(bar_chords, tuple):
        half = 8 // len(bar_chords)
        return [(i * half, half, c) for i, c in enumerate(bar_chords)]
    return [(0, 8, bar_chords)]


def section(bar: int) -> str:
    if bar < 4:
        return "intro"
    if bar < 16:
        return "verse"
    if bar < 24:
        return "pre"
    if bar < 40:
        return "chorus"
    return "tag"


def play_base(tr: Track, offset: int) -> None:
    for bar, entry in enumerate(PLAY_CHORDS):
        sec = section(bar)
        t0 = offset + bar * BAR
        for start, length, chord in chords_of(entry):
            ts = t0 + start * EIGHTH
            # piano comping: pushed pop rhythm on 0, 3, 4, 6 (scaled to the chord length)
            hits = [0, 3, 4, 6] if length == 8 else [0, 2, 3]
            pvel = {"intro": 46, "verse": 52, "pre": 56, "chorus": 62, "tag": 48}[sec]
            for h in hits:
                dur = EIGHTH * (2 if h in (0, 4) else 1)
                for p in voicing(chord):
                    tr.note(ts + h * EIGHTH, dur - 20, 0, p, pvel + (6 if h == 0 else 0))
            # bass: root, push, fifth, octave walk
            root = bass_root(chord)
            if sec != "intro":
                bvel = 92 if sec == "chorus" else 84
                pattern = [(0, 2, root), (3, 1, root), (4, 2, root + 7), (6, 2, root + 12)]
                if length < 8:
                    pattern = [(0, 2, root), (3, 1, root + 7)]
                for s, d, p in pattern:
                    tr.note(ts + s * EIGHTH, d * EIGHTH - 30, 1, p, bvel)
            # pizzicato off-beat stabs in pre-chorus and chorus
            if sec in ("pre", "chorus"):
                for s in (1, 5) if length == 8 else (1,):
                    for p in voicing(chord, 66):
                        tr.note(ts + s * EIGHTH, EIGHTH, 2, p, 58)
            # string pad under the chorus
            if sec == "chorus":
                for p in voicing(chord, 50):
                    tr.note(ts, length * EIGHTH - 10, 3, p, 50)
            # music box: the waiting arpeggio (intro, tag, and quietly in the verse)
            if sec in ("intro", "tag", "verse"):
                pcs = CHORDS[chord]
                arp = [in_range(pcs[0], 74), in_range(pcs[1], 74), in_range(pcs[2], 74)]
                arp = sorted(arp) + [sorted(arp)[0] + 12]
                order = [0, 1, 2, 3, 2, 1, 2, 3]
                mvel = 40 if sec == "verse" else 64
                for i in range(length):
                    tr.note(ts + i * EIGHTH, EIGHTH, 4, arp[order[i % 8]], mvel - (8 if i % 2 else 0))
        # drums (channel 9)
        if sec == "intro":
            for i in range(8):
                tr.note(t0 + i * EIGHTH, 60, 9, 42, 40 if i % 2 else 52)
            if bar == 3:
                for i, v in zip((4, 5, 6, 7), (50, 60, 70, 80)):
                    tr.note(t0 + i * EIGHTH, 60, 9, 37, v)
            continue
        kicks = [0, 4] if sec != "chorus" else [0, 3, 4]
        for k in kicks:
            tr.note(t0 + k * EIGHTH, 60, 9, 36, 84)
        for s in (2, 6):
            tr.note(t0 + s * EIGHTH, 60, 9, 37 if sec != "chorus" else 39, 70)
        for i in range(8):
            tr.note(t0 + i * EIGHTH, 60, 9, 42, 34 if i % 2 else 46)
        if sec in ("pre", "chorus"):
            for i in range(16):
                tr.note(t0 + i * EIGHTH // 2, 40, 9, 70, 26 if i % 2 else 36)
        if bar in (23, 39):
            for i, v in zip(range(4, 8), (60, 70, 80, 90)):
                tr.note(t0 + i * EIGHTH, 60, 9, 38, v)


def play_melody(tr: Track, offset: int, tier: int) -> None:
    for bar, text in enumerate(PLAY_MELODY):
        t0 = offset + bar * BAR
        notes = [n for n in parse_bar(text) if n[2] is not None]
        for i, (start, length, pitch) in enumerate(notes):
            ts = t0 + start * EIGHTH
            dur = length * EIGHTH - 24
            accent = 8 if start % 2 == 0 else 0
            if tier in (1, 2, 3):
                if melody_tier(start, length, i == 0) != tier:
                    continue
                tr.note(ts, dur, 5, pitch, 92 + accent)
                tr.note(ts, min(dur, EIGHTH * 2), 6, pitch, 58 + accent)
            elif tier == 4 and bar in CHORUS_BARS:
                tr.note(ts, dur, 7, third_below(pitch), 70)
                if start == 0:
                    tr.note(ts, EIGHTH * 2, 8, pitch + 12, 54)


def setup(tr: Track, bpm: float, programs) -> None:
    tr.meta_tempo(0, bpm)
    tr.meta_timesig(0, 4, 2)
    for ch, prog in programs:
        tr.program(0, ch, prog)
        tr.control(0, ch, 91, 52)  # reverb send: a small room, not a hall
        tr.control(0, ch, 93, 0)


PLAY_PROGRAMS = [
    (0, GM["piano"]), (1, GM["bass"]), (2, GM["pizz"]), (3, GM["strings"]),
    (4, GM["musicbox"]), (5, GM["synthvoice"]), (6, GM["celesta"]),
    (7, GM["oohs"]), (8, GM["glock"]),
]


def build_play(out_dir: str) -> None:
    bars = len(PLAY_CHORDS)
    stems = {
        "play_base": lambda tr, off: play_base(tr, off),
        "play_mel1": lambda tr, off: play_melody(tr, off, 1),
        "play_mel2": lambda tr, off: play_melody(tr, off, 2),
        "play_mel3": lambda tr, off: play_melody(tr, off, 3),
        "play_mel4": lambda tr, off: play_melody(tr, off, 4),
    }
    for name, fn in stems.items():
        tr = Track(name)
        setup(tr, PLAY_BPM, PLAY_PROGRAMS)
        for rep in range(LOOP_REPEATS):
            fn(tr, rep * bars * BAR)
        write(os.path.join(out_dir, name + ".mid"), [tr])


# --------------------------------------------------------------------------
# Menu: "Guestbook", D major, 90 BPM, 32 bars = 85.3 s
# The same chorus hook as a half-remembered lullaby over a canon progression.
# --------------------------------------------------------------------------

MENU_BPM = 90
MENU_CHORDS = ["D", "A/C#", "Bm", "F#m/A", "G", "D/F#", "G", "A"] * 4
MENU_HOOK = [
    "D6:2 C#6:1 B5:1 A5:4",
    "C#6:4 E5:4",
    "D6:2 C#6:1 B5:1 F#5:4",
    "A5:4 C#5:4",
    "B5:2 A5:1 G5:1 D5:4",
    "F#5:2 E5:1 D5:1 A5:4",
    "B5:3 D6:1 G5:4",
    "A5:4 r:4",
]
# the last pass forgets the ending: the song is unfinished until the singer is found
MENU_HOOK_FORGOTTEN = MENU_HOOK[:6] + ["B5:3 r:5", REST]

MENU_PROGRAMS = [
    (0, GM["piano"]), (3, GM["strings"]), (4, GM["musicbox"]), (5, GM["oohs"]),
    (1, GM["bass"]),
]


def menu_part(tr: Track, offset: int) -> None:
    for bar, chord in enumerate(MENU_CHORDS):
        t0 = offset + bar * BAR
        block = bar // 8
        pcs = CHORDS[chord]
        root = bass_root(chord)
        # piano: low root + rolling broken chord
        tr.note(t0, BAR - 30, 0, root, 58)
        tr.note(t0, BAR - 30, 0, root + 12, 44)
        up = sorted(in_range(pc, 62) for pc in pcs)
        figure = [up[0], up[1], up[2], up[0] + 12, up[2], up[1], up[2], up[0] + 12]
        for i, p in enumerate(figure):
            tr.note(t0 + i * EIGHTH, EIGHTH * 2, 0, p, 50 if i % 2 else 56)
        if block >= 1:
            for p in voicing(chord, 55):
                tr.note(t0, BAR - 20, 3, p, 42 if block != 2 else 50)
        if block == 2:
            tr.note(t0, BAR - 40, 1, root, 60)
        hook = {1: MENU_HOOK, 2: MENU_HOOK, 3: MENU_HOOK_FORGOTTEN}.get(block)
        if hook is None:
            continue
        for start, length, pitch in parse_bar(hook[bar % 8]):
            if pitch is None:
                continue
            ts = t0 + start * EIGHTH
            if block == 2:  # hummed an octave lower, music box keeps time above
                tr.note(ts, length * EIGHTH - 20, 5, pitch - 12, 74)
            else:
                tr.note(ts, length * EIGHTH - 20, 4, pitch, 80)
        if block == 2:
            for i in range(0, 8, 2):
                tr.note(t0 + i * EIGHTH, EIGHTH, 4, up[(i // 2) % 3] + 24, 40)


def build_menu(out_dir: str) -> None:
    tr = Track("menu")
    setup(tr, MENU_BPM, MENU_PROGRAMS)
    for rep in range(LOOP_REPEATS):
        menu_part(tr, rep * len(MENU_CHORDS) * BAR)
    write(os.path.join(out_dir, "menu.mid"), [tr])


# --------------------------------------------------------------------------
# Jingles (one-shots, 120 BPM)
# --------------------------------------------------------------------------

def build_jingles(out_dir: str) -> None:
    # Level complete: the hook finally sung all the way to the tonic.
    tr = Track("jingle_complete")
    setup(tr, PLAY_BPM, [(0, GM["piano"]), (1, GM["bass"]), (3, GM["strings"]),
                         (5, GM["synthvoice"]), (6, GM["celesta"]), (8, GM["glock"])])
    lead = parse_bar("D6:1 C#6:1 B5:1 A5:1 B5:1 C#6:1 E6:2")
    for start, length, pitch in lead:
        ts = start * EIGHTH
        tr.note(ts, length * EIGHTH - 10, 5, pitch, 100)
        tr.note(ts, length * EIGHTH - 10, 6, pitch, 70)
    for start, chord in ((0, "G"), (4, "A")):
        for p in voicing(chord):
            tr.note(start * EIGHTH, 4 * EIGHTH - 20, 0, p, 70)
        tr.note(start * EIGHTH, 4 * EIGHTH - 20, 1, bass_root(chord), 90)
    end = BAR
    tr.note(end, BAR * 1, 5, note_num("D6"), 108)
    tr.note(end, BAR, 6, note_num("D6"), 72)
    for i, p in enumerate([note_num(n) for n in ("D5", "F#5", "A5", "D6", "F#6", "A6")]):
        tr.note(end + i * 50, 3 * EIGHTH, 8, p, 60 + i * 4)
    for p in voicing("D", 50) + voicing("D", 62):
        tr.note(end, BAR, 3, p, 70)
        tr.note(end, BAR, 0, p, 76)
    tr.note(end, BAR, 1, note_num("D2"), 96)
    write(os.path.join(out_dir, "jingle_complete.mid"), [tr])

    # Game over: the music box tries the hook in D minor and runs down.
    tr = Track("jingle_gameover")
    setup(tr, 100, [(0, GM["piano"]), (4, GM["musicbox"])])
    seq = [("A5", 1), ("F5", 1), ("D5", 1), ("E5", 1), ("C#5", 2), ("D5", 4)]
    t = 0
    for name, length in seq:
        tr.note(t, length * EIGHTH - 10, 4, note_num(name), 84)
        t += length * EIGHTH
    for name in ("D3", "A3", "F4"):
        tr.note(4 * EIGHTH, 6 * EIGHTH, 0, note_num(name), 52)
    write(os.path.join(out_dir, "jingle_gameover.mid"), [tr])


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    build_play(out_dir)
    build_menu(out_dir)
    build_jingles(out_dir)


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "build/midi")
