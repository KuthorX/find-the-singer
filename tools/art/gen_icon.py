#!/usr/bin/env python3
"""Paints the Find The Singer app icon from the same pen as gen_art.py.

Usage:  python3 tools/art/gen_icon.py   (run from the repo root)
Writes images/icon.png (512), images/icon.ico (16-256) and images/icon_web_*.png.
Small sizes are drawn from bolder masters (48-64 px: thicker ink; 32 px: eyes
only, bigger flag; 16 px: bare silhouette) so they stay one clean silhouette instead
of a blurred copy of the 512 art.
"""
import base64
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_art import ACCENT, INK, OUT, PAPER, PAPER_HI, SS, ellipse_pts, pen, periodic_noise, poly_fill, roughen  # noqa: E402

W = 512
ROT = -0.36
ICO_SIZES = (16, 32, 48, 64, 128, 256)
WEB_SIZES = (32, 180)  # favicon (inlined via html/head_include), apple-touch


def rounded_square(inset, radius, n=24):
    """Closed outline of a rounded square in final px."""
    lo, hi = inset, W - inset
    corners = ((hi - radius, lo + radius, -math.pi / 2), (hi - radius, hi - radius, 0.0),
               (lo + radius, hi - radius, math.pi / 2), (lo + radius, lo + radius, math.pi))
    pts = []
    for cx, cy, a0 in corners:
        pts += ellipse_pts(cx, cy, radius, radius, 0.0, n=n, start=a0, end=a0 + math.pi / 2)
    return pts + pts[:1]


# per level: 0 = 128 px and up, 1 = 48-64 px, 2 = 32 px, 3 = 16 px
STEM_W = (44, 52, 62, 66)
FLAG_W = (12, 16, 22, 24)
GROUND = (12, 112)  # inset, corner radius (final px)
PAPER_EDGE = (214, 202, 178)  # the same paper, one shade darker


def ground(level):
    """Paper rounded square, bare edge (no frame line); its alpha clips the art."""
    img = Image.new("RGBA", (W * SS, W * SS), (0, 0, 0, 0))
    poly_fill(ImageDraw.Draw(img), rounded_square(*GROUND), PAPER)
    img = roughen(img, 0.6, seed=31)
    rim = Image.new("RGBA", img.size, (0, 0, 0, 0))  # pencil-grey paper edge for light desktops
    pen(ImageDraw.Draw(rim), rounded_square(GROUND[0] + 2, GROUND[1] - 2), 5, PAPER_EDGE, seed=32, wobble=0.3, pressure=0.1)
    img.alpha_composite(roughen(rim, 0.4, seed=35))
    return img


def head_at(cx, cy, scale):
    c, s = math.cos(ROT), math.sin(ROT)
    return lambda x, y: (cx + (x * c - y * s) * scale, cy + (x * s + y * c) * scale)


def face(d, at, k, level):
    """Two eyes looking up at the flag, and an open singing mouth at full size."""
    if level == 3:
        return
    big = level == 0
    eyes = ((-30, -14), (22, -20)) if big else ((-30, -10), (24, -16))
    r = (15, 20) if big else (17, 22)
    for ex, ey in eyes:
        poly_fill(d, ellipse_pts(*at(ex, ey), r[0] * k, r[1] * k, ROT + 0.15), PAPER)
    pr = (7.5, 10.5) if big else (10, 13)
    for ex, ey in eyes:
        poly_fill(d, ellipse_pts(*at(ex + 5, ey - 6), pr[0] * k, pr[1] * k, ROT), INK)
    if big:  # small "o": singing. Too dot-like below 128 px, so big only
        poly_fill(d, ellipse_pts(*at(0, 30), 9 * k, 7 * k, ROT + 0.2), PAPER)


def character(level):
    """The hero, singing: head low-left, stem and Tianyi-blue flag rising right."""
    cx, cy, k = (222, 340, 1.74) if level < 2 else (212, 352, 1.9)
    at = head_at(cx, cy, k)
    layer = Image.new("RGBA", (W * SS, W * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    body = ellipse_pts(cx, cy, 92 * k, 60 * k, ROT)
    poly_fill(d, body, INK)
    pen(d, body, 6, INK, seed=41, wobble=0.6)
    # stem from the right shoulder of the head, slightly leaning, then the flag
    sx, sy = at(86, -6)
    top = (sx + 8, 66 if level < 2 else 52)
    pen(d, [(sx - 4, sy + 10), (sx + 2, (sy + top[1]) / 2), top], STEM_W[level], INK, seed=43, wobble=1.0, pressure=0.12)
    tx, ty = top[0] - STEM_W[level] * 0.25, top[1] - 6
    f = (0.95, 1.0, 1.25, 1.3)[level]
    spine = [(tx, ty), (tx + 24 * f, ty + 42 * f), (tx + 78 * f, ty + 82 * f), (tx + 104 * f, ty + 136 * f), (tx + 88 * f, ty + 196 * f)]
    inner = [(tx, ty + 84 * f), (tx + 38 * f, ty + 108 * f), (tx + 68 * f, ty + 142 * f), (tx + 82 * f, ty + 190 * f)]
    poly_fill(d, spine + inner[::-1], ACCENT)
    pen(d, spine, FLAG_W[level], INK, seed=45, wobble=0.5)  # inked like the in-game hero
    pen(d, inner, FLAG_W[level] * 0.8, INK, seed=46, wobble=0.5)
    face(d, at, k, level)
    return roughen(layer, 0.7, seed=49)


def master(level):
    img = ground(level)
    art = character(level)
    a = np.asarray(art).copy()
    a[..., 3] = (a[..., 3].astype(np.uint16) * np.asarray(img)[..., 3] // 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(a, "RGBA"))
    return img


def shrink(img, size):
    out = img.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 48:  # crisp the colour edges; alpha stays plain so no halo
        rgb = Image.new("RGB", out.size, PAPER)  # flatten on paper, not on black
        rgb.paste(out, mask=out.getchannel("A"))
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.6, percent=80, threshold=0))
        out = Image.merge("RGBA", (*rgb.split(), out.getchannel("A")))
    return out


def inline_favicon(png_path, presets=os.path.join(os.path.dirname(OUT), "export_presets.cfg")):
    """Embed the hand-sized 32 px favicon in the Web preset's html/head_include."""
    with open(png_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    link = f"<link rel='icon' type='image/png' sizes='32x32' href='data:image/png;base64,{b64}'>"
    with open(presets, encoding="utf-8") as fh:
        text = fh.read()
    new, n = re.subn(r'^html/head_include=".*"$', lambda _: f'html/head_include="{link}"', text, flags=re.M)
    if n != 1:
        raise SystemExit(f"expected one html/head_include in {presets}, found {n}")
    with open(presets, "w", encoding="utf-8") as fh:
        fh.write(new)


def main(out_dir=OUT):
    masters = [master(level) for level in range(4)]
    pick = lambda s: shrink(masters[3 if s <= 16 else 2 if s <= 32 else 1 if s <= 64 else 0], s)  # noqa: E731
    pick(512).save(os.path.join(out_dir, "icon.png"))
    ico = [pick(s) for s in ICO_SIZES]
    ico[-1].save(os.path.join(out_dir, "icon.ico"), sizes=[(s, s) for s in ICO_SIZES], append_images=ico[:-1])
    for s in WEB_SIZES:
        pick(s).save(os.path.join(out_dir, f"icon_web_{s}.png"))
    if out_dir == OUT:
        inline_favicon(os.path.join(out_dir, "icon_web_32.png"))
    print("wrote icon.png, icon.ico, icon_web_*.png to", out_dir)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
