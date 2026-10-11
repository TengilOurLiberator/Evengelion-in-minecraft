"""Where everything of scenes 6 and 7 stands, taken from the anchors and the built hq set (never typed in twice), and the check that a 16x
giant can ride the launch shaft without catching on a fitting.

World coordinates: hq origin (3000, 0, 0); the sets' own lists (CAGE_LIGHTS, EYES_LEFT ...) are in local coordinates.
"""
import math
import sys

from core import num

# ------------------------------------------------------------------------------------------------ the giant
GIANT_W, GIANT_H, GIANT_EYE = 9.6, 28.8, 25.9      # hitbox and eye height of the player at scale 16 (fight README)

# ------------------------------------------------------------------------------------------------ the cockpit in front of the face
# The giant's eye slits are at world y 61..64 (z 57, in a recess behind the face plate at z 59); the nose ridge stands out to z 61.0 on
# the centre line.  The seat's rider has his eyes at feet + 1.62, so the feet go 1.62 below the middle of the slits.
COCKPIT_EYE = (3096.5, 62.8, 63.2)
COCKPIT_FEET = (COCKPIT_EYE[0], COCKPIT_EYE[1] - 1.62, COCKPIT_EYE[2])
COCKPIT_HALF = 1.5                                  # half-size of the amber glass cube round the head

# boxes (x, y, z, dx, dy, dz) for the rescue in launch_hooks.restore: the whole launch shaft above the pad, the air in front of the face
SHAFT_BOX = (3000, 8, 0, 20, 148, 20)
COCKPIT_BOX = (3088, 57, 56, 18, 22, 16)
CAGE_PROBE = (3096, 60, 100)                        # a block in the middle of the cage: if it is loaded the cage can be switched
PAD_FEET = (3009.0, 4.0, 9.0)
FACE_FEET = (3096.5, 54.0, 72.5)

# ------------------------------------------------------------------------------------------------ the plug
PLUG_FEET_Y = 12.0                                  # the plug_seat anchor: standing on the seat block
PLUG_BOX = dict(x0=3029.0, x1=3032.0, y0=10.0, y1=15.0, z0=6.0, z1=15.0)     # the open space inside the capsule

# ------------------------------------------------------------------------------------------------ the launch
CUT_FEET_Y = 108.0                                  # the white-out starts when the feet pass this height (head top 136.8; the sealed roof is at 157)


def hq_module(ctx):
    """The set module sets.hq with its lists filled (building the probe fills them)."""
    ctx.probe("hq")
    return sys.modules["sets.hq"]


def shaft_report(ctx, cut_feet=CUT_FEET_Y):
    """Clear cross-section of the launch shaft for the giant's hitbox, from the voxel set.  Returns (lines, first_block_height).
    The hitbox is GIANT_W wide about the pad centre and GIANT_H tall; blocks that are passable (air, light ...) do not count."""
    import numpy as np
    probe = ctx.probe("hq")
    o = probe.o
    mod = hq_module(ctx)
    X1, X2, Z1, Z2, F, T = (mod.SHAFT[k] for k in ("x1", "x2", "z1", "z2", "floor", "top"))
    c = (X1 + X2 + 1) / 2.0
    hw = GIANT_W / 2.0
    cells = [(x, z) for x in range(int(math.floor(c - hw)), int(math.floor(c + hw - 1e-9)) + 1)
             for z in range(int(math.floor(c - hw)), int(math.floor(c + hw - 1e-9)) + 1)]
    hits = {}
    for y in range(F + 1, T + 4):
        for (x, z) in cells:
            gid = probe.gid(o[0] + x, y, z)
            if not probe.passable[gid]:
                hits.setdefault(probe.pal[gid].replace("minecraft:", "").split("[")[0], set()).add(y)
    lines = [f"launch shaft: interior x {X1}..{X2}, z {Z1}..{Z2} ({X2 - X1 + 1} x {Z2 - Z1 + 1}); giant hitbox {GIANT_W} x {GIANT_H} about "
             f"({c:.1f}, {c:.1f}); footprint cells x,z {cells[0]}..{cells[-1]}"]
    # fittings that stand inside the 14 x 14 but outside the hitbox footprint
    side = {}
    for y in range(F + 1, T + 1):
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if (x, z) in cells:
                    continue
                gid = probe.gid(o[0] + x, y, z)
                if not probe.passable[gid]:
                    side.setdefault(probe.pal[gid].replace("minecraft:", "").split("[")[0], set()).add((x, z))
    if side:
        lines.append("  fittings inside the shaft but clear of the hitbox: " + "; ".join(
            f"{n} at {len(s)} cells (x,z) e.g. {sorted(s)[:4]}" for n, s in sorted(side.items())))
    first = None
    for n, ys in sorted(hits.items()):
        lines.append(f"  IN THE HITBOX FOOTPRINT: {n} at y {sorted(ys)[:6]}{' ...' if len(ys) > 6 else ''}")
        first = min(first, min(ys)) if first is not None else min(ys)
    if first is None:
        lines.append("  nothing inside the hitbox footprint")
    else:
        lines.append(f"  lowest obstruction y={first}: the hitbox top (feet + {GIANT_H}) reaches it when the feet are at y={first - GIANT_H:.1f}; "
                     f"the white-out starts at feet y={cut_feet} (top {cut_feet + GIANT_H:.1f}), so there is {first - GIANT_H - cut_feet:.1f} blocks to spare")
    return lines, first
