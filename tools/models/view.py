"""One custom view of a vehicle: python -m models.view car --eye 6 3 7 --at 0 .6 0 --fov 50 --out file.png [--size 800 500] [--ss 2] [--door DEG] [--only part,part]"""
import argparse
import os

import numpy as np

from . import preview
from .shots import car_instances, vtol_instances, wagon_instances


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("what", default="car", choices=["car", "vtol", "wagon", "wagon_nr"])
    ap.add_argument("--eye", nargs=3, type=float, required=True)
    ap.add_argument("--at", nargs=3, type=float, default=None)
    ap.add_argument("--yp", nargs=2, type=float, default=None, help="yaw pitch instead of --at (yaw to the left)")
    ap.add_argument("--fov", type=float, default=50.0)
    ap.add_argument("--hfov", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", nargs=2, type=int, default=[800, 520])
    ap.add_argument("--ss", type=int, default=2)
    ap.add_argument("--door", type=float, default=0.0)
    ap.add_argument("--roll", type=float, default=0.0, help="degrees about the lower right edge: 90 = lying on its right side")
    ap.add_argument("--only", default="")
    ap.add_argument("--hide", default="")
    ap.add_argument("--ambient", type=float, default=0.42)
    ap.add_argument("--noground", action="store_true")
    ap.add_argument("--up", nargs=3, type=float, default=[0, 1, 0])
    a = ap.parse_args(argv)
    inst = {"car": lambda: car_instances(a.door), "vtol": lambda: vtol_instances(3.2), "wagon": lambda: wagon_instances(True, "R"),
            "wagon_nr": lambda: wagon_instances(False, "R")}[a.what]()
    if a.roll:
        # the side-lying pose (models.roll_motion): rotated about the lower right edge, every part
        from .vmath import rax
        for i in inst:
            i.motion = (rax("z", a.roll), np.array([-1.84, 0.0, 0.0]), np.zeros(3))
    if a.only:
        keep = set(a.only.split(","))
        inst = [i for i in inst if i.name in keep]
    if a.hide:
        hid = set(a.hide.split(","))
        inst = [i for i in inst if i.name not in hid]
    cam = preview.Camera(a.eye, target=a.at, yaw_pitch=a.yp, fov=a.fov, aspect=a.size[0] / a.size[1], fov_is_horizontal=a.hfov, up=tuple(a.up))
    img = preview.render(inst, cam, tuple(a.size), ss=a.ss, shadow=(-1.9, 1.9, -3.5, 3.5), ambient=a.ambient, ground=not a.noground)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    preview.save(img, a.out, None)
    print(a.out)


if __name__ == "__main__":
    main()
