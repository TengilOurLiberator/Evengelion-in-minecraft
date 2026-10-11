"""finish.py - turn raw generations into candidates that satisfy the contract of the procedural file they would replace.

    python finish.py                       # every event that has raw files
    python finish.py music.fight sfx.      # these (names or prefixes)

For each event and candidate k it writes work/sound_candidates/<event>/cand<k>.ogg (+ cand<k>.json: the contract check, the profile,
what was done).  The contract is read from the procedural file (audio_utils.ref_path): channel layout, exact sample count,
integrated LUFS; and from tools/sound/manifest.json: whether it loops.  Nothing here touches the pack.

Per recipe
  oneshot        trim leading silence (onset within 30 ms), cut the event's exact length, fades, gain to the reference LUFS with the
                 project's look-ahead limiter keeping true peak < -1.3 dBTP before Vorbis (decoded value verified)
  bed            loop of exactly the reference length: n pieces (each from its own clip) equal-power crossfaded into each other and the
                 last into the first, so sample L-1 runs on into sample 0
  music_loop     pulse=false: best-matching start, tail continuation crossfaded into the head (xf seconds)
                 pulse=true : measure the tempo, time-stretch (Rubber Band) so the loop is a whole number of bars, start on a downbeat,
                 crossfade on the beat grid (xf_beats beats), then check that the continuation lines up with the head
  music_long_loop / music_launch   a long file plus its loop file with one shared gain so the hand-off has no level step
  music_oneshot  fixed length, fades, level
"""
import argparse
import json
import os
import sys

import numpy as np
import scipy.signal as sg
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio_utils as au
from audio_utils import SR, N
from gen import variant_cfg, n_candidates

RAW = os.path.join(au.CAND, "raw")
Q = {"amb": 4, "music": 5, "sfx": 6}
MANIFEST = os.path.join(au.SOUND_DIR, "manifest.json")
LUFS_TOL = 0.5
TICK = 2205                      # samples per game tick at 44.1 kHz


def prompts():
    return json.load(open(os.path.join(HERE, "prompts.json"), encoding="utf-8"))


def manifest():
    return json.load(open(MANIFEST, encoding="utf-8"))


def contract(event):
    ref = au.read_pack(au.ref_path(event))
    m = manifest().get(event, {})
    return dict(channels=1 if ref.ndim == 1 else ref.shape[1], samples=len(ref), lufs=au.lufs(ref), loop=bool(m.get("loop")),
                ref_tp=au.tp(ref), kind=event.split(".")[0], q=Q[event.split(".")[0]])


# ----------------------------------------------------------------------------------------------- loop helpers
def band_profile(seg):
    """log energy in third-octave bands 60 Hz - 12 kHz of a stereo/mono segment"""
    m = au.mono(seg)
    w = np.hanning(len(m))
    S = np.abs(np.fft.rfft(m * w)) ** 2
    f = np.fft.rfftfreq(len(m), 1 / SR)
    edges = 60 * 2 ** (np.arange(0, 22) / 3.0)
    edges = edges[edges < 12000]
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        out.append(10 * np.log10(S[(f >= lo) & (f < hi)].sum() + 1e-12))
    return np.array(out)


def join_cost(x, s, L, xf):
    a = x[s:s + xf]
    b = x[s + L:s + L + xf]
    return float(np.mean(np.abs(band_profile(a) - band_profile(b))))


def best_start(x, L, xf, lo, hi, step, grid=None):
    """start sample in [lo, hi] (every `step` samples, or on `grid`) whose head and continuation resemble each other most"""
    cands = grid if grid is not None else range(lo, hi, step)
    cands = [c for c in cands if lo <= c <= hi and c + L + xf <= len(x)]
    if not cands:
        return None, None
    costs = [join_cost(x, c, L, xf) for c in cands]
    i = int(np.argmin(costs))
    return int(cands[i]), costs[i]


def measure_lag(env, fs, s, L, win):
    """how many seconds later than env[s:s+win] the music repeats itself at s+L (onset-envelope cross-correlation, +-0.2 s)"""
    i0, i1 = int(s * fs), int((s + win) * fs)
    j0 = int((s + L) * fs)
    a = env[i0:i1]
    b = env[j0:j0 + (i1 - i0)]
    n = min(len(a), len(b))
    if n < int(2 * fs):
        return None
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    maxlag = int(0.2 * fs)
    cc = sg.correlate(b, a, mode="full")
    mid = n - 1
    seg = cc[mid - maxlag:mid + maxlag + 1]
    k = int(np.argmax(seg)) - maxlag
    # parabolic refinement
    kk = k + maxlag
    if 0 < kk < len(seg) - 1:
        y0, y1, y2 = seg[kk - 1], seg[kk], seg[kk + 1]
        den = y0 - 2 * y1 + y2
        if abs(den) > 1e-12:
            k = k + 0.5 * (y0 - y2) / den
    return k / fs


