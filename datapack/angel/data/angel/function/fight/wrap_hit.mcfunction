# a landed hit while the monster is wrapped round the giant (phase 3).  No guard, no reach: it always counts.  Feedback: the core flashes and cracks further
# (crack 1..4 as the hits left fall), the wrap shudders (pose wrap_hit), sfx.giant_punch, the countdown bar jumps back (wrap_bonus), the hits left on the action bar
execute if score #phase angel.fight matches 4.. run return 0
scoreboard players remove #ch angel.fight 1
execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0
scoreboard players add #whits angel.fight 1
execute if score #st angel.fight matches 7 run scoreboard players add #wt angel.fight 10
execute if score #wt angel.fight matches 321.. run scoreboard players set #wt angel.fight 320
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run function angel:fight/wrap_hit_fx
execute if score #st angel.fight matches 7 run scoreboard players set #shud angel.fight 4
execute if score #st angel.fight matches 7 run function angel:angel/pose_wrap_hit
execute if score #ch angel.fight matches ..8 run function angel:angel/core_crack_1
execute if score #ch angel.fight matches ..6 run function angel:angel/core_crack_2
execute if score #ch angel.fight matches ..4 run function angel:angel/core_crack_3
execute if score #ch angel.fight matches ..2 run function angel:angel/core_crack_4
execute as @e[tag=angel.giant,type=minecraft:player] run title @s actionbar [{"text":"CORE  ","color":"red","bold":true},{"score":{"name":"#ch","objective":"angel.fight"},"color":"white","bold":true},{"text":"  to go","color":"gray"}]
execute if score #ch angel.fight matches ..0 run function angel:fight/won_start
