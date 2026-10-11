# the core is broken
scoreboard players set #phase angel.fight 4
scoreboard players set #st angel.fight 8
scoreboard players set #pt angel.fight 0
function angel:angel/stop_walking
bossbar set angel:fight/wrap visible false
bossbar set angel:fight/angel visible false
execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 12 0.8
function angel:fight/bark {id:"7_15"}
function angel:fight/bark {id:"7_16"}
function angel:fight/bark {id:"7_17"}
function angel:fight/bark {id:"7_18"}
