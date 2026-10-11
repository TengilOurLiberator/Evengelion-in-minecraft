execute at @e[tag=angel.cmark,limit=1] run particle minecraft:explosion ~-2 ~-11 ~ 5 7 5 0 3 force
execute at @e[tag=angel.cmark,limit=1] run particle minecraft:flash{color:[1.0,0.85,0.5,1.0]} ~ ~ ~ 0 0 0 0 1 force
execute at @e[tag=angel.cmark,limit=1] run playsound minecraft:entity.generic.explode ambient @a ~ ~ ~ 6 1.3 0.35
