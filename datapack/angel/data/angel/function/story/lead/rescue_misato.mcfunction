scoreboard players set #ckn_misato angel.story 0
tag @e[tag=angel.cp,tag=angel.cp_misato] remove angel.cp_pick
tag @e[tag=angel.cp,tag=angel.cp_misato] remove angel.cp_chosen
execute as @a[limit=1] at @s rotated ~ 0 positioned ^ ^ ^8 as @e[tag=angel.cp,tag=angel.cp_misato,distance=9..] at @s if entity @a[limit=1,distance=3.5..6.5] run tag @s add angel.cp_pick
execute unless entity @e[tag=angel.cp_pick,tag=angel.cp_misato] as @a[limit=1] at @s as @e[tag=angel.cp,tag=angel.cp_misato] at @s if entity @a[limit=1,distance=3.5..10] run tag @s add angel.cp_pick
execute unless entity @e[tag=angel.cp_pick,tag=angel.cp_misato] run return 0
execute as @a[limit=1] at @s as @e[sort=nearest,limit=1,tag=angel.cp_pick,tag=angel.cp_misato] run tag @s add angel.cp_chosen
execute at @e[tag=angel.cp_chosen,limit=1] run tp @e[type=minecraft:mannequin,tag=angel.misato,limit=1] ~ ~ ~
function angel:story/lead/cpd_misato
tag @e[tag=angel.cp,tag=angel.cp_misato] remove angel.cp_pick
tag @e[tag=angel.cp,tag=angel.cp_misato] remove angel.cp_chosen
scoreboard players set #arrived_misato angel.cast 1
