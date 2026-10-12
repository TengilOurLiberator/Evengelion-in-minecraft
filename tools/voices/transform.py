"""Raw recordings -> finished character voices.

    python transform.py                        # every raw line of every character that is out of date
    python transform.py --speaker GENDO,REI    # just these
    python transform.py --ids 2.01,5.04        # just these lines
    python transform.py --force                # redo everything (after editing config.py)
    python transform.py --method dsp           # plain DSP chain instead of voice conversion
    python transform.py --make-refs            # (re)build the synthetic voice-conversion targets and stop

Reads   D:\\angel-attack\\voices\\raw\\<SPEAKER>\\<id>.wav          (from cut_takes.py)
Writes  D:\\angel-attack\\voices\\final\\<SPEAKER>\\<id>.wav        (mono, 48 kHz, 24 bit)
All the numbers live in config.py.

Voice-conversion targets (voices\\refs) are SYNTHETIC: Chatterbox's own built-in voice speaks a few sentences,
DSP (Rubber Band pitch + formant shift) turns that into a differently pitched/sized speaker, and Chatterbox
re-speaks a character-specific passage in that shaped voice so the target is a clean, natural-sounding
speech sample.  No recording of any real person other than the user is used anywhere.
"""
import argparse
import json
import os
import re
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import common
import config
import dsp
import fx
from common import SR, f0_stats, lufs, peak_db

BASE_TEXT = ("The morning briefing will begin shortly. Please check the status of the main systems and report any "
             "irregularities. We have very little time, so I would like everyone to listen carefully to what comes next.")


# ====================================================================================== VC engine
class Engine:
    """Chatterbox voice conversion, loaded on first use, with one synthetic target per character."""

    def __init__(self):
        self.vc = None
        self.refs = {}

    def _load(self):
        if self.vc is None:
            import logging
            logging.getLogger("chatterbox").setLevel(logging.ERROR)
            import warnings
            warnings.filterwarnings("ignore")
            import chatterbox.models.s3gen.flow_matching as fm
            fm.print = lambda *a, **k: None
            import torch
            from chatterbox.vc import ChatterboxVC
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            self.torch = torch
            self.vc = ChatterboxVC.from_pretrained(dev)
            self.dev = dev

    def _ref(self, speaker):
        if speaker not in self.refs:
            p = ref_path(speaker)
            if not os.path.exists(p):
                print(f"[refs] {p} missing - building the synthetic targets first")
                make_refs([s for s in common.HUMANS if not os.path.exists(ref_path(s))])
            self._load()
            w = common.read_audio(p, 24000)[:240000]
            with self.torch.inference_mode():
                self.refs[speaker] = self.vc.s3gen.embed_ref(w, 24000, device=self.dev)
        return self.refs[speaker]

    def convert(self, x, speaker, seed=0):
        """x: float32 mono 48 kHz -> float32 mono 48 kHz in the speaker's synthetic voice (same timing)."""
        ref = self._ref(speaker)
        torch = self.torch
        torch.manual_seed(seed)
        if len(x) > 28 * SR:
            print("  warning: line longer than 28 s, voice conversion may truncate it")
        with torch.inference_mode():
            a16 = torch.from_numpy(common.resample(x, SR, 16000)).float().to(self.dev)[None]
            tokens, _ = self.vc.s3gen.tokenizer(a16)
            wav, _ = self.vc.s3gen.inference(speech_tokens=tokens, ref_dict=ref)
            wav = wav.squeeze(0).detach().cpu().numpy()
            wav = self.vc.watermarker.apply_watermark(wav, sample_rate=self.vc.sr)    # Chatterbox's own inaudible mark
        return common.resample(np.asarray(wav, np.float32).reshape(-1), self.vc.sr, SR)


def ref_path(speaker):
    return os.path.join(common.REFS_DIR, f"{speaker}.wav")


