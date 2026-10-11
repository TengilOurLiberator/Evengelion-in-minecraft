"""Build the cast: the in-world characters (mannequin entities with our own skins), their walking, looking, posing,
riding, and the hospital gurney, as datapack functions plus the skin textures for the resource pack.

    python build_cast.py                 draw the skins, write textures and functions, check them, write the manifest
    python build_cast.py --preview       also render preview\\sheet.png (every skin, four angles, far view)
    python build_cast.py --check         build into a temporary folder and only check (writes nothing)
    python build_cast.py --out DIR       write the datapack part to DIR\\datapack\\angel and the textures to DIR\\pack\\angel-resources (test copy)

Use the Python of the D:\\voice-assistant environment (numpy, pillow).

Writes (and lists in tools\\cast\\build_manifest.json, so that a later build removes only what it wrote before):
    datapack\\angel\\data\\angel\\function\\cast\\...                 the API and its helpers (see README.md)
    pack\\angel-resources\\assets\\angel\\textures\\entity\\cast\\*.png    one skin per character
Nothing else is touched (not pack.mcmeta, not the function tags, not sounds.json).
"""
import argparse
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TOOLS, "world"))

import skins as skinlib          # noqa: E402

NS = "angel"
OBJ = "angel.cast"
DP_ROOT = os.path.join(ROOT, "datapack", "angel")
RP_ROOT = os.path.join(ROOT, "pack", "angel-resources")
FN_DIR = "data/angel/function/cast"
TEX_DIR = "assets/angel/textures/entity/cast"
MANIFEST = os.path.join(HERE, "build_manifest.json")
PREVIEW = os.path.join(HERE, "preview")

# id -> (tags besides angel.cast and angel.<id>, slim model)
CAST = {
    "misato": (["angel.char"], True),
    "ritsuko": (["angel.char"], True),
    "gendo": (["angel.char"], False),
    "rei": (["angel.char"], True),
    "rei_uniform": (["angel.char"], True),
    "medic1": (["angel.medic"], False),
    "medic2": (["angel.medic"], True),
}
IDS = list(CAST)
MAN = "type=minecraft:mannequin"

fns = {}                                   # path (under cast/) -> list of lines


def fn(path, *lines):
    fns[path] = [ln for block in lines for ln in (block if isinstance(block, list) else [block])]


def msel(inner):
    return f"@e[{MAN},{inner}]"


def sel(i, extra=""):
    return f"@e[{MAN},tag=angel.{i}{extra}]"


# ---------------------------------------------------------------------------------------------------------------------
# load, tick
# ---------------------------------------------------------------------------------------------------------------------
fn("load",
   f"scoreboard objectives add {OBJ} dummy",
   "team add angel.cast",
   "team modify angel.cast collisionRule never",
   "team modify angel.cast nametagVisibility never",
   "team modify angel.cast friendlyFire false",
   f"scoreboard players set #k36000 {OBJ} 36000",
   f"scoreboard players set #k1000 {OBJ} 1000",
   f"scoreboard players set #k2 {OBJ} 2",
   f"scoreboard players set #km1 {OBJ} -1",
   f"execute unless score #active {OBJ} matches 0.. run scoreboard players set #active {OBJ} 0",
   f"execute unless score #gmove {OBJ} matches 0.. run scoreboard players set #gmove {OBJ} 0")

fn("tick",
   f"execute unless score #active {OBJ} matches 1 run return 0",
   f"function {NS}:cast/tick_all")

fn("tick_all",
   [f"execute if score #on_{i} {OBJ} matches 1 run function {NS}:cast/tick/{i}" for i in IDS],
   f"execute if score #gmove {OBJ} matches 1 run function {NS}:cast/gm_step",
   f"scoreboard players add #idle {OBJ} 1",
   f"execute if score #idle {OBJ} matches 100.. run function {NS}:cast/idle_check")

# every 5 seconds: if nothing of the cast is left, stop doing any work at all
fn("idle_check",
   f"scoreboard players set #idle {OBJ} 0",
   f"execute unless entity @e[tag=angel.cast,limit=1] run scoreboard players set #active {OBJ} 0")

# ---------------------------------------------------------------------------------------------------------------------
# summon / remove
# ---------------------------------------------------------------------------------------------------------------------
fn("summon", f"$function {NS}:cast/spawn/$(id)")
for i, (extra, slim) in CAST.items():
    tags = ",".join(f'"{t}"' for t in ["angel.cast", *extra, f"angel.{i}"])
    nbt = (f'{{Tags:[{tags}],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,'
           f'profile:{{texture:"angel:entity/cast/{i}",model:"{"slim" if slim else "wide"}"}},'
           f'attributes:[{{id:"minecraft:step_height",base:1.0d}}]}}')
    fn(f"spawn/{i}",
       f"execute as {sel(i)} run function {NS}:cast/vanish",
       f"kill @e[type=minecraft:armor_stand,tag=angel.autoseat_{i}]",
       f"summon minecraft:mannequin ~ ~ ~ {nbt}",
       f"tp {sel(i)} ~ ~ ~ ~ 0",
       f"team join angel.cast {sel(i)}",
       f"scoreboard players set #on_{i} {OBJ} 1",
       f"scoreboard players set #walk_{i} {OBJ} 0",
       f"scoreboard players set #look_{i} {OBJ} 1",
       f"scoreboard players set #arrived_{i} {OBJ} 0",
       f"scoreboard players set #np_{i} {OBJ} 0",
       f"scoreboard players set #active {OBJ} 1")

