"""The conversation logic: who was addressed, story gating, asking Claude, speaking, remembering.

Used unchanged by the live bridge and by `bridge.py --text`.
"""
import queue
import threading
import time

import addressing
import characters as ch
from brain import BrainError, classify_consent
from config import CHARACTERS, COLORS, NAMES, SETTINGS, VOICE_ONLY
from speech_text import CONSENT_FAST, consent_heuristic, sentences


class ReplyJob:
    """A reply being written by Claude, in the background, as a queue of clean sentences."""

    def __init__(self, brain, message, max_sentences=None):
        self.q, self.cancelled, self.error = queue.Queue(), threading.Event(), None
        self.brain, self.message, self.started = brain, message, time.time()
        self.max_sentences = max_sentences
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        gen = self.brain.stream(self.message)
        try:
            for s in sentences(gen, max_sentences=self.max_sentences):
                if self.cancelled.is_set():
                    break
                self.q.put(s)
        except BrainError as e:
            self.error = e
        finally:
            gen.close()                # leaves the unread tail for the Brain to skip on its next turn
            self.q.put(None)

    def __iter__(self):
        while True:
            s = self.q.get()
            if s is None:
                if self.error:
                    print(f"   [claude] {self.error}", flush=True)
                return
            yield s

    def cancel(self):
        self.cancelled.set()


