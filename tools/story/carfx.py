"""Things done to the car rig: the door, rolling onto its side and back, boarding and getting out."""
from context import cast_mount, cast_remove, cast_summon, ride_passenger, tp_player, play_at
from core import NS, OBJ, P, PA, local_to_world, num, sset, QI, qaxis
from models import DOOR_OPEN_DEG, door_motion, roll_motion, SEAT_DRIVER, SEAT_PASSENGER


def pose_xyz(pose):
    return pose[0], pose[1], pose[2]


def door_world(pose, side=2.3):
    """Where the passenger door is (a little way out to the left of the car's centre)."""
    return local_to_world(pose_xyz(pose), pose[3], 0.0, side, 0.0, 0.0)


def seat_world(pose, role="passenger"):
    s = SEAT_PASSENGER if role == "passenger" else SEAT_DRIVER
    return local_to_world(pose_xyz(pose), pose[3], 0.0, s[0], s[1], s[2])


def door_cmds(rig, pose, open_, ticks=10):
    deg = DOOR_OPEN_DEG if open_ else 0.0
    x, y, z = door_world(pose)
    snd = "minecraft:block.iron_door.open" if open_ else "minecraft:block.iron_door.close"
    return rig.pose_cmds({"door": door_motion(deg)}, ticks) + [play_at(snd, x, y + 1, z, 1.2, 1.3, 0.3)]


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


def lie_stand_spots(pose, side_blocks=5.4, fwd=(-0.6, 1.2)):
    """Standing places for the player and Misato beside the car when it lies on its right side: on the right (the roof side)."""
    px, py, pz = local_to_world(pose_xyz(pose), pose[3], 0.0, -side_blocks, 0.0, fwd[0])
    mx, my, mz = local_to_world(pose_xyz(pose), pose[3], 0.0, -side_blocks, 0.0, fwd[1])
    return (px, pz), (mx, mz)
