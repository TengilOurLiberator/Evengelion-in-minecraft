"""A first-person ray-caster for the rides: what the boy sees from the passenger seat of the car (and of the car on the wagon).

It casts rays from a seated eye through the car's display boxes (every Part of models.car_parts(), rotated boxes included), a box model of
Misato in the driver's seat, and optionally the built voxel world (world_probe.Probe) behind them, and writes PNG renders and numbers:

    python ride_view.py car   [--out DIR]     forward / left / right / up / back renders of the car on its own, the obstruction numbers
    python ride_view.py wagon [--out DIR]     the car on the wagon at geofront.wall_opens and geofront.reveal against the built Geofront
    python ride_view.py old   [--out DIR]     the same numbers for the old closed coupe (kept in ride_view_old.py, for the before / after)

Model space is the rig's: +x LEFT, +y up, +z forward.  Camera angles: yaw is turned to the LEFT, pitch is up.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from core import qaxis, qmul, qrot                                  # noqa: E402
import models                                                       # noqa: E402

# ---------------------------------------------------------------------------------------------------- colours
COLOURS = {
    "blue_concrete": (40, 90, 220), "black_concrete": (25, 25, 28), "gray_concrete": (95, 98, 102), "light_gray_concrete": (170, 172, 176),
    "white_concrete": (240, 240, 240), "red_concrete": (210, 40, 40), "brown_concrete": (120, 80, 50), "iron_block": (215, 215, 220),
    "yellow_concrete": (235, 200, 40), "orange_concrete": (240, 120, 20), "light_blue_stained_glass": (150, 200, 235),
    "polished_blackstone": (40, 38, 46),
}
MISATO = [  # name, lo, hi (model space), colour: Misato seated as a standing figure with the legs forward: head, hair, jacket, dress, arms, legs, boots
    ("m_head", (-0.235, 1.4, -0.235), (0.235, 1.87, 0.235), (225, 190, 160)),
    ("m_hair", (-0.27, 1.38, -0.30), (0.27, 1.92, 0.27), (90, 40, 110)),
    ("m_hairback", (-0.27, 0.95, -0.34), (0.27, 1.4, -0.2), (90, 40, 110)),
    ("m_torso", (-0.25, 0.6, -0.14), (0.25, 1.42, 0.14), (190, 40, 50)),
    ("m_armR", (-0.42, 0.7, -0.12), (-0.25, 1.4, 0.12), (190, 40, 50)),
    ("m_armL", (0.25, 0.7, -0.12), (0.42, 1.4, 0.12), (190, 40, 50)),
    ("m_thighR", (-0.25, 0.4, 0.0), (-0.02, 0.62, 0.72), (30, 30, 36)),
    ("m_thighL", (0.02, 0.4, 0.0), (0.25, 0.62, 0.72), (30, 30, 36)),
    ("m_shinR", (-0.25, 0.0, 0.58), (-0.02, 0.45, 0.78), (30, 30, 36)),
    ("m_shinL", (0.02, 0.0, 0.58), (0.25, 0.45, 0.78), (30, 30, 36)),
]


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


class Box:
    def __init__(self, name, state, t, q, size, colour=None, kind="car"):
        self.name, self.state, self.kind = name, state, kind
        self.t = np.array(t, float)
        self.R = quat_mat(q)
        self.size = np.array(size, float)
        self.colour = colour or COLOURS.get(state, (160, 160, 160))


def car_boxes(parts, base_motion=None, motions=None, kind="car"):
    out = []
    for p in parts:
        extra = (motions or {}).get(p.name) or (motions or {}).get(p.group)
        mot = None
        bm = (base_motion or {}).get(p.name)
        if bm and extra:
            mot = models.compose(bm, extra)
        else:
            mot = extra or bm
        t, q, s = p.with_motion(*mot) if mot else p.with_motion()
        out.append(Box(p.name, p.state, t, q, s, kind="glass" if (p.state and "glass" in p.state) else kind))
    return out


def misato_boxes(seat_feet, reversed_car=False):
    """Misato as boxes at the driver's feet position (x, y, z); a reversed car turns her half a turn about the vertical axis."""
    out = []
    fx, fy, fz = seat_feet
    q = qaxis("y", 180.0) if reversed_car else (0, 0, 0, 1)
    for name, lo, hi, col in MISATO:
        size = tuple(h - l for l, h in zip(lo, hi))
        if reversed_car:
            # rotate the box about the vertical axis through the seat (feet) point
            tt = qrot(q, lo)
            out.append(Box(name, None, (fx + tt[0], fy + lo[1], fz + tt[2]), q, size, col, kind="misato"))
        else:
            out.append(Box(name, None, (fx + lo[0], fy + lo[1], fz + lo[2]), (0, 0, 0, 1), size, col, kind="misato"))
    return out


