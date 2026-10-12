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

Personal space.  A character who WAITS (a stop with wait=True, her companion beside her) never stands within SPACE (1.8) blocks of the player:
while she waits for him to catch up she is "armed" with an escape point 2.6 blocks on along the way she arrived (her own route: always
walkable), and when he walks into her space she walks there (`angel:cast/walk`, not a teleport) and turns back to look at him.  A companion's
place beside the leader is never closer than 2.0 blocks to the side and 3.0 behind.  `space_on(ctx, who, x, y, z)` / `space_off(who)` arm and
disarm the same rule for a character outside a lead (the loop door of scene 4).  The rule does not apply while she walks (a walking
character is stopped by the pause rule above when he lags, and he cannot overtake her at her own walking speed without meaning to).
"""
import math

from context import cast_look, tp_player
from core import NS, OBJ, P, fn, num, sset
from engine import C, Cond
from objective import follow_objective

FAR = 9.0
NEAR = 6.0
SPACE = 1.8                  # a waiting character never stands closer than this to the player
SPACE_STEP = 2.6             # ... and steps this far on when he walks into her
COMPANION_MIN_SIDE = 2.0     # a companion walks at least this far to the side of the leader's line and this far behind the leader
COMPANION_MIN_BACK = 3.0
CHAR = "@e[type=minecraft:mannequin,tag=angel.{who},limit=1]"
NAMES = {"misato": "Misato", "ritsuko": "Ritsuko", "gendo": "your father", "rei": "Rei"}


def char(who):
    return CHAR.format(who=who)


class Stop:
    """A place to walk to.  wait: stand there until the player has caught up; space: while she waits she keeps SPACE blocks from him by
    stepping on along the way she arrived (False: she stays put, for a stop with a wall or a door straight ahead); escape=(dx, dz): a unit
    direction to step in instead (to the side of the way she came, say)."""

    def __init__(self, x, y, z, wait=True, say_while=(), say_at=(), then=(), note="", space=True, escape=None):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.wait = wait
        self.space = space
        self.escape = escape
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
        f"execute if score #lm {OBJ} matches 0 unless score #hush {OBJ} matches 1 if score {flag_lp} {OBJ} matches 0 if score {arrived} matches 0 as {c} at @s "
        f"run playsound minecraft:block.deepslate_tiles.step master @a ~ ~ ~ 0.6 {'1.15' if who == 'ritsuko' else '0.95'} 0.15",
    ]
    ctx.extra_functions[f"story/lead/pause_{who}"] = [
        f'function {NS}:cast/stop {{id:"{who}"}}', sset(flag_lp, 1), cast_look(who, "player")]
    ctx.extra_functions[f"story/lead/resume_{who}"] = [
        sset(flag_lp, 0), cast_look(who, "ahead"), f"function {NS}:cast/walk with storage {NS}:story lead.{who}"]
    ctx.fx_tick.append(f"execute if score {flag_on} {OBJ} matches 1 run function {NS}:story/lead/mon_{who}")


def ensure_space(ctx, who):
    """The per-tick personal-space rule of `who` (a continuous effect, armed by the flag #f.sp_<who>: 1 armed, 2 stepping away)."""
    key = ("space", who)
    if key in ctx.helpers:
        return
    ctx.helpers[key] = True
    c = char(who)
    flag = f"#f.sp_{who}"
    ctx.extra_functions[f"story/lead/sp_{who}"] = [
        f"execute if score {flag} {OBJ} matches 1 if score #arrived_{who} angel.cast matches 1 as {c} at @s "
        f"if entity {P(f'distance=..{num(SPACE)}')} run function {NS}:story/lead/space_{who}",
        f"execute if score {flag} {OBJ} matches 2 as {c} at @s unless entity {P(f'distance=..{num(SPACE + 0.6)}')} run {sset(flag, 1)}"]
    ctx.extra_functions[f"story/lead/space_{who}"] = [
        sset(flag, 2), f"function {NS}:cast/walk with storage {NS}:story space.{who}"]
    ctx.fx_tick.append(f"execute if score {flag} {OBJ} matches 1..2 run function {NS}:story/lead/sp_{who}")


def _set_of(x):
    return "outskirts" if x < 1000 else "city" if x < 2000 else "geofront" if x < 3000 else "hq"


def _floor_ok(ctx, x, y, z):
    """floor within 0.75 of y under (x, z) and two blocks of headroom, in the built voxel set"""
    probe = ctx.probe(_set_of(x))
    if probe.solid(x, y + 0.6, z) or probe.solid(x, y + 1.6, z):
        return False
    sf = probe.surface(x, z, y)
    return sf is not None and abs(sf - y) <= 0.75


def way_clear(ctx, x, y, z, ex, ez, length=SPACE_STEP):
    """True when the straight line from (x, y, z) `length` blocks in direction (ex, ez) has floor under it (within 0.75) and two blocks of
    headroom all along, in the built voxel set (so an escape step never walks a character into a wall or off a ledge)."""
    probe = ctx.probe(_set_of(x))
    t = 0.4
    while t <= length + 1e-6:
        px, pz = x + ex * t, z + ez * t
        if probe.solid(px, y + 0.6, pz) or probe.solid(px, y + 1.6, pz):
            return False
        sf = probe.surface(px, pz, y)
        if sf is None or abs(sf - y) > 0.75:
            return False
        t += 0.4
    return True


def space_on(ctx, who, x, y, z, speed=0.12):
    """Arm the personal-space rule of `who` with the escape point (x, y, z): she walks there when the player comes within SPACE blocks."""
    ensure_space(ctx, who)
    return [f'data modify storage {NS}:story space.{who} set value {{id:"{who}",x:"{num(x)}",y:"{num(y)}",z:"{num(z)}",speed:"{num(speed)}"}}',
            sset(f"#f.sp_{who}", 1)]


def space_off(who):
    return [sset(f"#f.sp_{who}", 0)]


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
def lead(s, ctx, who, stops, speed=0.14, near=NEAR, far=FAR, companion=None, start=None, follow=True, follow_text=None):
    """Steps that make `who` lead the player along `stops` (see the module doc).  `start`: (x, z) of the place she starts from, used for
    the estimated time of the first leg and the companion's trail.  Returns the last Stop.
    `follow`: every wait of the walk carries the objective "Follow Misato" / "Follow Dr. Akagi" attached to the leader (objective.follow_objective:
    it shows only when the player is more than 8 blocks behind her or has stood still for 10 s); `follow_text` renames it ("Go through the door");
    follow=False for a walk that has an objective of its own."""
    obj_all = follow_objective(who) if follow else None
    obj_first = follow_objective(who, follow_text) if (follow and follow_text) else obj_all           # `follow_text` names the objective of the FIRST stop only
    ensure_monitor(ctx, who, near, far)
    if companion:
        ensure_monitor(ctx, companion[0], near, far)
        cw_, back_, side_ = companion
        side_orig = side_
        # personal space: a companion never walks closer than 2 to the side and 3 behind (the boy who follows the leader at a few blocks' distance
        # then stands at least SPACE from her) -- where the built set has floor for it (_floor_ok), else her old place
        companion = (cw_, max(back_, COMPANION_MIN_BACK), math.copysign(max(abs(side_), COMPANION_MIN_SIDE), side_))
    prev = start
    name = NAMES.get(who, who)
    last = None
    for n, st in enumerate(stops):
        st = _stop(st)
        obj = obj_first if n == 0 else obj_all
        d = math.hypot(st.x - prev[0], st.z - prev[1]) if prev else 10.0
        est = d / (speed * 20.0) + 1.0
        cmds = walk_cmds(who, st.x, st.y, st.z, speed)
        ux, uz = ((st.x - prev[0]) / max(d, 0.01), (st.z - prev[1]) / max(d, 0.01)) if prev and d > 0.5 else (None, None)
        comp_at = None
        if companion and prev:
            cw, back, side = companion
            for sd in (side, side * 0.8, side_orig):                      # the wider berth if the built set has floor there, else the old one
                gx = st.x - ux * back + uz * sd
                gz = st.z - uz * back - ux * sd
                if _floor_ok(ctx, gx, st.y, gz):
                    break
            comp_at = (gx, gz)
            cmds += walk_cmds(cw, gx, st.y, gz, speed)             # the companion has the same monitor: she too waits for the player
        s.do(*cmds, note=f"{who} walks to {st.note or f'({st.x:.1f}, {st.z:.1f})'}")
        for ln in st.say_while:
            s.until(near_char(who, 11.0), timeout=90, est=0.5, note=f"the player is within earshot of {who}", objective=obj)
            s.say(ln)
        if prev and d > 0.5:
            bx, bz = st.x - 2.0 * (st.x - prev[0]) / d, st.z - 2.0 * (st.z - prev[1]) / d
        else:
            bx, bz = st.x - 2.0, st.z
        bring = [f'function {NS}:cast/stop {{id:"{who}"}}',
                 f"tp {char(who)} {num(st.x)} {num(st.y)} {num(st.z)}",
                 tp_player(bx, st.y, bz)]
        s.until(arrived(who, est=est), est=est, timeout=180, on_timeout=bring,
                hint=(f"{name} is waiting for you.", []), hint_after=35, note=f"{who} reaches the stop", objective=obj, watch=False)
        if st.wait:
            arm = []
            if st.space and ux is not None:
                # the way to step: given, else on towards the next stop (the line she is about to walk anyway), else on the way she came;
                # a direction is only used if the built set shows floor and headroom along it
                cands = [st.escape] if st.escape else []
                if n + 1 < len(stops):
                    nx_ = _stop(stops[n + 1])
                    dn = math.hypot(nx_.x - st.x, nx_.z - st.z)
                    if dn > 0.5:
                        cands.append(((nx_.x - st.x) / dn, (nx_.z - st.z) / dn))
                cands.append((ux, uz))
                esc = next((c for c in cands if way_clear(ctx, st.x, st.y, st.z, c[0], c[1])), None)
                if esc is None:
                    ctx.warn(f"lead: no clear way for {who} to step aside at {st.note or (st.x, st.z)}: personal space not armed there")
                else:
                    ex, ez = esc
                    arm += space_on(ctx, who, st.x + ex * SPACE_STEP, st.y, st.z + ez * SPACE_STEP)
                    if companion and comp_at and way_clear(ctx, comp_at[0], st.y, comp_at[1], ex, ez):
                        arm += space_on(ctx, companion[0], comp_at[0] + ex * SPACE_STEP, st.y, comp_at[1] + ez * SPACE_STEP)
            s.do(cast_look(who, "player"), sset(f"#f.lp_{who}", 0), *arm, note=f"{who} turns to look for the player" + (" (personal space armed)" if arm else ""))
            s.until(near_char(who, near), timeout=180, est=0.5, on_timeout=bring[2:],
                    hint=(f"{name} is waiting for you.", []), hint_after=35, note=f"the player catches up with {who}", objective=obj)
            if arm:
                s.do(*space_off(who), *(space_off(companion[0]) if companion else []), note="personal space off")
        for ln in st.say_at:
            s.say(ln)
        if st.then:
            s.do(*st.then)
        prev = (st.x, st.z)
        last = st
    s.do(*lead_off(who), *(lead_off(companion[0]) if companion else []), *space_off(who), *(space_off(companion[0]) if companion else []),
         note=f"{who} stops leading")
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
