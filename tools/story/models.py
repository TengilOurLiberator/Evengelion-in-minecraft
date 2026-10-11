"""Display-entity models: the car, the rail wagon, the aircraft, the mushroom cloud, birds.

Model space (the rig's local frame, same as `^ ^ ^` in commands):  +x = LEFT, +y = up, +z = FORWARD, origin on the floor at the
centre of the model.  A display entity is summoned at the rig's position with the rig's yaw/pitch; because every part sits at the same
entity position, ONE `tp @e[tag=<rig>] ~ ~ ~ ~ ~` moves the whole model, and each part's `transformation` (translation, left rotation,
scale) holds its place inside the model.  Block displays: the unit cube [0,1]^3 is scaled by `scale` and put at `translation`.

Faces of a block display are visible from outside only (back faces are culled), so a seat or lining seen from inside the cabin is a box
whose OUTER face points into the cabin.
"""
import json
import math

from core import CFG, QI, TAG, fnum, num, qaxis, qmul, qrot, vadd, vsub


class Part:
    def __init__(self, name, state, lo, hi, rot=QI, pivot=(0, 0, 0), bright=None, group="body", props=None, item=None):
        """A box from `lo` to `hi` (model space).  `rot` rotates it about `pivot` (applied to the finished box)."""
        self.name = name
        self.state = state                   # block id ("blue_concrete") or None for an item display
        self.props = props
        self.lo = tuple(float(v) for v in lo)
        self.hi = tuple(float(v) for v in hi)
        self.rot = rot
        self.pivot = pivot
        self.bright = bright
        self.group = group                   # parts of one group can be animated together (door, etc.)
        self.item = item

    def base(self):
        """(translation, left_rotation, scale) of the box in model space."""
        size = tuple(h - l for l, h in zip(self.lo, self.hi))
        t = self.lo
        q = QI
        if self.rot != QI:
            t = vadd(self.pivot, qrot(self.rot, vsub(self.lo, self.pivot)))
            q = self.rot
        return t, q, size

    def with_motion(self, q_g=QI, c_g=(0, 0, 0), t_g=(0, 0, 0)):
        """Apply a rigid motion (rotation q_g about point c_g, then translation t_g) to the finished part."""
        t, q, s = self.base()
        t2 = vadd(vadd(c_g, qrot(q_g, vsub(t, c_g))), t_g)
        return t2, qmul(q_g, q), s


def _state_nbt(p):
    if p.props:
        pr = ",".join(f'{k}:"{v}"' for k, v in p.props.items())
        return f'{{id:"minecraft:{p.state}",properties:{{{pr}}}}}'
    return f'"minecraft:{p.state}"'


def transformation_nbt(t, q, s):
    f = lambda v: fnum(v)
    return (f"transformation:{{translation:[{f(t[0])},{f(t[1])},{f(t[2])}],left_rotation:[{f(q[0])},{f(q[1])},{f(q[2])},{f(q[3])}],"
            f"scale:[{f(s[0])},{f(s[1])},{f(s[2])}],right_rotation:[0f,0f,0f,1f]}}")


def summon_part(p, tags, tp_duration=3, motion=None, view_range=2.0, bright=None, pos="~ ~ ~"):
    """`summon` command for one part.  motion = (q_g, c_g, t_g) applies a rigid motion to the part's transformation."""
    t, q, s = p.with_motion(*motion) if motion else p.with_motion()
    tg = ",".join(f'"{x}"' for x in tags + [TAG])
    br = bright if bright is not None else p.bright
    brs = f",brightness:{{sky:{br[0]},block:{br[1]}}}" if br else ""
    if p.state:
        head = f'summon minecraft:block_display {pos} {{Tags:[{tg}],block_state:{_state_nbt(p)}'
    else:
        head = f'summon minecraft:item_display {pos} {{Tags:[{tg}],item:{{id:"minecraft:{p.item}",count:1}},item_display:"none"'
    return f"{head},teleport_duration:{tp_duration},view_range:{fnum(view_range)}{brs},{transformation_nbt(t, q, s)}}}"


def part_merge(p, tag, motion=None, interp=10, extra=""):
    """`data merge` that moves the part to a pose over `interp` ticks."""
    t, q, s = p.with_motion(*motion) if motion else p.with_motion()
    return (f"data merge entity @e[tag={tag},tag=angel.pt_{p.name},limit=1] {{start_interpolation:0,interpolation_duration:{interp},"
            f"{transformation_nbt(t, q, s)}{extra}}}")


