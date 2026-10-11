# after the defeat bark: restore, put the giant back at the launch, and begin again a moment later
execute as @e[tag=angel.giant] run tag @s add angel.pending
execute as @e[tag=angel.giant] run function angel:fight/leave_giant
function angel:fight/stop_quiet
scoreboard players set #lost_reason angel.fight 0
schedule function angel:fight/restart_go 60t