def make_refs(speakers=None, recast=True):
    """Build the synthetic targets.  See the module docstring for exactly how."""
    import logging
    logging.getLogger("chatterbox").setLevel(logging.ERROR)
    import warnings
    warnings.filterwarnings("ignore")
    import chatterbox.models.s3gen.flow_matching as fm
    fm.print = lambda *a, **k: None
    import torch
    from chatterbox.tts import ChatterboxTTS
    speakers = speakers or common.HUMANS
    os.makedirs(common.REFS_DIR, exist_ok=True)
    tts = ChatterboxTTS.from_pretrained("cuda" if torch.cuda.is_available() else "cpu")
    # Two built-in Chatterbox voices give two genuinely different starting points (a lower and a higher speaker).
    bases = {}
    base_files = {"v1": os.path.join(common.REFS_DIR, "_default_voice.wav"),
                  "turbo": os.path.join(common.REFS_DIR, "_default_voice_turbo.wav")}
    need = {config.CHARACTERS[s]["vc_ref"].get("base", "v1") for s in speakers if config.CHARACTERS[s].get("vc_ref")}
    if "v1" in need and not os.path.exists(base_files["v1"]):
        torch.manual_seed(1234)
        w = tts.generate(BASE_TEXT, exaggeration=0.4, cfg_weight=0.4, temperature=0.7).squeeze().cpu().numpy()
        common.write_wav(base_files["v1"], common.resample(w, tts.sr, SR))
    if "turbo" in need and not os.path.exists(base_files["turbo"]):
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        turbo = ChatterboxTurboTTS.from_pretrained("cuda" if torch.cuda.is_available() else "cpu")
        torch.manual_seed(5)
        w = turbo.generate(BASE_TEXT, temperature=0.7).squeeze().cpu().numpy()
        common.write_wav(base_files["turbo"], common.resample(w, turbo.sr, SR))
        del turbo
    for k in need:
        bases[k] = common.read_audio(base_files[k])
        print(f"[refs] built-in Chatterbox voice '{k}': median F0 {f0_stats(bases[k])['median']:.0f} Hz")
    for sp in speakers:
        r = config.CHARACTERS[sp].get("vc_ref")
        if not r:
            continue
        base = bases[r.get("base", "v1")]
        shaped = common.formant_shift_only(common.rubberband(base, pitch=r["pitch"], formant="preserved"), r["formant"])
        if r.get("colour"):                               # push the timbre further from the other characters
            shaped = colour(shaped, r["colour"])
        sp_p = os.path.join(common.REFS_DIR, f"_shaped_{sp}.wav")
        common.write_wav(sp_p, shaped)
        final = shaped
        if recast and r.get("recast", True):
            torch.manual_seed(1234 + zlib.crc32(sp.encode()) % 1000)
            tts.prepare_conditionals(sp_p, exaggeration=r["exaggeration"])
            w = tts.generate(r["text"], exaggeration=r["exaggeration"], cfg_weight=r["cfg"], temperature=0.7)
            final = common.resample(w.squeeze().cpu().numpy(), tts.sr, SR)
        final = final / max(1e-6, float(np.abs(final).max())) * 0.8
        common.write_wav(ref_path(sp), final)
        s = f0_stats(final)
        print(f"[refs] {sp:8} target {ref_path(sp)}  {len(final) / SR:4.1f}s  median F0 {s['median']:.0f} Hz")
    del tts


# ====================================================================================== stages
def cleanup(x):
    c = config.CLEANUP
    g = []
    if c.get("highpass_hz"):
        g.append(f"highpass=f={c['highpass_hz']}")
    if c.get("denoise_db"):
        g.append(f"afftdn=nr={c['denoise_db']}:nf={c.get('noise_floor_db', -50)}:tn=1")
    y = common.ffmpeg_filter(x, ",".join(g), SR) if g else x
    y = y - float(np.mean(y))
    return y.astype(np.float32)


def level_to(x, target_lufs):
    return (x * 10 ** ((target_lufs - lufs(x)) / 20)).astype(np.float32)


