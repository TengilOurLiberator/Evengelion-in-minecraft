"""Read the frame rate from a picture of the F3 overlay: the text is matched against the game's own font atlas (ascii.png of the
26.3 client jar, read only), so no OCR library is needed. read_fps(img, gui_scale) -> int or None."""
import os
import re
import zipfile

import numpy as np

MC = os.path.join(os.environ.get("APPDATA", ""), ".minecraft")
_ATLAS = {}


def _glyphs(font_zip=None):
    """{char: trimmed boolean bitmap} for ASCII 0x21..0x7e as the F3 overlay draws them: textures/font/ascii.png (16x16 grid) of
    the resource pack zip font_zip (e.g. Faithful's, 16 px cells) or of the 26.3 client jar (8 px cells), brought down to 8 px cells;
    a pixel is set if the glyph covers any part of it (the text shader keeps the full colour for every touched pixel)."""
    key = font_zip or ""
    if key not in _ATLAS:
        from PIL import Image
        import io
        src = font_zip or os.path.join(MC, "versions", "26.3", "26.3.jar")
        with zipfile.ZipFile(src) as z:
            im = Image.open(io.BytesIO(z.read("assets/minecraft/textures/font/ascii.png"))).convert("RGBA")
        a = np.asarray(im)[:, :, 3] > 128
        cell = im.width // 16
        f = max(1, cell // 8)
        if f > 1:
            h, w = a.shape
            a = a.reshape(h // f, f, w // f, f).any(axis=(1, 3))
        cell = 8
        out = {}
        for code in range(0x21, 0x7F):
            r, c = divmod(code, 16)
            g = a[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell]
            ys, xs = np.nonzero(g)
            if len(ys):
                out[chr(code)] = g[:, xs.min():xs.max() + 1]
        _ATLAS[key] = out
    return _ATLAS[key]

def _runs(flags):
    """[(start, end)] of consecutive True values."""
    res, start = [], None
    for i, f in enumerate(list(flags) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            res.append((start, i))
            start = None
    return res


def _classify(bm, font_zip=None):
    """Nearest glyph by Hamming distance (bm: boolean, 8 rows from the top of the text line, columns trimmed); '?' if it is far from all."""
    h, w = bm.shape
    best, score = "?", 1e9
    for ch, t in _glyphs(font_zip).items():
        W = max(w, t.shape[1])
        a = np.zeros((8, W), bool)
        b = np.zeros((8, W), bool)
        a[:min(8, h), :w] = bm[:8]
        b[:, :t.shape[1]] = t
        d = int(np.sum(a != b)) + 2 * abs(w - t.shape[1])
        if d < score:
            best, score = ch, d
    return best if score <= 9 else "?"

def read_text_lines(img, gui_scale, region=(0, 0, 900, 330), color=224, font_zip=None):
    """The text lines of one text colour (the F3 overlay writes white 224 and grey 170) in the region as strings (no spaces)."""
    a = np.asarray(img.convert("RGB"), dtype=np.uint8)[region[1]:region[3], region[0]:region[2]].astype(np.int16)
    mask = (np.abs(a - color) <= 1).all(axis=2)
    s = max(1, int(gui_scale))
    lines = []
    for r0, r1 in _runs(mask.any(axis=1)):
        if r1 - r0 < 4 * s or r1 - r0 > 12 * s:
            continue
        band = mask[r0:r1]
        text, last = "", None
        for c0, c1 in _runs(band.any(axis=0)):
            if last is not None and c0 - last >= 4 * s:
                text += " "
            last = c1
            g = band[:, c0:c1]
            h, w = g.shape
            if w % s or h % s:
                gh, gw = max(1, round(h / s)), max(1, round(w / s))
            else:
                gh, gw = h // s, w // s
            bm = np.zeros((gh, gw), dtype=bool)
            for y in range(gh):
                for x in range(gw):
                    blk = g[y * s:(y + 1) * s, x * s:(x + 1) * s]
                    bm[y, x] = blk.size and blk.mean() > 0.5
            text += _classify(bm, font_zip)
        lines.append(text)
    return lines


def read_fps(img, gui_scale=1, font_zip=None):
    """(average fps, p50, p98, p99.9) from the overlay: "954 fps T: ..." in white, "p50=1033 p98=673 p99.9=570 fps" in grey.
    Values the picture does not show are None; returns None if not even the first number was read."""
    avg = None
    for s in (gui_scale, 1, 2):
        for line in read_text_lines(img, s, font_zip=font_zip):
            m = re.search(r"^(\d+) ?fps", line)
            if m:
                avg = int(m.group(1))
                break
        if avg is not None:
            break
        gui_scale = s
    if avg is None:
        return None
    pct = (None, None, None)
    for line in read_text_lines(img, 1, font_zip=font_zip):       # the numbers of "p50=1033 p98=673 p99.9=570 fps" are white
        m = re.fullmatch(r"(\d+) (\d+) (\d+)", line.strip())
        if m:
            pct = tuple(int(x) for x in m.groups())
            break
    return (avg,) + pct





