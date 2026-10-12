function angel:story/s1/f_look40
execute if score #looking angel.story matches 1 run scoreboard players set #f.seen angel.story 1
execute if score #looking angel.story matches 1 run scoreboard players set #v.away angel.story 0
execute if score #f.seen angel.story matches 1 if score #looking angel.story matches 0 run scoreboard players add #v.away angel.story 1
execute if score #v.away angel.story matches 14.. run function angel:story/s1/x34
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 34 if score #stept angel.story matches 120 run function angel:story/s1/t34
execute if score #step angel.story matches 34 if score #force angel.story matches 1 run function angel:story/s1/x34
