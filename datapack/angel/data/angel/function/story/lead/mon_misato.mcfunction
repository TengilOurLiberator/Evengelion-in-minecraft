execute if score #f.lp_misato angel.story matches 0 if score #arrived_misato angel.cast matches 0 as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s unless entity @a[limit=1,distance=..9.0] run function angel:story/lead/pause_misato
execute if score #f.lp_misato angel.story matches 1 as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/lead/resume_misato
scoreboard players set #c9 angel.story 9
scoreboard players operation #lm angel.story = #tick angel.story
scoreboard players operation #lm angel.story %= #c9 angel.story
execute if score #lm angel.story matches 0 unless score #hush angel.story matches 1 if score #f.lp_misato angel.story matches 0 if score #arrived_misato angel.cast matches 0 as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s run playsound minecraft:block.deepslate_tiles.step master @a ~ ~ ~ 0.6 0.95 0.15
