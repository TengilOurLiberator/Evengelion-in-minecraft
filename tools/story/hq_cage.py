"""The headquarters set as lists of blocks the story switches: cage lights in banks, the booth, the eyes of the giant, the cage door, the
side door and the lift door, the lobby strips, the hand (raised and lowered) and the pipe rack that tears loose.

Everything is generated at build time from the set module (tools/world/sets/hq.py), through the same voxel build the checker uses:

  * lights: `hq.CAGE_LIGHTS`, minus `hq.BOOTH_LIGHTS` (own switch) and the lights that are not in the cage (the lake hall, the hospital
    vestibule).  The remaining 382 are sorted by distance from the player's stop (`hq.face`), farthest first, the lights that light the
    giant's face (the hidden light blocks and lamps round the head and under the jaw) are taken out as the LAST bank, the rest cut into
    `N_BANKS - 1` equal banks.  `bank_on(k)` / `bank_off(k)` switch one bank.  What "off" is comes from the built world (a gray lamp
    panel, or air for a hidden light block).
  * eyes: `hq.EYES_LEFT + hq.EYES_RIGHT` between `hq.EYE_OFF` and `hq.EYE_ON`.
  * cage door: the cells of `hq.DOORS["cage_door"]["box"]` with the blocks the build put there; opening is air.
  * hand: `hq.hand_cells(False/True)` CELL BY CELL.  What stands where a hand version is not (the coolant, the shoulder armour, a girder)
    comes from a second build of the set with the hand left out; the two versions are never swapped by box (the boxes overlap the head).
  * everything the story changes is restored by `angel:story/hq/reset_all` (called by story/stop, story/start and load when a flag says
    the story has been in the set).

The functions it writes are under angel:story/hq/.  A scene asks the Cage object (`cage(ctx)`) for the command lists.
"""
import collections
import importlib
import math

import sys

from core import NS, OBJ, P, PA, T, fn, num, sset
from audio import sfx
from models import Part, part_merge, summon_part
from core import qaxis, QI

N_BANKS = 8
EYE_POS = (96.5, 55.6, 72.5)              # the player's eyes at the stop (hq.face)
DEBRIS = (96.5, 105.0, 78.5)              # hq.debris_2


def _fill_cmds(cells):
    """{(x, y, z): block} -> fill / setblock commands (runs along x of the same block are one fill)."""
    rows = collections.defaultdict(list)
    for (x, y, z), b in cells.items():
        rows[(y, z, b)].append(x)
    out = []
    for (y, z, b), xs in sorted(rows.items()):
        xs.sort()
        start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x == prev + 1:
                prev = x
                continue
            out.append(f"setblock {start} {y} {z} {b}" if start == prev else f"fill {start} {y} {z} {prev} {y} {z} {b}")
            start = prev = x
    return out


