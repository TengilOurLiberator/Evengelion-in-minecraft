execute at @e[tag=angel.rei_uniform,tag=angel.char,limit=1] run particle minecraft:poof ~ ~1 ~ 0.25 0.6 0.25 0.02 10 force
function angel:cast/remove {id:"rei_uniform"}
kill @e[tag=angel.look_target]
scoreboard players set #step angel.story 30
function angel:story/s1/e30
