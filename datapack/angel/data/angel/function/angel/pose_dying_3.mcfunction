# pose dying_3 (held until the next pose)
schedule clear angel:angel/anim_tick
scoreboard players set #loop angel.mon 0
scoreboard players set #dur angel.mon 30
function angel:angel/pp/die_3
