"""Motion planning: smooth paths, speed profiles, and the per-tick frames the movers play.

A route is a list of LEGS; each leg is a polyline driven from rest to rest (or to a stop at a station).  A leg becomes a list of
frames, one per tick: (x, y, z, yaw, pitch).  Frames are played by a tiny tick function (see movers.py), so everything is exact,
repeatable and checkable offline: the simulator and the voxel check look at the very same frames the server plays.
"""
import math

import numpy as np

from core import TPS, angdiff, dir_to_yaw


# --------------------------------------------------------------------------------------------------- polylines
def line(a, b, step=0.5):
    a, b = np.array(a, float), np.array(b, float)
    n = max(2, int(np.linalg.norm(b - a) / step) + 1)
    return [tuple(a + (b - a) * i / (n - 1)) for i in range(n)]


def arc(cx, cz, r, a0, a1, y, step=0.5):
    """Points on a circle (centre cx, cz; angles in degrees measured like atan2(dz, dx)); y constant or (y0, y1)."""
    n = max(3, int(abs(math.radians(a1 - a0)) * r / step) + 1)
    y0, y1 = (y, y) if not isinstance(y, (tuple, list)) else y
    out = []
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(a0 + (a1 - a0) * t)
        out.append((cx + r * math.cos(a), y0 + (y1 - y0) * t, cz + r * math.sin(a)))
    return out


def catmull(points, step=0.5):
    """Catmull-Rom through (x, y, z) points, sampled about every `step` blocks."""
    P = np.array(points, float)
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        n = max(2, int(np.hypot(p2[0] - p1[0], p2[2] - p1[2]) / step))
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    out.append(tuple(P[-1]))
    return out


def join(*parts):
    """concatenate polylines, dropping a duplicated joint"""
    out = []
    for p in parts:
        p = list(p)
        if out and p and np.allclose(out[-1], p[0], atol=1e-6):
            p = p[1:]
        out += p
    return out


class Path:
    """A polyline parametrised by arc length (horizontal distance is used for the heading, 3-D for the length)."""

    def __init__(self, pts):
        self.p = np.array(pts, float)
        d = np.linalg.norm(np.diff(self.p, axis=0), axis=1)
        keep = np.concatenate([[True], d > 1e-9])
        self.p = self.p[keep]
        d = np.linalg.norm(np.diff(self.p, axis=0), axis=1)
        self.s = np.concatenate([[0.0], np.cumsum(d)])
        self.L = float(self.s[-1])

    def pos(self, s):
        s = min(max(s, 0.0), self.L)
        return tuple(np.array([np.interp(s, self.s, self.p[:, k]) for k in range(3)]))

    def heading(self, s, half=1.5):
        a, b = self.pos(s - half), self.pos(s + half)
        dx, dz = b[0] - a[0], b[2] - a[2]
        if abs(dx) + abs(dz) < 1e-9:
            a, b = self.pos(s - 3 * half), self.pos(s + 3 * half)
            dx, dz = b[0] - a[0], b[2] - a[2]
        return dir_to_yaw(dx, dz)

    def pitch(self, s, half=2.0):
        a, b = self.pos(s - half), self.pos(s + half)
        h = math.hypot(b[0] - a[0], b[2] - a[2])
        return math.degrees(math.atan2(-(b[1] - a[1]), max(h, 1e-6)))     # + = nose down

    def curvature(self, s, half=2.0):
        a0, a1 = self.heading(s - half), self.heading(s + half)
        return abs(math.radians(angdiff(a1, a0))) / (2 * half)


# --------------------------------------------------------------------------------------------------- speed profile
def speed_profile(path, vmax, a_acc, a_dec, a_lat=2.0, v0=0.0, v1=0.0, vcap=None, ds=0.1):
    """Returns (s_samples, v_samples): the highest speed along the path that respects the cap, the lateral acceleration limit,
    and the acceleration / braking limits, starting at v0 and ending at v1."""
    n = int(path.L / ds) + 1
    ss = np.linspace(0.0, path.L, n)
    v = np.full(n, float(vmax))
    for i, s in enumerate(ss):
        k = path.curvature(s)
        if k > 1e-4:
            v[i] = min(v[i], math.sqrt(a_lat / k))
        if vcap is not None:
            v[i] = min(v[i], vcap(s))
    v[0] = min(v[0], v0)
    v[-1] = min(v[-1], v1)
    for i in range(1, n):
        v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * a_acc * ds))
    for i in range(n - 2, -1, -1):
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * a_dec * ds))
    return ss, v


