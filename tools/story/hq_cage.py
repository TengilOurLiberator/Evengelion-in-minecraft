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

from core import NS, OBJ, P, PA, T, TAG, fn, num, sset
from audio import sfx
from models import Part, part_merge, summon_part, transformation_nbt
from core import qaxis, qmul, QI

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
        # the eyes' own glow (hidden light blocks over the brow and the bridge end, built as air) goes on and off WITH the eyes
        glow = list(getattr(hq, "EYE_GLOW", []))
        self.glow_cells = len(glow)
        for (x, y, z, b) in glow:
            a = self.A(x, y, z)
            self.eyes_on[a] = b if ":" in b.split("[")[0] else "minecraft:" + b
            self.eyes_off[a] = self.bname(x, y, z)

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
        self._write_hand_surge()
        self._write_rig2()
        self._write_misc2()
        # ready-made bundles for the impacts
        # the chains of the hanging rigs rattle (their blocks cannot swing; the sound and the dust shaken loose stand for it)
        # (the vanilla `block.iron_chain.hit` does not exist in 26.3 and `block.chain.hit` is a stand-in: the library has the real thing,
        # sfx.chains (5 s of heavy chains swinging) and sfx.lake_ring (7 s of the coolant ringing, from the lake below the bridge))
        self.reg("rattle", [sfx("sfx.chains", at=(88 + ox + 0.5, 96.0, 90.5), vol=2.6, pitch=0.9, minvol=0.5),
                            sfx("sfx.chains", at=(104 + ox + 0.5, 96.0, 102.5), vol=2.0, pitch=0.8, minvol=0.4)])
        self.reg("lake_ring_near", [sfx("sfx.lake_ring", at=(96.5 + ox, 38.0, 56.0), vol=3.0, pitch=1.0, minvol=0.6)])
        self.reg("impact1", [
            sfx("sfx.impact_above", at=(96.5 + ox, 100.0, 72.5), vol=4.0, pitch=0.85, minvol=0.9),
            fn("story/hq/rattle"), self.sched("rattle", 7), self.sched("lake_ring_near", 6),
            sfx("sfx.lights_flicker", vol=0.8), sfx("sfx.dust_fall", vol=0.7), fn("story/hq/dust"), fn("story/hq/rings"),
            f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:stone\"}} ~ ~4 ~ 3 1.5 3 0.0 24 force"])
        self.flicker("far", [2, 5], [(0, "off"), (2, "on"), (5, "off"), (7, "on")])
        self.reg("lake_ring_far", [sfx("sfx.lake_ring", at=(96.5 + ox, 38.0, 40.5), vol=1.4, pitch=0.9, minvol=0.35)])
        self.reg("impact_far", [
            sfx("sfx.impact_above", at=(96.5 + ox, 110.0, 40.5), vol=2.2, pitch=0.7, minvol=0.7),
            sfx("sfx.chains", at=(104 + ox + 0.5, 96.0, 90.5), vol=1.2, pitch=0.8, minvol=0.3), self.sched("lake_ring_far", 8),
            fn("story/hq/fl_far"), fn("story/hq/dust_c"), self.sched("dust_c", 10)])


    # ------------------------------------------------------------------ the hand surges up out of the coolant, stage by stage
    HAND_STAGES = 8
    HAND_STAGE_TICKS = 4

    def _write_hand_surge(self):
        """`story/hq/hand_surge`: the raised hand comes up in eight steps four ticks apart (the arm from the coolant upward, the palm sweeping
        in from the west over the bridge), each with a burst of coolant spray at the place it has reached and a column of spray on the
        bridge's west side at the player.  The lowered hand's cells are cleared in the first steps.  `hand_up` (all at once) stays for resets."""
        ox = self.ox
        cells = self.hand_up_cells
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

        def key(c):
            return 0.7 * (c[1] - y0) / max(1.0, y1 - y0) + 0.3 * (c[0] - x0) / max(1.0, x1 - x0)
        order = sorted(cells, key=key)
        n = self.HAND_STAGES
        per = int(math.ceil(len(order) / float(n)))
        calls = []
        for k in range(n):
            sl = order[k * per:(k + 1) * per]
            if not sl:
                continue
            cx = sum(c[0] for c in sl) / float(len(sl)) + 0.5
            cy = sum(c[1] for c in sl) / float(len(sl)) + 0.5
            cz = sum(c[2] for c in sl) / float(len(sl)) + 0.5
            lines = _fill_cmds({c: cells[c] for c in sl})
            lines += [f"particle minecraft:splash {num(cx)} 37.6 {num(cz)} 5 0.4 7 0.2 90 force",
                      f"particle minecraft:cloud {num(cx)} {num(cy)} {num(cz)} 2.5 2.5 2.5 0.04 18 force",
                      f"particle minecraft:dust{{color:[1.0,0.55,0.2],scale:2.2}} {num(cx)} {num(cy)} {num(cz)} 3 3 3 0 28 force",
                      f"particle minecraft:falling_dust{{block_state:\"minecraft:orange_concrete\"}} {num(cx)} {num(cy + 3)} {num(cz)} 3 1 3 0 14 force"]
            if k >= 2:
                # the wash thrown up beside the bridge on the arm's side (west), level with the player
                lines.append(f"execute at {P()} positioned {num(90.5 + ox)} 53.0 ~ run particle minecraft:splash ~ ~ ~ 0.6 3.0 4 0.25 50 force")
                lines.append(f"execute at {P()} positioned {num(90.5 + ox)} 55.0 ~ run particle minecraft:cloud ~ ~ ~ 0.6 3.0 3 0.05 14 force")
            self.reg(f"hand_st_{k}", lines)
            calls.append(fn(f"story/hq/hand_st_{k}") if k == 0 else self.sched(f"hand_st_{k}", k * self.HAND_STAGE_TICKS))
        self.reg("hand_surge", calls)
        self.hand_surge_ticks = (n - 1) * self.HAND_STAGE_TICKS

    # ------------------------------------------------------------------ the lighting rig that tears loose over the player, hangs, falls on the hand
    RIG_HANG_Y = 76.0          # the underside of the rig, 22 above the deck
    RIG_TOP_Y = 108.0          # where its two cables are fixed to the roof truss
    PALM_TOP_Y = 64.05         # the back of the raised hand, where it lands
    RIG_FALL_AT = 44           # ticks after the tear that it lets go (the tear sound's falling whistle begins at about 2 s)
    RIG_FALL_TICKS = 31        # 0.5 g t^2 = 11.95 blocks

    def _rig_parts(self, cable_hi):
        P_ = Part
        return [P_("lamp", "sea_lantern", (-1.6, 0.0, -1.2), (1.6, 0.5, 1.2), bright=(15, 15)),
                P_("frA", "black_concrete", (-1.9, 0.5, -1.5), (1.9, 0.85, -1.15)),
                P_("frB", "black_concrete", (-1.9, 0.5, 1.15), (1.9, 0.85, 1.5)),
                P_("frC", "black_concrete", (-1.9, 0.0, -1.5), (-1.6, 0.85, 1.5)),
                P_("frD", "black_concrete", (1.6, 0.0, -1.5), (1.9, 0.85, 1.5)),
                P_("spL", "iron_block", (-1.0, 0.85, -0.4), (-0.3, 1.45, 0.4)),
                P_("spR", "iron_block", (0.3, 0.85, -0.4), (1.0, 1.45, 0.4)),
                P_("bar", "iron_block", (-2.3, 1.45, -0.2), (2.3, 1.8, 0.2)),
                P_("cabL", "iron_chain", (-2.0, 1.8, -0.5), (-1.0, cable_hi, 0.5), props={"axis": "y"}),
                P_("cabR", "iron_chain", (1.0, 1.8, -0.5), (2.0, cable_hi, 0.5), props={"axis": "y"})]

    def _write_rig2(self):
        import random
        ox = self.ox
        XC = 96.5 + ox
        HY, TY = self.RIG_HANG_Y, self.RIG_TOP_Y
        HC = TY - HY
        D = HY - self.PALM_TOP_Y
        tag = "angel.rigdrop"
        at_rig = "execute at @e[tag=angel.rigpos,limit=1] run "
        near = f"execute if score #rg.near {OBJ} matches 1 "
        long_parts = self._rig_parts(HC)
        # ---- where it hangs: over the player, 2.5 blocks ahead, when he is within 11 blocks of the shield column; else over the hand
        # (clamped to the palm: the raised hand covers x 91..101, z 74..80)
        self.reg("rig2_place", [
            "kill @e[tag=angel.rigpos]",
            f"summon minecraft:marker {num(XC)} {num(HY)} 78.0 {{Tags:[\"{TAG}\",\"angel.rigpos\"]}}",
            sset("#rg.near", 0),
            f"execute positioned {num(XC)} 54.0 78.5 if entity {P('distance=..11')} run {sset('#rg.near', 1)}",
            f"{near}as {P()} at @s rotated ~ 0 positioned ^ ^ ^2.5 run tp @e[tag=angel.rigpos,limit=1] ~ {num(HY)} ~",
            f"execute store result score #rg.x {OBJ} run data get entity @e[tag=angel.rigpos,limit=1] Pos[0] 100",
            f"execute store result score #rg.z {OBJ} run data get entity @e[tag=angel.rigpos,limit=1] Pos[2] 100",
            f"execute store result score #rg.pz {OBJ} run data get entity {P()} Pos[2] 100",
            sset("#rg.xl", int(round((93.6 + ox) * 100))), sset("#rg.xh", int(round((99.4 + ox) * 100))),
            sset("#rg.zl", 7500), sset("#rg.zh", 7960),
            f"scoreboard players operation #rg.x {OBJ} > #rg.xl {OBJ}", f"scoreboard players operation #rg.x {OBJ} < #rg.xh {OBJ}",
            f"scoreboard players operation #rg.z {OBJ} > #rg.zl {OBJ}", f"scoreboard players operation #rg.z {OBJ} < #rg.zh {OBJ}",
            f"execute store result entity @e[tag=angel.rigpos,limit=1] Pos[0] double 0.01 run scoreboard players get #rg.x {OBJ}",
            f"execute store result entity @e[tag=angel.rigpos,limit=1] Pos[2] double 0.01 run scoreboard players get #rg.z {OBJ}",
            # which way is the far side: +1 when the player is north of the rig (debris goes south), -1 when south of it
            sset("#rg.sgn", 1), f"execute if score #rg.pz {OBJ} > #rg.z {OBJ} run {sset('#rg.sgn', -1)}"])
        # ---- spawn (at the marker)
        spawn = [summon_part(p, [tag, f"angel.pt_{p.name}"], tp_duration=0, view_range=4.0, pos="~ ~ ~") for p in long_parts]
        self.reg("rig2_spawn", spawn + [
            "summon minecraft:block_display ~-1.7 54.03 ~-1.5 {Tags:[\"" + TAG + "\",\"angel.rigshadow\"],block_state:\"minecraft:black_stained_glass\","
            "teleport_duration:6,view_range:2.0f,brightness:{sky:0,block:0},"
            "transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[3.4f,0.02f,3.0f],right_rotation:[0f,0f,0f,1f]}}"])
        # ---- the sway: about the cables' fixing at the roof (a pendulum along z), the shadow on the deck following it
        sway = [(0, -2.0, 1.0, 0.5, 5, -0.9), (6, 4.5, -2.0, 0.7, 14, 2.0), (20, -3.5, 2.0, 0.5, 14, -1.5), (34, 0.0, 0.0, 0.3, 10, 0.9)]
        sway_calls = []
        for i, (t, ax_, az_, sag, dur, sdz) in enumerate(sway):
            q = qmul(qaxis("x", ax_), qaxis("z", az_))
            lines = [part_merge(p, tag, motion=(q, (0.0, HC, 0.0), (0.0, -sag, 0.0)), interp=dur) for p in long_parts]
            lines.append(f"execute as @e[tag=angel.rigshadow] at @s run tp @s ~ ~ ~{num(sdz)}")
            lines.append(f"{at_rig}particle minecraft:electric_spark ~ ~1.0 ~ 1.6 0.6 1.4 0.25 18 force")
            lines.append(f"{at_rig}particle minecraft:electric_spark ~ ~{num(HC)} ~ 2.4 0.6 0.6 0.3 22 force")
            if i == 0:
                lines.append(f"{at_rig}particle minecraft:large_smoke ~ ~{num(HC)} ~ 2.4 0.6 0.6 0.02 10 force")
            self.reg(f"rig2_k{i}", lines)
            sway_calls.append(fn(f"story/hq/rig2_k{i}") if t == 0 else self.sched(f"rig2_k{i}", t))
        # ---- dust and sparks falling past the player's face (and, always, down the rig's own column)
        def rain(n):
            return [f"{at_rig}particle minecraft:falling_dust{{block_state:\"minecraft:gray_concrete\"}} ~ ~0.5 ~ 1.6 0.2 1.4 0 {n} force",
                    f"{at_rig}particle minecraft:falling_lava ~ ~0.2 ~ 1.4 0.2 1.2 0 {n // 2 + 3} force",
                    f"{at_rig}particle minecraft:white_ash ~ ~-1 ~ 2 3 2 0.01 {n} force",
                    f"{near}as {P()} at @s rotated ~ 0 positioned ^ ^3.5 ^1.0 run particle minecraft:falling_dust{{block_state:\"minecraft:gray_concrete\"}} ~ ~ ~ 0.9 1.2 0.9 0 {n + 6} force",
                    f"{near}as {P()} at @s rotated ~ 0 positioned ^ ^3.2 ^1.0 run particle minecraft:falling_lava ~ ~ ~ 0.6 1 0.6 0 {n // 2 + 2} force",
                    f"{near}as {P()} at @s rotated ~ 0 positioned ^ ^2.4 ^0.8 run particle minecraft:electric_spark ~ ~ ~ 0.5 0.8 0.5 0.05 12 force"]
        self.reg("rig2_rain_a", rain(26))
        self.reg("rig2_rain_b", rain(14))
        # a handful of fragments that fall past his face: tiny black and iron blocks, summoned 4.5 above his eyes a little ahead
        rnd = random.Random(21)
        bits = []
        for i in range(9):
            s_ = rnd.uniform(0.12, 0.34)
            blk = rnd.choice(["iron_block", "black_concrete", "gray_concrete", "iron_block"])
            bits.append(f'summon minecraft:block_display ~{num(rnd.uniform(-0.9, 0.9))} ~{num(rnd.uniform(-0.6, 1.4))} ~{num(rnd.uniform(-0.9, 0.9))} '
                        f'{{Tags:["{TAG}","angel.rigbit"],block_state:"minecraft:{blk}",view_range:1.5f,interpolation_duration:16,teleport_duration:0,'
                        f'{transformation_nbt((0, 0, 0), qaxis("z", rnd.uniform(0, 90)), (s_, s_ * 0.7, s_))}}}')
        self.reg("rig2_bits_spawn", bits)
        self.reg("rig2_bits_fall", ["execute as @e[tag=angel.rigbit] run data merge entity @s {start_interpolation:0,interpolation_duration:16,"
                                    "transformation:{translation:[0f,-9f,0f]}}"])
        self.reg("rig2_bits_kill", ["kill @e[tag=angel.rigbit]"])
        # ---- the fall: three keyframes, the cables snapping short
        fall_calls = []
        keys = [(0, 10, 1.2, 6.0, 9.0), (10, 20, 4.9, 14.0, 4.0), (20, 31, 11.65, 22.0, 3.0)]
        for i, (t0, t1, fall, roll, cab) in enumerate(keys):
            ps = self._rig_parts(cab)
            q = qaxis("z", roll)
            lines = [part_merge(p, tag, motion=(q, (0.0, 0.5, 0.0), (0.0, -(0.3 + fall), 0.0)), interp=t1 - t0) for p in ps]
            lines.append(f"{at_rig}particle minecraft:electric_spark ~ ~{num(-(0.3 + fall) + 1.0)} ~ 1.4 0.5 1.4 0.1 14 force")
            lines.append(f"{at_rig}particle minecraft:smoke ~ ~{num(-(0.3 + fall) + 1.0)} ~ 0.8 0.3 0.8 0.02 6 force")
            self.reg(f"rig2_f{i}", lines)
            fall_calls.append(fn(f"story/hq/rig2_f{i}") if t0 == 0 else self.sched(f"rig2_f{i}", t0))
        self.reg("rig2_fall", fall_calls + [self.sched("rig2_break", self.RIG_FALL_TICKS), self.sched("rig2_clear", self.RIG_FALL_TICKS + 50)])
        # ---- the break on the palm: the pieces hop off and fly away to the far side and the flanks (never over the bridge), then drop into the coolant
        short_parts = self._rig_parts(3.0)
        rnd = random.Random(5)
        for tag_s, sgn in (("p", 1), ("n", -1)):
            hop, down = [], []
            for i, p in enumerate(short_parts):
                side = -1 if i % 2 else 1
                dx = side * (8.5 + rnd.uniform(0, 3.0))
                dz = sgn * (3.0 + rnd.uniform(0, 4.0)) + rnd.uniform(-1.5, 1.5)
                q = qaxis("z", 22.0 + side * rnd.uniform(40, 160))
                hop.append(part_merge(p, tag, motion=(q, (0, 0, 0), (dx * 0.5, -D + 1.4, dz * 0.5)), interp=7))
                down.append(part_merge(p, tag, motion=(q, (0, 0, 0), (dx, -(HY - 37.5), dz)), interp=26))
            self.reg(f"rig2_hop_{tag_s}", hop)
            self.reg(f"rig2_down_{tag_s}", down)
            self.reg(f"rig2_far_{tag_s}", [
                f"{at_rig}particle minecraft:block{{block_state:\"minecraft:iron_block\"}} ~ 65.0 ~{num(sgn * 4.0)} 2.6 1.2 2.4 0.3 90 force",
                f"{at_rig}particle minecraft:falling_dust{{block_state:\"minecraft:gray_concrete\"}} ~ 66.0 ~{num(sgn * 5.0)} 2.6 0.6 2.2 0 50 force",
                f"{at_rig}particle minecraft:electric_spark ~ 65.0 ~{num(sgn * 4.0)} 2.5 1.0 2.0 0.4 60 force"])
            self.reg(f"rig2_break_{tag_s}", [fn(f"story/hq/rig2_hop_{tag_s}"), self.sched(f"rig2_down_{tag_s}", 7), fn(f"story/hq/rig2_far_{tag_s}")])
        self.reg("rig2_break", [
            f"execute if score #rg.sgn {OBJ} matches 1 run function {NS}:story/hq/rig2_break_p",
            f"execute if score #rg.sgn {OBJ} matches -1 run function {NS}:story/hq/rig2_break_n",
            f"{at_rig}particle minecraft:block{{block_state:\"minecraft:iron_block\"}} ~ 65.0 ~ 2.2 0.4 2.2 0.25 90 force",
            f"{at_rig}particle minecraft:block{{block_state:\"minecraft:copper_block\"}} ~ 65.0 ~ 2.0 0.4 2.0 0.2 50 force",
            f"{at_rig}particle minecraft:electric_spark ~ 65.0 ~ 2.5 0.6 2.5 0.3 80 force",
            f"{at_rig}particle minecraft:explosion ~ 65.5 ~ 1.5 0.2 1.5 0 3 force",
            f"{at_rig}particle minecraft:large_smoke ~ 65.5 ~ 2.5 0.5 2.5 0.03 30 force",
            f"{at_rig}playsound {NS}:sfx.rig_crash master {PA()} ~ 66.0 ~ 4.0 0.95 1.0",
            "kill @e[tag=angel.rigshadow]"])
        self.reg("rig2_clear", ["kill @e[tag=angel.rigdrop]", "kill @e[tag=angel.rigshadow]", "kill @e[tag=angel.rigbit]", "kill @e[tag=angel.rigpos]"])
        # ---- the tear itself: sound from where it hangs, the first sparks, the fragments, then the sway, the rain, and the fall
        self.reg("rig2_start", [
            f"{at_rig}function {NS}:story/hq/rig2_spawn",
            f"{at_rig}playsound {NS}:sfx.rig_tear master {PA()} ~ ~ ~ 5.0 1.0 1.0",
            f"{at_rig}particle minecraft:flash{{color:[1.0,0.85,0.5,1.0]}} ~ ~{num(HC)} ~ 0 0 0 0 1 force",
            f"{near}as {P()} at @s rotated ~ 0 positioned ^ ^4.5 ^1.2 run function {NS}:story/hq/rig2_bits_spawn",
            self.sched("rig2_bits_fall", 2), self.sched("rig2_bits_kill", 30),
            *sway_calls,
            fn("story/hq/rig2_rain_a"), self.sched("rig2_rain_b", 8), self.sched("rig2_rain_b2", 16), self.sched("rig2_rain_b3", 24), self.sched("rig2_rain_b4", 32),
            self.sched("rig2_bits_spawn2", 14), self.sched("rig2_bits_fall2", 16), self.sched("rig2_bits_kill2", 40),
            self.sched("rig2_fall", self.RIG_FALL_AT)])
        for k in (2, 3, 4):
            self.reg(f"rig2_rain_b{k}", rain(14 if k < 4 else 8))
        self.reg("rig2_bits_spawn2", [f"{near}as {P()} at @s rotated ~ 0 positioned ^ ^4.5 ^1.0 run function {NS}:story/hq/rig2_bits_spawn"])
        self.reg("rig2_bits_fall2", ["execute as @e[tag=angel.rigbit] run data merge entity @s {start_interpolation:0,interpolation_duration:16,"
                                     "transformation:{translation:[0f,-9f,0f]}}"])
        self.reg("rig2_bits_kill2", ["kill @e[tag=angel.rigbit]"])

    # ------------------------------------------------------------------ small effects of scenes 5 to 7
    def _write_misc2(self):
        ox = self.ox
        # the booth's light snaps on: one hard white flare at his face (he stands at the booth anchor, 3.6 tall, facing the stop: the flare is a block
        # in front of his face along the way he looks)
        b = booth_anchor(self.ctx)
        fx = math.radians(b["yaw"])
        px, pz = b["x"] - math.sin(fx) * 1.0, b["z"] + math.cos(fx) * 1.0
        self.reg("booth_flare", [f"particle minecraft:flash{{color:[1.0,0.95,0.85,1.0]}} {num(px)} {num(b['y'] + 3.0)} {num(pz)} 0 0 0 0 1 force",
                                 f"particle minecraft:end_rod {num(px)} {num(b['y'] + 2.6)} {num(pz)} 0.8 1.2 0.4 0.03 24 force"])
        # the eyes light: motes in the glow over the bridge, at the player
        self.reg("eyes_fx", [f"execute at {P()} run particle minecraft:end_rod ~ ~2 ~ 5 2.5 5 0.003 40 force",
                             f"particle minecraft:end_rod {num(96.5 + ox)} 62.0 59.5 3.0 1.5 0.4 0.01 40 force"])
        # the aftershock that throws Rei: dust shaken off the rails round the player, a deep thud from the bridge itself
        self.reg("shock_floor", [f"execute at {P()} run particle minecraft:dust_plume ~ 0.3 ~ 4 0.3 4 0.03 40 force",
                                 f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:gray_concrete\"}} ~ ~3.5 ~ 4 1.2 4 0 36 force"])