def align_pulse(x, design_bpm, L, log):
    """stretch x so a cycle of L samples is a whole number of bars at a steady tempo.  returns (x, bpm, phase_s, period_s, ok)"""
    Ls = L / SR
    nb = max(4, int(round(Ls * design_bpm / 60.0 / 4)) * 4)
    target = nb * 60.0 / Ls
    env, fs = au.onset_env(x)
    best = None
    for mult in (1.0, 2.0, 0.5):                          # tempo might be found at half or double
        bpm0, ph0, st0 = au.tempo_fit(env, fs, design_bpm * mult, rel=0.10, step=0.02)
        if best is None or st0 > best[2] * 1.15:
            best = (bpm0, ph0, st0, mult)
    bpm0, ph0, st0, mult = best
    log["tempo_first_fit"] = dict(bpm=round(bpm0, 2), strength=round(st0, 3), octave=mult)
    if mult != 1.0:                                       # the music runs at half/double the design: grid by the design tempo's multiple
        target_b = target * mult
    else:
        target_b = target
    ratio = target_b / bpm0
    log["stretch_ratio"] = round(ratio, 4)
    if abs(ratio - 1.0) > 0.07:
        log["aligned"] = False
        return x, bpm0, ph0, 60.0 / bpm0, False
    x = au.stretch(x, ratio)
    for it in range(3):                                    # measure the repeat distance at L and correct the remaining drift
        env, fs = au.onset_env(x)
        s0 = 4.0
        win = min(8.0, len(x) / SR - s0 - Ls - 0.5)
        lag = measure_lag(env, fs, s0, Ls, win) if win >= 3.0 else None
        log.setdefault("lag_ms", []).append(None if lag is None else round(lag * 1000, 1))
        if lag is None or abs(lag) < 0.004:
            break
        x = au.stretch(x, (Ls + lag) / Ls)
    env, fs = au.onset_env(x)
    f = target_b / 60.0
    t = np.arange(len(env)) / fs
    z = np.sum(env * np.exp(-2j * np.pi * f * t))
    phase = (np.angle(z) / (2 * np.pi * f)) % (1.0 / f)
    log["aligned"] = True
    return x, target_b, phase, 60.0 / target_b, True


def pulse_loop(x, e, L, log, want_downbeat=False):
    """tempo-aligned loop of exactly L samples from stereo x"""
    xf_beats = e["xf_beats"]
    x2, bpm, phase, period, ok = align_pulse(x, e["bpm"], L, log)
    if not ok:                                              # fall back: free crossfade of 2 beats at the designed tempo
        xf = N(xf_beats * 60.0 / e["bpm"])
        s, c = best_start(x2, L, xf, N(3.0), len(x2) - L - xf - N(0.5), N(0.25))
        log["fallback"] = "tempo not found within 7%: unaligned crossfade"
        return circular_pick(x2, s, L, xf), s, x2
    xf = N(xf_beats * period)
    env_low, fs = au.onset_env(x2, band=(30, 160))
    d_idx, dist = au.downbeat_index(env_low, fs, bpm, phase, 4)
    log["downbeat_beat_of_4"] = d_idx
    log["bar_accent_distribution"] = [round(float(v), 2) for v in dist]
    first = phase + d_idx * period
    bar = 4 * period
    grid = [int(round((first + k * bar) * SR)) for k in range(0, int((len(x2) / SR - first) / bar))]
    lo, hi = N(4.0), len(x2) - L - xf - N(0.3)
    s, c = best_start(x2, L, xf, lo, hi, 1, grid=grid)
    if s is None:
        s, c = best_start(x2, L, xf, N(1.0), len(x2) - L - xf - 1, N(0.25))
        log["fallback"] = "no bar start in range"
    if not want_downbeat:
        s += N(0.03)       # like the procedural loops: no hit sits exactly on the join (the launch drive keeps its kick on sample 0)
    log["start_s"] = round(s / SR, 3)
    log["join_cost"] = round(c, 2)
    return circular_pick(x2, s, L, xf), s, x2


