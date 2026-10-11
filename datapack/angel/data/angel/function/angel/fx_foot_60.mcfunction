# footfall at height 60: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^5.74 ^ ^11.70 run function angel:angel/fx_foot_60_at
execute if score #foot angel.mon matches 1 positioned ^-5.74 ^ ^11.70 run function angel:angel/fx_foot_60_at
