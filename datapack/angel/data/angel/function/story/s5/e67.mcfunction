scoreboard players set #force angel.story 0
execute positioned 3103.5 57.0 62.25 rotated 34.33 0 run function angel:cast/summon {id:"gendo"}
function angel:cast/scale {id:"gendo",scale:2.0}
function angel:cast/look {id:"gendo",mode:"ahead"}
scoreboard players set #f.turn_7 angel.story 8
scoreboard players set #present_gendo angel.story 1
function angel:story/hq/booth_on
function angel:story/hq/booth_flare
playsound angel:sfx.booth_light master @a 3103.5 59.5 62.25 4.0 1.0 1.0
scoreboard players set #step angel.story 68
function angel:story/s5/e68
