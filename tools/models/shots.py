"""Preview renders of the vehicles from outside and from the passenger's eye (reads the written models and textures back).

    cd D:\\angel-attack\\tools
    python -m models.shots car [--out DIR] [--ss 2] [--only exterior|cockpit|wheel]
"""
import argparse
import os
import sys

import numpy as np

from . import mdl, preview
from .vmath import look_matrix, rax


def instances(v, scale=1.0, door_deg=0.0, parts=None):
    inst = []
    for p in (parts if parts is not None else v.parts):
        m = v.models[p.model.name]
        s = p.scale * scale
        c = np.array(p.at, float) * scale if p.at is not None else np.array(m.center, float) * scale
        R = np.eye(3) if p.R is None else p.R
        motion = None
        if door_deg and p.group == "door":
            motion = (rax("y", door_deg), np.array([1.5, 0.0, 1.0]), np.zeros(3))
        inst.append(preview.Instance(m.name, t=c, R=R, s=s, motion=motion, name=p.name))
    return inst


def car_instances(door_deg=0.0):
    from . import car
    return instances(car.build_car(), 1.0, door_deg)


def vtol_instances(scale=3.2):
    from . import vtol
    return instances(vtol.build_vtol(), scale)


def wagon_instances(ramp=True, low_side="R"):
    from . import wagon
    v = wagon.build_wagon()
    return instances(v, 1.0, 0.0, wagon.parts_for(v, ramp, low_side))


def outside_views(inst, outdir, tag, ss=2, size=(560, 400), shadow=(-1.9, 1.9, -3.5, 3.5), centre=(0, 0.6, 0), views=None):
    views = views or {
        "front34": ((6.0, 3.2, 7.5), 52),
        "rear34": ((-6.2, 3.4, -7.5), 52),
        "side": ((12.0, 2.0, 0.0), 40),
        "top": ((0.01, 12.5, 0.0), 44),
        "front": ((0.0, 1.8, 11.0), 38),
        "back": ((0.0, 2.0, -11.0), 38),
    }
    paths = []
    for name, (eye, fov) in views.items():
        cam = preview.Camera(eye, target=centre, fov=fov, aspect=size[0] / size[1], up=(0, 0, 1) if name == "top" else (0, 1, 0))
        img = preview.render(inst, cam, size, ss=ss, shadow=shadow)
        p = os.path.join(outdir, f"{tag}_{name}.png")
        preview.save(img, p, f"{tag} {name}")
        paths.append(p)
    return paths


def eye_views(inst, outdir, tag, eye, ss=2, size=(560, 400), views=None):
    """From the passenger's eye: forward, toward the driver, down at the dashboard, out to the left."""
    views = views or {
        "forward": ((0, 0), 100),
        "driver": ((-62, -4), 90),
        "dash": ((-8, -48), 90),
        "left": ((90, -6), 100),
        "back": ((180, 5), 100),
        "down": ((0, -80), 100),
    }
    out = []
    for name, ((yaw, pitch), fov) in views.items():
        cam = preview.Camera(eye, yaw_pitch=(yaw, pitch), fov=fov, aspect=size[0] / size[1], fov_is_horizontal=True)
        img = preview.render(inst, cam, size, ss=ss, ground=True, sky=((135, 175, 225), (215, 228, 242)))
        p = os.path.join(outdir, f"{tag}_eye_{name}.png")
        preview.save(img, p, f"{tag} eye {name} yaw {yaw} pitch {pitch}")
        out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="?", default="car")
    ap.add_argument("--out", default=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "work", "shots", "models")))
    ap.add_argument("--ss", type=int, default=2)
    ap.add_argument("--only", default="")
    ap.add_argument("--door", type=float, default=0.0)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    if a.what == "car":
        inst = car_instances(a.door)
        if a.only in ("", "exterior"):
            for p in outside_views(inst, a.out, "car", a.ss):
                print(p)
        if a.only in ("", "cockpit"):
            from . import car
            eye = (car.SEAT_P[0], car.SEAT_P[1] + 1.62, car.SEAT_P[2])
            for p in eye_views(inst, a.out, "car", eye, a.ss):
                print(p)
        if a.only == "wheel":
            views = {"wheel": ((9.0, 0.5, 2.0), 20)}
            for p in outside_views(inst, a.out, "car", a.ss, centre=(1.64, 0.4, 2.0), views=views):
                print(p)


if __name__ == "__main__":
    main()
