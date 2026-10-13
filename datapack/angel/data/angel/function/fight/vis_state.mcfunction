# the one test: can a swing at the core count right now?  #vuln 1 = the barrier is down AND the giant is within arm's length of the core (or the monster is wrapped).
# On a change the look is switched (vis_hot / vis_dim).
execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0
execute if score #phase angel.fight matches 4.. run return 0
scoreboard players set #inreach angel.fight 0
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~-19.00 ~ store success score #inreach angel.fight if entity @e[tag=angel.giant,distance=..12.5]
scoreboard players set #vuln angel.fight 0
execute if score #inreach angel.fight matches 1 if score #bar angel.fight matches 0 run scoreboard players set #vuln angel.fight 1
execute if score #phase angel.fight matches 3 run scoreboard players set #vuln angel.fight 1
execute if score #vuln angel.fight matches 1 unless score #vs angel.fight matches 1 run function angel:fight/vis_hot
execute if score #vuln angel.fight matches 0 unless score #vs angel.fight matches 2 run function angel:fight/vis_dim
