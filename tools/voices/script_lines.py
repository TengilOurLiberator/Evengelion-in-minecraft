"""Parse D:\\angel-attack\\script.md and write one reading sheet per character.

    python script_lines.py                      # writes recording\\<SPEAKER>.md for every speaker
    python script_lines.py --check              # parse only, print counts and problems
    python script_lines.py --script x.md --out some\\dir

Spoken lines are single markdown lines of the form
    **MISATO** `2.01` Misato Katsuragi. Captain, technically. *(over the phone)*
Everything else (headings, "> " notes, stage directions) is not spoken. A trailing italic parenthetical is a
direction: it is removed from the spoken text and kept as metadata ("direction").
"""
import argparse
import os
import re
import sys

LINE_RE = re.compile(r"^\*\*(MISATO|RITSUKO|GENDO|REI|BASE)\*\* `(\d+\.\d\d)` (.+)$")
LOOSE_RE = re.compile(r"^\s*\*\*(MISATO|RITSUKO|GENDO|REI|BASE)\*\*", re.I)   # looks like a line, for warnings
DIRECTION_RE = re.compile(r"\*\(([^)]*)\)\*")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

SPEAKERS = ["MISATO", "RITSUKO", "GENDO", "REI", "BASE"]
DESCRIPTIONS = {
    "MISATO": "woman, late twenties, bright, quick, warm, a little rough",
    "RITSUKO": "woman, thirty, level, dry, precise",
    "GENDO": "man, late forties, low, slow, hard, almost no inflection",
    "REI": "girl of fourteen, very soft, breathy, flat",
    "BASE": "the base computer / PA voice, monotone",
}


def _clean_text(s):
    s = s.replace("\\*", "\u0001")                      # keep escaped asterisks
    s = re.sub(r"(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)", r"\1", s)     # *emphasis* -> emphasis
    s = re.sub(r"\*\*([^*]+?)\*\*", r"\1", s)
    s = re.sub(r"(?<![\w])_([^_]+?)_(?![\w])", r"\1", s)
    s = s.replace("\u0001", "*")
    return re.sub(r"\s+", " ", s).strip()


