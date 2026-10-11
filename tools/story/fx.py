"""Effects built from particles, sounds and display entities: birds, the ground jolt, the aircraft circling the monster and firing, the
one that comes down, the burning wreck, the mine's fireball and mushroom cloud, dust.

Nothing here uses real fire, real explosions or TNT: flames are `fire` block *displays* (they burn on screen and nowhere else), blasts are
particles and sounds, so neither the set nor the player can be hurt.
"""
import math
import random

import numpy as np

from context import play_at, play_player
from core import CFG, NS, OBJ, P, PA, TAG, fn, fnum, num, qaxis, sadd, sc, sset, ssub
from models import Part, aircraft_rig, transformation_nbt, summon_part

AIR_W = 0.9                     # degrees per tick the orbit turns (a lap in 400 ticks = 20 s)
CENTER_SPEED = 0.15             # blocks per tick the orbit centre drifts west with the monster
CENTER_TICKS = 361              # it walks from angel_spawn to angel_walk_4 in this many ticks (16 + 16 + 12 + 10 blocks at 0.15)
AC_PHASE = [0.0, 90.0, 180.0, 270.0]
AC_R = [52.0, 58.0, 50.0, 56.0]
AC_H = [6.0, 15.0, -3.0, 10.0]
HIT_TICK, FALL_TICK, FALL_FRAMES = 190, 215, 85
VOLLEY = 36                     # ticks between the volleys of one aircraft; the four are staggered
VOLLEY_AT = [6, 15, 24, 33]


def reg(ctx, path, lines, scheduled=False):
    ctx.extra_functions[path] = lines
    if scheduled:
        ctx.fx_scheduled.append(path)
    return fn(path)


# --------------------------------------------------------------------------------------------------- birds off the wires
def birds(ctx, x0=104, x1=150, y=75.0, n=14, seed=7):
    rnd = random.Random(seed)
    spawn, fly = [], []
    for i in range(n):
        x = rnd.uniform(x0, x1)
        z = rnd.choice([121.0, 135.0]) + rnd.uniform(-0.2, 0.2)
        tag = f'"{TAG}","angel.bird"'
        spawn.append(f'summon minecraft:block_display {num(x)} {num(y)} {num(z)} {{Tags:[{tag},"angel.bird{i}"],block_state:"minecraft:black_concrete",'
                     f'view_range:1.5f,interpolation_duration:70,teleport_duration:0,{transformation_nbt((-0.12, 0, -0.07), (0, 0, 0, 1), (0.24, 0.05, 0.14))}}}')
        dx, dz = rnd.uniform(-14, 14), rnd.uniform(-14, 14)
        up = rnd.uniform(11, 20)
        q = qaxis("y", rnd.uniform(-70, 70))
        fly.append(f"data merge entity @e[tag=angel.bird{i},limit=1] {{start_interpolation:0,interpolation_duration:70,"
                   f"{transformation_nbt((dx - 0.12, up, dz - 0.07), q, (0.24, 0.05, 0.14))}}}")
    reg(ctx, "story/fx/birds_fly", fly, True)
    reg(ctx, "story/fx/birds_kill", ["kill @e[tag=angel.bird]"], True)
    sx, sz = (x0 + x1) / 2, 128.0
    return spawn + [f"schedule function {NS}:story/fx/birds_fly 3t", f"schedule function {NS}:story/fx/birds_kill 100t",
                    play_at("minecraft:entity.parrot.fly", sx, y, sz, 3.0, 1.1), play_at("minecraft:entity.bat.takeoff", sx, y, sz, 3.0, 1.3)]


