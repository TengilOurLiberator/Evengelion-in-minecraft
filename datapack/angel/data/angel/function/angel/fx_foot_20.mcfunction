# footfall at height 20: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^1.91 ^ ^3.90 run function angel:angel/fx_foot_20_at
execute if score #foot angel.mon matches 1 positioned ^-1.91 ^ ^3.90 run function angel:angel/fx_foot_20_at
