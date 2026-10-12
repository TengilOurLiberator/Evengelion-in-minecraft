"""Shinji can talk to Misato, Ritsuko, Gendo and Rei at any time: microphone -> Claude -> voice, gated by the story.  And the bridge performs the
characters' SCRIPTED lines too: when the story reaches one it is cued over RCON, the bridge speaks it in the character's TTS voice (re-voiced a
little by Claude where the policy allows), and the story waits until it has been said.

    D:\\voice-assistant\\.venv\\Scripts\\python.exe bridge.py             live: microphone, voices, the game server (RCON)
    D:\\voice-assistant\\.venv\\Scripts\\python.exe bridge.py --text      terminal only: typed lines, printed replies, a fake server
    D:\\voice-assistant\\.venv\\Scripts\\python.exe bridge.py --text --live   typed lines, but against the real server (the scripted lines are performed silently)
    D:\\voice-assistant\\.venv\\Scripts\\python.exe bridge.py --story-test    scenes 1-6 through a fake game: cues, answers, real synthesis, a report per line

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
    ap.add_argument("--mute", action="store_true", help="microphone and game, but do not speak (replies print and show in game chat; the scripted lines are claimed and timed, silently)")
    ap.add_argument("--input", help="microphone: device index or part of its name (default: system default)")
    ap.add_argument("--output", help="speakers: device index or part of its name, e.g. 'Oculus' (default: system default)")
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--model", help=f"Claude model for the characters (default {SETTINGS['model']}; env ANGEL_MODEL)")
    ap.add_argument("--stt-model", help="faster-whisper model (default %s)" % SETTINGS["stt_model"])
    ap.add_argument("--fresh", action="store_true", help="forget earlier conversations (state.json)")
    ap.add_argument("--no-subtitles", action="store_true", help="do not tellraw the spoken sentences to the game chat")
    ap.add_argument("--talk-wait", type=float,
                    help="seconds to hold an utterance while a recorded line plays (default %.0f; text mode 1)" % SETTINGS["talk_wait"])
    ap.add_argument("--verbose", action="store_true", help="print every RCON command and answer")
    # the scripted lines
    ap.add_argument("--verbatim", action="store_true", help="speak every scripted line exactly as written (no Claude re-voicing at all); the pre-rendered takes play")
    ap.add_argument("--no-lines", action="store_true", help="do not perform the scripted lines (no heartbeat): the game plays its pre-rendered files, as when the bridge is not running")
    ap.add_argument("--dry", action="store_true", help="the scratch-server variant of the story (build_story.py --dry): a mannequin tagged angel.testplayer is the player")
    ap.add_argument("--synth", action="store_true", help="with --text --live: load the voices so adapted lines are synthesised (otherwise only the pre-rendered takes are performed)")
    ap.add_argument("--no-asr-check", action="store_true", help="do not transcribe adapted takes back to check them")
    ap.add_argument("--one-model", action="store_true", help="use one Chatterbox for replies and look-ahead (less GPU memory; a reply can wait behind a look-ahead line)")
    ap.add_argument("--steps", help="the story's step listing (default cache\\steps.json, rebuilt when the story's sources are newer)")
    # the self-test
    ap.add_argument("--story-test", action="store_true", help="run scenes 1-6 through a fake game with scripted answers and real synthesis; print a report per line")
    ap.add_argument("--test-scenes", default="1,2,3,4,5,6")
    ap.add_argument("--test-speed", type=float, default=1.0, help="speed of the fake game's clock (1 = real time; the synthesis does not speed up)")
    ap.add_argument("--test-cap", type=float, default=4.0, help="longest a step that is not a spoken line is allowed to take in the fake game, seconds")
    ap.add_argument("--test-report", help="write the report here as JSON (default cache\\story_test_report.json)")
    ap.add_argument("--story-report", help="print the report of an earlier --story-test from its JSON file and exit")
    # (start.ps1 launches the bridge without options: `$env:ANGEL_BRIDGE_ARGS = "--verbatim"` before .\start.ps1 adds them)
    return ap.parse_args(sys.argv[1:] + os.environ.get("ANGEL_BRIDGE_ARGS", "").split())


def report_sources(beats):
    import characters as ch
    for c in CHARACTERS:
        found = ch.sheet_text(c)[1]
        print("   %-8s %s" % (NAMES[c] + ":", "character sheet found" if found else "PLACEHOLDER (no characters\\%s.md yet)" % c))
    print("   beats table: %d entries" % len(beats) if beats else "   beats table: none (characters\\beats.md not found)")


def start_minds(model, adapter=False):
    """Start and warm one Claude per character plus the consent classifier (and the line editor), in parallel."""
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

    prompts = [(c, ch.system_prompt(c)) for c in CHARACTERS] + [("classifier", ch.CLASSIFIER_PROMPT)]
    if adapter:
        import adapter as adapt_mod
        prompts.append(("adapter", adapt_mod.system_prompt()))
    threads = [threading.Thread(target=make, args=p) for p in prompts]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errors:
        sys.exit("Could not start Claude: " + "; ".join(errors))
    return {c: minds[c] for c in CHARACTERS}, minds["classifier"], minds.get("adapter")


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


# ---------------------------------------------------------------------------------------------------------------- the scripted lines
class Performance:
    """Everything that performs the scripted lines: book, step listing, look-ahead, conductor; built once the minds and the voices exist."""

    def __init__(self, args, rcon_cue, rcon_watch, mixer, memory, adapter_brain, synth, ears=None, subtitles=True, log=print, pause=None):
        from conductor import Conductor
        from prepare import Preparer
        from storybook import Book, Story, load_steps
        self.ears = ears
        self.book = Book()
        steps = load_steps(args.steps, rebuild=False, log=log) if args.steps else load_steps(log=log)
        self.story = Story(steps)
        self.prep = Preparer(self.book, synth=None if args.verbatim else synth, brain=None if args.verbatim else adapter_brain,
                             asr_check=not args.no_asr_check, verbatim_only=args.verbatim, log=log)
        self.prep.pause = pause
        self.holder = {}
        self.conductor = Conductor(rcon_cue, self.book, self.story, self.prep, mixer, memory, on_line_start=self._line_start, subtitles=subtitles, log=log,
                                   verbose=args.verbose)
        self.rcon_watch = rcon_watch
        n_adapt = sum(1 for ln in self.book.human() if not ln.verbatim)
        how = "every line verbatim (--verbatim)" if args.verbatim else f"{n_adapt} of {len(self.book.human())} adaptable, the rest verbatim"
        takes = "found" if self.book.verbatim_wav("2.01") is not None else "MISSING (run tools\\voices\\tts_lines.py install)"
        log(f"   scripted lines: {how}; pre-rendered takes {takes}")

    def _line_start(self, ln, dur):
        d = self.holder.get("director")
        if d is not None and d.out.busy:
            d.out.abort()                                  # a reply being spoken gives way to the scripted line
        if self.ears is not None:
            self.ears.deaf = True
            threading.Timer(dur + 0.25, self._undeaf).start()

    def _undeaf(self):
        if self.ears is not None and not self.conductor.line_playing():
            self.ears.deaf = False
            self.ears.flush()

    def start(self):
        self.conductor.start(self.rcon_watch)
        self.conductor.replan(force=True)


def run_text(args):
    import characters as ch
    from director import Director
    from output import TextOutput
    from playback import NullMixer
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
    perform = bool(args.live and not args.no_lines)
    brains, classifier, adapter_brain = start_minds(args.model, adapter=perform and not args.verbatim)
    print(f"   ready in {time.time() - t0:.1f}s")
    perf = None
    if perform:
        from rcon_client import ReconnectingRcon
        synth = None
        if args.synth and not args.verbatim:
            import storybook  # noqa: F401  (puts tools\voices on the path)
            import tts_lib
            synth = tts_lib.Synth()
        perf = Performance(args, rcon, rcon, NullMixer(), memory, adapter_brain, synth, subtitles=SETTINGS["subtitles"])      # ONE RCON connection for everything (see rcon_commands.parse_score)
        perf.start()
        print("   performing the scripted lines silently (heartbeat on)")
    director = Director(world, brains, classifier, TextOutput(), memory, beats,
                        talk_wait=args.talk_wait if args.talk_wait is not None else 1.0, conductor=perf.conductor if perf else None)
    if perf:
        perf.holder["director"] = director
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
        if perf:
            perf.conductor.stop()
        shutdown()


def run_live(args):
    import characters as ch
    from director import Director
    from output import TextOutput, VoiceOutput
    from playback import Mixer, NullMixer, Player
    from rcon_client import ReconnectingRcon
    from voice import VoiceBank, find_device
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
    perform = not args.no_lines
    mind = threading.Thread(target=lambda: holder.update(zip(("brains", "classifier", "adapter"),
                                                              start_minds(args.model, adapter=perform and not args.verbatim))))
    mind.start()
    bank = prep_synth = None
    if not args.mute:
        print("   loading voices ...", flush=True)
        bank = VoiceBank()
        for c in CHARACTERS:
            print("   %-8s %s" % (NAMES[c] + ":", bank.source[c]))
        if perform and not args.verbatim:
            if args.one_model:
                prep_synth = bank.engine
            else:
                import tts_lib
                prep_synth = tts_lib.Synth()
    print("   loading the microphone listener ...", flush=True)
    from ears import Ears
    ears = Ears(in_dev)
    mind.join()
    mixer = NullMixer() if args.mute else Mixer(out_dev)
    out = VoiceOutput(bank, Player(mixer), ears) if bank else TextOutput()
    perf = None
    if perform:
        perf = Performance(args, world.rcon, world.rcon, mixer, memory, holder["adapter"], prep_synth, ears=ears,
                           subtitles=SETTINGS["subtitles"], pause=bank.busy if bank else None)
    director = Director(world, holder["brains"], holder["classifier"], out, memory, beats, talk_wait=args.talk_wait,
                        conductor=perf.conductor if perf else None)
    if perf:
        perf.holder["director"] = director
        perf.start()
    print(f"All warm in {time.time() - t0:.0f}s. Shinji, speak when you like."
          + (" The scripted lines are performed by the bridge." if perf else " (--no-lines: the game plays its own files.)"), flush=True)

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
        if perf:
            perf.conductor.stop()
        shutdown()


def main():
    args = parse_args()
    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        return
    if args.model:
        SETTINGS["model"] = args.model
    if args.stt_model:
        SETTINGS["stt_model"] = args.stt_model
    if args.no_subtitles:
        SETTINGS["subtitles"] = False
    if args.dry:
        import rcon_commands as rc
        rc.use_dry()
    if args.story_report:
        import story_test
        story_test.reprint(args.story_report)
        return
    if args.story_test:
        import story_test
        story_test.run(args)
        return
    (run_text if args.text else run_live)(args)


if __name__ == "__main__":
    main()
