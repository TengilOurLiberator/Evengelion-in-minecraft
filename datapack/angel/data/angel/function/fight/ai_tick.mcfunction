execute if score #phase angel.fight matches 0 run function angel:fight/intro_tick
execute if score #phase angel.fight matches 0 run return 0
execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0
execute if score #cd angel.fight matches 1.. run scoreboard players remove #cd angel.fight 1
scoreboard players add #t angel.fight 1
scoreboard players operation #odd angel.fight = #t angel.fight
scoreboard players operation #odd angel.fight %= #2 angel.fight
execute if score #st angel.fight matches 0 run function angel:fight/st_move
execute if score #st angel.fight matches 1 run function angel:fight/st_beam
execute if score #st angel.fight matches 2 run function angel:fight/st_beam_rec
execute if score #st angel.fight matches 3 run function angel:fight/st_thrust
execute if score #st angel.fight matches 4 run function angel:fight/st_thrust_rec
execute if score #st angel.fight matches 5 run function angel:fight/st_stagger
execute if score #st angel.fight matches 6 run function angel:fight/st_wrap_in
execute if score #st angel.fight matches 7 run function angel:fight/st_wrapped
execute if score #st angel.fight matches 9 run function angel:fight/st_bo_stagger
execute if score #st angel.fight matches 10 run function angel:fight/st_bo_retreat
