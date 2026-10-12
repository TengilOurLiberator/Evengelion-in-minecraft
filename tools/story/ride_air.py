"""Scene 1's air attack: five VTOL aircraft big enough to read from the street, circling the walking Angel at different heights and firing
tracers that fly to it and burst in flashes; one is hit, trails fire and smoke across the sky and comes down on outskirts.crash as a
burning wreck that stands there (with its smoke column) for the rest of the scene.  Also the birds on the wires.

Everything is display entities and particles (no real fire, no TNT).  Replaces the old fx.aircraft_setup / crash_functions pair (which
made four small jets that nobody could see at 100 blocks); fx.py is left as it was.

Functions written (all `angel:story/fx/...`): air_tick (per tick while #fx.air is 1), fire1..5 (a salvo of three tracers), tr_spawn, tr_tick,
tr_hit, flash_tick, ac3_hit, ac3_fall, fall_tick, impact_crash, wreck_tick, smoke_tick.  Flags (cleared by halt): #fx.air, #fx.smoke,
#fx.fall, #fx.wreck.  Story flag #f.crash is set at the impact.
"""
import math
import random

import numpy as np

from context import play_at
from core import NS, OBJ, TAG, fn, fnum, num, qaxis, sadd, sc, sset
from models import Part, Rig, summon_part, transformation_nbt

N_AC = 5
HIT = 2                                 # index of the aircraft that is hit (rig "ac3")
SCALE = 3.2                             # the VTOL is 13.4 blocks long, 16.6 across the wings
PHASE = [0.0, 72.0, 144.0, 216.0, 288.0]
RADIUS = [50.0, 58.0, 54.0, 62.0, 48.0]
HEIGHT = [-34.0, -12.0, 6.0, 22.0, -22.0]   # above the orbit centre (the monster's middle, 55 blocks above its feet)
CENTRE_UP = 55.0
AIR_W = 1.1                             # degrees per tick the orbit turns: a lap in 327 ticks (16 s)
BANK = 18.0                             # the aircraft lean into the turn
HIT_TICK, FALL_TICK, FALL_FRAMES = 190, 215, 85
CRASH_LEAD = 26                         # ticks: sfx.crash's impact is 1.3 s into the sound
VOLLEY = 36                             # ticks between the salvos of one aircraft; the five are staggered
VOLLEY_AT = [4, 11, 18, 25, 32]
HIT_RADIUS = 17.0                       # a tracer bursts when it comes this close to the monster's middle


def reg(ctx, path, lines, scheduled=False):
    ctx.extra_functions[path] = lines
    if scheduled:
        ctx.fx_scheduled.append(path)
    return fn(path)


# --------------------------------------------------------------------------------------------------- the model
def vtol_parts(scale=SCALE):
    """A VTOL, nose along +z, light grey with orange lift-fan glows under the wings and a red nose band so that it reads against the sky and the Angel."""
    P_ = Part
    s = scale
    raw = [
        ("fuselage", "light_gray_concrete", (-0.45, -0.3, -2.2), (0.45, 0.4, 2.0)),
        ("nose", "white_concrete", (-0.3, -0.2, 2.0), (0.3, 0.3, 2.7)),
        ("band", "red_concrete", (-0.47, -0.1, 1.5), (0.47, 0.3, 1.9)),
        ("canopy", "light_blue_stained_glass", (-0.3, 0.4, 0.6), (0.3, 0.7, 1.7)),
        ("wing", "gray_concrete", (-2.6, 0.0, -0.8), (2.6, 0.12, 0.6)),
        ("stripeL", "white_concrete", (1.2, 0.121, -0.6), (2.5, 0.14, 0.4)),
        ("stripeR", "white_concrete", (-2.5, 0.121, -0.6), (-1.2, 0.14, 0.4)),
        ("fin", "light_gray_concrete", (-0.06, 0.4, -2.2), (0.06, 1.3, -1.2)),
        ("tailplane", "gray_concrete", (-1.1, 0.35, -2.2), (1.1, 0.43, -1.6)),
        ("podL", "black_concrete", (1.9, -0.15, -0.9), (2.5, 0.35, 0.7)),
        ("podR", "black_concrete", (-2.5, -0.15, -0.9), (-1.9, 0.35, 0.7)),
        ("glowL", "orange_concrete", (2.0, -0.2, -0.85), (2.4, -0.15, 0.65)),
        ("glowR", "orange_concrete", (-2.4, -0.2, -0.85), (-2.0, -0.15, 0.65)),
        ("tailglow", "orange_concrete", (-0.2, -0.1, -2.35), (0.2, 0.25, -2.2)),
    ]
    out = []
    for n, b, lo, hi in raw:
        br = (15, 15) if b == "orange_concrete" else None
        out.append(P_(n, b, tuple(v * s for v in lo), tuple(v * s for v in hi), bright=br))
    return out


