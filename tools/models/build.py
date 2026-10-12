"""Paint every texture and write every model + item definition of the vehicles into the resource pack, then validate.

    cd D:\\angel-attack\\tools
    D:\\voice-assistant\\.venv\\Scripts\\python.exe -m models.build [car|wagon|vtol|all] [--pack DIR]
"""
import argparse
import os
import sys
import time

from . import mdl


def vehicles(which):
    out = []
    if which in ("car", "all"):
        from . import car
        out.append(car.build_car())
    if which in ("wagon", "all"):
        from . import wagon
        out.append(wagon.build_wagon())
    if which in ("vtol", "all"):
        from . import vtol
        out.append(vtol.build_vtol())
    return out


def write_vehicle(v, pack_root=mdl.PACK_ROOT, quiet=False):
    tdir = os.path.join(pack_root, "assets", "angel", "textures", "item")
    os.makedirs(tdir, exist_ok=True)
    t0 = time.time()
    # remove what an earlier build of this vehicle left (renamed or dropped models must not linger in the pack)
    for sub, ext in (("models/item", ".json"), ("items", ".json"), ("textures/item", ".png")):
        d = os.path.join(pack_root, "assets", "angel", *sub.split("/"))
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.startswith(v.name + "_") and f.endswith(ext):
                    os.remove(os.path.join(d, f))
    for s in v.sheets:
        s.pack()
        s.save(os.path.join(tdir, s.name + ".png"))
        if not quiet:
            print(f"  {s.name}.png {s.W}x{s.H}  ({len(s.regions)} regions)")
    n = 0
    for m in v.models.values():
        m.write(pack_root)
        n += len(m.elems)
    if not quiet:
        print(f"{v.name}: {len(v.models)} models, {n} elements, {len(v.parts)} display parts  ({time.time() - t0:.1f}s)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?", default="all")
    ap.add_argument("--pack", default=mdl.PACK_ROOT)
    a = ap.parse_args(argv)
    vs = vehicles(a.which)
    for v in vs:
        write_vehicle(v, a.pack)
    errs, warns, stats = mdl.validate_pack(a.pack, None)
    print(f"validate: {stats}  errors {len(errs)}  warnings {len(warns)}")
    for e in errs[:40]:
        print("  ERROR", e)
    for w in warns[:20]:
        print("  warn", w)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
