"""The title-card typeface: a Minecraft bitmap font built in Python from an openly licensed serif.

    python cardfont.py            write the font into the resource pack (idempotent), print the metrics
    python cardfont.py --preview PNG   also draw the four cards the way the game lays the glyphs out (for looking at)

Source: KaTeX_Main-Bold.ttf (capitals, digits, punctuation) and KaTeX_Main-Regular.ttf (lower case, for the small line), copied into
tools/story/fonts/ from the gradio package of the shared venv.  Both are Computer Modern Roman, (c) 2009-2010 Design Science, Inc.
and (c) 2014-2018 Khan Academy, under the SIL Open Font License 1.1 (the licence text is in the fonts' own name tables; see
fonts/LICENSE-KaTeX.txt, which is also copied next to the generated font).  Windows system fonts are not used: they cannot be shipped.

What is written (all new files, nothing existing is touched):
    pack/angel-resources/assets/angel/font/card.json         the font definition ("angel:card")
    pack/angel-resources/assets/angel/textures/font/card.png the glyph atlas (16 x 5 cells of 128 x 128 px)
    pack/angel-resources/assets/angel/textures/font/LICENSE-KaTeX.txt

How it works (checked against the vanilla font definitions in the 26.3 client jar, assets/minecraft/font/include/*.json):
  * one `bitmap` provider: file "angel:font/card.png" (= textures/font/card.png), `height` 16 font units for a 128 px cell (so one unit is
    8 px and the capitals are 10 units tall), `ascent` 13 (the baseline is 13 units below the top of the cell), `chars` = five rows of
    sixteen code points, "\\u0000" for an empty cell;
  * one `space` provider for the word gap;
  * the game gives every glyph the advance  int(0.5 + actual_width * height / cell_height) + 1,  where actual_width is the column of the
    right-most non-transparent pixel of the cell.  Letter spacing is made by putting one pixel of alpha 1 (white, 1/255: the text shader
    discards it) half a spacing to the right of the glyph's own advance, and starting the glyph half a spacing in from the left, so the
    gap is the font's own side bearings plus SPACING px, shared evenly, and a centred line stays centred;
  * the capitals are condensed to CONDENSE of their width when they are drawn (a bold, narrow, widely spaced capital).
"""
import io
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONT_DIR = os.path.join(HERE, "fonts")
BOLD = os.path.join(FONT_DIR, "KaTeX_Main-Bold.ttf")
REGULAR = os.path.join(FONT_DIR, "KaTeX_Main-Regular.ttf")
LICENSE_SRC = os.path.join(FONT_DIR, "LICENSE-KaTeX.txt")
ASSETS = os.path.join(ROOT, "pack", "angel-resources", "assets", "angel")
OUT_JSON = os.path.join(ASSETS, "font", "card.json")
OUT_PNG = os.path.join(ASSETS, "textures", "font", "card.png")
OUT_LICENSE = os.path.join(ASSETS, "textures", "font", "LICENSE-KaTeX.txt")

FONT_ID = "angel:card"
CELL = 144                         # px, square cells
COLS = 16
HEIGHT = 18                        # font units for one cell (vanilla's default is 8 for a 8 px cell)
ASCENT = 15                        # units from the top of the cell to the baseline
CAP_PX = 80                        # px, height of a capital letter (10 units)
CONDENSE = 0.84                    # horizontal scale of the glyphs
SPACING = 22                       # px added between neighbouring glyphs (2.75 units), shared half and half
SPACE_UNITS = 8                    # advance of the space character
ROWS = ["ABCDEFGHIJKLMNOP",
        "QRSTUVWXYZ012345",
        "6789.,'-!?:;&\"",
        "abcdefghijklmnop",
        "qrstuvwxyz"]
ROWS = [r + "\u0000" * (COLS - len(r)) for r in ROWS]
SCALE = HEIGHT / CELL              # font units per px


def _font(path, size):
    return ImageFont.truetype(path, size)


def _size_for_cap():
    """Font size (px per em) at which a capital H is CAP_PX tall."""
    lo, hi = 40, 400
    while hi - lo > 1:
        mid = (lo + hi) // 2
        b = _font(BOLD, mid).getbbox("H", anchor="ls")
        if -b[1] >= CAP_PX:
            hi = mid
        else:
            lo = mid
    return hi


