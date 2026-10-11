"""Shinji can talk to Misato, Ritsuko, Gendo and Rei at any time: microphone -> Claude -> voice, gated by the story.

    D:\\voice-assistant\\.venv\\Scripts\\python.exe bridge.py             live: microphone, voices, the game server (RCON)
    D:\\voice-assistant\\.venv\\Scripts\\python.exe bridge.py --text      terminal only: typed lines, printed replies, a fake server
    D:\\voice-assistant\\.venv\\Scripts\\python.exe bridge.py --text --live   typed lines, but against the real server

See README.md. All game commands are in rcon_commands.py.
"""
import argparse
import os
import sys
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import config  # noqa: E402  (sets HF_HOME)
from config import CHARACTERS, NAMES, SETTINGS  # noqa: E402

sys.stdout.reconfigure(line_buffering=True, encoding="utf-8", errors="replace")

HELP = """\
Type what Shinji says. Lines starting with / change the fake world:
  /beat N                    set #beat
  /wait 0|1|2                0 nothing, 1 story holds for any answer, 2 story holds for agreement to pilot
  /speaker misato|...        set #speaker (who asked)
  /present misato 0|1|2      0 absent, 1 in person, 2 voice only   (also: /present all 1)
  /talking 0|1               1 = a recorded line is playing (the next utterance is held, then dropped)
  /look misato|away          turn Shinji's head toward a character, or away
  /place misato DIST [DEG]   put a character DIST blocks away, DEG degrees to the left of where Shinji faces
  /line misato Some words    a recorded line by that character was just heard (they all overhear it)
  /state   /forget   /help   /quit"""


def parse_args():
    ap = argparse.ArgumentParser(description="Live conversation bridge for the characters of Angel Attack.")
    ap.add_argument("--text", action="store_true", help="no microphone, no TTS; a fake RCON unless --live")
    ap.add_argument("--live", action="store_true", help="with --text: talk to the real server instead of the fake one")
    ap.add_argument("--script", help="with --text: lines separated by | (also / commands), run them, then exit")
    ap.add_argument("--mute", action="store_true", help="microphone and game, but do not speak (replies print and show in chat)")
    ap.add_argument("--input", help="microphone: device index or part of its name (default: system default)")
    ap.add_argument("--output", help="speakers: device index or part of its name, e.g. 'Oculus' (default: system default)")
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--model", help=f"Claude model for the characters (default {SETTINGS['model']}; env ANGEL_MODEL)")
    ap.add_argument("--tts", choices=["turbo", "standard"], help="Chatterbox model (default turbo)")
    ap.add_argument("--stt-model", help="faster-whisper model (default %s)" % SETTINGS["stt_model"])
    ap.add_argument("--fresh", action="store_true", help="forget earlier conversations (state.json)")
    ap.add_argument("--no-subtitles", action="store_true", help="do not tellraw the spoken sentences to the game chat")
    ap.add_argument("--talk-wait", type=float,
                    help="seconds to hold an utterance while a recorded line plays (default %.0f; text mode 1)" % SETTINGS["talk_wait"])
    ap.add_argument("--verbose", action="store_true", help="print every RCON command and answer")
    return ap.parse_args()


def report_sources(beats):
    import characters as ch
    for c in CHARACTERS:
        found = ch.sheet_text(c)[1]
        print("   %-8s %s" % (NAMES[c] + ":", "character sheet found" if found else "PLACEHOLDER (no characters\\%s.md yet)" % c))
    print("   beats table: %d entries" % len(beats) if beats else "   beats table: none (characters\\beats.md not found)")


