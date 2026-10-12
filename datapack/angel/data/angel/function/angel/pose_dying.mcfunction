# the death: knees buckle, it folds, falls back (about 4 seconds); the core goes dark
schedule clear angel:angel/anim_tick
schedule clear angel:angel/charge_2
schedule clear angel:angel/charge_3
scoreboard players set #walking angel.mon 0
function angel:angel/pose_dying_1
function angel:angel/core_stage {stage:2}
schedule function angel:angel/die_2 30t
schedule function angel:angel/die_3 70t
