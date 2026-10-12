execute positioned 65.5 64.5 115.5 if entity @a[limit=1,distance=..1.8] run function angel:story/s1/x16
execute if score #step angel.story matches 16 if data entity @e[tag=angel.ia_phone,limit=1] interaction run function angel:story/s1/x16
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 16 if score #stept angel.story matches 3000 run function angel:story/s1/t16
execute if score #step angel.story matches 16 if score #stept angel.story matches 900 run function angel:story/s1/h16
execute if score #step angel.story matches 16 if score #force angel.story matches 1 run function angel:story/s1/x16