# --------------------------------------------------------------------------------------------------- the car
# The heroine's blue coupe, built to the proportions of outskirts.car(): 4 wide, 7 long, cabin 2 x 2 hollow, the passenger on the LEFT
# (right-hand drive), glass band at 1..1.9, roof carpet at 2.0625.  Seat cell centres (+-0.5, 0, 0): passenger X=+0.5, driver X=-0.5.
BODY = "blue_concrete"
SEAT_PASSENGER = (0.5, 0.0, 0.0)
SEAT_DRIVER = (-0.5, 0.0, 0.0)
DOOR_HINGE = (2.0, 0.0, 0.5)            # outer face, front edge of the passenger door
DOOR_OPEN_DEG = -62.0                   # rotation about +y that swings the free end of the left door out to the left


def car_parts():
    P_ = Part
    parts = [
        P_("floor", "gray_concrete", (-1, 0.0, -1.5), (1, 0.08, 0.5)),
        P_("front", BODY, (-2, 0.15, 0.5), (2, 1.05, 3.5)),
        P_("rear", BODY, (-2, 0.15, -3.5), (2, 1.05, -1.5)),
        P_("dash", "black_concrete", (-1, 0.08, 0.5), (1, 1.0, 1.5)),
        P_("cushion", "polished_blackstone_slab", (-1, 0.08, -1.5), (1, 0.5, -0.5), props={"type": "bottom"}),
        P_("sideR", BODY, (-2, 0.15, -1.5), (-1.85, 1.0, 0.5)),
        P_("windowR", "light_blue_stained_glass", (-2, 1.0, -1.4), (-1.9, 1.9, 0.4)),
        P_("liningR", "gray_concrete", (-1.12, 0.1, -1.5), (-1.0, 1.0, 0.5)),
        P_("liningL", "gray_concrete", (1.0, 0.1, -1.5), (1.12, 1.0, 0.5)),
        P_("roof", BODY, (-2, 1.94, -2.5), (2, 2.06, 1.5)),
        P_("glass", "light_blue_stained_glass", (-1.95, 1.0, -2.45), (1.95, 1.94, 1.45)),
        P_("pillarA1", BODY, (1.7, 1.0, 1.2), (2, 1.94, 1.5)),
        P_("pillarA2", BODY, (-2, 1.0, 1.2), (-1.7, 1.94, 1.5)),
        P_("pillarC1", BODY, (1.7, 1.0, -2.5), (2, 1.94, -2.2)),
        P_("pillarC2", BODY, (-2, 1.0, -2.5), (-1.7, 1.94, -2.2)),
        P_("wheelFL", "black_concrete", (1.5, 0.0, 1.5), (2.05, 1.0, 2.5)),
        P_("wheelFR", "black_concrete", (-2.05, 0.0, 1.5), (-1.5, 1.0, 2.5)),
        P_("wheelRL", "black_concrete", (1.5, 0.0, -2.5), (2.05, 1.0, -1.5)),
        P_("wheelRR", "black_concrete", (-2.05, 0.0, -2.5), (-1.5, 1.0, -1.5)),
        P_("headL", "white_concrete", (1.0, 0.55, 3.5), (1.9, 0.95, 3.62)),
        P_("headR", "white_concrete", (-1.9, 0.55, 3.5), (-1.0, 0.95, 3.62)),
        P_("tailL", "red_concrete", (1.0, 0.55, -3.62), (1.9, 0.95, -3.5)),
        P_("tailR", "red_concrete", (-1.9, 0.55, -3.62), (-1.0, 0.95, -3.5)),
        P_("stripe", "white_concrete", (-0.5, 1.05, 1.5), (0.5, 1.07, 3.5)),
        P_("wheel", "black_concrete", (-0.85, 0.9, 0.55), (-0.15, 0.96, 1.15), rot=qaxis("x", -25), pivot=(-0.5, 0.93, 0.85)),
        # the passenger door: closed it covers the left side; it hinges at its front edge (group "door")
        P_("doorL", BODY, (1.85, 0.15, -1.5), (2.0, 1.0, 0.5), group="door"),
        P_("doorGlass", "light_blue_stained_glass", (1.9, 1.0, -1.4), (2.0, 1.9, 0.4), group="door"),
    ]
    return parts


def door_motion(deg):
    """rigid motion for the door parts: rotate `deg` about +y through the hinge"""
    return (qaxis("y", deg), DOOR_HINGE, (0, 0, 0))


ROLL_PIVOT = (-2.0, 0.0, 0.0)           # the lower right edge: the car lies on its right side with the roof facing right


