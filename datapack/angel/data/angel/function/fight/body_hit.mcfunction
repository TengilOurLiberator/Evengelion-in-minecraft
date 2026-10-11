data remove entity @s attack
execute if score #hitcd angel.fight matches 1.. run return 0
scoreboard players set #hitcd angel.fight 7
particle minecraft:crit ~ ~ ~ 1 1 1 0.2 6 force
particle minecraft:electric_spark ~ ~ ~ 1.5 1.5 1.5 0.2 8 force
playsound minecraft:block.anvil.hit hostile @a ~ ~ ~ 2 1.8
function angel:fight/bark {id:"7_08"}
