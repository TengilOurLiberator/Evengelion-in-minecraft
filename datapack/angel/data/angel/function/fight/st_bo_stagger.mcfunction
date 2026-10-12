# it is thrown back 4.8 blocks in the first 6 ticks, reels, then turns its back (8 degrees per tick) and walks off
execute if score #t angel.fight matches 1..6 run function angel:fight/bo_shove
execute if score #t angel.fight matches 6..29 run function angel:fight/bo_turn
execute if score #t angel.fight matches 30.. run function angel:fight/bo_go
