scoreboard players set #force angel.story 0
function angel:story/launch/cage_lights_on
function angel:story/launch/eyes_off
function angel:cast/remove_all
function angel:cast/gurney_remove
execute positioned 3094.5 54.0 76.5 rotated 180.0 0 run function angel:cast/summon {id:"misato"}
execute positioned 3098.5 54.0 76.5 rotated 180.0 0 run function angel:cast/summon {id:"ritsuko"}
execute positioned 3107.0 63.0 53.75 rotated 29.2 0 run function angel:cast/summon {id:"gendo"}
function angel:cast/scale {id:"gendo",scale:2.0}
execute positioned 3096.5 54.0 80.5 rotated -90.0 0 run function angel:cast/gurney {}
execute positioned 3096.5 54.82 80.5 rotated -90.0 0 run function angel:cast/summon {id:"rei"}
function angel:cast/mount {id:"rei",tag:"angel.seat_gurney"}
function angel:cast/pose {id:"rei",pose:"lying"}
function angel:cast/look {id:"misato",mode:"player"}
function angel:cast/look {id:"ritsuko",mode:"player"}
function angel:cast/look {id:"gendo",mode:"player"}
scoreboard players set #present_misato angel.story 1
scoreboard players set #present_ritsuko angel.story 1
scoreboard players set #present_gendo angel.story 1
scoreboard players set #present_rei angel.story 1
scoreboard players set #beat angel.story 80
scoreboard players set #step angel.story 42
function angel:story/s7/e42
