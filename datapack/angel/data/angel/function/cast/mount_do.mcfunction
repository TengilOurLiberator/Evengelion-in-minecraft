$execute if entity @s[tag=angel.sitting] run function angel:cast/unsit {id:"$(id)"}
$scoreboard players set #walk_$(id) angel.cast 0
data merge entity @s {immovable:1b,NoGravity:1b}
$execute store success score #ok angel.cast run ride @s mount @e[tag=$(tag),sort=nearest,limit=1]
execute if score #ok angel.cast matches 1 run tag @s add angel.mounted
execute if score #ok angel.cast matches 1 run function angel:cast/align_yaw
scoreboard players set #active angel.cast 1
