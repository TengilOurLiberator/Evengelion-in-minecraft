"""Side-by-side before/after pictures from two folders of shots with the same file names.

    python tools\\visual\\pairs.py BEFORE_DIR AFTER_DIR OUT_DIR [--scale 0.5]

Every PNG that exists in both folders becomes OUT_DIR\\<name>.png: before on the left, after on the right, a thin white
line between, with "before" / "after" and the mean brightness written in the top corners.
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw


def luma(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    return float(0.2126 * a[..., 0].mean() + 0.7152 * a[..., 1].mean() + 0.0722 * a[..., 2].mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("out")
    ap.add_argument("--scale", type=float, default=0.6)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(a.after)):
        if not f.lower().endswith(".png") or not os.path.isfile(os.path.join(a.before, f)):
            continue
        b, c = Image.open(os.path.join(a.before, f)).convert("RGB"), Image.open(os.path.join(a.after, f)).convert("RGB")
        w, h = int(b.width * a.scale), int(b.height * a.scale)
        b, c = b.resize((w, h), Image.LANCZOS), c.resize((w, h), Image.LANCZOS)
        out = Image.new("RGB", (w * 2 + 4, h), "white")
        out.paste(b, (0, 0))
        out.paste(c, (w + 4, 0))
        d = ImageDraw.Draw(out)
        for x, label, im in ((6, "before", b), (w + 10, "after", c)):
            d.rectangle((x - 3, 3, x + 150, 20), fill=(0, 0, 0))
            d.text((x, 6), f"{label}  mean {luma(im):.1f}", fill=(255, 255, 255))
        out.save(os.path.join(a.out, f))
        n += 1
    print(f"{n} pairs in {a.out}")


if __name__ == "__main__":
    main()
