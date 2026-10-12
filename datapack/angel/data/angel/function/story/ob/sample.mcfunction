function angel:story/ob/measure
scoreboard players set #ob.pr angel.story 0
execute if score #ob.b angel.story < #ob.bb angel.story run scoreboard players set #ob.pr angel.story 1
execute if score #ob.pr angel.story matches 1 run function angel:story/ob/progress
execute if score #ob.pr angel.story matches 0 run scoreboard players add #ob.np angel.story 5
execute if score #ob.gate angel.story matches 1 run function angel:story/ob/gate
scoreboard players set #ob.ok angel.story 0
execute if score #ob.vis angel.story matches 1 if score #ob.t angel.story >= #ob.g angel.story run scoreboard players set #ob.ok angel.story 1
execute if score #ob.ok angel.story matches 1 if score #ob.shown angel.story matches 0 run function angel:story/ob/appear
execute if score #ob.ok angel.story matches 0 if score #ob.shown angel.story matches 1 run function angel:story/ob/hide
execute if score #ob.shown angel.story matches 1 run function angel:story/ob/update
execute if score #ob.shown angel.story matches 1 if score #ob.np angel.story >= #ob.rep angel.story run function angel:story/ob/reline
