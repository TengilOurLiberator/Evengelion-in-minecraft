"""Original 64x64 Minecraft player skins for the cast, drawn in code (pixel art with numpy/pillow).

    make_all() -> {id: (PIL image 64x64 RGBA, slim)}

The designs are our own renderings of plain role descriptions (see tools\\cast\\README.md). Every skin is drawn on
the modern 64x64 layout: base layer and the outer ("hat" / "jacket" / "sleeve" / "pants") layer, the arms either
4 pixels wide or, for the women and the girl, 3 pixels wide (the slim model; the datapack asks for it).

Drawing helpers: Skin.face(part, layer, face) is a view of one face as seen from outside (row 0 = top), and
Face.art() paints a face from a small ASCII picture. '.' in a picture leaves the pixel as it was.
"""
import random

import numpy as np
from PIL import Image

# ---------------------------------------------------------------- layout

PARTS = {                # name: (base uv, outer uv, width key, height, depth)
    "head": ((0, 0), (32, 0), "head", 8, 8),
    "body": ((16, 16), (16, 32), "body", 12, 4),
    "rarm": ((40, 16), (40, 32), "arm", 12, 4),
    "larm": ((32, 48), (48, 48), "arm", 12, 4),
    "rleg": ((0, 16), (0, 32), "leg", 12, 4),
    "lleg": ((16, 48), (0, 48), "leg", 12, 4),
}
FACES = ("top", "bottom", "right", "front", "left", "back")


def rgba(c):
    if c is None:
        return (0, 0, 0, 0)
    if isinstance(c, tuple):
        return c if len(c) == 4 else c + (255,)
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


