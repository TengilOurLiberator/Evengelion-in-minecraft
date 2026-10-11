"""A character who leads the player, and characters who turn to face things.

    lead(s, ctx, "misato", [Stop(x, y, z, say_at=["4.01"]), (x, y, z), ...], speed=0.14, near=6.0)

`lead` makes the character walk to each stop in turn (`angel:cast/walk`, real movement with the cast's arrival score) and NEVER leaves
the player behind:

  * at a stop she waits until the player is within `near` (6) blocks of HER, looking at him (`cast/look player`) while she waits;
  * while she walks, a monitor (running every tick as a continuous effect, whatever step the story is on) stops her and turns her to look
    back as soon as the player is more than `far` (9) blocks from her; she goes on to the same stop when he is within `near` again;
  * lines in `say_while` start only once the player is within 11 blocks (a conversation does not run away from him); lines in `say_at`
    are said at the stop once he has caught up;
  * a stop the player never reaches has a time limit (3 minutes), after which he is brought to it, so nothing can soft-lock; an
    actionbar hint comes first (after 35 s of waiting).

`companion=("misato", back, side)` sends a second character along the same route a little behind the leader and to one side
(`side` > 0 is the leader's left), so that she is beside the player when he follows the leader at a few blocks' distance.

    face(ctx, "ritsuko", x, y, z)       smooth turn (at most 14 degrees a tick, about a second) to look at a point, then hold still
    face_player(who) / look_ahead(who)  the cast's own player-tracking look on / off

The footsteps (a soft hard-floor step every 9 ticks while she walks) are played by the monitor.
"""
import math

from context import cast_look, tp_player
from core import NS, OBJ, P, fn, num, sset
from engine import C, Cond

FAR = 9.0
NEAR = 6.0
CHAR = "@e[type=minecraft:mannequin,tag=angel.{who},limit=1]"
NAMES = {"misato": "Misato", "ritsuko": "Ritsuko", "gendo": "your father", "rei": "Rei"}


def char(who):
    return CHAR.format(who=who)


class Stop:
    def __init__(self, x, y, z, wait=True, say_while=(), say_at=(), then=(), note=""):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.wait = wait
        self.say_while = list(say_while)
        self.say_at = list(say_at)
        self.then = list(then)
        self.note = note


def _stop(p):
    return p if isinstance(p, Stop) else Stop(*p)


# --------------------------------------------------------------------------------------------------- the monitor
def ensure_monitor(ctx, who, near=NEAR, far=FAR):
    """The per-tick monitor of a leader: pause when the player lags, resume when he is back, footsteps."""
    key = ("lead", who)
    if key in ctx.helpers:
        return
    ctx.helpers[key] = True
    c = char(who)
    flag_on, flag_lp = f"#f.lead_{who}", f"#f.lp_{who}"
    arrived = f"#arrived_{who} angel.cast"
    ctx.extra_functions[f"story/lead/mon_{who}"] = [
        f"execute if score {flag_lp} {OBJ} matches 0 if score {arrived} matches 0 as {c} at @s unless entity {P(f'distance=..{num(far)}')} "
        f"run function {NS}:story/lead/pause_{who}",
        f"execute if score {flag_lp} {OBJ} matches 1 as {c} at @s if entity {P(f'distance=..{num(near)}')} run function {NS}:story/lead/resume_{who}",
        f"scoreboard players set #c9 {OBJ} 9",
        f"scoreboard players operation #lm {OBJ} = #tick {OBJ}",
        f"scoreboard players operation #lm {OBJ} %= #c9 {OBJ}",
        f"execute if score #lm {OBJ} matches 0 if score {flag_lp} {OBJ} matches 0 if score {arrived} matches 0 as {c} at @s "
        f"run playsound minecraft:block.deepslate_tiles.step master @a ~ ~ ~ 0.6 {'1.15' if who == 'ritsuko' else '0.95'} 0.15",
    ]
    ctx.extra_functions[f"story/lead/pause_{who}"] = [
        f'function {NS}:cast/stop {{id:"{who}"}}', sset(flag_lp, 1), cast_look(who, "player")]
    ctx.extra_functions[f"story/lead/resume_{who}"] = [
        sset(flag_lp, 0), cast_look(who, "ahead"), f"function {NS}:cast/walk with storage {NS}:story lead.{who}"]
    ctx.fx_tick.append(f"execute if score {flag_on} {OBJ} matches 1 run function {NS}:story/lead/mon_{who}")


def walk_cmds(who, x, y, z, speed=0.14):
    """Commands that start `who` walking to a point and arm the monitor."""
    return [f'data modify storage {NS}:story lead.{who} set value {{id:"{who}",x:"{num(x)}",y:"{num(y)}",z:"{num(z)}",speed:"{num(speed)}"}}',
            sset(f"#f.lead_{who}", 1), sset(f"#f.lp_{who}", 0), cast_look(who, "ahead"),
            f'function {NS}:cast/walk {{id:"{who}",x:{num(x)},y:{num(y)},z:{num(z)},speed:{num(speed)}}}']


def lead_off(who):
    return [sset(f"#f.lead_{who}", 0), sset(f"#f.lp_{who}", 0)]


def near_char(who, r, est=0.5):
    return Cond([f"as {char(who)} at @s if entity {P(f'distance=..{num(r)}')}"], est, f"player within {r} of {who}")


def arrived(who, est=None):
    return Cond([f"if score #arrived_{who} angel.cast matches 1"], est, f"{who} has arrived")


