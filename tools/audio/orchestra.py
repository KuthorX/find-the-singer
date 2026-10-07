"""Orchestration for the rescore: which preset plays which MIDI channel of score.py.

The notes (and so the singer's melody) come unchanged from score.py; this
module only decides the sounds. Allowed sources: Vital and Serum 2 factory
presets, FluidSynth + MS Basic.sf3 (GM) and pedalboard built-in effects.
"""

import os

SERUM = "/Library/Audio/Presets/Xfer Records/Serum 2 Presets/Presets/Factory"
VITAL = os.path.expanduser("~/Music/Vital")

# --- instruments --------------------------------------------------------------
# Kinderjoy sounds two octaves above the played key, so its parts are transposed -24.
VOICE = {"type": "serum2", "preset": f"{SERUM}/Vox/VOX - Synth Pop Choir.SerumPreset"}
XYLO = {"type": "serum2", "preset": f"{SERUM}/Pluck/PL - Xylo Pluck.SerumPreset"}
FLUTE = {"type": "serum2", "preset": f"{SERUM}/Woodwind/WIND - Flute.SerumPreset"}
KEYS = {"type": "serum2", "preset": f"{SERUM}/Keyboard/KY - Delicacy.SerumPreset"}
HARPSICHORD = {"type": "serum2", "preset": f"{SERUM}/Keyboard/KY - Harpsichord.SerumPreset"}
MUSICBOX = {"type": "serum2", "preset": f"{SERUM}/Bell/BL - Kinderjoy.SerumPreset"}
STRINGS = {"type": "vital", "preset": f"{VITAL}/In The Mix/Presets/Strings Section.vital"}
CERAMIC = {"type": "vital", "preset": f"{VITAL}/Databroth/Presets/Factory Presets/Ceramic.vital"}
GM_FINGER_BASS = {"type": "fluidsynth", "program": 33, "gain": 0.6}
GM_ACOUSTIC_BASS = {"type": "fluidsynth", "program": 32, "gain": 0.6}
GM_KIT = {"type": "fluidsynth", "program": 0, "gain": 0.6}
GM_HARP = {"type": "fluidsynth", "program": 46, "gain": 0.6}
GM_PIZZ = {"type": "fluidsynth", "program": 45, "gain": 0.6}
KINDERJOY_SHIFT = -24

ROOM = {"type": "Reverb", "room_size": 0.45, "damping": 0.5, "wet_level": 0.16, "dry_level": 0.9, "width": 0.8}
HALL = {"type": "Reverb", "room_size": 0.7, "damping": 0.45, "wet_level": 0.24, "dry_level": 0.85}
TAME_HIGHS = {"type": "LowpassFilter", "cutoff_frequency_hz": 9000}
NO_RUMBLE = {"type": "HighpassFilter", "cutoff_frequency_hz": 140}
VOICE_DELAY = {"type": "Delay", "delay_seconds": 0.375, "feedback": 0.18, "mix": 0.12}


def track(name, midi, channel, instrument, gain_db=0.0, pan=0.0, fx=(), transpose=0):
    return {"name": name, "midi": midi, "track": None, "channel": channel, "transpose": transpose,
            "instrument": instrument, "gain_db": gain_db, "pan": pan, "fx": list(fx)}


def singer(prefix, midi, gain_db=0.0):
    """The singer: a vocal synth lead, doubled by a soft xylophone so each note has an attack."""
    return [
        track(f"{prefix}_voice", midi, 5, VOICE, gain_db, 0.0, [NO_RUMBLE, VOICE_DELAY, HALL]),
        track(f"{prefix}_xylo", midi, 6, XYLO, gain_db - 9, 0.1, [ROOM]),
    ]


def play_tracks(midi_dir):
    base = f"{midi_dir}/play_base.mid"
    tracks = [
        track("base_keys", base, 0, KEYS, -3, -0.15, [ROOM]),
        track("base_bass", base, 1, GM_FINGER_BASS, -1, 0.0),
        track("base_harpsichord", base, 2, HARPSICHORD, -12, 0.3, [TAME_HIGHS, ROOM]),
        track("base_strings", base, 3, STRINGS, -8, -0.1, [HALL]),
        track("base_musicbox", base, 4, MUSICBOX, -14, 0.25, [TAME_HIGHS, ROOM], KINDERJOY_SHIFT),
        track("base_drums", base, 9, GM_KIT, -4, 0.0, [ROOM]),
    ]
    for tier in (1, 2, 3):
        tracks += singer(f"mel{tier}", f"{midi_dir}/play_mel{tier}.mid")
    mel4 = f"{midi_dir}/play_mel4.mid"
    tracks += [
        track("mel4_harmony", mel4, 7, FLUTE, -6, -0.25, [HALL]),
        track("mel4_glock", mel4, 8, MUSICBOX, -15, 0.3, [TAME_HIGHS, ROOM], KINDERJOY_SHIFT),
    ]
    return tracks


def menu_tracks(midi_dir):
    menu = f"{midi_dir}/menu.mid"
    return [
        track("menu_keys", menu, 0, KEYS, -2, -0.1, [HALL]),
        track("menu_bass", menu, 1, GM_ACOUSTIC_BASS, -4, 0.0),
        track("menu_strings", menu, 3, STRINGS, -7, 0.1, [HALL]),
        track("menu_musicbox", menu, 4, MUSICBOX, -9, 0.15, [TAME_HIGHS, HALL], KINDERJOY_SHIFT),
        track("menu_hum", menu, 5, VOICE, -3, 0.0, [NO_RUMBLE, HALL]),
    ]


def jingle_complete_tracks(midi_dir):
    mid = f"{midi_dir}/jingle_complete.mid"
    return singer("complete", mid, 0.0) + [
        track("complete_keys", mid, 0, KEYS, -3, -0.15, [ROOM]),
        track("complete_bass", mid, 1, GM_FINGER_BASS, -2, 0.0),
        track("complete_strings", mid, 3, STRINGS, -7, 0.1, [HALL]),
        track("complete_glock", mid, 8, MUSICBOX, -13, 0.3, [TAME_HIGHS, HALL], KINDERJOY_SHIFT),
    ]


def jingle_gameover_tracks(midi_dir):
    mid = f"{midi_dir}/jingle_gameover.mid"
    return [
        track("gameover_keys", mid, 0, KEYS, -4, -0.1, [ROOM]),
        track("gameover_musicbox", mid, 4, MUSICBOX, -6, 0.1, [TAME_HIGHS, HALL], KINDERJOY_SHIFT),
    ]
