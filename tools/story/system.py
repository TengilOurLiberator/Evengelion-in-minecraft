"""The fixed part of the datapack: load, tick, halt, start/stop/scene/skip, the bridge's two entry points, the speak prompt, the ride lock,
the look check, and the rig functions.  Scenes are compiled by engine.py; this file wires them in."""
import json

from core import (CAST_IDS, CFG, CHARACTERS, DISPLAY_NAMES, NS, OBJ, PA, P, T, TAG, dispatch_tree, fn, num, sadd, sc, sset, ssub)

TICK_TAG_PLAYER = "@a[limit=1]"

# The story's props (the letter and the photograph of scene 1, the booklet of scene 3): written books and paper.  They are moved out of the
# hotbar (they would sit as a big block in the lower right of the picture) and cleared when the story starts and when scene 4 begins.
STORY_ITEMS = ("minecraft:written_book", "minecraft:paper")


def register(ctx):
    """What the engine does around the scenes, before they are compiled: commands run when a scene is entered."""
    ctx.enter_hooks.setdefault(4, []).extend(f"clear {PA()} {it}" for it in STORY_ITEMS)     # the props have served their purpose


def player_any():
    return P()


def text_json(s, color="white", **kw):
    d = {"text": s, "color": color}
    d.update(kw)
    return json.dumps(d, ensure_ascii=True)