def roll_motion(deg):
    return (qaxis("z", deg), ROLL_PIVOT, (0, 0, 0))


def compose(m1, m2):
    """motion m2 applied after m1 (each (q, c, t)).  Returned as a single (q, c=origin, t) motion about the origin."""
    q1, c1, t1 = m1
    q2, c2, t2 = m2
    # x -> c1 + q1 (x - c1) + t1 -> c2 + q2 (y - c2) + t2
    q = qmul(q2, q1)
    # evaluate at x = 0:  y0 = c1 - q1 c1 + t1;  out0 = c2 + q2 (y0 - c2) + t2
    y0 = vadd(vsub(c1, qrot(q1, c1)), t1)
    out0 = vadd(vadd(c2, qrot(q2, vsub(y0, c2))), t2)
    return (q, (0, 0, 0), out0)


# --------------------------------------------------------------------------------------------------- the wagon
def wagon_parts(ramp=False):
    P_ = Part
    parts = [
        P_("bed", "gray_concrete", (-2.5, -1.0, -4.5), (2.5, 0.0, 4.5), group="wagon"),
        P_("edgeL", "yellow_concrete", (2.2, -1.0, -4.5), (2.5, 0.01, 4.5), group="wagon"),
        P_("edgeR", "yellow_concrete", (-2.5, -1.0, -4.5), (-2.2, 0.01, 4.5), group="wagon"),
        P_("edgeF", "yellow_concrete", (-2.5, -1.0, 4.2), (2.5, 0.01, 4.5), group="wagon"),
        P_("edgeB", "yellow_concrete", (-2.5, -1.0, -4.5), (2.5, 0.01, -4.2), group="wagon"),
        P_("railL", "iron_block", (2.35, 0.8, -4.3), (2.5, 0.95, 4.3), group="wagon"),
        P_("railR", "iron_block", (-2.5, 0.8, -4.3), (-2.35, 0.95, 4.3), group="wagon"),
        P_("railF", "iron_block", (-2.5, 0.8, 4.15), (2.5, 0.95, 4.3), group="wagon"),
        P_("bogieL", "black_concrete", (-1.6, -1.55, -3.4), (1.6, -1.0, -2.2), group="wagon"),
        P_("bogieR", "black_concrete", (-1.6, -1.55, 2.2), (1.6, -1.0, 3.4), group="wagon"),
        P_("hitchF", "iron_block", (-0.25, -0.75, 4.5), (0.25, -0.35, 5.6), group="wagon"),
        P_("hitchB", "iron_block", (-0.25, -0.75, -5.6), (0.25, -0.35, -4.5), group="wagon"),
    ]
    for i, (x, z) in enumerate(((2.3, 4.15), (-2.5, 4.15), (2.3, -4.3), (-2.5, -4.3))):
        parts.append(P_(f"post{i}", "iron_block", (x, 0.0, z), (x + 0.2, 1.0, z + 0.15), group="wagon"))
    if ramp:
        # a loading ramp at the rear: from the platform (y -1) up to the bed (y 0) over 4 blocks
        ang = math.degrees(math.atan2(1.0, 4.0))
        parts.append(P_("ramp", "gray_concrete", (-2.3, -0.12, -8.5), (2.3, 0.0, -4.5), rot=qaxis("x", -ang), pivot=(0, 0, -4.5), group="wagon"))
    return parts


# --------------------------------------------------------------------------------------------------- the aircraft
def aircraft_parts(scale=2.0):
    """A small VTOL, nose along +z.  Scaled up so that it reads at a hundred blocks."""
    P_ = Part
    s = scale
    raw = [
        ("fuselage", "light_gray_concrete", (-0.45, -0.3, -2.2), (0.45, 0.4, 2.0)),
        ("nose", "gray_concrete", (-0.3, -0.2, 2.0), (0.3, 0.3, 2.7)),
        ("canopy", "light_blue_stained_glass", (-0.3, 0.4, 0.6), (0.3, 0.7, 1.7)),
        ("wing", "gray_concrete", (-2.6, 0.0, -0.8), (2.6, 0.12, 0.6)),
        ("fin", "light_gray_concrete", (-0.06, 0.4, -2.2), (0.06, 1.3, -1.2)),
        ("tailplane", "gray_concrete", (-1.1, 0.35, -2.2), (1.1, 0.43, -1.6)),
        ("podL", "black_concrete", (1.9, -0.15, -0.9), (2.5, 0.35, 0.7)),
        ("podR", "black_concrete", (-2.5, -0.15, -0.9), (-1.9, 0.35, 0.7)),
        ("glowL", "orange_concrete", (2.0, -0.08, -1.05), (2.4, 0.28, -0.9)),
        ("glowR", "orange_concrete", (-2.4, -0.08, -1.05), (-2.0, 0.28, -0.9)),
    ]
    return [P_(n, b, tuple(v * s for v in lo), tuple(v * s for v in hi)) for n, b, lo, hi in raw]