# --------------------------------------------------------------------------------------------------- the ground jolt
def jolt(ctx):
    """A deep, far-off thump and dust shaken loose around the player.  The camera is NOT shaken: that is for the stomach's sake in VR."""
    lines = [play_at("minecraft:entity.generic.explode", 200, 64, 128, 8.0, 0.45, 0.9),
             play_at("minecraft:entity.warden.emerge", 200, 64, 128, 8.0, 0.5, 0.8),
             f"execute at {P()} run particle minecraft:block{{block_state:\"minecraft:dirt\"}} ~ ~0.1 ~ 3 0.1 3 0.15 40 force",
             f"execute at {P()} run particle minecraft:dust_plume ~ ~0.5 ~ 4 0.5 4 0.03 60 force",
             f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:stone\"}} ~ ~4 ~ 5 1.5 5 0.0 50 force",
             f"schedule function {NS}:story/fx/jolt2 14t"]
    ctx.fx_scheduled.append("story/fx/jolt2")
    reg(ctx, "story/fx/jolt2", [play_at("minecraft:entity.generic.explode", 190, 64, 128, 6.0, 0.35, 0.8),
                                f"execute at {P()} run particle minecraft:dust_plume ~ ~0.5 ~ 4 0.5 4 0.03 40 force",
                                f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:stone\"}} ~ ~4 ~ 5 1.5 5 0.0 30 force"])
    return lines


# --------------------------------------------------------------------------------------------------- the aircraft
def orbit_state(t, ac):
    """Position and heading of aircraft `ac` (0..3) after the carousel has moved `t` ticks.  Mirrors what air_tick does on the server."""
    cx = 228.5 - CENTER_SPEED * min(t, CENTER_TICKS)
    psi = AIR_W * t
    a = math.radians(psi + AC_PHASE[ac])
    fx, fz = -math.sin(a), math.cos(a)
    return (cx + AC_R[ac] * fx, 93.0 + AC_H[ac], 128.5 + AC_R[ac] * fz), psi + AC_PHASE[ac] + 90.0


def aircraft_setup(ctx, scale=2.0):
    """Commands that create the four aircraft and the orbit marker; and the per-tick function they need.  Returns (start_cmds, rigs)."""
    rigs = [ctx.register_rig(aircraft_rig(f"ac{i + 1}", scale)) for i in range(4)]
    start = [f'summon minecraft:marker 228.5 93 128.5 {{Tags:["{TAG}","angel.cmark"],Rotation:[0f,0f]}}',
             sset("#fx.t", 0), sset("#c36", VOLLEY), sset("#fx.air", 1)]
    for i, rig in enumerate(rigs):
        pos, yaw = orbit_state(0, i)
        start += ctx.rig_spawn(rig, "fly", (pos[0], pos[1], pos[2], yaw, 0.0), seats=False)
    # --- per tick
    tick = [sadd("#fx.t"),
            f"execute {sc('#fx.t', f'..{CENTER_TICKS}')} as @e[tag=angel.cmark,limit=1] at @s run tp @s ~-{CENTER_SPEED} ~ ~ ~{AIR_W} ~",
            f"execute {sc('#fx.t', f'{CENTER_TICKS + 1}..')} as @e[tag=angel.cmark,limit=1] at @s run tp @s ~ ~ ~ ~{AIR_W} ~"]
    for i in range(4):
        tick.append(f"execute as @e[tag=angel.cmark,limit=1] at @s rotated ~{num(AC_PHASE[i])} ~ positioned ^ ^{num(AC_H[i])} ^{num(AC_R[i])} "
                    f"run tp @e[tag=angel.rig_ac{i + 1},tag=angel.part] ~ ~ ~ ~90 ~")
    tick += [f"scoreboard players operation #fx.m {OBJ} = #fx.t {OBJ}", f"scoreboard players operation #fx.m {OBJ} %= #c36 {OBJ}"]
    for i in range(4):
        tick.append(f"execute {sc('#fx.m', str(VOLLEY_AT[i]))} if entity @e[tag=angel.rig_ac{i + 1},tag=angel.pt_fuselage,limit=1] "
                    f"run function {NS}:story/fx/fire{i + 1}")
        reg(ctx, f"story/fx/fire{i + 1}", [
            f"execute as @e[tag=angel.rig_ac{i + 1},tag=angel.pt_fuselage,limit=1] at @s facing entity @e[tag=angel.cmark,limit=1] feet "
            f"run function {NS}:story/fx/tracer",
            f"schedule function {NS}:story/fx/impact 13t append"])
    ctx.fx_scheduled.append("story/fx/impact")
    reg(ctx, "story/fx/tracer", [f"particle minecraft:end_rod ^ ^ ^{k} 0 0 0 0 1 force" for k in range(5, 60, 3)]
        + [f"particle minecraft:flame ^ ^-0.5 ^3 0.2 0.2 0.2 0.02 4 force",
           f"playsound minecraft:entity.firework_rocket.launch ambient {PA()} ~ ~ ~ 4 0.85 0.3"])
    reg(ctx, "story/fx/impact", [
        f"execute at @e[tag=angel.cmark,limit=1] run particle minecraft:explosion ~{random.Random(1).randint(-4, 4)} ~{random.Random(2).randint(-12, 12)} ~ 5 7 5 0 3 force",
        f"execute at @e[tag=angel.cmark,limit=1] run particle minecraft:flash{{color:[1.0,0.85,0.5,1.0]}} ~ ~ ~ 0 0 0 0 1 force",
        f"execute at @e[tag=angel.cmark,limit=1] run playsound minecraft:entity.generic.explode ambient {PA()} ~ ~ ~ 6 1.3 0.35"])
    # the hit: smoke from the third aircraft; then it leaves its orbit and falls
    tick.append(f"execute {sc('#fx.t', str(HIT_TICK))} run function {NS}:story/fx/ac3_hit")
    reg(ctx, "story/fx/ac3_hit", [sset("#fx.smoke", 1), play_at("minecraft:entity.generic.explode", 150, 100, 128, 5.0, 1.0, 0.4)])
    tick.append(f"execute {sc('#fx.t', str(FALL_TICK))} run function {NS}:story/fx/ac3_fall")
    ctx.fx_flags = getattr(ctx, "fx_flags", set()) | {"smoke", "fall", "air"}
    return start, rigs, tick


