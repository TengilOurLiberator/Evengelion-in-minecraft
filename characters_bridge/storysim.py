"""A stand-in for the GAME for the bridge's self-test: the story's scoreboard and the say handshake as the datapack runs them, 20 ticks a second,
behind the same RCON surface as the real server (it answers the bridge's commands exactly like fake_rcon.FakeRcon, plus the handshake), and a walker
that goes through the step listing of the scenes (`build_story.py --steps`) cueing every line in order, with scripted answers from the "player".

What it mirrors (tools\\story\\lines.py, system.py `t_line`): #bridge_hb counted down every tick; a character line is CUED while the heartbeat is alive
(#cue, #talking, the watchdog on #line_left); `angel:say/claim` accepted only for the current unclaimed cue and writing the real length; the
unclaimed cue taken over by the game after 14 ticks or when the heartbeat stops; #talking released by the clock.  Time can be sped up (`speed`).
"""
import re
import threading
import time

import rcon_commands as rc
from config import CHARACTERS
from fake_rcon import FakeRcon
from storybook import id_to_code

ACK_TICKS = 14
WATCHDOG_TICKS = 60


class FakeGame(FakeRcon):
    def __init__(self, book, speed=1.0):
        super().__init__(verbose=False)
        self.book, self.speed = book, speed
        self.lock = threading.RLock()
        self.scores.update({"#scene": 0, "#step": -1, "#bridge_hb": 0, "#live_ok": 1, "#live": 0, "#cue": 0, "#cue_n": 0, "#cue_ack": -1,
                            "#cue_fb": 0, "#cue_wait": 0, "#line": 0, "#line_left": 0, "#subtitles": 0, "#consent": 0, "#lastspoke": 0,
                            rc.SCORE_BRIDGE_SPEAKING: 0})
        self.t0 = time.time()
        self.events = []                   # (seconds since start, kind, text)
        self.fallbacks = []                # line ids the game played itself
        self.stop_ev = threading.Event()
        self.ticks = 0
        threading.Thread(target=self._ticker, daemon=True).start()

    # ---- time ------------------------------------------------------------------------------------------------------
    def now(self):
        return (time.time() - self.t0) * self.speed

    def log(self, kind, text):
        self.events.append((round(self.now(), 2), kind, text))

    def _ticker(self):
        nxt = time.time()
        while not self.stop_ev.is_set():
            nxt += 0.05 / self.speed
            with self.lock:
                self._tick()
            d = nxt - time.time()
            if d > 0:
                time.sleep(d)

    def _tick(self):
        s = self.scores
        self.ticks += 1
        if s["#bridge_hb"] >= 1:
            s["#bridge_hb"] -= 1
        if s["#talking"] == 1:
            s["#line_left"] -= 1
            if s["#line_left"] <= 0:
                s["#talking"] = 0
        if s["#talking"] == 1 and s["#live"] == 1 and s["#cue_ack"] != s["#cue_n"]:
            s["#cue_wait"] += 1
            if s["#live"] == 1 and s["#bridge_hb"] < 1:
                self._fallback("the heartbeat stopped")
            if s["#live"] == 1 and s["#cue_wait"] >= ACK_TICKS:
                self._fallback("not claimed in 14 ticks")

    # ---- the say functions -------------------------------------------------------------------------------------------
    def _file_ticks(self, lid):
        sec = self.book.verbatim_seconds(lid)
        return int(round((sec if sec else 3.0) * 20)) + 4

    def _play_file(self, lid):
        s = self.scores
        ln = self.book.lines[lid]
        s["#talking"], s["#line_left"], s["#line"], s["#live"] = 1, self._file_ticks(lid), id_to_code(lid), 0
        if ln.speaker in CHARACTERS:
            s["#lastspoke"] = s["#speaker"] = CHARACTERS.index(ln.speaker) + 1
        self.fallbacks.append(lid) if ln.human and self._in_fallback else None

    _in_fallback = False

    def _fallback(self, why):
        s = self.scores
        s["#live"], s["#cue_fb"] = 0, 1
        lid = f"{s['#line'] // 100}.{s['#line'] % 100:02d}"
        self._in_fallback = True
        self._play_file(lid)
        self._in_fallback = False
        self.log("fallback", f"{lid}: the game plays the file ({why})")

    def say(self, lid):
        """angel:say/<key>"""
        with self.lock:
            s = self.scores
            ln = self.book.lines[lid]
            s["#line"] = id_to_code(lid)
            s["#live"] = 0
            if ln.human and s["#live_ok"] == 1 and s["#bridge_hb"] >= 1:
                s["#live"], s["#cue_fb"], s["#cue_wait"], s["#cue_ack"] = 1, 0, 0, -1
                s["#cue_n"] += 1
                s["#cue"] = s["#cue_n"] * 1000 + s["#line"]
                s["#talking"] = 1
                s["#line_left"] = self._file_ticks(lid) + WATCHDOG_TICKS
                s["#lastspoke"] = s["#speaker"] = CHARACTERS.index(ln.speaker) + 1
                self.log("cue", f"{lid} cued (n={s['#cue_n']})")
            else:
                self._play_file(lid)
                self.log("file", f"{lid} played from the file ({'a bark/BASE line' if not ln.human else 'no bridge'})")

    # ---- the RCON surface --------------------------------------------------------------------------------------------
    def cmd(self, command):
        with self.lock:
            m = re.fullmatch(r"function angel:say/claim \{n:(-?\d+),ticks:(-?\d+)\}", command)
            if m:
                n, ticks = int(m.group(1)), int(m.group(2))
                s = self.scores
                if s["#live"] == 1 and s["#talking"] == 1 and s["#cue_n"] == n and s["#cue_ack"] != n:
                    s["#cue_ack"], s["#line_left"] = n, ticks
                    self.log("claim", f"cue {n} claimed, {ticks} ticks")
                return "Executed function angel:say/claim"
            if command in (rc.FN_CONSENTED,):
                self.scores["#consent"] = 1
            return super().cmd(command)

    def close(self):
        self.stop_ev.set()