def start_minds(model):
    """Start and warm one Claude per character plus the consent classifier, in parallel."""
    import characters as ch
    from brain import Brain
    minds, errors = {}, []

    def make(key, prompt):
        try:
            b = Brain(key, prompt, model=model)
            b.warm()
            minds[key] = b
        except Exception as e:
            errors.append(f"{key}: {e}")

    threads = [threading.Thread(target=make, args=(c, ch.system_prompt(c))) for c in CHARACTERS]
    threads.append(threading.Thread(target=make, args=("classifier", ch.CLASSIFIER_PROMPT)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errors:
        sys.exit("Could not start Claude: " + "; ".join(errors))
    return {c: minds[c] for c in CHARACTERS}, minds["classifier"]


def control(line, fake, director, memory):
    """A /command in text mode. Returns False to quit."""
    import rcon_commands as rc
    parts = line[1:].split()
    if not parts:
        return True
    cmd, args = parts[0].lower(), parts[1:]
    try:
        if cmd in ("quit", "exit", "q"):
            return False
        if cmd == "help":
            print(HELP)
        elif cmd == "beat":
            fake.set_score(rc.SCORE_BEAT, int(args[0]))
        elif cmd == "wait":
            fake.set_score(rc.SCORE_WAIT, int(args[0]))
        elif cmd == "speaker":
            fake.set_score(rc.SCORE_SPEAKER, CHARACTERS.index(args[0]) + 1 if args[0] in CHARACTERS else 0)
        elif cmd == "talking":
            fake.set_score(rc.SCORE_TALKING, int(args[0]))
        elif cmd == "present":
            for c in (CHARACTERS if args[0] == "all" else [args[0]]):
                fake.set_score(rc.score_present(c), int(args[1]))
        elif cmd == "look":
            fake.look_away() if args[0] == "away" else fake.look_at(args[0])
        elif cmd == "place":
            fake.place(args[0], float(args[1]), float(args[2]) if len(args) > 2 else 0.0)
        elif cmd == "line":
            who, words = args[0], " ".join(args[1:])
            memory.recorded_line(who, words or None)
            print(f"   (recorded line by {NAMES[who]}: {words})")
        elif cmd == "forget":
            memory.clear()
            print("   (memory cleared)")
        elif cmd == "state":
            print("  ", director.world.snapshot().describe())
            for c in CHARACTERS:
                print(f"   {c}: pos={['%.1f' % v for v in fake.pos[c]]}")
            print(f"   player yaw={fake.yaw:.0f} pitch={fake.pitch:.0f}; last speaker: {memory.last_speaker}")
        else:
            print("unknown command; /help")
    except (IndexError, ValueError, KeyError) as e:
        print(f"bad command ({e.__class__.__name__}); /help")
    return True


def shutdown():
    try:
        from brain import close_all
        close_all()
    except Exception:
        pass
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)           # the Claude processes and reader threads are daemons; do not wait on them


def run_text(args):
    import characters as ch
    from director import Director
    from output import TextOutput
    from world import World

    if args.live:
        from rcon_client import ReconnectingRcon
        rcon, fake = ReconnectingRcon(), None
    else:
        from fake_rcon import FakeRcon
        rcon = fake = FakeRcon()
    world = World(rcon, verbose=args.verbose)
    memory = ch.Memory()
    if not args.fresh:
        memory.load(world.score("#beat"))
    beats = ch.load_beats()
    report_sources(beats)
    print(f"   starting Claude ({SETTINGS['model']}) ...", flush=True)
    t0 = time.time()
    brains, classifier = start_minds(args.model)
    print(f"   ready in {time.time() - t0:.1f}s")
    director = Director(world, brains, classifier, TextOutput(), memory, beats,
                        talk_wait=args.talk_wait if args.talk_wait is not None else 1.0)
    if fake:
        print("Fake server. " + HELP)
    lines = iter(args.script.split("|")) if args.script else None
    try:
        while True:
            if lines is not None:
                line = next(lines, None)
                if line is None:
                    break
                line = line.strip()
                print(f"\nShinji> {line}")
            else:
                try:
                    line = input("\nShinji> ").strip()
                except EOFError:
                    break
            if not line:
                continue
            if line.startswith("/"):
                if not fake and line.split()[0] not in ("/quit", "/help", "/forget", "/line"):
                    print("   (world commands only work on the fake server; run without --live)")
                    continue
                if not control(line, fake, director, memory):
                    break
                continue
            director.handle(line)
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        shutdown()


def run_live(args):
    import characters as ch
    from director import Director
    from output import TextOutput, VoiceOutput
    from rcon_client import ReconnectingRcon
    from voice import Player, VoiceBank, find_device
    from world import World

    in_dev, out_dev = find_device(args.input, "input"), find_device(args.output, "output")
    world = World(ReconnectingRcon(), verbose=args.verbose)
    print("Connected to the server.")
    memory = ch.Memory()
    if not args.fresh:
        print("   resumed earlier conversations." if memory.load(world.score("#beat")) else "   starting with a clean memory.")
    beats = ch.load_beats()
    report_sources(beats)

    t0 = time.time()
    holder = {}
    mind = threading.Thread(target=lambda: holder.update(zip(("brains", "classifier"), start_minds(args.model))))
    mind.start()
    bank = None
    if not args.mute:
        print("   loading voices ...", flush=True)
        bank = VoiceBank(SETTINGS["tts_engine"])
        for c in CHARACTERS:
            print("   %-8s %s" % (NAMES[c] + ":", bank.source[c]))
    print("   loading the microphone listener ...", flush=True)
    from ears import Ears
    ears = Ears(in_dev)
    mind.join()
    out = VoiceOutput(bank, Player(out_dev), ears) if bank else TextOutput()
    director = Director(world, holder["brains"], holder["classifier"], out, memory, beats, talk_wait=args.talk_wait)
    print(f"All warm in {time.time() - t0:.0f}s. Shinji, speak when you like.", flush=True)

    def watch():
        while True:
            time.sleep(SETTINGS["poll_s"])
            try:
                director.observe(*world.watch())
            except Exception:
                pass
    threading.Thread(target=watch, daemon=True).start()

    try:
        while True:
            text = ears.listen()
            print(f"\nShinji: {text}", flush=True)
            director.handle(text)
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        shutdown()


def main():
    args = parse_args()
    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        return
    if args.model:
        SETTINGS["model"] = args.model
    if args.tts:
        SETTINGS["tts_engine"] = args.tts
    if args.stt_model:
        SETTINGS["stt_model"] = args.stt_model
    if args.no_subtitles:
        SETTINGS["subtitles"] = False
    (run_text if args.text else run_live)(args)


if __name__ == "__main__":
    main()
