# pose idle: a slow loop of two key poses
schedule clear angel:angel/anim_tick
schedule clear angel:angel/die_2
schedule clear angel:angel/die_3
schedule clear angel:angel/charge_2
schedule clear angel:angel/charge_3
scoreboard players set #loop angel.mon 1
scoreboard players set #lp angel.mon 0
scoreboard players set #dur angel.mon 30
function angel:angel/pp/idle_a
schedule function angel:angel/anim_tick 40t
