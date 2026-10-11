scoreboard players set #force angel.story 0
execute positioned 3115.5 95.0 42.5 rotated 32.35 0 run function angel:cast/summon {id:"gendo"}
function angel:cast/look {id:"gendo",mode:"ahead"}
scoreboard players set #f.turn_7 angel.story 8
scoreboard players set #present_gendo angel.story 1
function angel:story/hq/fl_booth
playsound angel:sfx.booth_light master @a 3115.5 99.0 41.5 2.5 1.0 0.7
scoreboard players set #step angel.story 62
function angel:story/s5/e62
