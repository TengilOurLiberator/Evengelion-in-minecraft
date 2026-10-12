"""Original 64x64 Minecraft player skins for the cast, drawn in code (pixel art with numpy/pillow).

    make_all() -> {id: (PIL image 64x64 RGBA, slim)}

The designs are our own renderings of plain role descriptions (see tools\\cast\\README.md). Every skin is drawn on
the modern 64x64 layout: base layer and the outer ("hat" / "jacket" / "sleeve" / "pants") layer, the arms either
4 pixels wide or, for the women and the girl, 3 pixels wide (the slim model; the datapack asks for it).

Style rules (the first in-game look showed random speckle reading as dirt): flat areas of one colour; shading only
where form asks for it (under the chin, under the fringe, folds, hems, the shaded side of a limb, collar edges);
no random noise anywhere; faces readable at 6 blocks: eyebrows, eyes two pixels wide with a bright pixel, a nose
shadow, a visible mouth.

Drawing helpers: Skin.face(part, layer, face) is a view of one face as seen from outside (row 0 = top), and
Face.art() paints a face from a small ASCII picture. '.' in a picture leaves the pixel as it was.
"""
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
SIDES = ("front", "back", "right", "left")


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

    def tone_cols(self, tones, y0=0, y1=None, x0=0):
        """Vertical bands: one colour per column (tones is a list), rows y0..y1. Hair clumps."""
        y1 = self.h if y1 is None else y1
        for i, c in enumerate(tones):
            self.fill(c, x0 + i, x0 + i + 1, y0, y1)
        return self

    def darken_row(self, y, t=0.15, x0=0, x1=None):
        x1 = self.w if x1 is None else x1
        for x in range(x0, x1):
            if self.a[y, x, 3]:
                self.a[y, x, :3] = dark(tuple(self.a[y, x]), t)[:3]
        return self

    def darken_col(self, x, t=0.15, y0=0, y1=None):
        y1 = self.h if y1 is None else y1
        for y in range(y0, y1):
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

    def lift(self, part, mask=None, faces=FACES):
        """Copy base-layer pixels (satisfying mask) onto the outer layer (so hair, clothes and bandages stand off the body)."""
        for f in faces:
            self.face(part, 1, f).copy_from(self.face(part, 0, f), mask)

    def image(self):
        return Image.fromarray(self.a, "RGBA")


def seg(s, part, layer, y0, y1, c, side=None, top=None, bottom=None, faces=SIDES):
    """A band of one colour around a limb or the body (side faces optionally a shade darker)."""
    for f in faces:
        col = side if (side and f in ("right", "left")) else c
        s.face(part, layer, f).fill(col, y0=y0, y1=y1)
    if top:
        s.face(part, layer, "top").fill(top)
    if bottom:
        s.face(part, layer, "bottom").fill(bottom)


def hem(s, part, layer, y, c, faces=SIDES):
    for f in faces:
        s.face(part, layer, f).row(y, c)


def in_set(*colors):
    cs = [rgba(c) for c in colors]
    return lambda px: tuple(px) in cs


def base_body(skin, tone, shade):
    """Skin-coloured everything (the base layer under the clothes); soles and finger-ends a shade darker."""
    for part in PARTS:
        skin.fill_part(part, 0, tone)
    skin.face("head", 0, "bottom").fill(shade)
    for p in ("rarm", "larm", "rleg", "lleg"):
        skin.face(p, 0, "bottom").fill(shade)



# ---------------------------------------------------------------- MISATO

