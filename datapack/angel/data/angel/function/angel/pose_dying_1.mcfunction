# pose dying_1 (held until the next pose)
schedule clear angel:angel/anim_tick
schedule clear angel:angel/charge_2
schedule clear angel:angel/charge_3
scoreboard players set #loop angel.mon 0
scoreboard players set #dur angel.mon 30
function angel:angel/pp/die_1
