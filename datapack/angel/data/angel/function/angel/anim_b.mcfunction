scoreboard players set #lp angel.mon 1
execute if score #loop angel.mon matches 1 run scoreboard players set #dur angel.mon 40
execute if score #loop angel.mon matches 1 run function angel:angel/pp/idle_b
execute if score #loop angel.mon matches 1 run schedule function angel:angel/anim_tick 40t
