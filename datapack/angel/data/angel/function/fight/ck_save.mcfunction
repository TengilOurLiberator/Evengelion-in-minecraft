# called when the core cracks: where the monster and the giant stand (x10, so they fit a score) for the checkpoint restart
scoreboard players set #ck angel.fight 1
execute store result score #ckmx angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[0] 10
execute store result score #ckmy angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[1] 10
execute store result score #ckmz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[2] 10
execute store result score #ckgx angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[0] 10
execute store result score #ckgy angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[1] 10
execute store result score #ckgz angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[2] 10
