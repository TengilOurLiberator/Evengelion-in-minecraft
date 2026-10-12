"""The fixed part of the datapack: load, tick, halt, start/stop/scene/skip, the bridge's two entry points, the speak prompt, the ride lock,
the look check, and the rig functions.  Scenes are compiled by engine.py; this file wires them in."""
import json

from core import (CAST_IDS, CFG, CHARACTERS, DISPLAY_NAMES, NS, OBJ, PA, P, T, TAG, dispatch_tree, fn, num, sadd, sc, sset, ssub)

TICK_TAG_PLAYER = "@a[limit=1]"


def player_any():
    return P()


def text_json(s, color="white", **kw):
    d = {"text": s, "color": color}
    d.update(kw)
    return json.dumps(d, ensure_ascii=False)


def build_system(out, ctx):
    scenes = sorted(ctx.scenes, key=lambda s: s.n)
    flags = sorted(ctx.flags)

    # ----------------------------------------------------------------------------------------------------------- load
    defaults = {"#beat": 0, "#wait": 0, "#speaker": 0, "#talking": 0, "#lastspoke": 0, "#bridge_speaking": 0, "#running": 0,
                "#scene": 0, "#step": -1, "#mv.on": 0, "#mv.n": 0, "#mv.limit": 0, "#mv.route": 0, "#ride": 0, "#timeout_s": 0,
                "#subtitles": CFG.subtitles_default, "#line_left": 0, "#sleep": 0, "#force": 0, "#tick": 0, "#wt": -1, "#consent": 0,
                "#c5": 5, "#c20": 20, "#looking": 0, "#pk": 0, "#line": 0}
    for c in CHARACTERS:
        defaults[f"#present_{c}"] = 0
    load = [f"scoreboard objectives add {OBJ} dummy"]
    for k, v in defaults.items():
        load.append(f"execute unless score {k} {OBJ} matches -2147483648..2147483647 run {sset(k, v)}")
    load += [sset("#c5", 5), sset("#c20", 20)]
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
            fn("story/t_prompt")]
    for sc_ in scenes:
        tick.append(f"execute if score #scene {OBJ} matches {sc_.n} run function {NS}:story/s{sc_.n}/poll")
    tick.append(fn("story/t_fx"))
    out.function("story/tick", tick)
    # t_fx: continuous effects that scenes switch on with flags (aircraft orbit etc.)
    out.function("story/t_fx", ctx.fx_tick or ["# no continuous effects"])
    out.function("story/t_line", [f"execute {sc('#talking', '1')} run {ssub('#line_left')}",
                                  f"execute {sc('#talking', '1')} {sc('#line_left', '..0')} run {sset('#talking', 0)}"])

    # ----------------------------------------------------------------------------------------------------------- halt
    halt = ["# stop everything the story started: timers, entities, cast, monster, forceloads, scene flags"]
    for path in sorted(set(ctx.all_scheduled())):
        halt.append(f"schedule clear {NS}:{path}")
    halt += [f"kill @e[tag={TAG}]"]
    for cid in CAST_IDS:
        halt.append(f'function {NS}:cast/remove {{id:"{cid}"}}')
    halt.append(f"function {NS}:cast/gurney_remove")          # the hospital gurney (cast entities carry no story tag)
    halt.append(f"function {NS}:story/snd/stop_all")           # ambience beds, music, their restart timers
    halt += ctx.halt_extra
    halt.append(f"function {NS}:angel/remove")
    for (x, z) in sorted(ctx.forceloads):
        halt.append(f"forceload remove {x} {z}")
    halt += [sset("#wait", 0), sset("#talking", 0), sset("#line_left", 0), sset("#mv.on", 0), sset("#ride", 0), sset("#consent", 0)]
    halt += [sset(f"#fx.{f}", 0) for f in sorted(ctx.fx_flags)]
    halt += [sset(f"#f.{f}", 0) for f in flags]
    halt += [f"execute {sc('#bridge_speaking', '..-1')} run {sset('#bridge_speaking', 0)}"]
    out.function("story/halt", halt)

    # ----------------------------------------------------------------------------------------------------------- entry points
    out.function("story/scene", [f"$function {NS}:story/s$(n)/begin"])
    out.function("story/start", [fn("story/load"), *ctx.stop_extra, fn("story/halt"), "stopsound @a voice", f"effect clear {PA()} minecraft:blindness",
                                 sset("#running", 1), sset("#consent", 0),
                                 f"gamemode adventure {PA()}",
                                 f"function {NS}:story/scene {{n:1}}"])
    out.function("story/stop", [*ctx.stop_extra, fn("story/halt"), sset("#running", 0), sset("#scene", 0), sset("#step", -1), "stopsound @a voice",
                                f"effect clear {PA()} minecraft:blindness",
                                f"tellraw @a {text_json('[angel] story stopped', 'gray')}"])
    out.function("story/skip", [f"execute {sc('#wait', '1..')} run tellraw @a {text_json('[angel] wait skipped', 'gray')}",
                                sset("#wait", 0)])
    out.function("story/next", [fn("story/skip"),
                                sset("#talking", 0), sset("#line_left", 0), "stopsound @a voice",
                                sset("#force", 1), f"tellraw @a {text_json('[angel] step skipped', 'gray')}"])
    out.function("story/answered", [f"execute {sc('#wait', '1')} run {sset('#wait', 0)}"])
    out.function("story/consented", [f"execute {sc('#wait', '1..')} run {sset('#wait', 0)}", sset("#consent", 1)])
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
                                  f"execute {sc('#ride', '1')} {sc('#seated', '0')} if entity @e[tag=angel.seat_passenger,limit=1] as {P()} run function {NS}:story/reseat"])
    out.function("story/reseat", ["ride @s mount @e[tag=angel.seat_passenger,limit=1]"])

    # ----------------------------------------------------------------------------------------------------------- look check
    out.function("story/util/looking", [
        sset("#looking", 0),
        f"execute unless entity @e[tag=angel.gaze,limit=1] at {P()} run summon minecraft:marker ~ ~ ~ {{Tags:[\"angel.gaze\",\"{TAG}\"]}}",
        f"execute as {P()} at @s anchored eyes positioned ^ ^ ^1 run tp @e[tag=angel.gaze,limit=1] ~ ~ ~",
        f"execute as {P()} at @s anchored eyes facing entity @e[tag=angel.look_target,limit=1] eyes positioned ^ ^ ^1 "
        f"if entity @e[tag=angel.gaze,distance=..0.55] run {sset('#looking', 1)}"])

    # ----------------------------------------------------------------------------------------------------------- the speak prompt
    build_prompt(out, ctx)

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


