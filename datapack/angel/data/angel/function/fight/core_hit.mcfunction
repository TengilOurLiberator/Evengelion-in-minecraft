data remove entity @s attack
execute if score #hitcd angel.fight matches 1.. run return 0
execute if score #phase angel.fight matches 4.. run return 0
scoreboard players set #hitcd angel.fight 7
# the giant's reach point is 22.0 up; the box's foot is half its height below the core centre
execute positioned ~ ~-19.75 ~ if entity @e[tag=angel.giant,distance=..12.5] run return run function angel:fight/core_land
function angel:fight/core_blocked
