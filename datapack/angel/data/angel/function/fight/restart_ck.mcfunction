# the checkpoint restart: the giant stays giant (no trip back to the lift), the screen stays black for the pause, then start_ck puts everything
# back where it was when the core cracked
execute as @e[tag=angel.giant] run tag @s add angel.pending
function angel:fight/stop_quiet
execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:blindness 4 0 true
execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:slowness 4 6 true
scoreboard players set #lost_reason angel.fight 0
schedule function angel:fight/restart_ck_go 60t
