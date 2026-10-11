# back to human scale at a safe spot, everything cleaned up, then the story takes over
execute as @e[tag=angel.giant] run function angel:fight/leave_giant
function angel:fight/stop_quiet
scoreboard players set #test angel.fight 0
function angel:fight/hand_won
