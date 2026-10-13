# a swing that connects while the barrier is down and the giant is within arm's length.  It ALWAYS counts: there is no guard, nothing else gates it
scoreboard players remove #ch angel.fight 1
execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0
scoreboard players add #hit_n angel.fight 1
scoreboard players set #blk_n angel.fight 0
scoreboard players set #blk_why angel.fight 0
particle minecraft:flash{color:[1.0,0.55,0.45,1.0]} ~ ~3.00 ~ 0 0 0 0 1 force
particle minecraft:crit ~ ~3.00 ~ 1.2 1.2 1.2 0.4 30 force
particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~3.00 ~ 1.4 1.4 1.4 0 24 force
playsound angel:sfx.giant_punch hostile @a ~ ~ ~ 3 1
function angel:fight/bark {id:"7_08"}
# crack progress (slivers of light across the core)
execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..34 run function angel:angel/core_crack_1
execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..26 run function angel:angel/core_crack_2
execute if score #phase angel.fight matches 2 if score #ch angel.fight matches ..17 run function angel:angel/core_crack_1
execute if score #phase angel.fight matches 2 if score #ch angel.fight matches ..12 run function angel:angel/core_crack_2
# back-off: every backoff_hits landed hits (the wrap phase excluded) the monster disengages
execute if score #phase angel.fight matches 1..2 run scoreboard players add #bo angel.fight 1
execute if score #st angel.fight matches 3 run function angel:fight/begin_stagger
execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..22 run function angel:fight/core_crack
execute if score #phase angel.fight matches 1..2 if score #ch angel.fight matches ..10 run function angel:fight/wrap_start
execute if score #phase angel.fight matches 1..2 if score #bo angel.fight matches 9.. if score #ch angel.fight matches 1.. run function angel:fight/backoff_check
# the monster flinches (not when it is staggering, thrown back, retreating or wrapped: its own motion says it)
execute if score #st angel.fight matches 0..4 run function angel:fight/flinch
