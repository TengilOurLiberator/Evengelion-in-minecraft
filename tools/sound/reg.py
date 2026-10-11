"""reg.py - the sound registry.  A sound is a function  fn(r) -> audio  (r = numpy Generator seeded from the name),
registered with @sound("sfx.card", peak=-3, ...).  Audio is (n,) mono or (n,2) stereo float; fn may return
(audio, {"marker": value}) to put extra facts in the manifest."""
import zlib

REG = {}

# events that are not a file of their own: event -> list of sound names to pick from at random
GROUPS = {
    "sfx.bolt": ["sfx.bolt_1", "sfx.bolt_2", "sfx.bolt_3"],
}

DEFAULTS = {
    "amb": dict(stereo=True, loop=True, stream=True, q=4, atten=16, limit=False),
    "music": dict(stereo=True, loop=False, stream=True, q=5, atten=16, limit=False),
    "sfx": dict(stereo=False, loop=False, stream=False, q=6, atten=16, limit=True),
}


class Spec:
    def __init__(self, name, fn, **kw):
        self.name = name
        self.kind = name.split(".", 1)[0]
        self.short = name.split(".", 1)[1]
        self.fn = fn
        d = dict(DEFAULTS[self.kind])
        d.update(dict(lufs=None, peak=None, fin=None, fout=None, note="", expect=None, raw=False, ceiling=None))
        d.update(kw)
        self.__dict__.update(d)
        if self.lufs is None and self.peak is None and not self.raw:
            raise ValueError(f"{name}: needs lufs=, peak= or raw=True")

    @property
    def seed(self):
        return zlib.crc32(self.name.encode()) & 0xFFFFFFFF


def sound(name, **kw):
    def deco(fn):
        if name in REG:
            raise ValueError("duplicate sound " + name)
        REG[name] = Spec(name, fn, **kw)
        return fn
    return deco