def crash_route(ctx, crash_xyz):
    """Frames (x, y, z, yaw, pitch) of aircraft 3 coming down from its orbit position at FALL_TICK to the crash site, as functions
    `story/fx/fall_frame` driven by #fx.c."""
    p0, yaw0 = orbit_state(FALL_TICK, 2)
    d0 = np.array([-math.sin(math.radians(yaw0)), 0.0, math.cos(math.radians(yaw0))])
    p0 = np.array(p0)
    c = np.array(crash_xyz, float)
    p1 = p0 + d0 * 38 + np.array([0, -8.0, 0])
    p2 = c + np.array([22.0, 26.0, -6.0])
    frames = []
    n = FALL_FRAMES
    prev = None
    for k in range(n):
        u = (k + 1) / n
        w = u ** 1.5
        b = (1 - w) ** 3 * p0 + 3 * (1 - w) ** 2 * w * p1 + 3 * (1 - w) * w ** 2 * p2 + w ** 3 * c
        frames.append(b)
    out = []
    for k, b in enumerate(frames):
        a = frames[k - 1] if k else p0
        nx = frames[min(k + 1, n - 1)]
        d = nx - a
        yaw = math.degrees(math.atan2(-d[0], d[2])) if abs(d[0]) + abs(d[2]) > 1e-6 else yaw0
        pitch = math.degrees(math.atan2(-d[1], max(math.hypot(d[0], d[2]), 1e-6)))
        out.append((b[0], b[1], b[2], yaw, max(-40.0, min(70.0, pitch))))
    return out


