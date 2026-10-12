"""The launch pad's preparation (scene 6, 6.15 to 6.19): twenty seconds of the giant standing in the shaft looking up used to be one still frame.

Now the shaft is dark when he arrives, with warning beacons turning in its corners, four restraint arms holding him at the shoulders; and
  * the arms let go in turn (a hammer blow of sfx.bolt_n, sparks and dust at each, the arm sliding back into the wall): two on the first BASE call,
    one on Misato's answer, one while the commander speaks;
  * the ring lights of the shaft (the sea lanterns at every eighth block, in the set) come on from the bottom up one after another;
  * at "all green" (the end of the commander's word) every ring turns green in a wave from the bottom, the beacons with it;
  * while the launch-charge whine climbs (3 s) white light runs up the rings, three times.

Blocks: the ring cells are read from the built set (they are `sea_lantern` at every eighth block of the four walls); `off` is the wall plating
(`deepslate_tiles`), `green` verdant froglight.  `story/launch/shaft_reset` puts every ring back (called at the cut to the city and by
`story/launch/restore`, which the engine's halt runs).  Entities carry angel.story, angel.launch and angel.lpad (+ angel.lbeacon / angel.lbeam /
angel.larm).
"""
from core import OBJ, TAG, fnum, num, qaxis, sset
from models import Part, part_merge, summon_part, transformation_nbt

FLAG = "#f.shaft"                 # 1 while the rings are not as built (cleared by halt, which also calls the restore)
SHAFT_PROBE = (3009, 50, 9)
BEACON_FLAG = "#f.beacon"
STEP_TICKS = 5                    # one 60 degree step of the beacons every 5 ticks
RING_ON_BLOCK, RING_OFF_BLOCK, RING_GREEN_BLOCK = "minecraft:sea_lantern", "minecraft:deepslate_tiles", "minecraft:verdant_froglight"
BEACON_Y = [12, 28, 44, 60, 76, 92]
ARM_BASE_Y = 25.0                 # world y of the restraint arms' lower edge (his feet are at y 4; the shoulders are about 24 above them)
ARMS = ["w", "e", "n", "s"]


def _ring_planes(o, X1, X2, Z1, Z2):
    """(x0, z0, x1, z1) world rectangles of the four wall planes of a ring (one block thick)."""
    ox, oz = o[0], o[2]
    return [(ox + X1, oz + Z1 - 1, ox + X2, oz + Z1 - 1), (ox + X1, oz + Z2 + 1, ox + X2, oz + Z2 + 1),
            (ox + X1 - 1, oz + Z1, ox + X1 - 1, oz + Z2), (ox + X2 + 1, oz + Z1, ox + X2 + 1, oz + Z2)]


def _arm_parts(i, cx, cz, dx, dz):
    """Parts of one restraint arm, in model space (origin at the shaft's centre line at the arm's height).  (dx, dz): unit vector from the middle
    toward the arm's wall.  The arm reaches from the wall in to 4.4 blocks from the centre."""
    y0, y1 = 0.0, 4.0
    far, near = 7.0, 4.4
    parts = []
    if dx:
        lo_x, hi_x = (near, far) if dx > 0 else (-far, -near)
        parts.append(Part(f"{i}b", "iron_block", (lo_x, y0, -1.6), (hi_x, y1, 1.6)))
        parts.append(Part(f"{i}s", "yellow_concrete", (lo_x, y1, -1.6), (hi_x, y1 + 0.2, 1.6)))
        tip = (near, y0 - 0.2, -1.9), (near + 0.5, y1 + 0.2, 1.9)
        if dx < 0:
            tip = (-near - 0.5, y0 - 0.2, -1.9), (-near, y1 + 0.2, 1.9)
        parts.append(Part(f"{i}t", "black_concrete", tip[0], tip[1]))
        parts.append(Part(f"{i}p", "light_gray_concrete", (lo_x, y0 + 1.2, -0.45), (hi_x, y0 + 2.8, 0.45)))
    else:
        lo_z, hi_z = (near, far) if dz > 0 else (-far, -near)
        parts.append(Part(f"{i}b", "iron_block", (-1.6, y0, lo_z), (1.6, y1, hi_z)))
        parts.append(Part(f"{i}s", "yellow_concrete", (-1.6, y1, lo_z), (1.6, y1 + 0.2, hi_z)))
        tip = (-1.9, y0 - 0.2, near), (1.9, y1 + 0.2, near + 0.5)
        if dz < 0:
            tip = (-1.9, y0 - 0.2, -near - 0.5), (1.9, y1 + 0.2, -near)
        parts.append(Part(f"{i}t", "black_concrete", tip[0], tip[1]))
        parts.append(Part(f"{i}p", "light_gray_concrete", (-0.45, y0 + 1.2, lo_z), (0.45, y0 + 2.8, hi_z)))
    return parts


