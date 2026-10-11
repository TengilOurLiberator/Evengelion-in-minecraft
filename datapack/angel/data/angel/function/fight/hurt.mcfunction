# #dmg angel.fight = points. Shared invulnerability window; the real player also takes a token hit for the flash
execute if score #phase angel.fight matches 4.. run return 0
execute if score #ginv angel.fight matches 1.. run return 0
scoreboard players operation #gh angel.fight -= #dmg angel.fight
scoreboard players set #ginv angel.fight 20
scoreboard players set #gcalm angel.fight 0
execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 3 0.6
execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.iron_golem.damage hostile @a ~ ~ ~ 3 0.5
execute as @e[tag=angel.giant,type=minecraft:player] run damage @s 1 minecraft:magic
execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:instant_health 1 4 true
function angel:fight/bark {id:"7_04"}
function angel:fight/bark {id:"7_05"}
execute if score #gh angel.fight matches ..25 run function angel:fight/bark {id:"7_10"}
execute if score #gh angel.fight matches ..25 run function angel:fight/bark {id:"7_11"}
execute if score #gh angel.fight matches ..0 run function angel:fight/lost_start