def build():
    """Returns (png_bytes, json_text, advance_units {char: units}, atlas RGBA array)."""
    size = _size_for_cap()
    fb, fr = _font(BOLD, size), _font(REGULAR, size)
    atlas = np.zeros((CELL * len(ROWS), CELL * COLS, 4), np.uint8)
    atlas[:, :, :3] = 255
    base_y = int(round(ASCENT / SCALE))                  # baseline row inside a cell: 104
    half = SPACING // 2
    chars = {}
    for r, row in enumerate(ROWS):
        for c, ch in enumerate(row):
            if ch == "\u0000":
                continue
            f = fr if ch.islower() else fb
            adv = f.getlength(ch) * CONDENSE
            l, t, rr, b = f.getbbox(ch, anchor="ls")
            pad = 6
            w = rr - l + 2 * pad
            hgt = b - t + 2 * pad
            tile = Image.new("L", (w, hgt), 0)
            ImageDraw.Draw(tile).text((pad - l, pad - t), ch, font=f, fill=255, anchor="ls")
            nw = max(1, int(round(w * CONDENSE)))
            tile = tile.resize((nw, hgt), Image.LANCZOS)
            x0 = half + int(round((l - pad) * CONDENSE))           # tile's left edge in the cell: origin + bearing
            y0 = base_y + t - pad
            a = np.array(tile)
            # clip to the cell
            cx0, cy0 = max(0, x0), max(0, y0)
            cx1, cy1 = min(CELL, x0 + nw), min(CELL, y0 + hgt)
            if cx1 <= cx0 or cy1 <= cy0 or x0 < 0 or y0 < 0 or x0 + nw > CELL or y0 + hgt > CELL:
                # the ink padding may overhang; only the ink itself must fit
                ink = np.argwhere(a > 8)
                if ink.size and (x0 + ink[:, 1].min() < 0 or x0 + ink[:, 1].max() >= CELL or y0 + ink[:, 0].min() < 0
                                 or y0 + ink[:, 0].max() >= CELL):
                    raise ValueError(f"glyph {ch!r} does not fit its {CELL}px cell")
            ox, oy = c * CELL, r * CELL
            sub = a[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
            atlas[oy + cy0:oy + cy1, ox + cx0:ox + cx1, 3] = np.maximum(atlas[oy + cy0:oy + cy1, ox + cx0:ox + cx1, 3], sub)
            # the invisible marker that sets the advance: alpha 1, at the end of the spaced advance
            end = int(round(half + adv + half))
            if end >= CELL:
                raise ValueError(f"glyph {ch!r}: advance {end} px does not fit the cell")
            if atlas[oy:oy + CELL, ox + end - 1, 3].max() == 0:
                atlas[oy + CELL - 1, ox + end - 1, 3] = 1
            else:
                atlas[oy + CELL - 1, ox + end - 1, 3] = max(1, atlas[oy + CELL - 1, ox + end - 1, 3])
            chars[ch] = (r, c)
    # advances the way the game computes them
    adv_units = {}
    for ch, (r, c) in chars.items():
        cell = atlas[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL, 3]
        cols = np.nonzero(cell.max(axis=0))[0]
        actual = int(cols.max()) + 1
        adv_units[ch] = int(0.5 + actual * SCALE) + 1
    adv_units[" "] = SPACE_UNITS
    img = Image.fromarray(atlas, "RGBA")
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    definition = {"providers": [
        {"type": "bitmap", "file": "angel:font/card.png", "ascent": ASCENT, "height": HEIGHT, "chars": ROWS},
        {"type": "space", "advances": {" ": SPACE_UNITS}},
    ]}
    return buf.getvalue(), json.dumps(definition, indent=2) + "\n", adv_units, atlas


_CACHE = {}


def metrics():
    if "m" not in _CACHE:
        _CACHE["m"] = build()
    return _CACHE["m"]


def advance_units(text):
    """Width of `text` in font units, as the game lays it out (unknown characters count as the width of 'M')."""
    adv = metrics()[2]
    return sum(adv.get(ch, adv["M"]) for ch in text)


def covers(text):
    return all(ch in metrics()[2] for ch in text)


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.isfile(path):
        with open(path, "rb") as f:
            if f.read() == data:
                return False
    with open(path, "wb") as f:
        f.write(data)
    return True


def write_assets():
    """Write the font into the resource pack; returns the list of files that changed."""
    png, js, _, _ = metrics()
    changed = []
    for path, data in ((OUT_PNG, png), (OUT_JSON, js.encode("utf-8")), (OUT_LICENSE, open(LICENSE_SRC, "rb").read())):
        if _write(path, data):
            changed.append(path)
    return changed


def preview(path, lines=(("ANGEL ATTACK", None), ("A.D. 2015", None), ("EVANGELION  UNIT 01", None), ("TO BE CONTINUED", "an unofficial fan work"))):
    """Draw cards the way the game lays glyphs out: each glyph's cell at the running advance, the baseline on one line."""
    png, js, adv, atlas = metrics()
    unit = 4                                    # px per font unit in the preview
    rows = []
    for main, small in lines:
        rows.append((main, 1.0))
        if small:
            rows.append((small, 0.55))
    W = 1700
    img = Image.new("RGB", (W, 150 * len(rows) + 40), (0, 0, 0))
    y = 20
    for text, k in rows:
        total = sum(adv.get(ch, adv["M"]) for ch in text) * unit * k
        x = (W - total) / 2.0
        cellpx = CELL * SCALE * unit * k
        for ch in text:
            if ch in adv and ch != " ":
                r_, c_ = next((r, row.index(ch)) for r, row in enumerate(ROWS) if ch in row)
                cell = Image.fromarray(atlas[r_ * CELL:(r_ + 1) * CELL, c_ * CELL:(c_ + 1) * CELL], "RGBA")
                cell = cell.resize((int(cellpx), int(cellpx)), Image.LANCZOS)
                top = y + 60 * k - ASCENT * unit * k + 50
                img.paste(Image.new("RGB", cell.size, (255, 255, 255)), (int(x), int(top)), cell.getchannel("A"))
            x += adv.get(ch, adv["M"]) * unit * k
        y += int(150 * (1.0 if k == 1.0 else 0.6))
    img.save(path)


def main(argv):
    changed = write_assets()
    png, js, adv, atlas = metrics()
    print("card font: %d glyphs, atlas %dx%d, %d bytes; files changed: %s" % (len(adv) - 1, atlas.shape[1], atlas.shape[0], len(png),
                                                                         [os.path.relpath(p, ROOT) for p in changed] or "none"))
    for text in ("ANGEL ATTACK", "A.D. 2015", "EVANGELION  UNIT 01", "TO BE CONTINUED", "an unofficial fan work"):
        u = advance_units(text)
        print(f"  {text!r:28s} {u:4d} units = {u * 0.025:.2f} blocks at scale 1")
    if "--preview" in argv:
        preview(argv[argv.index("--preview") + 1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

