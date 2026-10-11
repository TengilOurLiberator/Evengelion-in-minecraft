"""analyze.py - look at and check every sound.

    python analyze.py                  # all sounds: preview/<name>.png + report.md + report.json
    python analyze.py sfx.mine amb     # just these (names or prefixes)
    python analyze.py --sheet amb      # also write preview/_sheet_<prefix>.png contact sheets (spectrograms, 6 per page)

Each preview has: waveform (L blue / R orange), short-term level in dB, a log-frequency spectrogram (30 Hz - 20 kHz,
80 dB range), and for loops a zoom of the join (last 25 ms + first 25 ms, the vertical line is the join).
The checks run on the decoded .ogg, not on the float source, so they see what the game will play.
"""
import argparse
import json
import os
import sys

import numpy as np
import scipy.signal as sg
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsp
import reg
import make_sound as ms

PREVIEW = os.path.join(HERE, "preview")
STOPS = [(0.0, (0, 0, 4)), (0.14, (31, 12, 72)), (0.29, (85, 15, 109)), (0.43, (136, 34, 106)), (0.57, (186, 54, 85)),
         (0.71, (227, 89, 51)), (0.86, (249, 140, 10)), (1.0, (252, 255, 164))]

# name -> (seconds, tolerance) for sounds with a specified length
EXPECT = {"sfx.mine": (9.0, 0.002), "sfx.ears_ringing": (8.0, 0.002), "sfx.siren": (20.0, 0.002), "sfx.gurney": (6.0, 0.002),
          "sfx.heartbeat": (10.0, 0.002), "sfx.klaxon": (4.0, 0.002), "sfx.air_open": (3.0, 0.002), "sfx.fluid_fill": (8.0, 0.002),
          "sfx.launch_charge": (3.0, 0.002), "sfx.beam_charge": (2.0, 0.002), "music.resolve": (12.0, 0.002),
          "music.defeat": (8.0, 0.002), "music.victory": (40.0, 0.002), "music.descent": (50.0, 1.5), "sfx.breaker": (1.2, 0.15),
          "sfx.launch_roar": (6.0, 0.002)}


def font(size=12):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def cmap(v):
    v = np.clip(v, 0, 1)
    xs = [s[0] for s in STOPS]
    out = np.zeros(v.shape + (3,), dtype=np.uint8)
    for c in range(3):
        out[..., c] = np.interp(v, xs, [s[1][c] for s in STOPS]).astype(np.uint8)
    return out


