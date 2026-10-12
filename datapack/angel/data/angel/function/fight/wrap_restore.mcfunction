scoreboard players set #shud angel.fight 0
execute if score #wstage angel.fight matches 1 run function angel:angel/pose_wrap_tight
execute unless score #wstage angel.fight matches 1 run function angel:angel/pose_wrapping