# Removing a mannequin with `kill` plays the death fall with the red flash, and if the world is saved in the
# half second it takes the server logs "Invalid pose: dying". So: take its tags away (nobody finds it any more),
# put it 2000 blocks below the world where nobody can see it, give it a death time of 19 (it is removed one tick
# after dying instead of twenty) and kill it there.
fn("vanish",                           # as the mannequin, anywhere
   "ride @s dismount",
   "effect clear @s",
   'data merge entity @s {DeathTime:19s,Tags:["angel.gone"],NoGravity:1b,Silent:1b}',
   "execute at @s run tp @s ~ -2000 ~",
   "kill @s")

fn("remove",
   f"$execute as @e[{MAN},tag=angel.$(id)] run function {NS}:cast/vanish",
   "$kill @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id)]",
   f"$scoreboard players set #on_$(id) {OBJ} 0",
   f"$scoreboard players set #walk_$(id) {OBJ} 0",
   f"$scoreboard players set #look_$(id) {OBJ} 0",
   f"$scoreboard players set #arrived_$(id) {OBJ} 0",
   f"$scoreboard players set #np_$(id) {OBJ} 0")

fn("remove_all",
   f"execute as @e[{MAN},tag=angel.cast] run function {NS}:cast/vanish",
   "kill @e[tag=angel.cast]",
   [f"scoreboard players set #{k}_{i} {OBJ} 0" for i in IDS for k in ("on", "walk", "look", "arrived", "np")],
   f"scoreboard players set #arrived_gurney {OBJ} 0",
   f"scoreboard players set #gmove {OBJ} 0",
   f"scoreboard players set #active {OBJ} 0",
   "data remove storage angel:cast walk",
   "data remove storage angel:cast gm")

# bigger (or smaller) characters, e.g. Gendo seen from far below: the `scale` attribute (0.0625 .. 16). A fresh summon
# is back at 1. Not compensated: the 0.9 / 0.125 shift of the lying pose (lie standing characters only).
fn("scale", "$attribute @e[type=minecraft:mannequin,tag=angel.$(id),limit=1] minecraft:scale base set $(scale)")

# ---------------------------------------------------------------------------------------------------------------------
# looking
# ---------------------------------------------------------------------------------------------------------------------
fn("look", f"$function {NS}:cast/look_$(mode) {{id:\"$(id)\"}}")
fn("look_player", f"$scoreboard players set #look_$(id) {OBJ} 1")
fn("look_ahead", f"$scoreboard players set #look_$(id) {OBJ} 0")

TURN = 1200      # at most 12 degrees per tick (x100)
fn("look_step",                       # as a character, at @s: turn towards the nearest player, a little each tick
   "execute unless entity @p[distance=..96] run return 0",
   f"execute store result score #y0 {OBJ} run data get entity @s Rotation[0] 100",
   "execute anchored eyes run rotate @s facing entity @p eyes",
   f"execute store result score #y1 {OBJ} run data get entity @s Rotation[0] 100",
   f"scoreboard players operation #y1 {OBJ} -= #y0 {OBJ}",
   f"scoreboard players operation #y1 {OBJ} %= #k36000 {OBJ}",
   f"execute if score #y1 {OBJ} matches 18001.. run scoreboard players remove #y1 {OBJ} 36000",
   f"execute if score #y1 {OBJ} matches {TURN + 1}.. run function {NS}:cast/look_clamp_pos",
   f"execute if score #y1 {OBJ} matches ..-{TURN + 1} run function {NS}:cast/look_clamp_neg",
   f"execute store result score #p0 {OBJ} run data get entity @s Rotation[1] 100",
   f"execute if score #p0 {OBJ} matches 3001.. run data modify entity @s Rotation[1] set value 30.0f",
   f"execute if score #p0 {OBJ} matches ..-3001 run data modify entity @s Rotation[1] set value -30.0f")
fn("look_clamp_pos",
   f"scoreboard players add #y0 {OBJ} {TURN}",
   f"execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #y0 {OBJ}")
fn("look_clamp_neg",
   f"scoreboard players remove #y0 {OBJ} {TURN}",
   f"execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #y0 {OBJ}")

for i in IDS:
    fn(f"tick/{i}",
       f"execute if score #np_{i} {OBJ} matches 1.. as {sel(i, ',limit=1')} run function {NS}:cast/nud/{i}",
       f"execute if score #walk_{i} {OBJ} matches 1.. as {sel(i, ',limit=1')} at @s run function {NS}:cast/step/{i}",
       f"execute if score #walk_{i} {OBJ} matches 0 if score #look_{i} {OBJ} matches 1 if score #np_{i} {OBJ} matches 0 "
       f"as {sel(i, ',tag=!angel.lying,limit=1')} at @s run function {NS}:cast/look_step",
       f"execute as {sel(i, ',tag=angel.mounted,limit=1')} run function {NS}:cast/check_mounted")

# a rider whose seat has gone is no longer mounted
fn("check_mounted",
   f"scoreboard players set #rid {OBJ} 0",
   f"execute on vehicle run scoreboard players set #rid {OBJ} 1",
   f"execute if score #rid {OBJ} matches 0 run tag @s remove angel.mounted",
   f"execute if score #rid {OBJ} matches 0 run tag @s remove angel.sitting")

# ---------------------------------------------------------------------------------------------------------------------
# walking
# ---------------------------------------------------------------------------------------------------------------------
fn("walk",
   '$data modify storage angel:cast walk.$(id) set value {id:"$(id)",x:$(x),y:$(y),z:$(z),speed:$(speed)}',
   f"$execute as {msel('tag=angel.$(id),limit=1')} at @s run function {NS}:cast/walk1 with storage angel:cast walk.$(id)")