def parse(path=None, warn=None):
    """Return [{id, speaker, text, direction, scene, scene_title, scene_note, cue, line_no}] in file order."""
    if path is None:
        import common
        path = common.SCRIPT_MD
    warn = warn or (lambda m: None)
    lines, seen = [], {}
    scene_title = scene_note = last_note = ""
    block = []
    prev = None
    with open(path, encoding="utf-8-sig") as f:
        for no, raw in enumerate(f, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if line.startswith(">"):                 # a note about what happens in the world; blocks of them are joined
                block.append(_clean_text(line.lstrip("> ").strip()))
                continue
            if block and line.strip():               # the note block just ended
                last_note = " ".join(block)
                scene_note = scene_note or last_note
                block = []
            h = HEADING_RE.match(line)
            if h:
                scene_title, scene_note, last_note = h.group(2).strip(), "", ""
                continue
            m = LINE_RE.match(line)
            if not m:
                if LOOSE_RE.match(line):
                    warn(f"line {no}: looks like a spoken line but does not match the format: {line[:70]}")
                continue
            speaker, lid, body = m.groups()
            dirs = [d.strip() for d in DIRECTION_RE.findall(body)]
            text = _clean_text(DIRECTION_RE.sub("", body))
            if lid in seen:
                warn(f"line {no}: id {lid} is used twice (first at line {seen[lid]})")
            seen[lid] = no
            # A line that is only a direction ("*(No words. One long breath...)*") is a non-verbal sound.
            rec = {"id": lid, "speaker": speaker, "text": text, "nonverbal": not text,
                   "direction": "; ".join(d for d in dirs if d),
                   "scene": lid.split(".")[0], "scene_title": scene_title, "scene_note": scene_note, "world": last_note,
                   "cue": ("%s: %s" % (prev["speaker"].title(), prev["text"])) if prev else "", "line_no": no}
            lines.append(rec)
            prev, last_note = rec, ""
    return lines


def lines_for(speaker, lines):
    return [l for l in lines if l["speaker"] == speaker]


def _short(s, n=110):
    return s if len(s) <= n else s[:n - 1].rstrip() + "\u2026"


def _sentences(s, n):
    """Whole sentences of s up to about n characters."""
    if len(s) <= n:
        return s
    cut = s[:n]
    k = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return cut[:k + 1] if k > 40 else cut.rstrip() + "\u2026"


def sheet_markdown(speaker, lines):
    mine = lines_for(speaker, lines)
    out = [f"# {speaker}", "", f"**Voice:** {DESCRIPTIONS[speaker]}.  **Lines:** {len(mine)}", "",
           "**How to record**", "",
           "- Read in your own natural voice, at your own pitch. Do not try to sound like the character: the voice is "
           "changed afterwards. Put the *feeling* in (the rushing, the dryness, the quiet); leave the voice alone.",
           "- Read every line top to bottom, in order. Leave a clear pause of about two seconds after each line.",
           "- If you flub a line, stop, wait the two seconds, and read it again from its beginning. The last good "
           "take is the one that is kept. Do not read the line number, the scene, or the small print under a line.",
           "- Read what is written. The text in (brackets) after a line is how it is heard in the game, not something "
           "to say.", "", "---", ""]
    cur = None
    for l in mine:
        if l["scene"] != cur:
            cur = l["scene"]
            title = l["scene_title"] or f"Scene {cur}"
            out += [f"## {title}" if title.lower().startswith("scene") else f"## Scene {cur}  \u2014  {title}", ""]
            if l["scene_note"]:
                out += [f"*{_sentences(l['scene_note'], 230)}*", ""]
        ctx = []
        if l["world"] and l["world"] != l["scene_note"]:
            ctx.append(f"in the story: {_sentences(l['world'], 200)}")
        if l["cue"]:
            ctx.append(f"cue \u2014 {_short(l['cue'])}")
        if l["nonverbal"]:
            out.append(f"### `{l['id']}`  \u2014  no words")
            out.append("")
            out.append(f"# *{l['direction']}*")
            out.append("")
            out.append("<sub>Make the sound once, close to the microphone. Nothing is said.</sub>")
            out.append("")
        else:
            out.append(f"### `{l['id']}`" + (f"  \u2014  *({l['direction']})*" if l["direction"] else ""))
            out.append("")
            out.append(f"# {l['text']}")
            out.append("")
        if ctx:
            out.append("<sub>" + "; ".join(ctx) + "</sub>")
            out.append("")
        out += ["---", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", help="script.md (default D:\\angel-attack\\script.md)")
    ap.add_argument("--out", help="folder for the sheets (default D:\\angel-attack\\recording)")
    ap.add_argument("--check", action="store_true", help="parse and report only; write nothing")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common
    script = a.script or common.SCRIPT_MD
    if not os.path.exists(script):
        sys.exit(f"{script} does not exist yet")
    problems = []
    lines = parse(script, warn=problems.append)
    ids = [l["id"] for l in lines]
    for p in problems:
        print("WARNING:", p)
    print(f"{len(lines)} spoken lines in {script}")
    for s in SPEAKERS:
        mine = lines_for(s, lines)
        words = sum(len(l["text"].split()) for l in mine)
        dirs = sum(1 for l in mine if l["direction"])
        print(f"  {s:8} {len(mine):4} lines  {words:5} words  {dirs:3} with a direction")
    dirs = sorted({l["direction"] for l in lines if l["direction"]})
    if dirs:
        print("directions in use:", "; ".join(dirs))
    if a.check:
        return
    out = a.out or common.RECORDING_DIR
    os.makedirs(out, exist_ok=True)
    for s in SPEAKERS:
        if not lines_for(s, lines):
            continue
        p = os.path.join(out, f"{s}.md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(sheet_markdown(s, lines))
        print("wrote", p)


if __name__ == "__main__":
    main()
