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
from core import NS, OBJ, P, TAG, fn, num, sadd, sset
from engine import C, Cond
from objective import follow_objective

FAR = 9.0
NEAR = 6.0
SPACE = 1.8                  # a waiting character never stands closer than this to the player
SPACE_STEP = 2.6             # ... and steps this far on when he walks into her
COMPANION_MIN_SIDE = 2.0     # a companion walks at least this far to the side of the leader's line and this far behind the leader (where the set has room)
COMPANION_MIN_BACK = 3.0
BODY_R = 0.4                 # the radius a character needs clear round her (the cast's mannequins are 0.6 wide; the step height is 1.0)
STUCK_SECONDS = 3            # a companion that has not moved for this long while farther than STUCK_FAR from the player is put on a reachable cell near him
STUCK_FAR = 6.0
CELL_STEP = 2.0              # the rescue cells lie this far apart along a companion's path
SINGLE_FILE_EXTRA = 2.5      # a companion who cannot walk beside the player (a 3-wide catwalk) walks this much farther behind the leader
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


# --------------------------------------------------------------------------------------------------- reachable cells (the companion guarantee)
class Nav:
    """Walkability on the built voxel set at one standing height: a cell is standable when there is floor within 0.6 of `y` under it AND under the four
    sides and corners of a 0.4-radius body, with two blocks of headroom all round (a railing, a wall, a lamp, a step too high all refuse it).  `reach`
    finds a path of straight segments, each of which is walkable end to end (what the cast's straight-line walk needs), round whatever stands between."""

    def __init__(self, ctx, y, set_name=None, open_cells=()):
        self.ctx, self.y = ctx, float(y)
        self.probe = ctx.probe(set_name or "hq")
        self.open = set(open_cells)                  # (x, y, z) cells that are solid in the built set but open when she walks (a door the story has opened)
        self._ok = {}

    def solid(self, x, y, z):
        if self.open and (math.floor(x), math.floor(y), math.floor(z)) in self.open:
            return False
        return self.probe.solid(x, y, z)

    def surface(self, x, z, ref_y, up=1.6, down=8):
        """Probe.surface with the opened cells counted as air"""
        if not self.open:
            return self.probe.surface(x, z, ref_y, up, down)
        from world_probe import top_of
        y0 = int(math.floor(ref_y + up))
        for y in range(y0, y0 - down - 2, -1):
            if self.solid(x, y, z) and not self.solid(x, y + 1, z):
                return y + top_of(self.probe.name(x, y, z))
        return None

    def ok(self, x, z, r=BODY_R):
        k = (round(x * 8), round(z * 8), r)
        v = self._ok.get(k)
        if v is None:
            v = self._ok[k] = self._cell(x, z, r)
        return v

    def _cell(self, x, z, r):
        p, y = self.probe, self.y
        sf = self.surface(x, z, y)
        if sf is None or abs(sf - y) > 0.6:
            return False
        for dx, dz in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r), (r, r), (-r, r), (r, -r), (-r, -r)):
            px, pz = x + dx, z + dz
            if self.solid(px, y + 0.6, pz) or self.solid(px, y + 1.6, pz):
                return False
            s2 = self.surface(px, pz, y)
            if s2 is None or abs(s2 - y) > 0.75:
                return False
        return True

    def seg(self, a, b, r=BODY_R, step=0.25):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / step))
        return all(self.ok(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, r) for i in range(n + 1))

    def reach(self, a, b, margin=8.0, cell=0.5):
        """A path [a, ..., b] of straight walkable segments, or None."""
        if self.seg(a, b):
            return [tuple(a), tuple(b)]
        import heapq
        x0, x1 = min(a[0], b[0]) - margin, max(a[0], b[0]) + margin
        z0, z1 = min(a[1], b[1]) - margin, max(a[1], b[1]) + margin
        snap = lambda p: (round((p[0] - x0) / cell), round((p[1] - z0) / cell))
        pos = lambda n: (x0 + n[0] * cell, z0 + n[1] * cell)
        start, goal = snap(a), snap(b)
        if not self.ok(*pos(start)):
            start = next((n for n in self._ring(start) if self.ok(*pos(n))), None)
        if not self.ok(*pos(goal)):
            goal = next((n for n in self._ring(goal) if self.ok(*pos(n))), None)
        if start is None or goal is None:
            return None
        openq, best, prev = [(0.0, start)], {start: 0.0}, {}
        while openq:
            _, cur = heapq.heappop(openq)
            if cur == goal:
                break
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nb = (cur[0] + dx, cur[1] + dz)
                pn = pos(nb)
                if not (x0 <= pn[0] <= x1 and z0 <= pn[1] <= z1) or not self.ok(*pn) or not self.seg(pos(cur), pn):
                    continue
                g = best[cur] + math.hypot(dx, dz)
                if g < best.get(nb, 1e18):
                    best[nb], prev[nb] = g, cur
                    heapq.heappush(openq, (g + math.hypot(nb[0] - goal[0], nb[1] - goal[1]), nb))
        if goal not in best:
            return None
        nodes = [goal]
        while nodes[-1] != start:
            nodes.append(prev[nodes[-1]])
        pts = [tuple(a)] + [pos(n) for n in reversed(nodes)][1:-1] + [tuple(b)]
        out, i = [pts[0]], 0                                   # string pulling: the farthest point that can be walked to straight
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self.seg(pts[i], pts[j]):
                j -= 1
            out.append(pts[j])
            i = j
        return out

    @staticmethod
    def _ring(n, rmax=4):
        for r in range(1, rmax + 1):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if max(abs(dx), abs(dz)) == r:
                        yield (n[0] + dx, n[1] + dz)


