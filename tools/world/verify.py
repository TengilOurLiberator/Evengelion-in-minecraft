"""Checks on compiled output: read every generated structure file (or replay every generated fill/setblock) back and
compare it with the canvas it came from."""
import gzip
import re

import numpy as np

import cmdcheck
import compile as comp
import mcdata
import nbt

_TAIL = nbt.named("entities", nbt.List(nbt.COMPOUND, [])) + b"\x00"
_EMPTY_BLOCKS = b"\x09\x00\x06blocks\x0a\x00\x00\x00\x00"
_BLOCKS_HEAD = len(b"\x09\x00\x06blocks\x0a") + 4


def expected(w, cs):
    """The canvas as compact ids, with the cells the compiler is allowed to leave out set to 0."""
    names, lut = comp.canon_table(w)
    full = lut[w.a].astype(np.uint32)
    if cs.air == "drop":
        full = np.where(full > 1, full, 0)
    return full, names


def _palette_names(root):
    return [e["id"] + ("[" + ",".join(f"{k}={e['properties'][k]}" for k in sorted(e["properties"])) + "]" if e.get("properties") else "")
            for e in root["palette"]]


def _fast_read(raw, n):
    """Read a structure written by encode_structure without building n Python dicts: the head (palette, size, version)
    with the general reader, the n fixed-size block records with numpy. Also checks the record layout byte for byte."""
    end = len(raw) - len(_TAIL)
    assert raw.endswith(_TAIL)
    start = end - 36 * n
    head = raw[:start - _BLOCKS_HEAD]
    root = nbt.loads(head + _EMPTY_BLOCKS + _TAIL)
    assert raw[start - _BLOCKS_HEAD:start] == b"\x09\x00\x06blocks\x0a" + n.to_bytes(4, "big")
    rec = np.frombuffer(raw[start:end], dtype=np.uint8).reshape(n, 36)
    fixed = np.frombuffer(bytes([3, 0, 5]) + b"state", dtype=np.uint8)
    assert (rec[:, :8] == fixed).all()
    assert (rec[:, 12:23] == np.frombuffer(bytes([9, 0, 3]) + b"pos" + bytes([3, 0, 0, 0, 3]), dtype=np.uint8)).all() and (rec[:, 35] == 0).all()
    state = rec[:, 8:12].copy().view(">i4").ravel()
    pos = np.stack([rec[:, o:o + 4].copy().view(">i4").ravel() for o in (23, 27, 31)], axis=1)
    return root, state, pos


def replay_structures(w, cs, generic_limit=400_000):
    """Rebuild an id canvas from the structure files. Tiles are read with the general NBT reader until
    `generic_limit` blocks have gone through it, the rest with the numpy reader (same layout checks)."""
    ids = {n: i for i, n in enumerate(cs.names) if n}
    out = np.zeros(w.size, dtype=np.uint32)
    dv = mcdata.data_version()
    read = 0
    for t in cs.tiles:
        raw = gzip.decompress(cs.structures[t.file])
        if read < generic_limit:
            read += t.blocks
            root = nbt.loads(raw)
            assert len(root["blocks"]) == t.blocks, t.file
            pal = _palette_names(root)
            state = np.array([int(b["state"]) for b in root["blocks"]], dtype=np.int64)
            pos = np.array([[int(v) for v in b["pos"]] for b in root["blocks"]], dtype=np.int64).reshape(-1, 3)
        else:
            root, state, pos = _fast_read(raw, t.blocks)
            pal = _palette_names(root)
        assert root["DataVersion"] == dv, (t.file, root["DataVersion"])
        assert [int(v) for v in root["size"]] == [t.hi[i] - t.lo[i] + 1 for i in range(3)], t.file
        assert all(isinstance(v, nbt.Int) for v in root["size"]) and all(isinstance(e["id"], str) for e in root["palette"])
        lut = np.array([ids[p] for p in pal], dtype=np.uint32)
        o = np.array([t.lo[i] - w.origin[i] for i in range(3)])
        p = pos + o
        out[p[:, 0], p[:, 1], p[:, 2]] = lut[state]
    return out


_FILL = re.compile(r"^fill (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (\S+)$")
_SET = re.compile(r"^setblock (-?\d+) (-?\d+) (-?\d+) (\S+)$")


def replay_commands(w, cs, commands):
    """Paint fill/setblock command text onto an empty canvas of ids."""
    ids = {n: i for i, n in enumerate(cs.names) if n}
    out = np.zeros(w.size, dtype=np.uint32)
    ox, oy, oz = w.origin
    for c in commands:
        m = _FILL.match(c)
        if m:
            x1, y1, z1, x2, y2, z2 = (int(v) for v in m.groups()[:6])
            blk = m.group(7)
        else:
            m = _SET.match(c)
            if not m:
                raise AssertionError(f"not a fill or setblock: {c}")
            x1 = x2 = int(m.group(1))
            y1 = y2 = int(m.group(2))
            z1 = z2 = int(m.group(3))
            blk = m.group(4)
        out[x1 - ox:x2 - ox + 1, y1 - oy:y2 - oy + 1, z1 - oz:z2 - oz + 1] = ids[blk]
    return out


def check_set(w, cs):
    """Compare the compiled set with its canvas. Returns (problems, cells checked)."""
    want, names = expected(w, cs)
    if cs.method == "template":
        got = replay_structures(w, cs)
    else:
        got = replay_commands(w, cs, [c for t in cs.tiles for c in t.cmds])
    problems = []
    bad = np.argwhere(got != want)
    if len(bad):
        x, y, z = bad[0]
        problems.append(f"{cs.name}: {len(bad)} cells differ, first at {tuple(int(v) for v in bad[0])}: "
                        f"canvas {cs.names[want[x, y, z]]!r}, compiled {cs.names[got[x, y, z]]!r}")
    return problems, int((want > 0).sum())


def check_functions(functions):
    """Run every generated function line through the command-tree check. functions: {path: [lines]}."""
    return cmdcheck.check_functions(functions)