class Director:
    def __init__(self, world, brains, classifier, output, memory, beats, cfg=SETTINGS, say=print, talk_wait=None):
        self.world, self.brains, self.classifier, self.out = world, brains, classifier, output
        self.mem, self.beats, self.cfg, self.say = memory, beats, cfg, say
        self.talk_wait = cfg["talk_wait"] if talk_wait is None else talk_wait
        self._prev_talking, self._prev_last = False, 0
        self.log = []                                    # (what happened) for tests
        self.busy = threading.Lock()

    # ---- watching the recorded lines --------------------------------------------------------------------------
    def observe(self, talking, lastspoke, speaker):
        """Called by the live watcher and at every utterance: note who has just spoken a recorded line."""
        if talking and not self._prev_talking:
            who = (CHARACTERS[lastspoke - 1] if 1 <= lastspoke <= len(CHARACTERS) else None) or \
                  (CHARACTERS[speaker - 1] if 1 <= speaker <= len(CHARACTERS) else None)
            if who:
                self.mem.recorded_line(who)
            if self.out.busy:                            # a scripted line starts: stop talking over it
                self.out.abort()
        elif lastspoke and lastspoke != self._prev_last and 1 <= lastspoke <= len(CHARACTERS):
            self.mem.recorded_line(CHARACTERS[lastspoke - 1])
        self._prev_talking, self._prev_last = talking, lastspoke

    def _wait_for_quiet(self):
        end = time.time() + self.talk_wait
        while time.time() < end:
            if not self.world.talking():
                return True
            time.sleep(0.15)
        return False

    # ---- one utterance ----------------------------------------------------------------------------------------
    def handle(self, text):
        """Process what Shinji said. Returns a dict describing what happened (used by the tests)."""
        with self.busy:
            return self._handle(text.strip())

    def _handle(self, text):
        t0 = time.time()
        res = {"text": text, "addressed": None, "why": "", "mode": "chat", "spoken": [], "action": None}
        if not text:
            return res
        st = self.world.snapshot()
        self.observe(st.talking, st.lastspoke, st.speaker)
        if st.talking:
            if not self._wait_for_quiet():
                self.say("   (a recorded line is playing; the utterance is dropped)")
                res["action"] = "dropped"
                return res
            st = self.world.snapshot()
            self.observe(st.talking, st.lastspoke, st.speaker)
        res["state"] = st.describe()
        who_hears = [c for c in CHARACTERS if st.present[c] > 0]
        mode = {1: "answer", 2: "pilot"}.get(st.wait, "chat")
        res["mode"] = mode

        # --- who is addressed ---
        last = self.mem.last_speaker if self.mem.last_speaker and st.present.get(self.mem.last_speaker) else None
        if mode != "chat" and st.speaker_id and st.present.get(st.speaker_id):
            last = last or st.speaker_id
        addr = why = None
        if mode == "answer" and st.speaker_id and st.present.get(st.speaker_id):
            addr, why = st.speaker_id, "asked the question (#speaker)"
        elif who_hears:
            player, rot, chars = self.world.positions(st)
            addr, why = addressing.resolve(text, st.present, player, rot, chars, last_speaker=last, cfg=self.cfg,
                                           asker=st.speaker_id if mode != "chat" else None)
        else:
            why = "nobody is present"
        res["addressed"], res["why"] = addr, why
        self.say(f"   -> {NAMES[addr] if addr else 'nobody'} ({why}); {res['state']}")

        # --- act on the gate (the utterance is added to memory when each reply is built) ---
        verdict = None
        if addr is None:
            self.mem.player_said(None, text, st.beat)
        if mode == "pilot":
            verdict = self._pilot(st, addr, text, res)
        elif mode == "answer":
            self._chat(addr, st, text, "answer", res, t0)
            if self.world.wait_value() == 1:
                self.world.story_answered()
                res["action"] = "answered"
        else:
            if addr:
                self._chat(addr, st, text, "chat", res, t0)
            else:
                self.say("   (silence)")
        res["verdict"] = verdict
        self.mem.save()
        return res

    # ---- pieces -----------------------------------------------------------------------------------------------
    def _message(self, who, st, text, mode):
        return ch.build_message(who, beat=st.beat, beats=self.beats, presence=st.present, memory=self.mem, utterance=text,
                                mode=mode, speaker_asked=st.speaker_id, cfg=self.cfg)

    def _job(self, who, st, text, mode):
        message = self._message(who, st, text, mode)          # built from memory BEFORE this utterance is added to it
        self.mem.player_said(who, text, st.beat)
        return ReplyJob(self.brains[who], message, max_sentences=None if mode == "chat" else 2)   # gate answers are brief

    def _speak(self, who, job, st, res, t0):
        self.world.bridge_speaking(who)
        try:
            sub = (lambda w, s: self.world.subtitle(NAMES[w], s, COLORS[w])) if self.cfg["subtitles"] else None
            spoken = self.out.speak(who, iter(job), st.present[who], sub, t0)
        finally:
            self.world.bridge_speaking(None)
        res["spoken"] = spoken
        if spoken:
            self.mem.character_said(who, " ".join(spoken))
        return spoken

    def _chat(self, who, st, text, mode, res, t0):
        if who is None:
            self.say("   (silence)")
            return
        self._speak(who, self._job(who, st, text, mode), st, res, t0)

    def _pilot(self, st, addr, text, res):
        """#wait == 2: is it a yes? On consent say nothing and run consented; otherwise the addressed character answers."""
        t0 = time.time()
        fast = bool(CONSENT_FAST.match(text))                          # a plain "okay" / "I'll do it" needs no model call
        job = None
        if fast:
            if addr:
                self.mem.player_said(addr, text, st.beat)
        elif addr:
            job = self._job(addr, st, text, "pilot")                   # write the reply while the classifier decides
        if fast:
            verdict = "consent"
        else:
            try:
                verdict = classify_consent(self.classifier, text)
            except BrainError as e:
                verdict = consent_heuristic(text)
                self.say(f"   [classifier unavailable: {e}; used keywords -> {verdict}]")
        self.say(f"   -> classified: {verdict}  (+{time.time() - t0:.1f}s)")
        if verdict == "consent":
            if job:
                job.cancel()
            if self.world.wait_value() == 2:
                self.world.story_consented()
                res["action"] = "consented"
            return verdict
        if job:
            self._speak(addr, job, st, res, t0)
        return verdict
