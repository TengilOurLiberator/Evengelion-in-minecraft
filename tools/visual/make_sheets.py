"""Contact sheets: python tools\\visual\\make_sheets.py <folder> [--cols 3 --rows 3 --width 1920] [--glob "s1_*.png"]
Writes <folder>\\sheets\\sheet_NN.png with each tile captioned by its file name (for looking at many pictures at once)."""
import argparse
import glob
import os
import re

from PIL import Image, ImageDraw, ImageFont


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--rows", type=int, default=3)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--glob", default="*.png")
    ap.add_argument("--prefix", default="sheet")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.folder, a.glob)), key=natural)
    files = [f for f in files if os.sep + "sheets" + os.sep not in f]
    tw = a.width // a.cols
    th = int(tw * 9 / 16)
    cap = 18
    out = os.path.join(a.folder, "sheets")
    os.makedirs(out, exist_ok=True)
    per = a.cols * a.rows
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    for n in range(0, len(files), per):
        sheet = Image.new("RGB", (tw * a.cols, (th + cap) * a.rows), (20, 20, 20))
        d = ImageDraw.Draw(sheet)
        for k, f in enumerate(files[n:n + per]):
            im = Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS)
            x, y = (k % a.cols) * tw, (k // a.cols) * (th + cap)
            sheet.paste(im, (x, y + cap))
            d.text((x + 3, y + 2), os.path.basename(f)[:-4], fill=(255, 255, 120), font=font)
        p = os.path.join(out, f"{a.prefix}_{n // per + 1:02d}.png")
        sheet.save(p)
        print(p, len(files[n:n + per]))


if __name__ == "__main__":
    main()
