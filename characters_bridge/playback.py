"""One always-open audio output with two voices on it: the scripted LINE and the live REPLY.

Opening a sound stream takes tens to hundreds of milliseconds; the stream here is opened once, at start, and runs for the life of the bridge
(silence when nothing plays), so a scripted line starts within one audio block (about 10-20 ms) of the call.  The line and the reply are
separate slots: stopping a reply (a scripted line is about to start) never touches the line, and the reverse.

`NullMixer` is the same interface without a sound card (tests, --text): `play` returns an event that is set when the clip would have finished.
"""
import threading
import time

import numpy as np

MIX_SR = 48000


def _resample(wav, sr):
    if sr == MIX_SR:
        return np.asarray(wav, dtype=np.float32)
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(MIX_SR, int(sr))
    return resample_poly(np.asarray(wav, dtype=np.float32), MIX_SR // g, int(sr) // g).astype(np.float32)


class _Slot:
    __slots__ = ("wav", "pos", "done")

    def __init__(self, wav):
        self.wav, self.pos, self.done = wav, 0, threading.Event()


class Mixer:
    SLOTS = ("line", "reply")

    def __init__(self, device=None, latency="low"):
        import sounddevice as sd
        self.lock = threading.Lock()
        self.slots = {k: None for k in self.SLOTS}
        self.started_at = {}
        self.stream = None
        # WASAPI (shared mode, converting to the device's rate) starts a sound about 20 ms after it is asked for; the default host API (MME) takes 90 ms
        try:
            apis = sd.query_hostapis()
            wa = next(i for i, h in enumerate(apis) if "WASAPI" in h["name"])
            dev = apis[wa]["default_output_device"] if device is None else device
            if device is not None and sd.query_devices(device)["hostapi"] != wa:
                want = sd.query_devices(device)["name"][:24].lower()
                dev = next((i for i, d in enumerate(sd.query_devices()) if d["hostapi"] == wa and d["max_output_channels"] > 0 and want in d["name"].lower()), dev)
            self.stream = sd.OutputStream(samplerate=MIX_SR, channels=1, dtype="float32", device=dev, latency=latency, callback=self._callback,
                                          extra_settings=sd.WasapiSettings(auto_convert=True))
            self.api = "WASAPI"
        except Exception:
            self.stream = sd.OutputStream(samplerate=MIX_SR, channels=1, dtype="float32", device=device, latency=latency, callback=self._callback)
            self.api = "default"
        self.stream.start()
        self.block_s = (self.stream.latency or 0.02)

    def _callback(self, outdata, frames, time_info, status):
        out = np.zeros(frames, dtype=np.float32)
        with self.lock:
            for name in self.SLOTS:
                s = self.slots[name]
                if s is None:
                    continue
                chunk = s.wav[s.pos:s.pos + frames]
                out[:len(chunk)] += chunk
                s.pos += frames
                if s.pos >= len(s.wav):
                    s.done.set()
                    self.slots[name] = None
        np.clip(out, -1.0, 1.0, out=out)
        outdata[:, 0] = out

    def play(self, name, wav, sr):
        """Start `wav` on slot `name` now (replacing what is there). Returns an Event set when it has been played or stopped."""
        s = _Slot(_resample(wav, sr))
        with self.lock:
            old = self.slots[name]
            self.slots[name] = s
            self.started_at[name] = time.time()
        if old is not None:
            old.done.set()
        return s.done

    def stop(self, name):
        with self.lock:
            s = self.slots[name]
            self.slots[name] = None
        if s is not None:
            s.done.set()

    def playing(self, name):
        with self.lock:
            return self.slots[name] is not None

    def close(self):
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass


class NullMixer:
    """No sound card: a clip 'plays' for its own length (scaled by `speed`) on a timer. `log` collects (time, slot, seconds) for the tests."""

    SLOTS = Mixer.SLOTS

    def __init__(self, speed=1.0):
        self.lock = threading.Lock()
        self.events = {k: None for k in self.SLOTS}
        self.speed = speed
        self.log = []
        self.block_s = 0.0

    def play(self, name, wav, sr):
        done = threading.Event()
        dur = len(wav) / float(sr)
        with self.lock:
            old = self.events[name]
            self.events[name] = done
            self.log.append((time.time(), name, dur))
        if old is not None:
            old.set()

        def finish():
            if not done.wait(dur / self.speed):
                done.set()
            with self.lock:
                if self.events[name] is done:
                    self.events[name] = None

        threading.Thread(target=finish, daemon=True).start()
        return done

    def stop(self, name):
        with self.lock:
            ev = self.events[name]
            self.events[name] = None
        if ev is not None:
            ev.set()

    def playing(self, name):
        with self.lock:
            return self.events[name] is not None and not self.events[name].is_set()

    def close(self):
        pass


class Player:
    """What VoiceOutput plays a reply with: blocking play on the mixer's reply slot, stop() cuts it."""

    def __init__(self, mixer):
        self.mixer = mixer

    def play(self, wav, sr):
        self.mixer.play("reply", wav, sr).wait()

    def stop(self):
        self.mixer.stop("reply")