def companion_goal(nav, prev, leader_prev, st, ux, uz, back, side):
    """Where a companion should stand when the leader stands at `st`: `back` behind her and `side` to her left (negative: right) where the set has room, else
    nearer her line, else farther back in single file -- the first standable cell, in order of closeness to the wish, that can be walked to from `prev`
    (round the furniture, through the neck of a catwalk).  Returns (goal, path) or None."""
    cands = []
    sgn = 1.0 if side >= 0 else -1.0
    sides = [side, side * 0.8, side * 0.6, side * 0.45, side * 0.3, 0.0, -sgn * 0.3 * abs(side), -sgn * 0.6 * abs(side), -side]
    backs = [back, back + 1.0, back + 2.0, back + 3.0, back + 4.5, back + 6.0]
    for bi, bk in enumerate(backs):
        for si, sd in enumerate(sides):
            eff = bk + (SINGLE_FILE_EXTRA if abs(sd) < 1.0 else 0.0)        # in single file she walks behind HIM (he follows the leader at 3 to 5 blocks), not on top of him
            gx = st.x - ux * eff + uz * sd
            gz = st.z - uz * eff - ux * sd
            cands.append((abs(sd - side) * 1.0 + bi * 1.5 + si * 0.2, (gx, gz)))
    cands.sort(key=lambda c: c[0])
    for _, g in cands:
        if math.hypot(g[0] - st.x, g[1] - st.z) < 1.8 or not nav.ok(*g):
            continue
        path = nav.reach(prev, g)
        if path:
            return g, path
    return None


def sample_chain(path, step=CELL_STEP):
    """[(x, z, k)]: cells every `step` blocks along a path of waypoints; k is the index (in the path) of the waypoint she walks to next from that cell."""
    out = []
    for k in range(1, len(path)):
        a, b = path[k - 1], path[k]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / step))
        for i in range(n):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, k))
    return out