def build_system(out, ctx):
    scenes = sorted(ctx.scenes, key=lambda s: s.n)
    flags = sorted(ctx.flags)

    # ----------------------------------------------------------------------------------------------------------- load
    defaults = {"#beat": 0, "#wait": 0, "#speaker": 0, "#talking": 0, "#lastspoke": 0, "#bridge_speaking": 0, "#running": 0,
                "#scene": 0, "#step": -1, "#mv.on": 0, "#mv.n": 0, "#mv.limit": 0, "#mv.route": 0, "#ride": 0, "#timeout_s": 0,
                "#subtitles": CFG.subtitles_default, "#line_left": 0, "#sleep": 0, "#force": 0, "#tick": 0, "#wt": -1, "#consent": 0,
                "#c5": 5, "#c20": 20, "#looking": 0, "#pk": 0, "#line": 0, "#rd": 0, "#placed": 0, "#nagt": 0, "#nagi": 0, "#hush": 0,
                "#ctl": 0, "#tut.off": 0, "#ob.on": 0, "#ob.line": -1, "#ob.shown": 0, "#stk": 0, "#stkh": 0, "#ob.k": 0, "#ob.gf": 1,
                # the voice bridge handshake (lines.py): heartbeat, live switch, the cue and its claim
                "#bridge_hb": 0, "#live_ok": 1, "#live": 0, "#cue": 0, "#cue_n": 0, "#cue_ack": -1, "#cue_fb": 0, "#cue_wait": 0, "#cue_t": 0, "#ack_t": 0}
    for c in CHARACTERS:
        defaults[f"#present_{c}"] = 0
    load = [f"scoreboard objectives add {OBJ} dummy"]
    for k, v in defaults.items():
        load.append(f"execute unless score {k} {OBJ} matches -2147483648..2147483647 run {sset(k, v)}")
    load += [sset("#c5", 5), sset("#c20", 20), sset("#c3600", 3600), sset("#c1000", 1000),
             sset("#stk_hint", T(CFG.stuck_hint_s)), sset("#stk_skip", T(CFG.stuck_skip_s)),        # (angel:story/stuck {hint_s:..,skip_s:..} changes them until the next reload)
             f"kill @e[tag=angel.objective]", sset("#ob.shown", 0), sset("#ob.bl", -1), sset("#ob.line", -1)]    # a /reload never leaves a duplicate waypoint: the tick makes them again
    # a reload or restart: if no story is running there is nothing that should still be standing
    load.append(f"execute unless score #running {OBJ} matches 1 run kill @e[tag={TAG}]")
    load += ctx.load_extra
    out.function("story/load", load)

    # ----------------------------------------------------------------------------------------------------------- tick
    tick = [fn("story/t_line"),
            f"execute unless score #running {OBJ} matches 1 run return 0",
            f"execute unless entity {P()} run return 0",          # nobody online (or no player yet): the story waits
            sadd("#tick"),
            fn("story/mover"),
            fn("story/t_ride"),
            fn("story/t_inv"),
            fn("story/t_prompt"),
            fn("story/ob/tick")]
    for sc_ in scenes:
        tick.append(f"execute if score #scene {OBJ} matches {sc_.n} run function {NS}:story/s{sc_.n}/poll")
    tick.append(fn("story/t_fx"))
    out.function("story/tick", tick)
    # t_fx: continuous effects that scenes switch on with flags (aircraft orbit etc.)
    out.function("story/t_fx", ctx.fx_tick or ["# no continuous effects"])
    # The line clock.  The ENGINE owns the end of every line: #line_left counts down and #talking goes to 0 at zero, whether the file or the bridge is
    # speaking (the bridge writes the real length with angel:say/claim), so a bridge that dies mid-line cannot hold the story.  #bridge_hb is the
    # bridge's heartbeat (set to 20 every quarter second), counted down here; a live cue nobody claims is taken over by the game (lines.py).
    out.function("story/t_line", [f"execute {sc('#bridge_hb', '1..')} run {ssub('#bridge_hb')}",
                                  f"execute {sc('#talking', '1')} run {ssub('#line_left')}",
                                  f"execute {sc('#talking', '1')} {sc('#line_left', '..0')} run {sset('#talking', 0)}",
                                  f"execute {sc('#talking', '1')} {sc('#live', '1')} unless score #cue_ack {OBJ} = #cue_n {OBJ} run function {NS}:say/unclaimed"])

    # ----------------------------------------------------------------------------------------------------------- halt
    halt = ["# stop everything the story started: timers, entities, cast, monster, forceloads, scene flags"]
    for path in sorted(set(ctx.all_scheduled())):
        halt.append(f"schedule clear {NS}:{path}")
    halt += [f"kill @e[tag={TAG}]"]
    for cid in CAST_IDS:
        halt.append(f'function {NS}:cast/remove {{id:"{cid}"}}')
    halt.append(fn("story/ob/end"))                            # objectives: waypoints, direction lines, target markers
    halt.append(f"function {NS}:cast/gurney_remove")          # the hospital gurney (cast entities carry no story tag)
    halt.append(f"function {NS}:story/snd/stop_all")           # ambience beds, music, their restart timers
    halt += ctx.halt_extra
    halt.append(f"function {NS}:angel/remove")
    for (x, z) in sorted(ctx.forceloads):
        halt.append(f"forceload remove {x} {z}")
    halt += [sset("#wait", 0), sset("#talking", 0), sset("#line_left", 0), sset("#live", 0), sset("#mv.on", 0), sset("#ride", 0), sset("#consent", 0), sset("#hush", 0), sset("#rd", 0)]
    halt += [sset(f"#fx.{f}", 0) for f in sorted(ctx.fx_flags)]
    halt += [sset(f"#f.{f}", 0) for f in flags]
    halt += [f"execute {sc('#bridge_speaking', '..-1')} run {sset('#bridge_speaking', 0)}"]
    out.function("story/halt", halt)

    # ----------------------------------------------------------------------------------------------------------- entry points
    out.function("story/scene", [f"$function {NS}:story/s$(n)/begin"])
    start_body = [fn("story/load"), *ctx.stop_extra, fn("story/halt"), "stopsound @a voice", f"effect clear {PA()} minecraft:blindness",
                  sset("#running", 1), sset("#consent", 0),
                  f"gamemode adventure {PA()}",
                  *[f"clear {PA()} {it}" for it in STORY_ITEMS],          # a restart: no letter, photograph or booklet left over
                  f"function {NS}:story/scene {{n:1}}"]
    out.function("story/start_run", start_body)
    out.function("story/start", [sset("#tut.off", 0), fn("story/start_run")])                    # with the 20-second opening tutorial (scene 1, after the card)
    out.function("story/start_no_tutorial", [sset("#tut.off", 1), fn("story/start_run")])        # a replay: no tutorial
    out.function("story/stop", [*ctx.stop_extra, fn("story/halt"), sset("#running", 0), sset("#scene", 0), sset("#step", -1), "stopsound @a voice",
                                f"effect clear {PA()} minecraft:blindness",
                                f"tellraw @a {text_json('[angel] story stopped', 'gray')}"])
    out.function("story/skip", [f"execute {sc('#wait', '1..')} run tellraw @a {text_json('[angel] wait skipped', 'gray')}",
                                sset("#wait", 0)])
    out.function("story/next", [fn("story/skip"),
                                sset("#talking", 0), sset("#line_left", 0), sset("#live", 0), "stopsound @a voice",
                                sset("#force", 1), f"tellraw @a {text_json('[angel] step skipped', 'gray')}"])
    out.function("story/answered", [f"execute {sc('#wait', '1')} run {sset('#wait', 0)}"])
    out.function("story/consented", [f"execute {sc('#wait', '1..')} run {sset('#wait', 0)}", sset("#consent", 1)])
    out.function("story/bridge_on", [sset("#live_ok", 1), f"tellraw @a {text_json('[angel] a connected voice bridge performs the lines', 'gray')}"])
    out.function("story/bridge_off", [sset("#live_ok", 0), f"tellraw @a {text_json('[angel] the pre-rendered lines always play', 'gray')}"])
    out.function("story/bridge_status", [
        "tellraw @a [" + ",".join([
            text_json("[angel] bridge heartbeat "), '{"score":{"name":"#bridge_hb","objective":"angel.story"}}', text_json(" live_ok "),
            '{"score":{"name":"#live_ok","objective":"angel.story"}}', text_json(" cue "), '{"score":{"name":"#cue","objective":"angel.story"}}',
            text_json(" ack "), '{"score":{"name":"#cue_ack","objective":"angel.story"}}', text_json(" fallback "),
            '{"score":{"name":"#cue_fb","objective":"angel.story"}}']) + "]"])
    out.function("story/timeout", [f"$scoreboard players set #timeout_s {OBJ} $(s)"])
    out.function("story/timeout_off", [sset("#timeout_s", 0)])
    out.function("story/subtitles_on", [sset("#subtitles", 1)])
    out.function("story/subtitles_off", [sset("#subtitles", 0)])
    out.function("story/wt_global", [f"scoreboard players operation #wt {OBJ} = #timeout_s {OBJ}",
                                     f"scoreboard players operation #wt {OBJ} *= #c20 {OBJ}"])
    out.function("story/wait_tick", [f"execute {sc('#wt', '1..')} run {ssub('#wt')}",
                                     f"execute {sc('#wt', '0')} run function {NS}:story/wt_expired"])
    out.function("story/wt_expired", [f"tellraw @a {text_json('[angel] the wait timed out; the story goes on', 'gray')}", sset("#wt", -1),
                                      fn("story/skip")])
    out.function("story/status", [
        "tellraw @a [" + ",".join([
            text_json("[angel] scene "), '{"score":{"name":"#scene","objective":"angel.story"}}', text_json(" step "),
            '{"score":{"name":"#step","objective":"angel.story"}}', text_json(" beat "), '{"score":{"name":"#beat","objective":"angel.story"}}',
            text_json(" wait "), '{"score":{"name":"#wait","objective":"angel.story"}}', text_json(" talking "),
            '{"score":{"name":"#talking","objective":"angel.story"}}', text_json(" mv "),
            '{"score":{"name":"#mv.n","objective":"angel.story"}}', text_json("/"), '{"score":{"name":"#mv.limit","objective":"angel.story"}}']) + "]"])

    # ----------------------------------------------------------------------------------------------------------- ride lock
    out.function("story/t_ride", [sset("#seated", 0),
                                  f"execute {sc('#ride', '1')} as {P()} on vehicle if entity @s[tag=angel.seat_passenger] run {sset('#seated', 1)}",
                                  f"execute {sc('#ride', '1')} {sc('#seated', '0')} if entity @e[tag=angel.seat_passenger,limit=1] as {P()} run function {NS}:story/reseat",
                                  # "Press Left Shift to dismount": the client shows it on the action bar when it learns that it is a passenger.  A new
                                  # seat (one that has not been seen yet) arms #rd, and for the next 80 ticks an EMPTY action bar goes out every tick, which
                                  # overwrites the hint whichever tick the client gets it on.
                                  f"execute {sc('#ride', '1')} as {P()} on vehicle unless entity @s[tag=angel.rd_seen] run function {NS}:story/ride_new",
                                  f"execute {sc('#rd', '1..')} run title {PA()} actionbar {{\"text\":\"\"}}",
                                  f"execute {sc('#rd', '1..')} run {ssub('#rd')}"])
    out.function("story/ride_new", ["tag @s add angel.rd_seen", sset("#rd", 80)])
    out.function("story/reseat", ["ride @s mount @e[tag=angel.seat_passenger,limit=1]", sset("#rd", 80)])
    # the props leave the hotbar: a given letter, photograph or booklet would sit in the selected slot as a big block in the lower right of
    # the picture for the rest of the film.  Whatever lands in the hotbar goes to the same slot of the main inventory (still there to read).
    inv = []
    for k in range(9):
        for it in STORY_ITEMS:
            inv.append(f"execute as @a if items entity @s hotbar.{k} {it} run function {NS}:story/inv_{k}")
        out.function(f"story/inv_{k}", [f"item replace entity @s inventory.{k} from entity @s hotbar.{k}",
                                        f"item replace entity @s hotbar.{k} with minecraft:air"])
    out.function("story/t_inv", [f"scoreboard players operation #ti {OBJ} = #tick {OBJ}", f"scoreboard players operation #ti {OBJ} %= #c5 {OBJ}",
                                 f"execute {sc('#ti', '0')} run function {NS}:story/t_inv_run"])
    out.function("story/t_inv_run", inv)

    # ----------------------------------------------------------------------------------------------------------- look check
    out.function("story/util/looking", [
        sset("#looking", 0),
        f"execute unless entity @e[tag=angel.gaze,limit=1] at {P()} run summon minecraft:marker ~ ~ ~ {{Tags:[\"angel.gaze\",\"{TAG}\"]}}",
        f"execute as {P()} at @s anchored eyes positioned ^ ^ ^1 run tp @e[tag=angel.gaze,limit=1] ~ ~ ~",
        f"execute as {P()} at @s anchored eyes facing entity @e[tag=angel.look_target,limit=1] eyes positioned ^ ^ ^1 "
        f"if entity @e[tag=angel.gaze,distance=..0.55] run {sset('#looking', 1)}"])

    # ----------------------------------------------------------------------------------------------------------- the speak prompt
    build_prompt(out, ctx)

    from objective import build_objectives
    build_objectives(out, ctx)

    # ----------------------------------------------------------------------------------------------------------- rigs and routes
    from movers import write_route, write_mover_system
    for r in ctx.routes.values():
        write_route(out, r)
    write_mover_system(out, list(ctx.routes.values()))
    for name, rig in ctx.rigs.items():
        follow = rig.follow_cmds(seats=True)
        if "driver" in rig.seats:
            follow.append(f"execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag={rig.tag},tag=angel.seat_driver,limit=1] "
                          f"at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] ~ 0")
        out.function(f"story/rig/{name}/follow", follow)
    for (rname, variant), (rig, motions, seats) in ctx.rig_variants.items():
        out.function(f"story/rig/{rname}/spawn_{variant}", rig.spawn_cmds(motions, seats) + rig.settle_cmds(seats))
    ctx.audio.write()
    for path, lines in ctx.extra_functions.items():
        out.function(path, lines)


