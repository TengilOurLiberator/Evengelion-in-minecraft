# the barrier comes down and the monster is free to advance again
scoreboard players set #hold angel.fight 0
scoreboard players set #bar angel.fight 0
scoreboard players set #barp angel.fight 0
scoreboard players set #nav angel.fight 99
execute if score #phase angel.fight matches 1 run bossbar set angel:fight/angel name {"text":"ANGEL","color":"red"}
execute if score #phase angel.fight matches 2 run bossbar set angel:fight/angel name {"text":"ANGEL  -  core cracked","color":"red"}
# the barrier comes down: a distinct cue (high tone, chime, flash and a burst of light) and the look follows at once (burning core if he is in reach, else the octagon of range)
scoreboard players set #blk_n angel.fight 0
scoreboard players set #blk_why angel.fight 0
function angel:fight/vis_state
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run function angel:fight/drop_cue
function angel:fight/shield_flare