def ensure_companion(ctx, who):
    """The per-tick companion follower of `who` (a continuous effect, on while #f.cq_<who> is 1): walks her through the waypoints queued in storage
    `angel:story cq.<who>` one after another, plays her footsteps, and every second runs the keeper:

        not moved for STUCK_SECONDS, her walk unfinished, farther than STUCK_FAR from the player  ->  she is put (tp, no sound, no particle) on the nearest of the
        reachable cells of her path (markers angel.cp_<who>, made by lead()) that lies 3.5 to 6.5 blocks from the player and out of his view (not within 9 of
        the point 8 blocks straight ahead of him), then walks on from there.

    She never pauses to wait for the player (the leader's monitor does that for the leader): a companion walks to where the player is going."""
    key = ("companion", who)
    if key in ctx.helpers:
        return
    ctx.helpers[key] = True
    c = char(who)
    flag = f"#f.cq_{who}"
    arr = f"#arrived_{who} angel.cast"
    x0, z0, n_ = f"#ckx0_{who}", f"#ckz0_{who}", f"#ckn_{who}"
    cp = lambda extra="": f"@e[tag=angel.cp,tag=angel.cp_{who}" + (f",{extra}" if extra else "") + "]"
    pick = f"@e[tag=angel.cp_pick,tag=angel.cp_{who}]"
    ctx.extra_functions[f"story/lead/cq_{who}"] = [
        f"execute if score {arr} matches 1 if data storage {NS}:story cq.{who}[0] run function {NS}:story/lead/cq_next_{who}",
        f"scoreboard players operation #lm {OBJ} = #tick {OBJ}", f"scoreboard players set #c9 {OBJ} 9", f"scoreboard players operation #lm {OBJ} %= #c9 {OBJ}",
        f"execute if score #lm {OBJ} matches 0 unless score #hush {OBJ} matches 1 if score {arr} matches 0 as {c} at @s "
        f"run playsound minecraft:block.deepslate_tiles.step master @a ~ ~ ~ 0.6 {'1.15' if who == 'ritsuko' else '0.95'} 0.15",
        f"scoreboard players operation #lk {OBJ} = #tick {OBJ}", f"scoreboard players operation #lk {OBJ} %= #c20 {OBJ}",
        f"execute if score #lk {OBJ} matches 0 run function {NS}:story/lead/ck_{who}"]
    ctx.extra_functions[f"story/lead/cq_next_{who}"] = [
        cast_look(who, "ahead"), f"function {NS}:story/lead/cq_go_{who} with storage {NS}:story cq.{who}[0]", f"data remove storage {NS}:story cq.{who}[0]"]
    ctx.extra_functions[f"story/lead/cq_go_{who}"] = [
        f'$function {NS}:cast/walk {{id:"{who}",x:$(x),y:$(y),z:$(z),speed:$(speed)}}']
    # the keeper (every second): has she moved?
    ctx.extra_functions[f"story/lead/ck_{who}"] = [
        f"execute store result score #ckx {OBJ} as {c} run data get entity @s Pos[0] 10",
        f"execute store result score #ckz {OBJ} as {c} run data get entity @s Pos[2] 10",
        f"scoreboard players operation #ckdx {OBJ} = #ckx {OBJ}", f"scoreboard players operation #ckdx {OBJ} -= {x0} {OBJ}",
        f"scoreboard players operation #ckdz {OBJ} = #ckz {OBJ}", f"scoreboard players operation #ckdz {OBJ} -= {z0} {OBJ}",
        sset("#ckm", 0),
        f"execute unless score #ckdx {OBJ} matches -2..2 run {sset('#ckm', 1)}", f"execute unless score #ckdz {OBJ} matches -2..2 run {sset('#ckm', 1)}",
        f"execute if score #ckm {OBJ} matches 1 run {sset(n_, 0)}", f"execute if score #ckm {OBJ} matches 0 run {sadd(n_, 1)}",
        f"scoreboard players operation {x0} {OBJ} = #ckx {OBJ}", f"scoreboard players operation {z0} {OBJ} = #ckz {OBJ}",
        f"execute if score {n_} {OBJ} matches {STUCK_SECONDS}.. if score {arr} matches 0 as {c} at @s unless entity {P(f'distance=..{num(STUCK_FAR)}')} "
        f"run function {NS}:story/lead/rescue_{who}"]
    # the rescue: the nearest reachable cell 3.5 to 6.5 blocks from the player and out of his view; failing that, the nearest 3.5 to 10 blocks from him
    # (a cell in his view is better than a companion left behind); she is put there and walks on from the next waypoint of her path
    behind = f"as {P()} at @s rotated ~ 0 positioned ^ ^ ^8 as {cp('distance=9..')} at @s if entity {P('distance=3.5..6.5')} run tag @s add angel.cp_pick"
    near_ = f"as {P()} at @s as {cp()} at @s if entity {P('distance=3.5..10')} run tag @s add angel.cp_pick"
    chosen = "@e[tag=angel.cp_chosen,limit=1]"
    ctx.extra_functions[f"story/lead/rescue_{who}"] = [
        sset(n_, 0), f"tag {cp()} remove angel.cp_pick", f"tag {cp()} remove angel.cp_chosen",
        f"execute {behind}",
        f"execute unless entity {pick} {near_}",
        f"execute unless entity {pick} run return 0",
        f"execute as {P()} at @s as {pick.replace('@e[', '@e[sort=nearest,limit=1,')} run tag @s add angel.cp_chosen",
        f"execute at {chosen} run tp {c} ~ ~ ~",
        f"function {NS}:story/lead/cpd_{who}",
        f"tag {cp()} remove angel.cp_pick", f"tag {cp()} remove angel.cp_chosen",
        f"scoreboard players set {arr} 1"]
    ctx.extra_functions.setdefault(f"story/lead/cpd_{who}", ["# (the queue to resume from each rescue cell: filled by lead())"])
    ctx.fx_tick.append(f"execute if score {flag} {OBJ} matches 1 run function {NS}:story/lead/cq_{who}")
    ctx.halt_extra += [sset(flag, 0), f"kill {cp()}"]