def crash_functions(ctx, crash_xyz, frames):
    """ac3_fall, fall_tick, impact and the wreck."""
    x, y, z = crash_xyz
    lines = []
    for k, (fx_, fy, fz, yaw, pitch) in enumerate(frames):
        lines.append(f"execute if score #fx.c {OBJ} matches {k} positioned {num(fx_)} {num(fy)} {num(fz)} rotated {num(yaw, 2)} {num(pitch, 2)} "
                     f"run tp @e[tag=angel.rig_ac3d,tag=angel.part] ~ ~ ~ ~ ~")
    fall_tick = [sadd("#fx.c")] + lines + [
        f"execute at @e[tag=angel.rig_ac3d,tag=angel.pt_fuselage,limit=1] run particle minecraft:large_smoke ~ ~ ~ 0.6 0.6 0.6 0.02 8 force",
        f"execute at @e[tag=angel.rig_ac3d,tag=angel.pt_fuselage,limit=1] run particle minecraft:flame ~ ~ ~ 0.5 0.5 0.5 0.03 6 force",
        f"execute {sc('#fx.c', str(len(frames) - 1))} run function {NS}:story/fx/impact_crash"]
    reg(ctx, "story/fx/fall_tick", fall_tick)
    reg(ctx, "story/fx/ac3_fall", ["tag @e[tag=angel.rig_ac3] add angel.rig_ac3d", "tag @e[tag=angel.rig_ac3d] remove angel.rig_ac3",
                                   sset("#fx.c", 0), sset("#fx.fall", 1), sset("#fx.smoke", 0),
                                   play_at("minecraft:entity.firework_rocket.twinkle", 120, 90, 140, 6.0, 0.6, 0.4)])
    ctx.fx_tick += [f"execute if score #fx.fall {OBJ} matches 1 run function {NS}:story/fx/fall_tick",
                    f"execute if score #fx.smoke {OBJ} matches 1 at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run "
                    f"function {NS}:story/fx/smoke_tick",
                    f"execute if score #fx.air {OBJ} matches 1 run function {NS}:story/fx/air_tick",
                    f"execute if score #fx.wreck {OBJ} matches 1 run function {NS}:story/fx/wreck_tick"]
    ctx.fx_flags = getattr(ctx, "fx_flags", set()) | {"wreck", "fall", "smoke", "air"}
    reg(ctx, "story/fx/smoke_tick", ["particle minecraft:large_smoke ~ ~ ~ 0.5 0.5 0.5 0.02 6 force",
                                     "particle minecraft:flame ~ ~ ~ 0.4 0.4 0.4 0.02 4 force"])
    # the impact: a ball of fire and smoke, a deep boom, burning wreckage (fire block displays: they burn on screen only)
    wreck = [sset("#fx.fall", 0), sset("#fx.wreck", 1), sset("#f.crash", 1), "kill @e[tag=angel.rig_ac3d]"]
    wreck += [f"particle minecraft:explosion_emitter {num(x)} {num(y + 1)} {num(z)} 0 0 0 0 1 force",
              f"particle minecraft:flash{{color:[1.0,0.7,0.3,1.0]}} {num(x)} {num(y + 3)} {num(z)} 0 0 0 0 1 force",
              f"particle minecraft:lava {num(x)} {num(y + 1)} {num(z)} 3 2 3 0.1 50 force",
              f"particle minecraft:flame {num(x)} {num(y + 1)} {num(z)} 4 2 4 0.1 120 force",
              f"particle minecraft:large_smoke {num(x)} {num(y + 3)} {num(z)} 3 3 3 0.08 120 force",
              f"particle minecraft:block{{block_state:\"minecraft:gray_concrete\"}} {num(x)} {num(y + 1)} {num(z)} 4 1 4 0.5 80 force",
              play_at("minecraft:entity.generic.explode", x, y, z, 10.0, 0.8, 0.9),
              play_at("minecraft:entity.dragon_fireball.explode", x, y, z, 8.0, 0.7, 0.7),
              play_at("minecraft:entity.lightning_bolt.impact", x, y, z, 6.0, 0.6, 0.6)]
    rnd = random.Random(11)
    pieces = [("gray_concrete", (-1.8, 0, -0.5), (1.8, 0.9, 0.9)), ("black_concrete", (0.6, 0, -2.2), (2.1, 0.5, 0.3)),
              ("light_gray_concrete", (-3.4, 0, 1.2), (-1.8, 0.35, 2.7)), ("black_concrete", (2.2, 0, 0.9), (3.0, 1.1, 1.7)),
              ("gray_concrete", (-0.4, 0, 1.6), (0.7, 0.4, 3.2)), ("orange_concrete", (-1.0, 0.1, -1.4), (0.2, 0.5, -0.2))]
    for n, (b, lo, hi) in enumerate(pieces):
        wreck.append(summon_part(Part(f"w{n}", b, lo, hi, qaxis("y", rnd.uniform(0, 360)) if n else (0, 0, 0, 1)), ["angel.wreck"], 0, None, 2.0,
                                 pos=f"{num(x)} {num(y)} {num(z)}"))
    for n in range(5):
        fx_, fz_ = x + rnd.uniform(-2.6, 2.6), z + rnd.uniform(-2.6, 2.6)
        s = rnd.uniform(1.1, 1.8)
        wreck.append(f'summon minecraft:block_display {num(fx_ - s / 2)} {num(y + 0.3)} {num(fz_ - s / 2)} {{Tags:["{TAG}","angel.wreck"],'
                     f'block_state:{{id:"minecraft:fire"}},brightness:{{sky:15,block:15}},view_range:1.5f,'
                     f'{transformation_nbt((0, 0, 0), (0, 0, 0, 1), (s, s, s))}}}')
    reg(ctx, "story/fx/impact_crash", wreck)
    reg(ctx, "story/fx/wreck_tick", [f"particle minecraft:campfire_signal_smoke {num(x)} {num(y + 1.5)} {num(z)} 0.8 0.5 0.8 0.01 2 force",
                                     f"particle minecraft:large_smoke {num(x)} {num(y + 2)} {num(z)} 1.2 1.5 1.2 0.02 1 force",
                                     f"particle minecraft:flame {num(x)} {num(y + 0.6)} {num(z)} 1.8 0.3 1.8 0.01 2 force"])
    ctx.fx_flags |= {"wreck"}


