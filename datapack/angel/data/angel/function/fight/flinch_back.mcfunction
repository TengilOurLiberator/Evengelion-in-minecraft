scoreboard players set #fl angel.fight 0
execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0
execute if score #phase angel.fight matches 3.. run return 0
# (a back-off that began meanwhile moves it by itself)
execute if score #st angel.fight matches 9..10 run return 0
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s run tp @s ^ ^ ^0.7
function angel:angel/sync
