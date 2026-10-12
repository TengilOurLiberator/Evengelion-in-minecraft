scoreboard players set #hbt angel.fight 0
execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.heartbeat master @a ~ ~ ~ 4 0.9
execute if score #wt angel.fight matches ..200 at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.heartbeat master @a ~ ~ ~ 4 1.2
execute if score #wt angel.fight matches ..100 at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.heartbeat master @a ~ ~ ~ 5 1.5
