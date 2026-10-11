"""A stand-in for the game's RCON, for `bridge.py --text`: a tiny simulated world driven from the terminal.

It answers exactly the commands rcon_commands.py builds (so those strings and their parsing are exercised) and
prints the commands that would change the game (functions, scoreboard writes, subtitles).
"""
import math
import re

import rcon_commands as rc
from config import CHARACTERS, NAMES


class FakeRcon:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.scores = {rc.SCORE_BEAT: 1, rc.SCORE_WAIT: 0, rc.SCORE_SPEAKER: 0, rc.SCORE_TALKING: 0}
        for c in CHARACTERS:
            self.scores[rc.score_present(c)] = 1
        self.player = [0.0, 64.0, 0.0]
        self.yaw, self.pitch = 0.0, 0.0
        self.pos = {}
        for c, (dist, bearing) in zip(CHARACTERS, [(3, 0), (4, 60), (6, -75), (5, 170)]):
            self.place(c, dist, bearing)
        self.last_functions = []

    # ---- things the text-mode user controls ----
    def place(self, who, dist, bearing=0.0):
        """Put a character `dist` blocks from the player, `bearing` degrees to the left of straight ahead (yaw 0)."""
        b = math.radians(self.yaw + bearing)
        self.pos[who] = [self.player[0] - math.sin(b) * dist, self.player[1], self.player[2] + math.cos(b) * dist]

    def look_at(self, who):
        dx, dz = self.pos[who][0] - self.player[0], self.pos[who][2] - self.player[2]
        self.yaw = math.degrees(math.atan2(-dx, dz))
        dy = (self.pos[who][1] + 0.9) - (self.player[1] + 1.62)
        self.pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz)))

    def look_away(self):
        self.yaw = (self.yaw + 180) % 360
        self.pitch = 0.0

    def set_score(self, name, value):
        self.scores[name] = int(value)

    # ---- RCON ----
    def cmd(self, command):
        m = re.fullmatch(rf"scoreboard players get (\S+) {re.escape(rc.OBJECTIVE)}", command)
        if m:
            name = m.group(1)
            if name in self.scores:
                return f"{name} has {self.scores[name]} [{rc.OBJECTIVE}]"
            return f"Can't get value of {rc.OBJECTIVE} for {name}; none is set"
        m = re.fullmatch(rf"scoreboard players set (\S+) {re.escape(rc.OBJECTIVE)} (-?\d+)", command)
        if m:
            self.scores[m.group(1)] = int(m.group(2))
            if self.verbose and m.group(1) != rc.SCORE_BRIDGE_SPEAKING:
                print(f"   [rcon] {command}")
            return f"Set [{rc.OBJECTIVE}] for {m.group(1)} to {m.group(2)}"
        if command == rc.player_pos():
            return "Shinji has the following entity data: [{:.2f}d, {:.2f}d, {:.2f}d]".format(*self.player)
        if command == rc.player_rotation():
            return f"Shinji has the following entity data: [{self.yaw:.2f}f, {self.pitch:.2f}f]"
        for c in CHARACTERS:
            if command == rc.character_pos(c):
                if self.scores.get(rc.score_present(c)) == 1:
                    return f"{NAMES[c]} has the following entity data: [{self.pos[c][0]:.2f}d, {self.pos[c][1]:.2f}d, {self.pos[c][2]:.2f}d]"
                return "No entity was found"
        if command.startswith("function "):
            self.last_functions.append(command)
            if self.verbose:
                print(f"   [rcon] {command}")
            if command in (rc.FN_ANSWERED, rc.FN_CONSENTED):
                self.scores[rc.SCORE_WAIT] = 0               # what the datapack's function does
            return "Executed function"
        if command.startswith("tellraw"):
            if self.verbose:
                print(f"   [rcon] {command}")
            return ""
        if self.verbose:
            print(f"   [rcon] (unrecognised by the fake server) {command}")
        return ""

    def close(self):
        pass