# --------------------------------------------------------------------------------------------------- the rig
class Rig:
    """A named set of display parts plus seat entities, moved as one."""

    def __init__(self, name, parts, seats, tp_duration=3, view_range=2.0, bright=None):
        self.name = name
        self.parts = parts
        self.seats = seats                # {"driver": (x, y, z), "passenger": (x, y, z)}: where the rider's FEET are, model space
        self.tp_duration = tp_duration
        self.view_range = view_range
        self.bright = bright
        self.base_motion = {}             # part name -> motion applied before anything else (the turned car inside the cartrain)

    @property
    def tag(self):
        return f"angel.rig_{self.name}"

    def motion_for(self, p, extra):
        base = self.base_motion.get(p.name)
        if base and extra:
            return compose(base, extra)
        return extra or base

    def spawn_cmds(self, motions=None, seats=True, pos="~ ~ ~"):
        """Commands (run positioned at the rig's pose) that create the parts and the seats, all tagged angel.new.
        motions: {part name or group: (q, c, t)} poses parts (door open, car on its side...)."""
        cmds = []
        for p in self.parts:
            extra = None
            if motions:
                extra = motions.get(p.name) or motions.get(p.group)
            tags = [self.tag, f"angel.pt_{p.name}", "angel.part", "angel.new"]
            cmds.append(summon_part(p, tags, self.tp_duration, self.motion_for(p, extra), self.view_range, self.bright, pos))
        if seats:
            for role in self.seats:
                cmds.append(f'summon minecraft:item_display {pos} {{Tags:["angel.seat","angel.seat_{role}","{TAG}","{self.tag}","angel.new"],'
                            f'teleport_duration:{self.tp_duration},item_display:"none"}}')
        return cmds

    def settle_cmds(self, seats=True):
        """After a spawn: bring everything to the context pose (rotation included), seats to their offsets; clear the 'new' tags."""
        return self.follow_cmds(seats) + ["tag @e[tag=angel.new] remove angel.new"]

    def follow_cmds(self, seats=True):
        """The commands that move the whole rig to the context's position and rotation."""
        cmds = [f"tp @e[tag={self.tag},tag=angel.part] ~ ~ ~ ~ ~"]
        if seats:
            for role, (x, y, z) in self.seats.items():
                # the rider's feet end up 0.6 below the seat entity's origin (measured on the server with a mannequin)
                cmds.append(f"tp @e[tag={self.tag},tag=angel.seat_{role},limit=1] ^{num(x)} ^{num(y + 0.6)} ^{num(z)} ~ ~")
        return cmds

    def pose_cmds(self, group_motions, interp):
        """data merge commands that move named parts/groups to a pose over `interp` ticks (door, roll)."""
        cmds = []
        for p in self.parts:
            extra = group_motions.get(p.name) or group_motions.get(p.group)
            if extra is not None or p.name in group_motions or p.group in group_motions:
                cmds.append(part_merge(p, self.tag, self.motion_for(p, extra), interp))
        return cmds


def car_rig(name="car"):
    return Rig(name, car_parts(), {"driver": SEAT_DRIVER, "passenger": SEAT_PASSENGER})


def cartrain_rig(name, reversed_car=False, ramp=False, bright=None):
    """Wagon plus the car in one rig.  `reversed_car`: the car stands the other way round on the wagon, so that its left (passenger)
    side faces the right-hand side of the direction of travel."""
    parts = list(wagon_parts(ramp)) + car_parts()
    sx = -1.0 if reversed_car else 1.0
    seats = {"driver": (sx * SEAT_DRIVER[0], 0.0, 0.0), "passenger": (sx * SEAT_PASSENGER[0], 0.0, 0.0)}
    r = Rig(name, parts, seats, bright=bright)
    if reversed_car:
        qy = qaxis("y", 180.0)
        for p in car_parts():
            r.base_motion[p.name] = (qy, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    r.reversed_car = reversed_car
    return r


def aircraft_rig(name, scale=2.0):
    return Rig(name, aircraft_parts(scale), {}, tp_duration=2, view_range=8.0)