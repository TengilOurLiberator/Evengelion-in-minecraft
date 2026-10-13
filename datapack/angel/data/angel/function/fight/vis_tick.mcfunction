function angel:fight/vis_state
execute if score #vs angel.fight matches 1 run function angel:fight/hot_tick
execute if score #vs angel.fight matches 2 run function angel:fight/shield_follow