def shape_pitch(y, cfg, method, info):
    """Median F0 to cfg['f0'] (softened by pitch_lock), vocal tract by formant, movement by inflection."""
    formant = cfg["formant"] if method.startswith("vc") else cfg["dsp_formant"]
    infl = cfg["inflection"]
    if len(y) < int(0.4 * SR):
        info["note"] = "too short for pitch work"
        return common.formant_shift_only(y, formant) if abs(formant - 1) > 0.01 else y
    st = f0_stats(y)
    info["f0_pre"] = st["median"]
    if st["voiced_s"] < 0.15:
        info["note"] = "no voiced speech (breath/noise): pitch left alone"
        return y
    ratio = (cfg["f0"] / st["median"]) ** cfg.get("pitch_lock", 0.85)
    ratio = float(np.clip(ratio, 0.4, 2.8))
    ps = float(np.clip(ratio, 1 / 1.22, 1.22))        # PSOLA handles the fine part, Rubber Band the big move
    rb = ratio / ps
    if abs(rb - 1) > 0.01:
        y = common.rubberband(y, pitch=rb, formant="preserved")
    return dsp.psola_contour(y, inflection=infl, formant=formant, pitch=ps)


def machine(y, cfg):
    m = cfg["machine"]
    y = dsp.bandlimit(y, m["lo_hz"], m["hi_hz"], SR, 4)
    delay = 1000.0 / cfg["f0"] if m["comb_ms"] == "auto" else m["comb_ms"]
    y = dsp.comb(y, delay, m["comb_gain"], SR)
    y = dsp.ring(y, m["ring_hz"], m["ring_depth"], SR)
    if m.get("crush_bits"):
        q = 2 ** (m["crush_bits"] - 1)
        y = (np.round(y * q) / q).astype(np.float32)
    return y


def colour(y, cfg):
    if cfg.get("eq"):
        y = common.ffmpeg_filter(y, cfg["eq"], SR)
    if cfg.get("comp"):
        y = common.ffmpeg_filter(y, cfg["comp"], SR)
    if cfg.get("saturate"):
        y = dsp.saturate(y, **cfg["saturate"])
    if cfg.get("breath_db") is not None:
        y = dsp.breath(y, SR, level_db=cfg["breath_db"])
    return y


def directions(speaker, direction):
    names = fx.effects_for(direction, config.DIRECTION_RULES)
    if not names and speaker == "BASE":
        d = config.CHARACTERS["BASE"].get("default_fx")
        names = [d] if d else []
    return names


def finish(y, cfg, tail_extra=0.0):
    """Common loudness target, ceiling, trimmed lead and tail."""
    y = common.trim_silence(y, SR, thresh_db=-52, lead=config.LEAD_S, tail=config.TAIL_S + tail_extra, fade=0.01)
    y = y * 10 ** ((config.TARGET_LUFS + cfg.get("gain_db", 0.0) - lufs(y)) / 20)
    ceiling = 10 ** (config.PEAK_CEILING_DB / 20)
    if np.abs(y).max() > ceiling:
        y = common.ffmpeg_filter(y, f"alimiter=limit={ceiling:.4f}:attack=2:release=30:level=disabled", SR)
        if np.abs(y).max() > ceiling:
            y = y * ceiling / np.abs(y).max()
    return y.astype(np.float32)


def render(speaker, x, direction="", method=None, engine=None, seed=0, nonverbal=False, force_fx=None):
    """One raw line -> one finished line.  Returns (audio, info)."""
    cfg = config.CHARACTERS[speaker]
    method = method or cfg.get("method", config.DEFAULT_METHOD)
    if speaker == "BASE":
        method = "dsp"
    info = {"method": method, "f0_in": f0_stats(x)["median"] if len(x) > 0.4 * SR else 0.0}
    y = cleanup(x)
    if method.startswith("vc") and not nonverbal:
        y = level_to(y, -23.0)
        y = (engine or Engine()).convert(y, speaker, seed)
    if not nonverbal:
        y = shape_pitch(y, cfg, method, info)
    if abs(cfg.get("tempo", 1.0) - 1) > 0.005:
        y = common.rubberband(y, tempo=cfg["tempo"], formant="preserved")
    if speaker == "BASE":
        y = machine(y, cfg)
    y = colour(y, cfg)
    names = [force_fx] if force_fx else directions(speaker, direction)
    names = [n for n in names if n and n != "none"]
    for name in names:
        y = fx.apply(y, name, config.FX[name], SR)
    info["fx"] = names
    y = finish(y, cfg, tail_extra=0.6 if any(n in ("pa", "street", "above") for n in names) else 0.0)
    info.update(dur=len(y) / SR, lufs=lufs(y), peak=peak_db(y))
    if len(y) > 0.4 * SR and not nonverbal:
        info["f0_out"] = f0_stats(y)["median"]
    return y, info


