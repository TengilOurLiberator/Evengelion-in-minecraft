execute store result score #y0 angel.cast run data get entity @s Rotation[0] 100
execute if entity @s[tag=angel.mounted] on vehicle store result score #y0 angel.cast run data get entity @s Rotation[0] 100
execute if entity @s[tag=angel.lying] run function angel:cast/yaw_lying
function angel:cast/nudge_self
