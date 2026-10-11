# footfall at height 80: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^7.65 ^ ^15.59 run function angel:angel/fx_foot_80_at
execute if score #foot angel.mon matches 1 positioned ^-7.65 ^ ^15.59 run function angel:angel/fx_foot_80_at
