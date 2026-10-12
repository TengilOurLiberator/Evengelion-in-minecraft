"""The first car (a closed blue coupe, 4 wide, 7 long, roof at 2.06), kept only so that ride_view.py can give the before / after numbers.
Nothing in the story uses it.  python ride_view_old.py [--out DIR]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from core import qaxis                                              # noqa: E402
from models import Part                                             # noqa: E402
import ride_view as rv                                              # noqa: E402

BODY = "blue_concrete"
OLD_PASSENGER = (0.5, 0.0, 0.0)
OLD_DRIVER = (-0.5, 0.0, 0.0)


def old_car_parts():
    P_ = Part
    return [
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
        P_("wheel", "black_concrete", (-0.85, 0.9, 0.55), (-0.15, 0.96, 1.15), rot=qaxis("x", -25), pivot=(-0.5, 0.93, 0.85)),
        P_("doorL", BODY, (1.85, 0.15, -1.5), (2.0, 1.0, 0.5), group="door"),
        P_("doorGlass", "light_blue_stained_glass", (1.9, 1.0, -1.4), (2.0, 1.9, 0.4), group="door"),
    ]


def numbers():
    parts = old_car_parts()
    boxes = rv.car_boxes(parts) + rv.misato_boxes(OLD_DRIVER)
    sc = rv.Scene(boxes, ground=(70, 70, 74))
    out = []
    for label, above in (("low", 1.5), ("flat", 1.62), ("tall", 1.8)):
        eye = rv.eye_of(OLD_PASSENGER, above)
        o = rv.obstruction(sc, eye, 0, 0, 100, 160)
        out.append(f"  old coupe, eye {label:4s} ({above:.2f} above the feet): forward 100x100 frame: opaque {100 * o['car']:5.1f} %  Misato {100 * o['misato']:4.1f} %  "
                   f"(glass {100 * o['glass']:4.1f} %)  clear {100 * o['clear']:5.1f} % ; with the glass counted as an obstruction: clear {100 * (o['clear'] - o['glass']):5.1f} %")
        azs, el = rv.horizon_sweep(sc, eye, (-80, 80), "car")
        out.append(f"      highest opaque car part in the forward 160 degrees: {el.max():+5.1f} deg above the horizon")
    return out, sc, rv.eye_of(OLD_PASSENGER, 1.62)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "ride_view"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lines, sc, eye = numbers()
    for l in lines:
        print(l)
    for name, yaw, pitch in (("forward", 0, 0), ("left", 90, 0), ("right", -90, 0), ("up", 0, 80)):
        img, r = sc.render(eye, yaw, pitch, 100.0, 240)
        rv.save(rv.cross(img), os.path.join(a.out, f"old_{name}.png"), f"OLD coupe {name} yaw {yaw} pitch {pitch}")
