execute if entity @s[tag=angel.lying] run return 0
$execute if entity @s[tag=angel.sitting] run function angel:cast/unsit {id:"$(id)"}
execute if entity @s[tag=!angel.mounted] run tp @s ^ ^0.125 ^0.9 ~ ~
tag @s add angel.lying
data merge entity @s {pose:"sleeping",immovable:1b,NoGravity:1b}
function angel:cast/align_yaw
