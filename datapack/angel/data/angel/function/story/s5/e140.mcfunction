scoreboard players set #force angel.story 0
execute positioned 3057.5 54.0 80.5 rotated -90 0 run function angel:cast/gurney
execute positioned 3057.5 54.0 80.5 rotated -90 0 run function angel:cast/summon {id:"rei"}
function angel:cast/mount {id:"rei",tag:"angel.seat_gurney"}
function angel:cast/pose {id:"rei",pose:"lying"}
function angel:cast/gurney_crew
function angel:cast/gurney_move {x:3096.5,y:54.0,z:80.5,speed:0.1875}
playsound angel:sfx.gurney master @a 3061.5 55.0 80.5 1.8 1.0 0.5
scoreboard players set #step angel.story 141
function angel:story/s5/e141
