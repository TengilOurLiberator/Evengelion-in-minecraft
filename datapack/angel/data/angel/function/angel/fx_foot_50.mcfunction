# footfall at height 50: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^4.78 ^ ^9.75 run function angel:angel/fx_foot_50_at
execute if score #foot angel.mon matches 1 positioned ^-4.78 ^ ^9.75 run function angel:angel/fx_foot_50_at
