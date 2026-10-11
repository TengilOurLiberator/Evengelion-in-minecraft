# within arm's length the fields cancel and the hit lands on the core
scoreboard players remove #ch angel.fight 1
execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0
particle minecraft:flash{color:[1.0,0.55,0.45,1.0]} ~ ~2.25 ~ 0 0 0 0 1 force
particle minecraft:crit ~ ~2.25 ~ 1.2 1.2 1.2 0.4 30 force
particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~2.25 ~ 1.4 1.4 1.4 0 24 force
playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 3 1.5
playsound minecraft:block.anvil.land hostile @a ~ ~ ~ 3 1.7
playsound minecraft:entity.iron_golem.damage hostile @a ~ ~ ~ 3 0.6
function angel:fight/bark {id:"7_08"}
execute if score #st angel.fight matches 3 run function angel:fight/begin_stagger
execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..20 run function angel:fight/core_crack
execute if score #phase angel.fight matches 1..2 if score #ch angel.fight matches ..8 run function angel:fight/wrap_start
execute if score #phase angel.fight matches 3 if score #ch angel.fight matches ..0 run function angel:fight/won_start