def vtol_rig(i):
    r = Rig(f"ac{i + 1}", vtol_parts(), {}, tp_duration=2, view_range=8.0)
    q = qaxis("z", BANK)
    for p in r.parts:
        r.base_motion[p.name] = (q, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    return r


# --------------------------------------------------------------------------------------------------- the orbit (a mirror of what air_tick does)
class Orbit:
    def __init__(self, spawn_xz, ground_y, walk_ticks, speed):
        self.x0, self.z0 = spawn_xz
        self.y = ground_y + CENTRE_UP
        self.speed = speed
        self.walk_ticks = walk_ticks

    def centre(self, t):
        return (self.x0 - self.speed * min(t, self.walk_ticks), self.y, self.z0)

    def state(self, t, i):
        cx, cy, cz = self.centre(t)
        a = math.radians(AIR_W * t + PHASE[i])
        return (cx + RADIUS[i] * (-math.sin(a)), cy + HEIGHT[i], cz + RADIUS[i] * math.cos(a)), AIR_W * t + PHASE[i] + 90.0


def fall_path(orbit, crash_xyz):
    """Frames (x, y, z, yaw, pitch) of the hit aircraft from its orbit position at FALL_TICK to the wreck site: it keeps its heading, sinks, banks
    round and comes in low from the east over the street at the right of the boy's view."""
    p0, yaw0 = orbit.state(FALL_TICK, HIT)
    d0 = np.array([-math.sin(math.radians(yaw0)), 0.0, math.cos(math.radians(yaw0))])
    p0 = np.array(p0)
    c = np.array(crash_xyz, float)
    p1 = p0 + d0 * 42 + np.array([0.0, -14.0, 0.0])
    p2 = c + np.array([34.0, 24.0, 9.0])
    n = FALL_FRAMES
    pts = []
    for k in range(n):
        u = (k + 1) / n
        w = u ** 1.4
        pts.append((1 - w) ** 3 * p0 + 3 * (1 - w) ** 2 * w * p1 + 3 * (1 - w) * w ** 2 * p2 + w ** 3 * c)
    out = []
    for k, b in enumerate(pts):
        a = pts[k - 1] if k else p0
        nx = pts[min(k + 1, n - 1)]
        d = nx - a
        yaw = math.degrees(math.atan2(-d[0], d[2])) if abs(d[0]) + abs(d[2]) > 1e-6 else yaw0
        pitch = math.degrees(math.atan2(-d[1], max(math.hypot(d[0], d[2]), 1e-6)))
        out.append((b[0], b[1], b[2], yaw, max(-30.0, min(65.0, pitch))))
    return out


# --------------------------------------------------------------------------------------------------- the attack
def setup(ctx, spawn, walk_pts, speed, crash_xyz, crash_y_extra=0.0):
    """Registers every function and returns (start_cmds, fall_frames, orbit).  `spawn` and `walk_pts` are anchors (dicts with x, y, z): the monster's
    spawn and its walk, so that the orbit's centre travels with it."""
    prev = (spawn["x"], spawn["z"])
    ticks = 0
    for w in walk_pts:
        ticks += int(round(((w["x"] - prev[0]) ** 2 + (w["z"] - prev[1]) ** 2) ** 0.5 / speed))
        prev = (w["x"], w["z"])
    orbit = Orbit((spawn["x"], spawn["z"]), spawn["y"], ticks, speed)
    rigs = [ctx.register_rig(vtol_rig(i)) for i in range(N_AC)]
    cx, cy, cz = orbit.centre(0)
    start = [f'summon minecraft:marker {num(cx)} {num(cy)} {num(cz)} {{Tags:["{TAG}","angel.cmark"],Rotation:[0f,0f]}}',
             sset("#fx.t", 0), sset("#c36", VOLLEY), sset("#fx.air", 1)]
    for i, rig in enumerate(rigs):
        pos, yaw = orbit.state(0, i)
        start += ctx.rig_spawn(rig, "fly", (pos[0], pos[1], pos[2], yaw, 0.0), seats=False)
    # ---------------- per tick: the centre follows the monster, the aircraft follow the centre, the salvos
    tick = [sadd("#fx.t"),
            f"execute {sc('#fx.t', f'..{ticks}')} as @e[tag=angel.cmark,limit=1] at @s run tp @s ~-{num(speed)} ~ ~ ~{num(AIR_W)} ~",
            f"execute {sc('#fx.t', f'{ticks + 1}..')} as @e[tag=angel.cmark,limit=1] at @s run tp @s ~ ~ ~ ~{num(AIR_W)} ~"]
    for i in range(N_AC):
        tick.append(f"execute as @e[tag=angel.cmark,limit=1] at @s rotated ~{num(PHASE[i])} ~ positioned ^ ^{num(HEIGHT[i])} ^{num(RADIUS[i])} "
                    f"run tp @e[tag=angel.rig_ac{i + 1},tag=angel.rpart] ~ ~ ~ ~90 ~")
    tick += [f"scoreboard players operation #fx.m {OBJ} = #fx.t {OBJ}", f"scoreboard players operation #fx.m {OBJ} %= #c36 {OBJ}"]
    for i in range(N_AC):
        tick.append(f"execute {sc('#fx.m', str(VOLLEY_AT[i]))} if entity @e[tag=angel.rig_ac{i + 1},tag=angel.pt_fuselage,limit=1] "
                    f"run function {NS}:story/fx/fire{i + 1}")
        reg(ctx, f"story/fx/fire{i + 1}", [
            f"execute as @e[tag=angel.rig_ac{i + 1},tag=angel.pt_fuselage,limit=1] at @s facing entity @e[tag=angel.cmark,limit=1] feet "
            f"run function {NS}:story/fx/tr_spawn",
            f"schedule function {NS}:story/fx/fire{i + 1}b 3t append", f"schedule function {NS}:story/fx/fire{i + 1}c 6t append"])
        for suffix in ("b", "c"):
            reg(ctx, f"story/fx/fire{i + 1}{suffix}", [
                f"execute as @e[tag=angel.rig_ac{i + 1},tag=angel.pt_fuselage,limit=1] at @s facing entity @e[tag=angel.cmark,limit=1] feet "
                f"run function {NS}:story/fx/tr_spawn"], scheduled=True)
    # tracers: a thin bright box 7 long that flies 6 blocks a tick along its heading and bursts at the monster
    tick += [f"function {NS}:story/fx/tr_tick", f"function {NS}:story/fx/flash_tick"]
    reg(ctx, "story/fx/tr_spawn", [
        f'summon minecraft:block_display ~ ~ ~ {{Tags:["{TAG}","angel.trc","angel.trnew"],block_state:"minecraft:yellow_concrete",'
        f'brightness:{{sky:15,block:15}},view_range:8.0f,teleport_duration:1,'
        f'{transformation_nbt((-0.3, -0.3, -3.5), (0, 0, 0, 1), (0.6, 0.6, 7.0))}}}',
        "tp @e[tag=angel.trnew] ^ ^-1.2 ^7 ~ ~",
        "tag @e[tag=angel.trnew] remove angel.trnew",
        "particle minecraft:flame ^ ^-1.0 ^6 0.3 0.3 0.3 0.02 6 force"])
    reg(ctx, "story/fx/tr_tick", [
        "execute as @e[tag=angel.trc] at @s run tp @s ^ ^ ^6",
        f"execute as @e[tag=angel.trc] at @s if entity @e[tag=angel.cmark,distance=..{num(HIT_RADIUS)}] run function {NS}:story/fx/tr_hit",
        f"scoreboard players add @e[tag=angel.trc] {OBJ} 1",
        f"kill @e[tag=angel.trc,scores={{{OBJ}=45..}}]"])
    reg(ctx, "story/fx/tr_hit", [
        f'summon minecraft:block_display ~ ~ ~ {{Tags:["{TAG}","angel.flash"],block_state:"minecraft:orange_concrete",'
        f'brightness:{{sky:15,block:15}},view_range:8.0f,interpolation_duration:4,'
        f'{transformation_nbt((-0.4, -0.4, -0.4), (0, 0, 0, 1), (0.8, 0.8, 0.8))}}}',
        "particle minecraft:explosion ~ ~ ~ 1.5 1.5 1.5 0 3 force",
        "particle minecraft:flash{color:[1.0,0.85,0.5,1.0]} ~ ~ ~ 0 0 0 0 1 force",
        "kill @s"])
    reg(ctx, "story/fx/flash_tick", [
        f"execute as @e[tag=angel.flash,tag=!angel.big] run data merge entity @s {{start_interpolation:0,interpolation_duration:5,"
        f"{transformation_nbt((-3.0, -3.0, -3.0), (0, 0, 0, 1), (6.0, 6.0, 6.0))}}}",
        "tag @e[tag=angel.flash,tag=!angel.big] add angel.big",
        f"scoreboard players add @e[tag=angel.flash] {OBJ} 1",
        f"kill @e[tag=angel.flash,scores={{{OBJ}=7..}}]"])
    # ---------------- the hit: a blast on the aircraft, then smoke and fire; later it leaves the orbit and falls
    tick.append(f"execute {sc('#fx.t', str(HIT_TICK))} run function {NS}:story/fx/ac3_hit")
    reg(ctx, "story/fx/ac3_hit", [
        sset("#fx.smoke", 1),
        "execute at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run particle minecraft:explosion_emitter ~ ~ ~ 0 0 0 0 1 force",
        "execute at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run particle minecraft:flash{color:[1.0,0.8,0.4,1.0]} ~ ~1 ~ 0 0 0 0 1 force",
        "execute at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run particle minecraft:lava ~ ~ ~ 3 1 3 0.1 40 force",
        play_at("angel:sfx.explosion_far", 150, 100, 128, 1.5, 1.1, 0.0)])
    tick.append(f"execute {sc('#fx.t', str(FALL_TICK))} run function {NS}:story/fx/ac3_fall")
    reg(ctx, "story/fx/ac3_fall", ["tag @e[tag=angel.rig_ac3] add angel.rig_ac3d", "tag @e[tag=angel.rig_ac3d] remove angel.rig_ac3",
                                   sset("#fx.c", 0), sset("#fx.fall", 1)])
    reg(ctx, "story/fx/smoke_tick", [
        "particle minecraft:large_smoke ~ ~ ~ 1.4 1.0 1.4 0.03 10 force", "particle minecraft:flame ~ ~ ~ 1.2 0.8 1.2 0.04 8 force",
        "particle minecraft:campfire_signal_smoke ~ ~ ~ 0.8 0.5 0.8 0.02 1 force"])
    frames = fall_path(orbit, crash_xyz)
    crash_functions(ctx, crash_xyz, frames)
    ctx.fx_flags |= {"smoke", "fall", "air", "wreck"}
    reg(ctx, "story/fx/air_tick", tick)
    return start, frames, orbit


def crash_functions(ctx, crash_xyz, frames):
    x, y, z = crash_xyz
    lines = []
    for k, (fx_, fy, fz, yaw, pitch) in enumerate(frames):
        lines.append(f"execute if score #fx.c {OBJ} matches {k} positioned {num(fx_)} {num(fy)} {num(fz)} rotated {num(yaw, 2)} {num(pitch, 2)} "
                     f"run tp @e[tag=angel.rig_ac3d,tag=angel.rpart] ~ ~ ~ ~ ~")
    fall_tick = [sadd("#fx.c")] + lines + [
        # a trail of fire and smoke behind it
        "execute at @e[tag=angel.rig_ac3d,tag=angel.pt_fuselage,limit=1] run particle minecraft:large_smoke ~ ~ ~ 1.6 1.0 1.6 0.03 14 force",
        "execute at @e[tag=angel.rig_ac3d,tag=angel.pt_fuselage,limit=1] run particle minecraft:flame ~ ~ ~ 1.2 0.8 1.2 0.05 12 force",
        "execute at @e[tag=angel.rig_ac3d,tag=angel.pt_fuselage,limit=1] run particle minecraft:lava ~ ~ ~ 1.5 0.5 1.5 0.1 3 force",
        f"execute {sc('#fx.c', str(len(frames) - 1))} run function {NS}:story/fx/impact_crash",
        # sfx.crash is 8 s: the falling scream runs for 1.3 s and the impact lands at 1.3 s, so it starts 26 ticks before the last frame
        f"execute {sc('#fx.c', str(max(0, len(frames) - 1 - CRASH_LEAD)))} run " + play_at("angel:sfx.crash", x, y, z, 2.0, 1.0, 0.0)]
    reg(ctx, "story/fx/fall_tick", fall_tick)
    ctx.fx_tick += [f"execute if score #fx.fall {OBJ} matches 1 run function {NS}:story/fx/fall_tick",
                    f"execute if score #fx.smoke {OBJ} matches 1 at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run function {NS}:story/fx/smoke_tick",
                    f"execute if score #fx.air {OBJ} matches 1 run function {NS}:story/fx/air_tick",
                    f"execute if score #fx.wreck {OBJ} matches 1 run function {NS}:story/fx/wreck_tick"]
    # the impact: a ball of fire and smoke, a deep boom, burning wreckage (fire block displays: they burn on screen only)
    wreck = [sset("#fx.fall", 0), sset("#fx.wreck", 1), sset("#f.crash", 1), "kill @e[tag=angel.rig_ac3d]"]
    wreck += [f"particle minecraft:explosion_emitter {num(x)} {num(y + 1)} {num(z)} 0 0 0 0 1 force",
              f"particle minecraft:explosion_emitter {num(x + 3)} {num(y + 2)} {num(z - 2)} 0 0 0 0 1 force",
              f"particle minecraft:flash{{color:[1.0,0.7,0.3,1.0]}} {num(x)} {num(y + 3)} {num(z)} 0 0 0 0 1 force",
              f"particle minecraft:lava {num(x)} {num(y + 1)} {num(z)} 4 2 4 0.1 80 force",
              f"particle minecraft:flame {num(x)} {num(y + 1)} {num(z)} 6 3 6 0.12 220 force",
              f"particle minecraft:large_smoke {num(x)} {num(y + 3)} {num(z)} 5 4 5 0.1 200 force",
              f"particle minecraft:block{{block_state:\"minecraft:gray_concrete\"}} {num(x)} {num(y + 1)} {num(z)} 6 1.5 6 0.6 140 force",
              play_at("angel:sfx.explosion_near", x, y, z, 1.2, 1.0, 0.0)]
    rnd = random.Random(11)
    k = 1.7
    pieces = [("gray_concrete", (-1.8, 0, -0.5), (1.8, 0.9, 0.9)), ("black_concrete", (0.6, 0, -2.2), (2.1, 0.5, 0.3)),
              ("light_gray_concrete", (-3.4, 0, 1.2), (-1.8, 0.35, 2.7)), ("black_concrete", (2.2, 0, 0.9), (3.0, 1.1, 1.7)),
              ("gray_concrete", (-0.4, 0, 1.6), (0.7, 0.4, 3.2)), ("orange_concrete", (-1.0, 0.1, -1.4), (0.2, 0.5, -0.2)),
              ("light_gray_concrete", (-4.6, 0, -1.8), (-2.4, 0.5, -0.6)), ("gray_concrete", (1.4, 0, -3.6), (3.6, 0.7, -2.0))]
    for n, (b, lo, hi) in enumerate(pieces):
        lo2, hi2 = tuple(v * k for v in lo), tuple(v * k for v in hi)
        wreck.append(summon_part(Part(f"w{n}", b, lo2, hi2, qaxis("y", rnd.uniform(0, 360)) if n else (0, 0, 0, 1)), ["angel.wreck"], 0, None, 4.0,
                                 pos=f"{num(x)} {num(y)} {num(z)}"))
    for n in range(10):
        fx_, fz_ = x + rnd.uniform(-5.0, 5.0), z + rnd.uniform(-5.0, 5.0)
        s = rnd.uniform(1.6, 3.2)
        wreck.append(f'summon minecraft:block_display {num(fx_ - s / 2)} {num(y + 0.3)} {num(fz_ - s / 2)} {{Tags:["{TAG}","angel.wreck"],'
                     f'block_state:{{id:"minecraft:fire"}},brightness:{{sky:15,block:15}},view_range:4.0f,'
                     f'{transformation_nbt((0, 0, 0), (0, 0, 0, 1), (s, s, s))}}}')
    reg(ctx, "story/fx/impact_crash", wreck)
    reg(ctx, "story/fx/wreck_tick", [
        f"particle minecraft:campfire_signal_smoke {num(x)} {num(y + 1.5)} {num(z)} 1.5 0.5 1.5 0.01 3 force",
        f"particle minecraft:large_smoke {num(x)} {num(y + 2)} {num(z)} 2.2 1.5 2.2 0.02 3 force",
        f"particle minecraft:flame {num(x)} {num(y + 0.6)} {num(z)} 3.2 0.4 3.2 0.01 4 force"])


def stop_cmds():
    """Take the aircraft away (used when the scene is torn down)."""
    return [sset("#fx.air", 0), "kill @e[tag=angel.cmark]"] + [f"kill @e[tag=angel.rig_ac{i + 1}]" for i in range(N_AC)] + \
           ["kill @e[tag=angel.trc]", "kill @e[tag=angel.flash]"]


# --------------------------------------------------------------------------------------------------- birds off the wires
def birds(ctx, x0=100, x1=150, y=75.0, n=26, seed=7):
    """(spawn commands, fly commands): the birds sit on the wires (the chains at z 121 and 135) from the moment the street is reached; the fly
    commands send them up and play sfx.birds_up (the flock goes at the instant the girl is gone), and a scheduled function removes them."""
    rnd = random.Random(seed)
    spawn, fly = [], []
    for i in range(n):
        x = rnd.uniform(x0, x1)
        z = rnd.choice([121.0, 135.0]) + rnd.uniform(-0.2, 0.2)
        tag = f'"{TAG}","angel.bird"'
        spawn.append(f'summon minecraft:block_display {num(x)} {num(y)} {num(z)} {{Tags:[{tag},"angel.bird{i}"],block_state:"minecraft:black_concrete",'
                     f'view_range:2.0f,interpolation_duration:70,teleport_duration:0,{transformation_nbt((-0.25, 0, -0.14), (0, 0, 0, 1), (0.5, 0.12, 0.28))}}}')
        dx, dz = rnd.uniform(-16, 16), rnd.uniform(-16, 16)
        up = rnd.uniform(12, 24)
        q = qaxis("y", rnd.uniform(-70, 70))
        fly.append(f"data merge entity @e[tag=angel.bird{i},limit=1] {{start_interpolation:0,interpolation_duration:70,"
                   f"{transformation_nbt((dx - 0.25, up, dz - 0.14), q, (0.5, 0.12, 0.28))}}}")
    reg(ctx, "story/fx/birds_kill", ["kill @e[tag=angel.bird]"], True)
    sx, sz = (x0 + x1) / 2, 128.0
    go = fly + [f"schedule function {NS}:story/fx/birds_kill 100t", play_at("angel:sfx.birds_up", x0 + 8.0, y, sz, 2.5, 1.0, 0.0)]
    return spawn, go
