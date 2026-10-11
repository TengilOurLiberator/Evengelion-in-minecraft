# footfall at height 40: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^3.82 ^ ^7.80 run function angel:angel/fx_foot_40_at
execute if score #foot angel.mon matches 1 positioned ^-3.82 ^ ^7.80 run function angel:angel/fx_foot_40_at
