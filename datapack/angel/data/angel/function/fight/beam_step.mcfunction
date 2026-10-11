# one block of the beam; stops on a block, on the giant, or after the range
execute unless block ~ ~ ~ #angel:fight/beam_pass run return run function angel:fight/beam_impact
execute positioned ~-0.5 ~-0.5 ~-0.5 if entity @e[tag=angel.giant,dx=0,dy=0,dz=0] run return run function angel:fight/beam_hit
particle minecraft:dust{color:[1.0,0.85,0.35],scale:3.0} ~ ~ ~ 0.25 0.25 0.25 0 1 force
scoreboard players add #bs angel.fight 1
scoreboard players remove #rs angel.fight 1
execute if score #rs angel.fight matches 1.. positioned ^ ^ ^1 run function angel:fight/beam_step
execute if score #rs angel.fight matches ..0 run summon minecraft:marker ~ ~ ~ {Tags:["angel.fight","angel.bi"]}
