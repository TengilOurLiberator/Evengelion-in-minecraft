execute if score #arrived_misato angel.cast matches 1 if data storage angel:story cq.misato[0] run function angel:story/lead/cq_next_misato
scoreboard players operation #lm angel.story = #tick angel.story
scoreboard players set #c9 angel.story 9
scoreboard players operation #lm angel.story %= #c9 angel.story
execute if score #lm angel.story matches 0 unless score #hush angel.story matches 1 if score #arrived_misato angel.cast matches 0 as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s run playsound minecraft:block.deepslate_tiles.step master @a ~ ~ ~ 0.6 0.95 0.15
scoreboard players operation #lk angel.story = #tick angel.story
scoreboard players operation #lk angel.story %= #c20 angel.story
execute if score #lk angel.story matches 0 run function angel:story/lead/ck_misato
