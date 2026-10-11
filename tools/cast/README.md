# The cast

The people of the story as entities in the world: Misato, Ritsuko, Gendo, Rei (in hospital, and once in school
uniform) and two medics. This folder makes them: the skins (drawn in code), and the datapack functions that
summon, walk, turn, pose, seat and wheel them about. The story scenes only call the functions below.

    python tools\cast\build_cast.py              (Python of D:\voice-assistant: numpy, pillow)
    python tools\cast\build_cast.py --preview    also render preview\sheet.png and preview\gurney.png
    python tools\cast\build_cast.py --check      build in a temporary folder, write nothing

The build writes only what is listed in `build_manifest.json` (a later build removes exactly those files first):

| Where | What |
|---|---|
| `datapack/angel/data/angel/function/cast/` | the API and its helpers (97 small functions) |
| `pack/angel-resources/assets/angel/textures/entity/cast/<id>.png` | the seven skins |

Every command line is also checked against the game's own command tree (`tools/world/cmdcheck.py`), with sample
values put in for `$(macro)` arguments.

## What a character is

A **`minecraft:mannequin`** (the entity Genesis used for Adam and Eve), summoned with

    Tags:["angel.cast", <"angel.char" | "angel.medic">, "angel.<id>"], Invulnerable, Silent, NoGravity, immovable,
    hide_description, attributes:[step_height 1.0],
    profile:{texture:"angel:entity/cast/<id>", model:"slim" | "wide"}

and put in the team `angel.cast` (collision rule *never*: nobody pushes anybody, whatever `immovable` says).

* **Skin**: `profile.texture` is a resource location under `textures/`, so `angel:entity/cast/misato` is
  `assets/angel/textures/entity/cast/misato.png` of the resource pack. `profile.model` is `"slim"` (3-pixel arms) or
  `"wide"`. The women and the girl are slim (misato, ritsuko, rei, rei_uniform, medic2); gendo and medic1 are wide.
* No AI, so no wandering; it never takes damage; it never despawns (it is not a Mob); silent; the floating
  "NPC" label is hidden; the nameplate is off (team rule) and there is no custom name.
* Tags: `angel.cast` on everything made here; `angel.char` on misato, ritsuko, gendo, rei and rei_uniform
  (the medics have `angel.medic` instead); `angel.<id>` on each. rei_uniform has `angel.rei_uniform` and **not**
  `angel.rei`. While in use: `angel.lying`, `angel.sitting`, `angel.mounted`.
* `Pos` is the feet (so for the bridge: `data get entity @e[tag=angel.misato,sort=nearest,limit=1] Pos`).
  Exception: lying, `Pos` is the foot end of the body (0.9 blocks from her middle).

## The API (macro functions, namespace `angel`, folder `cast`)

Ids: `misato ritsuko gendo rei rei_uniform medic1 medic2`. The objective is `angel.cast`.

| Call | Does |
|---|---|
| `function angel:cast/summon {id:"misato"}` | at the executor's position and yaw (pitch 0), standing, looking at the player. Summoning again replaces the old one. |
| `function angel:cast/remove {id:"misato"}` | removes it (and its own seat) |
| `function angel:cast/remove_all` | removes every cast entity: characters, gurney, seats |
| `function angel:cast/walk {id:"misato",x:1.5,y:65,z:2.5,speed:0.2}` | walks in a straight line to x,z at `speed` blocks per tick, facing the way it goes (walking animation: the client animates any entity that is moving), stepping up and down blocks, slabs and stairs, and stops there. **Arrival: `scoreboard players get #arrived_misato angel.cast` is 0 from the start of the walk and 1 once it stands still on the spot** (a few ticks after it gets there; it first settles onto the floor). `y` is only used as a last resort (below). |
| `function angel:cast/stop {id:"misato"}` | stops a walk where it is (the arrived score stays 0) |
| `function angel:cast/look {id:"misato",mode:"player"}` | turns (12 degrees a tick at most; head and body together) to face the nearest player within 96 blocks, while standing still. Mode `"ahead"` stops it. Default after summon: player. Not while walking (it resumes at arrival) and not while lying. |
| `function angel:cast/pose {id:"rei",pose:"standing"}` / `"sitting"` / `"lying"` | see below |
| `function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}` | rides the nearest entity that has that tag, takes the seat's yaw |
| `function angel:cast/dismount {id:"misato"}` | gets off, where the seat is (a sitter ends at her sitting height, 0.6 below the seat) |
| `function angel:cast/gurney {}` | a hospital gurney (26 block displays, `angel.gurney, angel.cast`, the mattress also `angel.gurney_root`) at the executor's position and yaw, and a seat `angel.seat_gurney`. Foot end forward. Replaces an earlier one. |
| `function angel:cast/gurney_move {x:..,y:..,z:..,speed:0.15}` | rolls the gurney there in a straight line (it turns to face the goal first), the rider and both medics moving with it. **`#arrived_gurney` is 0 while rolling, 1 at the goal.** |
| `angel:cast/load`, `angel:cast/tick` | called from the load/tick tags. Tick costs one score lookup when nothing of the cast exists. |

