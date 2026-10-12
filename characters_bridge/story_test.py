"""bridge.py --story-test: scenes 1-6 through a FAKE GAME, with no game running.

The fake game (storysim.py) cues every scripted line of the character in the order of the step listing, exactly as the datapack's handshake does; a
scripted "player" answers at the waits; the real Director answers him with real Claude replies, spoken (synthesised for real, played to a null sound
card); the bridge's conductor looks ahead, asks Claude to re-voice the adaptable lines, synthesises them on the second Chatterbox and performs every
cue.  At the end: a report per line (verbatim or adapted, the script text beside what was said, synthesis time, how far ahead of its cue it was ready,
its duration, the fallback if any) and the numbers of the handshake (cue to audio, claim round trips, takeovers by the game).

What is shortened: every step that is not a spoken line (a walk, a ride, a fade) takes at most --test-cap seconds (4 by default).  The real story has
tens of seconds there, so the margins measured here are the harsh ones.
"""
import json
import os
import statistics
import sys
import threading
import time

import characters as ch
from config import CHARACTERS, NAMES, SETTINGS


def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(round((len(v) - 1) * p)))] if v else 0.0


def run(args):
    import storybook
    import tts_lib
    from bridge import Performance, start_minds
    from director import Director
    from output import VoiceOutput
    from playback import NullMixer, Player
    from storysim import DEFAULT_SCRIPT, FakeGame, Walker
    from voice import VoiceBank
    from world import World

    scenes = [int(v) for v in args.test_scenes.split(",")]
    book = storybook.Book()
    t0 = time.time()
    print(f"story test: scenes {scenes}, clock x{args.test_speed:g}, steps that are not lines capped at {args.test_cap:g}s"
          + ("  [--verbatim: no adaptation]" if args.verbatim else ""))
    beats = ch.load_beats()
    holder = {}
    mind = threading.Thread(target=lambda: holder.update(zip(("brains", "classifier", "adapter"), start_minds(args.model, adapter=not args.verbatim))))
    mind.start()
    print("   loading the voices (replies) ...", flush=True)
    bank = VoiceBank()
    prep_synth = None
    if not args.verbatim:
        print("   loading the voices (look-ahead) ...", flush=True)
        prep_synth = bank.engine if args.one_model else tts_lib.Synth()
    mind.join()
    print(f"   everything warm in {time.time() - t0:.0f}s")

    game = FakeGame(book, speed=args.test_speed)
    mixer = NullMixer(speed=args.test_speed)
    memory = ch.Memory(path=os.path.join(config_cache(), "story_test_state.json"))
    memory.clear()
    world = World(game)
    perf = Performance(args, game, game, mixer, memory, holder["adapter"], prep_synth, subtitles=False, pause=bank.busy)
    director = Director(world, holder["brains"], holder["classifier"], VoiceOutput(bank, Player(mixer), None), memory, beats, talk_wait=2.0,
                        conductor=perf.conductor)
    perf.holder["director"] = director
    for c in CHARACTERS:                                       # who is where, as the story would have set it
        game.set_score(f"#present_{c}", 1)
    game.set_score("#beat", 20)
    steps_scene = {k: v for k, v in perf.story.steps.items()}
    perf.start()
    # the beats of the story, for the characters' prompts: approximate (the walker does not run the scenes' own do-steps)
    BEAT = {1: 11, 2: 20, 3: 30, 4: 40, 5: 50, 6: 60}

    def watcher():
        while not game.stop_ev.is_set():
            time.sleep(SETTINGS["poll_s"])
            try:
                sc = game.scores.get("#scene", 0)
                if sc in BEAT and game.scores.get("#beat") != BEAT[sc]:
                    game.set_score("#beat", BEAT[sc])
                director.observe(*world.watch())
            except Exception:
                pass
    threading.Thread(target=watcher, daemon=True).start()

    walker = Walker(game, perf.story, scenes, DEFAULT_SCRIPT, director=director, cap=args.test_cap, silent_s=10.0)
    t_run = time.time()
    walker.start()
    walker.done.wait()
    time.sleep(1.5)
    wall = time.time() - t_run
    perf.conductor.stop()

    report(args, perf, game, walker, wall, book)
    if walker.error:
        print(walker.error)
        sys.exit(1)
    os._exit(0)


def config_cache():
    from config import CACHE_DIR
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_DIR


def report(args, perf, game, walker, wall, book):
    rows = sorted(perf.conductor.cue_records, key=lambda r: r["cue"])
    out = args.test_report or os.path.join(config_cache(), "story_test_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "events": game.events, "wall_s": wall, "lines_said": len(walker.lines_said), "test_cap": args.test_cap,
                   "speed": args.test_speed}, f, indent=1, default=lambda o: str(o))
    print_report(rows, game.events, len(walker.lines_said), wall, book)
    print(f"report: {out}")