def time_of_distance(ss, v):
    t = np.zeros(len(ss))
    for i in range(1, len(ss)):
        vm = 0.5 * (v[i] + v[i - 1])
        t[i] = t[i - 1] + (ss[i] - ss[i - 1]) / max(vm, 0.05)
    return t


def leg_frames(path, vmax, a_acc=1.0, a_dec=1.4, a_lat=2.2, v0=0.0, v1=0.0, vcap=None, smooth=0.5, hold_end=0, yaw_fn=None,
               pitch_fn=None, yaw_half=1.5, pitch_half=2.0, yaw_end=None):
    """Frames (one per tick) driving `path` from speed v0 to v1.  The distance-over-time curve is softened by a box filter of
    `smooth` seconds (removes the corners of the acceleration steps: jerk-limited, which is what a rider's stomach notices).
    Returns (frames, s_of_frame): frames are (x, y, z, yaw, pitch)."""
    ss, v = speed_profile(path, vmax, a_acc, a_dec, a_lat, v0, v1, vcap)
    t = time_of_distance(ss, v)
    total = float(t[-1])
    nt = int(math.ceil(total * TPS)) + 1
    tt = np.arange(nt) / TPS
    s_t = np.interp(tt, t, ss)
    w = max(1, int(smooth * TPS))
    if w > 1:
        # a centred box filter over `w` ticks; the ends are extended by odd reflection, which keeps a constant-speed start (or end) exactly
        # straight and a standing start (or end) exactly where it is
        pad = np.pad(s_t, w, mode="reflect", reflect_type="odd")
        s_f = np.convolve(pad, np.ones(w) / w, mode="same")[w:-w]
        s_f = np.maximum.accumulate(s_f) - s_f[0]
        s_f = np.clip(s_f * (path.L / s_f[-1]), 0.0, path.L)       # a hair of scaling so that the last frame lands exactly on the end
        s_t = s_f
    frames = []
    ys = []
    for i, s in enumerate(s_t):
        x, y, z = path.pos(float(s))
        yaw = path.heading(float(s), yaw_half)
        pitch = path.pitch(float(s), pitch_half)
        if yaw_fn:
            yaw = yaw_fn(i / TPS, yaw)
        if pitch_fn:
            pitch = pitch_fn(i / TPS, pitch)
        frames.append([x, y, z, yaw, pitch])
        ys.append(float(s))
    if yaw_end:
        target, sec = yaw_end
        nb = max(2, int(sec * TPS))
        for i in range(max(0, len(frames) - nb), len(frames)):
            u = (i - (len(frames) - nb)) / (nb - 1)
            k = u * u * (3 - 2 * u)
            frames[i][3] = frames[i][3] + angdiff(target, frames[i][3]) * k
    # unwrap yaw so that interpolation on the client never takes the long way round, and ease yaw/pitch (the polyline's heading has steps)
    yaws = np.unwrap(np.radians([f[3] for f in frames]))
    yaws = np.degrees(yaws)
    pitches = np.array([f[4] for f in frames])
    k = 5
    if len(yaws) > 2 * k:
        yk = np.pad(yaws, k, mode="edge")
        pk = np.pad(pitches, k, mode="edge")
        ker = np.ones(2 * k + 1) / (2 * k + 1)
        yaws = np.convolve(yk, ker, mode="valid")
        pitches = np.convolve(pk, ker, mode="valid")
    for f, yw, pt in zip(frames, yaws, pitches):
        f[3] = ((yw + 180.0) % 360.0) - 180.0
        f[4] = float(pt)
    frames = [tuple(f) for f in frames]
    frames += [frames[-1]] * hold_end
    return frames, ys


def static_frames(pose, ticks):
    return [tuple(pose)] * ticks


def pose_at(frames, i):
    return frames[min(max(i, 0), len(frames) - 1)]


def nearest_s(path, x, z, step=0.25):
    """arc length of the path point nearest to (x, z)"""
    best, bs = 1e18, 0.0
    s = 0.0
    while s <= path.L:
        p = path.pos(s)
        d = (p[0] - x) ** 2 + (p[2] - z) ** 2
        if d < best:
            best, bs = d, s
        s += step
    return bs, math.sqrt(best)