def air_functions(ctx, tick_lines):
    reg(ctx, "story/fx/air_tick", tick_lines)


def air_stop_cmds():
    """Take the aircraft away (they fly off into the smoke), at the end of the scene."""
    return [sset("#fx.air", 0), "kill @e[tag=angel.cmark]", "kill @e[tag=angel.rig_ac1]", "kill @e[tag=angel.rig_ac2]",
            "kill @e[tag=angel.rig_ac3]", "kill @e[tag=angel.rig_ac4]"]


# --------------------------------------------------------------------------------------------------- the mine: fireball and mushroom
def mushroom(ctx, base, grow_ticks=100):
    """Fireball then a mushroom cloud over `base` (x, y, z) = the monster's feet.  Returns (spawn_cmds, step_functions): the spawn creates
    everything tiny; scheduled functions grow it."""
    bx, by, bz = base
    glow = 'brightness:{sky:15,block:15}'

    def disp(tag, block, lo, size, rot=(0, 0, 0, 1), vr=16.0):
        t = lo
        return (f'summon minecraft:block_display {num(bx)} {num(by)} {num(bz)} {{Tags:["{TAG}","angel.cloud","angel.cl_{tag}"],block_state:"minecraft:{block}",'
                f'{glow},view_range:{fnum(vr)},interpolation_duration:20,{transformation_nbt(t, rot, size)}}}')

    tiny = 0.05
    spawn = []
    parts = {}
    rots = [(0, 0, 0, 1), qaxis("y", 45), qaxis("x", 45), qaxis("z", 45)]
    for i, r in enumerate(rots):
        spawn.append(disp(f"fb{i}", "orange_concrete" if i % 2 == 0 else "yellow_concrete", (0, 30, 0), (tiny, tiny, tiny), r))
    spawn.append(disp("stem", "gray_concrete", (-2.0, 0, -2.0), (4.0, tiny, 4.0)))
    spawn.append(disp("capA", "white_concrete", (0, 30, 0), (tiny, tiny, tiny)))
    spawn.append(disp("capB", "light_gray_concrete", (0, 30, 0), (tiny, tiny, tiny), qaxis("y", 45)))
    spawn.append(disp("skirt", "gray_concrete", (0, 30, 0), (tiny, tiny, tiny)))

    def merge(tag, lo, size, rot=(0, 0, 0, 1), dur=20):
        return (f"data merge entity @e[tag=angel.cl_{tag},limit=1] {{start_interpolation:0,interpolation_duration:{dur},"
                f"{transformation_nbt(lo, rot, size)}}}")

    r1 = 15.0
    grow1 = [_centered_cube_merge(f"fb{i}", (0, 30, 0), r1, q, 14) for i, q in enumerate(rots)]
    grow2 = [merge("stem", (-3.0, 0, -3.0), (6.0, 40.0, 6.0), dur=90),
             _centered_cube_merge("capA", (0, 58, 0), 1.0, (0, 0, 0, 1), 90, size=(30.0, 12.0, 30.0)),
             _centered_cube_merge("capB", (0, 60, 0), 1.0, qaxis("y", 45), 90, size=(30.0, 9.0, 30.0)),
             _centered_cube_merge("skirt", (0, 50, 0), 1.0, (0, 0, 0, 1), 90, size=(21.0, 5.0, 21.0))]
    shrink = [_centered_cube_merge(f"fb{i}", (0, 30, 0), 4.0, q, 60) for i, q in enumerate(rots)]
    f1 = reg(ctx, "story/fx/cloud_1", grow1)
    f2 = reg(ctx, "story/fx/cloud_2", grow2 + shrink)
    f3 = reg(ctx, "story/fx/cloud_3", [f"particle minecraft:campfire_signal_smoke {num(bx)} {num(by + 55)} {num(bz)} 9 6 9 0.02 12 force"])
    ctx.fx_scheduled += ["story/fx/cloud_1", "story/fx/cloud_2"]
    return spawn, [f"schedule function {NS}:story/fx/cloud_1 3t", f"schedule function {NS}:story/fx/cloud_2 40t"]