def print_report(rows, events, n_said, wall, book):
    print("\n" + "=" * 118)
    print("PER LINE (as cued, in story order)")
    print("=" * 118)
    n_ad = n_ver = n_fb = 0
    margins, vmargins, starts, claims, claude_s, synth_s = [], [], [], [], [], []
    reasons = {}
    for r in rows:
        ln = book.lines.get(r["line"])
        who = ln.speaker.upper() if ln else "?"
        if r.get("result") != "played":
            n_fb += 1
            print(f"{r['line']:5} {who:8} NOT PLAYED BY THE BRIDGE: {r.get('result')}")
            continue
        kind = r["kind"]
        n_ad += kind == "adapted"
        n_ver += kind != "adapted"
        starts.append(r["cue_to_play_ms"])
        claims.append(r["claim_ms"])
        tag = "ADAPTED " if kind == "adapted" else "verbatim"
        extra = f"  ready {r['ready_margin']:6.1f}s ahead"
        if kind == "adapted":
            margins.append(r["ready_margin"])
            synth_s.append(r.get("synth_s") or 0)
            claude_s.append(r.get("claude_s") or 0)
            extra += f"  [claude {r.get('claude_s')}s, synthesis+check {r.get('synth_s')}s]"
        else:
            vmargins.append(r["ready_margin"])
            if ln and not ln.verbatim:
                why = r.get("adapt_why") or r.get("adapt_status") or r.get("why_not_adapted") or "not asked"
                key = "Claude left it as written" if why == "unchanged" else "re-voiced text was not synthesised in time" if r.get("adapt_status") == "text" else \
                    "Claude's answer was not back in time" if r.get("adapt_status") == "asked" else f"left as written ({why})"
                reasons[key] = reasons.get(key, 0) + 1
                extra += f"  [adaptable; fallback to the pre-rendered take: {key}]"
        print(f"{r['line']:5} {who:8} {tag} {r['dur']:4.1f}s  cue->audio {r['cue_to_play_ms']:3d} ms{extra}")
        if kind == "adapted":
            print(f"        script : {r['script']}\n        spoken : {r['text']}")
        elif r.get("adapt_rec") and r["adapt_rec"].get("adapted"):
            ar = r["adapt_rec"]
            print(f"        script : {r['script']}\n        adapted: {ar['adapted']}   (NOT USED: status {ar.get('status')}, {ar.get('why') or 'the take was not ready at the cue'})")
    print("\n" + "=" * 118)
    print("SUMMARY")
    print("=" * 118)
    print(f"{len(rows)} character lines cued; {n_ad} performed adapted, {n_ver} verbatim, {n_fb} left to the game; the walker said {n_said} lines (incl. BASE and nudges)")
    fbs = [e for e in events if e[1] == "fallback"]
    print(f"takeovers by the game (unclaimed cue): {len(fbs)}" + ("".join(f"\n   {e[0]:7.1f}s {e[2]}" for e in fbs)))
    if starts:
        print(f"cue -> audio start (the bridge's own work; the sound card's latency, 20 ms on WASAPI, is not included): median {statistics.median(starts):.0f} ms, "
              f"p95 {pct(starts, .95):.0f} ms, max {max(starts):.0f} ms  [n={len(starts)}]")
        print(f"   of which the claim and its read-back (2 commands): median {statistics.median(claims):.0f} ms, max {max(claims):.0f} ms")
    if margins:
        print(f"ADAPTED takes were ready this long BEFORE their cue: min {min(margins):.1f}s, median {statistics.median(margins):.1f}s, max {max(margins):.1f}s  [n={len(margins)}]")
        print(f"   Claude {statistics.median(claude_s):.1f}s (max {max(claude_s):.1f}), synthesis + transcript check {statistics.median(synth_s):.1f}s (max {max(synth_s):.1f})")
    if vmargins:
        print(f"verbatim takes were in memory this long before their cue: min {min(vmargins):.1f}s, median {statistics.median(vmargins):.1f}s  [n={len(vmargins)}; 0 = read from disk at the cue, ~ms]")
    adaptable = [r for r in rows if r.get("result") == "played" and book.lines[r["line"]].human and not book.lines[r["line"]].verbatim]
    print(f"adaptable lines cued: {len(adaptable)}; performed re-voiced {sum(1 for r in adaptable if r['kind'] == 'adapted')}; as written: "
          + (", ".join(f"{v} x {k}" for k, v in reasons.items()) or "none"))
    print(f"wall clock {wall / 60:.1f} min")


def reprint(path):
    import storybook
    d = json.load(open(path, encoding="utf-8"))
    print_report(d["rows"], [tuple(e) for e in d["events"]], d.get("lines_said", 0), d.get("wall_s", 0), storybook.Book())