scoreboard players set #force angel.story 0
execute as @e[type=minecraft:block_display,tag=angel.part] run data merge entity @s {Glowing:0b}
scoreboard players set #fx.crater angel.story 0
function angel:story/snd/stop_music
scoreboard players set #step angel.story 87
function angel:story/s2/e87