# ====================================================================================== batch
def script_index():
    import script_lines
    if not os.path.exists(common.SCRIPT_MD):
        return {}
    return {l["id"]: l for l in script_lines.parse(common.SCRIPT_MD)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--speaker", help="comma list, default all")
    ap.add_argument("--ids", help="comma list of line ids")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--method", choices=["vc+dsp", "dsp"])
    ap.add_argument("--allow-humans", action="store_true", help="also write the four human voices into voices\\final from the user's raw recordings (they are TTS now: see tts_lines.py)")
    ap.add_argument("--make-refs", action="store_true")
    ap.add_argument("--no-recast", action="store_true", help="with --make-refs: use the DSP-shaped voice directly")
    ap.add_argument("--raw", default=common.RAW_DIR)
    ap.add_argument("--out", default=common.FINAL_DIR)
    ap.add_argument("--script", help="script.md to read directions from (default D:\\angel-attack\\script.md)")
    a = ap.parse_args()
    speakers = [s.strip().upper() for s in a.speaker.split(",")] if a.speaker else common.SPEAKERS
    if os.path.normcase(os.path.abspath(a.out)) == os.path.normcase(os.path.abspath(common.FINAL_DIR)) and not a.make_refs and not a.allow_humans:
        # The four human voices are TTS now (tts_lines.py install writes voices\final\<SPEAKER>); rebuilding them from the user's raw recordings
        # would put the recorded voices back into the pack.
        if a.speaker and any(s in common.HUMANS for s in speakers):
            sys.exit("MISATO, RITSUKO, GENDO and REI are TTS voices now (tools\\voices\\tts_lines.py). transform.py into voices\\final would replace them with "
                     "the user's converted recordings; pass --allow-humans if that is really what you want, or --out another folder.")
        if not a.speaker:
            speakers = ["BASE"]
            print("(only BASE is transformed: the four human voices are made by tts_lines.py; --allow-humans to include them)")
    if a.make_refs:
        make_refs([s for s in speakers if s in common.HUMANS], recast=not a.no_recast)
        return
    if a.script:
        common.SCRIPT_MD = a.script
    idx = script_index()
    want = set(a.ids.split(",")) if a.ids else None
    cfg_time = max(os.path.getmtime(os.path.join(os.path.dirname(__file__), f)) for f in ("config.py", "transform.py", "dsp.py", "fx.py"))
    eng = Engine()
    done = 0
    for sp in speakers:
        src = os.path.join(a.raw, sp)
        if not os.path.isdir(src):
            continue
        files = sorted(f for f in os.listdir(src) if f.endswith(".wav") and not f.startswith("_"))
        stats_p = os.path.join(a.out, sp, "_stats.json")
        stats = json.load(open(stats_p)) if os.path.exists(stats_p) else {}
        for f in files:
            lid = f[:-4]
            if want and lid not in want:
                continue
            dst = os.path.join(a.out, sp, f)
            if not a.force and not want and os.path.exists(dst) and os.path.getmtime(dst) > max(os.path.getmtime(os.path.join(src, f)), cfg_time):
                continue
            rec = idx.get(lid, {})
            t0 = time.time()
            x = common.read_audio(os.path.join(src, f))
            y, info = render(sp, x, rec.get("direction", ""), a.method, eng, seed=zlib.crc32(lid.encode()),
                             nonverbal=bool(rec.get("nonverbal")))
            common.write_wav(dst, y)
            stats[lid] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in info.items()}
            done += 1
            print(f"{sp:8} {lid:6} {info['dur']:5.1f}s  F0 {info['f0_in']:4.0f} -> {info.get('f0_out', 0):4.0f} Hz  "
                  f"{info['lufs']:5.1f} LUFS  peak {info['peak']:5.1f}  fx {'+'.join(info['fx']) or '-'}  ({time.time() - t0:.1f}s)")
        if files:
            os.makedirs(os.path.join(a.out, sp), exist_ok=True)
            json.dump(stats, open(stats_p, "w"), indent=1)
    print(f"{done} lines transformed")


if __name__ == "__main__":
    main()
