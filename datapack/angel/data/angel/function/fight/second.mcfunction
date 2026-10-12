scoreboard players set #t20 angel.fight 0
execute if score #gcalm angel.fight matches 160.. if score #gh angel.fight matches ..99 run scoreboard players add #gh angel.fight 2
execute if score #gh angel.fight matches 101.. run scoreboard players set #gh angel.fight 100
execute if score #gh angel.fight matches 60.. run bossbar set angel:fight/giant color green
execute if score #gh angel.fight matches 30..59 run bossbar set angel:fight/giant color yellow
execute if score #gh angel.fight matches ..29 run bossbar set angel:fight/giant color red
# low health: the giant's heartbeat (a 10 s file: replayed when it has run out, cut when health comes back)
execute if score #hb angel.fight matches 1.. run scoreboard players remove #hb angel.fight 1
execute if score #gh angel.fight matches ..25 unless score #hb angel.fight matches 1.. unless score #phase angel.fight matches 3 run function angel:fight/heartbeat
execute if score #gh angel.fight matches 26.. if score #hb angel.fight matches 1.. run function angel:fight/heartbeat_stop
