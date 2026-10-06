#!/usr/bin/env python3
"""Builds the two UI fonts in fonts/ (run from the repo root).

  python3 tools/art/build_fonts.py <Caveat[wght].ttf> <LXGWWenKai-Regular.ttf>

* Caveat (OFL) variable font is pinned to weight 600 -> fonts/Caveat-SemiBold.ttf
* LXGW WenKai (OFL) is subset to GB2312 level-1 hanzi + every character used in
  i18n/translations.csv + ASCII/CJK punctuation, and renamed (OFL reserved font
  name) -> fonts/FTSHand-CJK.ttf. Re-run after adding rare characters to the CSV.
"""
import csv
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def caveat(src):
    font = instancer.instantiateVariableFont(TTFont(src), {"wght": 600})
    font.save(os.path.join(ROOT, "fonts", "Caveat-SemiBold.ttf"))


def charset():
    chars = set(chr(c) for c in range(0x20, 0x7F))
    chars |= set("，。！？、；：“”‘’（）《》【】…—·～ ")
    for hi in range(0xB0, 0xD8):
        for lo in range(0xA1, 0xFF):
            try:
                chars.add(bytes([hi, lo]).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    with open(os.path.join(ROOT, "i18n", "translations.csv"), encoding="utf-8") as f:
        for row in csv.reader(f):
            for cell in row:
                chars |= set(cell)
    return "".join(sorted(c for c in chars if c.isprintable()))


def wenkai(src):
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    font = TTFont(src)
    sub = subset.Subsetter(opts)
    sub.populate(text=charset())
    sub.subset(font)
    family = "FTS Hand CJK"
    for rec in font["name"].names:
        if rec.nameID in (1, 16):
            rec.string = family
        elif rec.nameID == 4:
            rec.string = family + " Regular"
        elif rec.nameID == 6:
            rec.string = "FTSHandCJK-Regular"
    font.save(os.path.join(ROOT, "fonts", "FTSHand-CJK.ttf"))


if __name__ == "__main__":
    caveat(sys.argv[1])
    wenkai(sys.argv[2])
