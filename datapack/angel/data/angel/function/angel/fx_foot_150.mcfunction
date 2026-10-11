# footfall at height 150: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^14.34 ^ ^29.24 run function angel:angel/fx_foot_150_at
execute if score #foot angel.mon matches 1 positioned ^-14.34 ^ ^29.24 run function angel:angel/fx_foot_150_at
