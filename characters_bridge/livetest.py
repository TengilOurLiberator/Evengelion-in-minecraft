"""Live handshake test against a SCRATCH Angel Attack server (nothing of the real server is touched, no game client is started).

    python livetest.py                      all scenarios
    python livetest.py --only nobridge,bridge,kill,cage
    python livetest.py --keep               leave the scratch folder (its path is printed) instead of deleting it

The scratch server is a copy of server\\ in a temp folder (prefix aa_voicebridge_), server-port 25605, rcon.port 25615, with the repo's datapack and the
story's DRY variant (`build_story.py --dry`: a mannequin tagged angel.testplayer is the player), the world placed fresh.  It is stopped and deleted at
the end, or when this script dies (the server is adopted by a job object).  The bridge runs as a subprocess in `--text --live --dry` mode; the "player"
is this script, which types his answers into the bridge's stdin when the story waits and pushes the steps that wait for a real person's movements
(`angel:story/next`).

Scenarios
  nobridge  scene 2 with no bridge: the cues never happen, the pre-rendered files play (#cue_n stays 0, #talking lasts as long as durations.json says)
  bridge    scene 2 with the bridge: every character line is cued and claimed; the engine waits for the REPORTED length; the latency in game ticks
  kill      scene 2, the bridge is killed in the middle of a line: the clock still releases the story, the next line is played by the game from its file
  bark      a fight bark (angel:fight/say/7_04) while the bridge is connected: played by the game at once, never cued
  cage      scene 5 (the cage) with the bridge and adaptation: through the waits, to the consent
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
PY = sys.executable
PORT, RPORT = 25605, 25615

from visual.server import Scratch  # noqa: E402
import rcon as toolsrcon  # noqa: E402


class VoiceScratch(Scratch):
    def __init__(self, **kw):
        super().__init__(**kw)
        shutil.rmtree(self.tmp, ignore_errors=True)               # (the parent class made an aa_visual_ folder: use our own prefix)
        self.tmp = tempfile.mkdtemp(prefix="aa_voicebridge_")
        self.srv = os.path.join(self.tmp, "server")


def port_free(p):
    import socket
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


class Conn:
    """ONE RCON connection shared by every thread of this test: the vanilla server keeps a single response buffer for all RCON clients, so two connections
    that run a command at the same moment get each other's text back.  (The bridge, a separate process, is a second client; its replies are checked by name.)"""

    def __init__(self, srv):
        self.srv, self.lock = srv, threading.Lock()
        self.rcon_port, self.password, self.dp = srv.rcon_port, srv.password, srv.dp

    def cmd(self, c):
        with self.lock:
            return self.srv.cmd(c)


def score(r, name):
    for _ in range(4):
        m = re.search(re.escape(name) + r" has (-?\d+)", r.cmd(f"scoreboard players get {name} angel.story") or "")
        if m:
            return int(m.group(1))
    return None


class Sampler(threading.Thread):
    """Reads the handshake scores on its own RCON connection as fast as the server answers; keeps the times at which they change."""

    def __init__(self, srv, names):
        super().__init__(daemon=True)
        self.r = srv
        self.names, self.stop_ev = names, threading.Event()
        self.vals, self.changes = {}, []
        self.samples = 0

    def run(self):
        while not self.stop_ev.is_set():
            for n in self.names:
                try:
                    v = score(self.r, n)
                except Exception:
                    time.sleep(0.2)
                    continue
                if self.vals.get(n) != v:
                    self.changes.append((time.time(), n, v))
                    self.vals[n] = v
            self.samples += 1

    def stop(self):
        self.stop_ev.set()


def build_dry(dest):
    r = subprocess.run([PY, os.path.join(ROOT, "tools", "story", "build_story.py"), "--dry", "--out", dest, "--quiet"], capture_output=True, text=True,
                       cwd=os.path.join(ROOT, "tools", "story"))
    if r.returncode:
        raise RuntimeError("dry build failed:\n" + (r.stdout + r.stderr)[-2000:])


