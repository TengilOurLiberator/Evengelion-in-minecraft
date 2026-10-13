# arrived (or gave up): it turns to face the giant again (st_move does that), holds its ground, and attacks soon
scoreboard players set #st angel.fight 0
scoreboard players set #t angel.fight 0
scoreboard players set #hold angel.fight 1
scoreboard players set #hold_t angel.fight 0
scoreboard players set #cd angel.fight 30
execute unless score #arrived angel.walk matches 1 run function angel:angel/stop_walking
execute unless score #arrived angel.walk matches 1 run scoreboard players set #dur angel.mon 20
execute unless score #arrived angel.walk matches 1 run function angel:angel/pose_idle
