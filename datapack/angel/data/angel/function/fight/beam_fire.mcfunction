scoreboard players set #st angel.fight 2
scoreboard players set #t angel.fight 0
kill @e[type=minecraft:marker,tag=angel.bi]
kill @e[type=minecraft:marker,tag=angel.bo]
scoreboard players set #rs angel.fight 150
scoreboard players set #bs angel.fight 0
scoreboard players set #dur angel.mon 8
function angel:angel/pose_idle
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^25.36 ^5.35 run summon minecraft:marker ~ ~ ~ {Tags:["angel.fight","angel.bo"]}
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^25.36 ^5.35 facing entity @e[type=minecraft:marker,tag=angel.aimpt,limit=1] feet run function angel:fight/beam_step
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound angel:sfx.beam_fire hostile @a ~ ~ ~ 9 1
execute if entity @e[type=minecraft:marker,tag=angel.bi] run function angel:fight/beam_visual
