"""Check function-file lines against the game's own command tree (commands.json from the data generator).

This is a structural check, not a full parser: it follows the Brigadier tree (literals, arguments, redirects such as
`execute ... run <command>`), counts the tokens each argument takes (three for a block position, selectors and NBT
count as one however many spaces they hold) and checks numbers, booleans and times. It does not look inside NBT, selectors
or JSON text, and it does not know whether a resource (a function, a structure, a biome) exists. Lines that begin with
`$` (macros) are skipped.
"""
import re

import mcdata

_NUM = re.compile(r"^-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_INT = re.compile(r"^-?\d+$")
_COORD = re.compile(r"^(~|\^)?(-?(\d+\.?\d*|\.\d+))?$")
_TIME = re.compile(r"^(\d+\.?\d*|\.\d+)[dst]?$")
_BOOL = ("true", "false")

# tokens consumed by argument parsers that take more than one
_WIDTH = {"minecraft:block_pos": 3, "minecraft:vec3": 3, "minecraft:column_pos": 2, "minecraft:vec2": 2, "minecraft:rotation": 2}
_REST = {"minecraft:message"}


def tokenize(line):
    """Split on spaces that are not inside [], {}, () or quotes."""
    toks, cur, depth, quote, esc = [], [], 0, None, False
    for ch in line:
        if quote:
            cur.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "[{(":
            depth += 1
            cur.append(ch)
        elif ch in "]})":
            depth -= 1
            cur.append(ch)
        elif ch == " " and depth <= 0:
            if cur:
                toks.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
    if cur:
        toks.append("".join(cur))
    if quote or depth != 0:
        raise ValueError("unbalanced brackets or quotes")
    return toks


def _arg_take(node, toks, i):
    """How many tokens this argument node takes at position i, or None if the text does not fit it."""
    parser = node.get("parser", "")
    props = node.get("properties", {})
    if i >= len(toks):
        return None
    t = toks[i]
    if parser == "brigadier:bool":
        return 1 if t in _BOOL else None
    if parser in ("brigadier:integer", "brigadier:long"):
        if not _INT.match(t):
            return None
        v = int(t)
        if ("min" in props and v < props["min"]) or ("max" in props and v > props["max"]):
            return None
        return 1
    if parser in ("brigadier:float", "brigadier:double"):
        if not _NUM.match(t):
            return None
        v = float(t)
        if ("min" in props and v < props["min"]) or ("max" in props and v > props["max"]):
            return None
        return 1
    if parser == "brigadier:string":
        return len(toks) - i if props.get("type") == "greedy" else 1
    if parser in _REST:
        return len(toks) - i
    if parser == "minecraft:time":
        return 1 if _TIME.match(t) or _INT.match(t) else None
    n = _WIDTH.get(parser)
    if n:
        if i + n > len(toks) or not all(_COORD.match(x) for x in toks[i:i + n]):
            return None
        return n
    if parser == "minecraft:angle":
        return 1 if _COORD.match(t) else None
    if parser in ("minecraft:resource_location", "minecraft:function", "minecraft:dimension"):
        return 1 if re.match(r"^#?[a-z0-9_.\-]+(:[a-z0-9_./\-]+)?$", t) else None
    return 1                                 # selectors, NBT, blocks, items, components: one token


class Checker:
    def __init__(self):
        self.root = mcdata.commands()
        # the report leaves out where `execute ... run` and `return run` go (back to the start of the tree); put it in
        for cmd in ("execute", "return"):
            run = self.root["children"][cmd]["children"].get("run")
            if run is not None:
                run.setdefault("redirect", [])

    def _children(self, node):
        if "redirect" in node:
            target = self.root
            for step in node["redirect"]:
                target = target["children"][step]
            return target.get("children", {})
        return node.get("children", {})

    def _walk(self, node, toks, i, depth=0):
        """None if the tokens from i on are a valid continuation of node, else the message of the furthest failure."""
        if i == len(toks):
            if node.get("executable"):
                return None
            return "the command is incomplete"
        kids = self._children(node)
        best = None
        t = toks[i]
        if t in kids and kids[t]["type"] == "literal":
            r = self._walk(kids[t], toks, i + 1, depth + 1)
            if r is None:
                return None
            best = r
        for name, kid in kids.items():
            if kid["type"] != "argument":
                continue
            n = _arg_take(kid, toks, i)
            if n is None:
                if best is None:
                    best = f"{toks[i]!r} is not a valid {name} ({kid.get('parser', '')})"
                continue
            r = self._walk(kid, toks, i + n, depth + 1)
            if r is None:
                return None
            best = r
        if best is None:
            best = f"unexpected {t!r}" + ("" if kids else " (nothing may follow)")
        return best

    def check(self, line):
        """None if fine, else a message."""
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("$"):
            return None
        if line.startswith("/"):
            return "a function line must not start with a slash"
        try:
            toks = tokenize(line)
        except ValueError as e:
            return str(e)
        return self._walk(self.root, toks, 0)


def check_functions(functions, checker=None):
    """functions: {path: [lines]} -> [(path, line number, line, message)]"""
    checker = checker or Checker()
    bad = []
    for path, lines in functions.items():
        for n, line in enumerate(lines, 1):
            msg = checker.check(line)
            if msg:
                bad.append((path, n, line, msg))
    return bad
