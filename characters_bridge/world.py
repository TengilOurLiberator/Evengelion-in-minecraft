"""The bridge's view of the game: reads the story scoreboard and positions, runs the story functions."""
import warnings
from dataclasses import dataclass, field

import rcon_commands as rc
from config import CHARACTERS, IN_PERSON


@dataclass
class State:
    beat: int = 0
    wait: int = 0
    speaker: int = 0                      # 1-4, or 0
    talking: bool = False
    lastspoke: int = 0                    # 1-4, or 0 (optional score)
    present: dict = field(default_factory=lambda: {c: 0 for c in CHARACTERS})

    @property
    def speaker_id(self):
        return CHARACTERS[self.speaker - 1] if 1 <= self.speaker <= len(CHARACTERS) else None

    @property
    def lastspoke_id(self):
        return CHARACTERS[self.lastspoke - 1] if 1 <= self.lastspoke <= len(CHARACTERS) else None

    def describe(self):
        pres = ", ".join(f"{c}={self.present[c]}" for c in CHARACTERS)
        return f"beat={self.beat} wait={self.wait} speaker={self.speaker_id or '-'} talking={int(self.talking)} present[{pres}]"


class World:
    def __init__(self, rcon, verbose=False):
        self.rcon, self.verbose = rcon, verbose
        self._warned = False

    def run(self, command):
        reply = self.rcon.cmd(command)
        if self.verbose:
            print(f"   [rcon] {command}  ->  {reply[:120]}")
        return reply

    def score(self, name):
        reply = self.run(rc.score_get(name))
        value = rc.parse_score(reply)
        if value is None and not self._warned and "objective" in reply.lower():
            self._warned = True
            warnings.warn(f"scoreboard objective {rc.OBJECTIVE} does not exist yet: {reply.strip()}")
        return value if value is not None else 0

    def snapshot(self):
        st = State(beat=self.score(rc.SCORE_BEAT), wait=self.score(rc.SCORE_WAIT), speaker=self.score(rc.SCORE_SPEAKER),
                   talking=self.score(rc.SCORE_TALKING) == 1, lastspoke=self.score(rc.SCORE_LASTSPOKE))
        for c in CHARACTERS:
            st.present[c] = self.score(rc.score_present(c))
        return st

    def watch(self):
        """The cheap part of the snapshot, for the background watcher."""
        return self.score(rc.SCORE_TALKING) == 1, self.score(rc.SCORE_LASTSPOKE), self.score(rc.SCORE_SPEAKER)

    def talking(self):
        return self.score(rc.SCORE_TALKING) == 1

    def wait_value(self):
        return self.score(rc.SCORE_WAIT)

    def positions(self, state):
        """-> (player (x,y,z) | None, (yaw, pitch) | None, {id: (x,y,z)} for in-person characters)"""
        pos = rc.parse_pos(self.run(rc.player_pos()))
        rot = rc.parse_rotation(self.run(rc.player_rotation())) if pos else None
        chars = {}
        for c in CHARACTERS:
            if state.present.get(c) == IN_PERSON:
                p = rc.parse_pos(self.run(rc.character_pos(c)))
                if p:
                    chars[c] = p
        return pos, rot, chars

    # ---- actions ----
    def story_answered(self):
        self.run(rc.FN_ANSWERED)

    def story_consented(self):
        self.run(rc.FN_CONSENTED)

    def subtitle(self, name, text, color):
        self.run(rc.subtitle(name, text, color))

    def bridge_speaking(self, who):
        self.run(rc.bridge_speaking(who))
