execute if score #t angel.fight matches ..14 if score #odd angel.fight matches 0 run function angel:fight/aim_track
execute if score #t angel.fight matches 15..25 run function angel:fight/thrust_warn
execute if score #t angel.fight matches 26 run function angel:fight/thrust_strike
