scoreboard players add #lp angel.mon 1
execute if score #lp angel.mon matches 8.. run scoreboard players set #lp angel.mon 0
scoreboard players set #dur angel.mon 9
execute if score #lp angel.mon matches 0 run function angel:angel/pp/regen_0
execute if score #lp angel.mon matches 1 run function angel:angel/pp/regen_1
execute if score #lp angel.mon matches 2 run function angel:angel/pp/regen_2
execute if score #lp angel.mon matches 3 run function angel:angel/pp/regen_3
execute if score #lp angel.mon matches 4 run function angel:angel/pp/regen_4
execute if score #lp angel.mon matches 5 run function angel:angel/pp/regen_5
execute if score #lp angel.mon matches 6 run function angel:angel/pp/regen_6
execute if score #lp angel.mon matches 7 run function angel:angel/pp/regen_7
schedule function angel:angel/anim_tick 10t