fn("walk1",                           # as the character, at @s: turn towards the goal, then work out one step
   "$rotate @s facing $(x) ~ $(z)",
   f"$execute at @s run function {NS}:cast/walk2 with storage angel:cast walk.$(id)")
fn("walk2",
   f"execute if entity @s[tag=angel.lying] run function {NS}:cast/unlie",
   "execute if entity @s[tag=angel.mounted] run ride @s dismount",
   "$kill @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id)]",
   "tag @s remove angel.mounted",
   "tag @s remove angel.sitting",
   f"$scoreboard players set #np_$(id) {OBJ} 0",
   "effect clear @s minecraft:invisibility",
   "data merge entity @s {immovable:0b,NoGravity:0b}",
   # one step of the right length and direction: ask a marker where ^ ^ ^speed is
   '$summon minecraft:marker ^ ^ ^$(speed) {Tags:["angel.tmp"]}',
   f"execute store result score #ax {OBJ} run data get entity @s Pos[0] 100000",
   f"execute store result score #az {OBJ} run data get entity @s Pos[2] 100000",
   f"execute store result score #bx {OBJ} run data get entity @e[type=minecraft:marker,tag=angel.tmp,limit=1] Pos[0] 100000",
   f"execute store result score #bz {OBJ} run data get entity @e[type=minecraft:marker,tag=angel.tmp,limit=1] Pos[2] 100000",
   "kill @e[type=minecraft:marker,tag=angel.tmp]",
   f"scoreboard players operation #bx {OBJ} -= #ax {OBJ}",
   f"scoreboard players operation #bz {OBJ} -= #az {OBJ}",
   f"$scoreboard players operation #mx_$(id) {OBJ} = #bx {OBJ}",
   f"$scoreboard players operation #mz_$(id) {OBJ} = #bz {OBJ}",
   f"$execute store result score #tx_$(id) {OBJ} run data get storage angel:cast walk.$(id).x 100",
   f"$execute store result score #tz_$(id) {OBJ} run data get storage angel:cast walk.$(id).z 100",
   f"$execute store result score #sp_$(id) {OBJ} run data get storage angel:cast walk.$(id).speed 100",
   f"$execute if score #sp_$(id) {OBJ} matches ..0 run scoreboard players set #sp_$(id) {OBJ} 1",
   # time limit: about twice the time the walk should take, plus three seconds
   f"scoreboard players operation #ax {OBJ} /= #k1000 {OBJ}",
   f"scoreboard players operation #az {OBJ} /= #k1000 {OBJ}",
   f"$scoreboard players operation #dx {OBJ} = #tx_$(id) {OBJ}",
   f"$scoreboard players operation #dz {OBJ} = #tz_$(id) {OBJ}",
   f"scoreboard players operation #dx {OBJ} -= #ax {OBJ}",
   f"scoreboard players operation #dz {OBJ} -= #az {OBJ}",
   f"execute if score #dx {OBJ} matches ..-1 run scoreboard players operation #dx {OBJ} *= #km1 {OBJ}",
   f"execute if score #dz {OBJ} matches ..-1 run scoreboard players operation #dz {OBJ} *= #km1 {OBJ}",
   f"scoreboard players operation #dx {OBJ} += #dz {OBJ}",
   f"$scoreboard players operation #dx {OBJ} /= #sp_$(id) {OBJ}",
   f"scoreboard players operation #dx {OBJ} *= #k2 {OBJ}",
   f"scoreboard players add #dx {OBJ} 60",
   f"$scoreboard players operation #tmax_$(id) {OBJ} = #dx {OBJ}",
   f"$scoreboard players set #t_$(id) {OBJ} 0",
   f"$scoreboard players set #arrived_$(id) {OBJ} 0",
   f"$scoreboard players set #walk_$(id) {OBJ} 1",
   f"scoreboard players set #active {OBJ} 1")

for i in IDS:
    fn(f"step/{i}",                    # every tick while walking, as the character at @s
       f"execute if score #walk_{i} {OBJ} matches 2 run return run function {NS}:cast/settle/{i}",
       f"scoreboard players add #t_{i} {OBJ} 1",
       f"execute if score #t_{i} {OBJ} > #tmax_{i} {OBJ} run return run function {NS}:cast/force/{i}",
       f"execute store result entity @s Motion[0] double 0.00001 run scoreboard players get #mx_{i} {OBJ}",
       f"execute store result entity @s Motion[2] double 0.00001 run scoreboard players get #mz_{i} {OBJ}",
       f"execute store result score #cx {OBJ} run data get entity @s Pos[0] 100",
       f"execute store result score #cz {OBJ} run data get entity @s Pos[2] 100",
       f"scoreboard players operation #dx {OBJ} = #tx_{i} {OBJ}",
       f"scoreboard players operation #dz {OBJ} = #tz_{i} {OBJ}",
       f"scoreboard players operation #dx {OBJ} -= #cx {OBJ}",
       f"scoreboard players operation #dz {OBJ} -= #cz {OBJ}",
       f"scoreboard players set #near {OBJ} 0",
       f"execute if score #dx {OBJ} matches -3000..3000 if score #dz {OBJ} matches -3000..3000 run scoreboard players set #near {OBJ} 1",
       f"execute if score #near {OBJ} matches 1 run scoreboard players operation #dx {OBJ} *= #dx {OBJ}",
       f"execute if score #near {OBJ} matches 1 run scoreboard players operation #dz {OBJ} *= #dz {OBJ}",
       f"execute if score #near {OBJ} matches 1 run scoreboard players operation #dx {OBJ} += #dz {OBJ}",
       f"scoreboard players operation #rr {OBJ} = #sp_{i} {OBJ}",
       f"scoreboard players add #rr {OBJ} 2",
       f"scoreboard players operation #rr {OBJ} *= #rr {OBJ}",
       f"execute if score #near {OBJ} matches 1 if score #dx {OBJ} <= #rr {OBJ} run function {NS}:cast/arrive/{i}")
    fn(f"arrive/{i}",                  # close enough: put it exactly on the spot (horizontally), let it settle onto the floor
       f"execute at @s run function {NS}:cast/arrive_m with storage angel:cast walk.{i}",
       "data modify entity @s Motion[0] set value 0.0d",
       "data modify entity @s Motion[2] set value 0.0d",
       f"scoreboard players set #walk_{i} {OBJ} 2",
       f"scoreboard players set #t_{i} {OBJ} 0")
    fn(f"force/{i}",                   # it did not get there in time (blocked?): put it there, y included
       f"function {NS}:cast/force_m with storage angel:cast walk.{i}",
       f"function {NS}:cast/arrive/{i}")
    fn(f"settle/{i}",
       f"scoreboard players add #t_{i} {OBJ} 1",
       f"execute if score #t_{i} {OBJ} matches 30.. run return run function {NS}:cast/finish/{i}",
       f"execute if entity @s[nbt={{OnGround:1b}}] run function {NS}:cast/finish/{i}")
    fn(f"finish/{i}",
       "data merge entity @s {immovable:1b,NoGravity:1b,Motion:[0.0d,0.0d,0.0d]}",
       f"scoreboard players set #walk_{i} {OBJ} 0",
       f"scoreboard players set #arrived_{i} {OBJ} 1")
