scoreboard players set #t20 angel.fight 0
execute if score #gcalm angel.fight matches 160.. if score #gh angel.fight matches ..99 run scoreboard players add #gh angel.fight 2
execute if score #gh angel.fight matches 101.. run scoreboard players set #gh angel.fight 100
execute if score #gh angel.fight matches 60.. run bossbar set angel:fight/giant color green
execute if score #gh angel.fight matches 30..59 run bossbar set angel:fight/giant color yellow
execute if score #gh angel.fight matches ..29 run bossbar set angel:fight/giant color red
