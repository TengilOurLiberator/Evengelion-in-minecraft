scoreboard players add #pt angel.fight 1
execute if score #pt angel.fight matches 2 run function angel:angel/pose_dying
execute if score #pt angel.fight matches ..130 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~2 ~ 1.5 1.5 1.5 0 2 force
# the pillar of light stands up out of the body, the body is gone, the pillar fades
execute if score #pt angel.fight matches 135 at @e[type=minecraft:marker,tag=angel.root,limit=1] run function angel:fight/pillar
execute if score #pt angel.fight matches 150 run function angel:angel/remove
execute if score #pt angel.fight matches 150 run tag @e[tag=angel.mon] add angel.fight
execute if score #pt angel.fight matches 240.. if function angel:fight/queue_empty run function angel:fight/won_final
execute if score #pt angel.fight matches 1500.. run function angel:fight/won_final
