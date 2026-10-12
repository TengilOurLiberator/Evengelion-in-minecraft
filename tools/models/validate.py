"""Validate the pack's item models against what 26.3 accepts:  python -m models.validate [--pack DIR]

Checks every assets/angel/models/item/*.json: valid JSON, an item definition that points at it, element from/to inside -16..32 (a model's elements fit a
3-block box around its centre), from <= to, rotation fields (origin + either axis/angle or x/y/z: free angles, no 22.5 degree restriction in 26.3), faces
among the six, a uv of four numbers inside 0..16 with a positive area, texture references that are defined and whose PNG exists, light_emission 0..15.
Also that every part of every vehicle fits a 48-unit box after the geometry is built (the same rule seen from the python side)."""
import argparse
import sys

from . import mdl


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=mdl.PACK_ROOT)
    a = ap.parse_args(argv)
    errs, warns, stats = mdl.validate_pack(a.pack)
    print(f"models {stats['models']}, elements {stats['elements']}, faces {stats['faces']}, rotated elements {stats['rotated']}")
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("warn", w)
    print(f"{len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
