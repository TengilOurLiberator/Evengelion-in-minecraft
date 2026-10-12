scoreboard players add #nt_medic2 angel.cast 1
execute if score #nt_medic2 angel.cast matches ..5 run return 0
execute if score #np_medic2 angel.cast matches 1 run return run function angel:cast/nud_to2/medic2
function angel:cast/nud_end/medic2