fn("arrive_m", "$tp @s $(x) ~ $(z)")
fn("force_m", "$tp @s $(x) $(y) $(z)")

fn("stop",                             # stop walking right where it is
   f"$scoreboard players set #walk_$(id) {OBJ} 0",
   f"$execute as {msel('tag=angel.$(id),limit=1')} run data merge entity @s {{immovable:1b,NoGravity:1b,Motion:[0.0d,0.0d,0.0d]}}")

# ---------------------------------------------------------------------------------------------------------------------
# poses: standing, sitting (on a hidden seat), lying (the sleeping pose)
# ---------------------------------------------------------------------------------------------------------------------
# THE RULE (read from the 26.3 client: LivingEntityRenderer.setupRotations, LivingEntity.tickHeadTurn, tick):
#  * The sleeping pose draws the body on its back, feet at the entity's position, head 1.8 blocks away in the
#    direction (-cos a, sin a) (x, z), a = the CLIENT's body rotation yBodyRot (not the Rotation we write!).
#    For a facing yaw y (facing vector (-sin y, cos y)) "feet toward the facing" needs a = -90 - y.
#  * yBodyRot is never sent by the server. The client sets it once, when the entity first appears (= head yaw
#    then), and afterwards only tickHeadTurn moves it: it stays where it is, except that it is clamped to within
#    50 degrees of the entity's yRot (Rotation[0]); a rider does not "move" so the walking turn never applies.
#    So writing Rotation[0] = a leaves the body anywhere in a - 50 .. a + 50 (that is how Rei lay across the gurney).
#  * Aligning therefore drives the clamp: Rotation = a + 50 for 6 ticks (the body is pushed to a .. a + 100), then
#    a - 50 for 6 ticks (pushed down to exactly a), then a (inside the window, the body stays at a). While this runs
#    (12 ticks, state #np/#nt/#na per character) the character is invisible. It is started by every call that
#    sets a seat-aligned or lying yaw (lie, unlie, mount, gurney_move's turn).
# We keep the story's idea of "facing": lying, the feet point where she faced, the head is behind her, and her
# middle stays where she stood (a shift of 0.9 blocks along the facing and 0.125 up).
fn("pose", f"$function {NS}:cast/pose_$(pose) {{id:\"$(id)\"}}")
fn("pose_standing",
   f"$execute as {msel('tag=angel.$(id),limit=1')} at @s run function {NS}:cast/stand_up {{id:\"$(id)\"}}")
fn("stand_up",
   f"execute if entity @s[tag=angel.lying] run function {NS}:cast/unlie",
   f"$execute if entity @s[tag=angel.sitting] run function {NS}:cast/unsit {{id:\"$(id)\"}}")
fn("pose_lying",
   f"$execute as {msel('tag=angel.$(id),limit=1')} at @s run function {NS}:cast/lie {{id:\"$(id)\"}}")
fn("lie",
   "execute if entity @s[tag=angel.lying] run return 0",
   f"$execute if entity @s[tag=angel.sitting] run function {NS}:cast/unsit {{id:\"$(id)\"}}",
   "execute if entity @s[tag=!angel.mounted] run tp @s ^ ^0.125 ^0.9 ~ ~",
   "tag @s add angel.lying",
   "data merge entity @s {pose:\"sleeping\",immovable:1b,NoGravity:1b}",
   f"function {NS}:cast/align_yaw")
fn("nud_cancel_self",                  # finish an unfinished alignment at once (Rotation back to the target)
   [f"execute if entity @s[tag=angel.{i}] if score #np_{i} {OBJ} matches 1.. run function {NS}:cast/nud_end/{i}" for i in IDS])
fn("unlie",
   f"function {NS}:cast/nud_cancel_self",
   "execute if entity @s[tag=!angel.mounted] run function angel:cast/yaw_flip_self",
   "tag @s remove angel.lying",
   # first back down to the floor, then the pose: a `data merge` of the pose drops an entity that hovers 0.125
   # above the floor onto it, which would sink her 0.125 into the floor
   "execute if entity @s[tag=!angel.mounted] at @s run tp @s ^ ^-0.125 ^-0.9 ~ ~",
   "data merge entity @s {pose:\"standing\"}",
   "execute if entity @s[tag=angel.mounted] run function angel:cast/align_yaw",
   f"execute if entity @s[tag=!angel.mounted] run function {NS}:cast/nudge_self")      # #y0 = the standing yaw
