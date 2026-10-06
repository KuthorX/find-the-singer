#!/usr/bin/env python3
"""Paints the "staff-paper guestbook" art set for Find The Singer.

Usage:  python3 tools/art/gen_art.py            (run from the repo root)
Writes PNGs into images/. Everything is drawn procedurally: paper grain, gel-pen
strokes, flat fills. The treble clef / quarter-note shapes come from the Bravura music
font (SIL OFL, tools/art/fonts/OFL-Bravura.txt). Deterministic (fixed seeds).
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "images")
BRAVURA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Bravura.otf")

SS = 4  # supersampling factor
PAPER = (244, 238, 225)
PAPER_HI = (251, 248, 240)
INK = (30, 34, 70)
ACCENT = (102, 204, 255)  # Tianyi blue: means "the song"
ACCENT_DK = (40, 140, 205)
RED = (214, 64, 52)


# ---------------------------------------------------------------- helpers
def canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def save(img, name, w, h, rough=True):
    if rough:
        img = roughen(img, 0.9, seed=len(name))
    img.resize((w, h), Image.Resampling.LANCZOS).save(os.path.join(OUT, name))
    print("wrote", name, w, h)


def smooth_noise(n, rng, k=6):
    """1-D smooth noise in [-1, 1], n samples."""
    ctrl = rng.uniform(-1, 1, k + 2)
    xs = np.linspace(0, k, n)
    i = np.floor(xs).astype(int)
    t = xs - i
    t = t * t * (3 - 2 * t)
    return ctrl[i] * (1 - t) + ctrl[i + 1] * t


def resample(pts, step):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for k in range(d):
            out.append((x0 + (x1 - x0) * k / d, y0 + (y1 - y0) * k / d))
    out.append(pts[-1])
    return out


def pen(d, pts, width, color, seed=0, wobble=1.2, alpha=255, pressure=0.25):
    """Gel-pen stroke: wobbly path, pressure-varying width, round nib. Coords in final px."""
    rng = np.random.default_rng(seed)
    p = resample([(x * SS, y * SS) for x, y in pts], SS * 0.6)
    n = len(p)
    if n < 2:
        return
    jx = smooth_noise(n, rng, max(2, n // 60)) * wobble * SS
    jy = smooth_noise(n, rng, max(2, n // 60)) * wobble * SS
    wv = 1 + smooth_noise(n, rng, max(2, n // 80)) * pressure
    taper = np.minimum(1, np.minimum(np.arange(n), np.arange(n)[::-1]) / max(1, min(12 * SS, n / 4)) + 0.45)
    col = color + (alpha,)
    for k, (x, y) in enumerate(p):
        r = width * SS * 0.5 * wv[k] * taper[k]
        cx, cy = x + jx[k], y + jy[k]
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)


def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=160, start=0.0, end=2 * math.pi):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for k in range(n + 1):
        a = start + (end - start) * k / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def poly_fill(d, pts, color, alpha=255):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=color + (alpha,))


def glyph_layer(size_px, char, height_px, pos, color, outline=None, outline_w=0):
    """Render a Bravura glyph scaled to height_px, top-left at pos (final px)."""
    font = ImageFont.truetype(BRAVURA, 400)
    pad = int(outline_w * 400 / max(1, height_px)) + 4
    tmp = Image.new("RGBA", (900, 1400), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    sw = int(outline_w * 400 / max(1, height_px)) if outline else 0
    if outline:
        td.text((200, 700), char, font=font, fill=outline + (255,), stroke_width=sw, stroke_fill=outline + (255,), anchor="ls")
    td.text((200, 700), char, font=font, fill=color + (255,), anchor="ls")
    g = tmp.crop(tmp.getbbox())
    k = height_px * SS / g.height
    g = g.resize((max(1, int(g.width * k)), max(1, int(g.height * k))), Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", (size_px[0] * SS, size_px[1] * SS), (0, 0, 0, 0))
    layer.alpha_composite(g, (int(pos[0] * SS), int(pos[1] * SS)))
    return layer


# ---------------------------------------------------------------- paper
def periodic_noise(h, w, sigma, rng):
    f = np.fft.fft2(rng.standard_normal((h, w)))
    ky = np.fft.fftfreq(h)[:, None]
    kx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-(kx ** 2 + ky ** 2) * (2 * math.pi * sigma) ** 2 / 2)
    n = np.real(np.fft.ifft2(f * g))
    return n / (np.abs(n).max() + 1e-9)


def paper_tile():
    w, h = 512, 512
    rng = np.random.default_rng(7)
    base = np.array(PAPER, dtype=np.float32)[None, None, :].repeat(h, 0).repeat(w, 1)
    base += periodic_noise(h, w, 40, rng)[..., None] * 5
    base += periodic_noise(h, w, 1.2, rng)[..., None] * 4
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # fibres (drawn with wrap-around)
    fib = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fib)
    r = random.Random(11)
    for _ in range(70):
        x, y = r.uniform(0, w), r.uniform(0, h)
        a, ln = r.uniform(0, math.pi), r.uniform(6, 22)
        col = (150, 130, 100, r.randint(18, 40))
        for dx in (-w, 0, w):
            for dy in (-h, 0, h):
                pts = [(x + dx + math.cos(a) * ln * t + math.sin(t * 3) * 2, y + dy + math.sin(a) * ln * t) for t in np.linspace(0, 1, 8)]
                fd.line(pts, fill=col, width=1)
    img.alpha_composite(fib)
    img.convert("RGB").save(os.path.join(OUT, "paper_plain.png"))
    print("wrote paper_plain.png", w, h)


# ---------------------------------------------------------------- characters & props
def roughen(layer, amount=1.3, sigma=2.5, seed=0):
    """Ink-on-paper edge: displace pixels by smooth noise (supersampled px)."""
    arr = np.asarray(layer)
    h, w = arr.shape[:2]
    rng = np.random.default_rng(seed)
    dx = periodic_noise(h, w, sigma * SS, rng) * amount * SS
    dy = periodic_noise(h, w, sigma * SS, rng) * amount * SS
    yy, xx = np.mgrid[0:h, 0:w]
    sx = np.clip((xx + dx).astype(int), 0, w - 1)
    sy = np.clip((yy + dy).astype(int), 0, h - 1)
    return Image.fromarray(arr[sy, sx], "RGBA")


def note_head(img, cx, cy, scale=1.0, face="idle", seed=1):
    """Solid gel-ink note head. face: idle | hurt | happy | None."""
    rot = -0.36
    rx, ry = 92 * scale, 58 * scale
    body = ellipse_pts(cx, cy, rx, ry, rot)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    poly_fill(ld, body, INK)
    pen(ld, body, 6 * scale, INK, seed=seed, wobble=1.2)
    c, s = math.cos(rot), math.sin(rot)

    def at(x, y):
        x, y = x * scale, y * scale
        return cx + x * c - y * s, cy + x * s + y * c

    w = 3.4 * scale
    for i, (ex, ey) in enumerate(((-4, 0), (36, -3))):
        px, py = at(ex, ey)
        if face == "idle":
            poly_fill(ld, ellipse_pts(px, py, 12 * scale, 16 * scale, rot + 0.15), PAPER)
            qx, qy = at(ex + 5, ey + 4)
            poly_fill(ld, ellipse_pts(qx, qy, 5.5 * scale, 7.5 * scale, rot), INK)
        elif face == "hurt":
            k = 9 * scale
            pen(ld, [(px - k, py - k), (px + k, py + k)], w, PAPER, seed=seed + 10 + i, wobble=0.3)
            pen(ld, [(px - k, py + k), (px + k, py - k)], w, PAPER, seed=seed + 20 + i, wobble=0.3)
        elif face == "happy":
            pen(ld, ellipse_pts(px, py + 4 * scale, 10 * scale, 9 * scale, rot, n=16, start=math.pi + 0.4, end=2 * math.pi - 0.4), w, PAPER, seed=seed + 10 + i, wobble=0.2)
    if face == "idle":
        pen(ld, ellipse_pts(*at(17, 22), 9 * scale, 7 * scale, rot, n=16, start=0.5, end=math.pi - 0.5), w * 1.4, PAPER_HI, seed=seed + 3, wobble=0.2)
    elif face == "hurt":
        pen(ld, [at(6, 30), at(12, 26), at(18, 30), at(24, 26), at(30, 30)], w * 0.9, PAPER, seed=seed + 3, wobble=0.2)
    elif face == "happy":
        mouth = ellipse_pts(*at(17, 20), 13 * scale, 11 * scale, rot, n=20, start=0.1, end=math.pi - 0.1)
        poly_fill(ld, mouth, PAPER)
    img.alpha_composite(roughen(layer, 1.0 * min(scale, 2), seed=seed))


def stem_and_flag(img, cx, cy, scale, seed=5):
    rot = -0.36
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sx = cx + 84 * scale * math.cos(rot) + 4 * scale
    sy = cy + 84 * scale * math.sin(rot) + 6 * scale
    top = (sx + 5 * scale, sy - 200 * scale)
    pen(d, [(sx, sy), (sx + 4 * scale, sy - 110 * scale), top], 9 * scale, INK, seed=seed, wobble=1.0, pressure=0.15)
    # flag: one hand-drawn tapering swoosh, Tianyi blue edged in ink
    tx, ty = top
    spine = [(tx, ty), (tx + 16 * scale, ty + 28 * scale), (tx + 52 * scale, ty + 56 * scale), (tx + 70 * scale, ty + 92 * scale), (tx + 58 * scale, ty + 132 * scale)]
    inner = [(tx, ty + 46 * scale), (tx + 26 * scale, ty + 66 * scale), (tx + 46 * scale, ty + 92 * scale), (tx + 56 * scale, ty + 128 * scale)]
    shape = spine + inner[::-1]
    poly_fill(d, shape, ACCENT)
    pen(d, spine, 5 * scale, INK, seed=seed + 1, wobble=0.8)
    pen(d, inner, 3.5 * scale, INK, seed=seed + 2, wobble=0.8)
    img.alpha_composite(roughen(layer, 0.9 * min(scale, 2), seed=seed))


def tiantian():
    w, h = 280, 330
    img = canvas(w, h)
    note_head(img, 110, 262, 1.0, seed=3)
    stem_and_flag(img, 110, 262, 1.0)
    save(img, "tiantian.png", w, h)


def title_note():
    w, h = 560, 660
    for face, name in (("idle", "title_note.png"), ("hurt", "note_hurt.png"), ("happy", "note_happy.png")):
        img = canvas(w, h)
        note_head(img, 220, 524, 2.0, face=face, seed=13)
        stem_and_flag(img, 220, 524, 2.0, seed=15)
        save(img, name, w, h)


def icon_life():
    w, h = 128, 128
    img = canvas(w, h)
    note_head(img, 64, 66, 0.6, seed=21)
    save(img, "icon_life.png", w, h)


def envelope(img, d, cx, cy, ew, eh, rot, seed):
    c, s = math.cos(rot), math.sin(rot)

    def at(x, y):
        return cx + x * c - y * s, cy + x * s + y * c

    hw, hh = ew / 2, eh / 2
    rect = [at(-hw, -hh), at(hw, -hh), at(hw, hh), at(-hw, hh), at(-hw, -hh)]
    poly_fill(d, rect, PAPER_HI)
    d2 = ImageDraw.Draw(img)
    pen(d2, rect, 4, INK, seed=seed + 1)
    pen(d2, [at(-hw, -hh), at(0, hh * 0.15), at(hw, -hh)], 3.5, INK, seed=seed + 2)
    pen(d2, [at(-hw, hh), at(-hw * 0.2, -hh * 0.05)], 2, INK, seed=seed + 3, alpha=150)
    pen(d2, [at(hw, hh), at(hw * 0.2, -hh * 0.05)], 2, INK, seed=seed + 4, alpha=150)
    # wax seal heart at the flap point
    hx, hy = at(0, hh * 0.12)
    r = eh * 0.17
    heart = []
    for k in range(80):
        t = 2 * math.pi * k / 80
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        heart.append((hx + x * r / 16, hy + y * r / 16))
    poly_fill(d2, heart, INK)
    pen(d2, heart + heart[:1], 2.6, INK, seed=seed + 5, wobble=0.4)


def letter():
    w, h = 211, 142
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    envelope(img, d, 105, 71, 168, 106, -0.08, seed=31)
    save(img, "letter.png", w, h)


def checkpoint():
    # matches the flag-shaped CollisionPolygon2D in Level_1 (pole left, pennant right)
    w, h = 211, 142
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    pennant = [(60, 8), (156, 34), (62, 64)]
    poly_fill(d, pennant, ACCENT)
    d = ImageDraw.Draw(img)
    pen(d, pennant + pennant[:1], 3.5, INK, seed=42)
    nh = glyph_layer((w, h), "\uE1D5", 30, (84, 18), PAPER_HI)  # quarter-note cut-out
    img.alpha_composite(nh)
    pen(d, [(57, 4), (56, 70), (55, 136)], 8, INK, seed=43, pressure=0.1)
    poly_fill(d, ellipse_pts(57, 5, 7, 7), INK)
    save(img, "checkpoint.png", w, h)


def metronome():
    w, h = 128, 128
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    body = [(40, 116), (88, 116), (76, 14), (52, 14), (40, 116)]
    poly_fill(d, body, PAPER_HI)
    d = ImageDraw.Draw(img)
    pen(d, body, 4, INK, seed=52)
    pen(d, [(64, 102), (88, 26)], 4, INK, seed=53, pressure=0.05)
    poly_fill(d, [(80, 42), (90, 46), (86, 56), (76, 52)], ACCENT)
    pen(d, [(80, 42), (90, 46), (86, 56), (76, 52), (80, 42)], 2, INK, seed=54)
    poly_fill(d, ellipse_pts(64, 102, 5, 5), INK)
    save(img, "clock.png", w, h)


# ---------------------------------------------------------------- platforms (341x115 canvas)
# Every platform is a hand-ruled measure of staff; its type is written in music notation.
PW, PH = 341, 115
X0, X1 = 30, 316  # barlines
LINES = [24 + i * 16 for i in range(5)]  # top line = collision top


def measure(sag=0.0, dashed=False, seed=0):
    img = canvas(PW, PH)
    d = ImageDraw.Draw(img)
    poly_fill(d, [(X0, LINES[0]), (X1, LINES[0]), (X1, LINES[-1]), (X0, LINES[-1])], PAPER)
    rng = random.Random(seed)
    for i, y in enumerate(LINES):
        pts = [(X0 + (X1 - X0) * t, y + sag * math.sin(math.pi * t)) for t in np.linspace(0, 1, 12)]
        if dashed:
            for k in range(0, 11, 2):
                pen(d, pts[k:k + 2], 3.2, INK, seed=seed + i * 20 + k, wobble=0.6)
        else:
            pen(d, pts, 3.2, INK, seed=seed + i, wobble=1.0, pressure=0.2)
    return img, d


def barline(d, x, seed, w=3.2):
    pen(d, [(x, LINES[0]), (x + 0.5, LINES[-1])], w, INK, seed=seed, wobble=0.3, pressure=0.05)


def plat_measure():
    img, d = measure(seed=600)
    barline(d, X0, 601)
    barline(d, X1, 602)
    save(img, "plat_measure.png", PW, PH)


def plat_fragile():
    """Broken (dashed) staff with a red-pen crack: it will not hold for long."""
    img, d = measure(dashed=True, seed=610)
    barline(d, X0, 611)
    barline(d, X1, 612)
    pen(d, [(150, 18), (160, 40), (146, 58), (162, 76), (152, 96)], 3.6, RED, seed=613, wobble=0.4, pressure=0.1)
    save(img, "plat_fragile.png", PW, PH)


def plat_repeat():
    """Repeat signs at both ends: this measure goes back and forth."""
    img, d = measure(seed=620)
    for x, thin, dots in ((X0, X0 + 13, X0 + 26), (X1, X1 - 13, X1 - 26)):
        barline(d, x, x, w=9)
        barline(d, thin, thin + 1)
        for y in (LINES[1] + 8, LINES[2] + 8):
            poly_fill(d, ellipse_pts(dots, y, 4.2, 4.2), INK)
    save(img, "plat_repeat.png", PW, PH)


def plat_spring():
    """Sagging lines like a trampoline, marcato accents above: it throws you up."""
    img, d = measure(sag=7, seed=630)
    barline(d, X0, 631)
    barline(d, X1, 632)
    for k, x in enumerate((120, 173, 226)):
        pen(d, [(x - 10, 16), (x, 4), (x + 10, 16)], 3.6, INK, seed=633 + k, wobble=0.3)
    save(img, "plat_spring.png", PW, PH)


def plat_gliss():
    """A glissando slide drawn across the staff: slippery."""
    img, d = measure(seed=640)
    barline(d, X0, 641)
    barline(d, X1, 642)
    pts = [(48 + t * 250, 82 - t * 52 + 5 * math.sin(t * 2 * math.pi * 7)) for t in np.linspace(0, 1, 120)]
    pen(d, pts, 3.4, INK, seed=643, wobble=0.2, pressure=0.0)
    save(img, "plat_gliss.png", PW, PH)


# ---------------------------------------------------------------- goal & page furniture
def clef_layer(size, height, pos, seed):
    return roughen(glyph_layer(size, "\uE050", height, pos, INK), 1.0, seed=seed)


def endpoint():
    w, h = 320, 240
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    for i in range(5):
        y = 92 + i * 18
        pen(d, [(12, y + 2), (160, y - 1), (308, y + 3)], 2.6, INK, seed=110 + i, wobble=1.0)
    img.alpha_composite(clef_layer((w, h), 200, (26, 12), 111))
    for k, (x, y) in enumerate(((176, 80), (222, 54), (266, 28))):
        img.alpha_composite(roughen(glyph_layer((w, h), "\uE1D5", 64 - k * 8, (x, y - 40), INK), 0.8, seed=k))
    save(img, "endpoint.png", w, h)


def staff_long():
    """Hand-ruled five-line staff across the page, ending in a final barline."""
    w, h = 1920, 200
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    for i in range(5):
        y = 40 + i * 30
        pen(d, [(-10, y + 1), (600, y - 2), (1200, y + 1), (1830, y - 1)], 3.2, INK, seed=200 + i, wobble=1.4, pressure=0.2)
    pen(d, [(1820, 36), (1822, 164)], 3.2, INK, seed=210, wobble=0.6)
    pen(d, [(1846, 36), (1847, 164)], 10, INK, seed=211, wobble=0.6, pressure=0.05)
    save(img, "staff_long.png", w, h)


def clef_ink():
    w, h = 140, 260
    img = canvas(w, h)
    img.alpha_composite(clef_layer((w, h), 250, (8, 4), 220))
    save(img, "clef.png", w, h)


def hole():
    """Binding hole punched through the page: the desk shows through."""
    w, h = 72, 72
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    poly_fill(d, ellipse_pts(36, 36, 22, 22), (62, 56, 52))
    pen(d, ellipse_pts(36, 36, 22, 22), 2.0, (196, 186, 166), seed=230, wobble=0.8)
    save(img, "hole.png", w, h)


def ui_underline():
    """One quick, uneven ink swoosh (stretched under the focused button)."""
    w, h = 256, 28
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    pts = [(2, 18), (60, 14), (130, 15), (200, 11), (252, 8)]
    pen(d, pts, 5, INK, seed=121, wobble=1.2, pressure=0.35)
    save(img, "ui_underline.png", w, h, rough=False)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    paper_tile()
    tiantian()
    title_note()
    icon_life()
    letter()
    checkpoint()
    metronome()
    plat_measure()
    plat_fragile()
    plat_repeat()
    plat_spring()
    plat_gliss()
    endpoint()
    staff_long()
    clef_ink()
    hole()
    ui_underline()
