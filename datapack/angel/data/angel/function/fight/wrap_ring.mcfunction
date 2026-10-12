# the ring at the giant's chest (18 up), radius 9 / 7 / 5 / 3.5 as the time runs down
execute if score #wt angel.fight matches 241.. at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_9
execute if score #wt angel.fight matches 161..240 at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_7
execute if score #wt angel.fight matches 81..160 at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_5
execute if score #wt angel.fight matches ..80 at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_3
