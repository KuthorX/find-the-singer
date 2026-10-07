"""Tiny dependency-free Standard MIDI File (type 1) writer.

Only what the score needs: tempo, time signature, program change, controller
and note on/off events. Times are in ticks (PPQ = 480).
"""

import struct

PPQ = 480


def _varlen(value: int) -> bytes:
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


class Track:
    def __init__(self, name: str = ""):
        self.events = []  # (tick, order, bytes)
        if name:
            data = name.encode("utf-8")
            self.events.append((0, 0, b"\xff\x03" + _varlen(len(data)) + data))

    def meta_tempo(self, tick: int, bpm: float) -> None:
        us = int(round(60_000_000 / bpm))
        self.events.append((tick, 0, b"\xff\x51\x03" + us.to_bytes(3, "big")))

    def meta_timesig(self, tick: int, num: int, den_pow2: int) -> None:
        self.events.append((tick, 0, bytes([0xFF, 0x58, 0x04, num, den_pow2, 24, 8])))

    def program(self, tick: int, ch: int, prog: int) -> None:
        self.events.append((tick, 1, bytes([0xC0 | ch, prog])))

    def control(self, tick: int, ch: int, cc: int, val: int) -> None:
        self.events.append((tick, 1, bytes([0xB0 | ch, cc, val])))

    def note(self, tick: int, dur: int, ch: int, pitch: int, vel: int) -> None:
        vel = max(1, min(127, int(vel)))
        # note-offs sort before note-ons at the same tick so repeated pitches retrigger
        self.events.append((tick, 3, bytes([0x90 | ch, pitch, vel])))
        self.events.append((tick + max(1, dur), 2, bytes([0x80 | ch, pitch, 0])))

    def to_bytes(self) -> bytes:
        body = b""
        last = 0
        for tick, _order, data in sorted(self.events, key=lambda e: (e[0], e[1])):
            body += _varlen(tick - last) + data
            last = tick
        body += b"\x00\xff\x2f\x00"
        return b"MTrk" + struct.pack(">I", len(body)) + body


def write(path: str, tracks) -> None:
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ)
    with open(path, "wb") as fh:
        fh.write(header + b"".join(t.to_bytes() for t in tracks))