class Bridge:
    """The bridge as a subprocess against the scratch server; collects its output."""

    def __init__(self, srv, args):
        env = dict(os.environ, ANGEL_RCON_HOST="127.0.0.1", ANGEL_RCON_PORT=str(srv.rcon_port), ANGEL_RCON_PASSWORD=srv.password, PYTHONIOENCODING="utf-8")
        self.p = subprocess.Popen([PY, "-u", os.path.join(HERE, "bridge.py"), "--text", "--live", "--dry", "--fresh"] + args, cwd=HERE, env=env,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", bufsize=1)
        self.lines = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for ln in self.p.stdout:
            self.lines.append((time.time(), ln.rstrip()))
            if "Sampling" not in ln:
                print("   | " + ln.rstrip(), flush=True)

    def wait_for(self, pattern, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if any(re.search(pattern, l) for _, l in self.lines):
                return True
            if self.p.poll() is not None:
                return False
            time.sleep(0.3)
        return False

    def say(self, text):
        try:
            self.p.stdin.write(text + "\n")
            self.p.stdin.flush()
        except OSError:
            pass

    def kill(self):
        self.p.kill()


class Driver:
    """The player and the engine's helper: pushes steps that wait for a person's movements, answers the waits."""

    def __init__(self, srv, steps, bridge=None, answers=None):
        self.srv, self.steps, self.bridge = srv, steps, bridge
        self.answers = answers or {}
        self.pos = None
        self.pos_since = time.time()
        self.wait_since = None
        self.answered = set()
        self.log = []

    def kind(self, scene, step):
        try:
            return self.steps[str(scene)][step]
        except (KeyError, IndexError):
            return None

    def tick(self):
        """One look at the story; returns (scene, step, wait, talking)."""
        scene, step = score(self.srv, "#scene"), score(self.srv, "#step")
        wait, talking = score(self.srv, "#wait"), score(self.srv, "#talking")
        now = time.time()
        if now - getattr(self, "_fl", 0) > 0.3:
            # a real player keeps the chunks round him loaded; the stand-in does not, and he rides a car at 9 blocks a second
            self._fl = now
            self.srv.cmd(f"execute at {PLAYER_SEL} run forceload add ~-48 ~-48 ~48 ~48")
        if (scene, step) != self.pos:
            self.pos, self.pos_since, self.wait_since = (scene, step), now, None
        st = self.kind(scene, step) if scene is not None and step is not None and step >= 0 else None
        if st and st["kind"] == "until" and not talking and now - self.pos_since > min(st.get("est") or 3.0, 5.0) + 1.0:
            self.srv.cmd("function angel:story/next")
            self.log.append((now, f"pushed {scene}:{step} ({st['note'][:40]})"))
            self.pos_since = now
        if st and st["kind"] == "wait" and wait and wait >= 1:
            if self.wait_since is None:
                self.wait_since = now
            key = (scene, step)
            ans = self.answers.get(key)
            if ans is not None and key not in self.answered and now - self.wait_since > ans[0] and not talking and self.bridge is not None:
                self.answered.add(key)
                self.log.append((now, f"Shinji says: {ans[1]}"))
                print(f"   Shinji> {ans[1]}", flush=True)
                self.bridge.say(ans[1])
            elif ans is None and now - self.wait_since > 25:
                self.srv.cmd("function angel:story/skip")
                self.log.append((now, f"skipped silent wait {scene}:{step}"))
                self.wait_since = now
        return scene, step, wait, talking


def start_scratch(keep):
    for p in (PORT, RPORT):
        if not port_free(p):
            sys.exit(f"port {p} is busy")
    tmp_dry = tempfile.mkdtemp(prefix="aa_voicebridge_dry_")
    log("building the dry variant of the story ...")
    build_dry(tmp_dry)
    srv = VoiceScratch(port=PORT, rcon_port=RPORT, exclude_dirs=("story", "say"), keep=keep)
    srv.prepare()
    shutil.copytree(os.path.join(tmp_dry, "data"), os.path.join(srv.dp, "data"), dirs_exist_ok=True)
    shutil.rmtree(tmp_dry, ignore_errors=True)
    log(f"scratch server in {srv.srv}; starting (server-port {PORT}, rcon {RPORT}) ...")
    srv.start(timeout=300)
    if "file/angel" not in srv.cmd("datapack list enabled"):
        log("the angel datapack was not enabled; enabling it")
        srv.cmd('datapack enable "file/angel"')
        time.sleep(3)
    mark = len(srv.log())
    srv.cmd("function angel:world/place_all")
    srv.wait_log(r"every set is placed", 900, since=mark)
    log("sets placed")
    # the mannequin waits far from every set (the story's `halt` removes the forceloads of the sets, and an unloaded mannequin is no player)
    srv.cmd("forceload add 1000 1000")
    time.sleep(1.5)
    srv.cmd('execute in minecraft:overworld run summon minecraft:mannequin 1000.5 80 1000.5 {Tags:["angel.testplayer"],NoGravity:1b,Invulnerable:1b}')
    time.sleep(1.0)
    log("mannequin: " + srv.cmd("execute if entity @e[type=minecraft:mannequin,tag=angel.testplayer]"))
    return srv


def make_conn(srv):
    return Conn(srv)


PLAYER_SEL = "@e[type=minecraft:mannequin,tag=angel.testplayer,limit=1]"


def home(srv):
    """The stand-in player goes back to his far chunk (the story's `halt` unforces the sets' chunks, and an unloaded mannequin is no player).
    If he is already gone he is made again."""
    if "passed" not in srv.cmd("execute if entity " + PLAYER_SEL):
        srv.cmd("forceload add 1000 1000")
        time.sleep(1.0)
        srv.cmd('execute in minecraft:overworld run summon minecraft:mannequin 1000.5 80 1000.5 {Tags:["angel.testplayer"],NoGravity:1b,Invulnerable:1b}')
        time.sleep(0.5)
        log("   (the stand-in player had to be made again)")
    srv.cmd(f"ride {PLAYER_SEL} dismount")
    srv.cmd(f"tp {PLAYER_SEL} 1000.5 80 1000.5")
    time.sleep(0.5)


def stop_story(srv):
    home(srv)
    srv.cmd("function angel:story/stop")
    time.sleep(1.0)


def run_scene(srv, drv, scene, until_fn, timeout):
    home(srv)
    srv.cmd(f"function angel:story/scene {{n:{scene}}}")
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = drv.tick()
        if until_fn(s):
            return True
        time.sleep(0.05)
    return False


# ======================================================================================================== the scenarios
def scenario_nobridge(srv, steps, res):
    log("== no bridge: scene 2 up to the first wait")
    smp = Sampler(srv, ["#cue_n", "#talking", "#line", "#live", "#bridge_hb", "#wait"])
    smp.start()
    drv = Driver(srv, steps)
    seen = []
    ok = run_scene(srv, drv, 2, lambda s: s[2] and s[2] >= 1 and s[1] > 5, 240)
    smp.stop()
    time.sleep(0.3)
    lines = [(t, v) for t, n, v in smp.changes if n == "#line" and v]
    talk = [(t, v) for t, n, v in smp.changes if n == "#talking"]
    spans = []
    start = None
    for t, v in talk:
        if v == 1:
            start = t
        elif start is not None:
            spans.append(t - start)
            start = None
    cue_n = smp.vals.get("#cue_n")
    durs = json.load(open(os.path.join(ROOT, "voices", "durations.json")))
    want = [durs.get(f"{v // 100}.{v % 100:02d}") for _, v in lines]
    log(f"   reached the wait: {ok}; lines played {[f'{v // 100}.{v % 100:02d}' for _, v in lines]}; #cue_n = {cue_n}; #talking spans {[round(x, 2) for x in spans]} (files: {want})")
    res["nobridge"] = dict(reached_wait=ok, cue_n=cue_n, lines=[v for _, v in lines], spans=spans, files=want,
                           ok=bool(ok and cue_n == 0 and lines and all(abs(a - b - 0.2) < 0.45 for a, b in zip(spans, want) if b)))
    stop_story(srv)


ANSWERS_S2 = {(2, 22): (3.0, "I'm fine. Just a bit shaken."), (2, 54): (2.0, "Yeah. I think I swallowed some dirt.")}


def cue_report(smp, bridge, srv):
    """Pair up the cue / ack / talking changes into rows."""
    ch = smp.changes
    cues = [(t, v) for t, n, v in ch if n == "#cue_n" and v]
    acks = [(t, v) for t, n, v in ch if n == "#cue_ack" and v is not None and v >= 0]
    return cues, acks


def scenario_bridge(srv, steps, res, kill=False, args=None):
    name = "kill" if kill else "bridge"
    log(f"== {'the bridge is killed in the middle of a line' if kill else 'with the bridge'}: scene 2")
    b = Bridge(srv, ["--verbatim", "--no-asr-check"] if kill else ["--verbatim", "--no-asr-check"])
    if not b.wait_for(r"performing the scripted lines silently", 240):
        res[name] = dict(ok=False, why="the bridge did not come up")
        b.kill()
        return
    time.sleep(1.0)
    hb = score(srv, "#bridge_hb")
    log(f"   #bridge_hb = {hb} (alive: {hb and hb > 0})")
    smp = Sampler(srv, ["#cue_n", "#cue_ack", "#talking", "#line", "#live", "#cue_fb", "#bridge_hb", "#line_left"])
    smp.start()
    drv = Driver(srv, steps, bridge=b, answers=ANSWERS_S2)
    killed = {"t": None}

    def until(s):
        scene, step, wait, talking = s
        if kill and killed["t"] is None and talking and smp.vals.get("#live") == 1 and smp.vals.get("#cue_ack", -1) == smp.vals.get("#cue_n") and (smp.vals.get("#line_left") or 0) > 60:
            killed["t"] = time.time()
            killed["line"] = smp.vals.get("#line")
            killed["left"] = smp.vals.get("#line_left")
            b.kill()
            log(f"   KILLED the bridge during line {killed['line'] // 100}.{killed['line'] % 100:02d} (#line_left {killed['left']} ticks = {killed['left'] / 20:.1f}s still to run)")
        if kill:
            return killed["t"] is not None and time.time() - killed["t"] > 14
        return scene == 2 and step is not None and step > 90          # past the call (2.16) and into the scene's end
    ok = run_scene(srv, drv, 2, until, 420)
    cues_n_end = score(srv, "#cue_n")
    ack_t = score(srv, "#ack_t")
    smp.stop()
    time.sleep(0.3)
    out = dict(reached=ok, pushed=len([1 for _, m in drv.log if m.startswith("pushed")]), samples=smp.samples)
    cues, acks = cue_report(smp, b, srv)
    ack_by_n = {v: t for t, v in acks}
    lat = []
    rows = []
    for t, n in cues:
        a = ack_by_n.get(n)
        rows.append((n, None if a is None else round((a - t) * 1000)))
        if a is not None:
            lat.append((a - t) * 1000)
    out["cues"], out["claimed"] = len(cues), len(lat)
    out["cue_to_ack_ms_observed"] = [r[1] for r in rows]
    if lat:
        out["observed_cue_to_ack_ms"] = dict(median=round(statistics.median(lat)), max=round(max(lat)))
    # the talking spans: how long the engine held the story for each claimed line
    talk = [(t, v) for t, n, v in smp.changes if n == "#talking"]
    spans, start = [], None
    for t, v in talk:
        if v == 1:
            start = t
        elif start is not None:
            spans.append(round(t - start, 2))
            start = None
    out["talking_spans_s"] = spans
    bridge_lines = [l for _, l in b.lines if re.search(r"\[cue \d+\]", l)]
    out["bridge_log"] = bridge_lines
    lat_ticks = []
    for l in b.lines:
        pass
    if kill:
        after = [(t, n, v) for t, n, v in smp.changes if t > (killed["t"] or 1e18)]
        release = next((t for t, n, v in after if n == "#talking" and v == 0), None)
        hb0 = next((t for t, n, v in after if n == "#bridge_hb" and v == 0), None)
        nxt_line = next((t for t, n, v in after if n == "#line" and v and v != killed.get("line")), None)
        live_after = [(round(t - killed["t"], 2), v) for t, n, v in after if n == "#live"]
        cue_after = [v for t, n, v in after if n == "#cue_n"]
        out.update(killed=killed["t"] is not None, release_after_kill_s=None if release is None else round(release - killed["t"], 2),
                   expected_remaining_s=None if not killed.get("left") else round(killed["left"] / 20, 2),
                   heartbeat_zero_after_s=None if hb0 is None else round(hb0 - killed["t"], 2),
                   next_line_after_s=None if nxt_line is None else round(nxt_line - killed["t"], 2), live_after=live_after, cue_n_changes_after=cue_after,
                   next_line=None if not nxt_line else [v for t, n, v in after if n == "#line" and v and v != killed.get("line")][0])
        out["ok"] = bool(killed["t"] and release is not None and release - killed["t"] <= killed["left"] / 20 + 0.6 and
                         (nxt_line is not None) and not [1 for t, n, v in after if n == "#cue_n" and t > (hb0 or 0) + 0.2])
    else:
        # (the last cue may still be waiting for its claim when the test ends)
        out["ok"] = bool(ok and len(cues) >= 8 and len(lat) >= len(cues) - 1 and not [1 for t, n, v in smp.changes if n == "#cue_fb" and v == 1])
    res[name] = out
    log(f"   {name}: cues {out['cues']}, claimed {out['claimed']}, observed cue->ack {out.get('observed_cue_to_ack_ms')} ms, talking spans {spans}")
    if kill:
        log(f"   killed -> story released after {out.get('release_after_kill_s')} s (the claimed length had {out.get('expected_remaining_s')} s to run); heartbeat 0 after "
            f"{out.get('heartbeat_zero_after_s')} s; the next line began {out.get('next_line_after_s')} s after the kill; #cue_n changes after: {out.get('cue_n_changes_after')}")
    b.kill()
    stop_story(srv)


def scenario_bark(srv, res):
    """With the bridge connected a fight bark is still played by the game from its file: instantly, never cued."""
    log("== a fight bark with the bridge connected")
    b = Bridge(srv, ["--verbatim", "--no-asr-check"])
    if not b.wait_for(r"performing the scripted lines silently", 240):
        res["bark"] = dict(ok=False, why="the bridge did not come up")
        b.kill()
        return
    time.sleep(1.0)
    hb = score(srv, "#bridge_hb")
    n0 = score(srv, "#cue_n")
    t0 = time.time()
    srv.cmd("function angel:fight/say/7_04")
    seen = []
    while time.time() - t0 < 12:
        seen.append((round(time.time() - t0, 2), score(srv, "#talking"), score(srv, "#live"), score(srv, "#line")))
        if len(seen) > 3 and seen[-1][1] == 0:
            break
        time.sleep(0.05)
    n1 = score(srv, "#cue_n")
    durs = json.load(open(os.path.join(ROOT, "voices", "durations.json")))
    started = next((t for t, tk, lv, ln in seen if tk == 1), None)
    ended = next((t for t, tk, lv, ln in seen if started is not None and t > started and tk == 0), None)
    span = None if (started is None or ended is None) else round(ended - started, 2)
    res["bark"] = dict(heartbeat=hb, cue_n_before=n0, cue_n_after=n1, started_after_s=started, talking_span_s=span, file_s=durs.get("7.04"),
                       ok=bool(hb and hb > 0 and n0 == n1 and started is not None and started < 0.3 and span is not None and abs(span - durs["7.04"] - 0.2) < 0.4))
    log(f"   bark 7.04: heartbeat {hb}, #cue_n {n0} -> {n1}, #talking began {started} s after the call and lasted {span} s (the file is {durs.get('7.04')} s)")
    b.kill()
    srv.cmd("scoreboard players set #talking angel.story 0")


ANSWERS_S5 = {(5, 64): (3.0, "What is that thing?"), (5, 75): (3.0, "Okay. My father is up there?"), (5, 97): (4.0, "Me? I can't pilot that."),
              (5, 113): (5.0, "I don't know. I'm scared."), (5, 130): (3.0, "Okay. I'll do it.")}


def scenario_cage(srv, steps, res):
    log("== the cage (scene 5) with the bridge and adaptation (look-ahead synthesis)")
    b = Bridge(srv, ["--synth"])
    if not b.wait_for(r"performing the scripted lines silently", 400):
        res["cage"] = dict(ok=False, why="the bridge did not come up")
        b.kill()
        return
    time.sleep(1.0)
    smp = Sampler(srv, ["#cue_n", "#cue_ack", "#talking", "#line", "#live", "#cue_fb", "#line_left", "#wait"])
    smp.start()
    drv = Driver(srv, steps, bridge=b, answers=ANSWERS_S5)
    ok = run_scene(srv, drv, 5, lambda s: s[0] == 5 and s[1] is not None and s[1] >= 205 or (smp.vals.get("#line") == 544), 900)
    smp.stop()
    cues, acks = cue_report(smp, b, srv)
    ack_by_n = {v: t for t, v in acks}
    lat = [(ack_by_n[n] - t) * 1000 for t, n in cues if n in ack_by_n]
    bl = [l for _, l in b.lines if re.search(r"\[cue \d+\]", l)]
    res["cage"] = dict(reached=ok, cues=len(cues), claimed=len(lat), takeovers=len([1 for t, n, v in smp.changes if n == "#cue_fb" and v == 1]),
                       observed_cue_to_ack_ms=dict(median=round(statistics.median(lat)), max=round(max(lat))) if lat else None,
                       adapted=[l for l in bl if " adapted " in l], bridge_log=bl, ok=bool(ok and lat and len(lat) >= len(cues) - 1))
    log(f"   cage: reached {ok}; cues {len(cues)} claimed {len(lat)}; adapted lines performed: {len(res['cage']['adapted'])}")
    b.kill()
    stop_story(srv)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="nobridge,bridge,kill,bark,cage")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "cache", "livetest_report.json"))
    a = ap.parse_args()
    which = a.only.split(",")
    steps = json.load(open(os.path.join(HERE, "cache", "steps.json")))
    scr = start_scratch(a.keep)
    srv = make_conn(scr)
    res = {}
    try:
        if "nobridge" in which:
            scenario_nobridge(srv, steps, res)
        if "bridge" in which:
            scenario_bridge(srv, steps, res)
        if "kill" in which:
            scenario_bridge(srv, steps, res, kill=True)
        if "bark" in which:
            scenario_bark(srv, res)
        if "cage" in which:
            scenario_cage(srv, steps, res)
    finally:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        json.dump(res, open(a.out, "w"), indent=1, default=str)
        log("stopping the scratch server ...")
        scr.stop()
        for k, v in res.items():
            print(f"  {k:9} {'PASS' if v.get('ok') else 'FAIL'}")
        print("report:", a.out)


if __name__ == "__main__":
    main()