def circular_pick(x, s, L, xf):
    return au.circular_xfade(x, s, L, xf)


# ----------------------------------------------------------------------------------------------- checks on the decoded file
def join_ratio(y):
    hpf = sg.butter(4, 2000.0 / (SR / 2), "high", output="sos")
    mm = au.mono(y)
    k = 8192
    seg = np.concatenate([mm[-k:], mm[:k]])
    hs = np.abs(sg.sosfiltfilt(hpf, seg))
    ref = max(float(np.percentile(np.abs(sg.sosfilt(hpf, mm)), 99.9)), 10 ** (-80 / 20))
    return float(hs[k - N(0.0005):k + N(0.0005)].max() / ref)


def check(event, y, c, loop, recipe_note=""):
    """contract verdict on a decoded candidate; hard failures in 'fail', softer ones in 'warn'"""
    fail, warn = [], []
    r = {}
    ch = 1 if y.ndim == 1 else y.shape[1]
    r["channels"] = ch
    if ch != c["channels"]:
        fail.append(f"channels {ch} != {c['channels']}")
    r["samples"] = len(y)
    if len(y) != c["samples"]:
        fail.append(f"samples {len(y)} != {c['samples']}")
    r["lufs"] = round(au.lufs(y), 2)
    r["lufs_ref"] = round(c["lufs"], 2)
    if abs(r["lufs"] - c["lufs"]) > LUFS_TOL:
        fail.append(f"lufs {r['lufs']} vs {c['lufs']:.2f}")
    r["tp"] = round(au.tp(y), 2)
    if r["tp"] > -1.0:
        fail.append(f"true peak {r['tp']}")
    r["dc"] = round(float(np.max(np.abs(np.mean(y, axis=0)))), 5)
    if r["dc"] > 0.003:
        fail.append(f"dc {r['dc']}")
    r["clipped"] = int(np.sum(np.abs(y) >= 0.999))
    if r["clipped"]:
        fail.append("clipping")
    m = au.mono(y)
    nz = np.where(np.abs(m) > 10 ** (-60 / 20))[0]
    if len(nz) == 0:
        fail.append("silent")
        return r, fail, warn
    r["lead_silence_s"] = round(nz[0] / SR, 3)
    r["tail_silence_s"] = round((len(m) - 1 - nz[-1]) / SR, 3)
    if loop:
        r["join_hf_ratio"] = round(join_ratio(y), 2)
        yy0 = y if y.ndim == 2 else y[:, None]
        e20 = N(0.02)
        r["join_onset_db"] = round(float(10 * np.log10(np.mean(yy0[:e20] ** 2) + 1e-14) - 10 * np.log10(np.mean(yy0[-e20:] ** 2) + 1e-14)), 1)
        # same rule as analyze.py: a downbeat/onset at the join is by design (the waveform itself is continuous: the tail's natural
        # continuation was crossfaded into the head); anything else above 1.3 is a click
        if r["join_hf_ratio"] > 1.3:
            if r["join_onset_db"] > 12.0:
                warn.append(f"hit on the join (hf ratio {r['join_hf_ratio']}, onset +{r['join_onset_db']} dB)")
            else:
                fail.append(f"loop join click {r['join_hf_ratio']}")
        if len(y) % TICK:
            fail.append("loop not a whole number of ticks")
        w = N(0.1)
        yy = y if y.ndim == 2 else y[:, None]
        a_ = 10 * np.log10(np.mean(yy[-w:] ** 2) + 1e-14)
        b_ = 10 * np.log10(np.mean(yy[:w] ** 2) + 1e-14)
        r["join_level_diff_db"] = round(float(a_ - b_), 2)
        if abs(r["join_level_diff_db"]) > 6.0:
            warn.append(f"join level step {r['join_level_diff_db']} dB")
    else:
        if r["lead_silence_s"] > 0.03:
            fail.append(f"leading silence {r['lead_silence_s']} s")
        handoff = event in ("music.decision", "music.launch")        # these run on into their loop file: the end is not faded
        lim = max(0.002, 0.01 * float(np.abs(m).max()))        # Vorbis can ring a little into the first/last samples of a hard hit
        if abs(m[0]) > lim or (abs(m[-1]) > lim and not handoff):
            fail.append("no fade at an end")
    return r, fail, warn