# ---------------------------------------------------------------------------------------------------- the world
def block_colour(name):
    n = (name or "air").replace("minecraft:", "").split("[")[0]
    if "water" in n:
        return (45, 100, 190)
    if any(k in n for k in ("glowstone", "sea_lantern", "froglight", "light", "lantern")):
        return (255, 235, 150)
    if "lily" in n or "moss" in n or "grass" in n or "leaves" in n:
        return (70, 140, 60)
    for col, rgb in (("white", (235, 235, 235)), ("light_gray", (160, 160, 160)), ("gray", (90, 90, 95)), ("black", (30, 30, 34)),
                     ("red", (180, 50, 40)), ("orange", (215, 120, 50)), ("yellow", (220, 190, 60)), ("lime", (130, 200, 60)),
                     ("green", (60, 120, 60)), ("cyan", (50, 150, 160)), ("light_blue", (120, 170, 220)), ("blue", (50, 80, 180)),
                     ("purple", (120, 60, 160)), ("brown", (110, 75, 50)), ("pink", (220, 130, 160))):
        if col in n:
            return rgb
    if "sandstone" in n or "sand" in n:
        return (215, 190, 130)
    if "terracotta" in n or "clay" in n or "mud" in n:
        return (170, 100, 70)
    if "quartz" in n:
        return (235, 230, 220)
    if "deepslate" in n:
        return (60, 60, 68)
    if "dirt" in n or "podzol" in n:
        return (120, 85, 55)
    if "stone" in n or "andesite" in n or "gravel" in n or "dripstone" in n:
        return (125, 125, 128)
    if "gold" in n:
        return (240, 200, 60)
    if "iron" in n:
        return (200, 200, 205)
    return (140, 140, 150)


class World:
    """The built voxel world seen as an array: solid mask + colours, marched in world coordinates."""

    def __init__(self, probe):
        self.probe = probe
        self.a = probe.w.a
        self.o = np.array(probe.o)
        self.solid_by_gid = ~probe.passable
        self.col_by_gid = np.array([block_colour(n) for n in probe.pal], float)

    def march(self, o, d, tmax=500.0, near=0.05):
        """o: (3,), d: (N, 3) unit.  Returns t (N,) of the first solid cell (inf if none) and the gid."""
        n = len(d)
        hit_t = np.full(n, np.inf)
        hit_g = np.zeros(n, int)
        alive = np.ones(n, bool)
        sh = np.array(self.a.shape)
        t = near
        while t < tmax and alive.any():
            idx = np.nonzero(alive)[0]
            p = o[None, :] + d[idx] * t - self.o[None, :]
            ip = np.floor(p).astype(int)
            inside = np.all((ip >= 0) & (ip < sh), axis=1)
            g = np.zeros(len(idx), int)
            ii = ip[inside]
            g[inside] = self.a[ii[:, 0], ii[:, 1], ii[:, 2]]
            s = self.solid_by_gid[g] & inside
            hit_t[idx[s]] = t
            hit_g[idx[s]] = g[s]
            alive[idx[s]] = False
            # out of the box and moving away: stop
            out = ~inside & ((p < 0) & (d[idx] < 0) | (p >= sh) & (d[idx] > 0)).any(axis=1)
            alive[idx[out]] = False
            t += 0.25 if t < 20 else (0.5 if t < 100 else 1.0)
        return hit_t, hit_g


