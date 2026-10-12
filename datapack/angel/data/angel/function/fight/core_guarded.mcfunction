# a hit on the core inside its guard: a few sparks and a dull clank.  No damage, no counter, does not re-arm the guard
scoreboard players add #guarded angel.fight 1
execute if score #sparkcd angel.fight matches 1.. run return 0
scoreboard players set #sparkcd angel.fight 4
particle minecraft:electric_spark ~ ~2.25 ~ 1 1 1 0.3 14 force
particle minecraft:smoke ~ ~2.25 ~ 0.6 0.6 0.6 0.01 5 force
playsound minecraft:block.iron_trapdoor.close hostile @a ~ ~2.25 ~ 2.2 0.5
