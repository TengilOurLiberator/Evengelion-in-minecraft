"""The bridge's half of the handshake with the story, and the look-ahead that feeds it.

THE HANDSHAKE (the datapack side is tools\\story\\lines.py and system.py; every command string is in rcon_commands.py)

  heartbeat   every 0.25 s the bridge sets  #bridge_hb = 20;  the game counts it down, so "a bridge is connected" means "it spoke in the last second".
  cue         when the story reaches a `say` step of MISATO / RITSUKO / GENDO / REI while the heartbeat is alive, the game does NOT play the file: it sets
              #cue = n * 1000 + (scene * 100 + number), #talking 1 and a watchdog on #line_left (the file's length + 3 s), and waits.
  claim       the bridge, polling #cue every 20 ms, takes the prepared audio, runs  function angel:say/claim {n:..,ticks:..}  (atomic in the game: it
              refuses a cue that has been taken over or has already ended) and reads #cue_ack back.  The claim writes the REAL length of the audio into
              #line_left, so the engine's clock -- not this process -- ends the line: a bridge that dies mid-line cannot hold the story.
  takeover    a cue nobody claims within 14 ticks (0.7 s), or whose heartbeat stops, is played by the game from the pre-rendered file.  The bridge
              skips a cue whose claim is refused.

THE LOOK-AHEAD

  The step listing (storybook.py) says which line each scene cues next.  A watcher reads #scene / #step / #wait every 0.25 s; every time the
  position changes it walks the story forward, loads the pre-rendered take of every coming line (so a cue is a memory read), and, for the lines
  the policy allows to change and whose context is KNOWN (no unanswered wait between here and the line), starts the adaptation: the lines before the
  next wait at the start of a scene, and the lines after a wait the moment the player's answer is known (the Director hands it over before the
  character has even begun to reply).  A wait that ends with no answer (the safety net, a skip) is context too.
"""
import threading
import time

import rcon_commands as rc
import storybook
from config import CHARACTERS, NAMES, SETTINGS

CLAIM_TAIL_TICKS = 5            # the 4-tick tail every line has, and one more for the audio device