def _centered_cube_merge(tag, centre, k, rot, dur, size=None):
    s = size or (k, k, k)
    # a cube of size s centred on `centre`, rotated about its own centre
    half = (-s[0] / 2, -s[1] / 2, -s[2] / 2)
    from core import qrot, vadd
    off = qrot(rot, half)
    t = vadd(centre, off)
    return (f"data merge entity @e[tag=angel.cl_{tag},limit=1] {{start_interpolation:0,interpolation_duration:{dur},"
            f"{transformation_nbt(t, rot, s)}}}")


# --------------------------------------------------------------------------------------------------- dust and small things
def dust_at(x, y, z, n=40, spread=1.5):
    return [f"particle minecraft:dust_plume {num(x)} {num(y)} {num(z)} {num(spread)} 0.4 {num(spread)} 0.02 {n} force",
            f"particle minecraft:block{{block_state:\"minecraft:dirt\"}} {num(x)} {num(y)} {num(z)} {num(spread)} 0.2 {num(spread)} 0.2 {n // 2} force"]


def flash_burst():
    """A white-out: flash particles right in front of the player's eyes, a few ticks apart (three are scheduled by the caller)."""
    return [f"execute at {P()} anchored eyes positioned ^ ^ ^0.4 run particle minecraft:flash{{color:[1.0,1.0,1.0,1.0]}} ~ ~ ~ 0 0 0 0 1 force"]