Additions beyond the brief:

| Call | Does |
|---|---|
| `function angel:cast/seat {tag:"angel.seat_driver"}` | an invisible seat (marker armor stand, tags `angel.cast`, `angel.seat`, your tag) at the executor's position and yaw; replaces one with the same tag. **Put it at the height of the surface she sits on** (see below). |
| `function angel:cast/gurney_crew {}` | summons medic1 and medic2 at their places beside the gurney (use it when you wheel the gurney in, then `gurney_move`) |
| `function angel:cast/gurney_remove` | removes the gurney and its seat only |

### Walking, in detail

* It is real movement (the game's own collision, step height 1.0, gravity), so it follows the floor over a
  slab, a stair or a single block, and down again. Verified on the hq corridor and the escalator stairs both ways.
* It needs **loaded, ticking chunks**: with a player nearby that is automatic; on an empty server only forceloaded
  chunks tick (this bit our own first tests).
* The straight line must be clear. If it is blocked, the walk gives up after about twice the expected time plus 3
  seconds and puts the character on the goal (x, y, z all used), so the story never waits forever.
* Walking a character who is lying, sitting or mounted first stands her up / dismounts her.
* While the entity is idle it is frozen (`immovable`, `NoGravity`); it is only unfrozen during a walk.

### Poses

The mannequin only knows `standing, crouching, swimming, fall_flying, sleeping` as poses and no arm poses at all
(so Gendo cannot clasp his hands; he stands with the arms down, gloves white). What the three poses do:

* **standing**: undoes the other two (stands up from lying where she lay; gets off her own seat).
* **sitting**: rides an invisible seat she brings herself, placed so that she stays where she is (seat 0.6
  above her feet): the client draws any rider with bent knees, arms forward. To sit on a *particular* chair or
  car seat use `seat` / your own seat entity and `mount`: **a standing or sitting rider's feet end 0.6 below the
  seat entity, so put the seat at the surface she sits on**.
* **lying**: the sleeping pose, on her back, feet toward where she faced, head behind, her middle where she
  stood (so summon her at the surface she lies on, e.g. the mattress top 0.82 above the gurney's floor point;
  the function lifts her 0.125). It is computed from the client's own rendering code (`LivingEntityRenderer`),
  not seen. Mounted, she takes the yaw of the vehicle (feet toward its forward). A lying rider's feet end is the
  seat position and her body extends 1.8 blocks behind the seat; on the gurney the seat is the mattress's foot end.
  Order for the gurney: `gurney`, `summon rei`, `mount rei angel.seat_gurney`, `pose rei lying`, `gurney_crew`.

### Looking

`look` needs a player: it picks `@p` within 96 blocks. With nobody online it does nothing. The turn logic was run
in tests with a marker standing in for the player (12 degrees a tick, shortest way round, pitch kept within 30).

## Skins

Seven 64x64 skins (`skins.py`), the modern layout with outer layers, all our own drawings from plain descriptions.
`render.py` is a small software renderer for the preview (both layers on the model, four angles and a far view);
`preview/sheet.png` is the sheet, `preview/gurney.png` the gurney drawn flat with the patient and crew outlined.

| id | model | the picture |
|---|---|---|
| misato | slim | long dark purple hair with a fringe that also falls over the back and shoulders; short red jacket over a black sleeveless dress, silver cross on a chain; black boots |
| ritsuko | slim | short blonde hair, dark brows, mole under the left eye; white lab coat open over a blue top and dark skirt/tights |
| gendo | wide | short black hair, grey temples, close beard along the jaw, orange-tinted glasses; dark high-collared jacket with a red collar, belt, white gloves |
| rei | slim | pale skin, short pale-blue hair, red eyes; white hospital gown; gauze band round the head and a pad over the right eye; left arm in a plaster cast, a sling strap over the shoulder, tape on the right arm for the drip, hospital slippers |
| rei_uniform | slim | the same girl unhurt: white blouse, blue-green pinafore, red ribbon, white socks |
| medic1, medic2 | wide, slim | green surgical caps, masks, pale green scrubs (different skin and cap tones) |

## Tests that were run (scratch server, port 25602)

See the report in the conversation that made this; in short: pack loads with zero errors (also a cold start); every
function in the API run; each id summoned and its tags, profile, pose read back; walks across the hq corridor and
the escalator both ways (it stays on the floor, y follows the stairs, arrival score); blocked walk; pose lying /
standing and sitting / standing (positions and yaw read back); mount, dismount, seat; gurney, rei mounted and
lying, crew, gurney_move (positions of all parts polled each half second); look turn logic. What only a person in the
game can judge: how every skin and the gurney look, the lying orientation, the sitting height, the walk animation,
smoothness of the moving gurney, and the head/body turn of `look`.
