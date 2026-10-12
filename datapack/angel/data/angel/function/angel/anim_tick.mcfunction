execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0
execute if score #walking angel.mon matches 1 run return 0
execute if score #loop angel.mon matches 0 run return 0
execute if score #loop angel.mon matches 2 run return run function angel:angel/anim_r
execute if score #lp angel.mon matches 0 run return run function angel:angel/anim_b
function angel:angel/anim_a