def build_prompt(out, ctx):
    """The speak prompt: when the story is holding for the player (#wait 1 or 2), nothing is being played and the bridge is not
    speaking, a small panel floats where it is easy to see -- a few dots and "Your turn - answer Misato" -- with a soft chime and the same
    words on the action bar.  It goes away the moment the wait ends or the bridge starts voicing the answer."""
    variants = ctx.prompt_variants
    for k, text in enumerate(variants):
        body = [{"text": "â— â— â—\n", "color": "gold", "bold": False},
                {"text": "Your turn", "color": "white", "bold": True},
                {"text": f" - {text}", "color": "gray"}]
        out.function(f"story/prompt/v{k}/spawn", [
            f'summon minecraft:text_display ~ ~ ~ {{Tags:["{TAG}","angel.prompt"],billboard:"center",background:1711276032,'
            f'brightness:{{sky:15,block:15}},line_width:400,shadow:1b,see_through:0b,view_range:0.35f,teleport_duration:6,'
            f'interpolation_duration:8,text:{json.dumps(body, ensure_ascii=False)},'
            f'transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[0.04f,0.04f,0.04f],right_rotation:[0f,0f,0f,1f]}}}}',
            f"schedule function {NS}:story/prompt/pop 2t"])
        out.function(f"story/prompt/v{k}/bar", [f"title {PA()} actionbar " + text_json(f"Your turn - {text}", "gray")])
    items_spawn = {k: [fn(f"story/prompt/v{k}/spawn")] for k in range(len(variants))}
    items_bar = {k: [fn(f"story/prompt/v{k}/bar")] for k in range(len(variants))}
    dispatch_tree(out, "story/prompt/sp", "#pk", items_spawn)
    dispatch_tree(out, "story/prompt/ba", "#pk", items_bar)
    out.function("story/prompt/pop", [
        'data merge entity @e[tag=angel.prompt,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:'
        '{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[0.32f,0.32f,0.32f],right_rotation:[0f,0f,0f,1f]}}'])
    out.function("story/prompt/spawn", [fn("story/prompt/sp/root")])
    out.function("story/prompt/bar", [fn("story/prompt/ba/root")])
    # put: spawn the panel at the current position, or move it there
    out.function("story/prompt/put", [sset("#placed", 1),
                                      f"execute unless entity @e[tag=angel.prompt,limit=1] run function {NS}:story/prompt/spawn",
                                      "execute if entity @e[tag=angel.prompt,limit=1] run tp @e[tag=angel.prompt,limit=1] ~ ~ ~"])
    # place: decide where it goes
    place = [sset("#placed", 0),
             # riding: fixed in the vehicle's frame, ahead of the passenger seat, so that it travels with the car
             f"execute {sc('#ride', '1')} if entity @e[tag=angel.seat_passenger,limit=1] as @e[tag=angel.seat_passenger,limit=1] at @s "
             f"positioned ^ ^0.95 ^1.5 run function {NS}:story/prompt/put"]
    for i, cid in enumerate(CHARACTERS, 1):
        place.append(f"execute {sc('#placed', '0')} {sc('#speaker', str(i))} {sc(f'#present_{cid}', '1')} "
                     f"if entity @e[tag=angel.{cid},tag=angel.char,limit=1] run function {NS}:story/prompt/at_{cid}")
        c = f"@e[tag=angel.{cid},tag=angel.char,limit=1]"
        out.function(f"story/prompt/at_{cid}", [
            # close to the player: a metre from his eyes toward the character
            f"execute as {P()} at @s anchored eyes if entity @e[tag=angel.{cid},tag=angel.char,distance=..3.3] "
            f"facing entity {c} eyes positioned ^ ^-0.2 ^1.0 run function {NS}:story/prompt/put",
            # across the room: two and a half metres in front of the character, toward the player
            f"execute {sc('#placed', '0')} at {c} anchored eyes if entity {P('distance=..26')} "
            f"facing entity {P()} eyes positioned ^ ^-0.3 ^2.5 run function {NS}:story/prompt/put",
            # a long way off (the commander in the booth): close to the player, in the direction of the voice
            f"execute {sc('#placed', '0')} as {P()} at @s anchored eyes facing entity {c} eyes positioned ^ ^-0.2 ^1.8 run function {NS}:story/prompt/put"])
    place.append(f"execute {sc('#placed', '0')} run function {NS}:story/prompt/at_voice")
    # a voice on the telephone or radio: in front of where the player is looking, and it stays put unless he walks away from it
    out.function("story/prompt/at_voice", [
        f"execute as {P()} at @s anchored eyes unless entity @e[tag=angel.prompt,limit=1] positioned ^ ^-0.2 ^1.7 run function {NS}:story/prompt/put",
        f"execute as {P()} at @s anchored eyes if entity @e[tag=angel.prompt,limit=1] unless entity @e[tag=angel.prompt,distance=..2.8,limit=1] "
        f"positioned ^ ^-0.2 ^1.7 run function {NS}:story/prompt/put"])
    out.function("story/prompt/place", place)
    out.function("story/prompt/show", [fn("story/prompt/place"),
                                       f"execute at {P()} run playsound angel:sfx.speak_chime master {PA()} ~ ~ ~ 0.6 1.0 0.5",
                                       fn("story/prompt/bar")])
    out.function("story/prompt/keep", [
        # in a vehicle the panel is moved every tick, otherwise every fifth
        f"execute {sc('#ride', '1')} run function {NS}:story/prompt/place",
        f"scoreboard players operation #t5 {OBJ} = #tick {OBJ}", f"scoreboard players operation #t5 {OBJ} %= #c5 {OBJ}",
        f"execute {sc('#ride', '0')} {sc('#t5', '0')} run function {NS}:story/prompt/place",
        f"scoreboard players operation #t20 {OBJ} = #tick {OBJ}", f"scoreboard players operation #t20 {OBJ} %= #c20 {OBJ}",
        f"execute {sc('#t20', '0')} run function {NS}:story/prompt/bar"])
    out.function("story/prompt/hide", ["kill @e[tag=angel.prompt]", f"title {PA()} actionbar {{\"text\":\"\"}}"])
    out.function("story/t_prompt", [
        sset("#pw", 0),
        f"execute {sc('#wait', '1..')} {sc('#talking', '0')} unless score #bridge_speaking {OBJ} matches 1.. run {sset('#pw', 1)}",
        f"execute {sc('#pw', '1')} unless entity @e[tag=angel.prompt,limit=1] run function {NS}:story/prompt/show",
        f"execute {sc('#pw', '1')} if entity @e[tag=angel.prompt,limit=1] run function {NS}:story/prompt/keep",
        f"execute {sc('#pw', '0')} if entity @e[tag=angel.prompt,limit=1] run function {NS}:story/prompt/hide"])