def finalize(event, x, c, log, fin=0.0, fout=0.0, loop=False, tp_ceil=-1.3):
    """level to the reference LUFS, limiter, fades; returns float signal ready to encode"""
    ch = c["channels"]
    x = au.channels(x, ch)
    if loop:
        x = x - x.mean(axis=0)
    else:
        x = au.dc_hp(x)
        x = au.fade(x, fin, 0.0, "lin")           # linear in: the signal passes -60 dBFS within a few ms even for a slow swell
        x = au.fade(x, 0.0, fout, "cos")
    y, lv = au.set_level(x, c["lufs"], ceil=tp_ceil)
    log["level"] = lv
    return y


def write_candidate(event, k, y, c, log, loop):
    folder = os.path.join(au.CAND, event)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"cand{k}.ogg")
    dec, info = au.encode_checked(y, path, c["q"])
    # the Vorbis round trip can move loudness a little; fix once if the decoded value is outside the tolerance
    if abs(info["lufs"] - c["lufs"]) > 0.25:
        y2 = y * au.db(c["lufs"] - info["lufs"])
        if au.tp(y2) < -1.2:
            dec, info = au.encode_checked(y2, path, c["q"])
            log["relevel_after_encode_db"] = round(c["lufs"] - info["lufs"], 2)
    r, fail, warn = check(event, dec, c, loop)
    prof = au.profile(dec, tempo_hint=log.get("tempo_hint"), scan=event.startswith("music."))
    rec = dict(event=event, candidate=k, file=os.path.relpath(path, au.ROOT), contract=r, fail=fail, warn=warn, profile=prof, log=log,
               encoded=info)
    json.dump(rec, open(os.path.join(folder, f"cand{k}.json"), "w"), indent=1, default=float)
    print(f"{event:24s} cand{k}  {r['lufs']:6.1f} LUFS (ref {r['lufs_ref']:.1f})  tp {r['tp']:5.1f}  "
          f"{'FAIL: ' + '; '.join(fail) if fail else 'ok'}{'  warn: ' + '; '.join(warn) if warn else ''}", flush=True)
    return dec


# ----------------------------------------------------------------------------------------------- recipes
def rawfile(event, part, k, piece=0):
    return os.path.join(RAW, event, f"{part}_k{k}_p{piece}.flac")


def do_oneshot(event, e, k, c, loop):
    log = {"recipe": "oneshot"}
    x = au.channels(au.load(rawfile(event, "main", k)), c["channels"])
    x = au.hp_zero(au.dc_hp(x), e.get("hp", 25.0))
    on = au.onset_index(x, floor_db=-60.0, rel_db=e.get("onset_rel_db", -30), back_db=-24.0)
    start = max(0, on - N(0.004))
    log["onset_s"] = round(on / SR, 3)
    for attempt in range(3):
        seg = x[start:start + c["samples"]]
        if len(seg) < c["samples"]:
            pad = c["samples"] - len(seg)
            seg = np.concatenate([seg, np.zeros((pad,) + seg.shape[1:])])
            log["padded_s"] = round(pad / SR, 2)
        # a short fade-in only: the onset is already trimmed, and the contract says the sound is audible within 30 ms
        y = finalize(event, seg, c, log, fin=min(e.get("fin", 0.004), 0.008), fout=e.get("fout", 1.0))
        nz = np.where(np.abs(au.mono(y)) > 10 ** (-60 / 20))[0]
        lead = nz[0] if len(nz) else 0
        if lead <= N(0.02):
            break
        start += lead - N(0.004)                  # the first samples are below -60 dBFS at the final level: slide the window on
        log["slid_for_lead_s"] = round((start - max(0, on - N(0.004))) / SR, 3)
    return [(event, y, log, False)]


def do_bed(event, e, k, c, loop):
    log = {"recipe": "bed", "pieces": e["pieces"], "xf": e["xf"]}
    clips = []
    for i in range(e["pieces"]):
        x = au.channels(au.load(rawfile(event, "main", k, i)), c["channels"])
        x = au.hp_zero(x - x.mean(axis=0), e.get("hp", 30.0))
        clips.append(x)
    if len(clips) > 1:
        clips = au.match_clips(clips)
        log["matched_pieces"] = True
    y = au.pieced_loop(clips, c["samples"], N(e["xf"]), skip=1.0)
    y = finalize(event, y, c, log, loop=True)
    return [(event, y, log, True)]