def spectrogram(x, width, height=260, fmin=30, fmax=20000, rng=80.0):
    m = dsp.mono(x)
    nfft = 4096
    hop = max(256, (len(m) - nfft) // max(width, 1))
    win = np.hanning(nfft)
    if len(m) < nfft:
        m = np.pad(m, (0, nfft - len(m)))
    nfr = (len(m) - nfft) // hop + 1
    idx = np.arange(nfft)[None, :] + hop * np.arange(nfr)[:, None]
    S = np.abs(np.fft.rfft(m[idx] * win, axis=1)) ** 2 / (win ** 2).sum()
    f = np.fft.rfftfreq(nfft, 1 / dsp.SR)
    rows = np.exp(np.linspace(np.log(fmax), np.log(fmin), height))
    pos = np.interp(rows, f, np.arange(len(f)))
    lo = np.floor(pos).astype(int)
    hi = np.minimum(lo + 1, len(f) - 1)
    w = pos - lo
    img = S[:, lo] * (1 - w) + S[:, hi] * w                    # frames x rows
    d = 10 * np.log10(img + 1e-14)
    ref = np.percentile(d, 99.9)
    d = (d - (ref - rng)) / rng
    d = np.repeat(d.T, 1, axis=1)
    # resample columns to width
    cols = np.minimum((np.arange(width) * d.shape[1] / width).astype(int), d.shape[1] - 1)
    return cmap(d[:, cols])


def waveform(x, width, height=110):
    img = Image.new("RGB", (width, height), (14, 14, 18))
    dr = ImageDraw.Draw(img)
    chans = [x] if x.ndim == 1 else [x[:, 0], x[:, 1]]
    n = len(chans[0])
    cols = [(90, 160, 255), (255, 170, 70)]
    dr.line([(0, height // 2), (width, height // 2)], fill=(40, 40, 50))
    for c, ch in enumerate(chans):
        edges = np.linspace(0, n, width + 1).astype(int)
        for i in range(width):
            seg = ch[edges[i]:max(edges[i] + 1, edges[i + 1])]
            if len(seg) == 0:
                continue
            a, b = seg.min(), seg.max()
            dr.line([(i, height / 2 - b * height / 2 * 0.95), (i, height / 2 - a * height / 2 * 0.95)], fill=cols[c])
    return img


def level_plot(x, width, height=60):
    img = Image.new("RGB", (width, height), (14, 14, 18))
    dr = ImageDraw.Draw(img)
    m = dsp.mono(x)
    win = dsp.N(0.1)
    nb = max(1, len(m) // win)
    e = 10 * np.log10(np.mean(m[:nb * win].reshape(nb, win) ** 2, axis=1) + 1e-12)
    for g in (-60, -40, -20):
        y = height * (-g) / 80.0
        dr.line([(0, y), (width, y)], fill=(40, 40, 55))
    pts = [(i * width / max(nb - 1, 1), min(height - 1, max(0, height * (-v) / 80.0))) for i, v in enumerate(e)]
    if len(pts) > 1:
        dr.line(pts, fill=(120, 230, 140))
    return img


def join_plot(x, width, height=70):
    img = Image.new("RGB", (width, height), (14, 14, 18))
    dr = ImageDraw.Draw(img)
    k = dsp.N(0.025)
    m = x if x.ndim == 1 else x[:, 0]
    seg = np.concatenate([m[-k:], m[:k]])
    sc = max(np.max(np.abs(seg)), 1e-6)
    pts = [(i * width / len(seg), height / 2 - seg[i] / sc * height / 2 * 0.9) for i in range(len(seg))]
    dr.line(pts, fill=(250, 220, 90))
    dr.line([(width / 2, 0), (width / 2, height)], fill=(255, 60, 60))
    return img


def render(name, y, rec, path, width=900):
    sp = Image.fromarray(spectrogram(y, width))
    wf = waveform(y, width)
    lv = level_plot(y, width)
    parts = [wf, lv, sp]
    spec = reg.REG.get(name)
    if spec is not None and spec.loop:
        parts.append(join_plot(y, width))
    H = 24 + sum(p.height for p in parts) + 4 * len(parts)
    img = Image.new("RGB", (width, H), (0, 0, 0))
    dr = ImageDraw.Draw(img)
    f = font(13)
    label = (f"{name}  {rec['seconds']:.2f}s  {rec['channels']}ch  {rec['lufs']:.1f} LUFS  tp {rec['true_peak']:.1f}  "
             f"{'LOOP' if rec['loop'] else ''}")
    dr.text((6, 4), label, fill=(235, 235, 235), font=f)
    yy = 24
    for p in parts:
        img.paste(p, (0, yy))
        yy += p.height + 4
    img.save(path)
    return img


def checks(name, y, rec):
    spec = reg.REG.get(name)
    sr = rec["sample_rate"]
    m = dsp.mono(y)
    res = {}
    flags = []
    res["peak_db"] = round(dsp.sample_peak_db(y), 2)
    res["true_peak_db"] = round(dsp.true_peak_db(y), 2)
    res["lufs"] = round(dsp.lufs(y), 2)
    res["dc"] = round(float(np.max(np.abs(np.mean(y, axis=0)))), 6)
    res["clipped_samples"] = int(np.sum(np.abs(y) >= 0.999))
    if res["true_peak_db"] > -1.0:
        flags.append("true peak above -1 dBFS")
    if res["clipped_samples"]:
        flags.append("clipping")
    if res["dc"] > 0.003:
        flags.append("DC offset")
    ab = np.abs(m)
    nz = np.where(ab > db_(-60))[0]
    if len(nz) == 0:
        flags.append("SILENT")
    else:
        res["lead_silence_s"] = round(nz[0] / sr, 3)
        res["tail_silence_s"] = round((len(m) - 1 - nz[-1]) / sr, 3)
    if name in EXPECT:
        want, tol = EXPECT[name]
        res["duration_ok"] = abs(rec["seconds"] - want) <= tol
        if not res["duration_ok"]:
            flags.append(f"duration {rec['seconds']} != {want}")
    if spec is not None and spec.loop:
        # A click at the join is a broadband impulse.  Look at the >2 kHz part of the signal around the join (the
        # decoded ogg, so codec noise is included) and compare its peak within +-0.5 ms to the 99.9th percentile of the
        # same quantity over the whole file; ~1 or less = indistinguishable from any other place in the loop.
        hpf = sg.butter(4, 2000.0 / (dsp.SR / 2), "high", output="sos")
        mm = dsp.mono(y)
        k = 8192
        seg = np.concatenate([mm[-k:], mm[:k]])
        hs = np.abs(sg.sosfiltfilt(hpf, seg))
        ref = max(float(np.percentile(np.abs(sg.sosfilt(hpf, mm)), 99.9)), db_(-80))
        jp = float(hs[k - dsp.N(0.0005):k + dsp.N(0.0005)].max())
        res["join_hf_ratio"] = round(jp / ref, 2)
        tk_ = rec["seconds"] * 20.0
        res["loop_ticks"] = round(tk_, 3)
        if abs(tk_ - round(tk_)) > 1e-3:
            flags.append(f"loop length {rec['seconds']} s is not a whole number of ticks ({tk_:.2f})")
        w = dsp.N(0.1)
        yy = y if y.ndim == 2 else y[:, None]
        a_ = 10 * np.log10(np.mean(yy[-w:] ** 2) + 1e-14)
        b_ = 10 * np.log10(np.mean(yy[:w] ** 2) + 1e-14)
        res["join_level_diff_db"] = round(float(a_ - b_), 2)
        e20 = dsp.N(0.02)
        l_first = 10 * np.log10(np.mean(yy[:e20] ** 2) + 1e-14)
        l_last = 10 * np.log10(np.mean(yy[-e20:] ** 2) + 1e-14)
        res["join_onset_db"] = round(float(l_first - l_last), 1)
        onset = (l_first - l_last) > 12.0
        res["join_note"] = "downbeat/onset at the join (by design)" if onset else "ok"
        if res["join_hf_ratio"] > 1.3 and not onset:
            flags.append(f"loop join click (hf ratio {res['join_hf_ratio']})")
            res["join_note"] = "check"
        if abs(res["join_level_diff_db"]) > 6.0 and not onset and spec.kind == "amb":
            flags.append("loop join level jump")
    if spec is not None and not spec.loop:
        # unintended cuts: a step of >30% of the local peak, where the signal was audible (> -50 dBFS) just before and
        # is <10% of that for the next 2 ms (a truncated tail), away from the end of the file
        from scipy.ndimage import maximum_filter1d
        a_ = np.abs(m)
        pre = maximum_filter1d(a_, size=101, origin=50)
        post = maximum_filter1d(a_, size=101, origin=-50)
        d_ = np.abs(np.diff(m, append=m[-1]))
        cand = np.where((d_ > 0.3 * pre) & (post < 0.1 * pre) & (pre > db_(-50)))[0]
        cand = [int(i) for i in cand if i < len(m) - dsp.N(0.03)]
        if name == "sfx.mine":
            cand = [i for i in cand if abs(i / sr - 0.4) > 0.01]
        if name == "sfx.alarm_cut":
            cand = [i for i in cand if abs(i / sr - 0.8) > 0.01]
        if cand:
            ts = sorted(set(round(i / sr, 2) for i in cand))
            res["cut_times_s"] = ts[:8]
            flags.append("abrupt cut at " + ", ".join(str(x) for x in ts[:4]) + " s")
    if name == "sfx.mine":
        t = np.arange(len(m)) / sr
        win = (t > 0.45) & (t < 2.35)
        res["silence_window_peak_db"] = round(float(dsp.todb(np.max(np.abs(m[win])))), 1)
        onset = np.where(np.abs(m) > db_(-30))[0]
        late = onset[onset > int(2.0 * sr)]
        res["blast_onset_s"] = round(float(late[0] / sr), 4) if len(late) else None
        early = onset[onset < int(1.0 * sr)]
        res["whine_end_s"] = round(float(early[-1] / sr), 4) if len(early) else None
        if res["silence_window_peak_db"] > -70:
            flags.append("mine silence window not silent")
        if res["blast_onset_s"] is None or abs(res["blast_onset_s"] - 2.4) > 0.03:
            flags.append("mine blast not at 2.4 s")
    if name == "music.descent":
        mm = dsp.mono(y)
        w = dsp.N(0.05)
        nb = len(mm) // w
        e = 10 * np.log10(np.mean(mm[:nb * w].reshape(nb, w) ** 2, axis=1) + 1e-14)
        de = np.diff(e)
        i0, i1 = int(3.0 / 0.05), int(15.0 / 0.05)
        k = int(np.argmax(de[i0:i1])) + i0
        res["bloom_steepest_rise_s"] = round((k + 1) * 0.05, 2)
        base_lvl = float(np.mean(e[int(6.0 / 0.05):int(7.4 / 0.05)]))
        up = np.where(e[int(6.0 / 0.05):] > base_lvl + 9.0)[0]
        res["bloom_onset_s"] = round((up[0] + int(6.0 / 0.05)) * 0.05, 2) if len(up) else None
        res["bloom_rise_db"] = round(float(e[int(8.6 / 0.05)] - base_lvl), 1)
        res["bloom_expected_s"] = rec.get("bloom_s")
        if res["bloom_onset_s"] is None or abs(res["bloom_onset_s"] - 8.0) > 0.25:
            flags.append("bloom not at 8 s")
    if spec is not None:
        tgt = spec.lufs
        if tgt is not None and abs(res["lufs"] - tgt) > 1.0 and not spec.loop is None:
            flags.append(f"lufs {res['lufs']} vs target {tgt}")
    res["flags"] = flags
    return res


def db_(v):
    return 10 ** (v / 20.0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--sheet", nargs="*", help="prefixes to make contact sheets for")
    ap.add_argument("--no-images", action="store_true")
    a = ap.parse_args(argv)
    ms.load_modules()
    with open(ms.MANIFEST, encoding="utf-8") as fh:
        man = json.load(fh)
    os.makedirs(PREVIEW, exist_ok=True)
    names = [n for n in sorted(man) if ms.matches(n, a.names)]
    report = {}
    sheets = {}
    for n in names:
        rec = man[n]
        path = os.path.join(ms.ROOT, rec["file"])
        if not os.path.exists(path):
            continue
        y, sr = sf.read(path, dtype="float64")
        rec = dict(rec, sample_rate=sr)
        report[n] = checks(n, y, rec)
        if not a.no_images:
            img = render(n, y, rec, os.path.join(PREVIEW, n + ".png"))
            sheets[n] = img
    # contact sheets
    for pref in (a.sheet or []):
        items = [n for n in names if n.startswith(pref)]
        for pg in range(0, len(items), 6):
            chunk = items[pg:pg + 6]
            ims = [sheets[n].resize((600, int(sheets[n].height * 600 / 900))) for n in chunk]
            cols = 2
            rows = (len(ims) + 1) // 2
            hh = max(i.height for i in ims)
            sheet = Image.new("RGB", (1200, hh * rows), (0, 0, 0))
            for i, im in enumerate(ims):
                sheet.paste(im, ((i % cols) * 600, (i // cols) * hh))
            sheet.save(os.path.join(PREVIEW, f"_sheet_{pref.replace('.', '_')}_{pg // 6}.png"))
    full = {}
    rp = os.path.join(PREVIEW, "report.json")
    if os.path.exists(rp) and a.names:
        with open(rp, encoding="utf-8") as fh:
            full = json.load(fh)
    full.update(report)
    with open(rp, "w", encoding="utf-8") as fh:
        json.dump(full, fh, indent=1)
    bad = {k: v for k, v in report.items() if v["flags"]}
    lines = ["| sound | s | lufs | tp | loop join (hf ratio, level dB, onset dB, note) | flags |", "|---|---|---|---|---|---|"]
    for n in names:
        if n not in report:
            continue
        v = report[n]
        rec = man[n]
        j = (f"{v.get('join_hf_ratio')}, {v.get('join_level_diff_db')}, {v.get('join_onset_db')}, {v.get('join_note')}" if rec["loop"] else "")
        lines.append(f"| {n} | {rec['seconds']:.2f} | {v['lufs']} | {v['true_peak_db']} | {j} | {'; '.join(v['flags'])} |")
    with open(os.path.join(PREVIEW, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n{len(report)} analysed, {len(bad)} with flags")


if __name__ == "__main__":
    main()
