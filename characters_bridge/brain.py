"""Claude as the characters' minds: long-lived headless Claude Code processes (same login and method as Genesis).

One process per character plus one for the consent classifier, started and warmed at launch so the first
reply is not a cold start. Each turn's message is self-contained (beat, memory, shared log), so a process's own
history is never relied on and each one is quietly replaced by a fresh one every `recycle_turns` turns.
Replies are streamed so the first sentence can be voiced while the rest is still being written.
"""
import json
import os
import queue
import subprocess
import threading
import time

from config import CACHE_DIR, CLAUDE_EXE, SETTINGS


class BrainError(RuntimeError):
    pass


_ALL = []


def close_all():
    for b in _ALL:
        b.close()


class _Proc:
    def __init__(self, system_prompt, model, effort):
        if not os.path.exists(CLAUDE_EXE):
            raise BrainError("Claude Code is not installed at " + CLAUDE_EXE)
        cwd = os.path.join(CACHE_DIR, "claude_cwd")          # an empty folder: nothing of ours leaks into the prompt
        os.makedirs(cwd, exist_ok=True)
        cmd = [CLAUDE_EXE, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
               "--include-partial-messages", "--model", model, "--system-prompt", system_prompt,
               "--no-session-persistence", "--exclude-dynamic-system-prompt-sections", "--disable-slash-commands",
               "--strict-mcp-config", "--mcp-config", json.dumps({"mcpServers": {}}), "--tools", ""]
        if effort:
            cmd += ["--effort", effort]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                  encoding="utf-8", bufsize=1, cwd=cwd, env={**os.environ, "MAX_THINKING_TOKENS": "0",
                                       # without this Claude Code makes a background "post-turn summary" call after every
                                       # reply and will not read the next message until it is done (up to ~1-5 s)
                                       "CLAUDE_CODE_CLASSIFIER_SUMMARY": "0"})
        self.events = queue.Queue()
        self.owed = 0                       # turns whose final 'result' line has not been read yet
        self.turns = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            for line in self.p.stdout:
                try:
                    self.events.put(json.loads(line))
                except ValueError:
                    pass
        finally:
            self.events.put(None)           # EOF

    def alive(self):
        return self.p.poll() is None

    def kill(self):
        try:
            self.p.kill()
        except OSError:
            pass


class Brain:
    def __init__(self, name, system_prompt, model=None, effort=None, recycle=None):
        self.name, self.system_prompt = name, system_prompt
        self.model = model or SETTINGS["model"]
        self.effort = SETTINGS["effort"] if effort is None else effort
        self.recycle = recycle or SETTINGS["recycle_turns"]
        self.lock = threading.Lock()        # one turn at a time per mind
        self.proc = _Proc(system_prompt, self.model, self.effort)
        self.spare = None
        _ALL.append(self)

    # ---- lifecycle ----
    def warm(self):
        """One throwaway turn so the process, the connection and the model are hot."""
        try:
            for _ in self.stream("Reply with the single word: ready"):
                pass
        except BrainError:
            pass

    def _fresh(self):
        old, self.proc = self.proc, (self.spare or _Proc(self.system_prompt, self.model, self.effort))
        self.spare = None
        old.kill()

    def _prepare_spare(self):
        if self.spare is None:
            def go():
                try:
                    self.spare = _Proc(self.system_prompt, self.model, self.effort)
                except BrainError:
                    pass
            threading.Thread(target=go, daemon=True).start()

    # ---- turns ----
    def stream(self, text):
        """Yield the reply's text in chunks as it is written. Abandoning the generator is safe."""
        with self.lock:
            if not self.proc.alive() or self.proc.turns >= self.recycle:
                self._fresh()
            elif self.proc.turns >= self.recycle - 2:
                self._prepare_spare()
            pr = self.proc
            pr.turns += 1
            try:
                pr.p.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
                pr.p.stdin.flush()
            except OSError as e:
                pr.kill()
                raise BrainError(f"{self.name}: cannot reach Claude ({e})")
            skip = pr.owed                  # still-unread tail of an earlier, early-finished turn
            pr.owed += 1
            deadline = SETTINGS["claude_timeout"]
            while True:
                try:
                    ev = pr.events.get(timeout=deadline)
                except queue.Empty:
                    pr.kill()
                    raise BrainError(f"{self.name}: Claude did not answer within {deadline:.0f}s")
                if ev is None:
                    raise BrainError(f"{self.name}: Claude closed unexpectedly")
                kind = ev.get("type")
                if kind == "result":
                    pr.owed -= 1
                    if skip:
                        skip -= 1
                        continue
                    if ev.get("is_error"):
                        raise BrainError(f"{self.name}: {ev.get('result')}")
                    return
                if skip:
                    continue
                if kind == "stream_event":
                    e = ev.get("event", {})
                    d = e.get("delta", {})
                    if e.get("type") == "content_block_delta" and d.get("type") == "text_delta":
                        yield d["text"]
                    elif e.get("type") == "message_stop":
                        # The tail ('post_turn_summary', 'result') can take a second; do not wait for it. The next
                        # turn skips it (owed), so the caller gets the reply the moment the text is complete.
                        return

    def ask(self, text):
        return "".join(self.stream(text)).strip()

    def close(self):
        for pr in (self.proc, self.spare):
            if pr:
                try:
                    pr.p.stdin.close()
                except OSError:
                    pass
                pr.kill()


def classify_consent(brain, utterance, context=""):
    """-> 'consent' | 'refusal' | 'other' (one cheap call)."""
    msg = (context + "\n" if context else "") + f'Shinji said: "{utterance}"\nOne word:'
    word = brain.ask(msg).lower()
    for w in ("consent", "refusal", "other"):
        if w in word:
            return w
    return "other"
