"""Microphone -> one utterance at a time (Silero VAD) -> text (faster-whisper). Same approach as Genesis."""
import os
import queue

from config import SETTINGS

MIC_SR, VAD_BLOCK = 16000, 512
NOISE = {"", "you", ".", "so", "thanks for watching!", "thank you for watching.", "thanks for watching.", "bye."}


class Ears:
    def __init__(self, device=None):
        import numpy as np  # noqa: F401
        import sounddevice as sd
        import torch
        from silero_vad import load_silero_vad

        lib = os.path.join(os.path.dirname(torch.__file__), "lib")
        os.add_dll_directory(lib)
        os.environ["PATH"] = lib + os.pathsep + os.environ["PATH"]
        from faster_whisper import WhisperModel

        self.torch, self.vad, self.threshold = torch, load_silero_vad(), SETTINGS["vad_threshold"]
        self.silence_blocks = int(SETTINGS["silence_s"] / (VAD_BLOCK / MIC_SR))
        self.blocks = queue.Queue()
        self.deaf = False                       # while a character is speaking, so they do not hear themselves
        self.stt = WhisperModel(SETTINGS["stt_model"], device="cuda", compute_type="float16")
        self._transcribe(__import__("numpy").zeros(MIC_SR, dtype="float32"))     # warm up
        self.stream = sd.InputStream(samplerate=MIC_SR, channels=1, dtype="float32", blocksize=VAD_BLOCK, device=device,
                                     callback=lambda data, *_: None if self.deaf else self.blocks.put(data[:, 0].copy()))
        self.stream.start()

    def _transcribe(self, audio):
        segs, _ = self.stt.transcribe(audio, language="en", beam_size=3, condition_on_previous_text=False,
                                      initial_prompt=SETTINGS["stt_prompt"])
        kept = [s.text.strip() for s in segs if not (s.no_speech_prob > 0.6 and s.avg_logprob < -1.0)]
        text = " ".join(kept).strip()
        if text.lower() == SETTINGS["stt_prompt"].lower().strip():
            return ""
        return text

    def flush(self):
        while not self.blocks.empty():
            self.blocks.get_nowait()
        self._reset = True          # the listening thread resets the detector itself: two threads in it at once corrupt its state

    def listen(self):
        import numpy as np

        pre, speech, silent, speaking = [], [], 0, False
        while True:
            block = self.blocks.get()
            if getattr(self, "_reset", False):
                self._reset = False
                self.vad.reset_states()
                pre, speech, silent, speaking = [], [], 0, False
            try:
                prob = self.vad(self.torch.from_numpy(block), MIC_SR).item()
            except RuntimeError:        # a corrupted detector state must not end the session
                self.vad.reset_states()
                continue
            if not speaking:
                pre = (pre + [block])[-10:]
                if prob >= self.threshold:
                    speaking, speech, silent = True, list(pre), 0
                continue
            speech.append(block)
            silent = 0 if prob >= self.threshold else silent + 1
            if silent >= self.silence_blocks:
                self.vad.reset_states()
                if (len(speech) - silent) * VAD_BLOCK / MIC_SR >= 0.3:
                    text = self._transcribe(np.concatenate(speech))
                    if text.lower() not in NOISE:
                        return text
                pre, speech, silent, speaking = [], [], 0, False
