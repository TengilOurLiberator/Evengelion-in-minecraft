# the body box only sparks: no damage, and it does not arm the core's guard.  (While the monster is wrapped round the giant it is the big box and counts as a core hit)
data remove entity @s attack
execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit
execute if score #sparkcd angel.fight matches 1.. run return 0
scoreboard players set #sparkcd angel.fight 4
particle minecraft:crit ~ ~ ~ 1 1 1 0.2 6 force
particle minecraft:electric_spark ~ ~ ~ 1.5 1.5 1.5 0.2 8 force
playsound minecraft:block.anvil.hit hostile @a ~ ~ ~ 2 1.8
function angel:fight/bark {id:"7_08"}
