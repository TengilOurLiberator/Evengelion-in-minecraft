# pose wrap_tight (held until the next pose)
schedule clear angel:angel/anim_tick
schedule clear angel:angel/charge_2
schedule clear angel:angel/charge_3
schedule clear angel:angel/die_2
schedule clear angel:angel/die_3
scoreboard players set #loop angel.mon 0
scoreboard players set #dur angel.mon 10
function angel:angel/pp/wrap_tight
