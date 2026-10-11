execute if entity @s[tag=!angel.mounted] run function angel:cast/yaw_flip_self
tag @s remove angel.lying
data merge entity @s {pose:"standing"}
execute if entity @s[tag=angel.mounted] run function angel:cast/align_yaw
execute if entity @s[tag=!angel.mounted] at @s run tp @s ^ ^-0.125 ^-0.9 ~ ~
