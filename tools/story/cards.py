"""Title cards: white capitals on black, readable in a VR headset and on a flat screen.

    s.card("EVANGELION  UNIT 01")                              # the card, held 3.5 s in silence after its hit
    s.card("TO BE CONTINUED", small="an unofficial fan work")  # with a small line under it
    s.card("ANGEL ATTACK", hold=2.0, back=2, back_wait=0.2)    # two seconds, then a quick return to the same view

Why not `title`: in Vivecraft the title is part of the HUD, which is drawn on a floating quad whose place and visibility depend on the
player's own settings (locked to the hand or the head, occluded by closer objects, dimmed); with the world blacked out by blindness it can
be anywhere or nowhere.  So the card is built in the world instead, around the player, and works the same in VR and on a flat screen:

  * a closed black room of six thin black slabs (block displays), 2.6 blocks to each side of the player's position at the moment of the
    card, on and above the floor he stands on; nothing of the set shows through it;
  * the text as `text_display` entities, fully bright, billboarded to face the viewer, 2.2 blocks from the player's eyes at eye height,
    FOUR copies 90 degrees apart (the server cannot know which way a headset is looking at that moment; one copy is always in front);
  * nothing follows the head: the card hangs in the room, so there is nothing to swim in the stereo image.

The sequence: the world goes dark with blindness (instantly), the room is built in the dark, blindness is cleared (the viewer sees only
black, the room hiding the world), the sound event angel:sfx.card plays and the text appears at the same instant, it is held in silence,
then blindness is applied again, the room and the text are removed in the dark and the story goes on (the next scene fades in from black
by itself).  There is no serif font in vanilla Minecraft: the text uses the resource pack's font "angel:card" (cardfont.py builds it from an
openly licensed Computer Modern: bold, condensed, widely spaced capitals, and a lighter lower case for the small line), already bold, so
the component says bold:false (the game's own bold would draw every glyph twice, offset).  The scale is computed from the font's real
advances, so every card is about TARGET_WIDTH blocks wide whatever its length.
"""
import json

import cardfont
from core import NS, P, PA, TAG, num, fnum

ROOM = 2.6                         # half-size of the black room
DIST = 2.2                         # distance of the text from the eyes
WIDTH_PX = 6.4                     # estimated width of a vanilla bold capital in pixels (for text in another font)
TARGET_WIDTH = 2.6                 # blocks the main line should span at that distance (about 62 degrees)
SMALL_RATIO = 0.8                  # the small line spans this fraction of that
CARD_FONT = cardfont.FONT_ID


def _units(text, font):
    """Width of the text in font units: the real advances of the card font, or a vanilla-width estimate for anything else."""
    if font == CARD_FONT and cardfont.covers(text):
        return float(cardfont.advance_units(text))
    return max(1, len(text)) * WIDTH_PX


def _auto_scale(text, target=TARGET_WIDTH, lo=0.35, hi=1.7, font=CARD_FONT):
    return max(lo, min(hi, target / (_units(text, font) * 0.025)))


def _text_display(comp, scale, dy, rot_yaw):
    t = (f'summon minecraft:text_display ~ ~ ~ {{Tags:["{TAG}","angel.card","angel.card_text"],billboard:"center",background:0,'
         f'brightness:{{sky:15,block:15}},line_width:4000,shadow:0b,see_through:0b,alignment:"center",view_range:3.0f,'
         f'text:{json.dumps(comp, ensure_ascii=True)},'
         f'transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[{fnum(scale)},{fnum(scale)},{fnum(scale)}],right_rotation:[0f,0f,0f,1f]}}}}')
    return (f"execute as {P()} at @s anchored eyes rotated ~{int(rot_yaw)} 0 positioned ^ ^{num(dy)} ^{num(DIST)} run {t}")


def room_commands(radius=ROOM):
    """Six black slabs around the player's feet (the commands are run by the server; they place themselves at the player)."""
    r, h = radius, radius * 2.0
    th = 0.12
    cmds = []
    # name, translation (from the entity at the player's feet), scale
    slabs = [("floor", (-r - th, 0.03, -r - th), (2 * r + 2 * th, th, 2 * r + 2 * th)),
             ("top", (-r - th, h, -r - th), (2 * r + 2 * th, th, 2 * r + 2 * th)),
             ("east", (r, 0.03, -r - th), (th, h, 2 * r + 2 * th)),
             ("west", (-r - th, 0.03, -r - th), (th, h, 2 * r + 2 * th)),
             ("south", (-r - th, 0.03, r), (2 * r + 2 * th, h, th)),
             ("north", (-r - th, 0.03, -r - th), (2 * r + 2 * th, h, th))]
    for name, t, s in slabs:
        cmds.append(f'execute at {P()} run summon minecraft:block_display ~ ~ ~ {{Tags:["{TAG}","angel.card","angel.card_bg"],'
                    f'block_state:"minecraft:black_concrete",brightness:{{sky:0,block:0}},view_range:3.0f,'
                    f'transformation:{{translation:[{fnum(t[0])},{fnum(t[1])},{fnum(t[2])}],left_rotation:[0f,0f,0f,1f],'
                    f'scale:[{fnum(s[0])},{fnum(s[1])},{fnum(s[2])}],right_rotation:[0f,0f,0f,1f]}}}}')
    return cmds


def card_index(ctx, text, small, font, bold, color):
    font = font or CARD_FONT
    if bold is None:
        bold = font != CARD_FONT                    # the card font is bold already
    key = (text, small, font, bool(bold), color)
    if key not in ctx.cards:
        ctx.cards[key] = len(ctx.cards) + 1
        k = ctx.cards[key]
        if font == CARD_FONT:
            for t in (text, small or ""):
                if not cardfont.covers(t):
                    raise ValueError(f"card text {t!r} has characters that the card font does not have")
        comp = {"text": text, "color": color, "bold": bool(bold), "font": font}
        sc_main = _auto_scale(text, font=font)
        lines = []
        for r in (0, 90, 180, 270):
            lines.append(_text_display(comp, sc_main, 0.07 if small else 0.0, r))
            if small:
                c2 = {"text": small, "color": "gray", "bold": False, "font": font}
                sc_small = _auto_scale(small, TARGET_WIDTH * SMALL_RATIO, 0.25, 0.9, font=font)
                lines.append(_text_display(c2, sc_small, 0.07 - (0.125 * sc_main + 0.2), r))
        ctx.extra_functions[f"story/card/c{k}"] = lines
        ctx.extra_functions["story/card/bg"] = room_commands()
        ctx.extra_functions["story/card/off_text"] = ["kill @e[tag=angel.card_text]"]
        ctx.extra_functions["story/card/off"] = ["kill @e[tag=angel.card]"]
    return ctx.cards[key]