class Cage:
    def __init__(self, ctx):
        self.ctx = ctx
        probe = ctx.probe("hq")
        self.probe = probe
        self.hq = importlib.import_module("sets.hq")
        hq = self.hq
        self.ox, self.oy, self.oz = probe.o

        # ------------------------------------------------------------ the set again, without hands (what the cells hold behind them)
        import layout
        import voxel
        orig_hand = hq.hand
        hq.hand = lambda w, x, y, z, raised: None
        try:
            self.base = voxel.World("hq_nohand", *layout.SETS["hq"])
            hq.build(self.base)
        finally:
            hq.hand = orig_hand
        self.cells_low = hq.hand_cells(False)
        self.cells_high = hq.hand_cells(True)
        self._lights()
        self._eyes()
        self._doors()
        self._hand()
        self._misc()
        self._write()

    # ------------------------------------------------------------------ helpers
    def A(self, x, y, z):
        return (x + self.ox, y + self.oy, z + self.oz)

    def bname(self, x, y, z):
        """block of the set (local coordinates) with the hands left out"""
        b = self.base.get(x, y, z)
        return b if b else "minecraft:air"

    def reg(self, name, lines):
        self.ctx.extra_functions[f"story/hq/{name}"] = list(lines)
        return fn(f"story/hq/{name}")

    def sched(self, name, ticks):
        self.ctx.fx_scheduled.append(f"story/hq/{name}")
        return f"schedule function {NS}:story/hq/{name} {max(1, int(ticks))}t"

    # ------------------------------------------------------------------ lights
    def _lights(self):
        hq = self.hq
        booth = {(x, y, z) for (x, y, z, b) in hq.BOOTH_LIGHTS}
        cage, vest = [], []
        for (x, y, z, b) in hq.CAGE_LIGHTS:
            if (x, y, z) in booth:
                continue
            if 64 <= x <= 128 and 24 <= z <= 137:
                cage.append((x, y, z, b))
            elif 50 <= x < 64 and 70 <= z <= 95:
                vest.append((x, y, z, b))
        face = [l for l in cage if l[2] <= 66 and l[1] <= 70 and abs(l[0] - 96) <= 26]
        rest = [l for l in cage if l not in face]
        rest.sort(key=lambda l: -math.dist((l[0] + .5, l[1] + .5, l[2] + .5), EYE_POS))
        per = int(math.ceil(len(rest) / float(N_BANKS - 1)))
        groups = [rest[i * per:(i + 1) * per] for i in range(N_BANKS - 1)] + [face]
        self.banks = [self._lightset(g) for g in groups]
        self.bank_dist = [(round(math.dist((g[0][0] + .5, g[0][1] + .5, g[0][2] + .5), EYE_POS)) if g else 0,
                           round(math.dist((g[-1][0] + .5, g[-1][1] + .5, g[-1][2] + .5), EYE_POS)) if g else 0) for g in groups]
        self.bank_pos = [(sum(l[0] + .5 for l in g) / len(g) + self.ox, sum(l[1] + .5 for l in g) / len(g), sum(l[2] + .5 for l in g) / len(g))
                         for g in groups]
        self.booth = self._lightset(list(hq.BOOTH_LIGHTS))
        self.vest = self._lightset(vest)

    def _lightset(self, lights):
        on, off = {}, {}
        for (x, y, z, b) in lights:
            a = self.A(x, y, z)
            on[a] = b if ":" in b.split("[")[0] else "minecraft:" + b
            off[a] = self.bname(x, y, z)
        return dict(on=on, off=off, n=len(on))

    # ------------------------------------------------------------------ eyes
    def _eyes(self):
        hq = self.hq
        cells = list(hq.EYES_LEFT) + list(hq.EYES_RIGHT)
        self.eyes_on = {self.A(*c): hq.EYE_ON for c in cells}
        self.eyes_off = {self.A(*c): self.bname(*c) for c in cells}
        for c, b in self.eyes_off.items():
            assert b == hq.EYE_OFF, f"eye cell {c} is {b}, not {hq.EYE_OFF}"

    # ------------------------------------------------------------------ doors
    def _doors(self):
        hq = self.hq
        x1, y1, z1, x2, y2, z2 = hq.DOORS["cage_door"]["box"]
        self.door = {}
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for z in range(z1, z2 + 1):
                    self.door[self.A(x, y, z)] = self.bname(x, y, z)
        self.door_cols = sorted({x for (x, y, z) in self.door})       # world x of the columns, west to east
        # side door of the hospital passage (the set leaves it open): one leaf across x = 62
        gz = hq.GURNEY_Z
        self.side = {}
        for z in (gz, gz + 1, gz + 2):
            for y in range(hq.BRIDGE_Y + 1, hq.BRIDGE_Y + 5):
                self.side[self.A(62, y, z)] = "minecraft:black_concrete" if z == gz + 1 else "minecraft:iron_block"
        self.side_base = {c: "minecraft:air" for c in self.side}
        for c in self.side_base:
            lx = (c[0] - self.ox, c[1] - self.oy, c[2] - self.oz)
            assert self.bname(*lx) == "minecraft:air", f"side door cell {lx} is {self.bname(*lx)}"
        # the lift's door onto the upper lobby: x = 7, z 159..161, y 107..109 (open in the set)
        self.lift = {self.A(7, y, z): "minecraft:iron_block" for y in (107, 108, 109) for z in (159, 160, 161)}
        self.lift_base = {c: "minecraft:air" for c in self.lift}
        for c in self.lift_base:
            lx = (c[0] - self.ox, c[1] - self.oy, c[2] - self.oz)
            assert self.bname(*lx) == "minecraft:air", f"lift cell {lx} is {self.bname(*lx)}"
        # the lobby and car ceiling strips (sea lanterns): dim to a red glow for the alert
        strips = []
        for x in range(2, 15):
            for y in range(105, 116):
                for z in range(152, 168):
                    if self.bname(x, y, z) == "minecraft:sea_lantern":
                        strips.append(self.A(x, y, z))
        self.strips = strips
        self.strips_on = {c: "minecraft:sea_lantern" for c in strips}
        self.strips_red = {c: "minecraft:magma_block" for c in strips}

    # ------------------------------------------------------------------ hand
    def _hand(self):
        low, high = self.cells_low, self.cells_high
        union = set(low) | set(high)

        def nb(n):
            return n if ":" in n.split("[")[0] else "minecraft:" + n

        def target(cell, version):
            cells = high if version else low
            return nb(cells.get(cell) or self.bname(*cell))
        self.hand_up_cells, self.hand_down_cells = {}, {}
        for c in union:
            a, b = target(c, False), target(c, True)
            if a != b:
                self.hand_down_cells[self.A(*c)] = a
                self.hand_up_cells[self.A(*c)] = b
        # safety: no cell of the raised hand where a person can stand or walk on the bridge, rails and spur
        for (x, y, z) in self.cells_high:
            assert not (93 <= x <= 99 and 53 <= y <= 60 and z >= 62), f"raised hand cell {(x, y, z)} in the bridge's walkway"
            assert not (64 <= x <= 92 and 53 <= y <= 57 and 77 <= z <= 83), f"raised hand cell {(x, y, z)} in the gurney spur"
        # the pipe rack over the shield: tears loose
        hq = self.hq
        zc = 78
        self.rack = {}
        for x in range(94, 99):
            for (y, z) in ((106, zc), (105, zc - 1), (105, zc + 1)):
                b = self.bname(x, y, z)
                if b != "minecraft:air":
                    self.rack[self.A(x, y, z)] = b
        self.rack_local = {(c[0] - self.ox, c[1], c[2]): b for c, b in self.rack.items()}

    def _misc(self):
        pass

    # ------------------------------------------------------------------ the functions
    def _write(self):
        hq = self.hq
        reg = self.reg
        for k, b in enumerate(self.banks):
            reg(f"bank_on_{k}", _fill_cmds(b["on"]))
            reg(f"bank_off_{k}", _fill_cmds(b["off"]))
        reg("booth_on", _fill_cmds(self.booth["on"]))
        reg("booth_off", _fill_cmds(self.booth["off"]))
        reg("vest_on", _fill_cmds(self.vest["on"]))
        reg("vest_off", _fill_cmds(self.vest["off"]))
        reg("eyes_on", _fill_cmds(self.eyes_on))
        reg("eyes_off", _fill_cmds(self.eyes_off))
        reg("hand_up", _fill_cmds(self.hand_up_cells))
        reg("hand_down", _fill_cmds(self.hand_down_cells))
        reg("strips_red", _fill_cmds(self.strips_red))
        reg("strips_on", _fill_cmds(self.strips_on))
        reg("rack_tear", _fill_cmds({c: "minecraft:air" for c in self.rack}))
        reg("rack_restore", _fill_cmds(self.rack))
        # --- the cage door: two leaves slide together from the sides (three stages, three ticks apart)
        cols = self.door_cols
        stages = [[cols[0], cols[-1]], [cols[1], cols[-2]], [c for c in cols[2:-2]]]
        for i, st in enumerate(stages):
            reg(f"door_close_{i}", _fill_cmds({c: b for c, b in self.door.items() if c[0] in st}))
            reg(f"door_open_{2 - i}", _fill_cmds({c: "minecraft:air" for c in self.door if c[0] in st}))
        reg("door_closed", _fill_cmds(self.door))
        reg("door_opened", _fill_cmds({c: "minecraft:air" for c in self.door}))
        reg("door_close", [fn("story/hq/door_close_0"), self.sched("door_close_1", 3), self.sched("door_close_2", 6)])
        reg("door_open", [fn("story/hq/door_open_0"), self.sched("door_open_1", 3), self.sched("door_open_2", 6)])
        # --- the side door of the hospital passage: the middle seam first, then the leaves
        mid = {c: "minecraft:air" for c, b in self.side.items() if b == "minecraft:black_concrete"}
        rest = {c: "minecraft:air" for c, b in self.side.items() if b != "minecraft:black_concrete"}
        reg("side_closed", _fill_cmds(self.side))
        reg("side_opened", _fill_cmds({c: "minecraft:air" for c in self.side}))
        reg("side_open_0", _fill_cmds(mid))
        reg("side_open_1", _fill_cmds(rest))
        reg("side_open", [fn("story/hq/side_open_0"), self.sched("side_open_1", 8)])
        # --- the lift door (upper lobby)
        reg("lift_closed", _fill_cmds(self.lift))
        reg("lift_opened", _fill_cmds({c: "minecraft:air" for c in self.lift}))
        # --- lights groups
        reg("lights_off", [fn(f"story/hq/bank_off_{k}") for k in range(N_BANKS)])
        reg("lights_on", [fn(f"story/hq/bank_on_{k}") for k in range(N_BANKS)])
        reg("all_off", [fn("story/hq/lights_off"), fn("story/hq/booth_off"), fn("story/hq/vest_off")])
        reg("all_on", [fn("story/hq/lights_on"), fn("story/hq/booth_on"), fn("story/hq/vest_on")])
        # --- reset: the set as it was built (lights off, eyes off, door shut, hand lowered, passages open, rack whole)
        dirty = f"scoreboard players set #hq.dirty {OBJ}"
        reg("reset_cage", [fn("story/hq/all_off"), fn("story/hq/eyes_off"), fn("story/hq/door_closed"), fn("story/hq/hand_down"),
                           fn("story/hq/side_opened"), fn("story/hq/rack_restore")])
        reg("reset_lobby", [fn("story/hq/lift_opened"), fn("story/hq/strips_on")])
        reg("reset_all", [f"execute if loaded {self.ox + 96} 60 100 run function {NS}:story/hq/reset_cage",
                          f"execute if loaded {self.ox + 8} 107 160 run function {NS}:story/hq/reset_lobby",
                          f"{dirty} 0"])
        self.ctx.stop_extra.append(f"execute if score #hq.dirty {OBJ} matches 1 run function {NS}:story/hq/reset_all")
        self.ctx.load_extra.append(f"execute unless score #running {OBJ} matches 1 if score #hq.dirty {OBJ} matches 1 run function {NS}:story/hq/reset_all")
        self._write_effects()

    # ------------------------------------------------------------------ effects: flicker, dust, rings, the falling rig
    def flicker(self, name, banks, pattern, extra_off=()):
        """Switch `banks` (and the groups in extra_off: "booth", "vest") off and on following pattern = [(tick, "on"/"off"), ...].
        Returns the command that starts it (step 0 now, the others scheduled)."""
        steps = []
        for i, (tick, what) in enumerate(pattern):
            cmds = [fn(f"story/hq/bank_{what}_{k}") for k in banks] + [fn(f"story/hq/{g}_{what}") for g in extra_off]
            name_i = f"fl_{name}_{i}"
            self.reg(name_i, cmds)
            steps.append((tick, name_i))
        start = []
        for tick, nm in steps:
            start.append(fn(f"story/hq/{nm}") if tick == 0 else self.sched(nm, tick))
        self.reg(f"fl_{name}", start)
        return fn(f"story/hq/fl_{name}")

    def _write_effects(self):
        hq = self.hq
        ox = self.ox
        # dust falling through the beams: columns over the bridge and the giant's shoulders, from the ceiling rigs
        cols = [(76 + ox, 109, 40), (116 + ox, 109, 40), (96 + ox, 109, 52), (96 + ox, 109, 90), (76 + ox, 109, 90), (116 + ox, 109, 100),
                (96 + ox, 109, 114), (76 + ox, 109, 126), (96 + ox, 109, 66), (88 + ox, 109, 78), (104 + ox, 109, 78), (96 + ox, 109, 102)]
        def dust(n_per, spread=2.0):
            out = []
            for (x, y, z) in cols:
                out.append(f"particle minecraft:falling_dust{{block_state:\"minecraft:gray_concrete\"}} {num(x + .5)} {num(y - 2)} {num(z + .5)} {num(spread)} 1.5 {num(spread)} 0.0 {n_per} force")
                out.append(f"particle minecraft:white_ash {num(x + .5)} {num(y - 12)} {num(z + .5)} {num(spread)} 6 {num(spread)} 0.01 {n_per} force")
            return out
        self.reg("dust_a", dust(10, 2.5))
        self.reg("dust_b", dust(7, 3.0))
        self.reg("dust_c", dust(4, 3.5))
        self.reg("dust_heavy", dust(18, 3.0) + [f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:stone\"}} ~ ~5 ~ 4 1.5 4 0.0 40 force"])
        self.reg("dust", [fn("story/hq/dust_a"), self.sched("dust_b", 16), self.sched("dust_c", 40)])
        # the coolant rings: an orange ring spreading from the giant's chest (centre x 96, z 46), four times
        ring = []
        for r in (3, 6, 10, 15, 21):
            for a in range(0, 360, 12):
                x, z = 96.5 + ox + r * math.cos(math.radians(a)), 46.0 + r * math.sin(math.radians(a))
                ring.append((r, f"particle minecraft:dust{{color:[1.0,0.55,0.2],scale:1.6}} {num(x)} 37.4 {num(z)} 0 0 0 0 1 force"))
        for i, r in enumerate((3, 6, 10, 15, 21)):
            self.reg(f"ring_{i}", [c for rr, c in ring if rr == r])
        self.reg("rings", [fn("story/hq/ring_0")] + [self.sched(f"ring_{i}", 5 * i) for i in range(1, 5)])
        self._write_rig()

    # ------------------------------------------------------------------ the rig that tears loose and falls onto the hand
    def _write_rig(self):
        ox = self.ox
        Ox, Oy, Oz = DEBRIS[0] + ox, DEBRIS[1], DEBRIS[2]            # world position of hq.debris_2
        parts = []
        # model space = world axes at yaw 0 (the display is summoned with no rotation), origin at debris_2.  The pipes: the real rack's cells.
        for i, ((x, y, z), b) in enumerate(sorted(self.rack_local.items())):
            parts.append(Part(f"r{i}", b.split("[")[0].replace("minecraft:", ""), (x - DEBRIS[0], y - Oy, z - Oz),
                              (x + 1.0 - DEBRIS[0], y + 1.0 - Oy, z + 1.0 - Oz)))
        # a lighting rig hangs under the pipes: a lit panel of sea lanterns in a black frame, and the cable that held it
        parts.append(Part("lamp", "sea_lantern", (-1.4, -1.25, -1.2), (1.4, -0.75, 1.2), bright=(15, 15)))
        parts.append(Part("frameA", "black_concrete", (-1.8, -0.75, -1.4), (1.8, -0.45, -1.1)))
        parts.append(Part("frameB", "black_concrete", (-1.8, -0.75, 1.1), (1.8, -0.45, 1.4)))
        parts.append(Part("frameC", "black_concrete", (-1.8, -1.5, -1.4), (-1.5, -0.75, 1.4)))
        parts.append(Part("frameD", "black_concrete", (1.5, -1.5, -1.4), (1.8, -0.75, 1.4)))
        parts.append(Part("cable", "iron_chain", (-0.15, 0.0, -0.15), (0.15, 3.0, 0.15), props={"axis": "y"}))
        self.rig_parts = parts
        spawn_pos = f"{num(Ox)} {num(Oy)} {num(Oz)}"
        tag = "angel.rigdrop"
        spawn = [summon_part(p, [tag, f"angel.pt_{p.name}"], tp_duration=0, view_range=3.0, pos=spawn_pos) for p in parts]
        # keyframes: tick, fall (blocks), roll (degrees about z).  g = 9.8 blocks/s^2: 0.5 g t^2 at 0.7, 1.4, 2.15, 2.85 s.
        keys = [(0, 0.0, 0.0), (14, 2.4, 5.0), (28, 9.6, 12.0), (43, 22.65, 19.0), (57, 39.5, 24.0)]
        self.rig_fall_ticks = keys[-1][0]

        def merge_all(fall, roll, dur):
            return [part_merge(p, tag, motion=(qaxis("z", roll), (0, 0, 0), (0, -fall, 0)), interp=dur) for p in parts]
        lines_k = []
        prev_t = 0
        for i, (t, fall, roll) in enumerate(keys[1:], 1):
            cmds = merge_all(fall, roll, t - prev_t)
            cmds += [f"particle minecraft:electric_spark {num(Ox)} {num(Oy - fall)} {num(Oz)} 1.4 0.5 1.4 0.1 14 force",
                     f"particle minecraft:smoke {num(Ox)} {num(Oy - fall + 0.5)} {num(Oz)} 0.8 0.3 0.8 0.02 6 force"]
            self.reg(f"rig_k{i}", cmds)
            lines_k.append((prev_t, i))
            prev_t = t
        # start: tear the real pipes out, show the display copy in their place, and let it fall
        start = [fn("story/hq/rack_tear")] + spawn
        for (t0, i) in lines_k:
            start.append(fn(f"story/hq/rig_k{i}") if t0 == 0 else self.sched(f"rig_k{i}", t0))
        start.append(self.sched("rig_break", keys[-1][0]))
        start.append(self.sched("rig_clear", keys[-1][0] + 45))
        self.reg("rig_fall", start)
        # the break: every piece hops off the palm and flies sideways (clear of the bridge: |dx| > 6.5), then falls into the coolant
        import random
        hop, down = [], []
        rnd = random.Random(5)
        for i, p in enumerate(parts):
            side = -1 if i % 2 else 1
            dx = side * (6.5 + rnd.uniform(0, 3.0))
            dz = rnd.uniform(-2.5, 2.5)
            q = qaxis("z", 24.0 + side * rnd.uniform(40, 160))
            hop.append(part_merge(p, tag, motion=(q, (0, 0, 0), (dx * 0.5, -39.5 + 1.2, dz * 0.5)), interp=7))
            down.append(part_merge(p, tag, motion=(q, (0, 0, 0), (dx, -(Oy - 37.5), dz)), interp=26))
        self.reg("rig_break_hop", hop)
        self.reg("rig_break_down", down)
        self.reg("rig_break", [
            fn("story/hq/rig_break_hop"), self.sched("rig_break_down", 7),
            f"particle minecraft:block{{block_state:\"minecraft:iron_block\"}} {num(Ox)} 65.0 {num(Oz)} 2.2 0.4 2.2 0.25 90 force",
            f"particle minecraft:block{{block_state:\"minecraft:copper_block\"}} {num(Ox)} 65.0 {num(Oz)} 2.0 0.4 2.0 0.2 50 force",
            f"particle minecraft:electric_spark {num(Ox)} 65.0 {num(Oz)} 2.5 0.6 2.5 0.3 80 force",
            f"particle minecraft:explosion {num(Ox)} 65.5 {num(Oz)} 1.5 0.2 1.5 0 3 force",
            f"particle minecraft:large_smoke {num(Ox)} 65.5 {num(Oz)} 2.5 0.5 2.5 0.03 30 force",
            sfx("sfx.rig_crash", at=(Ox, 66.0, Oz), vol=3.0, pitch=0.9, minvol=0.9)])
        self.reg("rig_clear", ["kill @e[tag=angel.rigdrop]"])
        # ready-made bundles for the impacts
        # the chains of the hanging rigs rattle (their blocks cannot swing; the sound and the dust shaken loose stand for it)
        rattle = []
        for (cx_, cz_) in ((88, 78), (104, 90), (88, 102), (104, 114)):
            for ev in ("minecraft:block.chain.hit", "minecraft:block.iron_chain.hit"):
                rattle.append(sfx(ev, at=(cx_ + ox + 0.5, 96.0, cz_ + 0.5), vol=2.5, pitch=0.6, minvol=0.4))
        self.reg("rattle", rattle)
        self.reg("impact1", [
            sfx("sfx.impact_above", at=(96.5 + ox, 100.0, 72.5), vol=4.0, pitch=0.85, minvol=0.9),
            fn("story/hq/rattle"), self.sched("rattle", 7),
            sfx("sfx.lights_flicker", vol=0.8), sfx("sfx.dust_fall", vol=0.7), fn("story/hq/dust"), fn("story/hq/rings"),
            f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:stone\"}} ~ ~4 ~ 3 1.5 3 0.0 24 force"])
        self.flicker("far", [2, 5], [(0, "off"), (2, "on"), (5, "off"), (7, "on")])
        self.reg("impact_far", [
            sfx("sfx.impact_above", at=(96.5 + ox, 110.0, 40.5), vol=2.2, pitch=0.7, minvol=0.7),
            fn("story/hq/fl_far"), fn("story/hq/dust_c"), self.sched("dust_c", 10)])


def cage(ctx):
    if "hq_cage" not in ctx.helpers:
        ctx.helpers["hq_cage"] = Cage(ctx)
    return ctx.helpers["hq_cage"]


def dirty_cmd():
    """Mark the set as touched, so that story/stop restores it."""
    return sset("#hq.dirty", 1)