def mix(a, b, t):
    a, b = rgba(a), rgba(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


def dark(c, t=0.2):
    return mix(c, (0, 0, 0), t)


def light(c, t=0.2):
    return mix(c, (255, 255, 255), t)


class Face:
    """One face of one box on the skin, seen from outside."""

    def __init__(self, arr, name):
        self.a, self.name = arr, name
        self.h, self.w = arr.shape[0], arr.shape[1]

    def fill(self, c, x0=0, x1=None, y0=0, y1=None):
        x1 = self.w if x1 is None else x1
        y1 = self.h if y1 is None else y1
        self.a[y0:y1, x0:x1] = rgba(c)
        return self

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = rgba(c)
        return self

    def get(self, x, y):
        return tuple(int(v) for v in self.a[y, x])

    def row(self, y, c, x0=0, x1=None):
        return self.fill(c, x0, x1, y, y + 1)

    def col(self, x, c, y0=0, y1=None):
        return self.fill(c, x, x + 1, y0, y1)

    def art(self, rows, legend, ox=0, oy=0):
        for j, line in enumerate(rows):
            for i, ch in enumerate(line):
                if ch == ".":
                    continue
                self.set(ox + i, oy + j, legend[ch])
        return self

    def noise(self, colors, density, seed, x0=0, x1=None, y0=0, y1=None):
        """Sprinkle pixels of the given colours (only where the face is already opaque)."""
        rnd = random.Random(seed)
        x1 = self.w if x1 is None else x1
        y1 = self.h if y1 is None else y1
        for y in range(y0, y1):
            for x in range(x0, x1):
                if self.a[y, x, 3] and rnd.random() < density:
                    self.a[y, x] = rgba(rnd.choice(colors))
        return self

    def streaks(self, base, lighter, darker, seed, x0=0, x1=None, y0=0, y1=None):
        """Hair: vertical strands of a lighter or darker tone on the base colour."""
        rnd = random.Random(seed)
        x1 = self.w if x1 is None else x1
        y1 = self.h if y1 is None else y1
        for x in range(x0, x1):
            y = y0
            while y < y1:
                run = rnd.choice((1, 2, 2, 3, 4))
                tone = rnd.choice((base, base, lighter, darker))
                for k in range(run):
                    if y + k < y1:
                        self.a[y + k, x] = rgba(tone)
                y += run
        return self

    def shade_edges(self, t=0.12):
        """Darken the outermost columns slightly (where opaque) to round the shape."""
        for x in (0, self.w - 1):
            for y in range(self.h):
                if self.a[y, x, 3]:
                    self.a[y, x, :3] = dark(tuple(self.a[y, x]), t)[:3]
        return self

    def darken_row(self, y, t=0.15, x0=0, x1=None):
        x1 = self.w if x1 is None else x1
        for x in range(x0, x1):
            if self.a[y, x, 3]:
                self.a[y, x, :3] = dark(tuple(self.a[y, x]), t)[:3]
        return self

    def copy_from(self, other, mask=None):
        for y in range(self.h):
            for x in range(self.w):
                px = tuple(int(v) for v in other.a[y, x])
                if px[3] and (mask is None or mask(px)):
                    self.a[y, x] = px
        return self


class Skin:
    def __init__(self, slim):
        self.a = np.zeros((64, 64, 4), np.uint8)
        self.slim = slim
        self.aw = 3 if slim else 4

    def dims(self, part):
        _, _, key, h, d = PARTS[part]
        w = {"head": 8, "body": 8, "arm": self.aw, "leg": 4}[key]
        return w, h, d

    def face(self, part, layer, face):
        base, outer, _, _, _ = PARTS[part]
        u0, v0 = outer if layer else base
        w, h, d = self.dims(part)
        rect = {"top": (u0 + d, v0, w, d), "bottom": (u0 + d + w, v0, w, d), "right": (u0, v0 + d, d, h),
                "front": (u0 + d, v0 + d, w, h), "left": (u0 + d + w, v0 + d, d, h),
                "back": (u0 + d + w + d, v0 + d, w, h)}[face]
        u, v, fw, fh = rect
        return Face(self.a[v:v + fh, u:u + fw], f"{part}.{layer}.{face}")

    def faces(self, part, layer, which=FACES):
        return [self.face(part, layer, f) for f in which]

    def fill_part(self, part, layer, c):
        for f in self.faces(part, layer):
            f.fill(c)

    def lift(self, part, mask, faces=FACES):
        """Copy base-layer pixels satisfying mask onto the outer layer (so hair, clothes and bandages stand off the body)."""
        for f in faces:
            self.face(part, 1, f).copy_from(self.face(part, 0, f), mask)

    def image(self):
        return Image.fromarray(self.a, "RGBA")


def band(skin, part, layer, y0, y1, c, faces=("right", "front", "left", "back"), top=False, bottom=False):
    for f in faces:
        skin.face(part, layer, f).fill(c, y0=y0, y1=y1)
    if top:
        skin.face(part, layer, "top").fill(c)
    if bottom:
        skin.face(part, layer, "bottom").fill(c)


def in_set(*colors):
    cs = [rgba(c) for c in colors]
    return lambda px: tuple(px) in cs


# ---------------------------------------------------------------- shared pieces

def base_body(skin, tone, shade):
    """Skin-coloured everything (the base layer under the clothes), with a little form shading."""
    for part in PARTS:
        skin.fill_part(part, 0, tone)
    for f in skin.faces("head", 0, ("bottom",)):
        f.fill(shade)
    for p in ("rarm", "larm", "rleg", "lleg"):
        skin.face(p, 0, "bottom").fill(shade)
        for side in ("left", "right"):
            skin.face(p, 0, side).fill(tone)
        skin.face(p, 0, "back").fill(tone)


# ---------------------------------------------------------------- MISATO

def misato():
    s = Skin(slim=True)
    skin_c, skin_s, skin_h = "#f1cdb0", "#d9aa8c", "#f9e0ca"
    hair, hair_d, hair_l = "#4a2a6c", "#2f1a49", "#74499f"
    red, red_d, red_l = "#c3242f", "#8b1826", "#e04a52"
    dress, dress_l = "#25212e", "#3a3447"
    boot, boot_l = "#17151c", "#34303c"
    base_body(s, skin_c, skin_s)
    lg = {"h": hair, "l": hair_l, "d": hair_d, "s": skin_c, "S": skin_s, "b": "#2c1a3d", "w": "#fbf8f8", "e": "#4a2c33",
          "n": skin_s, "m": "#c15f68", "H": skin_h}
    head = s.face("head", 0, "front")
    head.art(["hlhhdhlh",
              "hhdhhldh",
              "hhhssdhh",
              "hbbssbbh",
              "hwessewh",
              "hsssnsSh",
              "hssmmssh",
              "hSsssSsh"], lg)
    head.set(0, 7, hair); head.set(7, 7, hair)
    head.set(4, 2, skin_h); head.set(3, 2, skin_c)
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(hair).streaks(hair, hair_l, hair_d, 11 if face == "right" else 12)
        fc = 7 if face == "right" else 0
        for y in range(4, 8):
            f.set(fc, y, skin_c)
        f.set(fc, 7, skin_s)
        f.set(fc, 3, hair_d)
    s.face("head", 0, "back").fill(hair).streaks(hair, hair_l, hair_d, 13)
    t = s.face("head", 0, "top")
    t.fill(hair).streaks(hair, hair_l, hair_d, 14)
    t.col(3, hair_d); t.set(3, 5, hair_l); t.set(2, 2, hair_l); t.set(5, 3, hair_l)
    s.face("head", 0, "bottom").fill(hair_d)
    s.lift("head", lambda px: px[:3] in (rgba(hair)[:3], rgba(hair_l)[:3], rgba(hair_d)[:3]))
    # long hair falls behind the neck and over the shoulders (outer layer of the body)
    # torso: dress, short red jacket open at the front, a small silver cross on a chain
    body = s.face("body", 0, "front")
    body.art(["rjssssjr",
              "rrqssqrr",
              "rrqDDqrr",
              "rrqxxqrr",
              "rrqxDqrr",
              "rrqDDqrr",
              "qqqDDqqq",
              "DdDDDDdD",
              "DDDDDDDD",
              "DdDDDDdD",
              "DDDDDDDD",
              "dDDDDDDd"],
             {"r": red, "j": red_l, "s": skin_c, "q": red_d, "D": dress, "d": dress_l, "x": "#e8e8f2"})
    body.set(2, 1, red_d)
    body.set(3, 1, skin_c); body.set(4, 1, skin_c)
    body.set(3, 6, dress); body.set(4, 6, dress)
    bk = s.face("body", 0, "back")
    bk.fill(red, y1=7); bk.fill(dress, y0=7); bk.row(6, red_d); bk.col(3, red_d, 0, 6); bk.col(4, red_d, 0, 6)
    bk.noise([red_l, red_d], 0.08, 5, y1=6)
    for face in ("right", "left"):
        f = s.face("body", 0, face)
        f.fill(red, y1=7).fill(dress, y0=7).row(6, red_d)
        f.noise([red_l, red_d], 0.08, 6 if face == "right" else 7, y1=6)
    s.face("body", 0, "top").fill(red)
    s.face("body", 0, "bottom").fill(dress)
    # jacket on the outer layer (puffed edge), pendant on top
    s.lift("body", in_set(red, red_l, red_d, "#e8e8f2"), ("front", "back", "left", "right", "top"))
    # hair over the back and the front of the shoulders (outer layer)
    hb = s.face("body", 1, "back")
    for y in range(0, 10):
        x0, x1 = (0, 8) if y < 6 else (1 + (y - 6) // 2, 7 - (y - 6) // 2)
        for x in range(x0, x1):
            hb.set(x, y, hair)
    hb.streaks(hair, hair_l, hair_d, 21, y1=10)
    for y in range(10):
        for x in range(8):
            if hb.a[y, x, 3] == 0 or not (hb.get(x, y)[:3] in (rgba(hair)[:3], rgba(hair_l)[:3], rgba(hair_d)[:3])):
                continue
    hf = s.face("body", 1, "front")
    for y in range(0, 6):
        for x in (0, 1) if y < 4 else (0,):
            hf.set(x, y, hair if (x + y) % 3 else hair_d)
        for x in (6, 7) if y < 4 else (7,):
            hf.set(x, y, hair if (x + y) % 3 else hair_d)
    for face in ("right", "left"):
        f = s.face("body", 1, face)
        for y in range(0, 5):
            for x in range(4):
                f.set(x, y, hair if (x * 2 + y) % 3 else hair_l)
    s.face("body", 1, "top").fill(hair_d)
    # arms: short jacket sleeves, bare below (slim)
    for p in ("rarm", "larm"):
        band(s, p, 0, 0, 5, red, top=True)
        band(s, p, 1, 0, 5, red, top=True)
        for face in ("front", "back", "right", "left"):
            s.face(p, 0, face).row(4, red_d)
            s.face(p, 1, face).row(4, red_d)
            s.face(p, 1, face).noise([red_l, red_d], 0.1, 31, y1=4)
        for face in ("right", "left", "front", "back"):
            s.face(p, 0, face).row(11, skin_s)
        # silver bracelet
        for face in ("front", "back", "right", "left"):
            s.face(p, 0, face).row(9, "#c8c8d6")
    # legs: dark dress hem, bare skin, black ankle boots
    for p in ("rleg", "lleg"):
        band(s, p, 0, 0, 4, dress, top=True)
        band(s, p, 1, 0, 4, dress, top=True)
        band(s, p, 0, 9, 12, boot, bottom=True)
        for face in ("front", "back", "right", "left"):
            s.face(p, 1, face).row(3, dress_l)
            s.face(p, 0, face).row(9, boot_l)
            s.face(p, 0, face).row(7, skin_s)
        s.face(p, 0, "front").set(1, 8, skin_h)
    return s


# ---------------------------------------------------------------- RITSUKO

def ritsuko():
    s = Skin(slim=True)
    skin_c, skin_s, skin_h = "#f2d1b6", "#dab090", "#fae4d0"
    hair, hair_d, hair_l = "#e8cf7c", "#bd9f4c", "#f9eaa6"
    coat, coat_s, coat_d = "#f4f5fa", "#d4d9e6", "#b4bccf"
    blue, blue_d, blue_l = "#3e6fbe", "#2b4f93", "#5b8ad6"
    skirt, skirt_l = "#262a3e", "#363b54"
    tights, tights_l = "#2d2838", "#443d52"
    shoe = "#1a181f"
    base_body(s, skin_c, skin_s)
    lg = {"h": hair, "l": hair_l, "d": hair_d, "s": skin_c, "S": skin_s, "b": "#4a3224", "w": "#fdfafa", "e": "#3e3446",
          "n": skin_s, "m": "#c4636c", "o": "#7b4a3a"}
    head = s.face("head", 0, "front")
    head.art(["hlhhdhlh",
              "hhhdhhhh",
              "hhhhdssh",
              "hbbssbbh",
              "hwessewh",
              "hsssnoSh",
              "sssmmsss",
              "sSssssSs"], lg)
    head.set(1, 2, hair_d)
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(skin_c)
        f.fill(hair, 0, 8, 0, 6).streaks(hair, hair_l, hair_d, 41 if face == "right" else 42, 0, 8, 0, 6)
        fc = 7 if face == "right" else 0
        f.col(fc, skin_c, 3, 8)
        f.set(fc, 5, skin_s)
        ear = 4 if face == "right" else 3
        f.set(ear, 4, skin_c); f.set(ear, 3, skin_c); f.set(ear + (1 if face == "right" else -1), 4, skin_s)
        f.fill(hair, 0 if face == "right" else 5, 3 if face == "right" else 8, 6, 7)
    bk = s.face("head", 0, "back")
    bk.fill(skin_c).fill(hair, 0, 8, 0, 7).streaks(hair, hair_l, hair_d, 43, 0, 8, 0, 7)
    bk.row(7, skin_s)
    bk.row(6, hair_d)
    t = s.face("head", 0, "top")
    t.fill(hair).streaks(hair, hair_l, hair_d, 44)
    t.set(5, 6, hair_l); t.set(2, 2, hair_l)
    s.face("head", 0, "bottom").fill(skin_s)
    s.lift("head", in_set(hair, hair_l, hair_d))
    # torso: blue top, dark skirt, white lab coat hanging open
    body = s.face("body", 0, "front")
    body.art(["Bsssssb.",
              "bbbssbbb",
              "BbbBBbbB",
              "BbbBBbbB",
              "BbbBBbbB",
              "BbbBBbbB",
              "BbbBBbbB",
              "kkkkkkkk",
              "kKkkkkKk",
              "kkkkkkkk",
              "kKkkkkKk",
              "kkkkkkkk"],
             {"B": blue, "b": blue, "s": skin_c, "k": skirt, "K": skirt_l})
    body.set(0, 0, blue); body.set(7, 0, blue); body.set(3, 0, skin_c); body.set(4, 0, skin_c)
    for y in range(2, 7):
        body.set(3, y, blue_l if y % 2 else blue); body.set(4, y, blue_d)
    body.row(7, "#52587a", 0, 8)
    s.face("body", 0, "back").fill(blue, y1=7).fill(skirt, y0=7).row(7, "#52587a")
    for face in ("right", "left"):
        s.face("body", 0, face).fill(blue, y1=7).fill(skirt, y0=7)
    s.face("body", 0, "top").fill(blue)
    s.face("body", 0, "bottom").fill(skirt)
    # coat (outer layer): two panels in front, closed behind and at the sides
    cf = s.face("body", 1, "front")
    for y in range(12):
        for x in (0, 1, 2, 5, 6, 7):
            cf.set(x, y, coat if (x in (0, 1, 5, 6)) else coat_s)
    cf.col(2, coat_s); cf.col(5, coat_s)
    for x in (2, 5):
        cf.set(x, 0, coat_d); cf.set(x, 1, coat_d)
    cf.set(1, 0, coat_s); cf.set(6, 0, coat_s); cf.set(0, 0, coat_s); cf.set(7, 0, coat_s)
    cf.row(11, coat_s, 0, 3); cf.row(11, coat_s, 5, 8)
    for y in (4, 8):
        cf.set(2, y, coat_d); cf.set(5, y, coat_d)
    cf.noise([coat_s], 0.06, 51)
    for p, seedv in (("back", 52), ("right", 53), ("left", 54)):
        f = s.face("body", 1, p)
        f.fill(coat)
        f.noise([coat_s, coat_s, coat_d], 0.10, seedv)
        f.row(11, coat_s)
    bf = s.face("body", 1, "back")
    bf.col(3, coat_s, 5, 12); bf.col(4, coat_s, 5, 12); bf.col(3, coat_d, 9, 12)
    s.face("body", 1, "top").fill(coat)
    s.face("body", 1, "bottom").fill(coat_s)
    # arms: long coat sleeves with a blue cuff, hands bare
    for p in ("rarm", "larm"):
        band(s, p, 1, 0, 10, coat, top=True)
        for face in ("front", "back", "right", "left"):
            s.face(p, 1, face).noise([coat_s, coat_d], 0.10, 60, y1=10)
            s.face(p, 1, face).row(9, coat_s)
            s.face(p, 0, face).row(9, blue)
            s.face(p, 0, face).row(10, blue_d)
        s.face(p, 1, "front").set(0, 3, coat_s)
    # legs: dark tights, shoes, the coat's skirts over the thighs and knees
    for p in ("rleg", "lleg"):
        band(s, p, 0, 0, 10, tights, top=True)
        band(s, p, 0, 10, 12, shoe, bottom=True)
        for face in ("front", "back", "right", "left"):
            s.face(p, 0, face).noise([tights_l], 0.12, 71, y1=10)
            s.face(p, 0, face).row(10, "#2a2730")
        for face in ("back", "right", "left"):
            s.face(p, 1, face).fill(coat, y0=0, y1=7)
            s.face(p, 1, face).noise([coat_s], 0.12, 72, y1=7)
            s.face(p, 1, face).row(6, coat_s)
        s.face(p, 1, "front").fill(coat, x0=0 if p == "rleg" else 2, x1=2 if p == "rleg" else 4, y0=0, y1=7)
        s.face(p, 1, "front").row(6, coat_s, 0 if p == "rleg" else 2, 2 if p == "rleg" else 4)
        s.face(p, 1, "top").fill(coat)
    return s


# ---------------------------------------------------------------- GENDO

def gendo():
    s = Skin(slim=False)
    skin_c, skin_s, skin_h = "#dcb394", "#bd8f72", "#ebc8aa"
    hair, hair_g = "#1f1b1e", "#4d4a4c"
    beard, beard_l = "#2b2324", "#3d3233"
    coat, coat_l, coat_d = "#3a3344", "#4d4558", "#26212e"
    red, red_d = "#a91f2c", "#701622"
    glove, glove_s = "#f4f4f6", "#c9ccd6"
    shoe = "#141217"
    base_body(s, skin_c, skin_s)
    lg = {"h": hair, "g": hair_g, "s": skin_c, "S": skin_s, "b": "#1c1618", "a": beard, "A": beard_l, "f": "#2a1f1b",
          "o": "#f7a030", "O": "#d87b1c", "m": "#a37862", "n": skin_s}
    head = s.face("head", 0, "front")
    head.art(["hhhhhhhh",
              "hhhhhhhh",
              "hgsssshg",
              "sffssffs",
              "soOffOos",
              "assnnssa",
              "aasmmsaa",
              "aAaaaaAa"], lg)
    head.set(0, 2, hair); head.set(7, 2, hair)
    head.set(3, 5, beard); head.set(4, 5, beard)
    head.set(3, 2, skin_s); head.set(4, 2, skin_s)
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(skin_c)
        f.fill(hair, 0, 8, 0, 2)
        f.fill(hair, 0, 5 if face == "right" else 3, 2, 3) if face == "right" else f.fill(hair, 3, 8, 2, 3)
        f.fill(hair, 0, 3, 3, 5) if face == "right" else f.fill(hair, 5, 8, 3, 5)
        f.fill(hair, 0, 3, 5, 6) if face == "right" else f.fill(hair, 5, 8, 5, 6)
        fc = 7 if face == "right" else 0
        ear_x = 4 if face == "right" else 3
        f.set(ear_x, 4, skin_s); f.set(ear_x, 3, skin_c); f.set(ear_x + (1 if face == "right" else -1), 4, skin_s)
        for x in (range(5, 8) if face == "right" else range(0, 3)):
            f.set(x, 4, "#2a1f1b")                                   # the arm of the glasses
        for y in range(5, 8):
            for x in (range(4, 8) if face == "right" else range(0, 4)):
                f.set(x, y, beard if (x + y) % 4 else beard_l)
        f.set(fc, 3, skin_c)
        f.set(fc, 2, hair_g)
    bk = s.face("head", 0, "back")
    bk.fill(hair)
    bk.fill(skin_c, y0=6)
    bk.row(5, hair_g)
    bk.noise([hair_g], 0.08, 81, y1=5)
    t = s.face("head", 0, "top")
    t.fill(hair).noise([hair_g], 0.07, 82)
    s.face("head", 0, "bottom").fill(beard)
    s.lift("head", in_set(hair, hair_g))
    # hair stands off a little: top and back rows of the hat layer only (the face stays smooth)
    # uniform: dark jacket, high collar with a red accent, belt, white gloves
    body = s.face("body", 0, "front")
    body.art(["cRRRRRRc",
              "ccRRRRcc",
              "cccKKccc",
              "cLcKKcLc",
              "cccKKccc",
              "cLcKKcLc",
              "cccKKccc",
              "cLcKKcLc",
              "cccKKccc",
              "BBBBBBBB",
              "ttttttt t".replace(" ", ""),
              "tTttttTt"],
             {"c": coat, "R": red, "K": coat_d, "L": coat_l, "B": "#15121a", "t": "#26222e", "T": "#322d3b"})
    body.set(3, 9, "#c8c8d4"); body.set(4, 9, "#c8c8d4")
    body.set(0, 0, coat); body.set(7, 0, coat)
    body.set(3, 3, "#d4b150"); body.set(3, 5, "#d4b150"); body.set(3, 7, "#d4b150")
    bk = s.face("body", 0, "back")
    bk.fill(coat, y1=9).fill("#15121a", y0=9, y1=10).fill("#26222e", y0=10)
    bk.col(3, coat_d, 0, 9); bk.col(4, coat_d, 0, 9)
    bk.noise([coat_l, coat_d], 0.07, 91, y1=9)
    for face in ("right", "left"):
        f = s.face("body", 0, face)
        f.fill(coat, y1=9).fill("#15121a", y0=9, y1=10).fill("#26222e", y0=10)
        f.noise([coat_l, coat_d], 0.07, 92, y1=9)
    s.face("body", 0, "top").fill(coat)
    s.face("body", 0, "bottom").fill("#26222e")
    # outer layer: the stand-up collar (a ring around the neck, red inside) and the jacket's thickness
    o = s.face("body", 1, "front")
    o.fill(coat, y1=9)
    o.noise([coat_l], 0.06, 93, y1=9)
    o.art(["cRRRRRRc", "ccRRRRcc"], {"c": coat_l, "R": red})
    o.row(0, red, 1, 7)
    o.set(0, 0, coat_l); o.set(7, 0, coat_l)
    o.col(3, coat_d, 2, 9); o.col(4, coat_d, 2, 9)
    for y, x in ((3, 3), (5, 3), (7, 3)):
        o.set(x, y, "#d4b150")
    for fn in ("back", "right", "left"):
        f = s.face("body", 1, fn)
        f.fill(coat, y1=9).noise([coat_l, coat_d], 0.06, 94, y1=9)
        f.row(0, coat_l); f.row(1, coat_l)
    s.face("body", 1, "back").col(3, coat_d, 2, 9)
    s.face("body", 1, "back").col(4, coat_d, 2, 9)
    s.face("body", 1, "top").fill(coat_l)
    for p in ("rarm", "larm"):
        band(s, p, 0, 0, 9, coat, top=True)
        band(s, p, 0, 9, 12, glove, bottom=True)
        band(s, p, 1, 0, 9, coat, top=True)
        band(s, p, 1, 9, 12, glove)
        for face in ("front", "back", "right", "left"):
            s.face(p, 1, face).noise([coat_l, coat_d], 0.07, 95, y1=9)
            s.face(p, 1, face).row(8, coat_d)
            s.face(p, 1, face).row(9, glove_s)
            s.face(p, 1, face).row(11, glove_s)
            s.face(p, 0, face).row(9, glove_s)
        s.face(p, 1, "front").set(1, 10, glove_s); s.face(p, 1, "front").set(2, 10, glove_s)
    for p in ("rleg", "lleg"):
        band(s, p, 0, 0, 10, "#26222e", top=True)
        band(s, p, 0, 10, 12, shoe, bottom=True)
        for face in ("front", "back", "right", "left"):
            s.face(p, 0, face).noise(["#322d3b", "#1d1a24"], 0.1, 96, y1=10)
            s.face(p, 0, face).row(10, "#1b181f")
        s.face(p, 0, "front").col(1 if p == "rleg" else 2, "#322d3b", 0, 10)
        for face in ("front", "back", "right", "left"):
            s.face(p, 1, face).fill("#26222e", y0=0, y1=10)
            s.face(p, 1, face).noise(["#322d3b", "#1d1a24"], 0.1, 97, y1=10)
    return s


# ---------------------------------------------------------------- REI (hospital)

def _rei(hurt):
    s = Skin(slim=True)
    skin_c, skin_s, skin_h = "#f6e9e2", "#e1c9c6", "#fff6f0"
    hair, hair_d, hair_l = "#8fbbe0", "#628fba", "#bddaf2"
    lg = {"h": hair, "l": hair_l, "d": hair_d, "s": skin_c, "S": skin_s, "w": "#fcfcff", "e": "#d02a42", "E": "#8c1228",
          "n": skin_s, "m": "#dc9a9a"}
    base_body(s, skin_c, skin_s)
    head = s.face("head", 0, "front")
    head.art(["hlhhhhlh",
              "hhhdhhhh",
              "hhhssdhh",
              "hsssssSh",
              "heEssEeh",
              "hsssnsSh",
              "hssmmssh",
              "sSssssSs"], lg)
    head.set(3, 3, skin_c)
    head.set(1, 4, "#e03a52"); head.set(6, 4, "#e03a52")
    head.set(2, 4, "#7a0f26"); head.set(5, 4, "#7a0f26")
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(skin_c)
        f.fill(hair, 0, 8, 0, 6).streaks(hair, hair_l, hair_d, 101 if face == "right" else 102, 0, 8, 0, 6)
        fc = 7 if face == "right" else 0
        f.col(fc, hair, 0, 7)
        f.col(fc, skin_c, 3, 6)
        f.set(fc, 6, hair)
        f.set(4 if face == "right" else 3, 4, skin_s)
    bk = s.face("head", 0, "back")
    bk.fill(hair).streaks(hair, hair_l, hair_d, 103, 0, 8, 0, 6)
    bk.row(6, hair_d); bk.row(7, skin_s)
    t = s.face("head", 0, "top")
    t.fill(hair).streaks(hair, hair_l, hair_d, 104)
    t.set(5, 6, hair_l); t.set(2, 2, hair_l)
    s.face("head", 0, "bottom").fill(skin_s)
    s.lift("head", in_set(hair, hair_l, hair_d))
    if hurt:
        gauze, gauze_s, gauze_d = "#f1efe4", "#d4d0c0", "#b7b2a0"
        blood = "#a8423e"
        # the band around the head (one row, all sides), the pad over the right eye (viewer's left of the face)
        for fn in ("front", "back", "right", "left"):
            f = s.face("head", 1, fn)
            for x in range(8):
                f.set(x, 2, gauze if x % 3 else gauze_s)
        f = s.face("head", 1, "front")
        for y in range(3, 6):
            for x in (1, 2, 3):
                f.set(x, y, gauze if (x + y) % 2 else gauze_s)
        f.set(3, 3, gauze_s)
        f.set(0, 3, gauze_d); f.set(0, 4, gauze_d)
        f.set(2, 4, blood); f.set(2, 5, "#c1736a")
        # a strip up from the pad to the band, one down the cheek and back up behind the ear
        f.set(0, 5, gauze_s)
        s.face("head", 1, "right").fill(gauze, 6, 8, 3, 5)
        s.face("head", 1, "right").set(5, 3, gauze_s)
        for x in range(8):
            s.face("head", 1, "top").set(x, 7, gauze if x % 2 else gauze_s)
            s.face("head", 1, "top").set(x, 6, gauze_s if x % 2 else gauze)
        s.face("head", 1, "back").set(3, 3, gauze_s); s.face("head", 1, "back").set(4, 3, gauze_s)
        s.face("head", 1, "back").set(3, 4, gauze_d)
    # hospital gown (outer layer, over the base blouse)
    gown, gown_s, gown_d, dot = "#f2f4f6", "#d6dce4", "#b9c2ce", "#a9c3e0"
    s.face("body", 0, "front").fill(gown)
    for fn in ("back", "left", "right"):
        s.face("body", 0, fn).fill(gown)
    s.face("body", 0, "top").fill(gown)
    s.face("body", 0, "bottom").fill(gown_s)
    for fn in ("front", "back", "left", "right"):
        f = s.face("body", 1, fn)
        f.fill(gown)
        f.noise([gown_s, dot], 0.06, 111 + len(fn))
    nf = s.face("body", 1, "front")
    nf.art(["gs....sg", ".gs..sg."], {"g": gown_d, "s": skin_c})
    nf.set(3, 0, skin_c); nf.set(4, 0, skin_c); nf.set(3, 1, skin_c); nf.set(4, 1, skin_c)
    nf.row(0, skin_c, 2, 6)
    nf.set(2, 0, gown_d); nf.set(5, 0, gown_d); nf.set(2, 1, gown_s); nf.set(5, 1, gown_s)
    nf.set(3, 1, gown); nf.set(4, 1, gown)
    nb = s.face("body", 1, "back")
    nb.set(3, 5, gown_s); nb.set(4, 5, gown_s)
    nb.set(2, 6, gown_d); nb.set(5, 6, gown_d)                 # the ties
    if hurt:
        strap, strap_s = "#cdb98f", "#a89870"
        for i in range(8):
            y = i * 5 // 7
            nf.set(i, y + 1, strap if i % 2 else strap_s)
            nf.set(i, y + 2, strap)
        for y in range(0, 5):
            s.face("body", 1, "back").set(1 + y // 2, y, strap)
    # arms
    for p in ("rarm", "larm"):
        for fn in ("front", "back", "right", "left"):
            s.face(p, 0, fn).fill(skin_c)
        for fn in ("front", "back", "right", "left"):
            f = s.face(p, 1, fn)
            f.fill(gown, y1=4)
            f.row(3, gown_s)
            f.noise([gown_s, dot], 0.14, 121, y1=3)
        s.face(p, 1, "top").fill(gown)
    if hurt:
        # the right arm: a strip of tape over the vein, a small bruise
        f = s.face("rarm", 1, "front")
        for x in range(3):
            f.set(x, 6, "#f4f2ea")
        f.set(1, 5, "#f4f2ea"); f.set(1, 7, "#f4f2ea")
        f.set(1, 6, "#cfd4dc")
        s.face("rarm", 0, "front").set(2, 8, "#c9a0b4")
        # the left arm: plaster from just below the sleeve to the knuckles, on both layers
        pl, pl_s, pl_d = "#f1efe6", "#d9d5c6", "#bab5a2"
        for layer in (0, 1):
            for fn in ("front", "back", "right", "left"):
                f = s.face("larm", layer, fn)
                f.fill(pl, y0=4, y1=11)
                f.noise([pl_s, pl_s, pl], 0.2, 131 + layer, y0=4, y1=11)
                f.row(4, pl_d); f.row(10, pl_d)
                if layer == 1:
                    f.row(5, pl_s)
            s.face("larm", layer, "bottom").fill(pl_s)
        sf = s.face("larm", 1, "front")
        sf.set(1, 7, "#6d84a8"); sf.set(2, 7, "#6d84a8"); sf.set(1, 8, "#6d84a8")        # scribbles on the cast
        for fn in ("front", "back", "right", "left"):
            s.face("larm", 0, fn).row(11, skin_c)
            s.face("larm", 1, fn).row(11, None)
        s.face("larm", 1, "front").row(10, pl_d)
    else:
        for p in ("rarm", "larm"):
            for fn in ("front", "back", "right", "left"):
                s.face(p, 0, fn).row(11, skin_s)
    # legs: gown hem, bare, pale blue hospital slippers; a plaster on one shin
    slip, slip_s = "#a9c6e4", "#7f9fc4"
    for p in ("rleg", "lleg"):
        for fn in ("front", "back", "right", "left"):
            f = s.face(p, 1, fn)
            f.fill(gown, y1=3)
            f.row(2, gown_s)
            f.noise([gown_s, dot], 0.14, 141, y1=2)
            fb = s.face(p, 0, fn)
            fb.fill(slip, y0=10, y1=12)
            fb.row(10, slip_s)
        s.face(p, 0, "bottom").fill(slip_s)
        s.face(p, 1, "top").fill(gown)
    if hurt:
        f = s.face("rleg", 0, "front")
        for y in (6, 7):
            for x in (1, 2):
                f.set(x, y, "#f4f2ea")
    return s


def rei():
    return _rei(True)


# ---------------------------------------------------------------- REI (school uniform)

def rei_uniform():
    s = _rei(False)
    skin_c, skin_s = "#f6e9e2", "#e1c9c6"
    blouse, blouse_s, blouse_d = "#fbfbfd", "#dadfe8", "#bcc4d2"
    teal, teal_d, teal_l = "#2f8d99", "#1f6573", "#4cb0b8"
    rib, rib_d = "#c8242f", "#8e1722"
    sock, shoe = "#f4f5f8", "#3a2a2a"
    # wipe the gown: everything under the head is rebuilt
    for part in ("body", "rarm", "larm", "rleg", "lleg"):
        for layer in (0, 1):
            for fn in FACES:
                s.face(part, layer, fn).fill(None)
    for part in ("body", "rarm", "larm", "rleg", "lleg"):
        s.fill_part(part, 0, skin_c)
    for p in ("rarm", "larm", "rleg", "lleg"):
        s.face(p, 0, "bottom").fill(skin_s)
    # blouse (base layer)
    for fn in FACES:
        s.face("body", 0, fn).fill(blouse)
    # pinafore (outer layer): straps, bodice, pleated skirt
    f = s.face("body", 1, "front")
    f.art(["..tsst..",      # not used rows are overwritten below
           "tt....tt"], {"t": teal, "s": blouse})
    f.fill(None)
    # neckline: blouse collar and the red ribbon; straps over the shoulders; bodice from row 3 down
    for y in range(0, 12):
        for x in range(8):
            if y <= 2:
                if x in (1, 2, 5, 6) and y >= 0:
                    f.set(x, y, teal)
            elif y <= 6:
                f.set(x, y, teal)
            else:
                f.set(x, y, teal if (x + y) % 2 else teal_d)
    f.row(2, teal, 1, 3); f.row(2, teal, 5, 7)
    f.row(3, teal_d)
    for y in range(7, 12):
        for x in range(8):
            f.set(x, y, teal if x % 2 == 0 else teal_d)
    f.row(11, teal_d)
    # collar of the blouse (on the outer layer so it stands off the shoulders)
    for x in (2, 5):
        f.set(x, 1, blouse_s)
    f.set(1, 0, blouse); f.set(6, 0, blouse); f.set(2, 0, blouse); f.set(5, 0, blouse)
    for x in (3, 4):
        f.set(x, 0, blouse); f.set(x, 1, blouse_s)
    f.set(3, 2, rib); f.set(4, 2, rib); f.set(2, 2, rib_d); f.set(5, 2, rib_d); f.set(3, 3, rib_d); f.set(4, 3, rib_d)
    f.set(2, 3, rib); f.set(5, 3, rib)
    f.col(0, None, 0, 3); f.col(7, None, 0, 3)
    for y in range(0, 3):
        f.set(0, y, blouse_s); f.set(7, y, blouse_s)
    # the blouse shows between the straps' edges and the ribbon: keep the outer layer's first rows light
    for fn in ("back", "right", "left"):
        g = s.face("body", 1, fn)
        g.fill(teal, y0=3)
        g.fill(None, y0=0, y1=3)
        for y in range(7, 12):
            for x in range(g.w):
                g.set(x, y, teal if (x + y) % 2 else teal_d)
        g.row(3, teal_d)
        if fn == "back":
            for x in (1, 2, 5, 6):
                for y in range(0, 3):
                    g.set(x, y, teal)
    s.face("body", 1, "top").fill(None)
    s.face("body", 1, "bottom").fill(teal_d)
    # arms: short puffed blouse sleeves, bare forearms
    for p in ("rarm", "larm"):
        for fn in ("front", "back", "right", "left"):
            g = s.face(p, 1, fn)
            g.fill(blouse, y1=4)
            g.row(3, blouse_s)
            g.row(0, blouse)
            s.face(p, 0, fn).row(11, skin_s)
        s.face(p, 1, "top").fill(blouse)
    # legs: pleated skirt over the thighs, white socks, brown shoes
    for p in ("rleg", "lleg"):
        for fn in ("front", "back", "right", "left"):
            g = s.face(p, 1, fn)
            g.fill(teal, y1=4)
            for x in range(g.w):
                if x % 2:
                    g.fill(teal_d, x, x + 1, 0, 4)
            g.row(3, teal_d)
            b = s.face(p, 0, fn)
            b.fill(sock, y0=6, y1=10)
            b.row(6, blouse_s)
            b.fill(shoe, y0=10, y1=12)
            b.row(10, "#5a4038")
        s.face(p, 1, "top").fill(teal)
        s.face(p, 0, "bottom").fill(shoe)
    return s


# ---------------------------------------------------------------- MEDICS

def _medic(slim, tone, tone_s, cap, cap_d, cap_l, eyes, tag):
    s = Skin(slim=slim)
    mask, mask_s, mask_d = "#e3f0ee", "#bfd4d2", "#9db6b4"
    scrub, scrub_d, scrub_l = "#8fcfb4", "#69ab90", "#b0e4cc"
    pocket = "#74b89c"
    shoe, shoe_s = "#e9ecee", "#bfc5c9"
    base_body(s, tone, tone_s)
    lg = {"c": cap, "d": cap_d, "l": cap_l, "s": tone, "S": tone_s, "e": eyes, "w": "#fbfbfb", "b": "#3a2a24",
          "m": mask, "M": mask_s, "N": mask_d}
    head = s.face("head", 0, "front")
    head.art(["cclccccc",
              "ccccdccc",
              "dddddddd",
              "sbbssbbs",
              "swesswes",
              "mMmmmmMm",
              "MmNNNNmM",
              "mmMMMMmm"], lg)
    head.row(2, cap_d)
    head.set(0, 2, cap); head.set(7, 2, cap)
    head.set(3, 4, tone_s); head.set(4, 4, tone_s)
    head.set(3, 5, "#d0e2e0"); head.set(4, 5, "#d0e2e0")
    for fn in ("right", "left"):
        f = s.face("head", 0, fn)
        f.fill(tone)
        f.fill(cap, 0, 8, 0, 3)
        f.row(2, cap_d)
        fc = 7 if fn == "right" else 0
        # ear loop of the mask: a light line from the mask back to the ear
        for x in (range(3, 8) if fn == "right" else range(0, 5)):
            f.set(x, 5, mask)
        for y in range(5, 8):
            for x in (range(5, 8) if fn == "right" else range(0, 3)):
                f.set(x, y, mask if y != 6 else mask_s)
        f.set(4 if fn == "right" else 3, 4, tone_s)
        f.set(4 if fn == "right" else 3, 3, tone)
    bk = s.face("head", 0, "back")
    bk.fill(cap, y1=4).fill(tone, y0=4)
    bk.row(3, cap_d)
    bk.set(3, 4, mask); bk.set(4, 4, mask)                                    # the mask's tie
    bk.set(2, 5, mask_s); bk.set(5, 5, mask_s)
    t = s.face("head", 0, "top")
    t.fill(cap)
    t.col(3, cap_d); t.col(4, cap_l)
    s.face("head", 0, "bottom").fill(tone_s)
    s.lift("head", lambda px: px[:3] in (rgba(cap)[:3], rgba(cap_d)[:3], rgba(cap_l)[:3], rgba(mask)[:3],
                                          rgba(mask_s)[:3], rgba(mask_d)[:3]) and True)
    # scrubs: V-neck short-sleeved top with a chest pocket, drawstring trousers
    body = s.face("body", 0, "front")
    body.fill(scrub)
    body.art(["ssssssss",
              "Dsss ssD".replace(" ", "s"),
              "DDssssDD"], {"s": scrub, "D": scrub_d})
    body.set(3, 0, tone); body.set(4, 0, tone); body.set(2, 0, scrub_d); body.set(5, 0, scrub_d)
    body.set(3, 1, tone_s); body.set(4, 1, tone_s); body.set(2, 1, scrub_d); body.set(5, 1, scrub_d)
    body.set(3, 2, scrub_d); body.set(4, 2, scrub_d)
    for x in (5, 6):
        body.set(x, 4, pocket); body.set(x, 5, pocket)
    body.set(5, 3, scrub_d); body.set(6, 3, scrub_d)
    body.noise([scrub_l, scrub_d], 0.07, 151, y0=3)
    body.row(11, scrub_d)
    for fn in ("back", "right", "left"):
        f = s.face("body", 0, fn)
        f.fill(scrub)
        f.noise([scrub_l, scrub_d], 0.07, 152)
        f.row(11, scrub_d)
    s.face("body", 0, "top").fill(scrub)
    s.face("body", 0, "bottom").fill(scrub_d)
    s.lift("body", lambda px: True, ("front", "back", "left", "right"))
    s.face("body", 1, "front").fill(None, y0=0, y1=3)
    s.face("body", 1, "front").set(0, 0, scrub_d)
    # sleeves, trousers, shoes
    for p in ("rarm", "larm"):
        band(s, p, 0, 0, 5, scrub, top=True)
        band(s, p, 1, 0, 5, scrub)
        for fn in ("front", "back", "right", "left"):
            s.face(p, 0, fn).row(4, scrub_d)
            s.face(p, 1, fn).row(4, scrub_d)
            s.face(p, 1, fn).noise([scrub_l], 0.1, 153, y1=4)
            s.face(p, 0, fn).row(11, tone_s)
    for p in ("rleg", "lleg"):
        band(s, p, 0, 0, 10, scrub, bottom=False)
        band(s, p, 0, 10, 12, shoe, bottom=True)
        band(s, p, 1, 0, 10, scrub)
        for fn in ("front", "back", "right", "left"):
            s.face(p, 0, fn).noise([scrub_l, scrub_d], 0.07, 154, y1=10)
            s.face(p, 0, fn).row(10, shoe_s)
            s.face(p, 1, fn).noise([scrub_l, scrub_d], 0.08, 155, y1=10)
        s.face(p, 1, "top").fill(scrub)
        s.face(p, 0, "top").fill(scrub)
    return s


def medic1():
    return _medic(False, "#d9ac8b", "#bd8d6e", "#98d1b8", "#70ad93", "#b8e5d0", "#3a2a1c", "1")


def medic2():
    return _medic(True, "#9a6a4c", "#7e5139", "#6cc0c4", "#4c9ca3", "#92dadc", "#1f2c46", "2")


MAKERS = {"misato": misato, "ritsuko": ritsuko, "gendo": gendo, "rei": rei, "rei_uniform": rei_uniform,
          "medic1": medic1, "medic2": medic2}


def make_all():
    out = {}
    for name, fn in MAKERS.items():
        sk = fn()
        out[name] = (sk.image(), sk.slim)
    return out


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    skins = make_all()
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview"), exist_ok=True)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview", "sheet.png")
    render.sheet(skins, out)
    print(out)

