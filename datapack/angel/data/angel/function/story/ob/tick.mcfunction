execute if score #ob.line angel.story matches 1.. run scoreboard players remove #ob.line angel.story 1
execute if score #ob.line angel.story matches 0 run function angel:story/ob/line_off
execute unless score #ob.on angel.story matches 1 run return 0
execute if score #ob.hast angel.story matches 1 unless entity @e[tag=angel.ob_target,limit=1] run function angel:story/ob/td/root
execute if score #ob.fl angel.story matches 1 run function angel:story/ob/fd/root
scoreboard players add #ob.t angel.story 1
scoreboard players operation #ob.m angel.story = #ob.t angel.story
scoreboard players operation #ob.m angel.story %= #c5 angel.story
execute if score #ob.m angel.story matches 0 run function angel:story/ob/sample
