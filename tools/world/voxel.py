"""The block canvas every set is built on.

A set module (tools/world/sets/<name>.py) exposes build(w) and draws into a World
using coordinates local to the set: x east, y up, z south, (0, 0, 0) the set's lowest
north-west corner. The compiler turns the finished canvas into the datapack.
"""
import numpy as np

AIR = "minecraft:air"


class World:
    def __init__(self, name, origin, size):
        self.name = name
        self.origin = tuple(origin)
        self.size = tuple(size)
        # [x, y, z]; 0 is "untouched" (left as the void world has it), 1 is air set on purpose
        self.a = np.zeros(self.size, dtype=np.uint16)
        self.palette = [None, AIR]
        self._ix = {AIR: 1}
        self.anchors = {}
        self.commands = []

    def _id(self, block):
        if ":" not in block:
            block = "minecraft:" + block
        i = self._ix.get(block)
        if i is None:
            i = self._ix[block] = len(self.palette)
            self.palette.append(block)
        return i

    def inside(self, x, y, z):
        return 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]

    def set(self, x, y, z, block):
        """One block; block may carry a state, e.g. 'oak_stairs[facing=east]'. Out of bounds is ignored."""
        if self.inside(x, y, z):
            self.a[x, y, z] = self._id(block)

    def fill(self, x1, y1, z1, x2, y2, z2, block):
        """A solid box, corners inclusive, clipped to the set."""
        lo = [max(0, min(p, q)) for p, q in ((x1, x2), (y1, y2), (z1, z2))]
        hi = [min(s, max(p, q) + 1) for s, p, q in zip(self.size, (x1, y1, z1), (x2, y2, z2))]
        if all(l < h for l, h in zip(lo, hi)):
            self.a[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] = self._id(block)

    def get(self, x, y, z):
        """The block at a position, or None where nothing has been drawn."""
        return self.palette[self.a[x, y, z]] if self.inside(x, y, z) else None

    def abs(self, x, y, z):
        """Local to world coordinates."""
        return (self.origin[0] + x, self.origin[1] + y, self.origin[2] + z)

    def anchor(self, name, x, y, z, yaw=0.0, pitch=0.0):
        """A named place the story uses: where the player stands, where a character waits, a trigger."""
        ax, ay, az = self.abs(x, y, z)
        self.anchors[name] = {"x": ax, "y": ay, "z": az, "yaw": yaw, "pitch": pitch}

    def command(self, text):
        """A command to run once the blocks are placed (signs, item frames, light). World coordinates; use abs()."""
        self.commands.append(text)


_TINT = (
    ("water", (60, 100, 220)), ("lava", (240, 110, 20)), ("grass", (95, 160, 70)), ("leaves", (50, 120, 50)),
    ("dirt", (130, 95, 65)), ("sand", (220, 210, 160)), ("glass", (190, 225, 235)), ("red", (190, 50, 45)),
    ("orange", (225, 130, 40)), ("yellow", (230, 205, 70)), ("purple", (125, 65, 170)), ("green", (85, 150, 60)),
    ("blue", (55, 80, 190)), ("white", (235, 235, 235)), ("black", (30, 30, 34)), ("light_gray", (160, 160, 160)),
    ("gray", (90, 90, 95)), ("iron", (205, 205, 205)), ("quartz", (235, 230, 222)), ("deepslate", (70, 70, 76)),
    ("log", (105, 80, 50)), ("planks", (165, 130, 80)), ("concrete", (150, 150, 150)), ("stone", (125, 125, 125)),
)


def _color(block):
    for key, rgb in _TINT:
        if key in block:
            return rgb
    return (200, 80, 200)


def preview(w, path, axis="y", at=None):
    """Save a picture of the set to check it by eye: axis 'y' looks down from above (or from height `at`),
    'x' and 'z' cut a vertical slice at coordinate `at` (default the middle)."""
    from PIL import Image
    sx, sy, sz = w.size
    solid = w.a > 1
    rgb = np.array([(0, 0, 0), (0, 0, 0)] + [_color(b) for b in w.palette[2:]], dtype=np.float32)
    if axis == "y":
        top = sy if at is None else at + 1
        col = solid[:, :top, :]
        h = top - 1 - np.argmax(col[:, ::-1, :], axis=1)
        ids = np.take_along_axis(w.a[:, :top, :], h[:, None, :], axis=1)[:, 0, :]
        shade = (0.55 + 0.45 * h / max(1, sy - 1))[..., None]
        img = np.where(col.any(axis=1)[..., None], rgb[ids] * shade, 0).transpose(1, 0, 2)
    else:
        cut = (w.size[0] if axis == "x" else sz) // 2 if at is None else at
        ids = w.a[cut, :, :] if axis == "x" else w.a[:, :, cut]
        img = rgb[ids][:, ::-1].transpose(1, 0, 2) if axis == "z" else rgb[ids][::-1]
    scale = max(1, 900 // max(img.shape[:2]))
    Image.fromarray(img.astype(np.uint8)).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path)
