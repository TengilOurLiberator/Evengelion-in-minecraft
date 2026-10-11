"""Mean brightness of pictures, to compare shots numerically (e.g. a room at two times of day).

    python tools\\visual\\measure.py shot1.png shot2.png ...     mean R, G, B and mean luma (0-255) of each picture

Luma is 0.2126 R + 0.7152 G + 0.0722 B over the sRGB values as stored (what the eye reads off the picture).
"""
import sys

import numpy as np
from PIL import Image


def stats(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
    r, g, b = (a[..., i].mean() for i in range(3))
    return r, g, b, 0.2126 * r + 0.7152 * g + 0.0722 * b


if __name__ == "__main__":
    for p in sys.argv[1:]:
        r, g, b, y = stats(p)
        print(f"{y:7.2f}  rgb({r:6.2f} {g:6.2f} {b:6.2f})  {p}")