# --------------------------------------------------------------------------------------------------- the helper
def lead(s, ctx, who, stops, speed=0.14, near=NEAR, far=FAR, companion=None, start=None):
    """Steps that make `who` lead the player along `stops` (see the module doc).  `start`: (x, z) of the place she starts from, used for
    the estimated time of the first leg and the companion's trail.  Returns the last Stop."""
    ensure_monitor(ctx, who, near, far)
    if companion:
        ensure_monitor(ctx, companion[0], near, far)
    prev = start
    name = NAMES.get(who, who)
    last = None
    for n, st in enumerate(stops):
        st = _stop(st)
        d = math.hypot(st.x - prev[0], st.z - prev[1]) if prev else 10.0
        est = d / (speed * 20.0) + 1.0
        cmds = walk_cmds(who, st.x, st.y, st.z, speed)
        if companion and prev:
            cw, back, side = companion
            ux, uz = (st.x - prev[0]) / max(d, 0.01), (st.z - prev[1]) / max(d, 0.01)
            gx = st.x - ux * back + uz * side
            gz = st.z - uz * back - ux * side
            cmds += walk_cmds(cw, gx, st.y, gz, speed)             # the companion has the same monitor: she too waits for the player
        s.do(*cmds, note=f"{who} walks to {st.note or f'({st.x:.1f}, {st.z:.1f})'}")
        for ln in st.say_while:
            s.until(near_char(who, 11.0), timeout=90, est=0.5, note=f"the player is within earshot of {who}")
            s.say(ln)
        if prev and d > 0.5:
            bx, bz = st.x - 2.0 * (st.x - prev[0]) / d, st.z - 2.0 * (st.z - prev[1]) / d
        else:
            bx, bz = st.x - 2.0, st.z
        bring = [f'function {NS}:cast/stop {{id:"{who}"}}',
                 f"tp {char(who)} {num(st.x)} {num(st.y)} {num(st.z)}",
                 tp_player(bx, st.y, bz)]
        s.until(arrived(who, est=est), est=est, timeout=180, on_timeout=bring,
                hint=(f"{name} is waiting for you.", []), hint_after=35, note=f"{who} reaches the stop")
        if st.wait:
            s.do(cast_look(who, "player"), sset(f"#f.lp_{who}", 0), note=f"{who} turns to look for the player")
            s.until(near_char(who, near), timeout=180, est=0.5, on_timeout=bring[2:],
                    hint=(f"{name} is waiting for you.", []), hint_after=35, note=f"the player catches up with {who}")
        for ln in st.say_at:
            s.say(ln)
        if st.then:
            s.do(*st.then)
        prev = (st.x, st.z)
        last = st
    s.do(*lead_off(who), *(lead_off(companion[0]) if companion else []), note=f"{who} stops leading")
    return last


# --------------------------------------------------------------------------------------------------- turning
def _turn_index(ctx, who, x, y, z):
    key = ("turn", who, round(x, 2), round(y, 2), round(z, 2))
    if key not in ctx.helpers:
        k = len(ctx.turns) + 1
        ctx.turns.append(key)
        ctx.helpers[key] = k
        ctx.extra_functions[f"story/turn/t{k}"] = [
            f"scoreboard players remove #f.turn_{k} {OBJ} 1",
            f'execute as {char(who)} at @s run function {NS}:story/turn/step {{x:"{num(x)}",y:"{num(y)}",z:"{num(z)}"}}']
        ctx.fx_tick.append(f"execute if score #f.turn_{k} {OBJ} matches 1.. run function {NS}:story/turn/t{k}")
        ctx.extra_functions["story/turn/step"] = [
            f"execute store result score #ty0 {OBJ} run data get entity @s Rotation[0] 100",
            "$execute anchored eyes run rotate @s facing $(x) $(y) $(z)",
            f"execute store result score #ty1 {OBJ} run data get entity @s Rotation[0] 100",
            f"execute store result score #tp1 {OBJ} run data get entity @s Rotation[1] 100",
            f"scoreboard players operation #ty1 {OBJ} -= #ty0 {OBJ}",
            f"scoreboard players set #c36000 {OBJ} 36000",
            f"scoreboard players operation #ty1 {OBJ} %= #c36000 {OBJ}",
            f"execute if score #ty1 {OBJ} matches 18001.. run scoreboard players remove #ty1 {OBJ} 36000",
            f"execute if score #ty1 {OBJ} matches 1401.. run scoreboard players set #ty1 {OBJ} 1400",
            f"execute if score #ty1 {OBJ} matches ..-1401 run scoreboard players set #ty1 {OBJ} -1400",
            f"scoreboard players operation #ty0 {OBJ} += #ty1 {OBJ}",
            f"execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #ty0 {OBJ}",
            f"execute if score #tp1 {OBJ} matches 4501.. run scoreboard players set #tp1 {OBJ} 4500",
            f"execute if score #tp1 {OBJ} matches ..-3001 run scoreboard players set #tp1 {OBJ} -3000",
            f"execute store result entity @s Rotation[1] float 0.01 run scoreboard players get #tp1 {OBJ}"]
    return ctx.helpers[key]


def face(ctx, who, x, y, z, ticks=16):
    """Commands: `who` stops following the player with her eyes and turns, smoothly, to look at the point (x, y, z), and stays so."""
    k = _turn_index(ctx, who, x, y, z)
    return [cast_look(who, "ahead"), sset(f"#f.turn_{k}", ticks)]


def face_player(who):
    return cast_look(who, "player")


def look_ahead(who):
    return cast_look(who, "ahead")
