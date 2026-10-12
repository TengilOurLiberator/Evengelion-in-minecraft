scoreboard players set #force angel.story 0
execute as @e[type=minecraft:block_display,tag=angel.mon] run data merge entity @s {Glowing:1b,glow_color_override:16744448}
scoreboard players set #fx.crater angel.story 1
scoreboard players set #step angel.story 83
function angel:story/s2/e83
