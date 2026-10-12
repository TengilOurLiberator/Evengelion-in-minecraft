scoreboard players set #force angel.story 0
execute positioned 113.5 64.0 128.5 rotated 90.0 0 run function angel:cast/summon {id:"rei_uniform"}
function angel:cast/look {id:"rei_uniform",mode:"player"}
kill @e[tag=angel.girl_mark]
tag @e[tag=angel.rei_uniform,tag=angel.char,limit=1] add angel.look_target
scoreboard players set #f.seen angel.story 0
scoreboard players set #v.away angel.story 0
scoreboard players set #step angel.story 34
function angel:story/s1/e34
