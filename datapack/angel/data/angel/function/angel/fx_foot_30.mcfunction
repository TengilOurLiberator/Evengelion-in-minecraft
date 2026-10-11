# footfall at height 30: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^2.87 ^ ^5.85 run function angel:angel/fx_foot_30_at
execute if score #foot angel.mon matches 1 positioned ^-2.87 ^ ^5.85 run function angel:angel/fx_foot_30_at
