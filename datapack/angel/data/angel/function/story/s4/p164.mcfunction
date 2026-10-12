execute as @e[type=minecraft:mannequin,tag=angel.ritsuko,limit=1] at @s if entity @a[limit=1,distance=..11.0] run function angel:story/s4/x164
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 164 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 164 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s4/sk164
execute if score #step angel.story matches 164 if score #stept angel.story matches 1800 run function angel:story/s4/t164
execute if score #step angel.story matches 164 if score #force angel.story matches 1 run function angel:story/s4/x164