fn("yaw_flip_self",                    # yaw -> -90 - yaw (the conversion is its own inverse); leaves it in #y0
   f"execute store result score #y0 {OBJ} run data get entity @s Rotation[0] 100",
   f"function {NS}:cast/yaw_lying",
   f"execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #y0 {OBJ}")
# yaw of a rider: the seat's yaw (or its own if not riding); when lying, converted for the sleeping render;
# then the body is brought to exactly that yaw (see THE RULE above)
fn("align_yaw",
   f"execute store result score #y0 {OBJ} run data get entity @s Rotation[0] 100",
   f"execute if entity @s[tag=angel.mounted] on vehicle store result score #y0 {OBJ} run data get entity @s Rotation[0] 100",
   f"execute if entity @s[tag=angel.lying] run function {NS}:cast/yaw_lying",
   f"function {NS}:cast/nudge_self")
fn("nudge_self",                       # as the character; #y0 = the yaw (x100) the body must end at
   [f"execute if entity @s[tag=angel.{i}] run function {NS}:cast/nud_start/{i}" for i in IDS])
NUD = 6                                # ticks per phase: the client turns the yaw over 3 ticks, plus one for the clamp
for i in IDS:
    fn(f"nud_start/{i}",
       f"scoreboard players operation #na_{i} {OBJ} = #y0 {OBJ}",
       f"scoreboard players set #nt_{i} {OBJ} 0",
       f"scoreboard players set #np_{i} {OBJ} 1",
       "effect give @s minecraft:invisibility 2 0 true",
       f"function {NS}:cast/nud_a/{i}",
       f"scoreboard players set #active {OBJ} 1")
    for name, delta in (("a", 5000), ("b", -5000), ("c", 0)):
        fn(f"nud_{name}/{i}",
           f"scoreboard players operation #y1 {OBJ} = #na_{i} {OBJ}",
           f"scoreboard players add #y1 {OBJ} {delta}" if delta > 0 else
           (f"scoreboard players remove #y1 {OBJ} {-delta}" if delta < 0 else "scoreboard players add #y1 " + OBJ + " 0"),
           f"execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #y1 {OBJ}")
    fn(f"nud/{i}",                     # every tick while aligning, as the character
       f"scoreboard players add #nt_{i} {OBJ} 1",
       f"execute if score #nt_{i} {OBJ} matches ..{NUD - 1} run return 0",
       f"execute if score #np_{i} {OBJ} matches 1 run return run function {NS}:cast/nud_to2/{i}",
       f"function {NS}:cast/nud_end/{i}")
    fn(f"nud_to2/{i}",
       f"scoreboard players set #np_{i} {OBJ} 2",
       f"scoreboard players set #nt_{i} {OBJ} 0",
       f"function {NS}:cast/nud_b/{i}")
    fn(f"nud_end/{i}",
       f"scoreboard players set #np_{i} {OBJ} 0",
       f"function {NS}:cast/nud_c/{i}",
       "effect clear @s minecraft:invisibility")
fn("yaw_lying",
   f"scoreboard players set #y1 {OBJ} -9000",
   f"scoreboard players operation #y1 {OBJ} -= #y0 {OBJ}",
   f"scoreboard players operation #y1 {OBJ} %= #k36000 {OBJ}",
   f"execute if score #y1 {OBJ} matches 18001.. run scoreboard players remove #y1 {OBJ} 36000",
   f"scoreboard players operation #y0 {OBJ} = #y1 {OBJ}")
# standing up from the sleeping pose while riding must give back the vehicle's yaw, not the converted one
fn("pose_sitting",
   f"$execute as {msel('tag=angel.$(id),tag=!angel.mounted,tag=!angel.lying,limit=1')} at @s run function {NS}:cast/sit {{id:\"$(id)\"}}")
fn("sit",
   '$summon minecraft:armor_stand ~ ~0.6 ~ {Tags:["angel.cast","angel.seat","angel.autoseat_$(id)"],Marker:1b,Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}',
   "$ride @s mount @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id),limit=1]",
   "tag @s add angel.sitting",
   "tag @s add angel.mounted",
   "data merge entity @s {immovable:1b,NoGravity:1b}",
   f"$scoreboard players set #walk_$(id) {OBJ} 0",
   f"scoreboard players set #active {OBJ} 1")
fn("unsit",
   "ride @s dismount",
   "tp @s ~ ~ ~",                      # dismounting leaves her at the seat's position; ~ is where she sat
   "$kill @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id)]",
   "tag @s remove angel.sitting",
   "tag @s remove angel.mounted")

# ---------------------------------------------------------------------------------------------------------------------
# mount / dismount / seat
# ---------------------------------------------------------------------------------------------------------------------
fn("mount",
   f"$execute as {msel('tag=angel.$(id),limit=1')} at @s run function {NS}:cast/mount_do {{id:\"$(id)\",tag:\"$(tag)\"}}")
fn("mount_do",
   f"$execute if entity @s[tag=angel.sitting] run function {NS}:cast/unsit {{id:\"$(id)\"}}",
   f"$scoreboard players set #walk_$(id) {OBJ} 0",
   "data merge entity @s {immovable:1b,NoGravity:1b}",
   f"$execute store success score #ok {OBJ} run ride @s mount @e[tag=$(tag),sort=nearest,limit=1]",
   f"execute if score #ok {OBJ} matches 1 run tag @s add angel.mounted",
   f"execute if score #ok {OBJ} matches 1 run function {NS}:cast/align_yaw",
   f"scoreboard players set #active {OBJ} 1")
