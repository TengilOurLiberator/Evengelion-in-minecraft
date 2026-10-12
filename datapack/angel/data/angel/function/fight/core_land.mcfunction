# within arm's length the fields cancel and the hit lands on the core.  This (and only this) arms the core's guard
scoreboard players set #hitcd angel.fight 24
scoreboard players remove #ch angel.fight 1
execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0
particle minecraft:flash{color:[1.0,0.55,0.45,1.0]} ~ ~2.25 ~ 0 0 0 0 1 force
particle minecraft:crit ~ ~2.25 ~ 1.2 1.2 1.2 0.4 30 force
particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~2.25 ~ 1.4 1.4 1.4 0 24 force
playsound angel:sfx.giant_punch hostile @a ~ ~ ~ 3 1
function angel:fight/bark {id:"7_08"}
# back-off: every backoff_hits landed hits (the wrap phase excluded) the monster disengages
execute if score #phase angel.fight matches 1..2 run scoreboard players add #bo angel.fight 1
execute if score #st angel.fight matches 3 run function angel:fight/begin_stagger
execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..30 run function angel:fight/core_crack
execute if score #phase angel.fight matches 1..2 if score #ch angel.fight matches ..10 run function angel:fight/wrap_start
execute if score #phase angel.fight matches 1..2 if score #bo angel.fight matches 8.. if score #ch angel.fight matches 1.. run function angel:fight/backoff_check
