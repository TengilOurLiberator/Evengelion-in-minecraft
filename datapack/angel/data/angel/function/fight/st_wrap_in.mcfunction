tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]
execute if score #t angel.fight matches 1 run function angel:angel/walk_go
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..16] run function angel:fight/wrap_clamp
execute if score #st angel.fight matches 6 if score #t angel.fight matches 100.. run function angel:fight/wrap_clamp