fn("dismount",
   f"$execute as {msel('tag=angel.$(id),limit=1')} at @s run function {NS}:cast/dismount_do {{id:\"$(id)\"}}")
fn("dismount_do",
   "ride @s dismount",
   "tp @s ~ ~ ~",
   "$kill @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id)]",
   "tag @s remove angel.sitting",
   "tag @s remove angel.mounted")
# a hidden seat (an invisible marker armor stand) at the executor's position and rotation
fn("seat",
   "$kill @e[type=minecraft:armor_stand,tag=angel.seat,tag=$(tag)]",
   '$summon minecraft:armor_stand ~ ~ ~ {Tags:["angel.cast","angel.seat","$(tag)","angel.new"],Marker:1b,Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}',
   "tp @e[type=minecraft:armor_stand,tag=angel.new] ~ ~ ~ ~ 0",
   "tag @e[type=minecraft:armor_stand,tag=angel.new] remove angel.new")

# ---------------------------------------------------------------------------------------------------------------------
# the gurney: block displays that all sit at one point (the yaw turns them together), a seat, two medics
# ---------------------------------------------------------------------------------------------------------------------
# local axes of a display: +x = to the left of the way it faces, +y up, +z forward (the foot end). The patient lies
# with her head at the back (-z). (cx, cy, cz, sx, sy, sz, block); block corner and size, in blocks.
GURNEY = [
    (-0.55, 0.70, -1.05, 1.10, 0.12, 2.10, "minecraft:white_wool", True),          # mattress (the root)
    (-0.52, 0.62, -1.02, 1.04, 0.08, 2.04, "minecraft:light_gray_concrete", False),  # plate under it
    (-0.30, 0.82, -1.00, 0.60, 0.07, 0.38, "minecraft:white_concrete", False),     # pillow
    (-0.58, 0.82, 0.10, 1.16, 0.04, 0.95, "minecraft:light_blue_wool", False),     # blanket over the legs
    (-0.58, 0.58, 0.10, 0.04, 0.26, 0.95, "minecraft:light_blue_wool", False),     # ... hanging down on both sides
    (0.54, 0.58, 0.10, 0.04, 0.26, 0.95, "minecraft:light_blue_wool", False),
    (-0.46, 0.20, -0.90, 0.06, 0.06, 1.80, "minecraft:light_gray_concrete", False),  # frame rails
    (0.40, 0.20, -0.90, 0.06, 0.06, 1.80, "minecraft:light_gray_concrete", False),
    (-0.46, 0.20, -0.90, 0.92, 0.05, 0.05, "minecraft:light_gray_concrete", False),  # cross bars
    (-0.46, 0.20, 0.85, 0.92, 0.05, 0.05, "minecraft:light_gray_concrete", False),
    (-0.43, 0.26, -0.88, 0.05, 0.38, 0.05, "minecraft:light_gray_concrete", False),  # posts
    (0.38, 0.26, -0.88, 0.05, 0.38, 0.05, "minecraft:light_gray_concrete", False),
    (-0.43, 0.26, 0.83, 0.05, 0.38, 0.05, "minecraft:light_gray_concrete", False),
    (0.38, 0.26, 0.83, 0.05, 0.38, 0.05, "minecraft:light_gray_concrete", False),
    (0.34, 0.0, 0.74, 0.12, 0.2, 0.2, "minecraft:black_concrete", False),          # wheels
    (-0.46, 0.0, 0.74, 0.12, 0.2, 0.2, "minecraft:black_concrete", False),
    (0.34, 0.0, -0.94, 0.12, 0.2, 0.2, "minecraft:black_concrete", False),
    (-0.46, 0.0, -0.94, 0.12, 0.2, 0.2, "minecraft:black_concrete", False),
    (0.56, 0.84, -0.60, 0.02, 0.22, 1.20, "minecraft:light_gray_stained_glass", False),   # side rails
    (-0.58, 0.84, -0.60, 0.02, 0.22, 1.20, "minecraft:light_gray_stained_glass", False),
    (0.55, 1.04, -0.60, 0.04, 0.03, 1.20, "minecraft:light_gray_concrete", False),
    (-0.59, 1.04, -0.60, 0.04, 0.03, 1.20, "minecraft:light_gray_concrete", False),
    (-0.74, 0.30, -0.92, 0.05, 1.70, 0.05, "minecraft:white_concrete", False),     # drip stand on the right
    (-0.80, 0.30, -0.98, 0.17, 0.04, 0.17, "minecraft:light_gray_concrete", False),
    (-0.86, 1.98, -0.92, 0.17, 0.04, 0.05, "minecraft:white_concrete", False),
    (-0.88, 1.68, -0.93, 0.09, 0.28, 0.07, "minecraft:cyan_stained_glass", False),  # the bag
]
SEAT_Y, SEAT_Z = 0.945, 0.9            # the patient's feet end: mattress top 0.82 + 0.125, 0.9 forward of the middle
# lateral (+ = left), forward offsets of the crew: both on the left (the drip stand is on the right), medic1 at the
# foot end, medic2 at the head end, 0.95 out from the middle line = 0.4 clear of the mattress edge, 0.9 from the
# middle = level with the ends of the patient's body, so nobody stands in or across her
CREW = {"medic1": (0.95, 0.9), "medic2": (0.95, -0.9)}

