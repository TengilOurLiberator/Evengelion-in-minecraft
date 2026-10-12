execute unless score #walking angel.mon matches 1 run return 0
execute unless entity @e[type=minecraft:marker,tag=angel.root] run return run scoreboard players set #walking angel.mon 0
function angel:angel/turn
# arrived?
function angel:angel/walk_arrive_check with storage angel:mon walk
execute unless score #walking angel.mon matches 1 run return 0
# more than 16 degrees off the target: turn on the spot (it moves 0.3-0.9 blocks per tick and turns 4 degrees per tick, so with a target inside its turning circle it would orbit it)
execute unless score #dy angel.mon matches -159..159 run return run function angel:angel/walk_pivot
# one update of movement: 2 ticks worth
function angel:angel/walk_move with storage angel:mon walk
function angel:angel/sync
scoreboard players remove #step angel.mon 2
execute if score #step angel.mon matches ..0 run function angel:angel/step
schedule function angel:angel/walk_tick 2t