# ======================================================================================================== the walker
class Walker(threading.Thread):
    """Goes through the scenes' steps like the engine: lines are cued and waited for, sleeps and waits for the player's movements are shortened
    (`cap` seconds at most), a wait is released by the Director (answered / consented), by silence (`silent_s`), or by its timeout."""

    def __init__(self, game, story, scenes, script, director=None, cap=4.0, silent_s=12.0, log=print):
        super().__init__(daemon=True)
        self.game, self.story, self.scenes, self.script, self.director, self.cap, self.silent_s, self.log = game, story, scenes, script, director, cap, silent_s, log
        self.done = threading.Event()
        self.lines_said = []
        self.waits_seen = []
        self.error = None

    def sleep(self, sec):
        time.sleep(max(0.0, sec) / self.game.speed)

    def run(self):
        try:
            self._run()
        except Exception as e:
            import traceback
            self.error = traceback.format_exc()
            self.log("walker error:\n" + self.error)
        finally:
            self.done.set()

    def _run(self):
        g = self.game
        scene = self.scenes[0]
        i = 0
        entered_by_handover = False
        while True:
            steps = self.story.steps.get(scene)
            if steps is None or i >= len(steps):
                break
            st = steps[i]
            with g.lock:
                g.scores["#scene"], g.scores["#step"] = scene, i
            k = st["kind"]
            if k == "say":
                self.lines_said.append(st["line"])
                g.say(st["line"])
                self._until_quiet()
            elif k == "sleep":
                self.sleep(min(st["sec"], self.cap))
            elif k == "until":
                self.sleep(min(st.get("est") or 2.0, self.cap))
            elif k == "wait":
                self._wait(scene, i, st)
            elif k == "goto":
                i = st["target"]
                continue
            elif k == "branch":
                m = re.search(r"if score (\S+) angel\.story matches (\d+)", st.get("cond", ""))
                taken = bool(m) and g.scores.get(m.group(1), 0) == int(m.group(2))
                self.log(f"   (branch at {scene}:{i} -> {'taken' if taken else 'not taken'}: {st.get('cond', '')[:60]})")
                if taken:
                    i = st["target"]
                    continue
            elif k == "handover":
                nxt = st["to"]
                if nxt not in self.scenes:
                    break
                scene = nxt
                i = int(self.story.meta.get("setup_end", {}).get(str(nxt), 0))      # (the state is carried over: the setup steps are skipped)
                continue
            i += 1

    def _until_quiet(self):
        g = self.game
        while True:
            with g.lock:
                if g.scores["#talking"] == 0:
                    return
            time.sleep(0.02 / g.speed if g.speed > 1 else 0.02)

    def _wait(self, scene, i, st):
        g = self.game
        nth = sum(1 for w in self.waits_seen if w[0] == scene)
        self.waits_seen.append((scene, i))
        answers = list(self.script.get((scene, nth), []))
        speaker = st.get("speaker")
        with g.lock:
            g.scores["#wait"] = st["mode"]
            g.scores["#speaker"] = CHARACTERS.index(speaker) + 1 if speaker in CHARACTERS else 0
        t0 = time.time()
        timeout = min(st["timeout"], 20.0) if st.get("timeout") else None
        nudges = list(st.get("nudge_lines") or [])
        nfirst, nrep = st.get("nudge_first") or 0, st.get("nudge_repeat") or 0
        silent_ticks, nudge_k = 0.0, 0
        pending = None
        last_t = time.time()
        self.log(f"   (wait {scene}:{i} mode {st['mode']} for {speaker}; scripted: {[a[1] for a in answers] or 'silence'})")
        while True:
            time.sleep(0.02)
            now = time.time()
            dt = (now - last_t) * g.speed
            last_t = now
            with g.lock:
                released = g.scores["#wait"] == 0
                quiet = g.scores["#talking"] == 0 and g.scores[rc.SCORE_BRIDGE_SPEAKING] == 0
            if released:
                break
            el = (now - t0) * g.speed
            if quiet:
                silent_ticks += dt
            if nudges and quiet and silent_ticks >= nfirst:
                lid = nudges[min(nudge_k, len(nudges) - 1)]
                nudge_k += 1
                silent_ticks = nfirst - nrep                       # the next one `nrep` seconds of silence after this line ends
                g.say(lid)
                self.log(f"   (nudge {lid})")
                self.lines_said.append(lid)
                continue
            if pending is None and answers and el >= answers[0][0]:
                delay, text = answers.pop(0)
                pending = threading.Thread(target=self._player_says, args=(text,), daemon=True)
                pending.start()
            if pending is not None and not pending.is_alive():
                pending = None
                t0 = time.time()                                # the next scripted utterance is timed from the end of this exchange
                if answers:
                    answers[0] = (answers[0][0], answers[0][1])
            if not answers and pending is None:
                if st["mode"] == 1 and el >= self.silent_s and not st.get("timeout"):
                    self.log("   (the safety net lets the wait go: no answer)")
                    with g.lock:
                        g.scores["#wait"] = 0
                    break
                if timeout and el >= timeout:
                    self.log("   (the wait times out)")
                    with g.lock:
                        g.scores["#wait"] = 0
                    break
        self._until_quiet()

    def _player_says(self, text):
        """What the player says.  Like a person, he says it again if the story talked over him (the Director drops an utterance that waited too long)."""
        for attempt in range(6):
            self.log(f"\nShinji> {text}" + (" (again)" if attempt else ""))
            if self.director is None:
                with self.game.lock:
                    self.game.scores["#wait"] = 0
                return
            res = self.director.handle(text)
            if res.get("action") != "dropped":
                return
            time.sleep(1.5)
            with self.game.lock:
                if self.game.scores["#wait"] == 0:
                    return


# the player's side of the self-test: (scene, number of the wait inside the scene) -> [(seconds he waits before speaking, what he says)]
DEFAULT_SCRIPT = {
    (2, 0): [(3.0, "I'm fine. Just a bit shaken.")],
    (2, 1): [(2.0, "Yeah. I think I swallowed some dirt.")],
    (3, 0): [(4.0, "Yes, I have the card right here.")],
    (3, 1): [(6.0, "Not really. I haven't seen him in three years.")],
    (3, 2): [(2.5, "No. We're not close.")],
    (4, 0): [(7.0, "Yes. That's the same door we passed before.")],
    (4, 1): [],                                                      # says nothing: the story goes on without an answer
    (5, 0): [(3.0, "What is that thing?")],
    (5, 1): [],
    (5, 2): [(4.0, "Me? I can't pilot that.")],
    (5, 3): [(6.0, "I don't know. I'm scared.")],
    (5, 4): [(2.0, "I don't know if I can.")],                       # a non-yes at the consent wait: Misato answers; the wait times out
    (5, 5): [(26.0, "Okay. I'll do it.")],                           # long enough for the first nudge (5.39) before he agrees
    (6, 0): [],
}
