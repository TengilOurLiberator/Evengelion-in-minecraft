execute if score #phase angel.fight matches 5 run scoreboard players set #beat angel.story 81
execute if score #beat angel.story matches 81 if score #run angel.fight matches 1 if score #phase angel.fight matches 0..3 run scoreboard players set #beat angel.story 70
execute if score #phase angel.fight matches 1 if score #mus angel.story matches 0 run function angel:story/s7/f_mus_fight
execute if score #phase angel.fight matches 2..3 if score #mus angel.story matches 0..1 run function angel:story/s7/f_mus_final
execute if score #phase angel.fight matches 4 if score #mus angel.story matches 0..2 run function angel:story/s7/f_mus_stop
execute if score #phase angel.fight matches 5 if score #mus angel.story matches 0..2 run function angel:story/s7/f_mus_defeat
execute if score #phase angel.fight matches 0 if score #mus angel.story matches 3 run scoreboard players set #mus angel.story 0
function angel:story/s7/f_guide
execute if score #f.fight_won angel.story matches 1 run function angel:story/s7/x11
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 11 if score #force angel.story matches 1 run function angel:story/s7/x11
