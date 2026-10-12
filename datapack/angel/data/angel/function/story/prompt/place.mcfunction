scoreboard players set #placed angel.story 0
execute if score #ride angel.story matches 1 if entity @e[tag=angel.seat_passenger,limit=1] as @e[tag=angel.seat_passenger,limit=1] at @s positioned ^ ^0.75 ^1.7 run function angel:story/prompt/put
execute if score #placed angel.story matches 0 if score #speaker angel.story matches 1 if score #present_misato angel.story matches 1 if entity @e[tag=angel.misato,tag=angel.char,limit=1] run function angel:story/prompt/at_misato
execute if score #placed angel.story matches 0 if score #speaker angel.story matches 2 if score #present_ritsuko angel.story matches 1 if entity @e[tag=angel.ritsuko,tag=angel.char,limit=1] run function angel:story/prompt/at_ritsuko
execute if score #placed angel.story matches 0 if score #speaker angel.story matches 3 if score #present_gendo angel.story matches 1 if entity @e[tag=angel.gendo,tag=angel.char,limit=1] run function angel:story/prompt/at_gendo
execute if score #placed angel.story matches 0 if score #speaker angel.story matches 4 if score #present_rei angel.story matches 1 if entity @e[tag=angel.rei,tag=angel.char,limit=1] run function angel:story/prompt/at_rei
execute if score #placed angel.story matches 0 run function angel:story/prompt/at_voice
execute if entity @e[tag=angel.prompt_main,limit=1] run scoreboard players set #placed angel.story 1