part_cmds = []
for (cx, cy, cz, sx, sy, sz, block, root) in GURNEY:
    tags = ["angel.cast", "angel.gurney", "angel.new"] + (["angel.gurney_root"] if root else [])
    tg = ",".join(f'"{t}"' for t in tags)
    part_cmds.append(
        f"summon minecraft:block_display ~ ~ ~ {{Tags:[{tg}],block_state:\"{block}\",teleport_duration:3,view_range:1.5f,"
        f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],scale:[{sx}f,{sy}f,{sz}f],translation:[{cx}f,{cy}f,{cz}f]}}}}")
SEAT = ('summon minecraft:armor_stand ~ ~ ~ {Tags:["angel.cast","angel.seat","angel.seat_gurney","angel.new"],'
        'Marker:1b,Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}')
fn("gurney",
   f"function {NS}:cast/gurney_remove",
   part_cmds,
   "tp @e[tag=angel.new,type=minecraft:block_display] ~ ~ ~ ~ 0",
   f"execute positioned ^ ^{SEAT_Y} ^{SEAT_Z} run {SEAT}",
   f"execute positioned ^ ^{SEAT_Y} ^{SEAT_Z} run tp @e[tag=angel.new,type=minecraft:armor_stand] ~ ~ ~ ~ 0",
   "tag @e[tag=angel.new] remove angel.new",
   f"scoreboard players set #gmove {OBJ} 0",
   f"scoreboard players set #arrived_gurney {OBJ} 0",
   f"scoreboard players set #active {OBJ} 1")
fn("gurney_remove",
   "kill @e[tag=angel.gurney]",
   "kill @e[tag=angel.seat_gurney]",
   f"scoreboard players set #gmove {OBJ} 0",
   f"scoreboard players set #arrived_gurney {OBJ} 0")
fn("gurney_crew",                      # the two medics, at their places beside the gurney
   [f"execute as @e[tag=angel.gurney_root,limit=1] at @s positioned ^{lat} ^ ^{fw} rotated as @s run function {NS}:cast/spawn/{m}"
    for m, (lat, fw) in CREW.items()])
fn("gm_followers",                     # as the gurney's root, at @s: seat and crew follow it
   f"execute positioned ^ ^{SEAT_Y} ^{SEAT_Z} run tp @e[tag=angel.seat_gurney] ~ ~ ~ ~ ~",
   [f"execute positioned ^{lat} ^ ^{fw} as {sel(m)} run tp @s ~ ~ ~ ~ ~" for m, (lat, fw) in CREW.items()])
fn("gurney_move",
   '$data modify storage angel:cast gm set value {x:$(x),y:$(y),z:$(z),speed:$(speed)}',
   f"execute as @e[tag=angel.gurney_root,limit=1] at @s run function {NS}:cast/gm_begin with storage angel:cast gm")
isqrt = [f"scoreboard players operation #s {OBJ} = #n {OBJ}",
         f"scoreboard players operation #s {OBJ} /= #k1000 {OBJ}",
         f"scoreboard players add #s {OBJ} 100"]
for _ in range(14):
    isqrt += [f"scoreboard players operation #q {OBJ} = #n {OBJ}",
              f"scoreboard players operation #q {OBJ} /= #s {OBJ}",
              f"scoreboard players operation #s {OBJ} += #q {OBJ}",
              f"scoreboard players operation #s {OBJ} /= #k2 {OBJ}"]
fn("isqrt", isqrt)                     # #s := integer square root of #n
fn("gm_begin",                         # as the gurney's root, at @s
   "$tp @e[tag=angel.gurney] ~ ~ ~ facing $(x) ~ $(z)",
   f"execute at @s run function {NS}:cast/gm_followers",        # a fresh `at @s`: the yaw has just changed
   f"execute store result score #gtx {OBJ} run data get storage angel:cast gm.x 100",
   f"execute store result score #gtz {OBJ} run data get storage angel:cast gm.z 100",
   f"execute store result score #gty {OBJ} run data get storage angel:cast gm.y 100",
   f"execute store result score #gsp {OBJ} run data get storage angel:cast gm.speed 100",
   f"execute if score #gsp {OBJ} matches ..0 run scoreboard players set #gsp {OBJ} 1",
   f"execute store result score #cx {OBJ} run data get entity @s Pos[0] 100",
   f"execute store result score #cy {OBJ} run data get entity @s Pos[1] 100",
   f"execute store result score #cz {OBJ} run data get entity @s Pos[2] 100",
   f"scoreboard players operation #dx {OBJ} = #gtx {OBJ}",
   f"scoreboard players operation #dz {OBJ} = #gtz {OBJ}",
   f"scoreboard players operation #gdy {OBJ} = #gty {OBJ}",
   f"scoreboard players operation #dx {OBJ} -= #cx {OBJ}",
   f"scoreboard players operation #dz {OBJ} -= #cz {OBJ}",
   f"scoreboard players operation #gdy {OBJ} -= #cy {OBJ}",
   f"scoreboard players operation #n {OBJ} = #dx {OBJ}",
   f"scoreboard players operation #n {OBJ} *= #dx {OBJ}",
   f"scoreboard players operation #dz {OBJ} *= #dz {OBJ}",
   f"scoreboard players operation #n {OBJ} += #dz {OBJ}",
   f"function {NS}:cast/isqrt",
   f"scoreboard players operation #gn {OBJ} = #s {OBJ}",
   f"scoreboard players operation #gn {OBJ} /= #gsp {OBJ}",
   f"execute if score #gn {OBJ} matches ..0 run scoreboard players set #gn {OBJ} 1",
   f"scoreboard players operation #gdy {OBJ} *= #k1000 {OBJ}",
   f"scoreboard players operation #gdy {OBJ} /= #gn {OBJ}",
   f"execute if score #gdy {OBJ} matches -199..199 run scoreboard players set #gdy {OBJ} 0",
   f"execute store result storage angel:cast gm.dy double 0.00001 run scoreboard players get #gdy {OBJ}",
   [f"scoreboard players set #look_{m} {OBJ} 0" for m in CREW],
   f"execute as @e[tag=angel.seat_gurney] on passengers run function {NS}:cast/align_yaw",
   f"scoreboard players set #arrived_gurney {OBJ} 0",
   f"scoreboard players set #gmove {OBJ} 1",
   f"scoreboard players set #active {OBJ} 1")
