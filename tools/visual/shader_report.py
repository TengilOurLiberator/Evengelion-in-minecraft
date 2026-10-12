"""Report on the shader gallery (plan "shaders", one folder per variant in work\\shots\\shaders): the FPS table (average frames per
second at each view, from the F3 overlay, and the same as milliseconds per frame) and one contact sheet per view with all variants side by side.

    python tools\\visual\\shader_report.py [--root work\\shots\\shaders] [--variants a_vanilla,b_mods,...]
"""
import argparse
import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(root, variants):
    data = {}
    for v in variants:
        p = os.path.join(root, v, "manifest.json")
        if os.path.exists(p):
            data[v] = {s["name"]: s for s in json.load(open(p, encoding="utf-8"))["shots"] if "file" in s}
    return data


def table(data, variants):
    views = sorted({n for d in data.values() for n in d})
    lines = ["| view | " + " | ".join(variants) + " |", "|---|" + "---|" * len(variants)]
    sums = {v: [] for v in variants}
    for n in views:
        row = []
        for v in variants:
            s = data.get(v, {}).get(n)
            f = s.get("fps") if s else None
            row.append(f"{f} ({1000.0 / f:.2f} ms)" if f else "-")
            if f and not n.startswith("15_") and not n.startswith("16_"):
                sums[v].append(f)
        lines.append(f"| {n} | " + " | ".join(row) + " |")
    avg = []
    for v in variants:
        if sums[v]:
            ms = sum(1000.0 / f for f in sums[v]) / len(sums[v])        # mean frame time (the harmonic mean of the frame rates)
            avg.append(f"{1000.0 / ms:.0f} ({ms:.2f} ms)")
        else:
            avg.append("-")
    lines.append("| **mean, views 1-14** | " + " | ".join(avg) + " |")
    return "\n".join(lines)


def sheets(root, data, variants, out, tile=(800, 450), cols=3):
    os.makedirs(out, exist_ok=True)
    views = sorted({n for d in data.values() for n in d})
    for n in views:
        have = [v for v in variants if n in data.get(v, {})]
        rows = (len(have) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tile[0], rows * tile[1]), (20, 20, 20))
        for i, v in enumerate(have):
            im = Image.open(data[v][n]["file"]).convert("RGB").resize(tile, Image.LANCZOS)
            d = ImageDraw.Draw(im)
            f = data[v][n].get("fps")
            label = f"{v}  {f} fps" if f else v
            d.rectangle((0, 0, 8 * len(label) + 10, 18), fill=(0, 0, 0))
            d.text((5, 3), label, fill=(255, 255, 255))
            sheet.paste(im, ((i % cols) * tile[0], (i // cols) * tile[1]))
        sheet.save(os.path.join(out, n + ".png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(ROOT, "work", "shots", "shaders"))
    ap.add_argument("--variants", default="a_vanilla,b_mods,c_reimagined,d_reimagined_nocolor,e_bsl,f_makeup")
    ap.add_argument("--tile", default="800x450")
    ap.add_argument("--cols", type=int, default=3)
    a = ap.parse_args()
    variants = a.variants.split(",")
    data = load(a.root, variants)
    variants = [v for v in variants if v in data]
    t = table(data, variants)
    print(t)
    open(os.path.join(a.root, "fps_table.md"), "w", encoding="utf-8").write(t + "\n")
    tw, th = (int(x) for x in a.tile.split("x"))
    sheets(a.root, data, variants, os.path.join(a.root, "sheets"), (tw, th), a.cols)


if __name__ == "__main__":
    main()
