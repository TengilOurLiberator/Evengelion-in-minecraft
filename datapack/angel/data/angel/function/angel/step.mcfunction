# a step boundary: the foot that was moving forward has landed (fx), the other leg starts to swing
execute if score #landed angel.mon matches 1 run function angel:angel/fx_foot
scoreboard players set #landed angel.mon 1
scoreboard players set #dur angel.mon 0
scoreboard players operation #dur angel.mon = #T angel.mon
execute if score #foot angel.mon matches 0 run scoreboard players set #nextfoot angel.mon 1
execute if score #foot angel.mon matches 1 run scoreboard players set #nextfoot angel.mon 0
scoreboard players operation #foot angel.mon = #nextfoot angel.mon
scoreboard players operation #step angel.mon = #T angel.mon
execute if score #foot angel.mon matches 0 run function angel:angel/pp/walk_l
execute if score #foot angel.mon matches 1 run function angel:angel/pp/walk_r
