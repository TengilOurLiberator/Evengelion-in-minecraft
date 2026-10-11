"""A small NBT reader and writer (big-endian, gzip), enough for Minecraft structure files.

Types are kept by subclassing, so a value read back is of the same tag type it was written as:

    Byte, Short, Int, Long   (int subclasses)      Float, Double (float subclasses)
    str                      TAG_String            dict   TAG_Compound
    List(tag_id, items)      TAG_List              ByteArray / IntArray / LongArray (list subclasses)

`dumps(root)` / `loads(data)` work on the raw bytes, `save(path, root)` / `load(path)` on gzip files.
"""
import gzip
import struct

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTE_ARRAY, STRING, LIST, COMPOUND, INT_ARRAY, LONG_ARRAY = range(13)


class Byte(int): pass
class Short(int): pass
class Int(int): pass
class Long(int): pass
class Float(float): pass
class Double(float): pass
class ByteArray(list): pass
class IntArray(list): pass
class LongArray(list): pass


class List(list):
    """A TAG_List: all items are of one tag type (`tag_id`), even when empty."""

    def __init__(self, tag_id=END, items=()):
        super().__init__(items)
        self.tag_id = tag_id

    def __eq__(self, other):
        return isinstance(other, List) and list.__eq__(self, other) and (len(self) == 0 or self.tag_id == other.tag_id)

    __hash__ = None


_FMT = {BYTE: ">b", SHORT: ">h", INT: ">i", LONG: ">q", FLOAT: ">f", DOUBLE: ">d"}
_CLS = {BYTE: Byte, SHORT: Short, INT: Int, LONG: Long, FLOAT: Float, DOUBLE: Double}


def tag_id_of(v):
    if isinstance(v, Byte): return BYTE
    if isinstance(v, Short): return SHORT
    if isinstance(v, Int): return INT
    if isinstance(v, Long): return LONG
    if isinstance(v, Float): return FLOAT
    if isinstance(v, Double): return DOUBLE
    if isinstance(v, ByteArray): return BYTE_ARRAY
    if isinstance(v, IntArray): return INT_ARRAY
    if isinstance(v, LongArray): return LONG_ARRAY
    if isinstance(v, str): return STRING
    if isinstance(v, List): return LIST
    if isinstance(v, dict): return COMPOUND
    raise TypeError(f"not an NBT value: {v!r} ({type(v).__name__})")


def _str(s):
    b = s.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def _payload(v, out):
    t = tag_id_of(v)
    if t in _FMT:
        out.append(struct.pack(_FMT[t], v))
    elif t == STRING:
        out.append(_str(v))
    elif t == BYTE_ARRAY:
        out.append(struct.pack(">i", len(v)) + struct.pack(f">{len(v)}b", *v))
    elif t == INT_ARRAY:
        out.append(struct.pack(">i", len(v)) + struct.pack(f">{len(v)}i", *v))
    elif t == LONG_ARRAY:
        out.append(struct.pack(">i", len(v)) + struct.pack(f">{len(v)}q", *v))
    elif t == LIST:
        out.append(struct.pack(">bi", v.tag_id, len(v)))
        for item in v:
            if tag_id_of(item) != v.tag_id:
                raise TypeError(f"list of tag {v.tag_id} holds a tag {tag_id_of(item)}")
            _payload(item, out)
    else:  # compound
        for k, item in v.items():
            out.append(struct.pack(">b", tag_id_of(item)))
            out.append(_str(k))
            _payload(item, out)
        out.append(b"\x00")


def named(name, value):
    """One named tag inside a compound: tag id, name, payload."""
    out = [struct.pack(">b", tag_id_of(value)), _str(name)]
    _payload(value, out)
    return b"".join(out)


def dumps(root, name=""):
    """The raw (uncompressed) bytes of a named root compound."""
    if not isinstance(root, dict):
        raise TypeError("the root of an NBT file is a compound")
    out = [struct.pack(">b", COMPOUND), _str(name)]
    _payload(root, out)
    return b"".join(out)


class _Reader:
    def __init__(self, data):
        self.d, self.p = data, 0

    def take(self, n):
        b = self.d[self.p:self.p + n]
        if len(b) != n:
            raise ValueError("NBT data ends too soon")
        self.p += n
        return b

    def unpack(self, fmt, n):
        return struct.unpack(fmt, self.take(n))

    def string(self):
        (n,) = self.unpack(">H", 2)
        return self.take(n).decode("utf-8")

    def payload(self, t):
        if t in _FMT:
            fmt = _FMT[t]
            return _CLS[t](self.unpack(fmt, struct.calcsize(fmt))[0])
        if t == STRING:
            return self.string()
        if t in (BYTE_ARRAY, INT_ARRAY, LONG_ARRAY):
            (n,) = self.unpack(">i", 4)
            code, size, cls = {BYTE_ARRAY: ("b", 1, ByteArray), INT_ARRAY: ("i", 4, IntArray), LONG_ARRAY: ("q", 8, LongArray)}[t]
            return cls(struct.unpack(f">{n}{code}", self.take(n * size)))
        if t == LIST:
            tid, n = self.unpack(">bi", 5)
            return List(tid, [self.payload(tid) for _ in range(n)])
        if t == COMPOUND:
            out = {}
            while True:
                (tid,) = self.unpack(">b", 1)
                if tid == END:
                    return out
                name = self.string()
                out[name] = self.payload(tid)
        raise ValueError(f"unknown NBT tag {t}")


def loads(data):
    r = _Reader(data)
    (t,) = r.unpack(">b", 1)
    if t != COMPOUND:
        raise ValueError("an NBT file starts with a compound")
    r.string()
    root = r.payload(COMPOUND)
    if r.p != len(data):
        raise ValueError(f"{len(data) - r.p} bytes left over after the root compound")
    return root


def compress(raw, level=6):
    return gzip.compress(raw, compresslevel=level, mtime=0)


def save(path, root, level=6):
    with open(path, "wb") as f:
        f.write(compress(dumps(root), level))


def load(path):
    with open(path, "rb") as f:
        return loads(gzip.decompress(f.read()))
