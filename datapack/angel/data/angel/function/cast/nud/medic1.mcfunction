scoreboard players add #nt_medic1 angel.cast 1
execute if score #nt_medic1 angel.cast matches ..5 run return 0
execute if score #np_medic1 angel.cast matches 1 run return run function angel:cast/nud_to2/medic1
function angel:cast/nud_end/medic1
