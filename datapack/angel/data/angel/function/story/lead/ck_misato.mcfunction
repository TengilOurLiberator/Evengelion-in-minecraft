execute store result score #ckx angel.story as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] run data get entity @s Pos[0] 10
execute store result score #ckz angel.story as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] run data get entity @s Pos[2] 10
scoreboard players operation #ckdx angel.story = #ckx angel.story
scoreboard players operation #ckdx angel.story -= #ckx0_misato angel.story
scoreboard players operation #ckdz angel.story = #ckz angel.story
scoreboard players operation #ckdz angel.story -= #ckz0_misato angel.story
scoreboard players set #ckm angel.story 0
execute unless score #ckdx angel.story matches -2..2 run scoreboard players set #ckm angel.story 1
execute unless score #ckdz angel.story matches -2..2 run scoreboard players set #ckm angel.story 1
execute if score #ckm angel.story matches 1 run scoreboard players set #ckn_misato angel.story 0
execute if score #ckm angel.story matches 0 run scoreboard players add #ckn_misato angel.story 1
scoreboard players operation #ckx0_misato angel.story = #ckx angel.story
scoreboard players operation #ckz0_misato angel.story = #ckz angel.story
execute if score #ckn_misato angel.story matches 3.. if score #arrived_misato angel.cast matches 0 as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s unless entity @a[limit=1,distance=..6.0] run function angel:story/lead/rescue_misato