def do_music_loop(event, e, k, c, loop):
    log = {"recipe": "music_loop", "pulse": e["pulse"]}
    x = au.load(rawfile(event, "main", k))
    x = x - x.mean(axis=0)
    L = c["samples"]
    if e["pulse"]:
        log["tempo_hint"] = e["bpm"]
        y, s, x2 = pulse_loop(x, e, L, log)
    else:
        xf = N(e["xf"])
        s, cost = best_start(x, L, xf, N(2.0), len(x) - L - xf - N(0.5), N(0.25))
        log["start_s"] = round(s / SR, 2)
        log["join_cost"] = round(cost, 2)
        y = au.circular_xfade(x, s, L, xf)
    y = finalize(event, y, c, log, loop=True)
    return [(event, y, log, True)]


def level_pair(long_x, loop_x, tail_len, c_long, c_loop, log, early_ramp):
    """shared gain for a long file and its loop: the loop's tail section gets the same gain in both so the hand-off has no step.
    The early part of the long file is boosted/cut (smooth ramp over `early_ramp` samples) only if its own LUFS would be off."""
    g = c_loop["lufs"] - au.lufs(loop_x)
    boost = 0.0
    for _ in range(12):
        env = np.ones(len(long_x))
        n = min(early_ramp, len(long_x))
        env[:n] = au.db(boost) * (1 - 0.5 * (1 - np.cos(np.pi * np.arange(n) / n))) + 0.5 * (1 - np.cos(np.pi * np.arange(n) / n))
        yl = long_x * au.db(g) * (env[:, None] if long_x.ndim == 2 else env)
        err = c_long["lufs"] - au.lufs(yl)
        if abs(err) < 0.15 or abs(boost) > 8:
            break
        boost += err
    log["shared_gain_db"] = round(g, 2)
    log["early_boost_db"] = round(boost, 2)
    return yl, loop_x * au.db(g)


def limit_pair(a, b, ceil=-1.3):
    out = []
    for y in (a, b):
        t = au.tp(y)
        if t > ceil:
            y = au.dsp.limit(y, ceil - 0.2)
            y = y * au.db(min(0.0, ceil - au.tp(y)))
        out.append(y)
    return out


def do_music_long_loop(event, e, k, c, loop):
    outs = e["outputs"]
    c_long, c_loop = contract(outs[0]), contract(outs[1])
    log = {"recipe": "music_long_loop"}
    x = au.load(rawfile(event, "main", k))
    x = x - x.mean(axis=0)
    Lloop, T = c_loop["samples"], c_long["samples"]
    # tempo alignment of the whole generation so the final L is a whole number of beats
    log["tempo_hint"] = e["bpm"]
    ee = dict(e, xf_beats=e["xf_beats"])
    nb = int(round(Lloop / SR * e["bpm"] / 60.0))
    x2, bpm, phase, period, ok = align_pulse(x, e["bpm"], Lloop, log)
    xf = N(e["xf_beats"] * period) if ok else N(e["xf_beats"] * 60.0 / e["bpm"])
    on = au.onset_index(x2, floor_db=-55.0, rel_db=-50.0)         # no dead air in front of the cue
    x2 = x2[max(0, on - N(0.004)):]
    log["trimmed_lead_s"] = round(on / SR, 2)
    for attempt in range(4):
        if len(x2) < T + xf + N(0.1):
            raise RuntimeError("generation too short after stretch")
        long_x = x2[:T].copy()
        loop_y = au.circular_xfade(x2, T - Lloop, Lloop, xf)         # head = x[T-L : ...] blended with the continuation x[T : T+xf]
        log["hand_off"] = "loop sample 0 is the continuation of the long file's last sample"
        yl, yp = level_pair(long_x, loop_y, Lloop, c_long, c_loop, log, early_ramp=int(0.6 * T))
        yl = au.fade(yl, 0.05, 0.0, "lin")
        nz = np.where(np.abs(au.mono(yl)) > 10 ** (-60 / 20))[0]
        lead = nz[0] if len(nz) else 0
        if lead <= N(0.02):
            break
        x2 = x2[lead - N(0.004):]                                    # still quiet at the final level: slide the start on
        log["trimmed_lead_s"] = round(log["trimmed_lead_s"] + (lead - N(0.004)) / SR, 2)
    yl, yp = limit_pair(yl, yp)
    return [(outs[0], yl, dict(log, role="long"), False), (outs[1], yp, dict(log, role="loop"), True)]


