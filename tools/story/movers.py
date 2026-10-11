"""Movers: a route is a table of frames (position, yaw, pitch per tick) played from a counter.

    #mv.n      the frame being shown            #mv.limit   the highest frame the counter may reach right now
    #mv.route  which route is playing           #mv.on      1 while a route is playing

Each tick `#mv.n` goes up by one unless it has reached `#mv.limit`; the frame table then places the rig:
    execute if score #mv.n matches 123 positioned X Y Z rotated YAW PITCH run function angel:story/rig/<rig>/follow
The story raises the limit to let the vehicle go on (a "station" is a frame where the vehicle stands still: legs of a route start and
end at rest, so holding there is natural).  Holding is how the wagon waits in the tunnel for the player's answers.
"""
from core import NS, OBJ, fn, num, range_tree, sc, sset, TPS
from motion import leg_frames, Path, nearest_s


class Route:
    def __init__(self, name, rig, rid):
        self.name = name
        self.rig = rig
        self.id = rid
        self.frames = []
        self.stations = {}
        self.marks = {}
        self.legs = []                 # (first frame, last frame, name)
        self.notes = []

    @property
    def end(self):
        return len(self.frames) - 1

    def seconds(self, frame=None):
        return (self.end if frame is None else frame) / TPS

    def add_leg(self, name, path, vmax, station=None, marks=None, **kw):
        """Drive `path`; `station`: name for the frame where this leg ends (at rest); `marks`: {name: arc length along this path}."""
        frames, s_of = leg_frames(path, vmax, **kw)
        first = len(self.frames)
        self.frames += frames
        last = len(self.frames) - 1
        self.legs.append((first, last, name))
        if station:
            self.stations[station] = last
        for mk, dist in (marks or {}).items():
            idx = next((i for i, s in enumerate(s_of) if s >= dist), len(s_of) - 1)
            self.marks[mk] = first + idx
        return self

    def add_marks_by_point(self, path, base_frame, s_of, marks):
        pass

    def hold(self, sec):
        if self.frames:
            self.frames += [self.frames[-1]] * int(round(sec * TPS))
        return self

    def frame_of(self, where):
        if where is None or where == "end":
            return self.end
        if isinstance(where, int):
            return where
        if where in self.stations:
            return self.stations[where]
        if where in self.marks:
            return self.marks[where]
        raise KeyError(f"route {self.name}: no station or mark {where!r}")

    def pose(self, i=0):
        return self.frames[min(i, self.end)]

    # -------------------------------------------------------------------------- commands for steps
    def start_cmds(self, limit="end", frame=0):
        """Begin playing from `frame` (the rig must already stand at that pose), allowed to advance up to `limit`."""
        return [sset("#mv.route", self.id), sset("#mv.n", frame), sset("#mv.limit", self.frame_of(limit)), sset("#mv.on", 1),
                fn(f"story/m/{self.name}/root")]

    def limit_cmds(self, limit="end"):
        return [sset("#mv.limit", self.frame_of(limit))]

    def stop_cmds(self):
        return [sset("#mv.on", 0)]

    def cond_at(self, where, est=None):
        from engine import Cond
        f = self.frame_of(where)
        c = Cond([sc("#mv.route", str(self.id)), sc("#mv.n", f"{f}..")], est if est is not None else f / TPS,
                 f"route {self.name} at frame {f} ({where})")
        c.route, c.frame = self, f
        return c

    def cond_done(self):
        return self.cond_at("end")

    def jump_cmds(self, where):
        """Teleport the playing route to another frame (used to skip a long quiet stretch behind a fade)."""
        f = self.frame_of(where)
        return [sset("#mv.n", f), fn(f"story/m/{self.name}/root")]


def write_route(out, route, chunk=20):
    rig = route.rig
    ranges = []
    n = len(route.frames)
    for k in range(0, n, chunk):
        lines = []
        for i in range(k, min(n, k + chunk)):
            x, y, z, yaw, pitch = route.frames[i]
            lines.append(f"execute if score #mv.n {OBJ} matches {i} positioned {num(x)} {num(y)} {num(z)} "
                         f"rotated {num(yaw, 2)} {num(pitch, 2)} run function {NS}:story/rig/{rig}/follow")
        out.function(f"story/m/{route.name}/b{k // chunk}", lines)
        ranges.append((k, min(n, k + chunk) - 1, f"function {NS}:story/m/{route.name}/b{k // chunk}"))
    range_tree(out, f"story/m/{route.name}/t", "#mv.n", ranges)
    out.function(f"story/m/{route.name}/root", [f"function {NS}:story/m/{route.name}/t/root"])


def write_mover_system(out, routes):
    """story/mv_step and story/mover: the counter that plays whichever route is on."""
    step = ["scoreboard players add #mv.n angel.story 1"]
    for r in routes:
        step.append(f"execute if score #mv.route {OBJ} matches {r.id} run function {NS}:story/m/{r.name}/root")
    out.function("story/mv_step", step)
    out.function("story/mover", [f"execute if score #mv.on {OBJ} matches 1 if score #mv.n {OBJ} < #mv.limit {OBJ} run function {NS}:story/mv_step"])