def booth_anchor(ctx):
    """The commander's stand as {x, y, z, yaw, pitch} in WORLD coordinates, read from the set module at build time (sets/hq.py: BOOTH_STAND, BOOTH["y0"],
    BOOTH_SCALE), not from tools/world/anchors.json, which only follows the set when the world is rebuilt.  Yaw and pitch are the set's own formula
    (he faces the stop on the bridge and looks down at it).  Also marks the anchor as used."""
    probe = ctx.probe("hq")
    hq = sys.modules["sets.hq"]
    ox, oy, oz = probe.o
    sx, sz = hq.BOOTH_STAND
    y0 = hq.BOOTH["y0"]
    ddx, ddz = sx - 96.5, hq.FACE_Z - sz
    yaw = math.degrees(math.atan2(ddx, ddz))
    pitch = math.degrees(math.atan2(y0 + 1 + 1.62 * hq.BOOTH_SCALE - (hq.BRIDGE_Y + 1 + 1.62), math.hypot(ddx, ddz)))
    try:
        ctx.anchor("hq.booth")
    except KeyError:
        pass
    return dict(x=sx + ox, y=y0 + 1 + oy, z=sz + oz, yaw=round(yaw, 1), pitch=round(pitch, 1))


def cage(ctx):
    if "hq_cage" not in ctx.helpers:
        ctx.helpers["hq_cage"] = Cage(ctx)
    return ctx.helpers["hq_cage"]


def dirty_cmd():
    """Mark the set as touched, so that story/stop restores it."""
    return sset("#hq.dirty", 1)