# ---------------------------------------------------------------------------------------------------- the casting
def cam_dirs(yaw, pitch, fov, w, h):
    """Unit ray directions (h*w, 3) in model space for a camera turned `yaw` degrees to the left and `pitch` up; fov is the horizontal and the vertical angle."""
    ty = math.radians(yaw)
    tp = math.radians(pitch)
    fwd = np.array([math.sin(ty) * math.cos(tp), math.sin(tp), math.cos(ty) * math.cos(tp)])
    right = np.array([-math.cos(ty), 0.0, math.sin(ty)])
    up = np.cross(fwd, right) * -1.0
    up = np.array([-math.sin(ty) * math.sin(tp), math.cos(tp), -math.cos(ty) * math.sin(tp)])
    half = math.tan(math.radians(fov) / 2.0)
    us = (np.arange(w) + 0.5) / w * 2 - 1
    vs = 1 - (np.arange(h) + 0.5) / h * 2
    U, V = np.meshgrid(us * half, vs * half)
    d = fwd[None, None, :] + U[..., None] * right[None, None, :] + V[..., None] * up[None, None, :]
    d = d.reshape(-1, 3)
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def hit_boxes(o, d, boxes):
    """First box hit by each ray: (t (N,), index (N,) or -1, face axis (N,))."""
    n = len(d)
    best = np.full(n, np.inf)
    who = np.full(n, -1, int)
    axis = np.zeros(n, int)
    for k, b in enumerate(boxes):
        ol = b.R.T @ (o - b.t)
        dl = d @ b.R
        with np.errstate(divide="ignore", invalid="ignore"):
            inv = 1.0 / dl
            t1 = (0.0 - ol) * inv
            t2 = (b.size - ol) * inv
        tn = np.minimum(t1, t2)
        tf = np.maximum(t1, t2)
        t_enter = tn.max(axis=1)
        t_exit = tf.min(axis=1)
        # a block display is drawn from OUTSIDE only (back faces are culled): a ray that starts inside a box does not see that box
        ok = (t_exit > t_enter) & (t_enter > 1e-4) & (t_enter < best)
        if ok.any():
            best[ok] = t_enter[ok]
            who[ok] = k
            axis[ok] = np.argmax(tn, axis=1)[ok]
    return best, who, axis


class Scene:
    def __init__(self, boxes, world=None, pose=None, sky=(150, 190, 240), ground=None):
        """boxes: model-space boxes.  world + pose=(x, y, z, yaw, pitch): the rig stands at pose in the voxel world."""
        self.boxes = boxes
        self.world = world
        self.pose = pose
        self.sky = np.array(sky, float)
        self.ground = ground
        if pose is not None:
            from core import local_to_world
            x, y, z, yaw, pitch = pose
            self.origin = np.array([x, y, z], float)
            q = qmul(qaxis("y", -yaw), qaxis("x", pitch))
            self.M = quat_mat(q)
        else:
            self.origin = None
            self.M = None

    def cast(self, eye, d):
        """-> dict(t_box, who, axis, t_world, gid)"""
        e = np.array(eye, float)
        tb, who, axis = hit_boxes(e, d, self.boxes)
        out = {"t_box": tb, "who": who, "axis": axis}
        if self.world is not None:
            ow = self.origin + self.M @ e
            dw = d @ self.M.T
            tw, gid = self.world.march(ow, dw)
            out["t_world"], out["gid"] = tw, gid
        else:
            out["t_world"] = np.full(len(d), np.inf)
            out["gid"] = np.zeros(len(d), int)
        return out

    def render(self, eye, yaw, pitch, fov=100.0, size=240, shade=True):
        d = cam_dirs(yaw, pitch, fov, size, size)
        r = self.cast(eye, d)
        img = np.zeros((size * size, 3))
        img[:] = self.sky
        if self.world is not None:
            tw, gid = r["t_world"], r["gid"]
            m = np.isfinite(tw)
            base = self.world.col_by_gid[gid]
            fog = np.clip(tw / 400.0, 0, 1)[:, None]
            wc = base * (1 - 0.55 * fog) + np.array([20, 20, 30]) * 0.55 * fog
            img[m] = wc[m]
            img[~m] = (30, 30, 40) if self.ground is None else self.ground
        elif self.ground is not None:
            # a flat ground plane at y = 0 in model space
            with np.errstate(divide="ignore", invalid="ignore"):
                tg = -np.array(eye)[1] / d[:, 1]
            g = (d[:, 1] < 0) & (tg > 0)
            img[g] = self.ground
        tb, who = r["t_box"], r["who"]
        m = who >= 0
        if m.any():
            for k in np.unique(who[m]):
                mk = who == k
                col = np.array(self.boxes[k].colour, float)
                if shade:
                    ax = r["axis"][mk]
                    f = np.where(ax == 1, 1.0, np.where(ax == 0, 0.78, 0.62))[:, None]
                    # axis is in the box's own frame: fine for a shading hint
                    img[mk] = col[None, :] * f
                else:
                    img[mk] = col
        return img.reshape(size, size, 3).astype(np.uint8), r


