"""The standard review set: python -m models.final_shots [--out DIR]
car from outside (three-quarter front and rear, side, top) and from the passenger's eye (forward, toward the driver, down at the dashboard, out to the left
side, the door card), the VTOL, its wreck and the wagon."""
import argparse
import os

import numpy as np

from . import preview
from .shots import car_instances, vtol_instances, wagon_instances


def shot(inst, out, name, eye, at=None, yp=None, fov=50.0, hfov=False, size=(960, 600), ss=2, up=(0, 1, 0), ground=True, shadow=(-1.9, 1.9, -3.5, 3.5), label=None):
    cam = preview.Camera(eye, target=at, yaw_pitch=yp, fov=fov, aspect=size[0] / size[1], fov_is_horizontal=hfov, up=up)
    img = preview.render(inst, cam, size, ss=ss, ground=ground, shadow=shadow, sky=((135, 175, 225), (215, 228, 242)))
    p = os.path.join(out, name + ".png")
    preview.save(img, p, label or name)
    print(p)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "work", "shots", "models", "final")))
    ap.add_argument("--ss", type=int, default=2)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    car = car_instances()
    eye = (0.72, 1.79, -0.12)
    shot(car, a.out, "car_ext_front34", (5.4, 2.4, 6.0), at=(0, 0.55, 0.3), fov=52, ss=a.ss)
    shot(car, a.out, "car_ext_rear34", (-5.2, 2.6, -6.4), at=(0.2, 0.55, -0.6), fov=52, ss=a.ss)
    shot(car, a.out, "car_ext_side", (8.0, 1.5, 0.4), at=(0, 0.6, 0.0), fov=44, size=(1100, 520), ss=a.ss)
    shot(car, a.out, "car_ext_top", (0.01, 11.5, 0.0), at=(0, 0, 0), fov=44, up=(0, 0, 1), size=(700, 780), ss=a.ss)
    shot(car, a.out, "car_eye_forward", eye, yp=(0, 0), fov=100, hfov=True, ss=a.ss)
    shot(car, a.out, "car_eye_driver", eye, yp=(-62, -4), fov=90, hfov=True, ss=a.ss)
    shot(car, a.out, "car_eye_dash", eye, yp=(-8, -48), fov=90, hfov=True, ss=a.ss)
    shot(car, a.out, "car_eye_left", eye, yp=(90, -6), fov=100, hfov=True, ss=a.ss)
    shot(car, a.out, "car_eye_left_down", eye, yp=(80, -38), fov=100, hfov=True, ss=a.ss)
    shot(car, a.out, "car_eye_dials", (0.72, 1.55, -0.5), yp=(-22, -30), fov=80, hfov=True, ss=a.ss)
    shot(car_instances(-62.0), a.out, "car_ext_door_open", (5.5, 2.0, 4.5), at=(1.2, 0.5, 0.4), fov=50, ss=a.ss)
    v = vtol_instances(3.2)
    shot(v, a.out, "vtol_front34", (14, 6, 16), at=(0, 0, 0), fov=40, ss=a.ss, ground=False)
    shot(v, a.out, "vtol_rear34", (-14, 9, -16), at=(0, 0, 0), fov=40, ss=a.ss, ground=False)
    shot(v, a.out, "vtol_below", (-9, -4, 12), at=(0, 0, 0), fov=42, ss=a.ss, ground=False)
    shot(v, a.out, "vtol_far", (60, 22, 70), at=(0, 0, 0), fov=28, ss=a.ss, ground=False)
    shot(wagon_instances(True, "R"), a.out, "wagon_34", (-9, 5, -11), at=(0, -0.3, 0), fov=48, ss=a.ss, shadow=(-3, 3, -5, 5))
    shot(wagon_instances(False, "R"), a.out, "wagon_below", (8, -1.5, -6), at=(0, -0.5, 0), fov=50, ss=a.ss, shadow=None)
    return 0


if __name__ == "__main__":
    main()