def register(ctx, geo):
    """Write the launch pad's functions (once per build)."""
    if "story/launch/shaft_reset" in ctx.extra_functions:
        return
    mod = geo.hq_module(ctx)
    probe = ctx.probe("hq")
    o = probe.o
    S = mod.SHAFT
    X1, X2, Z1, Z2, F, T = (S[k] for k in ("x1", "x2", "z1", "z2", "floor", "top"))
    planes = _ring_planes(o, X1, X2, Z1, Z2)
    ring_ys = [y for y in range(F + 1, T + 1) if y % 8 == 0]
    # the cells are what the set says: the runs of sea lanterns of each ring (a numeral or a rail that crosses a ring is left as it is built)
    runs = {}
    for y in ring_ys:
        rr = []
        for (xa, za, xb, zb) in planes:
            cur = None
            for xx in range(xa, xb + 1):
                for zz in range(za, zb + 1):
                    if (probe.name(xx, y, zz) or "").replace("minecraft:", "") == "sea_lantern":
                        if cur is not None and (xx - cur[2] + zz - cur[3]) == 1:
                            cur = (cur[0], cur[1], xx, zz)
                        else:
                            if cur:
                                rr.append(cur)
                            cur = (xx, zz, xx, zz)
                    elif cur:
                        rr.append(cur)
                        cur = None
            if cur:
                rr.append(cur)
        runs[y] = rr
    ex = ctx.extra_functions
    n = len(ring_ys)

    def fills(y, block):
        return [f"fill {xa} {y} {za} {xb} {y} {zb} {block}" for (xa, za, xb, zb) in runs[y]]
    for k, y in enumerate(ring_ys):
        ex[f"story/launch/ring_off_{k}"] = fills(y, RING_OFF_BLOCK)
        ex[f"story/launch/ring_on_{k}"] = fills(y, RING_ON_BLOCK)
        ex[f"story/launch/ring_grn_{k}"] = fills(y, RING_GREEN_BLOCK)
    ex["story/launch/shaft_dark"] = [sset(FLAG, 1)] + [f"function angel:story/launch/ring_off_{k}" for k in range(n)]
    ex["story/launch/shaft_reset"] = [sset(FLAG, 0), sset(BEACON_FLAG, 0)] + [f"function angel:story/launch/ring_on_{k}" for k in range(n)]

    def sched(path, ticks, append=False):
        ctx.fx_scheduled.append(path)
        return f"schedule function angel:{path} {max(1, int(ticks))}t" + (" append" if append else "")
    # rings come on from the bottom, three ticks apart (19 rings: 2.9 s)
    ex["story/launch/shaft_up"] = [f"function angel:story/launch/ring_on_0"] + [sched(f"story/launch/ring_on_{k}", 3 * k) for k in range(1, n)]
    # the final all-green: a wave from the bottom, one ring a tick, beacons and all
    ex["story/launch/shaft_green"] = (["function angel:story/launch/ring_grn_0"] + [sched(f"story/launch/ring_grn_{k}", k) for k in range(1, n)]
                                      + ["execute as @e[tag=angel.lbeacon] run data merge entity @s {block_state:\"minecraft:lime_concrete\"}",
                                         "execute as @e[tag=angel.lbeam] run data merge entity @s {block_state:\"minecraft:lime_concrete\"}"])
    # the charge: white light runs up the rings (on, then green again three ticks later), three passes a second apart
    chase = []
    for p in range(3):
        for k in range(n):
            t0 = p * 20 + k
            chase.append(sched(f"story/launch/ring_on_{k}", t0, append=True) if t0 else "function angel:story/launch/ring_on_0")
            chase.append(sched(f"story/launch/ring_grn_{k}", t0 + 3, append=True))
    ex["story/launch/shaft_chase"] = chase
    # the beacons: a lamp and a two-sided beam in each corner at six heights, turning in 60 degree steps
    spawn = []
    ox, oz = o[0], o[2]
    cxs, czs = ox + (X1 + X2 + 1) / 2.0, oz + (Z1 + Z2 + 1) / 2.0
    for yy in BEACON_Y:
        for (bx, bz) in ((ox + X1 + 0.7, oz + Z1 + 0.7), (ox + X2 + 1 - 0.7, oz + Z1 + 0.7), (ox + X1 + 0.7, oz + Z2 + 1 - 0.7), (ox + X2 + 1 - 0.7, oz + Z2 + 1 - 0.7)):
            lamp = Part("lamp", "red_concrete", (-0.25, -0.25, -0.25), (0.25, 0.25, 0.25), bright=(15, 15))
            beam = Part("beam", "red_concrete", (-1.8, -0.07, -0.07), (1.8, 0.07, 0.07), bright=(15, 15))
            pos = f"{num(bx)} {num(yy + 0.5)} {num(bz)}"
            spawn.append(summon_part(lamp, [TAG, "angel.launch", "angel.lpad", "angel.lbeacon"], tp_duration=0, view_range=3.0, pos=pos))
            spawn.append(summon_part(beam, [TAG, "angel.launch", "angel.lpad", "angel.lbeam"], tp_duration=0, view_range=3.0, pos=pos))
    ex["story/launch/beacons_spawn"] = spawn
    steps = []
    for k in range(6):
        b = Part("beam", "red_concrete", (-1.8, -0.07, -0.07), (1.8, 0.07, 0.07), rot=qaxis("y", 60.0 * k), pivot=(0.0, 0.0, 0.0))
        t, q, s = b.base()
        tf = transformation_nbt(t, q, s)
        steps.append(f"execute if score #l.bk {OBJ} matches {k} as @e[tag=angel.lbeam] run data merge entity @s "
                     f"{{start_interpolation:0,interpolation_duration:{STEP_TICKS},{tf}}}")
    ex["story/launch/beacon_step"] = [f"execute unless score {BEACON_FLAG} {OBJ} matches 1 run return 0",
                                      f"scoreboard players add #l.bk {OBJ} 1", f"execute if score #l.bk {OBJ} matches 6.. run scoreboard players set #l.bk {OBJ} 0",
                                      *steps, sched("story/launch/beacon_step", STEP_TICKS)]
    ex["story/launch/beacons_on"] = [sset(BEACON_FLAG, 1), sset("#l.bk", 0), "function angel:story/launch/beacon_step"]
    # the restraint arms (displays standing between the shaft wall and the giant's shoulders), and how each retracts
    arm_spawn = []
    dirs = {"w": (-1, 0), "e": (1, 0), "n": (0, -1), "s": (0, 1)}
    arm_parts = {}
    for a in ARMS:
        dx, dz = dirs[a]
        parts = _arm_parts(a, cxs, czs, dx, dz)
        arm_parts[a] = parts
        for p in parts:
            arm_spawn.append(summon_part(p, [TAG, "angel.launch", "angel.lpad", "angel.larm", f"angel.larm_{a}", f"angel.pt_{p.name}"], tp_duration=0, view_range=3.0,
                                         pos=f"{num(cxs)} {num(ARM_BASE_Y)} {num(czs)}"))
    ex["story/launch/arms_spawn"] = arm_spawn
    for i, a in enumerate(ARMS):
        dx, dz = dirs[a]
        back = (dx * 2.8, 0.0, dz * 2.8)
        lines = [part_merge(p, f"angel.larm_{a}", motion=(qaxis("y", 0.0), (0, 0, 0), back), interp=8) for p in arm_parts[a]]
        ax, az = cxs + dx * 5.2, czs + dz * 5.2
        ay = ARM_BASE_Y + 2.0
        lines += [f"particle minecraft:electric_spark {num(ax)} {num(ay)} {num(az)} 1.0 1.2 1.0 0.3 50 force",
                  f"particle minecraft:dust_plume {num(ax)} {num(ay)} {num(az)} 1.4 1.4 1.4 0.04 40 force",
                  f"particle minecraft:explosion {num(ax)} {num(ay)} {num(az)} 0.6 0.6 0.6 0 2 force",
                  f"playsound angel:sfx.bolt_{i % 3 + 1} master @a {num(ax)} {num(ay)} {num(az)} 3.0 {num(1.0 - 0.06 * i)} 0.8",
                  f"particle minecraft:falling_dust{{block_state:\"minecraft:gray_concrete\"}} {num(ax)} {num(ay + 6)} {num(az)} 2.5 2 2.5 0 60 force"]
        ex[f"story/launch/arm_{a}"] = lines
    ex["story/launch/arms_we"] = ["function angel:story/launch/arm_w", sched("story/launch/arm_e", 6)]
    ex["story/launch/pad_off"] = ["kill @e[tag=angel.lpad]", sset(BEACON_FLAG, 0)]
    # the restore (halt): the shaft as built
    restore = ctx.extra_functions.get("story/launch/restore")
    line = f"execute if score {FLAG} {OBJ} matches 1 if loaded {SHAFT_PROBE[0]} {SHAFT_PROBE[1]} {SHAFT_PROBE[2]} run function angel:story/launch/shaft_reset"
    if restore is not None and line not in restore:
        restore.append(line)
    ctx.load_extra.append(f"execute unless score #running {OBJ} matches 1 if score {FLAG} {OBJ} matches 1 if loaded {SHAFT_PROBE[0]} {SHAFT_PROBE[1]} "
                          f"{SHAFT_PROBE[2]} run function angel:story/launch/shaft_reset")
    ctx.fx_scheduled.append("story/launch/beacon_step")
    ctx.fx_scheduled.append("story/launch/arm_e")
    ctx.shaft_ring_count = n

