execute as @e[tag=angel.gurney_root,limit=1] at @s run function angel:cast/gm_step_root
execute unless entity @e[tag=angel.gurney_root,limit=1] run scoreboard players set #gmove angel.cast 0