def misato():
    s = Skin(slim=True)
    skin_c, skin_s, skin_h = "#f3d3ba", "#d9aa8c", "#fae4d0"
    hair, hair_d, hair_l = "#4f2d73", "#321c4d", "#7b50a8"
    red, red_d, red_l = "#c3242f", "#8b1826", "#e04a52"
    dress, dress_l = "#25212e", "#37313f"
    boot, boot_l = "#17151c", "#34303c"
    base_body(s, skin_c, skin_s)
    lg = {"h": hair, "l": hair_l, "d": hair_d, "s": skin_c, "S": skin_s, "b": "#2c1a3d", "w": "#fffafa", "i": "#5a2f80",
          "I": "#331b4f", "n": skin_s, "m": "#c8505c", "M": "#8f3440"}
    # the face: fringe parted in the middle, long hair down both cheeks, eyes with a bright corner
    head = s.face("head", 0, "front")
    head.art(["hhhhhhhh",
              "hllhhllh",
              "hhhsshhh",
              "hbbssbbh",
              "hwissiwh",
              "hsssnssh",
              "hssmmssh",
              "hSSSSSSh"], lg)
    # hair on the sides, back and top: clear clumps (columns of one tone), a dark parting and a shine line
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(hair)
        f.tone_cols([hair_d, hair, hair, hair_l, hair, hair, hair_d, hair] if face == "right" else
                    [hair, hair_d, hair, hair, hair_l, hair, hair, hair_d])
        f.row(0, hair_d)
        fc = 7 if face == "right" else 0
        ear = 4 if face == "right" else 3
        for y in range(3, 7):
            f.set(fc, y, skin_c)
        f.set(fc, 7, skin_s)
    bk = s.face("head", 0, "back")
    bk.fill(hair).tone_cols([hair_d, hair, hair_l, hair, hair, hair_l, hair, hair_d])
    bk.row(0, hair_d); bk.row(7, hair_d)
    t = s.face("head", 0, "top")
    t.fill(hair).tone_cols([hair, hair_l, hair, hair_d, hair_d, hair, hair_l, hair])
    s.face("head", 0, "bottom").fill(hair_d)
    s.lift("head", in_set(hair, hair_l, hair_d))
    # torso: dress, short red jacket open at the front, a small silver cross on a chain
    body = s.face("body", 0, "front")
    body.art(["rjssssjr",
              "rrqssqrr",
              "rrqDDqrr",
              "rrqxDqrr",
              "rrqxxqrr",
              "rrqDxqrr",
              "qqqDDqqq",
              "DdDDDDdD",
              "DDDDDDDD",
              "DdDDDDdD",
              "DDDDDDDD",
              "dDDDDDDd"],
             {"r": red, "j": red_l, "s": skin_c, "q": red_d, "D": dress, "d": dress_l, "x": "#e8e8f2"})
    body.set(3, 1, skin_c); body.set(4, 1, skin_c)
    body.set(3, 0, skin_s); body.set(4, 0, skin_s)
    bk = s.face("body", 0, "back")
    bk.fill(red, y1=7).fill(dress, y0=7)
    bk.row(6, red_d); bk.col(3, red_d, 0, 6); bk.col(4, red_d, 0, 6)
    for face in ("right", "left"):
        f = s.face("body", 0, face)
        f.fill(red, y1=7).fill(dress, y0=7).row(6, red_d)
    s.face("body", 0, "top").fill(red)
    s.face("body", 0, "bottom").fill(dress)
    s.lift("body", in_set(red, red_l, red_d, "#e8e8f2"), ("front", "back", "left", "right", "top"))
    # the long hair over the back and the front of the shoulders (outer layer)
    hb = s.face("body", 1, "back")
    for y in range(0, 10):
        x0, x1 = (0, 8) if y < 6 else (1 + (y - 6) // 2, 7 - (y - 6) // 2)
        for x in range(x0, x1):
            hb.set(x, y, [hair_d, hair, hair_l, hair, hair, hair_l, hair, hair_d][x])
    hf = s.face("body", 1, "front")
    for y in range(0, 6):
        for x in ((0, 1) if y < 4 else (0,)):
            hf.set(x, y, hair if x else hair_d)
        for x in ((6, 7) if y < 4 else (7,)):
            hf.set(x, y, hair if x == 6 else hair_d)
    for face in ("right", "left"):
        f = s.face("body", 1, face)
        for y in range(0, 5):
            for x in range(4):
                f.set(x, y, hair_d if x == 3 else (hair_l if x == 1 else hair))
    s.face("body", 1, "top").fill(hair_d)
    # arms: short jacket sleeves, bare below (slim), a silver bracelet
    for p in ("rarm", "larm"):
        seg(s, p, 0, 0, 5, red, side=red_d, top=red)
        seg(s, p, 1, 0, 5, red, side=red_d, top=red)
        hem(s, p, 0, 4, red_d); hem(s, p, 1, 4, red_d)
        hem(s, p, 0, 9, "#c8c8d6")
        hem(s, p, 0, 11, skin_s)
    # legs: dark dress hem, bare skin, black ankle boots
    for p in ("rleg", "lleg"):
        seg(s, p, 0, 0, 4, dress, top=dress, bottom=None)
        seg(s, p, 1, 0, 4, dress, top=dress)
        hem(s, p, 1, 3, dress_l)
        seg(s, p, 0, 9, 12, boot, bottom=boot)
        hem(s, p, 0, 9, boot_l)
        hem(s, p, 0, 7, skin_s)
        s.face(p, 0, "front").set(1, 8, skin_h)
    return s


# ---------------------------------------------------------------- RITSUKO

def ritsuko():
    s = Skin(slim=True)
    skin_c, skin_s, skin_h = "#f4d5bb", "#dab090", "#fae4d0"
    hair, hair_d, hair_l = "#e8cf7c", "#bd9f4c", "#f9eaa6"
    coat, coat_s, coat_d = "#f4f5fa", "#d4d9e6", "#b4bccf"
    blue, blue_d, blue_l = "#3e6fbe", "#2b4f93", "#5b8ad6"
    skirt, skirt_l = "#262a3e", "#363b54"
    tights, tights_l = "#2d2838", "#443d52"
    shoe = "#1a181f"
    base_body(s, skin_c, skin_s)
    head = s.face("head", 0, "front")
    lg = {"h": hair, "l": hair_l, "d": hair_d, "s": skin_c, "S": skin_s, "b": "#5a3d2a", "w": "#fffafa", "i": "#46628f",
          "n": skin_s, "m": "#c4636c", "o": "#7b4a3a"}
    # short blonde hair, a swept fringe, a mole under the left eye (viewer's right)
    head.art(["hhhhhhhh",
              "hllllhhh",
              "hdhhhdsh",
              "hbbssbbh",
              "hwissiwh",
              "hsssnsoh",
              "sssmmsss",
              "sSSSSSSs"], lg)
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(skin_c)
        f.fill(hair, 0, 8, 0, 6)
        f.tone_cols([hair_d, hair, hair, hair_l, hair, hair, hair, hair_d] if face == "right" else
                    [hair_d, hair, hair, hair, hair_l, hair, hair, hair_d], y0=0, y1=6)
        f.row(0, hair_d)
        fc = 7 if face == "right" else 0
        ear = 4 if face == "right" else 3
        f.col(fc, skin_c, 3, 8)
        f.set(ear, 4, skin_c); f.set(ear, 3, skin_c); f.set(ear + (1 if face == "right" else -1), 4, skin_s)
        f.fill(hair, 0 if face == "right" else 5, 3 if face == "right" else 8, 6, 7)
    bk = s.face("head", 0, "back")
    bk.fill(skin_c).fill(hair, 0, 8, 0, 7).tone_cols([hair_d, hair, hair_l, hair, hair, hair_l, hair, hair_d], y1=7)
    bk.row(6, hair_d); bk.row(7, skin_s)
    t = s.face("head", 0, "top")
    t.fill(hair).tone_cols([hair, hair_l, hair, hair_d, hair_l, hair, hair, hair])
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
        body.set(3, y, blue_l); body.set(4, y, blue_d)
    body.row(7, "#52587a", 0, 8)
    s.face("body", 0, "back").fill(blue, y1=7).fill(skirt, y0=7).row(7, "#52587a")
    for face in ("right", "left"):
        s.face("body", 0, face).fill(blue, y1=7).fill(skirt, y0=7)
    s.face("body", 0, "top").fill(blue)
    s.face("body", 0, "bottom").fill(skirt)
    # coat (outer layer): two panels in front, closed behind and at the sides; one deliberate fold line per panel
    cf = s.face("body", 1, "front")
    for y in range(12):
        for x in (0, 1, 2, 5, 6, 7):
            cf.set(x, y, coat)
    cf.col(2, coat_s); cf.col(5, coat_s)
    cf.set(2, 0, coat_d); cf.set(5, 0, coat_d); cf.set(2, 1, coat_d); cf.set(5, 1, coat_d)
    cf.col(0, coat_s, 2, 12); cf.col(7, coat_s, 2, 12)
    cf.row(11, coat_s, 0, 3); cf.row(11, coat_s, 5, 8)
    for p in ("back", "right", "left"):
        f = s.face("body", 1, p)
        f.fill(coat)
        f.row(11, coat_s)
        if p != "back":
            f.col(0, coat_s); f.col(3, coat_s)
    bf = s.face("body", 1, "back")
    bf.col(3, coat_s, 5, 12); bf.col(4, coat_s, 5, 12); bf.col(3, coat_d, 9, 12)
    s.face("body", 1, "top").fill(coat)
    s.face("body", 1, "bottom").fill(coat_s)
    # arms: long coat sleeves with a blue cuff, hands bare
    for p in ("rarm", "larm"):
        seg(s, p, 1, 0, 10, coat, side=coat_s, top=coat)
        hem(s, p, 1, 9, coat_s)
        hem(s, p, 0, 9, blue)
        hem(s, p, 0, 10, blue_d)
        s.face(p, 1, "front").set(0, 3, coat_s)
    # legs: dark tights, shoes, the coat's skirts over the thighs and knees
    for p in ("rleg", "lleg"):
        seg(s, p, 0, 0, 10, tights, top=tights)
        seg(s, p, 0, 10, 12, shoe, bottom=shoe)
        hem(s, p, 0, 10, "#2a2730")
        s.face(p, 0, "front").col(1 if p == "rleg" else 2, tights_l, 1, 9)
        for face in ("back", "right", "left"):
            s.face(p, 1, face).fill(coat, y0=0, y1=7)
            s.face(p, 1, face).row(6, coat_s)
        s.face(p, 1, "front").fill(coat, x0=0 if p == "rleg" else 2, x1=2 if p == "rleg" else 4, y0=0, y1=7)
        s.face(p, 1, "front").row(6, coat_s, 0 if p == "rleg" else 2, 2 if p == "rleg" else 4)
        s.face(p, 1, "top").fill(coat)
    return s


# ---------------------------------------------------------------- GENDO

def gendo():
    s = Skin(slim=False)
    skin_c, skin_s, skin_h = "#e9c3a6", "#c49478", "#f4d6bd"
    hair, hair_g = "#1f1b1e", "#59565a"
    beard, beard_l = "#2f2627", "#473b3c"
    coat, coat_l, coat_d = "#3d3647", "#51495d", "#292430"
    red, red_d = "#b3222f", "#701622"
    glove, glove_s = "#f6f6f8", "#c9ccd6"
    shoe = "#141217"
    frame = "#2a1f1b"
    base_body(s, skin_c, skin_s)
    # face: forehead and cheeks light, orange glasses (frame, lens with a bright upper pixel and the eye below),
    # a nose line down the middle, close beard along the jaw, a dark mouth in it
    head = s.face("head", 0, "front")
    head.fill(skin_c)
    head.art(["hhhhhhhh",
              "hhhhhhhh",
              "hgsHHsgh",
              "fLLffLLf",
              "fOeNHeOf",
              "assNHssa",
              "aaSmmSaa",
              "aAaaaaAa"],
             {"h": hair, "g": hair_g, "s": skin_c, "S": skin_s, "H": skin_h, "N": "#a98068", "f": frame, "L": "#ffd070",
              "O": "#ee9322", "e": "#2a1a10", "m": "#7a4a44", "a": beard, "A": beard_l})
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(skin_c)
        f.fill(hair, 0, 8, 0, 2)
        if face == "right":
            f.fill(hair, 0, 5, 2, 3); f.fill(hair, 0, 3, 3, 5); f.fill(hair, 0, 3, 5, 6)
        else:
            f.fill(hair, 3, 8, 2, 3); f.fill(hair, 5, 8, 3, 5); f.fill(hair, 5, 8, 5, 6)
        fc = 7 if face == "right" else 0
        ear_x = 4 if face == "right" else 3
        f.set(ear_x, 4, skin_s); f.set(ear_x, 3, skin_c); f.set(ear_x + (1 if face == "right" else -1), 4, skin_s)
        for x in (range(5, 8) if face == "right" else range(0, 3)):
            f.set(x, 3, frame)                               # the arm of the glasses
        for y in range(5, 8):
            for x in (range(4, 8) if face == "right" else range(0, 4)):
                f.set(x, y, beard)
        f.set(fc, 2, hair_g)
        f.set(fc, 3, frame)
    bk = s.face("head", 0, "back")
    bk.fill(hair)
    bk.fill(skin_c, y0=6)
    bk.row(5, hair_g)
    t = s.face("head", 0, "top")
    t.fill(hair)
    t.col(2, hair_g, 0, 3)
    s.face("head", 0, "bottom").fill(beard)
    s.lift("head", in_set(hair, hair_g))
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
              "tttttttt",
              "tTttttTt"],
             {"c": coat, "R": red, "K": coat_d, "L": coat_l, "B": "#15121a", "t": "#2a2530", "T": "#37313f"})
    body.set(3, 9, "#c8c8d4"); body.set(4, 9, "#c8c8d4")
    for y in (3, 5, 7):
        body.set(3, y, "#d4b150")
    bk = s.face("body", 0, "back")
    bk.fill(coat, y1=9).fill("#15121a", y0=9, y1=10).fill("#2a2530", y0=10)
    bk.col(3, coat_d, 0, 9); bk.col(4, coat_d, 0, 9)
    for face in ("right", "left"):
        f = s.face("body", 0, face)
        f.fill(coat, y1=9).fill("#15121a", y0=9, y1=10).fill("#2a2530", y0=10)
        f.col(1, coat_l, 2, 9)
    s.face("body", 0, "top").fill(coat)
    s.face("body", 0, "bottom").fill("#2a2530")
    # outer layer: the stand-up collar (red inside) and the jacket's thickness
    o = s.face("body", 1, "front")
    o.fill(coat, y1=9)
    o.art(["cRRRRRRc", "ccRRRRcc"], {"c": coat_l, "R": red})
    o.col(3, coat_d, 2, 9); o.col(4, coat_d, 2, 9)
    for y in (3, 5, 7):
        o.set(3, y, "#d4b150")
    for fn in ("back", "right", "left"):
        f = s.face("body", 1, fn)
        f.fill(coat, y1=9)
        f.row(0, coat_l); f.row(1, coat_l)
    s.face("body", 1, "back").col(3, coat_d, 2, 9)
    s.face("body", 1, "back").col(4, coat_d, 2, 9)
    s.face("body", 1, "top").fill(coat_l)
    for p in ("rarm", "larm"):
        seg(s, p, 0, 0, 9, coat, side=coat_d, top=coat)
        seg(s, p, 0, 9, 12, glove, bottom=glove_s)
        seg(s, p, 1, 0, 9, coat, side=coat_d, top=coat)
        seg(s, p, 1, 9, 12, glove)
        hem(s, p, 1, 8, coat_d)
        hem(s, p, 1, 9, glove_s)
        hem(s, p, 1, 11, glove_s)
        hem(s, p, 0, 9, glove_s)
        s.face(p, 1, "front").set(1, 10, glove_s); s.face(p, 1, "front").set(2, 10, glove_s)
    for p in ("rleg", "lleg"):
        seg(s, p, 0, 0, 10, "#2a2530", top="#2a2530")
        seg(s, p, 0, 10, 12, shoe, bottom=shoe)
        hem(s, p, 0, 10, "#1b181f")
        s.face(p, 0, "front").col(1 if p == "rleg" else 2, "#3a3445", 0, 10)
        seg(s, p, 1, 0, 10, "#2a2530")
    return s