class Conductor:
    def __init__(self, rcon, book, story, prep, mixer, memory=None, on_line_start=None, subtitles=True, poll=0.02, hb_period=0.25, log=print,
                 verbose=False):
        self.rcon, self.book, self.story, self.prep, self.mixer, self.memory = rcon, book, story, prep, mixer, memory
        self.on_line_start, self.subtitles, self.poll, self.hb_period, self.log, self.verbose = on_line_start, subtitles, poll, hb_period, log, verbose
        self.stop_ev = threading.Event()
        self.last_n = None
        self.current = None                       # the line being played: dict(lid, end, ev, n)
        self.history = []                         # what was said aloud: ["Misato: ...", ...] (scripted and live), for the adaptation context
        self.cue_records = []                     # one dict per cue, for the report
        self.pos = (0, -1)                        # (scene, step) as last read
        self.wait = 0
        self.wait_since = None
        self.answer = None                        # dict(text, mode, t, dwell, speaker, scene, step) of the answer to the current wait
        self.last_wait_info = None                # what to tell the adaptation about the wait just passed
        self.planned_for = None
        self.lock = threading.RLock()
        self.threads = []
        self.alive_since = None
        self.rc_ms = []                           # round-trip times of the poll (ms), for the report
        self.watch_rcon = None

    # ------------------------------------------------------------------------------------------------------------- start / stop
    def start(self, watch_rcon=None):
        self.watch_rcon = watch_rcon or self.rcon
        for fn, name in ((self._cue_loop, "cue"), (self._watch_loop, "watch")):
            t = threading.Thread(target=fn, name=f"conductor-{name}", daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        self.stop_ev.set()
        try:
            self.rcon.cmd(rc.score_set(rc.SCORE_BRIDGE_HB, 0))
        except Exception:
            pass

    def say(self, m):
        if self.verbose:
            self.log(m)

    # ------------------------------------------------------------------------------------------------------------- the cue loop
    def _get(self, name, rcon=None):
        return rc.parse_score((rcon or self.rcon).cmd(rc.score_get(name)), name)

    def _cue_loop(self):
        hb_next = 0.0
        try:
            v = self._get(rc.SCORE_CUE)
            self.last_n = (v // 1000) if v else 0               # a cue left over from before the bridge started is not ours
        except Exception:
            self.last_n = 0
        cut_next = 0.0
        while not self.stop_ev.is_set():
            try:
                now = time.time()
                if now >= hb_next:
                    self.rcon.cmd(rc.heartbeat())
                    hb_next = now + self.hb_period
                    if self.alive_since is None:
                        self.alive_since = now
                t0 = time.time()
                v = self._get(rc.SCORE_CUE)
                t_seen = time.time()
                self.rc_ms.append((t_seen - t0) * 1000)
                if len(self.rc_ms) > 2000:
                    del self.rc_ms[:1000]
                if v and v // 1000 != self.last_n:
                    self.last_n = v // 1000
                    self._on_cue(v, t_seen)
                elif self.current is not None and now >= cut_next:
                    cut_next = now + 0.15
                    self._check_cut()
            except Exception as e:
                self.log(f"   [bridge] cue loop: {e.__class__.__name__}: {e}")
                time.sleep(0.5)
            time.sleep(self.poll)

    def _on_cue(self, v, t_seen):
        n, code = v // 1000, v % 1000
        lid = storybook.code_to_id(code)
        ln = self.book.lines.get(lid)
        rec = {"cue": n, "line": lid, "t_seen": t_seen}
        if ln is None or not ln.human:
            self.say(f"   [cue {n}] {lid}: not a character line")
            return
        p, why = self.prep.take(lid)
        t_taken = time.time()
        a = self.prep.records.pop(lid, None)
        if p is None:
            rec["result"] = "no audio: left to the game"
            self.cue_records.append(rec)
            self.log(f"   [cue {n}] {lid} {ln.speaker.upper()}: no pre-rendered take and nothing prepared; the game plays it")
            return
        if self.on_line_start:
            try:
                self.on_line_start(ln, p.dur)
            except Exception:
                pass
        ticks = int(round(p.dur * 20)) + CLAIM_TAIL_TICKS
        self.rcon.cmd(rc.claim(n, ticks))
        ack = self._get(rc.SCORE_CUE_ACK)
        for _ in range(3):
            if ack is not None:
                break
            ack = self._get(rc.SCORE_CUE_ACK)               # (a reply that is not about #cue_ack -- another RCON client got in between -- is read again)
        t_claimed = time.time()
        if ack != n:
            rec["result"] = "claim refused (the game had taken the line over, or it was over)"
            self.cue_records.append(rec)
            self.log(f"   [cue {n}] {lid}: claim refused (ack {ack}); not played")
            return
        ev = self.mixer.play("line", p.wav, 48000)
        t_play = time.time()
        end = t_play + p.dur
        self.current = {"lid": lid, "end": end, "ev": ev, "n": n}
        rec.update(result="played", kind=p.kind, text=p.text, script=ln.text, dur=round(p.dur, 2), ready_margin=round(t_seen - p.t_ready, 2),
                   cue_to_play_ms=round((t_play - t_seen) * 1000), claim_ms=round((t_claimed - t_taken) * 1000), why_not_adapted=why,
                   adapt=dict(a) if (a and p.kind == "adapted") else None)
        if a:
            rec["adapt_rec"] = {k: v for k, v in a.items() if k not in ("t_asked", "t_text", "t_ready")}
        if a and why:
            rec["adapt_status"] = a.get("status")
            rec["adapt_why"] = a.get("why")
        if a and p.kind == "adapted":
            rec["synth_s"], rec["claude_s"] = a.get("synth_s"), a.get("claude_s")
        self.cue_records.append(rec)
        spoken = p.text
        self.history.append(f"{NAMES[ln.speaker]}: {spoken}")
        if self.memory is not None:
            self.memory.recorded_line(ln.speaker, spoken)
        self.prep.spoken(lid)
        self.log(f"   [cue {n}] {lid} {ln.speaker.upper():8s} {p.kind:8s} {p.dur:4.1f}s  start +{(t_play - t_seen) * 1000:.0f} ms  {spoken}")
        if self.subtitles:
            try:
                if self._get(rc.SCORE_SUBTITLES) == 1:
                    self.rcon.cmd(rc.subtitle(NAMES[ln.speaker], spoken))
            except Exception:
                pass
        self.replan(force=True)

    def _check_cut(self):
        cur = self.current
        if cur is None:
            return
        if cur["ev"].is_set():
            self.current = None
            return
        if self._get(rc.SCORE_TALKING) == 0 and time.time() < cur["end"] - 0.5:
            self.mixer.stop("line")                            # the story cut the line (skip, stop, scene jump)
            self.log(f"   [cue {cur['n']}] {cur['lid']}: cut by the story")
            self.current = None

    def line_playing(self):
        c = self.current
        return c is not None and not c["ev"].is_set()

    # ------------------------------------------------------------------------------------------------------------- the watcher
    def _watch_loop(self):
        r = self.watch_rcon
        while not self.stop_ev.is_set():
            try:
                scene = self._get(rc.SCORE_SCENE, r)
                step = self._get(rc.SCORE_STEP, r)
                wait = self._get(rc.SCORE_WAIT, r) or 0
                if scene is not None and step is not None:
                    self.observe(scene, step, wait)
            except Exception as e:
                self.log(f"   [bridge] watcher: {e.__class__.__name__}: {e}")
            time.sleep(0.25)

    def observe(self, scene, step, wait):
        """The position of the story as just read (also called directly by the tests)."""
        now = time.time()
        with self.lock:
            prev_scene, prev_step = self.pos
            changed = (scene, step) != self.pos
            if wait >= 1 and self.wait == 0:
                self.wait_since = now
            if wait == 0 and self.wait >= 1:
                pass
            # a step that was a wait is behind us: it ended with the player's answer or without one
            if changed and prev_step >= 0:
                st = self.story.get(prev_scene, prev_step)
                if st is not None and st["kind"] == "wait":
                    dwell = now - (self.wait_since or now)
                    if self.answer and self.answer["scene"] == prev_scene and self.answer["step"] == prev_step:
                        self.last_wait_info = dict(self.answer, dwell=self.answer["dwell"])
                    else:
                        self.last_wait_info = dict(text=None, dwell=dwell, speaker=st["speaker"], scene=prev_scene, step=prev_step, skipped=True,
                                                   prompt=st.get("prompt"))
                    self.answer = None
                    self.wait_since = None
            self.pos, self.wait = (scene, step), wait
        if changed:
            self.replan()

    # ------------------------------------------------------------------------------------------------------------- what the player said
    def note_answer(self, text, mode, speaker=None):
        """The Director has the player's words for the current wait (before the character answers). Starts the adaptation of the lines that follow."""
        with self.lock:
            scene, step = self.pos
            st = self.story.get(scene, step)
            if st is None or st["kind"] != "wait" or mode != "answer":
                self.say(f"   [bridge] player's words noted (not at an answer-wait): {text!r}")
                return
            dwell = time.time() - (self.wait_since or time.time())
            self.answer = dict(text=text, mode=mode, speaker=st["speaker"], scene=scene, step=step, dwell=dwell, prompt=st.get("prompt"))
        self.replan(force=True)

    # ------------------------------------------------------------------------------------------------------------- planning
    def replan(self, force=False):
        scene, step = self.pos
        if step < 0:
            return
        with self.lock:
            answer = self.answer
            info = self.last_wait_info
        st = self.story.get(scene, step)
        start = (scene, step)
        if st is not None and st["kind"] == "wait" and answer is not None:
            succ = self.story.successors(scene, step)
            if succ:
                start = succ[0]
                ahead = self.story.ahead(start[0], start[1], max_lines=10)
                ctx_info = answer
            else:
                return
        else:
            ahead = [a for a in self.story.ahead(scene, step, max_lines=10) if not (a["scene"] == scene and a["step"] == step)]    # (the step now running is already being said)
            ctx_info = info
        # 1. the pre-rendered takes of everything coming (a memory read at the cue)
        for a in ahead:
            self.prep.preload(a["line"])
        # 2. adapt the lines whose context is known, as one group (a segment), with the fixed lines of the stretch as context
        group, fixed, later = [], [], []
        for a in ahead:
            lid = a["line"]
            if a.get("nudge"):
                continue
            if a["blocked"]:
                if len(later) < 3:
                    later.append(lid)
                continue
            ln = self.book.lines.get(lid)
            if ln is None:
                continue
            if self.prep.wants(lid):
                group.append(lid)
            else:
                fixed.append(lid)
        if group and not self.prep.verbatim_only:
            self.prep.adapt(group, self.context(ctx_info, group), later_ids=later or self._after(group), fixed_ids=[f for f in fixed])

    def _after(self, group):
        """The three script lines after the group, in script order (fixed context when the walk had nothing beyond the group)."""
        last = self.book.order.index(group[-1])
        return [i for i in self.book.order[last + 1:last + 6] if i not in group][:3]

    def context(self, info, group):
        moment = "Nothing in particular has happened since the last line; the story simply goes on."
        who = self.book.lines[group[0]].speaker
        if info:
            nm = NAMES.get(info.get("speaker"), "she")
            if info.get("skipped") or not info.get("text"):
                moment = (f"At the pause after {nm}'s question Shinji said nothing; after {info.get('dwell', 0):.0f} seconds the story went on without an "
                          f"answer. He may be shy, lost or simply not talking.")
            else:
                d = info.get("dwell", 0)
                speed = "at once" if d < 2.5 else f"after about {d:.0f} seconds" if d < 12 else f"only after a long {d:.0f} seconds"
                moment = (f'At the pause after {nm}\'s question Shinji answered aloud, {speed}: "{info["text"]}". {nm} has just replied to him in her '
                          f"own words (not shown), so the next line follows that reply.")
        return {"log": list(self.history), "moment": moment}