def save(img, path, label=None, scale=2):
    from PIL import Image, ImageDraw
    im = Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST)
    if label:
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, im.width, 16), fill=(0, 0, 0))
        dr.text((4, 2), label, fill=(255, 255, 255))
    im.save(path)


def cross(img, size=None):
    """draw the horizon (a thin line across the middle) and the centre mark"""
    out = img.copy()
    h = out.shape[0]
    out[h // 2, ::2] = (255, 0, 255)
    return out


# ---------------------------------------------------------------------------------------------------- the numbers
def obstruction(scene, eye, yaw=0.0, pitch=0.0, fov=100.0, size=200, kinds=("car", "glass", "misato")):
    """Fraction of a fov x fov frame whose first hit is a box of each kind: {'car': f, 'misato': f, 'clear': f}."""
    d = cam_dirs(yaw, pitch, fov, size, size)
    r = scene.cast(eye, d)
    who = r["who"]
    out = {}
    for kd in kinds:
        ks = [i for i, b in enumerate(scene.boxes) if b.kind == kd]
        out[kd] = float(np.isin(who, ks).mean()) if ks else 0.0
    out["clear"] = 1.0 - out.get("car", 0.0) - out.get("misato", 0.0)           # the windscreen glass is see-through: counted apart, not as an obstruction
    return out


def horizon_sweep(scene, eye, az_range=(-80, 80), kind="car", el_max=89.0, step=2.0):
    """For every azimuth (left positive) in the range: the highest elevation (degrees) at which a ray still meets a box of `kind`
    (-90 if none).  Returns (azimuths, elevations): a part that crosses the horizon has a value > 0."""
    azs = np.arange(az_range[0], az_range[1] + 1e-6, step)
    els = np.arange(-60.0, el_max + 1e-6, 1.0)
    ks = [i for i, b in enumerate(scene.boxes) if b.kind == kind]
    res = np.full(len(azs), -90.0)
    for i, az in enumerate(azs):
        ya, ye = math.radians(az), np.radians(els)
        d = np.stack([np.sin(ya) * np.cos(ye), np.sin(ye), np.cos(ya) * np.cos(ye)], axis=1)
        tb, who, _ = hit_boxes(np.array(eye, float), d, scene.boxes)
        hit = np.isin(who, ks)
        if hit.any():
            res[i] = els[np.nonzero(hit)[0].max()]
    return azs, res


def eye_of(seat_feet, above):
    return (seat_feet[0], seat_feet[1] + above, seat_feet[2])


# ---------------------------------------------------------------------------------------------------- the car alone
def car_scene(parts=None, reversed_car=False, misato=True, motions=None):
    parts = parts if parts is not None else models.car_parts()
    base = None
    if reversed_car:
        qy = qaxis("y", 180.0)
        base = {p.name: (qy, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)) for p in parts}
    boxes = car_boxes(parts, base, motions)
    if misato:
        boxes += misato_boxes(models.SEAT_DRIVER, reversed_car)
    return boxes


