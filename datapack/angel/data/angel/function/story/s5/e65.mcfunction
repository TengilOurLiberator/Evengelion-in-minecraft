scoreboard players set #force angel.story 0
execute positioned 3107.0 63.0 53.75 rotated 29.25 0 run function angel:cast/summon {id:"gendo"}
function angel:cast/scale {id:"gendo",scale:2.0}
function angel:cast/look {id:"gendo",mode:"ahead"}
scoreboard players set #f.turn_7 angel.story 8
scoreboard players set #present_gendo angel.story 1
function angel:story/hq/fl_booth
playsound angel:sfx.booth_light master @a 3107.0 67.0 52.75 2.5 1.0 0.7
scoreboard players set #step angel.story 66
function angel:story/s5/e66
