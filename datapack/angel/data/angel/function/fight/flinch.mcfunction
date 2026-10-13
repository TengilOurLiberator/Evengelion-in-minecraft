# a landed hit throws the monster back flinch_back blocks for flinch_ticks ticks (the parts glide: teleport_duration 2).  Not twice at once, not while it is wrapped
execute if score #fl angel.fight matches 1 run return 0
execute if score #phase angel.fight matches 3.. run return 0
scoreboard players set #fl angel.fight 1
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s run tp @s ^ ^ ^-0.7
function angel:angel/sync
schedule function angel:fight/flinch_back 3t