# ---------------------------------------------------------------- REI

GOWN = dict(g="#f0f4f8", s="#d4deea", d="#b2c1d4", trim="#9fb7d6")
PALE = dict(c="#f6e9e2", s="#e1c9c6", h="#fff6f0")
HAIR = dict(h="#8fbbe0", d="#628fba", l="#c1ddf3", dd="#4f78a0")


def _rei_head(s, hurt):
    c, sh = PALE["c"], PALE["s"]
    hair, hair_d, hair_l = HAIR["h"], HAIR["d"], HAIR["l"]
    base_body(s, c, sh)
    lg = {"h": hair, "l": hair_l, "d": hair_d, "s": c, "S": sh, "n": sh, "m": "#dc9a9a"}
    head = s.face("head", 0, "front")
    head.art(["hhhhhhhh",
              "hlhhhhlh",
              "hdhhhhdh",
              "hddssddh",
              "hsssssSh",
              "hsssnssh",
              "sssmmsss",
              "sSSSSSSs"], lg)
    red_hi, red_lo = "#ff6b83", "#d0213a"
    head.set(5, 4, red_hi); head.set(6, 4, red_lo)        # the one red eye (viewer's right): bright pixel, deep red
    if not hurt:
        head.set(1, 4, red_lo); head.set(2, 4, red_hi)    # unhurt: both eyes
    for face in ("right", "left"):
        f = s.face("head", 0, face)
        f.fill(c)
        f.fill(hair, 0, 8, 0, 6)
        f.tone_cols([hair_d, hair, hair, hair_l, hair, hair, hair_d, hair] if face == "right" else
                    [hair, hair_d, hair, hair, hair_l, hair, hair, hair_d], y0=0, y1=6)
        f.row(0, hair_d)
        fc = 7 if face == "right" else 0
        f.col(fc, hair, 0, 7)
        f.col(fc, c, 3, 6)
        f.set(fc, 6, hair)
        f.set(4 if face == "right" else 3, 4, sh)
    bk = s.face("head", 0, "back")
    bk.fill(hair).tone_cols([hair_d, hair, hair, hair_l, hair, hair, hair_d, hair], y1=6)
    bk.row(6, hair_d); bk.row(7, sh)
    t = s.face("head", 0, "top")
    t.fill(hair).tone_cols([hair, hair_l, hair, hair_d, hair_d, hair, hair_l, hair])
    s.face("head", 0, "bottom").fill(sh)
    s.lift("head", in_set(hair, hair_l, hair_d))
    if hurt:
        g, gs, gd = "#f6f3ea", "#e0dccd", "#bfb9a6"
        # a clean band round the head on the brow line (rows 2-3, all four sides) and a pad over the right eye
        # (viewer's left): x0..3 down to row 5. Neat edge: lightest in the middle, one shade darker rim below
        for fn in SIDES:
            f = s.face("head", 1, fn)
            f.fill(g, y0=2, y1=3)
            f.fill(gs, y0=3, y1=4)
        f = s.face("head", 1, "front")
        f.fill(g, 0, 4, 2, 6)
        f.row(5, gs, 0, 4)                                  # the pad's lower edge
        f.col(3, gs, 4, 6)                                  # its inner edge
        f.row(3, gs, 4, 8)                                  # the band's lower edge over the other eye
        f.row(2, g, 0, 8)
        f.set(3, 3, gs)
        # a slight shadow on the skin below the band and the pad (base layer, so it shows under the bandage edge)
        b = s.face("head", 0, "front")
        b.fill(sh, 0, 4, 6, 7)
        # the band wraps over the temples and ties at the back: two short tails
        bk1 = s.face("head", 1, "back")
        bk1.set(3, 4, gs); bk1.set(4, 4, gs); bk1.set(3, 5, gd); bk1.set(4, 5, gd)
    return s


