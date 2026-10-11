# footfall at height 100: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)
execute if score #foot angel.mon matches 0 positioned ^9.56 ^ ^19.49 run function angel:angel/fx_foot_100_at
execute if score #foot angel.mon matches 1 positioned ^-9.56 ^ ^19.49 run function angel:angel/fx_foot_100_at
