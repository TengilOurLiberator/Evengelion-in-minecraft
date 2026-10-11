# return value: 1 when no line is queued or playing
execute if data storage angel:fight q[0] run return 0
execute if score #talking angel.story matches 1 run return 0
execute if score #gap angel.fight matches 1.. run return 0
return 1