def _rei(hurt):
    s = Skin(slim=True)
    c, sh = PALE["c"], PALE["s"]
    _rei_head(s, hurt)
    g, gs, gd, trim = GOWN["g"], GOWN["s"], GOWN["d"], GOWN["trim"]
    # hospital gown: plain white-pale-blue, a clear V neckline with a darker trim, the sides one shade darker
    for fn in SIDES:
        s.face("body", 0, fn).fill(g)
        s.face("body", 1, fn).fill(g)
    s.face("body", 0, "top").fill(g); s.face("body", 1, "top").fill(g)
    s.face("body", 0, "bottom").fill(gs); s.face("body", 1, "bottom").fill(gs)
    nf = s.face("body", 1, "front")
    nf.art([".tssssT.",
            "..tssT..",
            "...tT..."], {"t": trim, "T": trim, "s": sh})
    nf.col(0, gs, 1, 12); nf.col(7, gs, 1, 12)
    nf.row(11, gs)
    nb = s.face("body", 1, "back")
    nb.row(0, trim, 2, 6)
    nb.col(0, gs); nb.col(7, gs); nb.row(11, gs)
    nb.set(3, 5, gd); nb.set(4, 5, gd)                        # the gown's ties
    nb.set(2, 6, gd); nb.set(5, 6, gd)
    for fn in ("left", "right"):
        f = s.face("body", 1, fn)
        f.col(0, gs); f.col(3, gs); f.row(11, gs)
    # arms
    for p in ("rarm", "larm"):
        for fn in SIDES:
            s.face(p, 0, fn).fill(c)
        seg(s, p, 1, 0, 4, g, side=gs, top=g)
        hem(s, p, 1, 3, gs)
        hem(s, p, 0, 11, sh)
    if hurt:
        # the right arm: a clean strip of tape over the vein
        f = s.face("rarm", 1, "front")
        f.fill("#f4f2ea", 0, 3, 6, 8)
        f.row(7, "#cfd4dc", 0, 3)
        # the left arm in plaster: one solid off-white from below the sleeve to the knuckles, both layers, the sides
        # one shade darker, a darker rim top and bottom
        pl, pl_s, pl_d = "#f3efe4", "#dcd7c8", "#bdb7a3"
        for layer in (0, 1):
            for fn in SIDES:
                f = s.face("larm", layer, fn)
                f.fill(pl_s if fn in ("left", "right") else pl, y0=4, y1=11)
                f.row(4, pl_d); f.row(10, pl_d)
            s.face("larm", layer, "bottom").fill(pl_s)
        for fn in SIDES:
            s.face("larm", 0, fn).row(11, c)
            s.face("larm", 1, fn).row(11, None)
        # the sling strap: ONE colour, a clean 2-pixel diagonal from the right shoulder (viewer's left) across the
        # chest to the left side, and a band round the cast at the wrist; behind, from the shoulder to the neck
        strap = "#c3ad7c"
        for i in range(0, 7):
            nf.set(1 + i, 1 + i, strap)
            nf.set(2 + i, 1 + i, strap)
        for fn in SIDES:
            s.face("larm", 1, fn).row(9, strap)
        for y in range(0, 5):
            nb.set(1 + y // 2, y, strap)
            nb.set(2 + y // 2, y, strap)
    else:
        for p in ("rarm", "larm"):
            for fn in SIDES:
                s.face(p, 0, fn).row(11, sh)
    # legs: gown hem, bare, pale blue hospital slippers; a small plaster on one shin
    slip, slip_s = "#aac7e6", "#7f9fc4"
    for p in ("rleg", "lleg"):
        for fn in SIDES:
            s.face(p, 0, fn).fill(c)
            f = s.face(p, 1, fn)
            f.fill(g, y1=3)
            f.row(2, gs)
            fb = s.face(p, 0, fn)
            fb.fill(slip, y0=10, y1=12)
            fb.row(10, slip_s)
        s.face(p, 0, "bottom").fill(slip_s)
        s.face(p, 1, "top").fill(g)
    if hurt:
        f = s.face("rleg", 0, "front")
        f.fill("#f4f2ea", 1, 3, 6, 8)
    return s

def rei():
    return _rei(True)


# ---------------------------------------------------------------- REI (school uniform)

def rei_uniform():
    s = Skin(slim=True)
    skin_c, skin_s = PALE["c"], PALE["s"]
    _rei_head(s, False)
    blouse, blouse_s, blouse_d = "#fbfbfd", "#dadfe8", "#bcc4d2"
    teal, teal_d, teal_l = "#2f8d99", "#1f6573", "#4cb0b8"
    rib, rib_d = "#c8242f", "#8e1722"
    sock, shoe = "#f4f5f8", "#3a2a2a"
    for part in ("body", "rarm", "larm", "rleg", "lleg"):
        s.fill_part(part, 0, skin_c)
        for fn in FACES:
            s.face(part, 1, fn).fill(None)
    for p in ("rarm", "larm", "rleg", "lleg"):
        s.face(p, 0, "bottom").fill(skin_s)
    for fn in FACES:
        s.face("body", 0, fn).fill(blouse)
    # pinafore (outer layer): straps over the shoulders, a plain bodice, a pleated skirt (alternating columns)
    f = s.face("body", 1, "front")
    for y in range(0, 12):
        for x in range(8):
            if y <= 2:
                if x in (1, 2, 5, 6):
                    f.set(x, y, teal)
            elif y <= 6:
                f.set(x, y, teal)
            else:
                f.set(x, y, teal if x % 2 == 0 else teal_d)
    f.row(3, teal_d)
    f.row(11, teal_d)
    for x in (3, 4):
        f.set(x, 0, blouse); f.set(x, 1, blouse_s)
    f.set(0, 0, blouse_s); f.set(7, 0, blouse_s); f.set(0, 1, blouse_s); f.set(7, 1, blouse_s)
    f.set(0, 2, blouse_s); f.set(7, 2, blouse_s)
    f.set(3, 2, rib); f.set(4, 2, rib); f.set(2, 2, rib_d); f.set(5, 2, rib_d)
    f.set(3, 3, rib_d); f.set(4, 3, rib_d); f.set(2, 3, rib); f.set(5, 3, rib)
    for fn in ("back", "right", "left"):
        g = s.face("body", 1, fn)
        g.fill(teal, y0=3)
        for y in range(7, 12):
            for x in range(g.w):
                g.set(x, y, teal if x % 2 == 0 else teal_d)
        g.row(3, teal_d)
        if fn == "back":
            for x in (1, 2, 5, 6):
                for y in range(0, 3):
                    g.set(x, y, teal)
    s.face("body", 1, "bottom").fill(teal_d)
    for p in ("rarm", "larm"):
        for fn in SIDES:
            g = s.face(p, 1, fn)
            g.fill(blouse, y1=4)
            g.row(3, blouse_s)
            s.face(p, 0, fn).row(11, skin_s)
        s.face(p, 1, "top").fill(blouse)
    for p in ("rleg", "lleg"):
        for fn in SIDES:
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

def _medic(slim, tone, tone_s, tone_h, cap, cap_d, cap_l, eye, brow):
    s = Skin(slim=slim)
    # the mask is a pale cool surgical blue-white, clearly lighter than any skin, and only covers nose and mouth
    # (cheeks and chin stay skin) so that it cannot read as a beard
    mask, mask_h, mask_s = "#e4f3f7", "#f7fcfd", "#a9c9d6"
    loop = "#cfe5ec"
    scrub, scrub_d, scrub_l = "#8fcfb4", "#69ab90", "#b0e4cc"
    pocket = "#74b89c"
    shoe, shoe_s = "#e9ecee", "#bfc5c9"
    base_body(s, tone, tone_s)
    head = s.face("head", 0, "front")
    head.fill(tone)
    head.art(["cclccccc",
              "cccccdcc",
              "dddddddd",
              "ssssssss",
              "ssssssss",
              "ssssssss",
              "ssssssss",
              "sSSssSSs"], {"c": cap, "d": cap_d, "l": cap_l, "s": tone, "S": tone_s})
    head.fill(tone, 0, 8, 3, 8)
    head.row(2, cap_d)
    head.set(0, 2, cap); head.set(7, 2, cap)
    for x in (1, 2, 5, 6):
        head.set(x, 3, brow)
    head.set(1, 4, "#fbfbfb"); head.set(2, 4, eye); head.set(5, 4, eye); head.set(6, 4, "#fbfbfb")
    head.set(0, 4, tone_s); head.set(7, 4, tone_s)
    head.set(3, 4, tone_s); head.set(4, 4, tone_s)
    # mask: rows 5-6 from x1..6 with a pleat line, nose wire pixels lighter on top, shadow below
    head.fill(mask, 1, 7, 5, 7)
    head.row(5, mask_h, 2, 6)
    head.row(6, mask_s, 1, 7)
    head.set(1, 5, loop); head.set(6, 5, loop)
    head.set(0, 5, loop); head.set(7, 5, loop)               # the ear loops reach the edge of the face
    head.row(7, tone_s, 1, 7)
    head.set(3, 7, tone); head.set(4, 7, tone)
    for fn in ("right", "left"):
        f = s.face("head", 0, fn)
        f.fill(tone)
        f.fill(cap, 0, 8, 0, 3)
        f.row(2, cap_d)
        fc = 7 if fn == "right" else 0
        for x in (range(3, 8) if fn == "right" else range(0, 5)):
            f.set(x, 5, loop)                                # ear loop of the mask
        f.set(4 if fn == "right" else 3, 4, tone_s)
        f.set(4 if fn == "right" else 3, 3, tone)
        f.set(fc, 5, mask); f.set(fc, 6, mask_s)
    bk = s.face("head", 0, "back")
    bk.fill(cap, y1=4).fill(tone, y0=4)
    bk.row(3, cap_d)
    bk.set(3, 4, loop); bk.set(4, 4, loop)                   # the cap's tie
    bk.set(3, 5, cap_d); bk.set(4, 5, cap_d)
    t = s.face("head", 0, "top")
    t.fill(cap)
    t.col(3, cap_d); t.col(4, cap_l)
    s.face("head", 0, "bottom").fill(tone_s)
    s.lift("head", in_set(cap, cap_d, cap_l, mask, mask_h, mask_s, loop))
    # scrubs: V-neck short-sleeved top with a chest pocket, drawstring trousers
    body = s.face("body", 0, "front")
    body.fill(scrub)
    body.set(2, 0, scrub_d); body.set(5, 0, scrub_d)
    body.set(3, 0, tone); body.set(4, 0, tone)
    body.set(2, 1, scrub_d); body.set(5, 1, scrub_d); body.set(3, 1, tone_s); body.set(4, 1, tone_s)
    body.set(3, 2, scrub_d); body.set(4, 2, scrub_d)
    body.fill(scrub_d, 0, 1, 1, 3); body.fill(scrub_d, 7, 8, 1, 3)
    body.fill(pocket, 5, 7, 4, 6)
    body.row(3, scrub_d, 5, 7)
    body.row(11, scrub_d)
    for fn in ("back", "right", "left"):
        f = s.face("body", 0, fn)
        f.fill(scrub)
        f.row(11, scrub_d)
        if fn != "back":
            f.col(0, scrub_d, 2, 12)
    s.face("body", 0, "top").fill(scrub)
    s.face("body", 0, "bottom").fill(scrub_d)
    s.lift("body", None, ("front", "back", "left", "right"))
    s.face("body", 1, "front").fill(None, y0=0, y1=3)
    s.face("body", 1, "front").set(0, 0, scrub_d)
    for p in ("rarm", "larm"):
        seg(s, p, 0, 0, 5, scrub, side=scrub_d, top=scrub)
        seg(s, p, 1, 0, 5, scrub, side=scrub_d)
        hem(s, p, 0, 4, scrub_d); hem(s, p, 1, 4, scrub_d)
        hem(s, p, 0, 11, tone_s)
    for p in ("rleg", "lleg"):
        seg(s, p, 0, 0, 10, scrub, side=scrub_d)
        seg(s, p, 0, 10, 12, shoe, bottom=True and shoe)
        seg(s, p, 1, 0, 10, scrub, side=scrub_d)
        hem(s, p, 0, 10, shoe_s)
        hem(s, p, 0, 9, scrub_d); hem(s, p, 1, 9, scrub_d)
        s.face(p, 1, "top").fill(scrub)
        s.face(p, 0, "top").fill(scrub)
    return s


def medic1():
    return _medic(False, "#d9ac8b", "#bd8d6e", "#e8c2a4", "#98d1b8", "#70ad93", "#b8e5d0", "#3a2a1c", "#4a3326")


def medic2():
    return _medic(True, "#9a6a4c", "#7e5139", "#b07e5e", "#6cc0c4", "#4c9ca3", "#92dadc", "#1f2c46", "#2a1c14")


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


