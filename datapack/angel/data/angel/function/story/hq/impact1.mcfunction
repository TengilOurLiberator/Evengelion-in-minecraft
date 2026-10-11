playsound angel:sfx.impact_above master @a 3096.5 100.0 72.5 4.0 0.85 0.9
function angel:story/hq/rattle
schedule function angel:story/hq/rattle 7t
execute at @a[limit=1] run playsound angel:sfx.lights_flicker master @a ~ ~ ~ 0.8 1.0 1.0
execute at @a[limit=1] run playsound angel:sfx.dust_fall master @a ~ ~ ~ 0.7 1.0 1.0
function angel:story/hq/dust
function angel:story/hq/rings
execute at @a[limit=1] run particle minecraft:falling_dust{block_state:"minecraft:stone"} ~ ~4 ~ 3 1.5 3 0.0 24 force
