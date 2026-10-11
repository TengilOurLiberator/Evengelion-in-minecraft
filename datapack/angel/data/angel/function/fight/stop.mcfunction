# function angel:fight/stop   removes every entity of the fight and returns the player to human size
execute as @e[tag=angel.giant] run function angel:fight/become_human
function angel:fight/stop_quiet
scoreboard players set #test angel.fight 0
kill @e[tag=angel.test]
