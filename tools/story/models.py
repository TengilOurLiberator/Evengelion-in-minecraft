"""Display-entity models: the car, the rail wagon, the aircraft, the mushroom cloud, birds.

Model space (the rig's local frame, same as `^ ^ ^` in commands):  +x = LEFT, +y = up, +z = FORWARD, origin on the floor at the
centre of the model.  A display entity is summoned at the rig's position with the rig's yaw/pitch; because every part sits at the same
entity position, ONE `tp @e[tag=<rig>] ~ ~ ~ ~ ~` moves the whole model, and each part's `transformation` (translation, left rotation,
scale) holds its place inside the model.  Block displays: the unit cube [0,1]^3 is scaled by `scale` and put at `translation`.

Every part carries the tag angel.rpart ("rig part"), NOT angel.part: that one belongs to the Angel (tools/fight) and its angel:angel/sync teleports
every block display with it to the monster every tick (which had parked the aircraft of scene 1 at the monster's feet).

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
# The heroine's blue roadster: an OPEN-TOP two-seater, right-hand drive (Japan).  3.0 wide over the body (3.6 over the wheels), 6.5 long,
# door tops at 0.9, a windscreen that ends at 1.37 and nothing above it: the passenger's eye (feet + 1.5 .. 1.8, see README) is above
# every part of the car in the forward 160 degrees and upward; ride_view.py ray-casts it to prove so.
# Model space: +x = LEFT (the PASSENGER side and its door), -x = RIGHT (the driver), +z = the nose.
BODY = "blue_concrete"
TRIM = "black_concrete"
CHROME = "iron_block"
SEAT_Y = 0.17                           # the rider's FEET (on the floor board); the seat entity is 0.6 above this
SEAT_PASSENGER = (0.72, SEAT_Y, -0.12)  # the player, on the left: 1.44 from the driver (centre to centre), a little behind her
SEAT_DRIVER = (-0.72, SEAT_Y, 0.12)     # Misato, on the right, a little ahead: when the boy looks ahead she is out of the edge of his view
DOOR_HINGE = (1.5, 0.0, 1.0)            # outer face, front edge of the passenger door
DOOR_OPEN_DEG = -62.0                   # rotation about +y that swings the free end of the left door out to the left
EYE_ABOVE_FEET = (1.5, 1.62, 1.8)       # a seated rider's eye above his feet: (low, flat-screen default, tall): README, 1.0..1.2 above the seat entity


def _ring(name, block, centre, radius, tilt_deg, n=8, thick=0.05, bright=None):
    """A round ring (a steering wheel) of n thin boxes in a plane that stands in x and y, then tilted about x by tilt_deg."""
    out = []
    seg = 2.0 * radius * math.tan(math.pi / n) + thick
    for i in range(n):
        a = 2.0 * math.pi * i / n
        c = qrot(qaxis("x", tilt_deg), (radius * math.cos(a), radius * math.sin(a), 0.0))
        q = qmul(qaxis("x", tilt_deg), qaxis("z", math.degrees(a) + 90.0))
        cx, cy, cz = centre[0] + c[0], centre[1] + c[1], centre[2] + c[2]
        out.append(Part(f"{name}{i}", block, (cx - seg / 2, cy - thick / 2, cz - thick / 2), (cx + seg / 2, cy + thick / 2, cz + thick / 2),
                        rot=q, pivot=(cx, cy, cz), bright=bright))
    return out


def car_parts():
    P_ = Part
    # the scuttle (the top of the bulkhead in front of the seats) is at 0.76; the bonnet is a slab that falls 9 degrees from it to the nose
    TOP = 0.72
    ZS, ZW = 0.86, 1.1                 # the scuttle's face towards the seats; the foot of the windscreen and the start of the bonnet
    bon_pivot = (0.0, TOP, ZW)
    bon_rot = qaxis("x", 11.0)
    # the windscreen plane: raked 35 degrees back from the scuttle; everything on it is drawn upright and rotated about the same pivot
    ws_pivot = (0.0, TOP, ZW)
    ws_rot = qaxis("x", -35.0)
    parts = [
        P_("floor", "gray_concrete", (-1.3, 0.05, -2.7), (1.3, 0.17, 2.9)),
        # --- the body's flanks: right side and left door (a low coaming of black on top of each)
        P_("sideR", BODY, (-1.5, 0.14, -1.2), (-1.22, TOP, ZS)),
        P_("coamingR", TRIM, (-1.52, TOP, -1.2), (-1.2, TOP + 0.02, ZS)),
        P_("doorL", BODY, (1.22, 0.14, -1.2), (1.5, TOP, ZS), group="door"),
        P_("coamingL", TRIM, (1.2, TOP, -1.2), (1.52, TOP + 0.02, ZS), group="door"),
        P_("handleL", CHROME, (1.5, 0.56, -0.7), (1.57, 0.64, -0.4), group="door"),
        # --- behind the seats: the tub, the twin humps behind the headrests, the tail
        P_("tub", BODY, (-1.5, 0.14, -3.05), (1.5, 0.82, -0.95)),
        P_("humpL", BODY, (0.3, 0.82, -2.0), (1.2, 1.24, -1.0), rot=qaxis("x", 14.0), pivot=(0.75, 0.82, -1.0)),
        P_("humpR", BODY, (-1.2, 0.82, -2.0), (-0.3, 1.24, -1.0), rot=qaxis("x", 14.0), pivot=(-0.75, 0.82, -1.0)),
        P_("bumperR", CHROME, (-1.3, 0.22, -3.2), (1.3, 0.38, -3.05)),
        P_("exhaustL", CHROME, (0.45, 0.2, -3.3), (0.65, 0.32, -3.05)),
        P_("exhaustR", CHROME, (-0.65, 0.2, -3.3), (-0.45, 0.32, -3.05)),
        P_("tailL", "red_concrete", (0.85, 0.5, -3.1), (1.4, 0.72, -3.04)),
        P_("tailR", "red_concrete", (-1.4, 0.5, -3.1), (-0.85, 0.72, -3.04)),
        # --- the scuttle, the bonnet, the nose
        P_("scuttle", BODY, (-1.5, 0.14, ZS), (1.5, TOP, ZW)),
        P_("bonnet", BODY, (-1.2, TOP - 0.3, ZW), (1.2, TOP, 3.1), rot=bon_rot, pivot=bon_pivot),
        P_("stripe", "white_concrete", (-0.28, TOP, ZW), (0.28, TOP + 0.015, 3.1), rot=bon_rot, pivot=bon_pivot),
        P_("stripeTub", "white_concrete", (-0.28, 0.82, -3.05), (0.28, 0.835, -1.0)),
        P_("nose", BODY, (-1.0, 0.26, 2.95), (1.0, 0.46, 3.3)),
        P_("grill", TRIM, (-0.5, 0.28, 3.29), (0.5, 0.42, 3.35)),
        P_("bumperF", CHROME, (-1.15, 0.2, 3.25), (1.15, 0.34, 3.4)),
        P_("headL", "white_concrete", (0.85, TOP - 0.34, 2.55), (1.3, TOP - 0.06, 2.95), rot=bon_rot, pivot=bon_pivot, bright=(15, 15)),
        P_("headR", "white_concrete", (-1.3, TOP - 0.34, 2.55), (-0.85, TOP - 0.06, 2.95), rot=bon_rot, pivot=bon_pivot, bright=(15, 15)),
        # --- the windscreen: raked glass and two thin posts at all (the glass ends in a bare edge); the highest point of the screen is 1.11, far below any seated eye
        P_("screen", "light_blue_stained_glass", (-1.32, TOP, ZW), (1.32, TOP + 0.44, ZW + 0.04), rot=ws_rot, pivot=ws_pivot),
        P_("postL", CHROME, (1.3, TOP, ZW - 0.02), (1.42, TOP + 0.46, ZW + 0.06), rot=ws_rot, pivot=ws_pivot),
        P_("postR", CHROME, (-1.42, TOP, ZW - 0.02), (-1.3, TOP + 0.46, ZW + 0.06), rot=ws_rot, pivot=ws_pivot),
        # --- the driver's dash: a binnacle in front of the right seat only, the steering column and wheel
        P_("binnacle", TRIM, (-1.25, TOP, ZS - 0.04), (-0.2, TOP + 0.09, ZS + 0.2)),
        P_("gauges", "light_gray_concrete", (-1.1, TOP + 0.09, ZS), (-0.55, TOP + 0.13, ZS + 0.12), bright=(0, 10)),
        P_("column", TRIM, (-0.78, 0.6, 0.46), (-0.66, 0.8, 0.84)),
        # --- the seats: cushion (its top is where the rider's seat bones are: 0.6 above the feet), back, headrest (the back leans 10 degrees)
        P_("cushionL", "brown_concrete", (0.4, 0.17, -0.58), (1.04, 0.74, 0.32)),
        P_("backL", "brown_concrete", (0.4, 0.74, -0.98), (1.04, 1.32, -0.78), rot=qaxis("x", -10.0), pivot=(0.72, 0.74, -0.88)),
        P_("restL", "brown_concrete", (0.5, 1.34, -1.04), (0.94, 1.7, -0.84), rot=qaxis("x", -10.0), pivot=(0.72, 0.74, -0.88)),
        P_("cushionR", "brown_concrete", (-1.04, 0.17, -0.34), (-0.4, 0.74, 0.56)),
        P_("backR", "brown_concrete", (-1.04, 0.74, -0.74), (-0.4, 1.32, -0.54), rot=qaxis("x", -10.0), pivot=(-0.72, 0.74, -0.64)),
        P_("restR", "brown_concrete", (-0.94, 1.34, -0.8), (-0.5, 1.7, -0.6), rot=qaxis("x", -10.0), pivot=(-0.72, 0.74, -0.64)),
        # --- wing mirrors: a stem off the screen post, a dark head on it
        P_("stemL", CHROME, (1.42, 0.78, ZW - 0.02), (1.66, 0.82, ZW + 0.04)),
        P_("mirrorL", TRIM, (1.64, 0.74, ZW - 0.1), (1.7, 0.9, ZW + 0.14)),
        P_("stemR", CHROME, (-1.66, 0.78, ZW - 0.02), (-1.42, 0.82, ZW + 0.04)),
        P_("mirrorR", TRIM, (-1.7, 0.74, ZW - 0.1), (-1.64, 0.9, ZW + 0.14)),
    ]
    # --- the steering wheel: a ring of eight boxes, tilted 30 degrees, in front of the driver's chest
    parts += _ring("wheel", TRIM, (SEAT_DRIVER[0], 1.12, 0.54), 0.27, 30.0, n=8, thick=0.06)
    parts.append(P_("hub", "light_gray_concrete", (SEAT_DRIVER[0] - 0.07, 1.06, 0.48), (SEAT_DRIVER[0] + 0.07, 1.18, 0.56)))
    # --- wheels: an octagon is two overlapping boxes; a grey hub cap on the outside
    for nm, sx, zc in (("FL", 1, 2.0), ("FR", -1, 2.0), ("RL", 1, -2.3), ("RR", -1, -2.3)):
        x0, x1 = (1.46, 1.82) if sx > 0 else (-1.82, -1.46)
        parts.append(P_(f"wheel{nm}a", TRIM, (x0, 0.12, zc - 0.4), (x1, 0.68, zc + 0.4)))
        parts.append(P_(f"wheel{nm}b", TRIM, (x0, 0.0, zc - 0.28), (x1, 0.8, zc + 0.28)))
        hx0, hx1 = (1.8, 1.86) if sx > 0 else (-1.86, -1.8)
        parts.append(P_(f"hub{nm}", "light_gray_concrete", (hx0, 0.26, zc - 0.14), (hx1, 0.54, zc + 0.14)))
    return parts

def door_motion(deg):
    """rigid motion for the door parts: rotate `deg` about +y through the hinge"""
    return (qaxis("y", deg), DOOR_HINGE, (0, 0, 0))


ROLL_PIVOT = (-1.84, 0.0, 0.0)          # the lower right edge (the right wheels' outer faces): the car lies on its right side, the open top facing right
LIE_REACH = (3.25, 3.65)                # lying: how far its top reaches to the right of the car's centre line, how high its left wheels stand


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
def wagon_parts(ramp=False, low_side=None):
    """The flat rail wagon (5 wide, 9 long, deck at y 0).  `low_side`: "R" or "L" (the wagon's own right/left): that side has no railing
    and no posts, only the yellow kerb, so that nothing stands between the car's seat and the view out of that side."""
    P_ = Part
    parts = [
        P_("bed", "gray_concrete", (-2.5, -1.0, -4.5), (2.5, 0.0, 4.5), group="wagon"),
        P_("edgeL", "yellow_concrete", (2.2, -1.0, -4.5), (2.5, 0.01, 4.5), group="wagon"),
        P_("edgeR", "yellow_concrete", (-2.5, -1.0, -4.5), (-2.2, 0.01, 4.5), group="wagon"),
        P_("edgeF", "yellow_concrete", (-2.5, -1.0, 4.2), (2.5, 0.01, 4.5), group="wagon"),
        P_("edgeB", "yellow_concrete", (-2.5, -1.0, -4.5), (2.5, 0.01, -4.2), group="wagon"),
        P_("bogieL", "black_concrete", (-1.6, -1.55, -3.4), (1.6, -1.0, -2.2), group="wagon"),
        P_("bogieR", "black_concrete", (-1.6, -1.55, 2.2), (1.6, -1.0, 3.4), group="wagon"),
        P_("hitchF", "iron_block", (-0.25, -0.75, 4.5), (0.25, -0.35, 5.6), group="wagon"),
        P_("hitchB", "iron_block", (-0.25, -0.75, -5.6), (0.25, -0.35, -4.5), group="wagon"),
    ]
    if low_side != "L":
        parts.append(P_("railL", "iron_block", (2.35, 0.8, -4.3), (2.5, 0.95, 4.3), group="wagon"))
    if low_side != "R":
        parts.append(P_("railR", "iron_block", (-2.5, 0.8, -4.3), (-2.35, 0.95, 4.3), group="wagon"))
    parts.append(P_("railF", "iron_block", (-2.5, 0.8, 4.15), (2.5, 0.95, 4.3), group="wagon"))
    for i, (x, z) in enumerate(((2.3, 4.15), (-2.5, 4.15), (2.3, -4.3), (-2.5, -4.3))):
        side = "L" if x > 0 else "R"
        if side == low_side:
            continue
        parts.append(P_(f"post{i}", "iron_block", (x, 0.0, z), (x + 0.2, 1.0, z + 0.15), group="wagon"))
    if low_side:
        # a low yellow kerb on the open side, so the edge reads without standing in the way (0.22 high: far below any seated eye)
        x0, x1 = (2.28, 2.5) if low_side == "L" else (-2.5, -2.28)
        parts.append(P_("kerb", "yellow_concrete", (x0, 0.0, -4.5), (x1, 0.22, 4.5), group="wagon"))
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
class _Seats(dict):
    """The seats {role: (x, y, z)}.  system.py adds a 'face the road' line for every rig that has a "driver" seat; a rig that turns the
    driver's head itself (the car: she looks at the road, then at the boy when she speaks) hides the key from that one test."""
    hide = ()

    def __contains__(self, k):
        return False if k in self.hide else dict.__contains__(self, k)


class Rig:
    """A named set of display parts plus seat entities, moved as one."""

    def __init__(self, name, parts, seats, tp_duration=3, view_range=2.0, bright=None, seat_yaw=0.0, driver_face=None):
        self.name = name
        self.parts = parts
        self.seats = _Seats(seats)          # {"driver": (x, y, z), "passenger": (x, y, z)}: where the rider's FEET are, model space
        self.tp_duration = tp_duration
        self.view_range = view_range
        self.bright = bright
        self.seat_yaw = seat_yaw            # degrees the seats are turned against the rig (the reversed car on the wagon)
        self.driver_face = driver_face      # None, or the yaw of the driver's forward against the rig: Misato is held facing the road unless she looks at the boy
        if driver_face is not None:
            self.seats.hide = ("driver",)
        self.base_motion = {}               # part name -> motion applied before anything else (the turned car inside the cartrain)

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
            tags = [self.tag, f"angel.pt_{p.name}", "angel.rpart", "angel.new"]
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
        cmds = [f"tp @e[tag={self.tag},tag=angel.rpart] ~ ~ ~ ~ ~"]
        if seats:
            yaw = f"~{num(self.seat_yaw)}" if self.seat_yaw else "~"
            for role, (x, y, z) in self.seats.items():
                # the rider's feet end up 0.6 below the seat entity's origin (measured on the server with a mannequin)
                cmds.append(f"tp @e[tag={self.tag},tag=angel.seat_{role},limit=1] ^{num(x)} ^{num(y + 0.6)} ^{num(z)} {yaw} ~")
            if self.driver_face is not None and "driver" in self.seats.keys():
                # Misato keeps her eyes on the road (a point 8 ahead of the seat and 0.6 down: her feet's height, so her gaze is level with the car) unless the cast has her looking at the boy (#look_misato 1)
                cmds.append(f"execute unless score #look_misato angel.cast matches 1 if entity @e[tag=angel.misato,tag=angel.char,limit=1] "
                            f"as @e[tag={self.tag},tag=angel.seat_driver,limit=1] at @s run "
                            f"rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8")
        return cmds

    def ahead_cmds(self):
        """One-off: Misato looks at the road now (used when the car stands still, where follow does not run)."""
        return [f"function angel:cast/look {{id:\"misato\",mode:\"ahead\"}}",
                f"execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag={self.tag},tag=angel.seat_driver,limit=1] at @s run "
                f"rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8"]

    def pose_cmds(self, group_motions, interp):
        """data merge commands that move named parts/groups to a pose over `interp` ticks (door, roll)."""
        cmds = []
        for p in self.parts:
            extra = group_motions.get(p.name) or group_motions.get(p.group)
            if extra is not None or p.name in group_motions or p.group in group_motions:
                cmds.append(part_merge(p, self.tag, self.motion_for(p, extra), interp))
        return cmds


def car_rig(name="car"):
    return Rig(name, car_parts(), {"driver": SEAT_DRIVER, "passenger": SEAT_PASSENGER}, driver_face=0.0)


def cartrain_rig(name, reversed_car=False, ramp=False, bright=None, low_side=None):
    """Wagon plus the car in one rig.  `reversed_car`: the car stands the other way round on the wagon (nose to the wagon's rear), so that
    its left (passenger) side faces the wagon's right-hand side.  `low_side`: see wagon_parts."""
    parts = list(wagon_parts(ramp, low_side)) + car_parts()
    if reversed_car:
        # a half turn about the vertical axis: (x, z) -> (-x, -z); the seats turn with it and face the other way
        seats = {"driver": (-SEAT_DRIVER[0], SEAT_DRIVER[1], -SEAT_DRIVER[2]), "passenger": (-SEAT_PASSENGER[0], SEAT_PASSENGER[1], -SEAT_PASSENGER[2])}
    else:
        seats = {"driver": SEAT_DRIVER, "passenger": SEAT_PASSENGER}
    r = Rig(name, parts, seats, bright=bright, seat_yaw=180.0 if reversed_car else 0.0, driver_face=0.0)
    if reversed_car:
        qy = qaxis("y", 180.0)
        for p in car_parts():
            r.base_motion[p.name] = (qy, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    r.reversed_car = reversed_car
    return r


def aircraft_rig(name, scale=2.0):
    return Rig(name, aircraft_parts(scale), {}, tp_duration=2, view_range=8.0)