def report_car(out_dir, parts=None, seat_p=None, seat_d=None, tag="car"):
    os.makedirs(out_dir, exist_ok=True)
    seat_p = seat_p or models.SEAT_PASSENGER
    parts = parts if parts is not None else models.car_parts()
    boxes = car_boxes(parts) + misato_boxes(seat_d or models.SEAT_DRIVER)
    sc = Scene(boxes, ground=(70, 70, 74))
    lines = [f"{tag}: {len(parts)} parts"]
    for label, above in (("low", models.EYE_ABOVE_FEET[0]), ("flat", models.EYE_ABOVE_FEET[1]), ("tall", models.EYE_ABOVE_FEET[2]), ("seated-low", 1.15)):
        eye = eye_of(seat_p, above)
        o = obstruction(sc, eye, 0, 0, 100, 160)
        o20 = obstruction(sc, eye, 0, 0, 100, 160)
        lines.append(f"  eye {label:10s} ({above:.2f} above the feet = y {eye[1]:.2f}): forward 100x100 frame: opaque car {100 * o['car']:5.1f} %  Misato {100 * o['misato']:4.1f} %  (glass {100 * o['glass']:4.1f} %)  clear {100 * o['clear']:5.1f} %")
        azs, el = horizon_sweep(sc, eye, (-80, 80), "car")
        lines.append(f"      highest car part in the forward 160 degrees: {el.max():+5.1f} deg above the horizon (at azimuth {azs[int(el.argmax())]:+.0f}); parts above the horizon: {'NONE' if el.max() <= 0 else 'YES'}")
        azm, elm = horizon_sweep(sc, eye, (-80, 80), "misato")
        vis = azm[elm > -90]
        lines.append("      Misato inside the forward 160 degrees: " + (f"azimuths {vis.min():+.0f}..{vis.max():+.0f} (right is negative)" if len(vis) else "not at all"))
        # the upward view: any box above +10 deg anywhere around
        d = cam_dirs(0, 80, 100, 100, 100)
        r = sc.cast(eye, d)
        lines.append(f"      looking up (pitch 80, fov 100): {100 * float((r['who'] >= 0).mean()):.1f} % covered by car or Misato")
    eye = eye_of(seat_p, models.EYE_ABOVE_FEET[1])
    for name, yaw, pitch in (("forward", 0, 0), ("left", 90, 0), ("right", -90, 0), ("up", 0, 80), ("back", 180, 0), ("down", 0, -70)):
        img, r = sc.render(eye, yaw, pitch, 100.0, 240)
        save(cross(img), os.path.join(out_dir, f"{tag}_{name}.png"), f"{tag} {name} yaw {yaw} pitch {pitch} eye {eye[1]:.2f}")
    # a conversation view: yaw -90 + a bit up to Misato's head
    img, r = sc.render(eye, -78, 6, 70.0, 240)
    save(cross(img), os.path.join(out_dir, f"{tag}_misato.png"), f"{tag} turned to Misato (yaw -78 pitch +6, fov 70)")
    # the car seen from outside, for the model's shape (a camera 9 blocks away, 3/4 view)
    outside = Scene(boxes, ground=(70, 70, 74))
    for name, ex, ey, ez, yw, pt in (("front34", 6.5, 3.2, 8.0, 180 + 38, -14), ("side", 9.5, 1.8, 0.0, 90 + 0, -5), ("rear34", -6.0, 3.0, -8.5, -38, -14)):
        d = cam_dirs(0, 0, 60, 240, 240)
        # build the camera as an eye pointing at the car's centre
        centre = np.array([0.0, 0.7, 0.0])
        e = np.array([ex, ey, ez])
        f = centre - e
        f /= np.linalg.norm(f)
        right = np.cross(f, [0, 1, 0])
        right /= np.linalg.norm(right)
        up = np.cross(right, f)
        half = math.tan(math.radians(60) / 2)
        us = (np.arange(240) + 0.5) / 240 * 2 - 1
        vs = 1 - (np.arange(240) + 0.5) / 240 * 2
        U, V = np.meshgrid(us * half, vs * half)
        dd = f[None, None, :] + U[..., None] * right + V[..., None] * up
        dd = dd.reshape(-1, 3)
        dd /= np.linalg.norm(dd, axis=1, keepdims=True)
        r = outside.cast(e, dd)
        img = np.zeros((240 * 240, 3))
        img[:] = (150, 190, 240)
        with np.errstate(divide="ignore", invalid="ignore"):
            tg = -e[1] / dd[:, 1]
        g = (dd[:, 1] < 0) & (tg > 0)
        img[g] = (70, 70, 74)
        m = r["who"] >= 0
        for k in np.unique(r["who"][m]):
            mk = r["who"] == k
            ax = r["axis"][mk]
            f_ = np.where(ax == 1, 1.0, np.where(ax == 0, 0.8, 0.62))[:, None]
            img[mk] = np.array(outside.boxes[k].colour, float)[None, :] * f_
        save(img.reshape(240, 240, 3).astype(np.uint8), os.path.join(out_dir, f"{tag}_out_{name}.png"), f"{tag} from outside: {name}")
    return lines


