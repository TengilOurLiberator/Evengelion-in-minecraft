# the beam itself: a thick white core and a wide yellow glow, from the eyes to where it ended; fades fast
execute store result storage angel:fight beam.len double 1 run scoreboard players get #bs angel.fight
execute at @e[type=minecraft:marker,tag=angel.bo,limit=1] run function angel:fight/beam_draw with storage angel:fight beam
execute as @e[type=minecraft:block_display,tag=angel.wnew] at @s run rotate @s facing entity @e[type=minecraft:marker,tag=angel.bi,limit=1] feet
tag @e[tag=angel.wnew] remove angel.wnew
schedule function angel:fight/fx_fade 4t
schedule function angel:fight/fx_clear 14t
