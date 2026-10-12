"""Having the next lines ready before the story asks for them.

Every scripted line has a pre-rendered take (voices\\final, the same TTS voice) that can be played at once: that is the verbatim version and the
fallback.  For the lines line_policy.py allows to change, `Preparer.adapt` asks Claude for a re-voiced text (adapter.py), SYNTHESISES it with
the character's voice on a second Chatterbox (so a live reply is never queued behind it), checks the take by transcribing it back, and applies the
effect and loudness of the line's direction (tts_lib.master).  `take(lid)` is what the cue gets: the adapted take if it is ready, else the verbatim one.
Nothing here ever waits for the story, and nothing the story needs ever waits for this.
"""
import itertools
import queue
import threading
import time

import numpy as np

import adapter as adapt_mod
import storybook
from config import CHARACTERS, NAMES


class Prepared:
    def __init__(self, lid, text, wav, kind, **info):
        self.lid, self.text, self.wav, self.kind = lid, text, wav, kind
        self.dur = len(wav) / 48000.0
        self.t_ready = time.time()
        self.info = info

    def __repr__(self):
        return f"<Prepared {self.lid} {self.kind} {self.dur:.1f}s>"


class Preparer:
    def __init__(self, book, synth=None, brain=None, asr_check=True, verbatim_only=False, log=print):
        self.book, self.synth, self.log = book, synth, log
        self.verbatim_only = verbatim_only or brain is None or synth is None
        self.adapter = adapt_mod.Adapter(brain, log) if brain is not None else None
        self.asr_check = asr_check
        self.pause = None                 # callable -> True while a live reply is being synthesised (bridge: VoiceBank.busy)
        self.lock = threading.RLock()
        self.verb = {}                    # lid -> Prepared (the pre-rendered take)
        self.adapted = {}                 # lid -> Prepared (the live version, when it is ready)
        self.requested = set()            # lines whose adaptation was asked for since they were last spoken
        self.records = {}                 # lid -> dict, what happened to the line (for the report)
        self.q = queue.PriorityQueue()
        self.seq = itertools.count()
        self._asr = None
        self._asr_lock = threading.Lock()
        if not self.verbatim_only:
            threading.Thread(target=self._synth_worker, daemon=True).start()
            import tts_lib
            tts_lib.voice_modules()           # import the effect stage now, not at the first line
            if asr_check:
                threading.Thread(target=self._warm_asr, daemon=True).start()      # (Whisper large-v3 takes ~10 s to load: not during the first line)

    # ---- verbatim ---------------------------------------------------------------------------------------------------
    def preload(self, lid):
        """Make sure the pre-rendered take of `lid` is in memory (a few ms). -> Prepared or None when the file does not exist."""
        with self.lock:
            if lid in self.verb:
                return self.verb[lid]
        wav = self.book.verbatim_wav(lid)
        if wav is None:
            return None
        p = Prepared(lid, self.book.lines[lid].text, wav, "verbatim")
        with self.lock:
            self.verb.setdefault(lid, p)
            return self.verb[lid]

    # ---- adaptation ---------------------------------------------------------------------------------------------------
    def wants(self, lid):
        ln = self.book.lines.get(lid)
        return bool(ln) and ln.human and not ln.verbatim and not self.verbatim_only

    def adapt(self, lids, context, later_ids=(), fixed_ids=()):
        """Ask for the adaptable lines among `lids` (one Claude call for the group) in a background thread. Safe to call repeatedly."""
        todo = []
        with self.lock:
            for lid in lids:
                if self.wants(lid) and lid not in self.requested:
                    self.requested.add(lid)
                    todo.append(lid)
                    self.records[lid] = {"id": lid, "script": self.book.lines[lid].text, "status": "asked", "t_asked": time.time(),
                                         "speaker": self.book.lines[lid].speaker}
        if not todo:
            return
        threading.Thread(target=self._adapt_job, args=(todo, context, list(later_ids), list(fixed_ids)), daemon=True).start()

    def _adapt_job(self, lids, context, later_ids, fixed_ids):
        book = self.book
        items = []
        for lid in lids:
            ln = book.lines[lid]
            items.append((ln, "on the radio/telephone" if ln.direction and any(k in ln.direction for k in ("radio", "telephone", "intercom", "handset")) else
                          "from above" if "above" in ln.direction else "in person"))
        ctx = dict(context)
        ctx["fixed_between"] = [book.lines[i] for i in fixed_ids if i in book.lines and i not in lids]
        got, left, secs = self.adapter.adapt(items, ctx, [book.lines[i] for i in later_ids if i in book.lines])
        now = time.time()
        for lid in lids:
            rec = self.records[lid]
            rec["claude_s"] = round(secs, 2)
            rec["t_text"] = now
            if lid in got:
                rec.update(status="text", adapted=got[lid])
                self.q.put((self._prio(lid), next(self.seq), {"lid": lid, "text": got[lid]}))
                self.log(f"   [adapt] {lid}: {got[lid]}   (claude {secs:.1f}s)")
            else:
                rec.update(status="as written", why=left.get(lid, "?"))
                self.log(f"   [adapt] {lid}: as written ({left.get(lid, '?')})")

    def _prio(self, lid):
        return self.book.order.index(lid)

    def _synth_worker(self):
        while True:
            _, _, job = self.q.get()
            waited = 0.0
            while self.pause is not None and self.pause() and waited < 1.0:       # a live reply is being synthesised: it goes first (the GPU is shared)
                time.sleep(0.05)
                waited += 0.05
            try:
                self._synth(job)
            except Exception as e:                                   # never let one line stop the worker
                rec = self.records.get(job["lid"], {})
                rec.update(status="as written", why=f"synthesis failed: {e.__class__.__name__}: {e}")
                self.log(f"   [prepare] {job['lid']}: {e.__class__.__name__}: {e}")

    def _warm_asr(self):
        try:
            import numpy as np
            self._asr_transcribe(np.zeros(16000, dtype=np.float32))
        except Exception as e:
            self.log(f"   [prepare] transcript check unavailable ({e.__class__.__name__}: {e}); adapted lines go unchecked")
            self.asr_check = False

    def _asr_transcribe(self, x):
        with self._asr_lock:
            if self._asr is None:
                import asr
                self._asr = asr
            return self._asr.transcribe(x)[0]

    def _synth(self, job):
        import tts_lib
        lid, text = job["lid"], job["text"]
        ln = self.book.lines[lid]
        sp = ln.speaker.upper()
        rec = self.records[lid]
        t0 = time.time()
        best = None
        for k in range(3):
            raw = self.synth.raw(sp, text, seed=tts_lib.seed_for(lid + text, k))
            sim, heard = None, ""
            if self.asr_check:
                heard = self._asr_transcribe(raw)
                sim = tts_lib.similarity(text, heard)
            act = tts_lib.active_stats(raw)
            ok = (sim is None or sim >= 0.9) and act["inner_silence_s"] <= 1.4 and act["peak"] < 2.5 and act["speech_s"] > 0.3
            score = (sim if sim is not None else 1.0) - (0 if ok else 0.5)
            if best is None or score > best[0]:
                best = (score, raw, k, sim, heard)
            if ok:
                break
        score, raw, k, sim, heard = best
        final = tts_lib.master(sp, raw, ln.direction)
        dur = len(final) / 48000.0
        v = self.book.verbatim_seconds(lid)
        rec.update(synth_s=round(time.time() - t0, 2), tries=k + 1, sim=None if sim is None else round(sim, 3), dur=round(dur, 2), verbatim_dur=round(v, 2) if v else None)
        if score < 0.5:
            rec.update(status="as written", why=f"the take was not clean (heard {heard!r})")
            self.log(f"   [adapt] {lid}: as written ({rec['why']})")
            return
        if v and not (0.5 * v <= dur <= 1.6 * v):
            rec.update(status="as written", why=f"length {dur:.1f}s against {v:.1f}s")
            self.log(f"   [adapt] {lid}: as written ({rec['why']})")
            return
        p = Prepared(lid, text, final, "adapted", sim=sim)
        with self.lock:
            self.adapted[lid] = p
        rec.update(status="ready", t_ready=p.t_ready)
        self.log(f"   [adapt] {lid}: ready ({dur:.1f}s, {time.time() - t0:.1f}s to make)")

    # ---- what a cue gets ---------------------------------------------------------------------------------------------
    def take(self, lid):
        """-> (Prepared or None, why_not_adapted)  The adapted take if it is ready, else the verbatim one."""
        with self.lock:
            p = self.adapted.get(lid)
        if p is not None:
            return p, ""
        rec = self.records.get(lid)
        why = "" if not self.wants(lid) else (rec["status"] if rec else "never asked")
        return self.preload(lid), why

    def spoken(self, lid):
        """The line has been cued: the next time it is due (a replay, a nag) it is prepared afresh."""
        with self.lock:
            self.adapted.pop(lid, None)
            self.requested.discard(lid)

    def queue_depth(self):
        return self.q.qsize()