BUBBLE = "\U0001F4AC"        # U+1F4AC, a speech bubble: a 16 x 16 glyph of the default font's Unifont layer (checked in the 26.3 asset index), drawn in gold

MAIN_SCALE = 0.62            # the panel's text: "Your turn" ~ 12 cm tall letters, readable at 2 to 3 m in a headset
SUB_SCALE = 0.40             # "answer Misato" beneath it, smaller
SUB_DROP = 0.21              # how far under the main line the small one hangs (blocks, in the panel's own frame)
PULSE = 1.28                 # the panel swells by this factor for a moment when the prompt pulses (the nudge of a silent player)
BG = 1711276032              # 40 % black


def _tf(scale, ty=0.0):
    return (f"transformation:{{translation:[0f,{ty:g}f,0f],left_rotation:[0f,0f,0f,1f],scale:[{scale:g}f,{scale:g}f,{scale:g}f],"
            f"right_rotation:[0f,0f,0f,1f]}}")


def build_prompt(out, ctx):
    """The speak prompt: when the story is holding for the player (#wait 1 or 2), nothing is being played and the bridge is not
    speaking, a small two-line panel floats where it is easy to see -- a speech-bubble glyph and "Your turn" in white, and in smaller grey
    letters beneath it what to do ("answer Misato") -- with a soft chime.  It is made of two billboarded text displays (tags angel.prompt,
    angel.prompt_main / angel.prompt_sub) so that the second line can be smaller.  The words go on the action bar too, but ONLY when no
    panel could be placed.  It goes away the moment the wait ends or the bridge starts voicing the answer.

    Placement (never over the speaker's face): near the player the panel hangs between him and her, 0.85 below the line of sight to her eyes;
    farther away (or a voice only) it hangs 2.1 m from his eyes toward her, 0.8 below that line; in a vehicle it is fixed in the vehicle's
    frame ahead of the passenger seat and travels with it.  `angel:story/prompt/pulse` swells it and plays the chime again (the nudge)."""
    variants = ctx.prompt_variants
    for k, text in enumerate(variants):
        main = [{"text": BUBBLE + " ", "color": "gold"}, {"text": "Your turn", "color": "white", "bold": True}]
        loud = text in ctx.prompt_loud                      # the consent wait: the question and what to do, in yellow, bold
        sub = [{"text": text, "color": "yellow", "bold": True}] if loud else [{"text": text, "color": "gray"}]

        def summon(role, comp, ty, scale):
            return (f'summon minecraft:text_display ~ ~ ~ {{Tags:["{TAG}","angel.prompt","angel.prompt_{role}"],billboard:"center",background:{BG},'
                    f'brightness:{{sky:15,block:15}},line_width:400,shadow:1b,see_through:0b,view_range:0.35f,teleport_duration:6,'
                    f'interpolation_duration:8,text:{json.dumps(comp, ensure_ascii=True)},{_tf(0.04, ty * 0.1)}}}')
        out.function(f"story/prompt/v{k}/spawn", [summon("main", main, 0.0, MAIN_SCALE), summon("sub", sub, -SUB_DROP, SUB_SCALE),
                                                  f"schedule function {NS}:story/prompt/pop 2t"])
        out.function(f"story/prompt/v{k}/bar", [f"title {PA()} actionbar " + text_json(f"Your turn - {text}", "yellow" if loud else "gray")])
    ctx.fx_scheduled += ["story/prompt/pop", "story/prompt/pulse_back"]            # halt clears them
    items_spawn = {k: [fn(f"story/prompt/v{k}/spawn")] for k in range(len(variants))}
    items_bar = {k: [fn(f"story/prompt/v{k}/bar")] for k in range(len(variants))}
    dispatch_tree(out, "story/prompt/sp", "#pk", items_spawn)
    dispatch_tree(out, "story/prompt/ba", "#pk", items_bar)
    main_e, sub_e = "@e[tag=angel.prompt_main,limit=1]", "@e[tag=angel.prompt_sub,limit=1]"

    def restyle(factor, dur):
        return [f"data merge entity {main_e} {{start_interpolation:0,interpolation_duration:{dur},{_tf(MAIN_SCALE * factor)}}}",
                f"data merge entity {sub_e} {{start_interpolation:0,interpolation_duration:{dur},{_tf(SUB_SCALE * factor, -SUB_DROP * factor)}}}"]
    out.function("story/prompt/pop", restyle(1.0, 8))
    out.function("story/prompt/pulse", [
        f"execute if entity {main_e} run function {NS}:story/prompt/pulse_go"])
    out.function("story/prompt/pulse_go", [f"execute at {P()} run playsound angel:sfx.speak_chime master {PA()} ~ ~ ~ 0.6 1.0 0.5",
                                           *restyle(PULSE, 4), f"schedule function {NS}:story/prompt/pulse_back 5t"])
    out.function("story/prompt/pulse_back", restyle(1.0, 6))
    out.function("story/prompt/spawn", [fn("story/prompt/sp/root")])
    out.function("story/prompt/bar", [fn("story/prompt/ba/root")])
    # put: spawn the panel at the current position, or move it there (both lines together)
    out.function("story/prompt/put", [sset("#placed", 1),
                                      f"execute unless entity @e[tag=angel.prompt_main,limit=1] run function {NS}:story/prompt/spawn",
                                      "execute if entity @e[tag=angel.prompt_main,limit=1] run tp @e[tag=angel.prompt] ~ ~ ~"])
    # place: decide where it goes
    place = [sset("#placed", 0),
             # riding: fixed in the vehicle's frame, ahead of the passenger seat, so that it travels with the car
             f"execute {sc('#ride', '1')} if entity @e[tag=angel.seat_passenger,limit=1] as @e[tag=angel.seat_passenger,limit=1] at @s "
             f"positioned ^ ^0.75 ^1.7 run function {NS}:story/prompt/put"]
    for i, cid in enumerate(CHARACTERS, 1):
        place.append(f"execute {sc('#placed', '0')} {sc('#speaker', str(i))} {sc(f'#present_{cid}', '1')} "
                     f"if entity @e[tag=angel.{cid},tag=angel.char,limit=1] run function {NS}:story/prompt/at_{cid}")
        c = f"@e[tag=angel.{cid},tag=angel.char,limit=1]"
        out.function(f"story/prompt/at_{cid}", [
            # very close (inside 2.2 m): a metre from his eyes, in front of her and clear of her arms, 0.5 below the line of sight to her eyes (her chest, not her face)
            f"execute as {P()} at @s anchored eyes if entity @e[tag=angel.{cid},tag=angel.char,distance=..2.2] "
            f"facing entity {c} eyes positioned ^ ^-0.5 ^1.0 run function {NS}:story/prompt/put",
            # close to the player: between them, well below the line of sight to her eyes (her face stays clear)
            f"execute {sc('#placed', '0')} as {P()} at @s anchored eyes if entity @e[tag=angel.{cid},tag=angel.char,distance=..3.6] "
            f"facing entity {c} eyes positioned ^ ^-0.7 ^1.5 run function {NS}:story/prompt/put",
            # farther away (across the room, the commander in the booth): near the player, in her direction, below the line to her
            f"execute {sc('#placed', '0')} as {P()} at @s anchored eyes facing entity {c} eyes positioned ^ ^-0.8 ^2.1 run function {NS}:story/prompt/put"])
    place.append(f"execute {sc('#placed', '0')} run function {NS}:story/prompt/at_voice")
    # a voice on the telephone or radio: in front of where the player is looking, and it stays put unless he walks away from it
    out.function("story/prompt/at_voice", [
        f"execute as {P()} at @s anchored eyes unless entity @e[tag=angel.prompt_main,limit=1] positioned ^ ^-0.3 ^2.0 run function {NS}:story/prompt/put",
        f"execute as {P()} at @s anchored eyes if entity @e[tag=angel.prompt_main,limit=1] unless entity @e[tag=angel.prompt_main,distance=..3.4,limit=1] "
        f"positioned ^ ^-0.3 ^2.0 run function {NS}:story/prompt/put"])
    # whatever happened above, a panel standing in the world counts as placed (the action bar says the same words only when it does not)
    place.append(f"execute if entity @e[tag=angel.prompt_main,limit=1] run {sset('#placed', 1)}")
    out.function("story/prompt/place", place)
    out.function("story/prompt/show", ["kill @e[tag=angel.ob_line]", sset("#ob.line", -1), fn("story/prompt/place"),
                                       f"execute at {P()} run playsound angel:sfx.speak_chime master {PA()} ~ ~ ~ 0.6 1.0 0.5",
                                       f"execute {sc('#placed', '0')} run function {NS}:story/prompt/bar"])
    out.function("story/prompt/keep", [
        # in a vehicle the panel is moved every tick, otherwise every fifth
        f"execute {sc('#ride', '1')} run function {NS}:story/prompt/place",
        f"scoreboard players operation #t5 {OBJ} = #tick {OBJ}", f"scoreboard players operation #t5 {OBJ} %= #c5 {OBJ}",
        f"execute {sc('#ride', '0')} {sc('#t5', '0')} run function {NS}:story/prompt/place",
        f"scoreboard players operation #t20 {OBJ} = #tick {OBJ}", f"scoreboard players operation #t20 {OBJ} %= #c20 {OBJ}",
        f"execute {sc('#t20', '0')} {sc('#placed', '0')} run function {NS}:story/prompt/bar"])
    out.function("story/prompt/hide", ["kill @e[tag=angel.prompt]", f"title {PA()} actionbar {{\"text\":\"\"}}"])
    out.function("story/t_prompt", [
        sset("#pw", 0),
        f"execute {sc('#wait', '1..')} {sc('#talking', '0')} unless score #bridge_speaking {OBJ} matches 1.. run {sset('#pw', 1)}",
        f"execute {sc('#pw', '1')} unless entity @e[tag=angel.prompt_main,limit=1] run function {NS}:story/prompt/show",
        f"execute {sc('#pw', '1')} if entity @e[tag=angel.prompt_main,limit=1] run function {NS}:story/prompt/keep",
        f"execute {sc('#pw', '0')} if entity @e[tag=angel.prompt_main,limit=1] run function {NS}:story/prompt/hide"])
