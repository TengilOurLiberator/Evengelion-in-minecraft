# the beam warning may repeat, with a cooldown, and only if nothing else is waiting
execute if score #cd09 angel.fight matches 1.. run return 0
execute if score #talking angel.story matches 1 run return 0
execute if data storage angel:fight q[0] run return 0
scoreboard players set #cd09 angel.fight 400
data modify storage angel:fight q append value {id:"7_09"}
