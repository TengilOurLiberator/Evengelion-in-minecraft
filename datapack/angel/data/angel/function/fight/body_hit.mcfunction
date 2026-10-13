# the body box: no damage.  Small sparks and a dull thud say 'you hit it, but not there', and the core flashes once to point at the place to hit.
# (While the monster is wrapped round the giant it is the big box and counts as a core hit)
data remove entity @s attack
execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit
execute if score #sparkcd angel.fight matches 1.. run return 0
scoreboard players set #sparkcd angel.fight 4
particle minecraft:crit ~ ~8.40 ~ 0.8 0.8 0.8 0.2 5 force
particle minecraft:electric_spark ~ ~8.40 ~ 1.0 1.0 1.0 0.15 6 force
playsound minecraft:block.stone.hit hostile @a ~ ~8.40 ~ 2.5 0.5
function angel:fight/bark {id:"7_08"}
execute if score #ptcd angel.fight matches 0 run function angel:fight/core_point
