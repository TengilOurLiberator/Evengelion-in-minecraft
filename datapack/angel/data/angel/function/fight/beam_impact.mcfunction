summon minecraft:marker ~ ~ ~ {Tags:["angel.fight","angel.bi"]}
particle minecraft:explosion_emitter ~ ~ ~ 0 0 0 0 2 force
particle minecraft:flash{color:[1.0,0.9,0.6,1.0]} ~ ~ ~ 0 0 0 0 1 force
particle minecraft:large_smoke ~ ~ ~ 2.5 2.5 2.5 0.05 40 force
playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 12 0.6
# a little damage to the city, never near the ground (plaza, street and the lift stay)
execute if score #destroy angel.fight matches 1 run function angel:fight/beam_break
