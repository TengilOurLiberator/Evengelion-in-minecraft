# pose charging: stage 1 now, stage 2 after 10 ticks, stage 3 after 24 (the beam fires at 34 / 40)
schedule clear angel:angel/anim_tick
schedule clear angel:angel/die_2
schedule clear angel:angel/die_3
scoreboard players set #loop angel.mon 0
scoreboard players set #dur angel.mon 10
function angel:angel/pp/charge
schedule function angel:angel/charge_2 10t
schedule function angel:angel/charge_3 24t