def do_music_launch(event, e, k, c, loop):
    outs = e["outputs"]
    c_long, c_loop = contract(outs[0]), contract(outs[1])
    log = {"recipe": "music_launch"}
    Lc = c_loop["samples"]
    build_n = N(20.0)
    # --- the drive cycle, from a downbeat
    xd = au.load(rawfile(event, "drive", k))
    xd = xd - xd.mean(axis=0)
    log["tempo_hint"] = e["bpm"]
    cyc, s, xd2 = pulse_loop(xd, e, Lc, log, want_downbeat=True)
    # --- the build: a 20.000 s window ending at its climax, on the beat if a pulse is audible
    xb = au.load(rawfile(event, "build", k))
    xb = xb - xb.mean(axis=0)
    m = au.mono(xb)
    w = N(0.25)
    en = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, mode="same"))
    lo, hi = N(20.0), len(m) - N(0.4)
    end = lo + int(np.argmax(en[lo:hi]))
    env, fs = au.onset_env(xb)
    bpm_b, ph_b, st_b = au.tempo_fit(env, fs, e["bpm"], rel=0.08, step=0.02)
    log["build"] = dict(climax_s=round(end / SR, 2), bpm=round(bpm_b, 2), strength=round(st_b, 3))
    per = 60.0 / bpm_b
    beats = ph_b + np.arange(int(len(m) / SR / per)) * per
    nearest = beats[np.argmin(np.abs(beats - end / SR))]
    if abs(nearest - end / SR) < 0.2 and st_b > 0.04:
        end = int(round(nearest * SR))
        log["build"]["snapped_to_beat"] = True
    start = end - build_n
    on = au.onset_index(xb, floor_db=-55.0, rel_db=-50.0)
    if start < on - N(0.004):                                      # the window would open on silence: slide it later
        start = on - N(0.004)
        end = start + build_n
        log["build"]["slid_to_onset_s"] = round(on / SR, 2)
    if start < 0 or end > len(xb):
        raise RuntimeError("build too short for 20 s")
    build = xb[start:end].copy()
    build = au.fade(build, 0.25, 0.03, "cos")
    long_x = np.concatenate([build, cyc, cyc])
    assert len(long_x) == c_long["samples"], (len(long_x), c_long["samples"])
    yl, yp = level_pair(long_x, cyc, Lc, c_long, c_loop, log, early_ramp=build_n)
    yl, yp = limit_pair(yl, yp)
    return [(outs[0], yl, dict(log, role="long"), False), (outs[1], yp, dict(log, role="loop"), True)]


def do_music_oneshot(event, e, k, c, loop):
    log = {"recipe": "music_oneshot"}
    x = au.channels(au.load(rawfile(event, "main", k)), c["channels"])
    x = au.dc_hp(x)
    on = au.onset_index(x, floor_db=-55.0, rel_db=-50.0)
    seg = x[max(0, on - N(0.004)):][:c["samples"]]
    log["onset_s"] = round(on / SR, 3)
    if len(seg) < c["samples"]:
        raise RuntimeError("generation shorter than the cue")
    y = finalize(event, seg, c, log, fin=e.get("fin", 0.02), fout=e.get("fout", 1.5))
    return [(event, y, log, False)]


RECIPES = {"oneshot": do_oneshot, "bed": do_bed, "music_loop": do_music_loop, "music_long_loop": do_music_long_loop,
           "music_launch": do_music_launch, "music_oneshot": do_music_oneshot}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--only-k", type=int, nargs="*", help="only these candidate numbers")
    a = ap.parse_args()
    P = prompts()["events"]
    for event, e in P.items():
        if a.names and not any(event == p or event.startswith(p) for p in a.names):
            continue
        for k in range(1, n_candidates(e) + 1):
            if a.only_k and k not in a.only_k:
                continue
            ek = variant_cfg(e, k)
            outs = e.get("outputs", [event])
            c = contract(event if event in outs else outs[0])
            try:
                results = RECIPES[e["recipe"]](event, ek, k, c, c["loop"])
            except (FileNotFoundError, RuntimeError, AssertionError) as ex:
                print(f"{event:24s} cand{k}  SKIPPED: {type(ex).__name__}: {ex}", flush=True)
                continue
            for ev, y, log, loop in results:
                cc = contract(ev)
                write_candidate(ev, k, y, cc, log, loop)


if __name__ == "__main__":
    main()