def companion_leg(ctx, who, path, y, speed, nav):
    """Commands that send `who` along `path` (waypoints, the first being where she stands): the queue, the rescue cells, the follower on."""
    ensure_companion(ctx, who)
    k0 = ctx.helpers.get(("cpn", who), 0)
    cells = sample_chain(path)
    cmds = [f"kill @e[tag=angel.cp_{who}]"]
    dispatch = ctx.extra_functions[f"story/lead/cpd_{who}"]
    if dispatch[0].startswith("#"):
        dispatch.clear()
    wps = lambda k: "[" + ",".join(f'{{x:"{num(p[0])}",y:"{num(y)}",z:"{num(p[1])}",speed:"{num(speed)}"}}' for p in path[k:]) + "]"
    for i, (cx, cz, k) in enumerate(cells):
        idx = k0 + i + 1
        cmds.append(f'summon minecraft:marker {num(cx)} {num(y)} {num(cz)} {{Tags:["{TAG}","angel.cp","angel.cp_{who}","angel.cpi_{idx}"]}}')
        dispatch.append(f"execute if entity @e[tag=angel.cp_chosen,tag=angel.cpi_{idx},limit=1] run data modify storage {NS}:story cq.{who} set value {wps(k)}")
    ctx.helpers[("cpn", who)] = k0 + len(cells)
    cmds += [f"data modify storage {NS}:story cq.{who} set value {wps(1)}", sset(f"#f.cq_{who}", 1), sset(f"#ckn_{who}", 0),
             sset(f"#ckx0_{who}", 0), sset(f"#ckz0_{who}", 0), f"scoreboard players set #arrived_{who} angel.cast 1"]
    ctx.companion_legs.append(dict(who=who, y=y, path=list(path), cells=[(c[0], c[1]) for c in cells], nav=nav))
    return cmds


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
def lead(s, ctx, who, stops, speed=None, near=NEAR, far=FAR, companion=None, start=None, follow=True, follow_text=None, companion_at=None, nav_open=()):
    """Steps that make `who` lead the player along `stops` (see the module doc).  `start`: (x, z) of the place she starts from, used for
    the estimated time of the first leg and the companion's trail.  Returns the last Stop.  `speed`: blocks a tick (default: the pace preset's lead_speed).
    `follow`: every wait of the walk carries the objective "Follow Misato" / "Follow Dr. Akagi" attached to the leader (objective.follow_objective:
    it shows only when the player is more than 8 blocks behind her or has stood still for 10 s); `follow_text` renames it ("Go through the door");
    follow=False for a walk that has an objective of its own.

    `companion=("misato", back, side)`: her path is planned on the built set (Nav): her place at each stop is the standable cell nearest to the wish
    (back / side from the leader) that she can walk to from where she stood, by straight segments round whatever is in the way (the 3-wide catwalk has
    no room to the side: she walks behind, in single file), and the rescue keeper (ensure_companion) puts her on a reachable cell near the player,
    out of his view, if she is ever stuck for 3 s more than 6 blocks from him.  She never waits for him; she goes where he is going."""
    import pace
    speed = pace.PACE.lead_speed if speed is None else speed
    obj_all = follow_objective(who) if follow else None
    obj_first = follow_objective(who, follow_text) if (follow and follow_text) else obj_all           # `follow_text` names the objective of the FIRST stop only
    ensure_monitor(ctx, who, near, far)
    if companion:
        cw_, back_, side_ = companion
        side_orig = side_
        # personal space: a companion never walks closer than 2 to the side and 3 behind (the boy who follows the leader at a few blocks' distance
        # then stands at least SPACE from her) -- where the built set has room for it, else nearer the leader's line / farther back (companion_goal)
        companion = (cw_, max(back_, COMPANION_MIN_BACK), math.copysign(max(abs(side_), COMPANION_MIN_SIDE), side_))
        comp_pos = None                                               # where she is planned to stand (x, z): her start is behind the leader's start
        comp_nav = None
    prev = start
    name = NAMES.get(who, who)
    last = None
    for n, st in enumerate(stops):
        st = _stop(st)
        obj = obj_first if n == 0 else obj_all
        d = math.hypot(st.x - prev[0], st.z - prev[1]) if prev else 10.0
        est = d / (speed * 20.0) + pace.PACE.lead_est_pad
        if pace.PACE.est_overlap and st.say_while:
            # the lines said WHILE she walks are not extra time: the walk goes on under them (an estimate only; nothing in the game depends on it, so the
            # lines' lengths are read without being counted as scheduled against: Line._seconds)
            est = max(0.3, est - sum(ctx.lines[ln]._seconds + pace.PACE.gap + 0.2 for ln in st.say_while))
        cmds = walk_cmds(who, st.x, st.y, st.z, speed)
        ux, uz = ((st.x - prev[0]) / max(d, 0.01), (st.z - prev[1]) / max(d, 0.01)) if prev and d > 0.5 else (None, None)
        comp_at = None
        if companion and prev and ux is not None:
            cw, back, side = companion
            if comp_nav is None:
                comp_nav = Nav(ctx, st.y, open_cells=nav_open)
            cur = comp_pos or companion_at or prev
            res = companion_goal(comp_nav, cur, prev, st, ux, uz, back, side)
            leg = dict(who=cw, stop=st.note or (st.x, st.z), start=cur, y=st.y, ok=res is not None, nav=comp_nav, leader=(st.x, st.z))
            if res is None:
                ctx.warn(f"lead: {cw} cannot be placed near {leg['stop']}: no reachable standable cell")
                leg.update(path=[cur], goal=None, cells=[])
                ctx.companion_legs.append(leg)
            else:
                comp_at, path = res
                comp_pos = comp_at
                cmds += companion_leg(ctx, cw, path, st.y, speed, comp_nav)
                ctx.companion_legs[-1].update(leg, goal=comp_at)
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
        s.until(arrived(who, est=est), est=est, timeout=pace.PACE.lead_timeout, on_timeout=bring,
                hint=(f"{name} is waiting for you.", []), hint_after=pace.PACE.lead_hint, note=f"{who} reaches the stop", objective=obj, watch=False)
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
            s.until(near_char(who, near), timeout=pace.PACE.lead_timeout, est=0.5, on_timeout=bring[2:],
                    hint=(f"{name} is waiting for you.", []), hint_after=pace.PACE.lead_hint, note=f"the player catches up with {who}", objective=obj)
            if arm:
                s.do(*space_off(who), *(space_off(companion[0]) if companion else []), note="personal space off")
        for ln in st.say_at:
            s.say(ln)
        if st.then:
            s.do(*st.then)
        prev = (st.x, st.z)
        last = st
    if companion and comp_pos:
        cw = companion[0]
        # the guarantee at the end of the walk: she has reached her place; if she has not within 10 s she is put on a reachable cell near him
        s.until(Cond([f"if score #arrived_{cw} angel.cast matches 1"], 0.0, f"{cw} has reached her place"), timeout=10.0, est=0.0,
                on_timeout=[f"function {NS}:story/lead/rescue_{cw}"], watch=False, note=f"{cw} (companion) has reached her place, or is put near him")
    s.do(*lead_off(who), *(lead_off(companion[0]) if companion else []), *space_off(who), *(space_off(companion[0]) if companion else []),
         *([sset(f"#f.cq_{companion[0]}", 0), f"kill @e[tag=angel.cp_{companion[0]}]"] if companion and comp_pos else []),
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