# ---------------------------------------------------------------------------------------------------- the car on the wagon, in the Geofront
def wagon_report(ctx, out_dir, route_name="geofront_ride", rig_name="cartrain_b"):
    """The passenger's view out of the car on the wagon against the built Geofront at geofront.wall_opens and geofront.reveal (and a little
    after): renders of looking left / right / ahead / back, and for the pyramid, the lake and the hanging towers whether a ray from his eye
    reaches them (not stopped by the wagon, the car, Misato or the voxel world)."""
    import importlib
    os.makedirs(out_dir, exist_ok=True)
    r = ctx.routes[route_name]
    rig = ctx.rigs[rig_name]
    probe = ctx.probe("geofront")
    world = World(probe)
    gm = importlib.import_module("sets.geofront")
    g = probe.built
    ox = probe.o[0]
    rev = getattr(rig, "reversed_car", False)
    boxes = car_boxes(rig.parts, rig.base_motion) + misato_boxes(rig.seats["driver"], rev)
    seat = rig.seats["passenger"]
    lines = []
    top = gm.LAND + 1
    halfs = [int(math.floor(gm.PYR_HALF - 0.875 * k)) for k in range(gm.PYR_H)]
    targets = {"pyramid": [], "lake": [], "towers": []}
    targets["pyramid"].append((ox + gm.PX + 0.5, top + gm.PYR_H + 1.5, gm.TZ + 0.5))
    for k in (6, 14, 22, 30):
        h = halfs[k]
        for off in (-12, 0, 12):
            targets["pyramid"].append((ox + gm.PX + 0.5 + off, top + k + 0.5, gm.TZ - h - 0.6))
            targets["pyramid"].append((ox + gm.PX - h - 0.6, top + k + 0.5, gm.TZ + 0.5 + off))
    lx, lz, la, lb = gm.LK
    for ax in np.linspace(-0.8, 0.8, 9):
        for az in np.linspace(-0.8, 0.8, 7):
            x_, z_ = lx + ax * la, lz + az * lb
            ix, iz = int(x_), int(z_)
            if g.q[ix, iz] < 0.8 and g.Hh[ix, iz] <= gm.WATER_Y - 1:
                targets["lake"].append((ox + x_, gm.WATER_Y + 1.0, z_))
    for i, (cx, cz, hx, hz) in enumerate(g.towers):
        L = g.tower_lengths[i]
        for fy in (0.1, 0.5, 0.9):
            targets["towers"].append((ox + cx + 0.5, gm.TOWER_Y - int(L * fy) + 0.5, cz + 0.5))
    for label, fr in (("wall_opens", r.marks["wall_opens"]), ("reveal", r.marks["reveal"]), ("reveal_plus_2s", min(r.end, r.marks["reveal"] + 40))):
        pose = r.frames[fr]
        sc = Scene(boxes, world, pose)
        lines.append(f"{label} (frame {fr}, rig at x {pose[0]:.1f} y {pose[1]:.1f} z {pose[2]:.1f}, yaw {pose[3]:.1f}):")
        for above in (1.5, 1.62, 1.8):
            eye = (seat[0], seat[1] + above, seat[2])
            ow = sc.origin + sc.M @ np.array(eye)
            res = {}
            blocked_by = {}
            for kind, pts in targets.items():
                seen = 0
                flags = []
                for p_ in pts:
                    p_ = np.array(p_, float)
                    dv = p_ - ow
                    dist = float(np.linalg.norm(dv))
                    dw = dv / dist
                    dm = (sc.M.T @ dw)[None, :]
                    tb, who, _ = hit_boxes(np.array(eye, float), dm, boxes)
                    if tb[0] < dist:
                        nm = boxes[who[0]].name
                        blocked_by[nm] = blocked_by.get(nm, 0) + 1
                        flags.append(False)
                        continue
                    tw, gid = world.march(ow, dw[None, :], tmax=dist + 1.0)
                    ok_ = (not np.isfinite(tw[0])) or tw[0] >= dist - 1.6
                    flags.append(bool(ok_))
                    seen += int(ok_)
                if kind == "towers":
                    # a tower counts as seen if one of its three aim points (top, middle, bottom) is
                    res["towers"] = (sum(1 for k in range(0, len(flags), 3) if any(flags[k:k + 3])), len(flags) // 3)
                else:
                    res[kind] = (seen, len(pts))
            lines.append(f"   eye {above:.2f}: pyramid {res['pyramid'][0]}/{res['pyramid'][1]} sight lines clear, lake {res['lake'][0]}/{res['lake'][1]} clear, hanging towers {res['towers'][0]}/{res['towers'][1]} seen (one of three aim points)"
                         + (f"; blocked by the car/wagon: {blocked_by}" if blocked_by else "; none blocked by the car, wagon or Misato"))
        eye = (seat[0], seat[1] + 1.62, seat[2])
        for name, yaw in (("ahead", 180), ("out_of_the_window", 0 - 90 * 0), ("left", 90), ("right", -90), ("back", 0)):
            pass
        # the passenger's own directions: he faces backward on the wagon when the car is reversed
        face = 180.0 if rev else 0.0
        for name, dy in (("ahead", 0), ("window", 90 if not rev else 90), ("back", 180), ("other_side", -90)):
            yaw = face + dy
            img, rr = sc.render(eye, yaw, 4, 100.0, 200)
            save(img, os.path.join(out_dir, f"wagon_{label}_{name}.png"), f"{label}: the passenger looks {name} (rig yaw {yaw:.0f}, eye {eye[1]:.2f})", 2)
            tb, who = rr["t_box"], rr["who"]
            opaque = np.mean([(boxes[k].kind != "glass") for k in who if k >= 0]) if (who >= 0).any() else 0
            frac_rig = float((who >= 0).mean())
            lines.append(f"      look {name:11s}: car/wagon/Misato cover {100 * frac_rig:4.1f} % of a 100-degree frame")
    return lines


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["car", "wagon", "old"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "ride_view"))
    a = ap.parse_args()
    if a.what == "car":
        for l in report_car(a.out):
            print(l)
    elif a.what == "wagon":
        import build_story
        build_story.ONLY[:] = [1, 2, 3]
        ctx, out, summary = build_story.build(False, os.path.join(os.environ.get("TEMP", "."), "ang_ride_view_build"), warn=lambda m: None)
        for l in wagon_report(ctx, a.out):
            print(l)
    else:
        import ride_view_old
        for l in ride_view_old.numbers()[0]:
            print(l)