fn("gm_step",
   f"execute as @e[tag=angel.gurney_root,limit=1] at @s run function {NS}:cast/gm_step_root",
   f"execute unless entity @e[tag=angel.gurney_root,limit=1] run scoreboard players set #gmove {OBJ} 0")
fn("gm_step_root",
   f"scoreboard players remove #gn {OBJ} 1",
   f"execute if score #gn {OBJ} matches ..0 run return run function {NS}:cast/gm_arrive with storage angel:cast gm",
   f"function {NS}:cast/gm_move with storage angel:cast gm",
   f"function {NS}:cast/gm_followers")
fn("gm_move", "$execute as @e[tag=angel.gurney] at @s run tp @s ^ ^$(dy) ^$(speed)")
fn("gm_arrive",
   "$tp @e[tag=angel.gurney] $(x) $(y) $(z)",
   f"execute at @s run function {NS}:cast/gm_followers",     # a fresh `at @s`: the root has just been moved
   [f"execute if entity {sel(m)} run scoreboard players set #look_{m} {OBJ} 1" for m in CREW],
   f"scoreboard players set #gmove {OBJ} 0",
   f"scoreboard players set #arrived_gurney {OBJ} 1")


# ---------------------------------------------------------------------------------------------------------------------
# checking, writing
# ---------------------------------------------------------------------------------------------------------------------
SAMPLE = {"id": "misato", "x": "1.5", "y": "65", "z": "2.5", "speed": "0.2", "pose": "standing", "tag": "angel.seat_driver",
          "mode": "player", "dy": "0.01", "scale": "1.6"}


def check_lines():
    """Run every line past the command tree of the game (macro lines with sample values filled in)."""
    import re
    import cmdcheck
    bad = []
    checker = cmdcheck.Checker()
    for path, lines in fns.items():
        for n, line in enumerate(lines, 1):
            text = line
            if text.startswith("$"):
                text = re.sub(r"\$\((\w+)\)", lambda m: SAMPLE[m.group(1)], text[1:])
            try:
                msg = checker.check(text)
            except Exception as e:                       # noqa: BLE001
                msg = f"{type(e).__name__}: {e}"
            if msg:
                bad.append((path, n, line, msg))
    return bad


def write_all(dp_base, rp_base, skins_out, log):
    written = []

    def put(base, rel, data, tag):
        p = os.path.join(base, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not (os.path.isfile(p) and os.path.getsize(p) == len(data) and open(p, "rb").read() == data):
            with open(p, "wb") as f:
                f.write(data)
        written.append(f"{tag}:{rel}")

    for path, lines in sorted(fns.items()):
        put(dp_base, f"{FN_DIR}/{path}.mcfunction", "\n".join(lines) + "\n", "dp")
    for name, (img, _slim) in skins_out.items():
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        put(rp_base, f"{TEX_DIR}/{name}.png", buf.getvalue(), "rp")
    return written


def clean_old(written, bases):
    n = 0
    if not os.path.isfile(MANIFEST):
        return 0
    old = json.load(open(MANIFEST, encoding="utf-8")).get("files", [])
    for entry in old:
        if entry in written:
            continue
        tag, rel = entry.split(":", 1)
        p = os.path.join(bases[tag], *rel.split("/"))
        if os.path.isfile(p):
            os.remove(p)
            n += 1
        d = os.path.dirname(p)
        while d != bases[tag] and os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            d = os.path.dirname(d)
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args(argv)

    print("drawing skins")
    skins_out = skinlib.make_all()
    bad = check_lines()
    print(f"{len(fns)} functions, {sum(len(v) for v in fns.values())} lines: {len(bad)} the command tree does not accept")
    for path, n, line, msg in bad[:40]:
        print(f"  cast/{path} line {n}: {msg}: {line[:150]}")
    if bad:
        return 1
    if args.preview:
        import render
        os.makedirs(PREVIEW, exist_ok=True)
        print("preview:", render.sheet(skins_out, os.path.join(PREVIEW, "sheet.png")))
        print("preview:", render.gurney_preview(GURNEY, SEAT_Y, SEAT_Z, CREW, os.path.join(PREVIEW, "gurney.png")))
    if args.check:
        tmp = tempfile.mkdtemp(prefix="angel-cast-check-")
        write_all(os.path.join(tmp, "dp"), os.path.join(tmp, "rp"), skins_out, print)
        shutil.rmtree(tmp, ignore_errors=True)
        print("check ok (nothing written)")
        return 0
    if args.out:
        dp, rp = os.path.join(args.out, "datapack", "angel"), os.path.join(args.out, "pack", "angel-resources")
        manifest_ok = False
    else:
        dp, rp, manifest_ok = DP_ROOT, RP_ROOT, True
    written = write_all(dp, rp, skins_out, print)
    if manifest_ok:
        removed = clean_old(written, {"dp": dp, "rp": rp})
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"files": sorted(written)}, f, indent=0)
        print(f"wrote {len(written)} files ({removed} stale removed); manifest {MANIFEST}")
    else:
        print(f"wrote {len(written)} files to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())





