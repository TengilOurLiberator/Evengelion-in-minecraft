"""Things done to the car rig: the door, rolling onto its side and back, boarding and getting out, where Misato looks.

The car is an open roadster, right-hand drive: the boy (the passenger) sits on the LEFT, Misato on the RIGHT, one seat width and a half apart
(models.py).  The passenger door is the left one; on the street the car stops with its left side to the boy.
"""
from context import cast_look, cast_mount, cast_remove, cast_summon, ride_passenger, tp_player, play_at
from core import NS, OBJ, P, PA, local_to_world, num, sset, QI, qaxis
from models import DOOR_OPEN_DEG, LIE_REACH, door_motion, roll_motion, SEAT_DRIVER, SEAT_PASSENGER


def pose_xyz(pose):
    return pose[0], pose[1], pose[2]


def door_world(pose, side=2.2):
    """Where the passenger door is (a little way out to the left of the car's centre line: the body's left flank is at 1.5, its wheels at 1.82)."""
    return local_to_world(pose_xyz(pose), pose[3], 0.0, side, 0.0, 0.0)


def seat_world(pose, role="passenger"):
    s = SEAT_PASSENGER if role == "passenger" else SEAT_DRIVER
    return local_to_world(pose_xyz(pose), pose[3], 0.0, s[0], s[1], s[2])


def door_cmds(rig, pose, open_, ticks=10):
    deg = DOOR_OPEN_DEG if open_ else 0.0
    x, y, z = door_world(pose)
    # sfx.car_door is a slam (1.2 s): the shut is the sound itself, the open the same sample softer and higher (a latch and a swing)
    snd = play_at("angel:sfx.car_door", x, y + 1, z, 0.55, 1.25, 0.0) if open_ else play_at("angel:sfx.car_door", x, y + 1, z, 1.2, 1.0, 0.0)
    return rig.pose_cmds({"door": door_motion(deg)}, ticks) + [snd]


def roll_keyframes(rig, deg_from, deg_to, ticks, steps=8):
    """[(delay_ticks, [commands])] rolling the car from one angle to another in `steps` linear pieces (so the squash that a straight
    interpolation of a rotation would cause between the ends never shows)."""
    out = []
    per = max(1, ticks // steps)
    for i in range(1, steps + 1):
        a = deg_from + (deg_to - deg_from) * i / steps
        out.append(((i - 1) * per, rig.pose_cmds({p.name: roll_motion(a) for p in rig.parts}, per + 1)))
    return out


def roll_motions(rig, deg):
    return {p.name: roll_motion(deg) for p in rig.parts}


def board_player_cmds():
    """The player climbs in: he is put on the passenger seat entity (never teleported again while riding) and the ride lock turns on."""
    return ride_passenger()


def lie_stand_spots(pose, side_blocks=6.0, fwd=(-0.6, 1.2)):
    """Standing places for the player and Misato beside the car when it lies on its right side: on the right, where the open top faces."""
    px, py, pz = local_to_world(pose_xyz(pose), pose[3], 0.0, -side_blocks, 0.0, fwd[0])
    mx, my, mz = local_to_world(pose_xyz(pose), pose[3], 0.0, -side_blocks, 0.0, fwd[1])
    return (px, pz), (mx, mz)


def lie_top(pose):
    """The middle of the open top of the car lying on its right side (its reach to the right is LIE_REACH[0])."""
    return local_to_world(pose_xyz(pose), pose[3], 0.0, -(LIE_REACH[0] + 0.35), 0.0, 0.0)


def lie_centre(pose):
    """The middle of the car lying on its right side, on the ground (for the push's hit box, the dust, the sounds)."""
    return local_to_world(pose_xyz(pose), pose[3], 0.0, -2.5, 0.0, 0.0)


# ---------------------------------------------------------------------------------------------------- where Misato looks
def look_boy():
    """Misato turns to the boy (the cast turns her, 12 degrees a tick, while she stands still or sits)."""
    return [cast_look("misato", "player")]


def look_road(rig):
    """Misato looks at the road again: the cast's own tracking off, and the rig holds her facing the way the car goes."""
    return rig.ahead_cmds()


def say_glancing(s, rig, lid, glance=2.6, gap=None):
    """Say a line of Misato's as she drives: she turns to the boy as it begins, and looks at the road again `glance` seconds in
    (the line goes on).  glance=None: she looks at him for the whole line and the road is left to the caller."""
    s.do(*look_boy(), note=f"{lid}: she glances at the boy")
    if glance is not None:
        s.after(glance, *look_road(rig), note=f"{lid}: eyes back on the road")
    s.say(lid, gap=gap)
    return s
