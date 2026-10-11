"""Where a character's reply goes: the terminal (text mode) or speakers (voice mode). Both take a stream of sentences."""
import queue
import threading
import time

from config import NAMES


class TextOutput:
    """No audio: print each sentence as it arrives."""
    busy = False

    def speak(self, who, sentence_iter, presence, on_sentence=None, t0=None):
        spoken, t0 = [], t0 or time.time()
        for s in sentence_iter:
            print(f"{NAMES[who].upper():>8}{' (radio)' if presence == 2 else ''}: {s}   [+{time.time() - t0:.1f}s]", flush=True)
            if on_sentence:
                on_sentence(who, s)
            spoken.append(s)
        return spoken

    def abort(self):
        pass


class VoiceOutput:
    """Synthesise sentence by sentence on one thread while the previous sentence is still playing on another."""

    def __init__(self, bank, player, ears=None):
        self.bank, self.player, self.ears = bank, player, ears
        self.aborted = threading.Event()
        self.busy = False

    def abort(self):
        self.aborted.set()
        self.player.stop()

    def speak(self, who, sentence_iter, presence, on_sentence=None, t0=None):
        t0 = t0 or time.time()
        self.aborted.clear()
        self.busy = True
        if self.ears:
            self.ears.deaf = True
        ready, spoken = queue.Queue(maxsize=2), []

        def synth():
            try:
                for s in sentence_iter:
                    if self.aborted.is_set():
                        break
                    ready.put((s, self.bank.synth(who, s, presence), time.time()))
            except Exception as e:                           # a TTS or Claude failure must not hang playback
                print(f"   [voice] {e.__class__.__name__}: {e}", flush=True)
            finally:
                ready.put(None)

        threading.Thread(target=synth, daemon=True).start()
        first = True
        try:
            while True:
                item = ready.get()
                if item is None:
                    break
                s, wav, made = item
                if self.aborted.is_set():
                    continue
                print(f"{NAMES[who].upper():>8}{' (radio)' if presence == 2 else ''}: {s}   [first audio +{time.time() - t0:.1f}s]" if first
                      else f"{'':>8}  {s}", flush=True)
                first = False
                if on_sentence:
                    on_sentence(who, s)
                self.player.play(wav, self.bank.sr)
                if not self.aborted.is_set():
                    spoken.append(s)
        finally:
            self.busy = False
            if self.ears:
                self.ears.deaf = False
                self.ears.flush()
        if self.aborted.is_set():
            print("   (interrupted by a recorded line)", flush=True)
        return spoken
